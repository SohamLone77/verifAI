"""Unit tests for multi-agent system"""

import unittest

from verifai.agents.brand_agent import BrandAgent
from verifai.agents.factuality_agent import FactualityAgent
from verifai.agents.multi_agent_panel import MultiAgentPanel
from verifai.agents.safety_agent import SafetyAgent
from verifai.models.agent_models import ReviewRequest


class TestSafetyAgent(unittest.TestCase):
    def test_detects_safety_risk(self):
        agent = SafetyAgent()
        vote = agent.review("This includes a bomb threat")
        self.assertLess(vote.score, 1.0)
        self.assertTrue(vote.flags)


class TestFactualityAgent(unittest.TestCase):
    def test_detects_factual_error(self):
        agent = FactualityAgent()
        vote = agent.review("The Eiffel Tower is in Berlin and was built in 2020.")
        self.assertLess(vote.score, 1.0)
        self.assertTrue(vote.flags)


class TestBrandAgent(unittest.TestCase):
    def test_detects_brand_overpromise(self):
        agent = BrandAgent()
        vote = agent.review("This is the best ever solution and guaranteed results.")
        self.assertLess(vote.score, 1.0)
        self.assertTrue(vote.flags)


class TestMultiAgentPanel(unittest.TestCase):
    def test_panel_review(self):
        panel = MultiAgentPanel()
        request = ReviewRequest(content="This product is the best ever!")
        response = panel.review(request)

        self.assertIsNotNone(response.consensus)
        self.assertGreaterEqual(response.consensus.final_score, 0.0)
        self.assertLessEqual(response.consensus.final_score, 1.0)
        self.assertTrue(response.agent_responses)
        self.assertTrue(response.summary)


if __name__ == "__main__":
    unittest.main()
