"""
test_spec.py — OpenEnv spec compliance checks.

Validates that openenv.yaml exists, contains all required keys,
and satisfies the schema expected by OpenEnv.
"""

from pathlib import Path
import pytest
import yaml

SPEC_PATH = Path(__file__).parent.parent / "openenv.yaml"
REQUIRED_TOP_LEVEL_KEYS = {"name", "version", "tasks", "action_schema", "observation_schema"}
REQUIRED_TASK_KEYS = {"name", "description", "difficulty", "max_steps"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
REQUIRED_TASK_NAMES = {"classify", "rewrite", "iterative"}


@pytest.fixture(scope="module")
def spec() -> dict:
    assert SPEC_PATH.exists(), f"openenv.yaml not found at {SPEC_PATH}"
    with open(SPEC_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_spec_file_exists():
    assert SPEC_PATH.exists(), "openenv.yaml must exist in the project root"


def test_spec_top_level_keys(spec):
    missing = REQUIRED_TOP_LEVEL_KEYS - set(spec.keys())
    assert not missing, f"openenv.yaml missing required keys: {missing}"


def test_spec_name_is_string(spec):
    assert isinstance(spec["name"], str) and spec["name"], "spec.name must be a non-empty string"


def test_spec_version_is_string(spec):
    assert isinstance(spec["version"], str), "spec.version must be a string"


def test_spec_tasks_is_list(spec):
    assert isinstance(spec["tasks"], list), "spec.tasks must be a list"
    assert len(spec["tasks"]) >= 1, "spec.tasks must have at least one task"


def test_spec_all_required_tasks_present(spec):
    task_names = {t["name"] for t in spec["tasks"]}
    missing = REQUIRED_TASK_NAMES - task_names
    assert not missing, f"openenv.yaml missing required tasks: {missing}"


def test_spec_each_task_has_required_keys(spec):
    for task in spec["tasks"]:
        missing = REQUIRED_TASK_KEYS - set(task.keys())
        assert not missing, f"Task '{task.get('name', '?')}' missing keys: {missing}"


def test_spec_task_difficulties_valid(spec):
    for task in spec["tasks"]:
        assert task["difficulty"] in VALID_DIFFICULTIES, (
            f"Task '{task['name']}' has invalid difficulty: '{task['difficulty']}'"
        )


def test_spec_task_max_steps_positive(spec):
    for task in spec["tasks"]:
        assert isinstance(task["max_steps"], int) and task["max_steps"] >= 1, (
            f"Task '{task['name']}' max_steps must be a positive integer"
        )


def test_spec_action_schema_has_required_keys(spec):
    schema = spec["action_schema"]
    assert "type" in schema, "action_schema must have 'type'"
    assert "properties" in schema, "action_schema must have 'properties'"
    assert "action_type" in schema["properties"], "action_schema must include 'action_type'"
    assert "content" in schema["properties"], "action_schema must include 'content'"


def test_spec_reward_range_if_present(spec):
    if "reward_range" in spec:
        rr = spec["reward_range"]
        assert len(rr) == 2, "reward_range must be [min, max]"
        assert rr[0] <= rr[1], "reward_range min must be <= max"
