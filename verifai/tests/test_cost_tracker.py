"""Unit tests for cost tracking features"""

import unittest

from verifai.environment.cost_tracker import CostTracker, CostAwareActionSelector
from verifai.optimization.cost_optimizer import CostOptimizer
from verifai.optimization.budget_manager import BudgetManager
from verifai.models.cost_models import CostEventType, BudgetConfig


class TestCostTracker(unittest.TestCase):
    """Test CostTracker functionality"""

    def setUp(self):
        self.tracker = CostTracker()

    def test_calculate_cost(self):
        """Test cost calculation"""
        cost = self.tracker.calculate_cost("gpt-4", 1000, 500)
        self.assertGreater(cost, 0)
        self.assertLess(cost, 0.10)
        self.assertAlmostEqual(cost, 0.06, places=3)

    def test_log_event(self):
        """Test logging events"""
        event = self.tracker.log_event(
            model="gpt-4",
            input_tokens=1000,
            output_tokens=500,
            event_type=CostEventType.REVIEW,
            episode_id=1,
        )

        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.cost, 0.06)
        self.assertEqual(len(self.tracker.events), 1)

    def test_total_cost(self):
        """Test total cost calculation"""
        self.tracker.log_event("gpt-4", 1000, 500, CostEventType.REVIEW)
        self.tracker.log_event("gpt-3.5-turbo", 500, 200, CostEventType.REVIEW)

        total = self.tracker.total_cost()
        self.assertGreater(total, 0)

    def test_cost_breakdown(self):
        """Test cost breakdown by model"""
        self.tracker.log_event("gpt-4", 1000, 500, CostEventType.REVIEW)
        self.tracker.log_event("gpt-4", 2000, 1000, CostEventType.REWRITE)
        self.tracker.log_event("gpt-3.5-turbo", 500, 200, CostEventType.REVIEW)

        by_model = self.tracker.cost_by_model()

        self.assertIn("gpt-4", by_model)
        self.assertIn("gpt-3.5-turbo", by_model)
        self.assertGreater(by_model["gpt-4"], by_model["gpt-3.5-turbo"])

    def test_efficiency_score(self):
        """Test efficiency score calculation"""
        self.tracker.record_quality(0.9)
        self.tracker.record_quality(0.85)

        self.tracker.log_event("gpt-4", 1000, 500, CostEventType.REVIEW)

        score = self.tracker.efficiency_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)

    def test_budget_monitoring(self):
        """Test budget monitoring"""
        config = BudgetConfig(monthly_budget=1.0)
        tracker = CostTracker(budget_config=config)

        tracker.log_event("gpt-4", 10000, 5000, CostEventType.REVIEW)

        budget_status = tracker.get_budget_status()
        self.assertIn("status", budget_status)


class TestCostOptimizer(unittest.TestCase):
    """Test CostOptimizer functionality"""

    def setUp(self):
        self.tracker = CostTracker()
        self.optimizer = CostOptimizer(self.tracker)

        for i in range(100):
            self.tracker.log_event(
                model="gpt-4" if i < 60 else "gpt-3.5-turbo",
                input_tokens=1000,
                output_tokens=500,
                event_type=CostEventType.REVIEW,
                episode_id=i % 10,
            )
            self.tracker.record_quality(0.8)

    def test_analyze_costs(self):
        """Test cost analysis"""
        suggestions = self.optimizer.analyze_costs(days=7)

        self.assertIsInstance(suggestions, list)
        if suggestions:
            self.assertIsNotNone(suggestions[0].suggestion_id)
            self.assertIsNotNone(suggestions[0].title)

    def test_generate_report(self):
        """Test report generation"""
        report = self.optimizer.generate_optimization_report(days=7)

        self.assertIsNotNone(report.report_id)
        self.assertIsNotNone(report.current_costs)
        self.assertIsNotNone(report.suggestions)
        self.assertGreaterEqual(report.total_savings, 0)


class TestBudgetManager(unittest.TestCase):
    """Test BudgetManager functionality"""

    def setUp(self):
        self.tracker = CostTracker()
        self.manager = BudgetManager(self.tracker)

    def test_can_make_request(self):
        """Test request permission"""
        self.assertTrue(self.manager.can_make_request(0.01))

        self.manager.pause_spending()
        self.assertFalse(self.manager.can_make_request(0.01))

        self.manager.resume_spending()
        self.assertTrue(self.manager.can_make_request(0.01))

    def test_budget_forecast(self):
        """Test budget forecasting"""
        for _ in range(100):
            self.tracker.log_event(
                model="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                event_type=CostEventType.REVIEW,
            )

        forecast = self.manager.get_budget_forecast(days=7)

        self.assertIn("current_spending", forecast)
        self.assertIn("daily_average", forecast)
        self.assertIn("forecast", forecast)
        self.assertEqual(len(forecast["forecast"]), 7)


class TestCostAwareActionSelector(unittest.TestCase):
    """Test action selector with cost awareness"""

    def setUp(self):
        self.tracker = CostTracker()
        self.selector = CostAwareActionSelector(self.tracker)

    def test_select_model(self):
        """Test model selection based on quality requirements"""
        model = self.selector.select_model(required_quality=0.9)
        self.assertIn(model, ["gpt-4", "claude-3-opus"])

        model = self.selector.select_model(required_quality=0.7)
        self.assertIn(model, ["gpt-4-turbo", "claude-3-sonnet"])

        model = self.selector.select_model(required_quality=0.5, prefer_fast=True)
        self.assertIsNotNone(model)

    def test_should_skip_review(self):
        """Test review skipping logic"""
        skip = self.selector.should_skip_review(
            confidence=0.95,
            previous_score=0.9,
            cost_estimate=0.05,
        )
        self.assertTrue(skip)

        skip = self.selector.should_skip_review(
            confidence=0.6,
            previous_score=0.9,
            cost_estimate=0.05,
        )
        self.assertFalse(skip)

    def test_select_batch_size(self):
        """Test batch size selection"""
        for _ in range(10):
            self.tracker.log_event(
                model="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                event_type=CostEventType.REVIEW,
            )

        batch_size = self.selector.select_batch_size(total_items=100)
        self.assertGreater(batch_size, 0)
        self.assertLessEqual(batch_size, 50)


if __name__ == "__main__":
    unittest.main()
