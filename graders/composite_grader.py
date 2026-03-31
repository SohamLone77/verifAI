# COST_TRACKING
from __future__ import annotations

from typing import Optional

from app.models import Rubric
from graders import GraderResult, register_grader
from graders.rubric_grader import RubricGrader
from graders.semantic_grader import SemanticGrader
from reward.cost_tracker import CostTracker


@register_grader("composite")
class CompositeGrader:
    """
    Weighted blend of rubric (rule-based) and semantic graders.

    Default weights:
      - Rubric (safety/brevity/factuality/brand voice): 0.65
      - Semantic (embedding cosine similarity): 0.35

    Final score is clamped to [0.0, 1.0].
    """

    RUBRIC_WEIGHT: float = 0.65
    SEMANTIC_WEIGHT: float = 0.35

    def __init__(self) -> None:
        self._rubric = RubricGrader()
        self._semantic = SemanticGrader()

    def grade(
        self,
        prompt: str,
        output: str,
        rubric: Optional[Rubric] = None,
        reference: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None,
    ) -> GraderResult:
        rubric_result = self._rubric.grade(prompt=prompt, output=output, rubric=rubric)
        semantic_result = self._semantic.grade(
            prompt=prompt,
            output=output,
            rubric=rubric,
            reference=reference,
            cost_tracker=cost_tracker,
        )

        composite_score = (
            rubric_result.score * self.RUBRIC_WEIGHT
            + semantic_result.score * self.SEMANTIC_WEIGHT
        )
        composite_score = round(max(0.0, min(1.0, composite_score)), 4)

        breakdown = {
            **{f"rubric_{k}": v for k, v in rubric_result.breakdown.items()},
            **{f"semantic_{k}": v for k, v in semantic_result.breakdown.items()},
            "rubric_composite": rubric_result.score,
            "semantic_composite": semantic_result.score,
        }

        notes = rubric_result.notes + semantic_result.notes

        metadata = {}
        if semantic_result.metadata:
            metadata.update(semantic_result.metadata)

        return GraderResult(
            score=composite_score,
            breakdown=breakdown,
            notes=notes,
            metadata=metadata,
        )
