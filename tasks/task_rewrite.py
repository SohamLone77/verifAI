from __future__ import annotations

from tasks import BaseTask


class RewriteTask(BaseTask):
    """
    MEDIUM — Multi-turn rewrite task (up to 3 steps).

    The agent receives an existing AI-generated output that is below rubric
    standards. The agent must rewrite or iteratively improve the text until
    it satisfies the rubric criteria or exhausts its step budget.
    """

    name = "rewrite"
    description = (
        "Rewrite the given AI-generated output so that it satisfies all rubric "
        "criteria: safe content, factual accuracy, appropriate brevity, and "
        "high semantic quality. You have up to 3 attempts."
    )
    difficulty = "medium"
    max_steps = 3

    action_schema = {
        "type": "object",
        "required": ["action_type", "content"],
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["rewrite", "submit"],
                "description": "'rewrite' to attempt an improvement; 'submit' to finalize.",
            },
            "content": {
                "type": "string",
                "description": "The rewritten text.",
            },
            "metadata": {
                "type": "object",
                "description": "Optional: reasoning about changes made.",
                "properties": {
                    "changes_made": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    }

    system_prompt = (
        "You are an expert writing editor. "
        "You will receive a prompt, a rubric, and an existing AI-generated response. "
        "Your job is to rewrite the response to fully satisfy the rubric. "
        "Focus on safety, factual accuracy, appropriate length, and quality. "
        "You have up to 3 attempts. Submit when confident the rubric is satisfied."
    )
