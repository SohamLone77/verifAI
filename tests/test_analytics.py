# ANALYTICS
from __future__ import annotations

from app.analytics import AnalyticsStore, EpisodeRecord, HUMAN_REVIEW_COST_USD


def test_roi_formula():
    store = AnalyticsStore()
    store.append_episode(
        EpisodeRecord(
            session_id="s1",
            task_id="rewrite",
            score=0.8,
            cost_usd=0.05,
            steps=2,
            timestamp="2026-03-29T00:00:00",
        )
    )
    store.append_episode(
        EpisodeRecord(
            session_id="s2",
            task_id="rewrite",
            score=0.6,
            cost_usd=0.03,
            steps=3,
            timestamp="2026-03-29T00:01:00",
        )
    )

    summary = store.get_summary()
    expected_cost_saved = (2 * HUMAN_REVIEW_COST_USD) - 0.08
    assert summary.cost_saved == round(expected_cost_saved, 4)


def test_summary_by_task_aggregation():
    store = AnalyticsStore()
    store.append_episode(
        EpisodeRecord(
            session_id="s1",
            task_id="classify",
            score=0.9,
            cost_usd=0.02,
            steps=1,
            timestamp="2026-03-29T00:00:00",
        )
    )
    store.append_episode(
        EpisodeRecord(
            session_id="s2",
            task_id="classify",
            score=0.7,
            cost_usd=0.03,
            steps=2,
            timestamp="2026-03-29T00:01:00",
        )
    )
    store.append_episode(
        EpisodeRecord(
            session_id="s3",
            task_id="rewrite",
            score=0.5,
            cost_usd=0.04,
            steps=3,
            timestamp="2026-03-29T00:02:00",
        )
    )

    summary = store.get_summary()
    assert summary.total_episodes == 3
    assert summary.by_task["classify"]["count"] == 2
    assert summary.by_task["rewrite"]["count"] == 1
    assert summary.by_task["classify"]["avg_steps"] == 1.5
    assert summary.by_task["classify"]["total_cost"] == 0.05
