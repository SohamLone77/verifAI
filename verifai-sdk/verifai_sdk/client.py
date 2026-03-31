"""Main synchronous client for VerifAI SDK"""

import os
import time
import hashlib
import json
from typing import List, Dict, Optional, Any, Union, Iterator
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
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
    RubricDimension,
    ReviewConfig,
    ClientConfig,
    ComplianceFramework,
    AgentRole,
    CostBreakdown,
    AgentVote,
)
from verifai_sdk.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError,
    ValidationError,
    TimeoutError,
)
from verifai_sdk.cache import ResponseCache
from verifai_sdk.utils import (
    validate_api_key,
    validate_content,
    format_duration,
    calculate_cost,
)

logger = logging.getLogger(__name__)

VerifAIClientConfig = ClientConfig


class VerifAIClient:
    """
    Main client for VerifAI API

    Features:
    - Single and batch review
    - Output improvement
    - Compliance checking
    - Multi-agent review
    - Cost tracking
    - ROI calculation
    - Response caching
    - Automatic retries

    Usage:
        client = VerifAIClient(api_key="your-key")

        # Single review
        result = client.review("Your AI-generated text")
        print(f"Score: {result.score}")

        # Batch review
        results = client.batch_review(["text1", "text2", "text3"])

        # Improve output
        improved = client.improve(result)

        # Compliance check
        compliance = client.check_compliance("Text", framework="GDPR")

        # Multi-agent review
        multi = client.multi_agent_review("Content", agents=["safety", "factuality"])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[ClientConfig] = None,
        **kwargs,
    ):
        """
        Initialize VerifAI client

        Args:
            api_key: Your VerifAI API key (can also be set via VERIFAI_API_KEY env var)
            config: Client configuration
            **kwargs: Override config values
        """
        self.config = config or ClientConfig()

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.api_key = api_key or self.config.api_key or os.environ.get("VERIFAI_API_KEY")

        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set VERIFAI_API_KEY environment variable or pass api_key argument"
            )

        validate_api_key(self.api_key)

        self.base_url = self.config.base_url.rstrip("/")
        self.timeout = self.config.timeout
        self.max_retries = self.config.max_retries
        self.cache = ResponseCache(ttl=self.config.cache_ttl) if self.config.cache_enabled else None

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._get_headers(),
        )

        logger.info(f"VerifAI client initialized (base_url: {self.base_url})")

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"verifai-sdk/{__import__('verifai_sdk').__version__}",
        }

    def _get_cache_key(self, endpoint: str, data: Dict) -> str:
        """Generate cache key for request"""
        key_data = {
            "endpoint": endpoint,
            "data": data,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Make API request with retry logic

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            use_cache: Whether to use cache

        Returns:
            Response data
        """
        url = f"/{endpoint.lstrip('/')}"
        cache_key = self._get_cache_key(url, data) if use_cache else None

        if use_cache and self.cache and cache_key:
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {url}")
                return cached

        try:
            response = self._client.request(
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

            result = response.json()

            if use_cache and self.cache and cache_key:
                self.cache.set(cache_key, result)

            return result

        except httpx.TimeoutException as e:
            raise TimeoutError(f"Request timeout after {self.timeout}s") from e
        except httpx.HTTPError as e:
            status_code = 500
            response = getattr(e, "response", None)
            if response is not None:
                status_code = response.status_code
            raise APIError(f"HTTP error: {str(e)}", status_code=status_code) from e

    def review(
        self,
        content: str,
        rubric: Optional[List[str]] = None,
        config: Optional[ReviewConfig] = None,
        **kwargs,
    ) -> ReviewResult:
        """
        Review a single output

        Args:
            content: The text to review
            rubric: List of rubric dimensions (e.g., ["safety", "factuality"])
            config: Review configuration
            **kwargs: Override config values

        Returns:
            ReviewResult object
        """
        validate_content(content)

        if config is None:
            config = ReviewConfig()

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        data = {
            "content": content,
            "rubric": rubric or config.rubric,
            "compliance": config.compliance.value if config.compliance else None,
            "multi_agent": config.multi_agent,
            "agents": [a.value for a in config.agents] if config.agents else None,
            "depth": config.depth,
            "include_reasoning": config.include_reasoning,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }

        start_time = time.time()
        response = self._request("POST", "review", data)
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
            metadata=response.get("metadata", {}),
        )

    def batch_review(
        self,
        contents: List[str],
        rubric: Optional[List[str]] = None,
        max_concurrent: int = 5,
        **kwargs,
    ) -> BatchResult:
        """
        Review multiple outputs in batch

        Args:
            contents: List of texts to review
            rubric: List of rubric dimensions
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional review parameters

        Returns:
            BatchResult object
        """
        import concurrent.futures

        results = []
        errors = []
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {
                executor.submit(self.review, content, rubric, **kwargs): content
                for content in contents
            }

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append({
                        "content": futures[future][:100],
                        "error": str(e),
                    })

        total_time = (time.time() - start_time) * 1000

        return BatchResult(
            total_items=len(contents),
            successful_items=len(results),
            failed_items=len(errors),
            results=results,
            errors=errors,
            average_score=sum(r.score for r in results) / len(results) if results else 0,
            total_cost=sum(r.cost for r in results),
            total_time_ms=total_time,
        )

    def improve(
        self,
        result: Union[ReviewResult, str],
        max_iterations: int = 3,
        improvement_threshold: float = 0.05,
        **kwargs,
    ) -> ImprovedOutput:
        """
        Iteratively improve output based on review

        Args:
            result: ReviewResult object or string to review and improve
            max_iterations: Maximum improvement iterations
            improvement_threshold: Minimum improvement to continue
            **kwargs: Additional review parameters

        Returns:
            ImprovedOutput object
        """
        start_time = time.time()

        if isinstance(result, str):
            result = self.review(result, **kwargs)

        current = result.original_output
        current_score = result.score
        current_flags = result.flags
        changes_made = []
        iterations = 0
        total_cost = result.cost

        for _ in range(max_iterations):
            iterations += 1

            suggestions = self._get_suggestions(current, current_flags)

            if not suggestions:
                break

            improved = self._apply_improvements(current, suggestions)
            changes_made.extend(suggestions[:2])

            new_result = self.review(improved, rubric=list(result.rubric_scores.keys()))
            total_cost += new_result.cost

            if new_result.score > current_score + improvement_threshold:
                current = improved
                current_score = new_result.score
                current_flags = new_result.flags
            else:
                break

        processing_time = (time.time() - start_time) * 1000

        return ImprovedOutput(
            original=result.original_output,
            improved=current,
            improvement_delta=current_score - result.score,
            iterations=iterations,
            final_score=current_score,
            changes_made=changes_made,
            cost=total_cost,
            processing_time_ms=processing_time,
        )

    def _get_suggestions(self, content: str, flags: List[Issue]) -> List[str]:
        """Get improvement suggestions from API"""
        response = self._request(
            "POST",
            "suggest",
            data={"content": content, "flags": [f.__dict__ for f in flags]},
        )
        return response.get("suggestions", [])

    def _apply_improvements(self, content: str, suggestions: List[str]) -> str:
        """Apply improvement suggestions to content"""
        response = self._request(
            "POST",
            "apply",
            data={"content": content, "suggestions": suggestions},
        )
        return response.get("improved_content", content)

    def check_compliance(
        self,
        content: str,
        framework: ComplianceFramework,
        **kwargs,
    ) -> ComplianceResult:
        """
        Check content against compliance framework

        Args:
            content: Text to check
            framework: Compliance framework (GDPR, HIPAA, etc.)
            **kwargs: Additional parameters

        Returns:
            ComplianceResult object
        """
        response = self._request(
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

    def multi_agent_review(
        self,
        content: str,
        agents: Optional[List[AgentRole]] = None,
        depth: str = "standard",
        **kwargs,
    ) -> MultiAgentResult:
        """
        Run multi-agent review with specialized agents

        Args:
            content: Text to review
            agents: List of agent roles to use
            depth: Review depth (quick, standard, deep)
            **kwargs: Additional parameters

        Returns:
            MultiAgentResult object
        """
        start_time = time.time()

        response = self._request(
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

    def get_cost_report(self, days: int = 30) -> CostReport:
        """Get cost tracking report"""
        response = self._request("GET", f"cost/report?days={days}")

        breakdown = CostBreakdown(
            by_model=response.get("breakdown", {}).get("by_model", {}),
            by_agent=response.get("breakdown", {}).get("by_agent", {}),
            by_task=response.get("breakdown", {}).get("by_task", {}),
            total_cost=response.get("breakdown", {}).get("total_cost", 0),
            average_cost_per_review=response.get("breakdown", {}).get("average_cost", 0),
        )

        return CostReport(
            period_days=days,
            total_cost=response.get("total_cost", 0),
            total_reviews=response.get("total_reviews", 0),
            average_cost=response.get("average_cost", 0),
            breakdown=breakdown,
            efficiency_score=response.get("efficiency_score", 0),
            optimization_suggestions=response.get("optimization_suggestions", []),
            budget_status=response.get("budget_status", {}),
        )

    def calculate_roi(
        self,
        daily_volume: int,
        cost_per_review: float,
        **kwargs,
    ) -> ROIResult:
        """Calculate ROI for VerifAI implementation"""
        response = self._request(
            "POST",
            "roi",
            data={
                "daily_volume": daily_volume,
                "cost_per_review": cost_per_review,
                **kwargs,
            },
        )

        return ROIResult(
            annual_savings=response.get("annual_savings", 0),
            labor_savings=response.get("labor_savings", 0),
            error_savings=response.get("error_savings", 0),
            brand_savings=response.get("brand_savings", 0),
            compliance_savings=response.get("compliance_savings", 0),
            productivity_savings=response.get("productivity_savings", 0),
            verifai_cost=response.get("verifai_cost", 0),
            net_profit=response.get("net_profit", 0),
            roi_percentage=response.get("roi_percentage", 0),
            payback_days=response.get("payback_days", 0),
            five_year_savings=response.get("five_year_savings", 0),
            recommendations=response.get("recommendations", []),
        )

    def stream_review(self, content: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """Stream review results token by token"""
        with self._client.stream(
            "POST",
            "/review/stream",
            json={"content": content, **kwargs},
            timeout=self.timeout,
        ) as response:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)

    def close(self):
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
