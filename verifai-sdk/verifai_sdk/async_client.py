"""Async client for VerifAI SDK"""

import asyncio
import time
from typing import List, Dict, Optional, Any, Union
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from verifai_sdk.models import (
    ReviewResult,
    ImprovedOutput,
    BatchResult,
    ComplianceResult,
    MultiAgentResult,
    CostReport,
    ROIResult,
    Issue,
    ReviewConfig,
    ClientConfig,
    ComplianceFramework,
    AgentRole,
    AgentVote,
)
from verifai_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError,
    TimeoutError,
)
from verifai_sdk.client import VerifAIClient

logger = logging.getLogger(__name__)


class AsyncVerifAIClient:
    """
    Async client for VerifAI API

    Usage:
        client = AsyncVerifAIClient(api_key="your-key")

        # Single review
        result = await client.review("Your AI-generated text")

        # Batch review (concurrent)
        results = await client.batch_review(["text1", "text2", "text3"])

        # Close client
        await client.close()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ClientConfig] = None,
        **kwargs,
    ):
        self.config = config or ClientConfig()

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.api_key = api_key or self.config.api_key
        if not self.api_key:
            import os

            self.api_key = os.environ.get("VERIFAI_API_KEY")

        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set VERIFAI_API_KEY environment variable or pass api_key argument"
            )

        self.base_url = self.config.base_url.rstrip("/")
        self.timeout = self.config.timeout
        self.max_retries = self.config.max_retries

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"verifai-sdk/{__import__('verifai_sdk').__version__}",
            },
        )

        logger.info(f"Async VerifAI client initialized (base_url: {self.base_url})")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make async API request with retry logic"""
        url = f"/{endpoint.lstrip('/')}"

        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout,
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please wait and retry.")
            if response.status_code >= 400:
                error_data = response.json() if response.text else {"error": response.text}
                raise APIError(
                    message=error_data.get("error", f"HTTP {response.status_code}"),
                    status_code=response.status_code,
                    response=error_data,
                )

            return response.json()

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timeout after {self.timeout}s") from e

    async def review(
        self,
        content: str,
        rubric: Optional[List[str]] = None,
        config: Optional[ReviewConfig] = None,
        **kwargs,
    ) -> ReviewResult:
        """Async review of a single output"""
        if config is None:
            config = ReviewConfig()

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        start_time = time.time()
        response = await self._request(
            "POST",
            "review",
            data={
                "content": content,
                "rubric": rubric or config.rubric,
                "compliance": config.compliance.value if config.compliance else None,
                "multi_agent": config.multi_agent,
                "agents": [a.value for a in config.agents] if config.agents else None,
                "depth": config.depth,
                "include_reasoning": config.include_reasoning,
            },
        )
        latency_ms = (time.time() - start_time) * 1000

        return ReviewResult(
            id=response.get("id"),
            original_output=content,
            score=response.get("score", 0.0),
            flags=[Issue(**f) for f in response.get("flags", [])],
            rubric_scores=response.get("rubric_scores", {}),
            compliance_results=response.get("compliance_results"),
            multi_agent_results=[
                AgentVote(**a) for a in response.get("multi_agent_results", [])
            ] if config.multi_agent else None,
            cost=response.get("cost", 0.0),
            latency_ms=latency_ms,
            tokens_used=response.get("tokens_used", 0),
            model_used=response.get("model_used", "gpt-4"),
            reasoning_chain=response.get("reasoning_chain"),
        )

    async def batch_review(
        self,
        contents: List[str],
        rubric: Optional[List[str]] = None,
        max_concurrent: int = 10,
        **kwargs,
    ) -> BatchResult:
        """Async batch review with concurrency"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def review_one(content):
            async with semaphore:
                return await self.review(content, rubric, **kwargs)

        start_time = time.time()
        tasks = [review_one(content) for content in contents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = []
        errors = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({"content": contents[i][:100], "error": str(result)})
            else:
                successful.append(result)

        total_time = (time.time() - start_time) * 1000

        return BatchResult(
            total_items=len(contents),
            successful_items=len(successful),
            failed_items=len(errors),
            results=successful,
            errors=errors,
            average_score=sum(r.score for r in successful) / len(successful) if successful else 0,
            total_cost=sum(r.cost for r in successful),
            total_time_ms=total_time,
        )

    async def improve(
        self,
        result: Union[ReviewResult, str],
        max_iterations: int = 3,
        improvement_threshold: float = 0.05,
        **kwargs,
    ) -> ImprovedOutput:
        """Async output improvement"""
        if isinstance(result, str):
            result = await self.review(result, **kwargs)

        current = result.original_output
        current_score = result.score
        current_flags = result.flags
        changes_made = []
        iterations = 0
        total_cost = result.cost

        for _ in range(max_iterations):
            iterations += 1

            suggestions = await self._get_suggestions(current, current_flags)
            if not suggestions:
                break

            improved = self._apply_improvements(current, suggestions)
            changes_made.extend(suggestions[:2])

            new_result = await self.review(improved, rubric=list(result.rubric_scores.keys()))
            total_cost += new_result.cost

            if new_result.score > current_score + improvement_threshold:
                current = improved
                current_score = new_result.score
                current_flags = new_result.flags
            else:
                break

        return ImprovedOutput(
            original=result.original_output,
            improved=current,
            improvement_delta=current_score - result.score,
            iterations=iterations,
            final_score=current_score,
            changes_made=changes_made,
            cost=total_cost,
        )

    async def _get_suggestions(self, content: str, flags: List[Issue]) -> List[str]:
        """Get improvement suggestions"""
        response = await self._request(
            "POST",
            "suggest",
            data={"content": content, "flags": [f.__dict__ for f in flags]},
        )
        return response.get("suggestions", [])

    def _apply_improvements(self, content: str, suggestions: List[str]) -> str:
        """Apply improvements (sync operation)"""
        improved = content + "\n\n[Improved: " + ", ".join(suggestions[:2]) + "]"
        return improved

    async def check_compliance(
        self,
        content: str,
        framework: ComplianceFramework,
        **kwargs,
    ) -> ComplianceResult:
        """Async compliance check"""
        response = await self._request(
            "POST",
            "compliance",
            data={
                "content": content,
                "framework": framework.value,
                **kwargs,
            },
        )

        return ComplianceResult(
            framework=framework,
            score=response.get("score", 0.0),
            violations=[Issue(**v) for v in response.get("violations", [])],
            remediation=response.get("remediation", []),
            risk_level=response.get("risk_level", "medium"),
            confidence=response.get("confidence", 0.8),
        )

    async def multi_agent_review(
        self,
        content: str,
        agents: Optional[List[AgentRole]] = None,
        depth: str = "standard",
        **kwargs,
    ) -> MultiAgentResult:
        """Async multi-agent review"""
        start_time = time.time()

        response = await self._request(
            "POST",
            "multi-agent",
            data={
                "content": content,
                "agents": [a.value for a in agents] if agents else None,
                "depth": depth,
                **kwargs,
            },
        )

        processing_time = (time.time() - start_time) * 1000

        return MultiAgentResult(
            consensus_decision=response.get("consensus_decision", "NEEDS_REVIEW"),
            final_score=response.get("final_score", 0.0),
            consensus_reached=response.get("consensus_reached", False),
            agent_votes=[AgentVote(**v) for v in response.get("agent_votes", [])],
            disagreements=response.get("disagreements", []),
            recommendations=response.get("recommendations", []),
            summary=response.get("summary", ""),
            processing_time_ms=processing_time,
            cost=response.get("cost", 0.0),
        )

    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
