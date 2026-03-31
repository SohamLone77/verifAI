# MULTI_AGENT
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.panel_orchestrator import PanelCompareResult, PanelOrchestrator, PanelResult
from app.models import TaskName
from app.session import session_store
from verifai.agents.multi_agent_panel import MultiAgentPanel
from verifai.models.agent_models import (
    AgentRole,
    ConsensusConfig,
    ReviewRequest,
    ReviewResponse,
)

router = APIRouter()
_orchestrator = PanelOrchestrator()


class PanelStepRequest(BaseModel):
    session_id: str
    task_id: TaskName


class MultiAgentReviewRequest(BaseModel):
    content: str
    context: Optional[Dict[str, Any]] = None
    review_depth: Literal["quick", "standard", "deep"] = "standard"
    strategy: Literal["weighted_voting", "majority", "unanimous", "dynamic"] = "weighted_voting"
    required_agents: Optional[List[AgentRole]] = None


@router.post("/panel/step", response_model=PanelResult)
async def panel_step(request: PanelStepRequest):
    session = session_store.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if request.task_id != TaskName.iterative or session.state.task != TaskName.iterative:
        raise HTTPException(
            status_code=422,
            detail="Panel orchestration is only supported for iterative tasks.",
        )

    try:
        return await _orchestrator.run_panel(request.session_id, session.obs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/panel/compare", response_model=PanelCompareResult)
async def panel_compare(session_id: str):
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.state.task != TaskName.iterative:
        raise HTTPException(
            status_code=422,
            detail="Panel orchestration is only supported for iterative tasks.",
        )

    try:
        return await _orchestrator.compare(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/panel/review", response_model=ReviewResponse)
async def panel_review(request: MultiAgentReviewRequest):
    config = ConsensusConfig(strategy=request.strategy)
    review_request = ReviewRequest(
        content=request.content,
        context=request.context,
        review_depth=request.review_depth,
        required_agents=request.required_agents,
        consensus_config=config,
    )
    panel = MultiAgentPanel(config)

    try:
        return panel.review(review_request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
