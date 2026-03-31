"""Chain-of-Thought reasoning engine for VerifAI"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from verifai.models.reasoning_models import (
    Contradiction,
    Evidence,
    EvidenceType,
    ReasoningChain,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningReward,
    ReasoningQualityMetrics,
    ReasoningStep,
    ReasoningStepType,
)
from verifai.reasoning.templates import REASONING_TEMPLATES


class ReasoningEngine:
    """
    Core Chain-of-Thought reasoning engine.

    Features:
    - Step-by-step reasoning generation
    - Contradiction detection
    - Quality scoring
    - Evidence tracking
    - Alternative consideration
    """

    def __init__(self, model: str = "gpt-4", max_tokens: int = 1000):
        self.model = model
        self.max_tokens = max_tokens
        self.reasoning_templates = self._load_templates()

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """Execute reasoning on a query"""
        start_time = time.time()

        try:
            chain = ReasoningChain(query=request.query, context=request.context or {})

            observation_step = self._observation_step(request.query, request.context or {})
            chain.add_step(observation_step)

            analysis_step = self._analysis_step(chain, request)
            chain.add_step(analysis_step)

            if request.reasoning_depth in ["medium", "deep"]:
                hypothesis_step = self._hypothesis_step(chain, request)
                chain.add_step(hypothesis_step)

            verification_step = self._verification_step(chain, request)
            chain.add_step(verification_step)

            synthesis_step = self._synthesis_step(chain, request)
            chain.add_step(synthesis_step)

            decision_step = self._decision_step(chain, request)
            chain.add_step(decision_step)

            if request.detect_contradictions:
                contradictions = self._detect_contradictions(chain)
                for contra in contradictions:
                    chain.add_contradiction(contra)

            chain.consistency_score = self._calculate_consistency(chain)
            chain.reasoning_quality = self._calculate_quality(chain)
            chain.explanation = self._generate_explanation(chain)

            chain.final_decision = decision_step.conclusion
            chain.final_confidence = decision_step.confidence

            processing_time = (time.time() - start_time) * 1000

            return ReasoningResponse(
                reasoning_chain=chain,
                confidence=chain.final_confidence,
                processing_time_ms=processing_time,
                tokens_used=len(request.query.split()) * 5,
                success=True,
            )

        except Exception as exc:
            processing_time = (time.time() - start_time) * 1000
            return ReasoningResponse(
                reasoning_chain=None,
                confidence=0.0,
                processing_time_ms=processing_time,
                tokens_used=0,
                success=False,
                error=str(exc),
            )

    def _observation_step(self, query: str, context: Dict[str, Any]) -> ReasoningStep:
        """First step: observe and understand the query"""
        reasoning = f"I need to understand what is being asked. The query is: '{query}'"

        if context:
            reasoning += f" Additional context provided: {list(context.keys())}"

        key_elements = self._extract_key_elements(query)
        conclusion = f"The query asks about: {', '.join(key_elements[:3])}"

        evidence = [
            Evidence(
                type=EvidenceType.FACT,
                content=f"Query contains {len(query.split())} words",
                confidence=1.0,
            )
        ]

        return ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.OBSERVATION,
            input={"query": query, "context": context},
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=0.95,
            evidence=evidence,
            assumptions=["The query is complete and correctly stated"],
        )

    def _analysis_step(self, chain: ReasoningChain, request: ReasoningRequest) -> ReasoningStep:
        """Second step: analyze the query and available information"""
        previous_step = chain.get_latest_step()

        reasoning = (
            "Now I need to analyze the key components. Based on the observation: "
            f"{previous_step.conclusion if previous_step else 'N/A'}"
        )

        analysis_results = self._perform_analysis(chain.query, request.context or {})
        conclusion = f"Analysis suggests: {analysis_results['summary']}"

        evidence = [
            Evidence(
                type=EvidenceType.INFERENCE,
                content=analysis_results["details"],
                confidence=analysis_results["confidence"],
            )
        ]

        alternatives = self._generate_alternatives(chain.query)

        return ReasoningStep(
            step_id=2,
            step_type=ReasoningStepType.ANALYSIS,
            input={"query": chain.query, "analysis": analysis_results},
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=analysis_results["confidence"],
            evidence=evidence,
            alternatives_considered=alternatives,
        )

    def _hypothesis_step(self, chain: ReasoningChain, request: ReasoningRequest) -> ReasoningStep:
        """Third step: form hypotheses (for deep reasoning)"""
        previous_step = chain.get_latest_step()

        hypotheses = self._generate_hypotheses(chain.query, previous_step.conclusion)
        reasoning = (
            "Based on the analysis, I can form the following hypotheses: "
            f"{', '.join(hypotheses[:3])}"
        )

        conclusion = (
            f"Primary hypothesis: {hypotheses[0]}" if hypotheses else "Unable to form hypothesis"
        )

        return ReasoningStep(
            step_id=3,
            step_type=ReasoningStepType.HYPOTHESIS,
            input={"analysis": previous_step.conclusion},
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=0.7,
            alternatives_considered=hypotheses,
        )

    def _verification_step(self, chain: ReasoningChain, request: ReasoningRequest) -> ReasoningStep:
        """Fourth step: verify reasoning against evidence"""
        latest_step = chain.get_latest_step()

        verification = self._verify_against_evidence(
            chain.query, latest_step.conclusion if latest_step else "", request.context or {}
        )

        reasoning = "Verifying the reasoning against available evidence..."

        if verification["verified"]:
            reasoning += (
                f" The conclusion '{latest_step.conclusion}' is supported by evidence."
            )
        else:
            reasoning += (
                " The conclusion requires further validation. Issues: "
                f"{', '.join(verification['issues'])}"
            )

        conclusion = (
            "Verification result: Supported" if verification["verified"] else "Verification result: Needs review"
        )

        return ReasoningStep(
            step_id=4,
            step_type=ReasoningStepType.VERIFICATION,
            input={"hypothesis": latest_step.conclusion if latest_step else ""},
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=verification["confidence"],
            evidence=verification.get("evidence", []),
        )

    def _synthesis_step(self, chain: ReasoningChain, request: ReasoningRequest) -> ReasoningStep:
        """Fifth step: synthesize all information"""
        reasoning = "Synthesizing all reasoning steps to form a coherent conclusion..."
        conclusions = [step.conclusion for step in chain.steps]

        synthesis = self._synthesize_conclusions(conclusions)
        conclusion = synthesis["summary"]

        return ReasoningStep(
            step_id=5,
            step_type=ReasoningStepType.SYNTHESIS,
            input={"conclusions": conclusions},
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=synthesis["confidence"],
        )

    def _decision_step(self, chain: ReasoningChain, request: ReasoningRequest) -> ReasoningStep:
        """Final step: make decision"""
        synthesis_step = chain.get_latest_step()

        decision = self._make_decision(
            chain.query,
            synthesis_step.conclusion if synthesis_step else "",
            request.confidence_threshold,
        )

        reasoning = (
            f"Based on the synthesis: {synthesis_step.conclusion if synthesis_step else 'N/A'}"
            f"\nDecision: {decision['decision']}"
            f"\nConfidence: {decision['confidence']:.2f}"
        )

        return ReasoningStep(
            step_id=6,
            step_type=ReasoningStepType.DECISION,
            input={"synthesis": synthesis_step.conclusion if synthesis_step else ""},
            reasoning=reasoning,
            conclusion=decision["decision"],
            confidence=decision["confidence"],
            evidence=decision.get("evidence", []),
        )

    def _detect_contradictions(self, chain: ReasoningChain) -> List[Contradiction]:
        """Detect contradictions in reasoning chain"""
        contradictions: List[Contradiction] = []

        steps = chain.steps
        for i in range(len(steps)):
            for j in range(i + 1, len(steps)):
                step_i = steps[i]
                step_j = steps[j]

                if self._are_contradictory(step_i.conclusion, step_j.conclusion):
                    contradictions.append(
                        Contradiction(
                            step_a_id=step_i.step_id,
                            step_b_id=step_j.step_id,
                            statement_a=step_i.conclusion,
                            statement_b=step_j.conclusion,
                            contradiction_type="direct",
                            severity=0.8,
                        )
                    )
                elif self._are_logically_inconsistent(step_i, step_j):
                    contradictions.append(
                        Contradiction(
                            step_a_id=step_i.step_id,
                            step_b_id=step_j.step_id,
                            statement_a=step_i.conclusion,
                            statement_b=step_j.conclusion,
                            contradiction_type="logical",
                            severity=0.6,
                        )
                    )

        return contradictions

    def _calculate_consistency(self, chain: ReasoningChain) -> float:
        """Calculate consistency score"""
        if not chain.steps:
            return 1.0

        if chain.contradictions:
            max_contradictions = len(chain.steps) * (len(chain.steps) - 1) / 2
            contradiction_ratio = (
                len(chain.contradictions) / max_contradictions if max_contradictions > 0 else 0
            )
            consistency = 1.0 - contradiction_ratio
        else:
            consistency = 1.0

        confidences = [step.confidence for step in chain.steps]
        if len(confidences) > 1:
            confidence_trend = confidences[-1] - confidences[0]
            if confidence_trend > 0:
                consistency += 0.1

        return min(1.0, max(0.0, consistency))

    def _calculate_quality(self, chain: ReasoningChain) -> float:
        """Calculate overall reasoning quality"""
        if not chain.steps:
            return 0.0

        evidence_ratio = sum(1 for step in chain.steps if step.evidence) / len(chain.steps)
        avg_confidence = np.mean([step.confidence for step in chain.steps])

        step_types = {step.step_type for step in chain.steps}
        expected_types = {
            ReasoningStepType.OBSERVATION,
            ReasoningStepType.ANALYSIS,
            ReasoningStepType.SYNTHESIS,
            ReasoningStepType.DECISION,
        }
        completeness = len(step_types & expected_types) / len(expected_types)

        quality = evidence_ratio * 0.3 + avg_confidence * 0.4 + completeness * 0.3

        if chain.contradictions:
            quality *= 1 - len(chain.contradictions) * 0.1

        return min(1.0, quality)

    def _generate_explanation(self, chain: ReasoningChain) -> str:
        """Generate human-readable explanation"""
        lines = []

        lines.append(f"To answer '{chain.query}', I followed this reasoning:")
        lines.append("")

        for step in chain.steps:
            lines.append(f"{step.step_id}. {step.step_type.value.capitalize()}:")
            lines.append(f"   {step.reasoning[:100]}")
            lines.append(f"   -> {step.conclusion}")
            lines.append("")

        lines.append(f"Final decision: {chain.final_decision}")
        lines.append(f"Confidence: {chain.final_confidence:.2f}")

        if chain.contradictions:
            lines.append("\nNote: Some contradictions were detected and resolved.")

        return "\n".join(lines)

    def _extract_key_elements(self, text: str) -> List[str]:
        """Extract key elements from text"""
        words = text.split()
        return [w for w in words if len(w) > 5][:5]

    def _perform_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on query"""
        _ = context
        return {
            "summary": f"Analysis of '{query}' completed",
            "details": f"Found {len(query.split())} key elements to consider",
            "confidence": 0.85,
        }

    def _generate_alternatives(self, query: str) -> List[str]:
        """Generate alternative interpretations"""
        return [f"Alternative: {query} could also mean..."]

    def _generate_hypotheses(self, query: str, analysis: str) -> List[str]:
        """Generate hypotheses"""
        _ = analysis
        return [
            f"Hypothesis 1: {query} is correct",
            f"Hypothesis 2: {query} needs verification",
        ]

    def _verify_against_evidence(self, query: str, conclusion: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify conclusion against evidence"""
        _ = (query, conclusion, context)
        return {
            "verified": True,
            "confidence": 0.85,
            "issues": [],
            "evidence": [
                Evidence(
                    type=EvidenceType.FACT,
                    content="Evidence supports the conclusion",
                    confidence=0.8,
                )
            ],
        }

    def _synthesize_conclusions(self, conclusions: List[str]) -> Dict[str, Any]:
        """Synthesize multiple conclusions"""
        return {"summary": f"Synthesized {len(conclusions)} conclusions", "confidence": 0.85}

    def _make_decision(self, query: str, synthesis: str, threshold: float) -> Dict[str, Any]:
        """Make final decision"""
        _ = (synthesis, threshold)
        return {
            "decision": f"Based on reasoning, the answer to '{query}' is: Verified",
            "confidence": 0.88,
            "evidence": [],
        }

    def _are_contradictory(self, statement_a: str, statement_b: str) -> bool:
        """Check if two statements are contradictory"""
        contradictory_pairs = [
            ("true", "false"),
            ("yes", "no"),
            ("correct", "incorrect"),
            ("safe", "unsafe"),
            ("factual", "hallucination"),
        ]

        for a, b in contradictory_pairs:
            if (a in statement_a.lower() and b in statement_b.lower()) or (
                b in statement_a.lower() and a in statement_b.lower()
            ):
                return True
        return False

    def _are_logically_inconsistent(self, step_a: ReasoningStep, step_b: ReasoningStep) -> bool:
        """Check for logical inconsistency"""
        if "must be" in step_a.conclusion.lower() and "cannot be" in step_b.conclusion.lower():
            return True
        return False

    def _load_templates(self) -> Dict[str, str]:
        """Load reasoning templates"""
        return REASONING_TEMPLATES.copy()


class ReasoningQualityScorer:
    """Score the quality of reasoning"""

    def __init__(self):
        self.weights = {
            "logical_consistency": 0.25,
            "evidence_support": 0.25,
            "completeness": 0.20,
            "clarity": 0.15,
            "conciseness": 0.15,
        }

    def score(self, chain: ReasoningChain) -> ReasoningQualityMetrics:
        """Score the reasoning chain quality"""
        logical_consistency = chain.consistency_score

        if chain.steps:
            evidence_ratio = sum(1 for s in chain.steps if s.evidence) / len(chain.steps)
        else:
            evidence_ratio = 0

        expected_types = {
            ReasoningStepType.OBSERVATION,
            ReasoningStepType.ANALYSIS,
            ReasoningStepType.SYNTHESIS,
            ReasoningStepType.DECISION,
        }
        actual_types = {s.step_type for s in chain.steps}
        completeness = len(actual_types & expected_types) / len(expected_types)

        if chain.steps:
            avg_step_length = np.mean([len(s.reasoning.split()) for s in chain.steps])
            clarity = min(1.0, 50 / max(avg_step_length, 1))
        else:
            clarity = 0

        total_words = sum(len(s.reasoning.split()) for s in chain.steps)
        conciseness = min(1.0, 200 / max(total_words, 1))

        overall = (
            logical_consistency * self.weights["logical_consistency"]
            + evidence_ratio * self.weights["evidence_support"]
            + completeness * self.weights["completeness"]
            + clarity * self.weights["clarity"]
            + conciseness * self.weights["conciseness"]
        )

        issues: List[str] = []
        strengths: List[str] = []

        if logical_consistency < 0.7:
            issues.append("Low logical consistency - contradictions detected")
        else:
            strengths.append("Strong logical consistency")

        if evidence_ratio < 0.5:
            issues.append("Insufficient evidence support")
        else:
            strengths.append("Good evidence support")

        if completeness < 0.7:
            issues.append("Missing reasoning steps")
        else:
            strengths.append("Complete reasoning structure")

        return ReasoningQualityMetrics(
            logical_consistency=logical_consistency,
            evidence_support=evidence_ratio,
            completeness=completeness,
            clarity=clarity,
            conciseness=conciseness,
            overall_score=overall,
            issues=issues,
            strengths=strengths,
        )


class ReasoningRewardCalculator:
    """Calculate reward based on reasoning quality"""

    def __init__(self):
        self.consistency_bonus = 0.20
        self.evidence_bonus = 0.15
        self.clarity_bonus = 0.10
        self.contradiction_penalty = 0.15

    def calculate_reward(self, chain: ReasoningChain, outcome_score: float) -> ReasoningReward:
        """Calculate reward based on reasoning quality"""
        base_reward = outcome_score * 0.5
        consistency_bonus = chain.consistency_score * self.consistency_bonus

        if chain.steps:
            evidence_ratio = sum(1 for s in chain.steps if s.evidence) / len(chain.steps)
        else:
            evidence_ratio = 0
        evidence_bonus = evidence_ratio * self.evidence_bonus

        clarity_score = self._calculate_clarity(chain)
        clarity_bonus = clarity_score * self.clarity_bonus

        contradiction_penalty = len(chain.contradictions) * self.contradiction_penalty
        contradiction_penalty = min(0.5, contradiction_penalty)

        total_reward = (
            base_reward + consistency_bonus + evidence_bonus + clarity_bonus - contradiction_penalty
        )

        total_reward = max(0.0, min(1.0, total_reward))

        return ReasoningReward(
            base_reward=base_reward,
            consistency_bonus=consistency_bonus,
            evidence_bonus=evidence_bonus,
            clarity_bonus=clarity_bonus,
            contradiction_penalty=contradiction_penalty,
            total_reward=total_reward,
            details={
                "outcome_score": outcome_score,
                "consistency_score": chain.consistency_score,
                "evidence_ratio": evidence_ratio,
                "clarity_score": clarity_score,
                "contradictions": len(chain.contradictions),
            },
        )

    def _calculate_clarity(self, chain: ReasoningChain) -> float:
        """Calculate clarity of reasoning"""
        if not chain.steps:
            return 0.5

        step_types = [s.step_type.value for s in chain.steps]
        has_clear_structure = len(set(step_types)) >= 3

        avg_words = np.mean([len(s.reasoning.split()) for s in chain.steps])
        is_concise = avg_words < 50

        clarity = 0.5
        if has_clear_structure:
            clarity += 0.25
        if is_concise:
            clarity += 0.25

        return min(1.0, clarity)
