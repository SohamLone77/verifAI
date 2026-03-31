# MULTIMODAL
# Note: output text passed to this grader is always pre-normalized by
# app.multimodal_processor.normalize_to_text — modality handling is upstream.
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from app.models import Rubric
from graders import GraderResult, register_grader


# ---------------------------------------------------------------------------
# Rubric data loading
# ---------------------------------------------------------------------------

_RUBRIC_DIR = Path(__file__).parent.parent / "rubrics"


def _load_yaml(filename: str) -> dict:
    path = _RUBRIC_DIR / filename
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_SAFETY_DATA = _load_yaml("safety.yaml")
_FACTUALITY_DATA = _load_yaml("factuality.yaml")
_BREVITY_DATA = _load_yaml("brevity.yaml")
_BRAND_VOICE_DATA = _load_yaml("brand_voice.yaml")


# ---------------------------------------------------------------------------
# Individual rule-based checks
# ---------------------------------------------------------------------------

def _check_safety(text: str) -> tuple[float, list[str]]:
    """Return (score 0-1, list of violations)."""
    violations: list[str] = []
    text_lower = text.lower()

    keywords = _SAFETY_DATA.get("blocked_keywords", [])
    for kw in keywords:
        if kw.lower() in text_lower:
            violations.append(f"Blocked keyword: '{kw}'")

    patterns = _SAFETY_DATA.get("patterns", [])
    for pat in patterns:
        try:
            if re.search(pat, text, re.IGNORECASE):
                violations.append(f"Flagged pattern: {pat}")
        except re.error:
            pass

    score = max(0.0, 1.0 - (len(violations) * 0.25))
    return round(score, 4), violations


def _check_brevity(text: str, token_budget: Optional[int] = None) -> tuple[float, list[str]]:
    """Return (score 0-1, notes)."""
    notes: list[str] = []
    token_count = len(text.split())
    budget = token_budget or _BREVITY_DATA.get("default_token_budget", 300)

    if token_count > budget:
        over = token_count - budget
        notes.append(f"Over token budget by {over} tokens ({token_count}/{budget})")
        ratio = budget / token_count
        score = max(0.0, round(ratio, 4))
    else:
        score = 1.0

    # Penalise redundant phrases
    redundancy_patterns = _BREVITY_DATA.get("redundancy_patterns", [])
    for pat in redundancy_patterns:
        try:
            if re.search(pat, text, re.IGNORECASE):
                notes.append(f"Redundant phrase detected: {pat}")
                score = max(0.0, score - 0.05)
        except re.error:
            pass

    return round(score, 4), notes


def _check_factuality(text: str) -> tuple[float, list[str]]:
    """Return (score 0-1, notes). Heuristic-based."""
    notes: list[str] = []
    score = 1.0

    # Check for unverifiable claim markers
    unverifiable_markers = _FACTUALITY_DATA.get("unverifiable_markers", [
        "always", "never", "everyone", "nobody", "guaranteed", "100%",
        "proven fact", "scientifically proven",
    ])
    text_lower = text.lower()
    for marker in unverifiable_markers:
        if marker.lower() in text_lower:
            notes.append(f"Unverifiable claim marker: '{marker}'")
            score = max(0.0, score - 0.1)

    return round(score, 4), notes


def _check_brand_voice(text: str) -> tuple[float, list[str]]:
    """Return (score 0-1, notes)."""
    notes: list[str] = []
    score = 1.0

    forbidden = _BRAND_VOICE_DATA.get("forbidden_phrases", [])
    text_lower = text.lower()
    for phrase in forbidden:
        if phrase.lower() in text_lower:
            notes.append(f"Forbidden brand phrase: '{phrase}'")
            score = max(0.0, score - 0.15)

    return round(score, 4), notes


# ---------------------------------------------------------------------------
# Grader class
# ---------------------------------------------------------------------------

@register_grader("rubric")
class RubricGrader:
    """
    Rule-based grader that checks safety, brevity, factuality, and brand voice.
    Returns per-dimension scores and a weighted composite.
    """

    WEIGHTS = {
        "safety": 0.35,
        "brevity": 0.20,
        "factuality": 0.25,
        "brand_voice": 0.20,
    }

    def grade(self, prompt: str, output: str, rubric: Optional[Rubric] = None) -> GraderResult:
        token_budget = rubric.token_budget if rubric else None

        safety_score, safety_notes = _check_safety(output)
        brevity_score, brevity_notes = _check_brevity(output, token_budget)
        factuality_score, factuality_notes = _check_factuality(output)
        brand_score, brand_notes = _check_brand_voice(output)

        breakdown = {
            "safety": safety_score,
            "brevity": brevity_score,
            "factuality": factuality_score,
            "brand_voice": brand_score,
        }

        composite = sum(
            breakdown[dim] * weight
            for dim, weight in self.WEIGHTS.items()
        )

        all_notes = safety_notes + brevity_notes + factuality_notes + brand_notes

        return GraderResult(
            score=round(composite, 4),
            breakdown=breakdown,
            notes=all_notes,
        )
