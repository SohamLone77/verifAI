"""
test_environment.py — reset/step/state contract tests.

Verifies that PromptReviewEnv correctly implements the OpenEnv contract:
- reset() returns a valid Observation and State
- step() returns a valid StepResponse with correct types
- State is maintained across multiple steps
- Done flag is set correctly
"""

import pytest

from app.environment import PromptReviewEnv
from app.models import Action, ActionType, Observation, State, StepResponse, TaskName


@pytest.fixture
def env() -> PromptReviewEnv:
    return PromptReviewEnv()


# ---------------------------------------------------------------------------
# reset() tests
# ---------------------------------------------------------------------------

def test_reset_returns_observation_and_state(env):
    obs, state = env.reset(task_name=TaskName.classify)
    assert isinstance(obs, Observation)
    assert isinstance(state, State)


def test_reset_observation_has_required_fields(env):
    obs, _ = env.reset(task_name=TaskName.classify)
    assert obs.session_id
    assert obs.task == TaskName.classify
    assert obs.step == 0
    assert isinstance(obs.prompt, str) and obs.prompt
    assert obs.done is False


def test_reset_state_initial_values(env):
    _, state = env.reset(task_name=TaskName.rewrite)
    assert state.step == 0
    assert state.done is False
    assert state.total_reward == 0.0
    assert state.max_steps > 0


def test_reset_different_tasks(env):
    for task in [TaskName.classify, TaskName.rewrite, TaskName.iterative]:
        obs, state = env.reset(task_name=task)
        assert obs.task == task
        assert state.task == task


def test_reset_with_difficulty(env):
    obs, state = env.reset(task_name=TaskName.rewrite, difficulty="medium")
    assert obs.task == TaskName.rewrite


# ---------------------------------------------------------------------------
# step() tests
# ---------------------------------------------------------------------------

def _make_action(action_type: ActionType = ActionType.rewrite) -> Action:
    return Action(
        action_type=action_type,
        content="This is a well-structured, factually accurate, and concise response.",
    )


def test_step_returns_step_response(env):
    obs, state = env.reset(task_name=TaskName.rewrite)
    action = _make_action()
    response = env.step(state=state, obs=obs, action=action)
    assert isinstance(response, StepResponse)


def test_step_observation_fields(env):
    obs, state = env.reset(task_name=TaskName.rewrite)
    action = _make_action()
    response = env.step(state=state, obs=obs, action=action)
    assert isinstance(response.observation, Observation)
    assert response.observation.step == 1


def test_step_reward_in_range(env):
    obs, state = env.reset(task_name=TaskName.rewrite)
    action = _make_action()
    response = env.step(state=state, obs=obs, action=action)
    assert 0.0 <= response.reward.value <= 1.0


def test_step_done_on_submit(env):
    obs, state = env.reset(task_name=TaskName.rewrite)
    action = Action(action_type=ActionType.submit, content="Final answer here.")
    response = env.step(state=state, obs=obs, action=action)
    assert response.done is True


def test_step_state_updated(env):
    obs, state = env.reset(task_name=TaskName.rewrite)
    assert state.step == 0
    action = _make_action()
    env.step(state=state, obs=obs, action=action)
    assert state.step == 1


def test_step_info_has_score(env):
    obs, state = env.reset(task_name=TaskName.classify)
    action = _make_action(ActionType.classify)
    response = env.step(state=state, obs=obs, action=action)
    assert "score" in response.info
    assert response.info["score"] is not None


def test_multiple_steps_accumulate_reward(env):
    obs, state = env.reset(task_name=TaskName.iterative)
    total = 0.0
    for _ in range(2):
        if state.done:
            break
        action = _make_action()
        response = env.step(state=state, obs=obs, action=action)
        obs = response.observation
        total += response.reward.value
    assert state.total_reward > 0.0


def test_done_at_max_steps(env):
    obs, state = env.reset(task_name=TaskName.classify)
    action = _make_action(ActionType.classify)
    response = env.step(state=state, obs=obs, action=action)
    # classify task has max_steps=1, so done should be True
    assert response.done is True
