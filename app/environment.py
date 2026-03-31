# ANALYTICS
# COT_REWARD
# MULTIMODAL
# COST_TRACKING
from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any, Optional

from app.analytics import EpisodeRecord, analytics_store
from app.models import (
    Action,
    ActionType,
    CostSummary,
    EpisodeInfo,
    Observation,
    Reward,
    Rubric,
    State,
    StepResponse,
    TaskName,
)
from app.multimodal_processor import normalize_to_text
from data.scenario_loader import sample_scenario
from graders.composite_grader import CompositeGrader
from reward.reward_fn import compute_reward
from app.session import session_store
from tasks import load_task


class PromptReviewEnv:
    """
    Core OpenEnv-compatible environment.

    Each call to `reset()` begins a new episode for the given task.
    Calls to `step()` apply an action and return the next observation,
    shaped reward, done flag, and info dict.
    """

    def __init__(self) -> None:
        self._grader = CompositeGrader()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(
        self,
        task_name: TaskName,
        session_id: Optional[str] = None,
        scenario_id: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> tuple[Observation, State]:
        """Start a new episode. Returns the initial observation and state."""
        sid = session_id or str(uuid.uuid4())
        task = load_task(task_name)

        # Load a scenario (specific id or random by difficulty)
        scenario = sample_scenario(
            difficulty=difficulty or task.difficulty,
            scenario_id=scenario_id,
        )

        state = State(
            session_id=sid,
            task=task_name,
            step=0,
            max_steps=task.max_steps,
            done=False,
            total_reward=0.0,
            history=[],
        )

        obs = Observation(
            session_id=sid,
            task=task_name,
            step=0,
            prompt=scenario["prompt"],
            current_output=scenario.get("reference_output", ""),
            rubric=Rubric(**scenario.get("rubric", {})),
            done=False,
            score=None,
            image_url=scenario.get("image_url"),
            image_b64=scenario.get("image_b64"),
        )

        # Store scenario reference on state for downstream grading
        state.history.append({
            "type": "reset",
            "scenario": scenario,
            "prompt": scenario["prompt"],
        })

        return obs, state

    def step(
        self,
        state: State,
        obs: Observation,
        action: Action,
    ) -> StepResponse:
        """Apply an action and return next observation, reward, done, info."""
        new_step = state.step + 1
        done = False
        score: Optional[float] = None
        info: dict[str, Any] = {}

        # Normalize action content to plain text (handles text/image/structured)
        grading_text = normalize_to_text(action)

        session = session_store.get(state.session_id)
        cost_tracker = session.cost_tracker if session is not None else None

        # Grade the agent's output
        grade_result = self._grader.grade(
            prompt=obs.prompt,
            output=grading_text,
            rubric=obs.rubric,
            cost_tracker=cost_tracker,
        )
        score = grade_result.score

        # Determine termination
        if action.action_type == ActionType.submit or new_step >= state.max_steps:
            done = True

        # Compute shaped reward
        rubric_id = "custom" if obs.rubric.custom_notes else "default"
        reward = compute_reward(
            score=score,
            step=new_step,
            max_steps=state.max_steps,
            done=done,
            action_text=grading_text,
            reasoning=action.reasoning,
            reasoning_steps=action.reasoning_steps,
            rubric_id=rubric_id,
            previous_score=self._get_last_score(state),
        )

        usage = grade_result.metadata.get("usage") if grade_result.metadata else None
        if session is not None and usage and not usage.get("tracked"):
            model = usage.get("model")
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            if model:
                session.cost_tracker.track(
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

        if session is not None:
            report = session.cost_tracker.get_episode_cost(session_id=state.session_id)
            reward.cost_summary = CostSummary(
                total_usd=report.total_usd,
                tokens_used=report.total_tokens,
                hint=report.hints[0] if report.hints else None,
            )

        # Update state
        state.step = new_step
        state.done = done
        state.total_reward += reward.value
        state.history.append({
            "step": new_step,
            "action_type": action.action_type,
            "modality": action.modality,
            "content_preview": grading_text[:100],
            "score": score,
            "reward": reward.value,
        })

        if done:
            analytics_store.append_episode(
                EpisodeRecord(
                    session_id=state.session_id,
                    task_id=state.task.value,
                    score=score or 0.0,
                    cost_usd=reward.cost_summary.total_usd if reward.cost_summary else 0.0,
                    steps=new_step,
                    timestamp=datetime.utcnow().isoformat(),
                    event_type="review",
                    model_usage=session.cost_tracker.model_usage if session is not None else None,
                )
            )

        # Build next observation — propagate multimodal fields from the action
        next_obs = Observation(
            session_id=obs.session_id,
            task=obs.task,
            step=new_step,
            prompt=obs.prompt,
            current_output=grading_text,
            rubric=obs.rubric,
            done=done,
            score=score if done else None,
            image_b64=action.image_b64,
            image_url=action.image_url,
            structured_output=action.structured_data,
        )

        info = {
            "score": score,
            "breakdown": grade_result.breakdown,
            "total_reward": state.total_reward,
        }

        return StepResponse(
            observation=next_obs,
            reward=reward,
            done=done,
            info=info,
        )

    def get_episode_info(self, state: State, final_score: Optional[float]) -> EpisodeInfo:
        return EpisodeInfo(
            session_id=state.session_id,
            task=state.task,
            total_steps=state.step,
            total_reward=state.total_reward,
            final_score=final_score,
            success=(final_score is not None and final_score >= 0.7),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_last_score(self, state: State) -> Optional[float]:
        for entry in reversed(state.history):
            if "score" in entry and entry["score"] is not None:
                return entry["score"]
        return None
