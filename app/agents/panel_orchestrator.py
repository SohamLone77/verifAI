# MULTI_AGENT
from __future__ import annotations

import asyncio
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.agents.base_agent import AgentFeedback
from app.agents.factuality_agent import FactualityAgent
from app.agents.rewriter_agent import RewriterAgent
from app.agents.safety_agent import SafetyAgent
from app.environment import PromptReviewEnv
from app.models import Action, Observation, State, TaskName
from app.session import session_store
from graders.rubric_grader import RubricGrader
from reward.cost_tracker import CostTracker


class PanelResult(BaseModel):
    individual_actions: list[Action]
    individual_scores: list[float]
    final_action: Action
    final_score: float
    panel_cost_usd: float = Field(0.0, ge=0.0)


class PanelCompareResult(BaseModel):
    session_id: str
    single_agent_score: float
    panel_score: float
    delta: float


class PanelOrchestrator:
    def __init__(self, env: Optional[PromptReviewEnv] = None) -> None:
        self._env = env or PromptReviewEnv()
        self._safety_agent = SafetyAgent()
        self._factuality_agent = FactualityAgent()
        self._rewriter_agent = RewriterAgent()
        self._rubric_grader = RubricGrader()

    async def run_panel(self, session_id: str, observation: Observation) -> PanelResult:
        session = session_store.get(session_id)
        if session is None:
            raise ValueError(f"Session '{session_id}' not found.")

        state = session.state
        if state.task != TaskName.iterative:
            raise ValueError("Panel orchestration is only supported for iterative tasks.")

        return await self._run_panel_with_state(
            session_id=session_id,
            state=state,
            observation=observation,
            apply_state=True,
        )

    async def compare(self, session_id: str) -> PanelCompareResult:
        session = session_store.get(session_id)
        if session is None:
            raise ValueError(f"Session '{session_id}' not found.")

        if session.state.task != TaskName.iterative:
            raise ValueError("Panel orchestration is only supported for iterative tasks.")

        state_copy = session.state.model_copy(deep=True)
        obs_copy = session.obs.model_copy(deep=True)

        single_action = await self._rewriter_agent.run_with_feedback(obs_copy, [])
        single_response = self._env.step(state_copy, obs_copy, single_action)
        single_score = single_response.info.get("score", 0.0)

        panel_result = await self._run_panel_with_state(
            session_id=session_id,
            state=session.state.model_copy(deep=True),
            observation=session.obs.model_copy(deep=True),
            apply_state=False,
        )

        panel_score = panel_result.final_score
        return PanelCompareResult(
            session_id=session_id,
            single_agent_score=single_score,
            panel_score=panel_score,
            delta=round(panel_score - single_score, 4),
        )

    async def _run_panel_with_state(
        self,
        session_id: str,
        state: State,
        observation: Observation,
        apply_state: bool,
    ) -> PanelResult:
        cost_tracker = CostTracker()

        safety_action, factuality_action = await asyncio.gather(
            self._safety_agent.run(observation),
            self._factuality_agent.run(observation),
        )

        feedback = [
            AgentFeedback(
                name=(safety_action.metadata or {}).get("agent", "SafetyAgent"),
                rubric_focus=(safety_action.metadata or {}).get("rubric_focus", ["safety"]),
                feedback=safety_action.content,
            ),
            AgentFeedback(
                name=(factuality_action.metadata or {}).get("agent", "FactualityAgent"),
                rubric_focus=(factuality_action.metadata or {}).get("rubric_focus", ["factuality"]),
                feedback=factuality_action.content,
            ),
        ]

        final_action = await self._rewriter_agent.run_with_feedback(observation, feedback)

        for action in (safety_action, factuality_action, final_action):
            self._track_usage(action, cost_tracker)

        safety_score = self._score_action(observation, safety_action.content)
        factuality_score = self._score_action(observation, factuality_action.content)

        response = self._env.step(state=state, obs=observation, action=final_action)
        final_score = response.info.get("score", 0.0)

        if apply_state:
            session_store.update(session_id, state, response.observation)

        return PanelResult(
            individual_actions=[safety_action, factuality_action, final_action],
            individual_scores=[
                round(safety_score, 4),
                round(factuality_score, 4),
                round(final_score, 4),
            ],
            final_action=final_action,
            final_score=round(final_score, 4),
            panel_cost_usd=round(cost_tracker.total_usd, 6),
        )

    def _score_action(self, observation: Observation, text: str) -> float:
        result = self._rubric_grader.grade(
            prompt=observation.prompt,
            output=text,
            rubric=observation.rubric,
        )
        return result.score

    def _track_usage(self, action: Action, tracker: CostTracker) -> None:
        usage = action.metadata.get("usage") if action.metadata else None
        if not usage:
            return
        tracker.track(
            model=usage.get("model", "gpt-4o-mini"),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
