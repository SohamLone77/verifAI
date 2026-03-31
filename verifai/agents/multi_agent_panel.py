"""Multi-agent panel orchestrator for VerifAI"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from verifai.agents.base_agent import BaseAgent
from verifai.agents.brand_agent import BrandAgent
from verifai.agents.compliance_agent import ComplianceAgent
from verifai.agents.factuality_agent import FactualityAgent
from verifai.agents.latency_agent import LatencyAgent
from verifai.agents.safety_agent import SafetyAgent
from verifai.models.agent_models import (
    AgentRole,
    AgentVote,
    ConsensusConfig,
    ConsensusResult,
    ReviewRequest,
    ReviewResponse,
)


class MultiAgentPanel:
    """
    Orchestrates multiple specialized agents for comprehensive review.

    Features:
    - Parallel agent execution
    - Configurable consensus mechanisms
    - Dynamic agent weighting
    - Performance tracking
    """

    def __init__(self, config: Optional[ConsensusConfig] = None):
        self.config = config or ConsensusConfig()
        self.agents: Dict[AgentRole, BaseAgent] = {}
        self.executor = ThreadPoolExecutor(max_workers=8)
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all specialized agents"""
        self.agents[AgentRole.SAFETY] = SafetyAgent()
        self.agents[AgentRole.FACTUALITY] = FactualityAgent()
        self.agents[AgentRole.BRAND] = BrandAgent()
        self.agents[AgentRole.LATENCY] = LatencyAgent()
        self.agents[AgentRole.COMPLIANCE] = ComplianceAgent()

    def review(self, request: ReviewRequest) -> ReviewResponse:
        """Perform multi-agent review"""
        start_time = time.time()

        agents_to_use = self._select_agents(request)
        votes = self._run_agents_parallel(agents_to_use, request.content, request.context)
        consensus = self._calculate_consensus(votes, request)
        recommendations = self._generate_recommendations(votes, consensus)
        summary = self._generate_summary(votes, consensus)

        total_cost = sum(v.processing_time_ms / 1000 * 0.01 for v in votes)
        total_tokens = sum(len(request.content.split()) * 5 for _ in votes)
        processing_time = (time.time() - start_time) * 1000

        return ReviewResponse(
            consensus=consensus,
            agent_responses=votes,
            processing_time_ms=processing_time,
            tokens_used=total_tokens,
            cost=total_cost,
            recommendations=recommendations,
            summary=summary,
        )

    async def review_async(self, request: ReviewRequest) -> ReviewResponse:
        """Async version of review"""
        return await asyncio.get_event_loop().run_in_executor(self.executor, self.review, request)

    def _select_agents(self, request: ReviewRequest) -> List[BaseAgent]:
        """Select which agents to use based on request"""
        if request.required_agents:
            return [self.agents[role] for role in request.required_agents if role in self.agents]
        return list(self.agents.values())

    def _run_agents_parallel(
        self,
        agents: List[BaseAgent],
        content: str,
        context: Optional[Dict[str, Any]],
    ) -> List[AgentVote]:
        """Run agents in parallel"""
        votes: List[AgentVote] = []
        futures = []

        for agent in agents:
            futures.append(self.executor.submit(agent.review, content, context))

        for future in futures:
            try:
                vote = future.result(timeout=30)
                votes.append(vote)
            except Exception as exc:
                votes.append(
                    AgentVote(
                        agent_id="error",
                        agent_name="Error",
                        role=AgentRole.SAFETY,
                        score=0.0,
                        confidence=0.0,
                        reasoning=f"Agent failed: {exc}",
                    )
                )

        return votes

    def _calculate_consensus(self, votes: List[AgentVote], request: ReviewRequest) -> ConsensusResult:
        """Calculate consensus using configured strategy"""
        if self.config.strategy == "weighted_voting":
            return self._weighted_voting_consensus(votes)
        if self.config.strategy == "majority":
            return self._majority_consensus(votes)
        if self.config.strategy == "unanimous":
            return self._unanimous_consensus(votes)
        return self._dynamic_consensus(votes, request)

    def _weighted_voting_consensus(self, votes: List[AgentVote]) -> ConsensusResult:
        total_weight = 0.0
        weighted_score = 0.0

        for vote in votes:
            agent_profile = self.agents.get(vote.role)
            weight = agent_profile.profile.weight if agent_profile else 1.0
            total_weight += weight
            weighted_score += vote.score * weight

        final_score = weighted_score / total_weight if total_weight > 0 else 0.5

        disagreements = []
        scores = [v.score for v in votes]
        score_variance = self._calculate_variance(scores)

        if score_variance > self.config.disagreement_threshold:
            disagreements = self._find_disagreements(votes)

        consensus_reached = len(disagreements) == 0

        if final_score >= 0.8:
            final_decision = "APPROVED"
        elif final_score >= 0.6:
            final_decision = "NEEDS_REVIEW"
        else:
            final_decision = "REJECTED"

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=consensus_reached,
            votes=votes,
            weighted_score=weighted_score,
            disagreements=disagreements,
            resolution_strategy="weighted_voting",
            confidence=1.0 - score_variance,
            requires_escalation=not consensus_reached and self.config.escalation_threshold > 0,
        )

    def _majority_consensus(self, votes: List[AgentVote]) -> ConsensusResult:
        approved = sum(1 for v in votes if v.score >= 0.7)
        rejected = len(votes) - approved

        if approved > rejected:
            final_score = sum(v.score for v in votes if v.score >= 0.7) / approved if approved else 0.5
            final_decision = "APPROVED"
        else:
            final_score = sum(v.score for v in votes if v.score < 0.7) / rejected if rejected else 0.5
            final_decision = "REJECTED"

        consensus_reached = approved != rejected

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=consensus_reached,
            votes=votes,
            weighted_score=final_score,
            disagreements=[],
            resolution_strategy="majority",
            confidence=abs(approved - rejected) / len(votes) if votes else 0.5,
        )

    def _unanimous_consensus(self, votes: List[AgentVote]) -> ConsensusResult:
        all_approved = all(v.score >= 0.7 for v in votes)
        all_rejected = all(v.score < 0.3 for v in votes)

        consensus_reached = all_approved or all_rejected

        if all_approved:
            final_score = sum(v.score for v in votes) / len(votes)
            final_decision = "APPROVED"
        elif all_rejected:
            final_score = sum(v.score for v in votes) / len(votes)
            final_decision = "REJECTED"
        else:
            final_score = 0.5
            final_decision = "NEEDS_REVIEW"

        return ConsensusResult(
            final_score=final_score,
            final_decision=final_decision,
            consensus_reached=consensus_reached,
            votes=votes,
            weighted_score=final_score,
            disagreements=self._find_disagreements(votes) if not consensus_reached else [],
            resolution_strategy="unanimous",
            confidence=1.0 if consensus_reached else 0.5,
        )

    def _dynamic_consensus(self, votes: List[AgentVote], request: ReviewRequest) -> ConsensusResult:
        base_consensus = self._weighted_voting_consensus(votes)

        if request.review_depth == "deep" and not base_consensus.consensus_reached:
            base_consensus.final_score *= 0.9
            if base_consensus.final_score < 0.6:
                base_consensus.final_decision = "REJECTED"

        base_consensus.resolution_strategy = "dynamic"
        return base_consensus

    def _calculate_variance(self, values: List[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _find_disagreements(self, votes: List[AgentVote]) -> List[Dict[str, Any]]:
        disagreements = []

        for i, vote_a in enumerate(votes):
            for vote_b in votes[i + 1 :]:
                if abs(vote_a.score - vote_b.score) > self.config.disagreement_threshold:
                    disagreements.append(
                        {
                            "agent_a": vote_a.agent_name,
                            "score_a": vote_a.score,
                            "reasoning_a": vote_a.reasoning[:100],
                            "agent_b": vote_b.agent_name,
                            "score_b": vote_b.score,
                            "reasoning_b": vote_b.reasoning[:100],
                            "difference": abs(vote_a.score - vote_b.score),
                        }
                    )

        return disagreements

    def _generate_recommendations(
        self, votes: List[AgentVote], consensus: ConsensusResult
    ) -> List[str]:
        recommendations: List[str] = []

        all_suggestions = []
        for vote in votes:
            all_suggestions.extend(vote.suggestions)

        recommendations.extend(all_suggestions[:3])

        if consensus.final_score < 0.6:
            recommendations.append("Content requires significant revision before approval")
        elif consensus.final_score < 0.8:
            recommendations.append("Minor revisions recommended to improve quality")

        low_score_agents = [v for v in votes if v.score < 0.5]
        if low_score_agents:
            agent_names = [a.agent_name for a in low_score_agents]
            recommendations.append(f"Pay special attention to {', '.join(agent_names)} concerns")

        return recommendations[:5]

    def _generate_summary(self, votes: List[AgentVote], consensus: ConsensusResult) -> str:
        summary_parts = []

        summary_parts.append(
            f"Decision: {consensus.final_decision} (Score: {consensus.final_score:.2f})"
        )

        agent_summary = ", ".join([f"{v.agent_name}: {v.score:.2f}" for v in votes])
        summary_parts.append(f"Agent Scores: {agent_summary}")

        all_flags = []
        for vote in votes:
            all_flags.extend(vote.flags)

        if all_flags:
            top_issues = all_flags[:3]
            issue_summary = ", ".join([f.get("type", "issue") for f in top_issues])
            summary_parts.append(f"Key Issues: {issue_summary}")

        return " | ".join(summary_parts)

    def get_agent_performance(self) -> Dict[str, Any]:
        return {role.value: agent.get_performance_summary() for role, agent in self.agents.items()}

    def reset_agents(self) -> None:
        for agent in self.agents.values():
            agent.reset()
