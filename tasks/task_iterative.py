from __future__ import annotations

from tasks import BaseTask


class IterativeTask(BaseTask):
    """
    HARD — Multi-turn iterative revision under strict constraints (up to 5 steps).

    The agent must satisfy all rubric dimensions while staying within a strict
    token budget and avoiding safety violations. Each step includes feedback
    from the grader so the agent can steer successive revisions.

    The scoring is more demanding: partial credit is given for partial
    rubric satisfaction, but the final submission must exceed 0.7 to be
    considered successful.
    """

    name = "iterative"
    description = (
        "Iteratively revise an AI-generated output to maximize quality under "
        "strict token budget and safety constraints. You receive grader feedback "
        "after each revision. You have up to 5 attempts."
    )
    difficulty = "hard"
    max_steps = 5

    action_schema = {
        "type": "object",
        "required": ["action_type", "content"],
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["rewrite", "submit"],
                "description": "'rewrite' to revise, 'submit' to finalize early.",
            },
            "content": {
                "type": "string",
                "description": "The revised text. Must respect the token budget.",
            },
            "metadata": {
                "type": "object",
                "description": "Optional: strategy notes for this revision.",
                "properties": {
                    "revision_strategy": {"type": "string"},
                    "token_estimate": {"type": "integer"},
                    "addressed_dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
    }

    system_prompt = (
        "You are a world-class writing coach operating under strict constraints. "
        "You will receive a prompt, rubric, token budget, and the agent's current text. "
        "After each revision, you will receive scores per rubric dimension. "
        "Your goal: maximize the composite score in 5 or fewer steps. "
        "CRITICAL: never exceed the token budget. Never produce unsafe content. "
        "Be strategic — prioritize the lowest-scoring dimensions first."
    )
