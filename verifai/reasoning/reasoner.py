"""Reasoner wrapper for Chain-of-Thought utilities"""

from verifai.environment.chain_of_thought import (
    ReasoningEngine,
    ReasoningQualityScorer,
    ReasoningRewardCalculator,
)
from verifai.models.reasoning_models import ReasoningRequest


class Reasoner:
    """High-level helper for reasoning workflows"""

    def __init__(self, model: str = "gpt-4", max_tokens: int = 1000):
        self.engine = ReasoningEngine(model=model, max_tokens=max_tokens)
        self.scorer = ReasoningQualityScorer()
        self.rewarder = ReasoningRewardCalculator()

    def analyze(self, request: ReasoningRequest):
        """Run reasoning for a request"""
        return self.engine.reason(request)

    def score(self, chain):
        """Score a reasoning chain"""
        return self.scorer.score(chain)

    def reward(self, chain, outcome_score: float):
        """Calculate reward for a reasoning chain"""
        return self.rewarder.calculate_reward(chain, outcome_score)
