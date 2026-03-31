# COST_TRACKING
from __future__ import annotations

import pytest

from reward.cost_tracker import CostTracker


def test_cost_tracker_accumulates_prompt_and_completion_tokens():
    tracker = CostTracker()
    tracker.track("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    tracker.track("gpt-4o", prompt_tokens=2000, completion_tokens=0)

    report = tracker.get_episode_cost(session_id="session-1")

    assert report.total_prompt_tokens == 3000
    assert report.total_completion_tokens == 500
    assert report.total_tokens == 3500

    expected_cost = (1000 * 5.0 / 1_000_000) + (500 * 15.0 / 1_000_000) + (2000 * 5.0 / 1_000_000)
    assert report.total_usd == pytest.approx(expected_cost)


def test_cost_tracker_unknown_model_has_zero_cost():
    tracker = CostTracker()
    tracker.track("unknown-model", prompt_tokens=123, completion_tokens=456)

    report = tracker.get_episode_cost(session_id="session-2")

    assert report.total_tokens == 579
    assert report.total_usd == pytest.approx(0.0)
