# COST_TRACKING
from __future__ import annotations

"""
Baseline inference script — powered by OpenRouter (OpenAI-compatible SDK).

Usage:
    python baseline/run_baseline.py --task classify --api-key YOUR_KEY
    python baseline/run_baseline.py --task rewrite --model meta-llama/llama-3.3-70b-instruct:free
"""

import argparse
from dataclasses import asdict
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from openai import RateLimitError

from app.environment import PromptReviewEnv
from app.models import Action, ActionType, TaskName
from app.multimodal_processor import _detect_mime
from baseline.agent_prompts import build_user_message, get_system_prompt
from reward.cost_tracker import CostTracker


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def _get_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Build an OpenRouter client. Priority:
    1. --api-key CLI argument
    2. OPENROUTER_API_KEY environment variable
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise EnvironmentError(
            "OpenRouter API key not found.\n"
            "Pass it with --api-key YOUR_KEY  OR  set the env var:\n"
            "  Windows PowerShell:  $env:OPENROUTER_API_KEY = 'your-key'\n"
            "  Linux/Mac:           export OPENROUTER_API_KEY=your-key"
        )
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        default_headers={"HTTP-Referer": "https://verifai.local", "X-Title": "VerifAI"},
    )


# ---------------------------------------------------------------------------
# Helper: call OpenRouter with retry on 429 rate-limit
# ---------------------------------------------------------------------------

def _generate_with_retry(
    client: OpenAI,
    model: str,
    messages: list[dict],
    max_retries: int = 3,
    tracker: Optional[CostTracker] = None,
) -> str:
    """Call completion with linear back-off on rate limits."""
    delay = 5  # Start with 5 seconds for rate limits
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            if tracker and getattr(response, "usage", None):
                usage = response.usage
                prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens = getattr(usage, "completion_tokens", None)
                if completion_tokens is None:
                    total_tokens = getattr(usage, "total_tokens", 0) or 0
                    completion_tokens = max(0, total_tokens - prompt_tokens)
                tracker.track(
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )
            return response.choices[0].message.content.strip()
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait = delay * (attempt + 1)
                print(f"  [rate limit] Quota exhausted or strict limit. Waiting {wait}s before retry {attempt + 2}/{max_retries}...")
                time.sleep(wait)
                continue
            else:
                raise RuntimeError(
                    f"OpenRouter rate limit persists after {max_retries} retries.\n"
                    f"Original error: {e}"
                ) from e
        except Exception as e:
            if "model_decommissioned" in str(e) or "does not exist" in str(e):
                raise RuntimeError(
                    f"The requested model '{model}' is currently unavailable.\n"
                    f"Original error: {e}"
                ) from e
            raise  # immediately raise other errors


# ---------------------------------------------------------------------------
# Main episode runner
# ---------------------------------------------------------------------------

def run_baseline_episode(
    task_name: str,
    scenario_id: Optional[str] = None,
    model: str = "meta-llama/llama-3.3-70b-instruct:free",
    api_key: Optional[str] = None,
) -> dict:
    """
    Run one full baseline episode using OpenRouter and return results dict:
    - task, model, total_steps, final_score, success, step_log
    """
    client = _get_client(api_key)
    env = PromptReviewEnv()
    cost_tracker = CostTracker()

    task = TaskName(task_name)
    obs, state = env.reset(task_name=task, scenario_id=scenario_id)

    system_prompt = get_system_prompt(task_name)

    # Initialize chat history (system prompt will be prepended to first user message)
    messages: list[dict] = []
    
    step_log = []
    step_response = None

    while not state.done:
        user_message_text = build_user_message(obs)
        if state.step == 0:
            user_message_text = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n{user_message_text}"
        
        # Build multimodal prompt if image exists in observation
        user_content: list[dict[str, Any]] = [{"type": "text", "text": user_message_text}]
        is_multimodal = False
        if obs.image_url:
            user_content.append({"type": "image_url", "image_url": {"url": obs.image_url}})
            is_multimodal = True
        elif obs.image_b64:
            mime = _detect_mime(obs.image_b64)
            user_content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{obs.image_b64}"}})
            is_multimodal = True

        messages.append({"role": "user", "content": user_content})

        # Auto-switch to vision model if image is present
        active_model = model
        if is_multimodal and "vision" not in active_model.lower() and "llava" not in active_model.lower() and "gemma-3" not in active_model.lower():
            active_model = "google/gemma-3-4b-it:free"

        agent_text = _generate_with_retry(
            client,
            active_model,
            messages,
            tracker=cost_tracker,
        )

        # Append assistant reply to history
        messages.append({"role": "assistant", "content": agent_text})

        action_type = _decide_action_type(task_name, state.step, state.max_steps)
        
        # Multimodal structured output step 2 logic
        parsed_json = None
        if task_name == "classify":
            try:
                # Strip markdown code blocks just in case
                clean_text = agent_text
                if "```json" in clean_text:
                    clean_text = clean_text.split("```json")[-1].split("```")[0].strip()
                elif "```" in clean_text:
                    clean_text = clean_text.split("```")[-1].split("```")[0].strip()
                
                parsed_json = json.loads(clean_text)
            except json.JSONDecodeError:
                pass # fallback to plain text if parsing fails
        
        if parsed_json:
            action = Action(
                action_type=action_type, 
                content="", 
                modality="structured", 
                structured_data=parsed_json
            )
        else:
            action = Action(
                action_type=action_type, 
                content=agent_text, 
                modality="text"
            )

        step_response = env.step(state=state, obs=obs, action=action)
        obs = step_response.observation

        step_log.append({
            "step": state.step,
            "action_type": action_type.value,
            "content_preview": agent_text[:120],
            "score": step_response.info.get("score"),
            "reward": step_response.reward.value,
        })

        if step_response.done:
            break

    final_score = step_response.info.get("score") if step_response else None
    episode_info = env.get_episode_info(state, final_score)
    cost_report = cost_tracker.get_episode_cost()

    return {
        "task": task_name,
        "model": model,
        "total_steps": episode_info.total_steps,
        "total_reward": episode_info.total_reward,
        "final_score": episode_info.final_score,
        "success": episode_info.success,
        "cost_report": asdict(cost_report),
        "step_log": step_log,
    }


def _decide_action_type(task_name: str, step: int, max_steps: int) -> ActionType:
    if step >= max_steps - 1:
        return ActionType.submit
    if task_name == "classify":
        return ActionType.classify
    return ActionType.rewrite


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run VerifAI baseline agent (OpenRouter).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python baseline/run_baseline.py --task classify --api-key YOUR_KEY\n"
            "  python baseline/run_baseline.py --task rewrite --model meta-llama/llama-3.3-70b-instruct:free\n"
            "  python baseline/run_baseline.py --task iterative --model mixtral-8x7b-32768\n"
        ),
    )
    parser.add_argument("--task", choices=["classify", "rewrite", "iterative"], required=True)
    parser.add_argument(
        "--model",
        default="meta-llama/llama-3.3-70b-instruct:free",
        help="OpenRouter model tag (default: meta-llama/llama-3.3-70b-instruct:free)",
    )
    parser.add_argument("--api-key", default=None, help="OpenRouter API key (overrides env var)")
    parser.add_argument("--scenario-id", default=None)
    parser.add_argument("--output", default=None, help="Save JSON results to this file")
    args = parser.parse_args()

    print(f"\nRunning OpenRouter baseline:")
    print(f"  task  = {args.task}")
    print(f"  model = {args.model}")

    try:
        result = run_baseline_episode(
            task_name=args.task,
            scenario_id=args.scenario_id,
            model=args.model,
            api_key=args.api_key,
        )
    except RuntimeError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except EnvironmentError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    print(f"\nResults:")
    fs = result["final_score"]
    print(f"  Final score:   {fs:.4f}" if fs is not None else "  Final score: N/A")
    print(f"  Total steps:   {result['total_steps']}")
    print(f"  Total reward:  {result['total_reward']:.4f}")
    print(f"  Success:       {result['success']}")
    print()
    for s in result["step_log"]:
        sc = f"{s['score']:.4f}" if s["score"] is not None else "N/A"
        print(f"  Step {s['step']}: score={sc}  reward={s['reward']:.4f}  [{s['action_type']}]")
        print(f"    {s['content_preview'][:80]}...")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nSaved results to {args.output}")


if __name__ == "__main__":
    main()
