"""
test_tasks.py — End-to-end task execution tests (without real OpenAI calls).

Verifies:
- All 3 tasks can be instantiated via load_task()
- Each task has required attributes: name, description, difficulty, max_steps, action_schema
- Tasks run end-to-end in the environment without raising exceptions
- Using mock/local actions (no OpenAI API needed)
"""

import pytest

from app.environment import PromptReviewEnv
from app.models import Action, ActionType, TaskName
from tasks import load_task
from tasks.task_classify import ClassifyTask
from tasks.task_rewrite import RewriteTask
from tasks.task_iterative import IterativeTask


# ---------------------------------------------------------------------------
# Task instantiation
# ---------------------------------------------------------------------------

def test_load_task_classify():
    task = load_task(TaskName.classify)
    assert isinstance(task, ClassifyTask)


def test_load_task_rewrite():
    task = load_task(TaskName.rewrite)
    assert isinstance(task, RewriteTask)


def test_load_task_iterative():
    task = load_task(TaskName.iterative)
    assert isinstance(task, IterativeTask)


def test_load_task_invalid():
    with pytest.raises((ValueError, Exception)):
        load_task("nonexistent_task")  # type: ignore


# ---------------------------------------------------------------------------
# Task attribute checks
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("task_name", [TaskName.classify, TaskName.rewrite, TaskName.iterative])
def test_task_has_required_attributes(task_name):
    task = load_task(task_name)
    assert task.name, f"{task_name} must have a name"
    assert task.description, f"{task_name} must have a description"
    assert task.difficulty in {"easy", "medium", "hard"}
    assert isinstance(task.max_steps, int) and task.max_steps >= 1
    assert isinstance(task.action_schema, dict)


def test_classify_is_single_step():
    task = load_task(TaskName.classify)
    assert task.max_steps == 1


def test_rewrite_is_medium_difficulty():
    task = load_task(TaskName.rewrite)
    assert task.difficulty == "medium"
    assert task.max_steps == 3


def test_iterative_is_hard():
    task = load_task(TaskName.iterative)
    assert task.difficulty == "hard"
    assert task.max_steps == 5


# ---------------------------------------------------------------------------
# End-to-end execution (mock agent, no OpenAI)
# ---------------------------------------------------------------------------

MOCK_GOOD_OUTPUT = (
    "This is a clear, factual, and concise response that addresses the prompt directly "
    "without using excessive words or making unverifiable claims."
)


@pytest.fixture
def env() -> PromptReviewEnv:
    return PromptReviewEnv()


def _run_episode(env: PromptReviewEnv, task_name: TaskName, action_type: ActionType) -> dict:
    """Run a full episode with a fixed mock action."""
    obs, state = env.reset(task_name=task_name)
    total_reward = 0.0
    final_score = None

    while not state.done:
        at = action_type
        if state.step >= state.max_steps - 1:
            at = ActionType.submit
        action = Action(action_type=at, content=MOCK_GOOD_OUTPUT)
        response = env.step(state=state, obs=obs, action=action)
        obs = response.observation
        total_reward += response.reward.value
        final_score = response.info.get("score")

    return {"total_reward": total_reward, "final_score": final_score, "done": state.done}


def test_classify_task_end_to_end(env):
    result = _run_episode(env, TaskName.classify, ActionType.classify)
    assert result["done"] is True
    assert result["final_score"] is not None
    assert 0.0 <= result["final_score"] <= 1.0


def test_rewrite_task_end_to_end(env):
    result = _run_episode(env, TaskName.rewrite, ActionType.rewrite)
    assert result["done"] is True
    assert result["final_score"] is not None
    assert 0.0 <= result["final_score"] <= 1.0


def test_iterative_task_end_to_end(env):
    result = _run_episode(env, TaskName.iterative, ActionType.rewrite)
    assert result["done"] is True
    assert result["total_reward"] >= 0.0


def test_all_tasks_complete_without_exception(env):
    """Smoke test: all tasks run without raising any exceptions."""
    for task_name, action_type in [
        (TaskName.classify, ActionType.classify),
        (TaskName.rewrite, ActionType.rewrite),
        (TaskName.iterative, ActionType.rewrite),
    ]:
        result = _run_episode(env, task_name, action_type)
        assert result["done"] is True
