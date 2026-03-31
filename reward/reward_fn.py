# COT_REWARD
from __future__ import annotations

from typing import Optional

from app.models import Reward
from reward.cot_scorer import detect_reasoning_quality, score_reasoning
from reward.reward_config import RewardConfig

_cfg = RewardConfig()


def compute_reward(
    score: float,
    step: int,
    max_steps: int,
    done: bool,
    action_text: str = "",
    reasoning: Optional[str] = None,
    reasoning_steps: Optional[list[str]] = None,
    rubric_id: str = "default",
    previous_score: Optional[float] = None,
) -> Reward:
    """
    Compute the shaped reward for a single environment step.

    Components:
    - Base score reward (scaled by quality weight)
    - Progress bonus: extra if score improved vs. previous step
    - Step penalty: small cost per step to encourage efficiency
    - Completion bonus: awarded on final step if score >= success_threshold
    - Safety penalty: applied if score is very low (likely safety failure)
    """
    # Base reward from grader score
    base = score * _cfg.quality_weight

    # Progress bonus
    progress_bonus = 0.0
    if previous_score is not None and score > previous_score:
        delta = score - previous_score
        progress_bonus = delta * _cfg.progress_bonus_multiplier

    # Step penalty
    step_penalty = _cfg.step_penalty

    # Completion bonus (on final step only)
    done_bonus = 0.0
    if done and score >= _cfg.success_threshold:
        done_bonus = _cfg.completion_bonus

    # Safety penalty (very low score = likely safety violation)
    safety_penalty = 0.0
    if score < _cfg.safety_penalty_threshold:
        safety_penalty = _cfg.safety_penalty

    combined_reasoning = (reasoning or "").strip()
    if reasoning_steps:
        steps_text = "\n".join(f"- {step}" for step in reasoning_steps)
        combined_reasoning = f"{combined_reasoning}\n{steps_text}".strip()

    cot_score = score_reasoning(combined_reasoning, action_text, rubric_id)

    steps_for_quality: list[str] = []
    if reasoning_steps:
        steps_for_quality = reasoning_steps
    elif combined_reasoning:
        for line in combined_reasoning.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if stripped.startswith(("-", "*")):
                steps_for_quality.append(stripped.lstrip("-* "))
                continue
            if lower.startswith("step "):
                steps_for_quality.append(stripped)
                continue
            if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
                steps_for_quality.append(stripped)

    reasoning_quality_score = detect_reasoning_quality(steps_for_quality)
    if reasoning_quality_score <= 0.0:
        reasoning_quality = "none"
    elif reasoning_quality_score < 0.34:
        reasoning_quality = "low"
    elif reasoning_quality_score < 0.67:
        reasoning_quality = "medium"
    else:
        reasoning_quality = "high"

    total = base + progress_bonus - step_penalty + done_bonus - safety_penalty + cot_score.cot_bonus
    total = round(max(0.0, min(1.0, total)), 4)

    return Reward(
        value=total,
        breakdown={
            "base": round(base, 4),
            "progress_bonus": round(progress_bonus, 4),
            "done_bonus": round(done_bonus, 4),
            "safety_penalty": round(-safety_penalty, 4),
            "cot_bonus": round(cot_score.cot_bonus, 4),
        },
        step_penalty=round(step_penalty, 4),
        done_bonus=round(done_bonus, 4),
        cot_bonus=round(cot_score.cot_bonus, 4),
        reasoning_quality=reasoning_quality,
    )
