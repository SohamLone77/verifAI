"""Unit tests for multi-modal review features"""

import unittest
import base64
import json
from PIL import Image
import io
import tempfile
import os

from verifai.models.multimodal import (
    ReviewConfig, SafetyViolation, SafetyViolationType,
    ImageReviewResult, AudioReviewResult, VideoReviewResult
)
from verifai.environment.multimodal_review import (
    MultiModalReviewer, ImageAnalyzer, MultiModalReward
)


class TestImageAnalyzer(unittest.TestCase):
    """Test image analysis functionality"""

    def setUp(self):
        self.config = ReviewConfig()
        self.analyzer = ImageAnalyzer(self.config)

        # Create a test image
        self.test_image = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        self.test_image.save(img_bytes, format='PNG')
        self.test_image_base64 = base64.b64encode(img_bytes.getvalue()).decode()

    def test_analyze_safety(self):
        """Test safety analysis"""
        violations, score = self.analyzer.analyze_safety(self.test_image)
        self.assertIsInstance(violations, list)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_detect_brand_violations(self):
        """Test brand violation detection"""
        violations = self.analyzer.detect_brand_violations(self.test_image)
        self.assertIsInstance(violations, list)

    def test_detect_deepfake(self):
        """Test deepfake detection"""
        result = self.analyzer.detect_deepfake(self.test_image)
        self.assertIsNotNone(result)
        self.assertIsInstance(result.is_deepfake, bool)
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)


class TestMultiModalReviewer(unittest.TestCase):
    """Test main multi-modal reviewer"""

    def setUp(self):
        self.reviewer = MultiModalReviewer()

        # Create test image
        test_img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='PNG')
        self.test_image_base64 = base64.b64encode(img_bytes.getvalue()).decode()

    def test_review_image(self):
        """Test image review"""
        result = self.reviewer.review_image(self.test_image_base64)

        self.assertIsInstance(result, ImageReviewResult)
        self.assertIsNotNone(result.image_id)
        self.assertGreaterEqual(result.overall_safety_score, 0.0)
        self.assertLessEqual(result.overall_safety_score, 1.0)
        self.assertIsInstance(result.flags, list)

    def test_review_image_with_safety_only(self):
        """Test image review with safety only"""
        result = self.reviewer.review_image(self.test_image_base64, review_type="safety")

        self.assertIsInstance(result, ImageReviewResult)
        self.assertGreaterEqual(result.overall_safety_score, 0.0)

    def test_review_audio(self):
        """Test audio review"""
        # Create a simple test audio (simulated)
        test_audio = b'\x00' * 1024  # Simulated audio bytes
        test_audio_base64 = base64.b64encode(test_audio).decode()

        result = self.reviewer.review_audio(test_audio_base64)

        self.assertIsInstance(result, AudioReviewResult)
        self.assertIsNotNone(result.audio_id)
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 1.0)

    def test_review_video(self):
        """Test video review"""
        # Create a simple test video (simulated)
        test_video = b'\x00' * 1024 * 100  # Simulated video bytes
        test_video_base64 = base64.b64encode(test_video).decode()

        result = self.reviewer.review_video(test_video_base64, frame_interval=10, max_frames=20)

        self.assertIsInstance(result, VideoReviewResult)
        self.assertIsNotNone(result.video_id)
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 1.0)


class TestMultiModalReward(unittest.TestCase):
    """Test reward calculation"""

    def setUp(self):
        self.reward = MultiModalReward()

    def test_calculate_reward(self):
        """Test reward calculation"""
        result = self.reward.calculate_reward(
            detection_time_ms=100,
            detection_accuracy=0.9,
            false_positives=0,
            severity=0.8
        )

        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.total_reward, 0.0)
        self.assertLessEqual(result.total_reward, 1.0)

    def test_false_positive_penalty(self):
        """Test false positive penalty"""
        result = self.reward.calculate_reward(
            detection_time_ms=100,
            detection_accuracy=0.9,
            false_positives=3,
            severity=0.8
        )

        # With false positives, reward should be lower
        result_no_fp = self.reward.calculate_reward(
            detection_time_ms=100,
            detection_accuracy=0.9,
            false_positives=0,
            severity=0.8
        )

        self.assertLess(result.total_reward, result_no_fp.total_reward)

    def test_speed_penalty(self):
        """Test speed penalty"""
        fast_result = self.reward.calculate_reward(
            detection_time_ms=50,
            detection_accuracy=0.9,
            false_positives=0,
            severity=0.8,
            expected_time_ms=500
        )

        slow_result = self.reward.calculate_reward(
            detection_time_ms=1000,
            detection_accuracy=0.9,
            false_positives=0,
            severity=0.8,
            expected_time_ms=500
        )

        self.assertGreater(fast_result.total_reward, slow_result.total_reward)


class TestIntegration(unittest.TestCase):
    """Integration tests for multi-modal features"""

    def setUp(self):
        self.reviewer = MultiModalReviewer()

    def test_full_pipeline(self):
        """Test full multi-modal review pipeline"""

        # Create test image
        test_img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format='PNG')
        test_image_base64 = base64.b64encode(img_bytes.getvalue()).decode()

        # Review image
        result = self.reviewer.review_image(test_image_base64)

        # Verify results
        self.assertIsInstance(result, ImageReviewResult)
        self.assertTrue(0.0 <= result.overall_safety_score <= 1.0)
        self.assertTrue(0.0 <= result.brand_compliance_score <= 1.0)
        self.assertTrue(0.0 <= result.authenticity_score <= 1.0)

        # Verify metadata
        self.assertIsNotNone(result.image_id)
        self.assertTrue(result.dimensions["width"] > 0)
        self.assertTrue(result.dimensions["height"] > 0)
        self.assertTrue(result.processing_time_ms > 0)


if __name__ == '__main__':
    unittest.main()
