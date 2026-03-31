# COT_REWARD
from __future__ import annotations

from reward.cot_scorer import CoTScore, detect_reasoning_quality, score_reasoning


def test_no_reasoning_scores_zero():
    result = score_reasoning("", "", "default")
    assert isinstance(result, CoTScore)
    assert result.steps_count == 0
    assert result.cot_bonus == 0.0
    assert result.identified_issues is False
    assert result.explained_fix is False


def test_weak_reasoning_no_bonus():
    reasoning = "Fix issues."
    result = score_reasoning(reasoning, "", "default")
    assert result.cot_bonus == 0.0
    assert result.steps_count == 0


def test_strong_reasoning_partial_bonus():
    reasoning = (
        "Step 1: Identify safety issues because the response includes unsafe claims.\n"
        "Step 2: Remove unsafe wording to ensure safety."
    )
    result = score_reasoning(reasoning, "", "default")
    assert result.steps_count == 2
    assert result.cot_bonus == 0.1

    steps = [
        "Identify safety issues because the response includes unsafe claims.",
        "Remove unsafe wording to ensure safety.",
    ]
    quality = detect_reasoning_quality(steps)
    assert quality >= 0.6


def test_perfect_reasoning_full_bonus():
    reasoning = (
        "1. Identify brevity and factuality issues in the draft.\n"
        "2. Explain that removing unverifiable claims improves factuality because it reduces hallucinations.\n"
        "3. Shorten sentences to meet the token budget."
    )
    result = score_reasoning(reasoning, "", "default")
    assert result.steps_count == 3
    assert result.cot_bonus == 0.15

    steps = [
        "Identify brevity and factuality issues in the draft.",
        "Explain that removing unverifiable claims improves factuality because it reduces hallucinations.",
        "Shorten sentences to meet the token budget.",
    ]
    quality = detect_reasoning_quality(steps)
    assert quality >= 0.9
