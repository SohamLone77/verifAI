# MULTI_AGENT
from __future__ import annotations

from app.agents.base_agent import BaseAgent


class SafetyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="SafetyAgent",
            rubric_focus=["safety"],
            rubric_filename="safety.yaml",
        )
