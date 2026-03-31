"""Chain-of-Thought reasoning data models for VerifAI"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import BaseModel, Field


class ReasoningStepType(str, Enum):
    """Types of reasoning steps"""
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    HYPOTHESIS = "hypothesis"
    VERIFICATION = "verification"
    SYNTHESIS = "synthesis"
    DECISION = "decision"
    EXPLANATION = "explanation"
    COUNTERFACTUAL = "counterfactual"
    UNCERTAINTY = "uncertainty"


class EvidenceType(str, Enum):
    """Types of evidence"""
    FACT = "fact"
    DATA = "data"
    RULE = "rule"
    EXAMPLE = "example"
    CONTRADICTION = "contradiction"
    INFERENCE = "inference"
    SOURCE = "source"


class Evidence(BaseModel):
    """Evidence supporting a reasoning step"""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EvidenceType
    content: str
    source: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningStep(BaseModel):
    """Individual reasoning step"""
    step_id: int
    step_type: ReasoningStepType
    input: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    alternatives_considered: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "input": self.input,
            "reasoning": self.reasoning,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "evidence": [e.dict() for e in self.evidence],
            "alternatives_considered": self.alternatives_considered,
            "assumptions": self.assumptions,
            "timestamp": self.timestamp.isoformat(),
        }


class Contradiction(BaseModel):
    """Detected contradiction in reasoning"""
    contradiction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_a_id: int
    step_b_id: int
    statement_a: str
    statement_b: str
    contradiction_type: Literal["direct", "logical", "temporal", "causal"]
    severity: float = Field(ge=0.0, le=1.0)
    resolution: Optional[str] = None
    resolved: bool = False


class ReasoningChain(BaseModel):
    """Complete reasoning chain"""
    chain_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    context: Dict[str, Any] = Field(default_factory=dict)
    steps: List[ReasoningStep] = Field(default_factory=list)
    final_decision: str = ""
    final_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    contradictions: List[Contradiction] = Field(default_factory=list)
    consistency_score: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_step(self, step: ReasoningStep) -> None:
        """Add a step to the reasoning chain"""
        self.steps.append(step)
        self.updated_at = datetime.now()

    def add_contradiction(self, contradiction: Contradiction) -> None:
        """Add a contradiction to the chain"""
        self.contradictions.append(contradiction)
        self.updated_at = datetime.now()

    def get_step(self, step_id: int) -> Optional[ReasoningStep]:
        """Get a step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_latest_step(self) -> Optional[ReasoningStep]:
        """Get the most recent step"""
        if self.steps:
            return self.steps[-1]
        return None

    def to_markdown(self) -> str:
        """Convert reasoning chain to markdown format"""
        lines = []
        lines.append(f"# Reasoning Chain: {self.chain_id[:8]}")
        lines.append(f"\n**Query:** {self.query}")
        lines.append(f"**Final Decision:** {self.final_decision}")
        lines.append(f"**Confidence:** {self.final_confidence:.2f}")
        lines.append(f"**Consistency:** {self.consistency_score:.2f}")
        lines.append(f"**Quality:** {self.reasoning_quality:.2f}")

        lines.append("\n## Reasoning Steps")
        for step in self.steps:
            lines.append(f"\n### Step {step.step_id}: {step.step_type.value.upper()}")
            lines.append(f"**Reasoning:** {step.reasoning}")
            lines.append(f"**Conclusion:** {step.conclusion}")
            lines.append(f"**Confidence:** {step.confidence:.2f}")
            if step.evidence:
                lines.append("**Evidence:**")
                for ev in step.evidence:
                    lines.append(f"- {ev.content} (confidence: {ev.confidence:.2f})")
            if step.alternatives_considered:
                lines.append(
                    f"**Alternatives:** {', '.join(step.alternatives_considered)}"
                )

        if self.contradictions:
            lines.append("\n## Contradictions Detected")
            for contra in self.contradictions:
                lines.append(f"\n- Step {contra.step_a_id} vs Step {contra.step_b_id}")
                lines.append(f"  - Statement A: {contra.statement_a}")
                lines.append(f"  - Statement B: {contra.statement_b}")
                lines.append(f"  - Resolution: {contra.resolution or 'Pending'}")

        lines.append("\n## Explanation")
        lines.append(self.explanation)

        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "chain_id": self.chain_id,
            "query": self.query,
            "context": self.context,
            "steps": [s.to_dict() for s in self.steps],
            "final_decision": self.final_decision,
            "final_confidence": self.final_confidence,
            "contradictions": [c.dict() for c in self.contradictions],
            "consistency_score": self.consistency_score,
            "reasoning_quality": self.reasoning_quality,
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ReasoningRequest(BaseModel):
    """Request for reasoning on a query"""
    query: str
    context: Optional[Dict[str, Any]] = None
    max_steps: int = Field(default=10, ge=1, le=50)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_alternatives: bool = Field(default=True)
    detect_contradictions: bool = Field(default=True)
    reasoning_depth: Literal["shallow", "medium", "deep"] = "medium"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningResponse(BaseModel):
    """Response from reasoning engine"""
    reasoning_chain: Optional[ReasoningChain] = None
    confidence: float
    processing_time_ms: float
    tokens_used: int
    success: bool
    error: Optional[str] = None


class ReasoningQualityMetrics(BaseModel):
    """Quality metrics for reasoning"""
    logical_consistency: float
    evidence_support: float
    completeness: float
    clarity: float
    conciseness: float
    overall_score: float
    issues: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)


class ReasoningReward(BaseModel):
    """Reward for reasoning quality"""
    base_reward: float
    consistency_bonus: float
    evidence_bonus: float
    clarity_bonus: float
    contradiction_penalty: float
    total_reward: float
    details: Dict[str, Any] = Field(default_factory=dict)


class ReasonedAction(BaseModel):
    """Action with reasoning attached"""
    action_type: Literal["reasoned"] = "reasoned"
    reasoning_chain: ReasoningChain
    actual_action: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
