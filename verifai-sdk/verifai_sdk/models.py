"""Data models for VerifAI SDK"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from enum import Enum


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks"""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    FDA = "fda"
    SOC2 = "soc2"
    PCI = "pci"
    CCPA = "ccpa"


class AgentRole(str, Enum):
    """Multi-agent roles"""
    SAFETY = "safety_expert"
    FACTUALITY = "factuality_checker"
    BRAND = "brand_guardian"
    LATENCY = "latency_analyst"
    COMPLIANCE = "compliance_specialist"


@dataclass
class Issue:
    """Detected issue in content"""
    type: str  # safety, factuality, brand, latency, compliance
    severity: float  # 0.0 to 1.0
    description: str
    location: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 0.8


@dataclass
class RubricDimension:
    """Rubric dimension for quality assessment"""
    name: str
    score: float = 0.0
    weight: float = 1.0
    threshold: float = 0.7


@dataclass
class AgentVote:
    """Vote from a specialized agent"""
    agent_name: str
    role: AgentRole
    score: float
    confidence: float
    reasoning: str
    agent_id: Optional[str] = None
    flags: List[Issue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: Optional[datetime] = None


@dataclass
class ReviewResult:
    """Result of a single review"""
    id: str
    original_output: str
    score: float
    flags: List[Issue]
    rubric_scores: Dict[str, float]
    compliance_results: Optional[Dict[str, Any]] = None
    multi_agent_results: Optional[List[AgentVote]] = None
    cost: float = 0.0
    latency_ms: float = 0.0
    tokens_used: int = 0
    model_used: str = "gpt-4"
    reasoning_chain: Optional[List[str]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImprovedOutput:
    """Result of output improvement"""
    original: str
    improved: str
    improvement_delta: float
    iterations: int
    final_score: float
    changes_made: List[str] = field(default_factory=list)
    cost: float = 0.0
    processing_time_ms: float = 0.0


@dataclass
class BatchResult:
    """Result of batch review"""
    total_items: int
    successful_items: int
    failed_items: int
    results: List[ReviewResult]
    errors: List[Dict[str, Any]]
    average_score: float
    total_cost: float
    total_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceResult:
    """Result of compliance check"""
    framework: ComplianceFramework
    score: float
    violations: List[Issue]
    remediation: List[str]
    risk_level: Literal["low", "medium", "high", "critical"]
    confidence: float


@dataclass
class MultiAgentResult:
    """Result from multi-agent review"""
    consensus_decision: str
    final_score: float
    consensus_reached: bool
    agent_votes: List[AgentVote]
    disagreements: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    processing_time_ms: float
    cost: float


@dataclass
class CostBreakdown:
    """Detailed cost breakdown"""
    by_model: Dict[str, float]
    by_agent: Dict[str, float]
    by_task: Dict[str, float]
    total_cost: float
    average_cost_per_review: float


@dataclass
class CostReport:
    """Cost tracking report"""
    period_days: int
    total_cost: float
    total_reviews: int
    average_cost: float
    breakdown: CostBreakdown
    efficiency_score: float
    optimization_suggestions: List[str]
    budget_status: Dict[str, Any]


@dataclass
class ROIResult:
    """ROI calculation result"""
    annual_savings: float
    labor_savings: float
    error_savings: float
    brand_savings: float
    compliance_savings: float
    productivity_savings: float
    verifai_cost: float
    net_profit: float
    roi_percentage: float
    payback_days: int
    five_year_savings: float
    recommendations: List[str]


@dataclass
class ReviewConfig:
    """Configuration for review"""
    rubric: Optional[List[str]] = None
    compliance: Optional[ComplianceFramework] = None
    multi_agent: bool = False
    agents: Optional[List[AgentRole]] = None
    depth: Literal["quick", "standard", "deep"] = "standard"
    include_reasoning: bool = False
    max_tokens: Optional[int] = None
    temperature: float = 0.0


@dataclass
class ClientConfig:
    """Client configuration"""
    api_key: Optional[str] = None
    base_url: str = "https://api.verifai.ai"
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 1.0
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    log_level: str = "INFO"
