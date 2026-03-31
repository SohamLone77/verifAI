# MULTI_AGENT
from __future__ import annotations

import asyncio

import pytest

from app.agents.panel_orchestrator import PanelOrchestrator
from app.environment import PromptReviewEnv
from app.models import Action, ActionType, TaskName
from app.session import session_store


@pytest.mark.asyncio
async def test_panel_orchestration_order_and_score(monkeypatch):
    env = PromptReviewEnv()
    obs, state = env.reset(task_name=TaskName.iterative)
    session_id = "panel-session"
    session_store.create(session_id, state, obs)

    orchestrator = PanelOrchestrator(env=env)

    order: list[str] = []
    safety_ready = asyncio.Event()
    factuality_ready = asyncio.Event()

    async def mock_safety_run(observation):
        order.append("safety")
        safety_ready.set()
        return Action(
            action_type=ActionType.rewrite,
            content="Safety feedback: remove harmful phrasing.",
            metadata={
                "agent": "SafetyAgent",
                "rubric_focus": ["safety"],
                "usage": {"model": "gpt-4o-mini", "prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    async def mock_factuality_run(observation):
        order.append("factuality")
        factuality_ready.set()
        return Action(
            action_type=ActionType.rewrite,
            content="Factuality feedback: remove unverifiable claims.",
            metadata={
                "agent": "FactualityAgent",
                "rubric_focus": ["factuality"],
                "usage": {"model": "gpt-4o-mini", "prompt_tokens": 12, "completion_tokens": 6},
            },
        )

    async def mock_rewriter_run(observation, feedback):
        assert safety_ready.is_set()
        assert factuality_ready.is_set()
        order.append("rewriter")
        return Action(
            action_type=ActionType.rewrite,
            content="Final rewrite applying both fixes.",
            metadata={
                "agent": "RewriterAgent",
                "rubric_focus": ["safety", "factuality", "brevity", "quality"],
                "usage": {"model": "gpt-4o-mini", "prompt_tokens": 14, "completion_tokens": 7},
            },
        )

    monkeypatch.setattr(orchestrator._safety_agent, "run", mock_safety_run)
    monkeypatch.setattr(orchestrator._factuality_agent, "run", mock_factuality_run)
    monkeypatch.setattr(orchestrator._rewriter_agent, "run_with_feedback", mock_rewriter_run)

    result = await orchestrator.run_panel(session_id, obs)

    assert "rewriter" in order
    assert set(order[:2]) == {"safety", "factuality"}
    assert order[-1] == "rewriter"

    assert len(result.individual_actions) == 3
    assert len(result.individual_scores) == 3
    assert 0.0 <= result.final_score <= 1.0
    assert result.final_score == result.individual_scores[-1]
    assert result.panel_cost_usd >= 0.0
