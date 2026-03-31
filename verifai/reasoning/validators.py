"""Reasoning validation helpers"""

from typing import List

from verifai.models.reasoning_models import ReasoningChain


def validate_chain(chain: ReasoningChain) -> List[str]:
    """Return validation issues for a reasoning chain"""
    issues: List[str] = []

    if not chain.steps:
        issues.append("Reasoning chain has no steps")

    if not chain.final_decision:
        issues.append("Final decision is missing")

    return issues
