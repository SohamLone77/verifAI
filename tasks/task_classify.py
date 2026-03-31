from __future__ import annotations

from tasks import BaseTask


class ClassifyTask(BaseTask):
    """
    EASY — Single-turn task.

    The agent is shown an AI-generated text and must classify its overall
    quality on a scale of 0 to 10. The rubric grader checks the numeric
    value and the reasoning provided.
    """

    name = "classify"
    description = (
        "Given an AI-generated output and its source prompt, output a numeric "
        "quality score from 0 (very poor) to 10 (excellent), with a brief justification."
    )
    difficulty = "easy"
    max_steps = 1

    action_schema = {
        "type": "object",
        "required": ["action_type", "content"],
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["classify"],
                "description": "Must be 'classify' for this task.",
            },
            "content": {
                "type": "string",
                "description": (
                    "A JSON-encoded object with keys 'score' (int 0-10) "
                    "and 'justification' (string)."
                ),
            },
        },
    }

    system_prompt = (
        "You are an expert writing evaluator. "
        "Given a prompt and an AI-generated response, assess the response quality "
        "on a scale of 0 (poor) to 10 (excellent). "
        "Reply with a JSON object: {\"score\": <int>, \"justification\": <str>}."
    )
