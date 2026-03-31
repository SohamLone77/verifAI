# MULTI_AGENT
from __future__ import annotations

import asyncio

from typing import Any

from app.agents.base_agent import AgentFeedback, BaseAgent
from app.models import Action, ActionType, Observation


class RewriterAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            name="RewriterAgent",
            rubric_focus=["safety", "factuality", "brevity", "quality"],
            rubric_filename="brand_voice.yaml",
        )

    async def run_with_feedback(
        self,
        observation: Observation,
        feedback: list[AgentFeedback],
    ) -> Action:
        messages = self._build_messages_with_feedback(observation, feedback)
        text, usage = await asyncio.to_thread(self._generate, messages)
        metadata: dict[str, Any] = {
            "agent": self.name,
            "rubric_focus": self.rubric_focus,
        }
        if usage:
            metadata["usage"] = usage

        return Action(
            action_type=ActionType.rewrite,
            content=text,
            modality="text",
            metadata=metadata,
        )

    def _build_messages_with_feedback(
        self,
        observation: Observation,
        feedback: list[AgentFeedback],
    ) -> list[dict[str, Any]]:
        feedback_lines = []
        for item in feedback:
            focus = ", ".join(item.rubric_focus)
            feedback_lines.append(f"- {item.name} ({focus}): {item.feedback}")

        feedback_block = "\n".join(feedback_lines) if feedback_lines else "(no feedback)"
        user_message = (
            "Rewrite the text using the feedback below.\n\n"
            f"PROMPT:\n{observation.prompt}\n\n"
            f"CURRENT TEXT:\n{observation.current_output}\n\n"
            f"FEEDBACK:\n{feedback_block}\n\n"
            "Return only the rewritten response."
        )

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
