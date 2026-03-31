"""Utility functions for VerifAI SDK"""

import re
import time
from typing import Dict, Any, Optional
from functools import wraps


def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key or len(api_key) < 10:
        raise ValueError("Invalid API key format")

    if not re.match(r"^[a-zA-Z0-9_\-]+$", api_key):
        raise ValueError("API key contains invalid characters")

    return True


def validate_content(content: str, max_length: int = 10000) -> bool:
    """Validate content for review"""
    if not content or not content.strip():
        raise ValueError("Content cannot be empty")

    if len(content) > max_length:
        raise ValueError(f"Content too long. Max {max_length} characters")

    return True


def format_duration(ms: float) -> str:
    """Format milliseconds to human-readable string"""
    if ms < 1000:
        return f"{ms:.0f}ms"
    if ms < 60000:
        return f"{ms / 1000:.1f}s"
    return f"{ms / 60000:.1f}m"


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4",
) -> float:
    """Calculate API cost based on tokens"""
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
    }

    prices = pricing.get(model, pricing["gpt-4"])

    cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1000
    return round(cost, 6)


def estimate_tokens(text: str) -> int:
    """Roughly estimate token count (4 chars ~= 1 token)"""
    return len(text) // 4


def truncate_text(text: str, max_tokens: int = 4000) -> str:
    """Truncate text to approximate token limit"""
    max_chars = max_tokens * 4
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for retry with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        sleep_time = backoff_factor * (2 ** attempt)
                        time.sleep(sleep_time)
            raise last_exception

        return wrapper

    return decorator


class Timer:
    """Context manager for timing operations"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        self.end_time = time.time()

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        return self.elapsed_ms / 1000
