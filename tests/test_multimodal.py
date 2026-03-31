# MULTIMODAL
"""
tests/test_multimodal.py

Three test cases covering the multimodal pipeline end-to-end:
  1. text-only action (baseline — no change in behaviour)
  2. image action (URL-based, no API key needed — graceful degradation)
  3. structured JSON action
"""

from __future__ import annotations

import pytest

from app.environment import PromptReviewEnv
from app.models import Action, ActionType, TaskName, ValidationResult
from app.multimodal_processor import (
    normalize_to_text,
    validate_structured_output,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def env() -> PromptReviewEnv:
    return PromptReviewEnv()


# ---------------------------------------------------------------------------
# Test case 1: Text-only action (baseline behaviour)
# ---------------------------------------------------------------------------

class TestTextModality:
    def test_normalize_returns_content_unchanged(self):
        """normalize_to_text on a text action is a simple pass-through."""
        action = Action(
            action_type=ActionType.rewrite,
            content="Machine learning enables systems to learn from data without explicit programming.",
            modality="text",
        )
        result = normalize_to_text(action)
        assert result == action.content

    def test_text_action_env_step(self, env):
        """A text-modality action completes an episode without error."""
        obs, state = env.reset(task_name=TaskName.rewrite)

        action = Action(
            action_type=ActionType.submit,
            content="Machine learning is a branch of AI that enables systems to learn from data.",
            modality="text",
        )
        response = env.step(state=state, obs=obs, action=action)

        assert response.done is True
        assert 0.0 <= response.reward.value <= 1.0
        assert response.info.get("score") is not None
        # Multimodal fields should be None for a text-only action
        assert response.observation.image_b64 is None
        assert response.observation.image_url is None
        assert response.observation.structured_output is None


# ---------------------------------------------------------------------------
# Test case 2: Image modality (URL-based; graceful degradation without API key)
# ---------------------------------------------------------------------------

class TestImageModality:
    def test_normalize_image_url_without_api_key(self, monkeypatch):
        """
        Without GROQ/OPENROUTER key the processor should return a graceful
        placeholder, NOT raise an exception.
        """
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        action = Action(
            action_type=ActionType.rewrite,
            content="Here is a diagram of the architecture.",
            modality="image",
            image_url="https://example.com/diagram.png",
        )
        result = normalize_to_text(action)

        assert "Here is a diagram of the architecture." in result
        assert "[Image" in result  # placeholder or description prefix

    def test_image_action_env_step(self, env, monkeypatch):
        """An image-modality action can complete an episode; score is in [0, 1]."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        obs, state = env.reset(task_name=TaskName.classify)

        action = Action(
            action_type=ActionType.submit,
            content="The diagram shows a neural network with three hidden layers.",
            modality="image",
            image_url="https://example.com/nn_diagram.png",
        )
        response = env.step(state=state, obs=obs, action=action)

        assert response.done is True
        assert 0.0 <= response.reward.value <= 1.0
        # The observation should carry the image_url forward
        assert response.observation.image_url == "https://example.com/nn_diagram.png"

    def test_image_action_requires_payload(self):
        """Creating an image Action without b64 or url should raise ValueError."""
        with pytest.raises(ValueError, match="image_b64 or image_url"):
            Action(
                action_type=ActionType.rewrite,
                content="some text",
                modality="image",
                # deliberately omit image_b64 and image_url
            )


# ---------------------------------------------------------------------------
# Test case 3: Structured JSON modality
# ---------------------------------------------------------------------------

class TestStructuredModality:
    _SCHEMA = {
        "required": ["category", "confidence"],
        "properties": {
            "category": {"type": "string"},
            "confidence": {"type": "number"},
            "explanation": {"type": "string"},
        },
        "additionalProperties": False,
    }

    def test_validate_structured_valid(self):
        """A well-formed structured output should pass validation."""
        output = {
            "category": "factual",
            "confidence": 0.92,
            "explanation": "The response accurately describes the concept.",
        }
        result = validate_structured_output(output, self._SCHEMA)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert result.errors == []
        assert "category: factual" in result.normalized_text
        assert "confidence: 0.92" in result.normalized_text

    def test_validate_structured_missing_required(self):
        """Missing required fields should produce errors and valid=False."""
        output = {"confidence": 0.5}  # missing 'category'
        result = validate_structured_output(output, self._SCHEMA)

        assert result.valid is False
        assert any("category" in e for e in result.errors)

    def test_validate_structured_wrong_type(self):
        """A field with the wrong type should be flagged."""
        output = {
            "category": "factual",
            "confidence": "high",  # should be a number, not a string
        }
        result = validate_structured_output(output, self._SCHEMA)

        assert result.valid is False
        assert any("confidence" in e for e in result.errors)

    def test_validate_structured_extra_field_rejected(self):
        """Extra fields should be flagged when additionalProperties=False."""
        output = {
            "category": "factual",
            "confidence": 0.9,
            "unexpected_key": "oops",
        }
        result = validate_structured_output(output, self._SCHEMA)

        assert result.valid is False
        assert any("unexpected_key" in e for e in result.errors)

    def test_normalize_structured_action(self):
        """normalize_to_text on a structured action returns key: value lines."""
        action = Action(
            action_type=ActionType.submit,
            content="Classification result",
            modality="structured",
            structured_data={
                "category": "factual",
                "confidence": 0.92,
                "explanation": "The response is factually accurate.",
            },
        )
        result = normalize_to_text(action)

        assert "Classification result" in result
        assert "category: factual" in result
        assert "confidence: 0.92" in result

    def test_structured_action_env_step(self, env):
        """A structured-modality action can complete a classify episode."""
        obs, state = env.reset(task_name=TaskName.classify)

        action = Action(
            action_type=ActionType.submit,
            content="",
            modality="structured",
            structured_data={
                "category": "accurate",
                "confidence": 0.95,
                "explanation": (
                    "The AI-generated response is factually accurate, "
                    "concise, and uses appropriate terminology."
                ),
            },
        )
        response = env.step(state=state, obs=obs, action=action)

        assert response.done is True
        assert 0.0 <= response.reward.value <= 1.0
        # structured_output should be propagated to the next observation
        assert response.observation.structured_output is not None
        assert response.observation.structured_output["category"] == "accurate"

    def test_structured_action_requires_data(self):
        """Creating a structured Action without structured_data should raise ValueError."""
        with pytest.raises(ValueError, match="structured_data"):
            Action(
                action_type=ActionType.submit,
                content="result",
                modality="structured",
                # deliberately omit structured_data
            )
