# MULTI_AGENT
from __future__ import annotations

from app.agents.base_agent import BaseAgent


class FactualityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="FactualityAgent",
            rubric_focus=["factuality"],
            rubric_filename="factuality.yaml",
        )
