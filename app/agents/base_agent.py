# MULTI_AGENT
from __future__ import annotations

import asyncio

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from openai import OpenAI

from app.models import Action, ActionType, Observation


@dataclass
class AgentFeedback:
    name: str
    rubric_focus: list[str]
    feedback: str


class BaseAgent:
    def __init__(
        self,
        name: str,
        rubric_focus: list[str],
        rubric_filename: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.name = name
        self.rubric_focus = rubric_focus
        self.model = model
        self.system_prompt = self._load_system_prompt(rubric_filename)

    async def run(self, observation: Observation) -> Action:
        messages = self._build_messages(observation)
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

    def _build_messages(self, observation: Observation) -> list[dict[str, Any]]:
        user_message = (
            "Review the current text only for the rubric focus below.\n\n"
            f"RUBRIC FOCUS: {', '.join(self.rubric_focus)}\n\n"
            f"PROMPT:\n{observation.prompt}\n\n"
            f"CURRENT TEXT:\n{observation.current_output}\n\n"
            "Provide concise feedback with issues and suggested fixes."
        )
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

    def _load_system_prompt(self, rubric_filename: str) -> str:
        rubrics_dir = Path(__file__).resolve().parents[2] / "rubrics"
        rubric_path = rubrics_dir / rubric_filename
        rubric_data = {}
        if rubric_path.exists():
            with open(rubric_path, encoding="utf-8") as handle:
                rubric_data = yaml.safe_load(handle) or {}

        rubric_text = yaml.safe_dump(rubric_data, sort_keys=False).strip()
        if not rubric_text:
            rubric_text = "(No rubric data found.)"

        return (
            f"You are {self.name}, a specialist reviewer.\n"
            f"Focus areas: {', '.join(self.rubric_focus)}.\n\n"
            "Rubric reference:\n"
            f"{rubric_text}\n\n"
            "Respond with clear, actionable feedback only."
        )

    def _generate(self, messages: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=400,
        )
        content = response.choices[0].message.content.strip()

        usage = None
        if getattr(response, "usage", None):
            usage = {
                "model": self.model,
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(response.usage, "completion_tokens", 0)
                or 0,
            }

        return content, usage

    def _get_client(self) -> OpenAI:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set for multi-agent panel.")
        return OpenAI(api_key=api_key)
