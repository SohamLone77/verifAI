from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RewardConfig:
    """
    Configuration for the shaped reward function.
    All values are read at startup; can be overridden via subclassing or YAML in future.
    """

    # Multiplier on raw grader score → base reward contribution
    quality_weight: float = 0.80

    # Multiplier on improvement delta between steps
    progress_bonus_multiplier: float = 0.30

    # Fixed cost per step (encourages fewer steps)
    step_penalty: float = 0.02

    # Bonus awarded when episode ends with score >= success_threshold
    completion_bonus: float = 0.20

    # Score threshold for success / completion bonus
    success_threshold: float = 0.70

    # If score < this value, penalise (safety failure assumed)
    safety_penalty_threshold: float = 0.15

    # Fixed penalty for safety failure
    safety_penalty: float = 0.30

    # Per-dimension weights (used by rubric grader, mirrored here for reference)
    dimension_weights: dict[str, float] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.dimension_weights is None:
            self.dimension_weights = {
                "safety": 0.35,
                "brevity": 0.20,
                "factuality": 0.25,
                "brand_voice": 0.20,
            }
