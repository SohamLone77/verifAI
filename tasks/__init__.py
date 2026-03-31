from __future__ import annotations

from app.models import TaskName


class BaseTask:
    """Abstract base for all tasks."""

    name: str = ""
    description: str = ""
    difficulty: str = "easy"
    max_steps: int = 1

    action_schema: dict = {
        "type": "object",
        "required": ["action_type", "content"],
        "properties": {
            "action_type": {"type": "string"},
            "content": {"type": "string"},
        },
    }


def load_task(name: TaskName) -> BaseTask:
    """Factory: return the task class matching the given name."""
    from tasks.task_classify import ClassifyTask
    from tasks.task_rewrite import RewriteTask
    from tasks.task_iterative import IterativeTask

    registry: dict[str, type[BaseTask]] = {
        "classify": ClassifyTask,
        "rewrite": RewriteTask,
        "iterative": IterativeTask,
    }

    key = name.value if hasattr(name, "value") else name
    if key not in registry:
        raise ValueError(f"Unknown task: '{key}'. Available: {list(registry.keys())}")

    return registry[key]()
