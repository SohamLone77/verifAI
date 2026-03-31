from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import TaskName
from baseline.run_baseline import run_baseline_episode

router = APIRouter()


class BaselineRunRequest(BaseModel):
    task: TaskName
    scenario_id: str | None = None
    model: str = "llama-3.3-70b-versatile"
    api_key: str | None = None  # Optional — falls back to GROQ_API_KEY env var


@router.post("/run")
async def run_baseline(request: BaselineRunRequest):
    """
    Run a full baseline agent loop via Groq for the given task.
    Returns per-step scores, final score, and episode summary.

    You can pass your Groq API key in the request body as `api_key`,
    or set the GROQ_API_KEY environment variable on the server.
    """
    try:
        result = run_baseline_episode(
            task_name=request.task.value,
            scenario_id=request.scenario_id,
            model=request.model,
            api_key=request.api_key,
        )
    except EnvironmentError as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"{e}\n\n"
                "Pass your key in the request body as 'api_key', or set "
                "GROQ_API_KEY as a server environment variable."
            ),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Baseline run failed: {e}")

    return result
