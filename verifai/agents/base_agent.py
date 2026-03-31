"""Base agent class for all specialized agents"""

from abc import ABC, abstractmethod
from datetime import datetime
import time
from typing import Any, Dict, List, Optional

from verifai.models.agent_models import AgentMetrics, AgentProfile, AgentVote


class BaseAgent(ABC):
    """Abstract base class for all VerifAI agents"""

    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.metrics = AgentMetrics()
        self.review_history: List[Dict[str, Any]] = []

    @abstractmethod
    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content and return vote"""
        raise NotImplementedError

    def review(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Wrapper for analysis with metrics tracking"""
        start_time = time.time()

        try:
            vote = self.analyze(content, context)
            vote.processing_time_ms = (time.time() - start_time) * 1000

            self.review_history.append(
                {
                    "timestamp": datetime.now(),
                    "content": content[:200],
                    "vote": vote.dict(),
                    "processing_time": vote.processing_time_ms,
                }
            )

            self._update_metrics(vote)
            return vote

        except Exception as exc:
            return AgentVote(
                agent_id=self.profile.agent_id,
                agent_name=self.profile.name,
                role=self.profile.role,
                score=0.0,
                confidence=0.0,
                reasoning=f"Error during analysis: {exc}",
                flags=[{"error": str(exc)}],
            )

    def _update_metrics(self, vote: AgentVote) -> None:
        """Update agent performance metrics"""
        total_reviews = len(self.review_history)

        self.metrics.total_reviews = total_reviews
        self.metrics.average_score = (
            (self.metrics.average_score * (total_reviews - 1) + vote.score) / total_reviews
        )
        self.metrics.average_confidence = (
            (self.metrics.average_confidence * (total_reviews - 1) + vote.confidence)
            / total_reviews
        )
        self.metrics.average_latency_ms = (
            (self.metrics.average_latency_ms * (total_reviews - 1) + vote.processing_time_ms)
            / total_reviews
        )

        self.metrics.last_updated = datetime.now()

    def update_accuracy(self, ground_truth_score: float) -> None:
        """Update accuracy metrics with ground truth"""
        if not self.review_history:
            return

        last_vote = self.review_history[-1]["vote"]
        predicted = last_vote["score"]

        correct = abs(predicted - ground_truth_score) < 0.2
        total = self.metrics.total_reviews

        self.metrics.accuracy = (
            (self.metrics.accuracy * (total - 1) + (1 if correct else 0)) / total
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "agent_id": self.profile.agent_id,
            "name": self.profile.name,
            "role": self.profile.role.value,
            "metrics": self.metrics.dict(),
            "total_reviews": len(self.review_history),
            "recent_reviews": self.review_history[-5:] if self.review_history else [],
        }

    def reset(self) -> None:
        """Reset agent state"""
        self.review_history = []
        self.metrics = AgentMetrics()

    def get_confidence(self, content: str) -> float:
        """Calculate confidence in analysis"""
        _ = content
        return 0.7

    def should_delegate(self, content: str) -> bool:
        """Determine if agent should delegate to another agent"""
        _ = content
        return False
