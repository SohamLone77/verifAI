# COT_REWARD
# MULTIMODAL
# COST_TRACKING
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskName(str, Enum):
    classify = "classify"
    rewrite = "rewrite"
    iterative = "iterative"


class ActionType(str, Enum):
    classify = "classify"
    rewrite = "rewrite"
    submit = "submit"


class Modality(str, Enum):
    text = "text"
    image = "image"
    structured = "structured"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# ---------------------------------------------------------------------------
# Core RL Types
# ---------------------------------------------------------------------------

class Rubric(BaseModel):
    safety: bool = True
    brevity: bool = True
    factuality: bool = True
    semantic: bool = True
    token_budget: Optional[int] = None
    custom_notes: Optional[str] = None


class Observation(BaseModel):
    session_id: str
    task: TaskName
    step: int
    prompt: str
    current_output: str
    rubric: Rubric
    done: bool = False
    score: Optional[float] = None
    # Multimodal extensions
    image_b64: Optional[str] = Field(None, description="Base64-encoded image attached to this turn")
    image_url: Optional[str] = Field(None, description="Public URL of an image attached to this turn")
    structured_output: Optional[dict[str, Any]] = Field(None, description="Structured JSON output from the previous action")


class Action(BaseModel):
    action_type: ActionType
    content: str = Field(..., description="Agent output text or classification value")
    reasoning: Optional[str] = Field(
        None, description="Agent scratchpad or rationale before acting"
    )
    reasoning_steps: Optional[list[str]] = Field(
        None, description="Structured reasoning steps before acting"
    )
    modality: Literal["text", "image", "structured"] = "text"
    image_b64: Optional[str] = Field(None, description="Base64-encoded image supplied by the agent")
    image_url: Optional[str] = Field(None, description="URL of an image supplied by the agent")
    structured_data: Optional[dict[str, Any]] = Field(None, description="Structured JSON payload when modality='structured'")
    metadata: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def _check_modality_payload(self) -> "Action":
        if self.modality == "image" and not (self.image_b64 or self.image_url):
            raise ValueError("Action with modality='image' must supply image_b64 or image_url.")
        if self.modality == "structured" and self.structured_data is None:
            raise ValueError("Action with modality='structured' must supply structured_data.")
        return self


class CostSummary(BaseModel):
    total_usd: float
    tokens_used: int
    hint: Optional[str] = None


class Reward(BaseModel):
    value: float = Field(..., ge=0.0, le=1.0)
    breakdown: dict[str, float] = Field(default_factory=dict)
    step_penalty: float = 0.0
    done_bonus: float = 0.0
    cot_bonus: float = 0.0
    reasoning_quality: Literal["none", "low", "medium", "high"] = "none"
    cost_summary: Optional[CostSummary] = None


class State(BaseModel):
    session_id: str
    task: TaskName
    step: int
    max_steps: int
    done: bool
    total_reward: float
    history: list[dict[str, Any]] = Field(default_factory=list)


class EpisodeInfo(BaseModel):
    session_id: str
    task: TaskName
    total_steps: int
    total_reward: float
    final_score: Optional[float]
    success: bool


# ---------------------------------------------------------------------------
# API Request / Response Wrappers
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    task: TaskName = TaskName.classify   # defaults to 'classify' if not supplied
    scenario_id: Optional[str] = None
    difficulty: Optional[Difficulty] = None


class StepRequest(BaseModel):
    session_id: str
    action: Action


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class GradeRequest(BaseModel):
    prompt: str
    output: str
    rubric: Optional[Rubric] = None


class GradeResponse(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    breakdown: dict[str, float]
    passed: bool


class ValidationResult(BaseModel):
    """Result of structured output schema validation."""
    valid: bool
    errors: list[str] = Field(default_factory=list)
    normalized_text: Optional[str] = None


class TaskInfo(BaseModel):
    name: TaskName
    description: str
    difficulty: Difficulty
    max_steps: int
    action_schema: dict[str, Any]
