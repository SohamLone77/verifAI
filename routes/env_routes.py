# COST_TRACKING
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.environment import PromptReviewEnv
from app.models import ResetRequest, State, StepRequest, StepResponse
from app.session import session_store

router = APIRouter()
_env = PromptReviewEnv()


@router.post("/reset", response_model=dict)
async def reset(request: ResetRequest):
    """
    Start a new episode for the given task.
    Returns the initial observation and a session_id for subsequent steps.
    """
    session_id = str(uuid.uuid4())

    try:
        obs, state = _env.reset(
            task_name=request.task,
            session_id=session_id,
            scenario_id=request.scenario_id,
            difficulty=request.difficulty.value if request.difficulty else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

    session_store.create(session_id, state, obs)

    return {
        "session_id": session_id,
        "observation": obs.model_dump(),
        "message": f"Episode started. Task: {request.task.value}",
    }


@router.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    """
    Submit an action for the current episode.
    Returns the next observation, shaped reward, and done flag.
    """
    session = session_store.get(request.session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{request.session_id}' not found. Call /reset first.",
        )

    state: State = session.state
    obs = session.obs

    if state.done:
        raise HTTPException(
            status_code=409,
            detail="Episode is already finished. Call /reset to start a new episode.",
        )

    try:
        response = _env.step(state=state, obs=obs, action=request.action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {e}")

    # Persist updated state
    session_store.update(request.session_id, state, response.observation)

    return response


@router.get("/status/{session_id}")
async def status(session_id: str):
    """Return the current state of an active session."""
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    state: State = session.state
    return {
        "session_id": session_id,
        "task": state.task,
        "step": state.step,
        "max_steps": state.max_steps,
        "done": state.done,
        "total_reward": state.total_reward,
    }
