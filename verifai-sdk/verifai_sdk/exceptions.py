"""Custom exceptions for VerifAI SDK"""

from typing import Any


class VerifAIError(Exception):
    """Base exception for all VerifAI SDK errors"""
    pass


class AuthenticationError(VerifAIError):
    """Raised when authentication fails"""
    pass


class RateLimitError(VerifAIError):
    """Raised when rate limit is exceeded"""
    pass


class ValidationError(VerifAIError):
    """Raised when input validation fails"""
    pass


class APIError(VerifAIError):
    """Raised when API returns an error"""

    def __init__(self, message: str, status_code: int, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TimeoutError(VerifAIError):
    """Raised when request times out"""
    pass


class ConfigurationError(VerifAIError):
    """Raised when configuration is invalid"""
    pass
