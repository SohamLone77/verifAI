from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models import TaskInfo, TaskName
from tasks import load_task

router = APIRouter()

_TASK_NAMES = [t.value for t in TaskName]


@router.get("", response_model=list[TaskInfo])
async def list_tasks():
    """List all available tasks with descriptions and difficulty."""
    result = []
    for name in _TASK_NAMES:
        task = load_task(TaskName(name))
        result.append(
            TaskInfo(
                name=TaskName(name),
                description=task.description,
                difficulty=task.difficulty,
                max_steps=task.max_steps,
                action_schema=task.action_schema,
            )
        )
    return result


@router.get("/{name}/schema")
async def task_schema(name: str):
    """Return the action schema for a given task."""
    if name not in _TASK_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{name}' not found. Available: {_TASK_NAMES}",
        )
    task = load_task(TaskName(name))
    return {
        "task": name,
        "difficulty": task.difficulty,
        "max_steps": task.max_steps,
        "action_schema": task.action_schema,
    }
