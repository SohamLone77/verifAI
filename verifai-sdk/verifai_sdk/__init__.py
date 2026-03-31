"""
VerifAI Python SDK - Verify AI, One Output at a Time

A comprehensive SDK for integrating VerifAI's AI quality review capabilities
into your applications.

Features:
- Single and batch review of AI-generated content
- Multi-agent review with specialized agents
- Cost tracking and optimization
- ROI calculation
- Compliance checking (GDPR, HIPAA, etc.)
- Async support
- CLI tools

Usage:
    from verifai_sdk import VerifAIClient

    client = VerifAIClient(api_key="your-api-key")
    result = client.review("Your AI-generated text")
    print(f"Quality score: {result.score}")
"""

__version__ = "1.0.0"
__author__ = "VerifAI Team"
__license__ = "MIT"

from verifai_sdk.client import VerifAIClient, VerifAIClientConfig
from verifai_sdk.async_client import AsyncVerifAIClient
from verifai_sdk.models import (
    ReviewResult,
    ImprovedOutput,
    BatchResult,
    ComplianceResult,
    MultiAgentResult,
    CostReport,
    ROIResult,
    Issue,
    RubricDimension,
)
from verifai_sdk.exceptions import (
    VerifAIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError,
)

__all__ = [
    "VerifAIClient",
    "VerifAIClientConfig",
    "AsyncVerifAIClient",
    "ReviewResult",
    "ImprovedOutput",
    "BatchResult",
    "ComplianceResult",
    "MultiAgentResult",
    "CostReport",
    "ROIResult",
    "Issue",
    "RubricDimension",
    "VerifAIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "APIError",
]
