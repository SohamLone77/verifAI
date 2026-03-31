"""Cost optimization strategies for VerifAI"""

import hashlib
import uuid
from datetime import datetime
from typing import List, Optional

import numpy as np

from verifai.models.cost_models import (
    BudgetConfig,
    CostSummary,
    OptimizationReport,
    OptimizationSuggestion,
)
from verifai.environment.cost_tracker import CostTracker


class CostOptimizer:
    """
    Generate and apply cost optimization strategies.

    Features:
    - Model tiering optimization
    - Batch processing suggestions
    - Cache optimization
    - Token usage reduction
    - Request consolidation
    """

    def __init__(self, cost_tracker: CostTracker, budget_config: Optional[BudgetConfig] = None):
        self.cost_tracker = cost_tracker
        self.budget_config = budget_config or BudgetConfig()

    def analyze_costs(
        self, time_range_days: int = 7, days: Optional[int] = None
    ) -> List[OptimizationSuggestion]:
        """Analyze costs and generate optimization suggestions"""
        if days is not None:
            time_range_days = days
        suggestions: List[OptimizationSuggestion] = []

        model_suggestions = self._analyze_model_optimization(time_range_days)
        suggestions.extend(model_suggestions)

        batch_suggestion = self._analyze_batch_optimization(time_range_days)
        if batch_suggestion:
            suggestions.append(batch_suggestion)

        cache_suggestion = self._analyze_cache_optimization()
        if cache_suggestion:
            suggestions.append(cache_suggestion)

        token_suggestion = self._analyze_token_optimization(time_range_days)
        if token_suggestion:
            suggestions.append(token_suggestion)

        consolidation_suggestion = self._analyze_request_consolidation(time_range_days)
        if consolidation_suggestion:
            suggestions.append(consolidation_suggestion)

        suggestions.sort(key=lambda x: (x.priority == "high", -x.estimated_savings), reverse=True)

        return suggestions

    def _analyze_model_optimization(self, days: int) -> List[OptimizationSuggestion]:
        """Analyze if we can save costs by switching models"""
        suggestions: List[OptimizationSuggestion] = []

        costs_by_model = self.cost_tracker.cost_by_model(days)

        expensive_models = ["gpt-4", "claude-3-opus"]
        expensive_cost = sum(costs_by_model.get(m, 0) for m in expensive_models)
        total_cost = self.cost_tracker.total_cost(days)

        if total_cost > 0 and expensive_cost > total_cost * 0.5:
            savings = expensive_cost * 0.7

            suggestions.append(
                OptimizationSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    type="model_optimization",
                    title="Switch to cheaper models for simple reviews",
                    description=(
                        f"Currently {expensive_cost/total_cost:.0%} of costs come from premium models. "
                        "Consider using gpt-4-turbo or gpt-3.5-turbo for non-critical reviews."
                    ),
                    estimated_savings=savings,
                    estimated_quality_impact=-0.05,
                    implementation_difficulty="easy",
                    priority="high",
                    action_items=[
                        "Identify reviews with low complexity",
                        "Create model selection rules based on task difficulty",
                        "Implement model fallback strategy",
                    ],
                    metrics={
                        "current_premium_cost": expensive_cost,
                        "potential_savings": savings,
                        "affected_reviews": len(
                            [e for e in self.cost_tracker.events if e.model in expensive_models]
                        ),
                    },
                )
            )

        return suggestions

    def _analyze_batch_optimization(self, days: int) -> Optional[OptimizationSuggestion]:
        """Analyze batch processing opportunities"""
        events = self.cost_tracker._filter_by_time_range(days)
        review_events = [e for e in events if e.event_type.value == "review"]

        if len(review_events) < 10:
            return None

        avg_cost = sum(e.cost for e in review_events) / len(review_events)
        savings = avg_cost * len(review_events) * 0.35

        return OptimizationSuggestion(
            suggestion_id=str(uuid.uuid4()),
            type="batch_processing",
            title="Implement batch processing for reviews",
            description=(
                f"Processing {len(review_events)} reviews individually. "
                "Batch processing could reduce costs by up to 35%."
            ),
            estimated_savings=savings,
            estimated_quality_impact=0.0,
            implementation_difficulty="medium",
            priority="medium",
            action_items=[
                "Group similar review requests",
                "Implement batch API calls",
                "Add batch result caching",
            ],
            metrics={
                "total_reviews": len(review_events),
                "current_avg_cost": avg_cost,
                "batch_savings_percentage": 35,
            },
        )

    def _analyze_cache_optimization(self) -> Optional[OptimizationSuggestion]:
        """Analyze cache hit rate and potential improvements"""
        total_requests = self.cost_tracker.cache_hits + self.cost_tracker.cache_misses

        if total_requests == 0:
            return None

        hit_rate = self.cost_tracker.cache_hits / total_requests
        avg_cost = self.cost_tracker.average_cost_per_review()

        if hit_rate < 0.2:
            potential_savings = avg_cost * total_requests * 0.3

            return OptimizationSuggestion(
                suggestion_id=str(uuid.uuid4()),
                type="caching",
                title="Improve cache hit rate",
                description=(
                    f"Current cache hit rate is {hit_rate:.1%}. "
                    "Implementing better caching strategies could save up to 30%."
                ),
                estimated_savings=potential_savings,
                estimated_quality_impact=0.0,
                implementation_difficulty="medium",
                priority="medium",
                action_items=[
                    "Increase cache TTL for stable content",
                    "Implement semantic caching for similar content",
                    "Use content hashing for exact matches",
                ],
                metrics={
                    "current_hit_rate": hit_rate,
                    "target_hit_rate": 0.5,
                    "total_requests": total_requests,
                },
            )

        return None

    def _analyze_token_optimization(self, days: int) -> Optional[OptimizationSuggestion]:
        """Analyze token usage and optimization opportunities"""
        events = self.cost_tracker._filter_by_time_range(days)

        if not events:
            return None

        avg_input_tokens = np.mean([e.input_tokens for e in events])
        avg_output_tokens = np.mean([e.output_tokens for e in events])

        if avg_input_tokens > 2000 or avg_output_tokens > 500:
            savings = self.cost_tracker.total_cost(days) * 0.2

            return OptimizationSuggestion(
                suggestion_id=str(uuid.uuid4()),
                type="token_optimization",
                title="Reduce token usage",
                description=(
                    f"Average input tokens: {avg_input_tokens:.0f}, "
                    f"output tokens: {avg_output_tokens:.0f}. "
                    "Consider truncating inputs and limiting outputs."
                ),
                estimated_savings=savings,
                estimated_quality_impact=-0.03,
                implementation_difficulty="easy",
                priority="high",
                action_items=[
                    "Truncate inputs to relevant sections only",
                    "Set max_tokens parameter appropriately",
                    "Remove redundant context from prompts",
                ],
                metrics={
                    "avg_input_tokens": avg_input_tokens,
                    "avg_output_tokens": avg_output_tokens,
                    "token_reduction_target": "30%",
                },
            )

        return None

    def _analyze_request_consolidation(self, days: int) -> Optional[OptimizationSuggestion]:
        """Analyze if requests can be consolidated"""
        events = self.cost_tracker._filter_by_time_range(days)

        request_hashes = {}
        for event in events:
            hash_key = hashlib.md5(f"{event.model}_{event.metadata}".encode()).hexdigest()
            request_hashes[hash_key] = request_hashes.get(hash_key, 0) + 1

        duplicates = sum(1 for count in request_hashes.values() if count > 1)

        if duplicates > len(request_hashes) * 0.2:
            savings = self.cost_tracker.total_cost(days) * 0.15

            return OptimizationSuggestion(
                suggestion_id=str(uuid.uuid4()),
                type="request_consolidation",
                title="Consolidate duplicate requests",
                description=f"Found {duplicates} duplicate requests that could be cached or consolidated.",
                estimated_savings=savings,
                estimated_quality_impact=0.0,
                implementation_difficulty="medium",
                priority="medium",
                action_items=[
                    "Implement request deduplication",
                    "Cache identical requests",
                    "Use request pooling for similar content",
                ],
                metrics={
                    "duplicate_requests": duplicates,
                    "total_unique_requests": len(request_hashes),
                },
            )

        return None

    def generate_optimization_report(
        self,
        time_range_days: int = 7,
        apply_suggestions: bool = False,
        days: Optional[int] = None,
    ) -> OptimizationReport:
        """Generate a complete optimization report"""
        if days is not None:
            time_range_days = days

        current_summary = self.cost_tracker.get_cost_summary(time_range_days)
        suggestions = self.analyze_costs(time_range_days)

        total_savings = sum(s.estimated_savings for s in suggestions)

        projected_summary = CostSummary(
            total_cost=current_summary.total_cost - total_savings,
            average_cost_per_review=current_summary.average_cost_per_review * 0.7,
            total_tokens_processed=current_summary.total_tokens_processed,
            total_api_calls=current_summary.total_api_calls,
            cost_efficiency_score=current_summary.cost_efficiency_score * 1.2,
            budget_remaining=current_summary.budget_remaining + total_savings,
            budget_usage_percentage=current_summary.budget_usage_percentage
            - (
                total_savings / current_summary.budget_remaining
                if current_summary.budget_remaining > 0
                else 0
            ),
            alert_count=current_summary.alert_count,
            time_range_days=time_range_days,
        )

        if suggestions:
            quality_impact = (
                sum(s.estimated_quality_impact * s.estimated_savings for s in suggestions)
                / total_savings
                if total_savings > 0
                else 0
            )
        else:
            quality_impact = 0.0

        report = OptimizationReport(
            report_id=str(uuid.uuid4()),
            current_costs=current_summary,
            projected_costs=projected_summary,
            total_savings=total_savings,
            savings_percentage=total_savings / current_summary.total_cost
            if current_summary.total_cost > 0
            else 0,
            quality_impact=quality_impact,
            suggestions=suggestions,
            timestamp=datetime.now(),
        )

        if apply_suggestions and suggestions:
            for suggestion in suggestions:
                self.apply_suggestion(suggestion)

        return report

    def apply_suggestion(self, suggestion: OptimizationSuggestion) -> bool:
        """Apply an optimization suggestion (simulated)"""
        _ = suggestion
        return True
