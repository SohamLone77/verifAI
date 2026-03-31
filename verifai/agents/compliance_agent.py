"""Compliance specialist agent for regulatory checks"""

from typing import Any, Dict, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote


class ComplianceAgent(BaseAgent):
    """Specialized agent for compliance issues"""

    def __init__(self, profile: Optional[AgentProfile] = None):
        if profile is None:
            profile = AgentProfile(
                name="ComplianceSpecialist",
                role=AgentRole.COMPLIANCE,
                weight=1.3,
                confidence_threshold=0.75,
            )
        super().__init__(profile)

        self.prohibited_claims = [
            "guaranteed",
            "100% safe",
            "always works",
            "cures",
            "fda approved",
            "risk free",
        ]

    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content for compliance risks"""
        _ = context
        flags = []
        confidence = 0.8

        lowered = content.lower()
        for claim in self.prohibited_claims:
            if claim in lowered:
                flags.append(
                    {
                        "type": "compliance_risk",
                        "severity": 0.7,
                        "claim": claim,
                        "suggestion": "Remove or qualify regulated claims",
                    }
                )

        total_risk = sum(flag["severity"] for flag in flags)
        max_risk = max(1, len(self.prohibited_claims))
        compliance_score = max(0.0, 1.0 - (total_risk / max_risk))

        if flags:
            confidence = max(0.6, confidence - len(flags) * 0.05)
            reasoning = (
                f"Detected {len(flags)} compliance risk(s). "
                f"Compliance score: {compliance_score:.2f}."
            )
        else:
            reasoning = "No compliance issues detected."

        return AgentVote(
            agent_id=self.profile.agent_id,
            agent_name=self.profile.name,
            role=self.profile.role,
            score=compliance_score,
            confidence=confidence,
            reasoning=reasoning,
            flags=flags,
            suggestions=[f["suggestion"] for f in flags if "suggestion" in f],
        )
