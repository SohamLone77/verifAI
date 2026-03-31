"""Retry helpers for VerifAI SDK"""

from typing import Iterable, Tuple, Type

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


def with_retry(
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 1.0,
):
    """Return a tenacity retry decorator with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
    )
