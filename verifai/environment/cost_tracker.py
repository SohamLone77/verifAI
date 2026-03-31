"""Cost tracking and optimization for VerifAI"""

import hashlib
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from verifai.models.cost_models import (
    BudgetAlert,
    BudgetAlertLevel,
    BudgetConfig,
    CostBreakdown,
    CostEvent,
    CostEventType,
    CostSummary,
    DEFAULT_MODEL_PRICING,
    ModelPricingConfig,
)


class CostTracker:
    """
    Track and optimize API costs for VerifAI operations.

    Features:
    - Track costs per model, task, episode
    - Budget monitoring and alerts
    - Cost efficiency scoring
    - Optimization suggestions
    """

    def __init__(
        self,
        budget_config: Optional[BudgetConfig] = None,
        pricing_config: Optional[ModelPricingConfig] = None,
        enable_persistence: bool = False,
    ):
        self.budget_config = budget_config or BudgetConfig()
        self.pricing_config = pricing_config or ModelPricingConfig(
            models=DEFAULT_MODEL_PRICING
        )
        self.enable_persistence = enable_persistence

        self.events: List[CostEvent] = []
        self.alerts: List[BudgetAlert] = []
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self._episode_costs: Dict[int, float] = defaultdict(float)

        # Performance metrics
        self._total_latency_ms: float = 0.0
        self._total_tokens: int = 0
        self._quality_scores: List[float] = []

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost for a single API call"""
        pricing = self.pricing_config.models.get(model)
        if not pricing:
            pricing = self.pricing_config.models.get(
                self.pricing_config.default_model,
                DEFAULT_MODEL_PRICING["gpt-4"],
            )

        cost = (
            (input_tokens * pricing.input_price_per_1k)
            + (output_tokens * pricing.output_price_per_1k)
        ) / 1000

        return round(cost, 6)

    def log_event(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        event_type: CostEventType,
        episode_id: Optional[int] = None,
        task_id: Optional[int] = None,
        quality_impact: float = 0.0,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEvent:
        """Log a cost event and return the event"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        event = CostEvent(
            event_id=str(uuid.uuid4()),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            event_type=event_type,
            cost=cost,
            quality_impact=quality_impact,
            episode_id=episode_id,
            task_id=task_id,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        self.events.append(event)

        if episode_id is not None:
            self._episode_costs[episode_id] += cost

        if latency_ms:
            self._total_latency_ms += latency_ms

        self._total_tokens += input_tokens + output_tokens

        self._check_budget()

        return event

    def log_cache_hit(self) -> None:
        """Log a cache hit"""
        self.cache_hits += 1

    def log_cache_miss(self) -> None:
        """Log a cache miss"""
        self.cache_misses += 1

    def record_quality(self, score: float) -> None:
        """Record quality score for efficiency calculation"""
        self._quality_scores.append(score)

    def total_cost(self, time_range_days: Optional[int] = None) -> float:
        """Calculate total cost across all events"""
        events = self._filter_by_time_range(time_range_days)
        return sum(e.cost for e in events)

    def cost_by_event_type(self, time_range_days: Optional[int] = None) -> Dict[str, float]:
        """Break down costs by event type"""
        events = self._filter_by_time_range(time_range_days)
        breakdown: Dict[str, float] = defaultdict(float)
        for event in events:
            breakdown[event.event_type.value] += event.cost
        return dict(breakdown)

    def cost_by_model(self, time_range_days: Optional[int] = None) -> Dict[str, float]:
        """Break down costs by model"""
        events = self._filter_by_time_range(time_range_days)
        breakdown: Dict[str, float] = defaultdict(float)
        for event in events:
            breakdown[event.model] += event.cost
        return dict(breakdown)

    def cost_by_task(self, time_range_days: Optional[int] = None) -> Dict[int, float]:
        """Break down costs by task"""
        events = self._filter_by_time_range(time_range_days)
        breakdown: Dict[int, float] = defaultdict(float)
        for event in events:
            if event.task_id is not None:
                breakdown[event.task_id] += event.cost
        return dict(breakdown)

    def average_cost_per_review(self, time_range_days: Optional[int] = None) -> float:
        """Calculate average cost per review"""
        events = self._filter_by_time_range(time_range_days)
        review_events = [e for e in events if e.event_type == CostEventType.REVIEW]
        if not review_events:
            return 0.0
        return sum(e.cost for e in review_events) / len(review_events)

    def efficiency_score(self) -> float:
        """
        Calculate cost efficiency (quality per dollar).
        Higher is better: 1.0 = perfect efficiency.
        """
        total = self.total_cost()
        if total == 0:
            return 1.0

        avg_quality = np.mean(self._quality_scores) if self._quality_scores else 0.5

        efficiency = avg_quality / (1 + total)
        return min(1.0, efficiency)

    def cost_performance_ratio(self) -> float:
        """Calculate cost per quality point"""
        total = self.total_cost()
        avg_quality = np.mean(self._quality_scores) if self._quality_scores else 0.5

        if avg_quality == 0:
            return float("inf")

        return total / avg_quality

    def get_cost_summary(self, time_range_days: int = 7) -> CostSummary:
        """Get comprehensive cost summary"""
        events = self._filter_by_time_range(time_range_days)

        total = sum(e.cost for e in events)
        avg_review = self.average_cost_per_review(time_range_days)
        total_tokens = sum(e.input_tokens + e.output_tokens for e in events)

        budget_limit = self._get_current_budget_limit()
        budget_remaining = max(0, budget_limit - total)
        budget_usage = total / budget_limit if budget_limit > 0 else 0

        return CostSummary(
            total_cost=total,
            average_cost_per_review=avg_review,
            total_tokens_processed=total_tokens,
            total_api_calls=len(events),
            cost_efficiency_score=self.efficiency_score(),
            budget_remaining=budget_remaining,
            budget_usage_percentage=budget_usage,
            alert_count=len(self.alerts),
            time_range_days=time_range_days,
        )

    def get_cost_breakdown(self, time_range_days: int = 7) -> CostBreakdown:
        """Get detailed cost breakdown"""
        return CostBreakdown(
            by_event_type=self.cost_by_event_type(time_range_days),
            by_model=self.cost_by_model(time_range_days),
            by_task=self.cost_by_task(time_range_days),
            by_episode=dict(self._episode_costs),
        )

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        total = self.total_cost()
        budget_limit = self._get_current_budget_limit()
        remaining = max(0, budget_limit - total)
        usage = total / budget_limit if budget_limit > 0 else 0

        status = "ok"
        if usage >= self.budget_config.critical_threshold:
            status = "critical"
        elif usage >= self.budget_config.alert_threshold:
            status = "warning"

        return {
            "budget_limit": budget_limit,
            "current_cost": total,
            "remaining": remaining,
            "usage_percentage": usage,
            "status": status,
            "alert_count": len(
                [
                    a
                    for a in self.alerts
                    if a.level in [BudgetAlertLevel.WARNING, BudgetAlertLevel.CRITICAL]
                ]
            ),
            "daily_budget": self.budget_config.daily_budget,
            "weekly_budget": self.budget_config.weekly_budget,
            "monthly_budget": self.budget_config.monthly_budget,
        }

    def should_optimize(self) -> bool:
        """Check if optimization is recommended"""
        total = self.total_cost()
        budget_limit = self._get_current_budget_limit()

        if budget_limit == 0:
            return False

        usage = total / budget_limit

        return usage > 0.6 or self.efficiency_score() < 0.5

    def _check_budget(self) -> None:
        """Check if budget thresholds have been exceeded"""
        total = self.total_cost()
        budget_limit = self._get_current_budget_limit()

        if budget_limit == 0:
            return

        usage = total / budget_limit
        alert_id = str(uuid.uuid4())

        if usage >= self.budget_config.critical_threshold:
            recent_alerts = [
                a for a in self.alerts if a.timestamp > datetime.now() - timedelta(minutes=5)
            ]
            if not any(a.level == BudgetAlertLevel.CRITICAL for a in recent_alerts):
                alert = BudgetAlert(
                    alert_id=alert_id,
                    level=BudgetAlertLevel.CRITICAL,
                    current_cost=total,
                    budget_limit=budget_limit,
                    percentage_used=usage,
                    message=(
                        f"CRITICAL: Budget {usage:.1%} used. "
                        f"${budget_limit - total:.2f} remaining."
                    ),
                    recommended_action="Reduce usage or increase budget limit",
                )
                self.alerts.append(alert)

        elif usage >= self.budget_config.alert_threshold:
            recent_alerts = [
                a for a in self.alerts if a.timestamp > datetime.now() - timedelta(hours=1)
            ]
            if not any(a.level == BudgetAlertLevel.WARNING for a in recent_alerts):
                alert = BudgetAlert(
                    alert_id=alert_id,
                    level=BudgetAlertLevel.WARNING,
                    current_cost=total,
                    budget_limit=budget_limit,
                    percentage_used=usage,
                    message=f"Warning: Budget {usage:.1%} used.",
                    recommended_action="Consider cost optimization",
                )
                self.alerts.append(alert)

    def _get_current_budget_limit(self) -> float:
        """Get the applicable budget limit based on time period"""
        if self.budget_config.daily_budget:
            today = datetime.now().date()
            daily_events = [e for e in self.events if e.timestamp.date() == today]
            daily_total = sum(e.cost for e in daily_events)
            if daily_total >= self.budget_config.daily_budget:
                return self.budget_config.daily_budget

        return self.budget_config.monthly_budget or 100.0

    def _filter_by_time_range(self, days: Optional[int]) -> List[CostEvent]:
        """Filter events by time range"""
        if days is None:
            return self.events

        cutoff = datetime.now() - timedelta(days=days)
        return [e for e in self.events if e.timestamp > cutoff]

    def reset(self) -> None:
        """Reset all cost tracking data"""
        self.events = []
        self.alerts = []
        self.cache_hits = 0
        self.cache_misses = 0
        self._episode_costs = defaultdict(float)
        self._total_latency_ms = 0.0
        self._total_tokens = 0
        self._quality_scores = []

    def export_data(self) -> Dict[str, Any]:
        """Export all cost data for analysis"""
        return {
            "events": [e.dict() for e in self.events],
            "alerts": [a.dict() for a in self.alerts],
            "summary": self.get_cost_summary().dict(),
            "breakdown": self.get_cost_breakdown().dict(),
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses)
                if (self.cache_hits + self.cache_misses) > 0
                else 0,
            },
            "performance": {
                "total_latency_ms": self._total_latency_ms,
                "avg_latency_ms": self._total_latency_ms / len(self.events)
                if self.events
                else 0,
                "total_tokens": self._total_tokens,
            },
        }


class CostAwareActionSelector:
    """Select actions with cost awareness"""

    def __init__(self, cost_tracker: CostTracker, quality_threshold: float = 0.85):
        self.cost_tracker = cost_tracker
        self.quality_threshold = quality_threshold
        self.model_quality_estimates = {
            "gpt-4": 0.95,
            "claude-3-opus": 0.94,
            "gpt-4-turbo": 0.88,
            "claude-3-sonnet": 0.85,
            "gpt-3.5-turbo": 0.69,
            "gemini-pro": 0.69,
            "llama-3-70b": 0.65,
        }

    def select_model(
        self,
        required_quality: float,
        max_cost: Optional[float] = None,
        prefer_fast: bool = False,
    ) -> str:
        """
        Select the cheapest model that meets quality requirements.

        Args:
            required_quality: Minimum required quality (0-1)
            max_cost: Maximum allowed cost per call
            prefer_fast: Prefer faster models over cheaper

        Returns:
            Model name to use
        """
        candidates: List[tuple[str, float, float]] = []

        for model, quality in self.model_quality_estimates.items():
            if quality >= required_quality:
                pricing = self.cost_tracker.pricing_config.models.get(model)
                if pricing:
                    estimated_cost = (
                        pricing.input_price_per_1k + pricing.output_price_per_1k
                    ) / 1000
                else:
                    estimated_cost = 0.05

                if max_cost is None or estimated_cost <= max_cost:
                    candidates.append((model, quality, estimated_cost))

        if not candidates:
            return "gpt-4"

        if prefer_fast:
            candidates.sort(key=lambda x: x[1], reverse=True)
        else:
            candidates.sort(key=lambda x: x[2])

        return candidates[0][0]

    def should_skip_review(
        self,
        confidence: float,
        previous_score: float,
        cost_estimate: float,
    ) -> bool:
        """
        Determine if we should skip a review to save cost.

        Args:
            confidence: Confidence in previous review
            previous_score: Previous quality score
            cost_estimate: Estimated cost of new review

        Returns:
            True if we should skip
        """
        if confidence > 0.9 and previous_score > self.quality_threshold:
            return True

        if cost_estimate > 0.05 and previous_score > 0.8:
            return True

        return False

    def select_batch_size(
        self,
        total_items: int,
        max_cost_per_batch: float = 0.50,
    ) -> int:
        """
        Select optimal batch size for cost efficiency.

        Args:
            total_items: Total items to process
            max_cost_per_batch: Maximum cost per batch

        Returns:
            Optimal batch size
        """
        avg_cost_per_item = self.cost_tracker.average_cost_per_review()

        if avg_cost_per_item == 0:
            return min(total_items, 10)

        optimal_batch = int(max_cost_per_batch / avg_cost_per_item)

        return max(1, min(optimal_batch, total_items, 50))
