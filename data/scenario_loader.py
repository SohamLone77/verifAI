from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

import yaml

_SCENARIOS_PATH = Path(__file__).parent / "scenarios.yaml"

# Cache loaded scenarios
_CACHE: list[dict] = []


def _load_all() -> list[dict]:
    global _CACHE
    if not _CACHE:
        with open(_SCENARIOS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        _CACHE = data.get("scenarios", [])
    return _CACHE


def load_scenarios(difficulty: Optional[str] = None) -> list[dict]:
    """Return all scenarios, optionally filtered by difficulty."""
    all_s = _load_all()
    if difficulty:
        return [s for s in all_s if s.get("difficulty") == difficulty]
    return list(all_s)


def get_scenario(scenario_id: str) -> Optional[dict]:
    """Return a specific scenario by ID, or None if not found."""
    for s in _load_all():
        if s.get("id") == scenario_id:
            return s
    return None


def sample_scenario(
    difficulty: Optional[str] = None,
    scenario_id: Optional[str] = None,
) -> dict:
    """
    Return a single scenario.

    Priority:
    1. If scenario_id is given, return that specific scenario.
    2. If difficulty is given, randomly sample from that difficulty.
    3. Otherwise, randomly sample from all scenarios.
    """
    if scenario_id:
        scenario = get_scenario(scenario_id)
        if scenario:
            return scenario

    pool = load_scenarios(difficulty=difficulty)
    if not pool:
        pool = load_scenarios()  # fallback to all

    return random.choice(pool)
