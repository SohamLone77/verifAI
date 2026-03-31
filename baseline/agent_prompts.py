# COT_REWARD
from __future__ import annotations

"""
System and user prompt templates for the VerifAI baseline agent.
Each task has its own system prompt and a shared user message builder.
"""

from app.models import Observation

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

_CLASSIFY_SYSTEM = """You are an expert writing quality evaluator.

You will be shown a writing PROMPT, an AI-generated RESPONSE, and optionally an attached IMAGE.
If an image is attached, base your evaluation on how well the response describes or relates to the visual content.
Your task is to evaluate the quality of the response on a scale of 0 to 10, where:
  0 = completely inappropriate, harmful, or irrelevant
  5 = acceptable but with notable issues
  10 = excellent — accurate, clear, safe, and well-written

Respond with a JSON object:
{"score": <integer 0-10>, "justification": "<one to two sentence explanation>"}

Be concise and specific in your justification. Do not pad or repeat yourself."""


_REWRITE_SYSTEM = """You are an expert writing editor.

You will receive:
1. A writing PROMPT (and potentially an attached IMAGE)
2. An existing AI-generated RESPONSE that may not fully satisfy the rubric
3. A RUBRIC describing quality criteria

Your task is to REWRITE the response to fully satisfy all rubric criteria:
- Safety: no harmful, offensive, or misleading content
- Brevity: concise and within the token budget
- Factuality: only verifiable, defensible claims
- Quality: clear, professional, and accurate

Produce ONLY the rewritten text. Do not add commentary, preamble, or meta-explanation.
If you believe the current text is already good, you may submit it unchanged."""


_REWRITE_SYSTEM_COT = """You are an expert writing editor who reasons step-by-step before acting.

You will receive:
1. A writing PROMPT (and potentially an attached IMAGE)
2. An existing AI-generated RESPONSE that may not fully satisfy the rubric
3. A RUBRIC describing quality criteria

Before you rewrite, think through the issues and the fixes in order:
1) Identify the rubric issues in the current text
2) Explain why your fixes will address those issues
3) Produce the revised response

Keep your reasoning concise and structured. Then output the rewritten text.
If you believe the current text is already good, you may submit it unchanged."""


_ITERATIVE_SYSTEM = """You are a world-class writing coach operating under strict constraints.

You will receive:
1. A writing PROMPT (and potentially an attached IMAGE)
2. The CURRENT TEXT to improve
3. A RUBRIC and TOKEN BUDGET (word count limit)
4. GRADER FEEDBACK from the previous step (after the first step)

Your goal is to maximise the composite quality score across multiple revision rounds.
Strategy:
- On step 1: do a thorough first revision addressing all rubric dimensions
- On subsequent steps: focus on the dimensions with the lowest scores
- NEVER exceed the token budget
- NEVER produce unsafe content
- Submit early if you are confident the text is near-perfect

Produce ONLY the revised text. No preamble, no meta-commentary."""


_ITERATIVE_SYSTEM_COT = """You are a world-class writing coach who reasons step-by-step before acting.

You will receive:
1. A writing PROMPT (and potentially an attached IMAGE)
2. The CURRENT TEXT to improve
3. A RUBRIC and TOKEN BUDGET (word count limit)
4. GRADER FEEDBACK from the previous step (after the first step)

Before you rewrite, think through the issues and the fixes in order:
1) Identify the rubric issues in the current text
2) Explain why your fixes will address those issues
3) Produce the revised response

Keep your reasoning concise and structured. Then output the revised text.
Submit early if you are confident the text is near-perfect."""


_SYSTEM_PROMPTS: dict[str, str] = {
    "classify": _CLASSIFY_SYSTEM,
    "rewrite": _REWRITE_SYSTEM,
    "iterative": _ITERATIVE_SYSTEM,
}

_SYSTEM_PROMPTS_COT: dict[str, str] = {
    "classify": _CLASSIFY_SYSTEM,
    "rewrite": _REWRITE_SYSTEM_COT,
    "iterative": _ITERATIVE_SYSTEM_COT,
}


def get_system_prompt(task_name: str, use_cot: bool = False) -> str:
    """Return the system prompt for the given task name."""
    prompt_map = _SYSTEM_PROMPTS_COT if use_cot else _SYSTEM_PROMPTS
    if task_name not in prompt_map:
        raise ValueError(f"Unknown task: '{task_name}'")
    return prompt_map[task_name]


# ---------------------------------------------------------------------------
# User Message Builder
# ---------------------------------------------------------------------------

def build_user_message(obs: Observation) -> str:
    """Build the per-step user message from the current observation."""
    rubric_lines = []
    if obs.rubric.safety:
        rubric_lines.append("- Safety: avoid harmful, offensive, or misleading content")
    if obs.rubric.brevity:
        budget = obs.rubric.token_budget or 300
        rubric_lines.append(f"- Brevity: stay within {budget} words")
    if obs.rubric.factuality:
        rubric_lines.append("- Factuality: use only verifiable, defensible claims")
    if obs.rubric.semantic:
        rubric_lines.append("- Quality: clear, professional, and accurate writing")
    if obs.rubric.custom_notes:
        rubric_lines.append(f"- Additional: {obs.rubric.custom_notes}")

    rubric_str = "\n".join(rubric_lines) if rubric_lines else "No specific rubric constraints."

    return f"""--- TASK CONTEXT (Step {obs.step + 1}) ---

PROMPT:
{obs.prompt}

CURRENT TEXT TO EVALUATE/IMPROVE:
{obs.current_output or "(no existing output yet — produce the best response you can)"}

RUBRIC:
{rubric_str}

--- YOUR RESPONSE BELOW ---"""
