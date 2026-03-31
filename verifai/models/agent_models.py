"""Multi-agent data models for VerifAI"""

from datetime import datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Specialized agent roles"""
    SAFETY = "safety_expert"
    FACTUALITY = "factuality_checker"
    BRAND = "brand_guardian"
    LATENCY = "latency_analyst"
    COMPLIANCE = "compliance_specialist"
    UX = "ux_reviewer"


class AgentStatus(str, Enum):
    """Agent operational status"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    VOTING = "voting"
    COMPLETED = "completed"
    ERROR = "error"


class AgentVote(BaseModel):
    """Individual agent vote"""
    agent_id: str
    agent_name: str
    role: AgentRole
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    flags: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentMetrics(BaseModel):
    """Performance metrics for an agent"""
    total_reviews: int = 0
    average_score: float = 0.0
    average_confidence: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    average_latency_ms: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    improvement_trend: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.now)


class AgentProfile(BaseModel):
    """Agent configuration and profile"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    model: str = "gpt-4"
    version: str = "1.0.0"
    enabled: bool = True
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    custom_rules: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ConsensusConfig(BaseModel):
    """Configuration for consensus mechanism"""
    strategy: Literal[
        "weighted_voting",
        "majority",
        "unanimous",
        "dynamic",
    ] = "weighted_voting"
    require_consensus: bool = False
    disagreement_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    tie_breaker: Literal["safety", "factuality", "confidence"] = "safety"
    escalation_threshold: int = Field(default=2, ge=0)
    human_escalation_required: bool = False


class ConsensusResult(BaseModel):
    """Result of consensus mechanism"""
    consensus_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    final_score: float = Field(ge=0.0, le=1.0)
    final_decision: str
    consensus_reached: bool
    votes: List[AgentVote]
    weighted_score: float
    disagreements: List[Dict[str, Any]]
    resolution_strategy: str
    confidence: float
    requires_escalation: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


class ReviewRequest(BaseModel):
    """Request for multi-agent review"""
    content: str
    context: Optional[Dict[str, Any]] = None
    review_depth: Literal["quick", "standard", "deep"] = "standard"
    required_agents: Optional[List[AgentRole]] = None
    consensus_config: Optional[ConsensusConfig] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReviewResponse(BaseModel):
    """Response from multi-agent review"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consensus: ConsensusResult
    agent_responses: List[AgentVote]
    processing_time_ms: float
    tokens_used: int
    cost: float
    recommendations: List[str]
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentCollaboration(BaseModel):
    """Agent collaboration session"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    agents_involved: List[str]
    iterations: int = 0
    initial_scores: Dict[str, float]
    final_scores: Dict[str, float]
    improvements: Dict[str, float]
    collaboration_log: List[Dict[str, Any]] = Field(default_factory=list)
    duration_seconds: float
    successful: bool


class AgentTrainingData(BaseModel):
    """Training data for agent improvement"""
    episode_id: str
    agent_id: str
    input_content: str
    agent_output: AgentVote
    ground_truth_score: float
    human_feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
