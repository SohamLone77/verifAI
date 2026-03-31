from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraderResult:
    """Result from any grader."""
    score: float                         # composite 0.0–1.0
    breakdown: dict[str, float] = field(default_factory=dict)  # per-dimension
    passed: bool = False
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.score = max(0.0, min(1.0, self.score))
        self.passed = self.score >= 0.7


# Grader registry — populated by each grader module
_GRADER_REGISTRY: dict[str, type] = {}


def register_grader(name: str):
    """Class decorator to register a grader."""
    def decorator(cls):
        _GRADER_REGISTRY[name] = cls
        return cls
    return decorator


def get_grader(name: str):
    if name not in _GRADER_REGISTRY:
        raise ValueError(f"Unknown grader: '{name}'. Available: {list(_GRADER_REGISTRY)}")
    return _GRADER_REGISTRY[name]()
