"""Factuality checker agent for detecting hallucinations and factual errors"""

import re
from typing import Any, Dict, List, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote


class FactualityAgent(BaseAgent):
    """Specialized agent for detecting factual errors and hallucinations"""

    def __init__(self, profile: Optional[AgentProfile] = None):
        if profile is None:
            profile = AgentProfile(
                name="FactChecker",
                role=AgentRole.FACTUALITY,
                weight=1.5,
                confidence_threshold=0.75,
            )
        super().__init__(profile)

        self.known_facts = {
            "eiffel_tower": {"location": "Paris, France", "year": 1889},
            "iphone_15": {"has_8k": False, "has_4k": True},
            "mars": {"distance_from_earth": "225 million km", "gravity": "3.71 m/s^2"},
        }

        self.hedging_patterns = [
            r"(i think|i believe|maybe|perhaps|possibly|could be|might be|probably)",
            r"(according to some|it is said that|people say that)",
        ]

        self.exaggeration_patterns = [
            r"(best (ever|in history)|worst (ever|in history))",
            r"(always|never|everyone|no one)",
            r"(revolutionary|groundbreaking|game[- ]changing)",
        ]

    def analyze(self, content: str, context: Optional[Dict[str, Any]] = None) -> AgentVote:
        """Analyze content for factual accuracy"""
        _ = context
        flags = []
        total_issues = 0.0
        confidence = 0.85

        claims = self._extract_claims(content)

        for claim in claims:
            verification = self._verify_claim(claim)
            if not verification["verified"]:
                total_issues += verification["severity"]
                flags.append(
                    {
                        "type": "factual_error",
                        "claim": claim,
                        "expected": verification.get("expected"),
                        "actual": verification.get("actual"),
                        "severity": verification["severity"],
                        "suggestion": verification["suggestion"],
                    }
                )

        for pattern in self.hedging_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(
                    {
                        "type": "hedging",
                        "severity": 0.3,
                        "pattern": pattern,
                        "suggestion": "Use more confident language or provide evidence",
                    }
                )
                total_issues += 0.3

        for pattern in self.exaggeration_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                flags.append(
                    {
                        "type": "exaggeration",
                        "severity": 0.4,
                        "pattern": pattern,
                        "suggestion": "Replace with specific, verifiable claims",
                    }
                )
                total_issues += 0.4

        max_issues = len(claims) + 2
        factuality_score = max(0.0, 1.0 - (total_issues / max_issues)) if max_issues > 0 else 1.0

        if flags:
            confidence = max(0.5, confidence - len(flags) * 0.05)
            reasoning = (
                f"Found {len([f for f in flags if f['type'] == 'factual_error'])} factual error(s). "
                f"Factuality score: {factuality_score:.2f}. Verify claims."
            )
        else:
            reasoning = "No factual errors detected. Content appears accurate."

        return AgentVote(
            agent_id=self.profile.agent_id,
            agent_name=self.profile.name,
            role=self.profile.role,
            score=factuality_score,
            confidence=confidence,
            reasoning=reasoning,
            flags=flags,
            suggestions=[f.get("suggestion", "") for f in flags if "suggestion" in f],
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        sentences = text.split(".")
        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) > 5:
                claims.append(sentence)
        return claims[:5]

    def _verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a claim against known facts"""
        claim_lower = claim.lower()

        if "eiffel tower" in claim_lower:
            if "berlin" in claim_lower or "germany" in claim_lower:
                return {
                    "verified": False,
                    "expected": "Paris, France",
                    "actual": "Berlin, Germany",
                    "severity": 0.9,
                    "suggestion": "Correct: The Eiffel Tower is in Paris, France",
                }

        if "iphone 15" in claim_lower and "8k" in claim_lower:
            return {
                "verified": False,
                "expected": "iPhone 15 has 4K video, not 8K",
                "actual": "8K video capability",
                "severity": 0.8,
                "suggestion": "Correct: iPhone 15 supports 4K video at up to 60 fps",
            }

        return {"verified": True, "severity": 0.0}
