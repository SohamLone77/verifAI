"""Consensus and voting mechanism for multi-agent review"""

from typing import Any, Dict, List, Optional

from verifai.models.agent_models import AgentProfile, AgentRole, AgentVote, ConsensusConfig, ConsensusResult


class ConsensusEngine:
    """Compute consensus outcomes for multi-agent votes"""

    def __init__(
        self,
        config: Optional[ConsensusConfig] = None,
        agent_profiles: Optional[Dict[AgentRole, AgentProfile]] = None,
    ):
        self.config = config or ConsensusConfig()
        self.agent_profiles = agent_profiles or {}

    def calculate(self, votes: List[AgentVote], review_depth: str = "standard") -> ConsensusResult:
        """Calculate consensus based on configured strategy"""
        if self.config.strategy == "majority":
            return self._majority(votes)
        if self.config.strategy == "unanimous":
            return self._unanimous(votes)
        if self.config.strategy == "dynamic":
            return self._dynamic(votes, review_depth)
        return self._weighted(votes)

    def _weighted(self, votes: List[AgentVote]) -> ConsensusResult:
        total_weight = 0.0
        weighted_score = 0.0

        for vote in votes:
            profile = self.agent_profiles.get(vote.role)
            weight = profile.weight if profile else 1.0
            total_weight += weight
            weighted_score += vote.score * weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.5

        disagreements = self._find_disagreements(votes)
        consensus_reached = len(disagreements) == 0

        final_decision = self._decision_from_score(final_score)

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=consensus_reached,
            votes=votes,
            weighted_score=weighted_score,
            disagreements=disagreements,
            resolution_strategy="weighted_voting",
            confidence=1.0 - self._variance([v.score for v in votes]),
            requires_escalation=not consensus_reached and self.config.escalation_threshold > 0,
        )

    def _majority(self, votes: List[AgentVote]) -> ConsensusResult:
        approved = [v for v in votes if v.score >= 0.7]
        rejected = [v for v in votes if v.score < 0.7]

        if len(approved) > len(rejected):
            final_score = sum(v.score for v in approved) / len(approved)
            final_decision = "APPROVED"
        else:
            final_score = sum(v.score for v in rejected) / len(rejected) if rejected else 0.5
            final_decision = "REJECTED"

        consensus_reached = len(approved) != len(rejected)

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=consensus_reached,
            votes=votes,
            weighted_score=final_score,
            disagreements=[],
            resolution_strategy="majority",
            confidence=abs(len(approved) - len(rejected)) / len(votes) if votes else 0.5,
        )

    def _unanimous(self, votes: List[AgentVote]) -> ConsensusResult:
        all_approved = all(v.score >= 0.7 for v in votes)
        all_rejected = all(v.score < 0.3 for v in votes)

        if all_approved:
            final_decision = "APPROVED"
        elif all_rejected:
            final_decision = "REJECTED"
        else:
            final_decision = "NEEDS_REVIEW"

        final_score = sum(v.score for v in votes) / len(votes) if votes else 0.5

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=all_approved or all_rejected,
            votes=votes,
            weighted_score=final_score,
            disagreements=self._find_disagreements(votes) if not (all_approved or all_rejected) else [],
            resolution_strategy="unanimous",
            confidence=1.0 if all_approved or all_rejected else 0.5,
        )

    def _dynamic(self, votes: List[AgentVote], review_depth: str) -> ConsensusResult:
        base = self._weighted(votes)
        if review_depth == "deep" and not base.consensus_reached:
            base.final_score = base.final_score * 0.9
            base.final_decision = self._decision_from_score(base.final_score)
        base.resolution_strategy = "dynamic"
        return base

    def _decision_from_score(self, score: float) -> str:
        if score >= 0.8:
            return "APPROVED"
        if score >= 0.6:
            return "NEEDS_REVIEW"
        return "REJECTED"

    def _variance(self, values: List[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _find_disagreements(self, votes: List[AgentVote]) -> List[Dict[str, Any]]:
        disagreements = []
        for i, vote_a in enumerate(votes):
            for vote_b in votes[i + 1 :]:
                diff = abs(vote_a.score - vote_b.score)
                if diff > self.config.disagreement_threshold:
                    disagreements.append(
                        {
                            "agent_a": vote_a.agent_name,
                            "score_a": vote_a.score,
                            "reasoning_a": vote_a.reasoning[:100],
                            "agent_b": vote_b.agent_name,
                            "score_b": vote_b.score,
                            "reasoning_b": vote_b.reasoning[:100],
                            "difference": diff,
                        }
                    )
        return disagreements
