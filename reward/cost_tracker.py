# COST_TRACKING
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Cost per 1 million tokens (USD)
PRICING_TABLE = {
    "gpt-4o": {"prompt": 5.00, "completion": 15.00},
    "gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    "text-embedding-3-small": {"prompt": 0.02, "completion": 0.00},
    # Free OpenRouter Models Fallback
    "meta-llama/llama-3.3-70b-instruct:free": {"prompt": 0.0, "completion": 0.0},
    "google/gemma-3-4b-it:free": {"prompt": 0.0, "completion": 0.0},
    "qwen/qwen-vl-plus:free": {"prompt": 0.0, "completion": 0.0},
}


@dataclass
class CostReport:
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_usd: float
    hints: list[str]


def get_optimization_hints(report: CostReport) -> list[str]:
    """Analyze the CostReport and surface actionable cost-saving hints."""
    hints = []
    
    if report.total_usd > 0.05:
        hints.append(
            "Episode cost exceeded $0.05. Consider switching from gpt-4o to "
            "gpt-4o-mini if the performance score delta remains < 0.05."
        )
    
    if report.total_prompt_tokens > 20000:
        hints.append(
            "Token budget is massive. Recommend summarizing context before feeding into the PromptReviewEnv."
        )

    return hints


class CostTracker:
    """Tracks token consumption and USD costs throughout an episode."""
    
    def __init__(self) -> None:
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_usd: float = 0.0
        self.model_usage: dict[str, dict[str, float]] = {}

    def track(self, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        prompt_tokens = max(0, int(prompt_tokens))
        completion_tokens = max(0, int(completion_tokens))

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        
        # Calculate USD cost
        pricing = PRICING_TABLE.get(model, {"prompt": 0.0, "completion": 0.0})
        cost = (prompt_tokens * pricing["prompt"] / 1_000_000) + (
            completion_tokens * pricing["completion"] / 1_000_000
        )
        
        self.total_usd += cost

        # Save per-model stats
        if model not in self.model_usage:
            self.model_usage[model] = {"prompt": 0, "completion": 0, "cost": 0.0}
        
        self.model_usage[model]["prompt"] += prompt_tokens
        self.model_usage[model]["completion"] += completion_tokens
        self.model_usage[model]["cost"] += cost

    def get_episode_cost(self, session_id: Optional[str] = None) -> CostReport:
        """
        Returns the CostReport dataclass for the active tracker.
        session_id is an optional parameter to match the explicit user specification.
        """
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        report = CostReport(
            total_prompt_tokens=self.total_prompt_tokens,
            total_completion_tokens=self.total_completion_tokens,
            total_tokens=total_tokens,
            total_usd=self.total_usd,
            hints=[],
        )
        # Populate hints using the standalone helper mapping
        report.hints = get_optimization_hints(report)
        return report
