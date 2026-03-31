"""Unit tests for Chain-of-Thought reasoning"""

import unittest

from verifai.models.reasoning_models import (
    Contradiction,
    Evidence,
    EvidenceType,
    ReasoningChain,
    ReasoningRequest,
    ReasoningStep,
    ReasoningStepType,
)
from verifai.environment.chain_of_thought import (
    ReasoningEngine,
    ReasoningQualityScorer,
    ReasoningRewardCalculator,
)


class TestReasoningStep(unittest.TestCase):
    """Test ReasoningStep model"""

    def test_create_step(self):
        step = ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.OBSERVATION,
            reasoning="I observe that...",
            conclusion="The observation is...",
            confidence=0.95,
        )

        self.assertEqual(step.step_id, 1)
        self.assertEqual(step.step_type, ReasoningStepType.OBSERVATION)
        self.assertEqual(step.confidence, 0.95)

    def test_step_with_evidence(self):
        evidence = Evidence(type=EvidenceType.FACT, content="Evidence content", confidence=0.9)

        step = ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.ANALYSIS,
            reasoning="Analysis...",
            conclusion="Conclusion...",
            confidence=0.85,
            evidence=[evidence],
        )

        self.assertEqual(len(step.evidence), 1)
        self.assertEqual(step.evidence[0].content, "Evidence content")


class TestReasoningChain(unittest.TestCase):
    """Test ReasoningChain model"""

    def setUp(self):
        self.chain = ReasoningChain(
            query="Test query",
            final_decision="Test decision",
            final_confidence=0.9,
            explanation="Test explanation",
        )

    def test_add_step(self):
        step = ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.OBSERVATION,
            reasoning="Observing...",
            conclusion="Observation complete",
            confidence=0.95,
        )

        self.chain.add_step(step)
        self.assertEqual(len(self.chain.steps), 1)
        self.assertEqual(self.chain.get_step(1), step)

    def test_add_contradiction(self):
        contradiction = Contradiction(
            step_a_id=1,
            step_b_id=2,
            statement_a="Statement A",
            statement_b="Statement B",
            contradiction_type="direct",
            severity=0.8,
        )

        self.chain.add_contradiction(contradiction)
        self.assertEqual(len(self.chain.contradictions), 1)

    def test_to_markdown(self):
        step = ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.OBSERVATION,
            reasoning="Observing...",
            conclusion="Observation complete",
            confidence=0.95,
        )
        self.chain.add_step(step)

        markdown = self.chain.to_markdown()
        self.assertIn("Reasoning Chain", markdown)
        self.assertIn("Test query", markdown)


class TestReasoningEngine(unittest.TestCase):
    """Test ReasoningEngine functionality"""

    def setUp(self):
        self.engine = ReasoningEngine()

    def test_reason_basic(self):
        """Test basic reasoning"""
        request = ReasoningRequest(query="What is the capital of France?", reasoning_depth="shallow")

        response = self.engine.reason(request)

        self.assertTrue(response.success)
        self.assertIsNotNone(response.reasoning_chain)
        self.assertGreater(response.confidence, 0)
        self.assertGreater(response.processing_time_ms, 0)

    def test_reason_deep(self):
        """Test deep reasoning"""
        request = ReasoningRequest(
            query="The Eiffel Tower is in Berlin. Is this true?",
            reasoning_depth="deep",
            detect_contradictions=True,
        )

        response = self.engine.reason(request)

        self.assertTrue(response.success)
        chain = response.reasoning_chain

        self.assertGreater(len(chain.steps), 3)
        self.assertIsNotNone(chain.final_decision)

    def test_contradiction_detection(self):
        """Test contradiction detection"""
        request = ReasoningRequest(query="Test with contradictory information", detect_contradictions=True)

        response = self.engine.reason(request)

        if response.success and response.reasoning_chain:
            self.assertIsNotNone(response.reasoning_chain.contradictions)


class TestReasoningQualityScorer(unittest.TestCase):
    """Test quality scoring"""

    def setUp(self):
        self.scorer = ReasoningQualityScorer()
        self.chain = ReasoningChain(
            query="Test query",
            final_decision="Test decision",
            final_confidence=0.8,
            explanation="Test explanation",
        )

    def test_score_empty_chain(self):
        """Test scoring empty chain"""
        metrics = self.scorer.score(self.chain)

        self.assertIsNotNone(metrics)
        self.assertGreaterEqual(metrics.overall_score, 0)
        self.assertLessEqual(metrics.overall_score, 1)

    def test_score_with_steps(self):
        """Test scoring chain with steps"""
        step = ReasoningStep(
            step_id=1,
            step_type=ReasoningStepType.OBSERVATION,
            reasoning="Observation",
            conclusion="Conclusion",
            confidence=0.9,
            evidence=[Evidence(type=EvidenceType.FACT, content="Evidence", confidence=0.8)],
        )
        self.chain.add_step(step)

        metrics = self.scorer.score(self.chain)

        self.assertGreater(metrics.evidence_support, 0)
        self.assertIsInstance(metrics.issues, list)
        self.assertIsInstance(metrics.strengths, list)


class TestReasoningRewardCalculator(unittest.TestCase):
    """Test reward calculation"""

    def setUp(self):
        self.calculator = ReasoningRewardCalculator()
        self.chain = ReasoningChain(
            query="Test query",
            final_decision="Test decision",
            final_confidence=0.9,
            explanation="Test explanation",
            consistency_score=0.9,
        )

    def test_calculate_reward(self):
        """Test reward calculation"""
        reward = self.calculator.calculate_reward(self.chain, outcome_score=0.8)

        self.assertIsNotNone(reward)
        self.assertGreaterEqual(reward.total_reward, 0)
        self.assertLessEqual(reward.total_reward, 1)
        self.assertGreater(reward.base_reward, 0)


class TestReasoningIntegration(unittest.TestCase):
    """Integration tests for reasoning system"""

    def test_full_pipeline(self):
        """Test full reasoning pipeline"""
        engine = ReasoningEngine()
        scorer = ReasoningQualityScorer()
        calculator = ReasoningRewardCalculator()

        request = ReasoningRequest(
            query="The product is the best ever created. Is this appropriate marketing?",
            reasoning_depth="medium",
            detect_contradictions=True,
        )

        response = engine.reason(request)

        self.assertTrue(response.success)

        chain = response.reasoning_chain

        quality = scorer.score(chain)
        reward = calculator.calculate_reward(chain, outcome_score=0.7)

        self.assertIsNotNone(chain)
        self.assertGreater(quality.overall_score, 0)
        self.assertGreater(reward.total_reward, 0)

        step_types = [s.step_type.value for s in chain.steps]
        self.assertIn("observation", step_types)
        self.assertIn("analysis", step_types)
        self.assertIn("decision", step_types)


if __name__ == "__main__":
    unittest.main()
