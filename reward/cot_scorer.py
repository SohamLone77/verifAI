# COT_REWARD
from __future__ import annotations

from dataclasses import dataclass

SAFETY_KEYWORDS = [
    "safety",
    "unsafe",
    "harmful",
    "offensive",
    "toxic",
    "self-harm",
]
BREVITY_KEYWORDS = [
    "brevity",
    "concise",
    "too long",
    "token budget",
    "shorten",
    "trim",
]
FACTUALITY_KEYWORDS = [
    "factual",
    "factuality",
    "verify",
    "verifiable",
    "hallucination",
    "evidence",
    "inaccurate",
]
SEMANTIC_KEYWORDS = [
    "relevance",
    "semantic",
    "on topic",
    "coherent",
    "clarity",
]
QUALITY_KEYWORDS = [
    "quality",
    "clear",
    "professional",
    "tone",
    "brand",
]

_RUBRIC_KEYWORDS = (
    SAFETY_KEYWORDS
    + BREVITY_KEYWORDS
    + FACTUALITY_KEYWORDS
    + SEMANTIC_KEYWORDS
    + QUALITY_KEYWORDS
)

_WHY_KEYWORDS = [
    "because",
    "so that",
    "therefore",
    "to ensure",
    "to improve",
    "so it",
]

_ISSUE_KEYWORDS = [
    "issue",
    "problem",
    "flaw",
    "violat",
    "missing",
    "incorrect",
    "unsafe",
    "too long",
    "off topic",
]


@dataclass
class CoTScore:
    identified_issues: bool
    explained_fix: bool
    steps_count: int
    cot_bonus: float


def _extract_steps(reasoning: str) -> list[str]:
    steps: list[str] = []
    for line in reasoning.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if stripped.startswith(("-", "*")):
            steps.append(stripped.lstrip("-* "))
            continue
        if lower.startswith("step "):
            steps.append(stripped)
            continue
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".)":
            steps.append(stripped)
    return steps


def _mentions_rubric_dimension(text: str) -> bool:
    return any(keyword in text for keyword in _RUBRIC_KEYWORDS)


def _mentions_issue(text: str) -> bool:
    return any(keyword in text for keyword in _ISSUE_KEYWORDS)


def _explains_why(text: str) -> bool:
    return any(keyword in text for keyword in _WHY_KEYWORDS)


def detect_reasoning_quality(steps: list[str]) -> float:
    if not steps:
        return 0.0

    score = 0.0
    if len(steps) >= 3:
        score += 0.4

    joined = " ".join(step.lower() for step in steps)
    if any(keyword in joined for keyword in _WHY_KEYWORDS):
        score += 0.3
    if _mentions_rubric_dimension(joined):
        score += 0.3

    return min(1.0, score)


def score_reasoning(reasoning: str, action_text: str, rubric_id: str) -> CoTScore:
    _ = (action_text, rubric_id)
    reasoning_text = (reasoning or "").strip().lower()
    steps = _extract_steps(reasoning_text)
    steps_count = len(steps)

    identified_issues = _mentions_issue(reasoning_text)
    explained_fix = _explains_why(reasoning_text)

    cot_bonus = 0.0
    if _mentions_rubric_dimension(reasoning_text):
        cot_bonus += 0.05
    if explained_fix:
        cot_bonus += 0.05
    if steps_count >= 3:
        cot_bonus += 0.05

    cot_bonus = round(min(0.15, cot_bonus), 4)

    return CoTScore(
        identified_issues=identified_issues,
        explained_fix=explained_fix,
        steps_count=steps_count,
        cot_bonus=cot_bonus,
    )
