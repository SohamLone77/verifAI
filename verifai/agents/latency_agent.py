"""Latency analyst agent for performance considerations"""

from typing import Any, Dict, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote


class LatencyAgent(BaseAgent):
    """Specialized agent for latency and size concerns"""

    def __init__(self, profile: Optional[AgentProfile] = None):
        if profile is None:
            profile = AgentProfile(
                name="LatencyAnalyst",
                role=AgentRole.LATENCY,
                weight=0.8,
                confidence_threshold=0.65,
            )
        super().__init__(profile)

    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content for latency impact"""
        _ = context
        flags = []
        confidence = 0.75

        word_count = len(content.split())
        estimated_latency_ms = 50 + word_count * 4

        if word_count > 250:
            flags.append(
                {
                    "type": "latency_risk",
                    "severity": 0.5,
                    "word_count": word_count,
                    "suggestion": "Shorten content to reduce processing time",
                }
            )

        if word_count > 500:
            flags.append(
                {
                    "type": "latency_risk",
                    "severity": 0.8,
                    "word_count": word_count,
                    "suggestion": "Consider splitting content into smaller chunks",
                }
            )

        max_risk = 2
        total_risk = sum(flag["severity"] for flag in flags)
        latency_score = max(0.0, 1.0 - (total_risk / max_risk))

        if flags:
            confidence = max(0.6, confidence - len(flags) * 0.05)
            reasoning = (
                f"Estimated latency {estimated_latency_ms:.0f} ms. "
                f"Latency score: {latency_score:.2f}."
            )
        else:
            reasoning = "Content length is within expected bounds."

        return AgentVote(
            agent_id=self.profile.agent_id,
            agent_name=self.profile.name,
            role=self.profile.role,
            score=latency_score,
            confidence=confidence,
            reasoning=reasoning,
            flags=flags,
            suggestions=[f["suggestion"] for f in flags if "suggestion" in f],
        )
