"""Safety expert agent for detecting harmful content"""

import re
from typing import Any, Dict, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote


class SafetyAgent(BaseAgent):
    """Specialized agent for detecting safety violations"""

    def __init__(self, profile: Optional[AgentProfile] = None):
        if profile is None:
            profile = AgentProfile(
                name="SafetyGuard",
                role=AgentRole.SAFETY,
                weight=1.5,
                confidence_threshold=0.7,
            )
        super().__init__(profile)

        self.safety_keywords = {
            "violence": ["kill", "murder", "attack", "violence", "weapon", "gun", "bomb"],
            "hate_speech": ["hate", "racist", "sexist", "discrimination", "bigot"],
            "harassment": ["harass", "bully", "threat", "intimidate", "abuse"],
            "self_harm": ["suicide", "self-harm", "die", "end my life"],
            "nsfw": ["explicit", "porn", "nudity", "adult content"],
            "illegal": ["illegal", "crime", "steal", "fraud", "scam"],
        }

        self.safety_weights = {
            "violence": 0.9,
            "hate_speech": 1.0,
            "harassment": 0.8,
            "self_harm": 1.0,
            "nsfw": 0.7,
            "illegal": 0.9,
        }

    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content for safety violations"""
        _ = context
        flags = []
        total_risk = 0.0
        confidence = 0.8

        for category, keywords in self.safety_keywords.items():
            found_keywords = [keyword for keyword in keywords if keyword in content.lower()]

            if found_keywords:
                severity = self.safety_weights.get(category, 0.5)
                total_risk += severity
                flags.append(
                    {
                        "type": "safety_violation",
                        "category": category,
                        "severity": severity,
                        "keywords": found_keywords,
                        "suggestion": f"Remove or rephrase content containing: {', '.join(found_keywords)}",
                    }
                )

        jailbreak_patterns = [
            r"ignore (all|previous) (instructions|rules)",
            r"you are now (DAN|jailbroken|unrestricted)",
            r"no (restrictions|limitations|boundaries)",
            r"pretend you are (evil|unfiltered)",
        ]

        for pattern in jailbreak_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(
                    {
                        "type": "jailbreak_attempt",
                        "severity": 1.0,
                        "pattern": pattern,
                        "suggestion": "Block content - jailbreak attempt detected",
                    }
                )
                total_risk += 1.0
                confidence = 0.95

        max_risk = len(self.safety_keywords) + 1
        safety_score = max(0.0, 1.0 - (total_risk / max_risk))

        if flags:
            confidence = min(0.95, confidence + len(flags) * 0.05)
            reasoning = (
                f"Detected {len(flags)} safety violation(s). "
                f"Safety score: {safety_score:.2f}. Recommend review."
            )
        else:
            reasoning = "No safety violations detected. Content appears safe."

        return AgentVote(
            agent_id=self.profile.agent_id,
            agent_name=self.profile.name,
            role=self.profile.role,
            score=safety_score,
            confidence=confidence,
            reasoning=reasoning,
            flags=flags,
            suggestions=[f["suggestion"] for f in flags if "suggestion" in f],
        )
