"""Brand guardian agent for tone and messaging checks"""

from typing import Any, Dict, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote


class BrandAgent(BaseAgent):
    """Specialized agent for brand voice and messaging"""

    def __init__(self, profile: Optional[AgentProfile] = None):
        if profile is None:
            profile = AgentProfile(
                name="BrandGuardian",
                role=AgentRole.BRAND,
                weight=1.2,
                confidence_threshold=0.7,
            )
        super().__init__(profile)

        self.brand_keywords = {
            "overpromise": ["best ever", "guaranteed", "life changing", "world-class"],
            "competitor": ["better than", "beats", "destroys", "crushes"],
            "tone": ["cheap", "lazy", "whatever", "meh"],
        }

        self.brand_weights = {"overpromise": 0.6, "competitor": 0.5, "tone": 0.4}

    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content for brand alignment"""
        _ = context
        flags = []
        total_risk = 0.0
        confidence = 0.8

        for category, keywords in self.brand_keywords.items():
            found = [keyword for keyword in keywords if keyword in content.lower()]
            if found:
                severity = self.brand_weights.get(category, 0.4)
                total_risk += severity
                flags.append(
                    {
                        "type": "brand_voice",
                        "category": category,
                        "severity": severity,
                        "keywords": found,
                        "suggestion": "Adjust tone to match brand guidelines",
                    }
                )

        max_risk = len(self.brand_keywords)
        brand_score = max(0.0, 1.0 - (total_risk / max_risk)) if max_risk else 1.0

        if flags:
            confidence = max(0.6, confidence - len(flags) * 0.05)
            reasoning = (
                f"Detected {len(flags)} brand alignment issue(s). "
                f"Brand score: {brand_score:.2f}."
            )
        else:
            reasoning = "Brand voice appears consistent and on message."

        return AgentVote(
            agent_id=self.profile.agent_id,
            agent_name=self.profile.name,
            role=self.profile.role,
            score=brand_score,
            confidence=confidence,
            reasoning=reasoning,
            flags=flags,
            suggestions=[f["suggestion"] for f in flags if "suggestion" in f],
        )
