"""Cost tracking data models for VerifAI"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, validator


class ModelTier(str, Enum):
    """Model pricing tiers"""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"


class ModelPricing(BaseModel):
    """Pricing structure for a model"""
    input_price_per_1k: float = Field(ge=0.0, description="Price per 1,000 input tokens")
    output_price_per_1k: float = Field(ge=0.0, description="Price per 1,000 output tokens")
    tier: ModelTier
    description: Optional[str] = None
    recommended_for: List[str] = Field(default_factory=list)


class CostEventType(str, Enum):
    """Types of cost events"""
    REVIEW = "review"
    REWRITE = "rewrite"
    APPROVAL = "approval"
    SUGGESTION = "suggestion"
    BATCH = "batch"
    RETRY = "retry"
    CACHE_MISS = "cache_miss"


class CostEvent(BaseModel):
    """Record of a single cost event"""
    event_id: str
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: CostEventType
    cost: float = Field(ge=0.0)
    quality_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    episode_id: Optional[int] = None
    task_id: Optional[int] = None
    latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BudgetAlertLevel(str, Enum):
    """Budget alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


class BudgetAlert(BaseModel):
    """Budget alert notification"""
    alert_id: str
    level: BudgetAlertLevel
    current_cost: float
    budget_limit: float
    percentage_used: float
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    recommended_action: Optional[str] = None


class CostBreakdown(BaseModel):
    """Breakdown of costs by category"""
    by_event_type: Dict[str, float] = Field(default_factory=dict)
    by_model: Dict[str, float] = Field(default_factory=dict)
    by_task: Dict[int, float] = Field(default_factory=dict)
    by_episode: Dict[int, float] = Field(default_factory=dict)


class CostSummary(BaseModel):
    """Summary of cost metrics"""
    total_cost: float
    average_cost_per_review: float
    total_tokens_processed: int
    total_api_calls: int
    cost_efficiency_score: float
    budget_remaining: float
    budget_usage_percentage: float
    alert_count: int
    time_range_days: int
    timestamp: datetime = Field(default_factory=datetime.now)


class OptimizationSuggestion(BaseModel):
    """Cost optimization suggestion"""
    suggestion_id: str
    type: Literal[
        "model_optimization",
        "batch_processing",
        "caching",
        "token_optimization",
        "request_consolidation",
        "retry_optimization",
    ]
    title: str
    description: str
    estimated_savings: float
    estimated_quality_impact: float = Field(ge=-1.0, le=1.0)
    implementation_difficulty: Literal["easy", "medium", "hard"]
    priority: Literal["low", "medium", "high"]
    action_items: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class OptimizationReport(BaseModel):
    """Complete optimization report"""
    report_id: str
    current_costs: CostSummary
    projected_costs: CostSummary
    total_savings: float
    savings_percentage: float
    quality_impact: float
    suggestions: List[OptimizationSuggestion]
    implemented_changes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    generated_by: str = "VerifAI Cost Optimizer"


class BudgetConfig(BaseModel):
    """Budget configuration"""
    daily_budget: Optional[float] = None
    weekly_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    per_episode_budget: Optional[float] = None
    alert_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    critical_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    auto_optimize: bool = Field(default=False)
    max_cost_per_request: float = Field(default=0.10, ge=0.0)


class ModelPricingConfig(BaseModel):
    """Configuration for model pricing"""
    models: Dict[str, ModelPricing] = Field(default_factory=dict)
    default_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"

    @validator("models")
    def validate_models(cls, v):
        """Ensure required models exist"""
        required = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        for model in required:
            if model not in v:
                raise ValueError(f"Required model {model} not in pricing config")
        return v


class CostAnalytics(BaseModel):
    """Analytics data for cost visualization"""
    daily_costs: List[Dict[str, Any]] = Field(default_factory=list)
    weekly_trend: List[float] = Field(default_factory=list)
    cost_performance_ratio: float
    roi_estimate: float
    optimization_potential: float
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# Default Pricing Configuration
# ============================================================================

DEFAULT_MODEL_PRICING: Dict[str, ModelPricing] = {
    "gpt-4": ModelPricing(
        input_price_per_1k=0.03,
        output_price_per_1k=0.06,
        tier=ModelTier.PREMIUM,
        description="Best quality, highest cost",
        recommended_for=["critical reviews", "compliance", "safety-critical"],
    ),
    "gpt-4-turbo": ModelPricing(
        input_price_per_1k=0.01,
        output_price_per_1k=0.03,
        tier=ModelTier.STANDARD,
        description="Good quality, moderate cost",
        recommended_for=["standard reviews", "rewrites"],
    ),
    "gpt-3.5-turbo": ModelPricing(
        input_price_per_1k=0.001,
        output_price_per_1k=0.002,
        tier=ModelTier.ECONOMY,
        description="Lower quality, very low cost",
        recommended_for=["batch reviews", "pre-filtering"],
    ),
    "claude-3-opus": ModelPricing(
        input_price_per_1k=0.015,
        output_price_per_1k=0.075,
        tier=ModelTier.PREMIUM,
        description="Anthropic best model",
        recommended_for=["safety reviews", "complex analysis"],
    ),
    "claude-3-sonnet": ModelPricing(
        input_price_per_1k=0.003,
        output_price_per_1k=0.015,
        tier=ModelTier.STANDARD,
        description="Good balance of quality and cost",
        recommended_for=["general reviews"],
    ),
    "gemini-pro": ModelPricing(
        input_price_per_1k=0.0005,
        output_price_per_1k=0.0015,
        tier=ModelTier.ECONOMY,
        description="Google economical option",
        recommended_for=["high volume", "non-critical"],
    ),
    "llama-3-70b": ModelPricing(
        input_price_per_1k=0.0001,
        output_price_per_1k=0.0002,
        tier=ModelTier.ECONOMY,
        description="Open source, very low cost",
        recommended_for=["batch processing", "pre-screening"],
    ),
}
