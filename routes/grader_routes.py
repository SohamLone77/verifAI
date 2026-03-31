# COST_TRACKING
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app.models import GradeRequest, GradeResponse
from app.session import session_store
from graders.composite_grader import CompositeGrader

router = APIRouter()
_grader = CompositeGrader()


@router.post("/grade", response_model=GradeResponse)
async def grade(request: GradeRequest):
    """
    Score an output against a prompt (and optional rubric).
    Returns composite score, per-dimension breakdown, and pass/fail.
    """
    if not request.output or not request.output.strip():
        raise HTTPException(status_code=422, detail="Output text cannot be empty.")

    try:
        result = _grader.grade(
            prompt=request.prompt,
            output=request.output,
            rubric=request.rubric,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grading failed: {e}")

    return GradeResponse(
        score=result.score,
        breakdown=result.breakdown,
        passed=result.passed,
    )


@router.get("/cost/{session_id}")
async def get_cost(session_id: str):
    """Return the cost report for a given session."""
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    report = session.cost_tracker.get_episode_cost(session_id=session_id)
    return asdict(report)
