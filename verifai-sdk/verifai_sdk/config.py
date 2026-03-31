"""Configuration management for VerifAI SDK"""

from __future__ import annotations

import os

from verifai_sdk.models import ClientConfig


VerifAIClientConfig = ClientConfig


def load_config_from_env() -> ClientConfig:
    """Build ClientConfig from environment variables."""
    defaults = ClientConfig()
    return ClientConfig(
        api_key=os.environ.get("VERIFAI_API_KEY", defaults.api_key),
        base_url=os.environ.get("VERIFAI_BASE_URL", defaults.base_url),
        timeout=float(os.environ.get("VERIFAI_TIMEOUT", defaults.timeout)),
        max_retries=int(os.environ.get("VERIFAI_MAX_RETRIES", defaults.max_retries)),
        retry_backoff_factor=float(
            os.environ.get("VERIFAI_RETRY_BACKOFF", defaults.retry_backoff_factor)
        ),
        cache_enabled=os.environ.get("VERIFAI_CACHE_ENABLED", "true").lower() in ("1", "true", "yes"),
        cache_ttl=int(os.environ.get("VERIFAI_CACHE_TTL", defaults.cache_ttl)),
        log_level=os.environ.get("VERIFAI_LOG_LEVEL", defaults.log_level),
    )
