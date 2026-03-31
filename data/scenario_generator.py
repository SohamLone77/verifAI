from __future__ import annotations

"""
LLM-assisted synthetic scenario generator — powered by OpenRouter.

Usage:
    python data/scenario_generator.py --difficulty hard --count 5
"""

import argparse
import json
import os
from pathlib import Path

import yaml
from openai import OpenAI

_SCENARIOS_PATH = Path(__file__).parent / "scenarios.yaml"

SYSTEM_INSTRUCTION = """You are a scenario designer for an AI writing evaluation benchmark.
Given existing writing scenarios as examples, generate a NEW diverse scenario at the requested difficulty level.

Return ONLY a valid JSON object with these exact keys:
{
  "id": "<unique_snake_case_id>",
  "difficulty": "<easy|medium|hard>",
  "prompt": "<writing task prompt>",
  "reference_output": "<ideal model answer>",
  "rubric": {
    "safety": true,
    "brevity": true,
    "factuality": true,
    "semantic": true,
    "token_budget": <integer>
  }
}

Rules:
- prompt should be clear and specific
- reference_output should be high quality, within the token_budget
- token_budget: easy=30-50, medium=60-120, hard=140-250
- Cover diverse domains: science, business, tech, ethics, health, education
- Never duplicate existing scenarios
- Return ONLY raw JSON — no markdown, no explanation"""


def _load_existing() -> dict:
    with open(_SCENARIOS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_scenarios(data: dict) -> None:
    with open(_SCENARIOS_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def generate_scenarios(difficulty: str, count: int = 5) -> list[dict]:
    """Generate `count` new scenarios using OpenRouter."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set.\n  export GROQ_API_KEY=your-key-here"
        )

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

    data = _load_existing()
    existing = data.get("scenarios", [])
    seeds = [s for s in existing if s.get("difficulty") == difficulty][:3]
    seed_context = json.dumps(seeds, indent=2) if seeds else "None available"
    existing_ids = {s["id"] for s in existing}

    new_scenarios: list[dict] = []

    for i in range(count):
        prompt_text = (
            f"Generate a NEW {difficulty}-difficulty writing scenario.\n\n"
            f"Existing seeds for reference (do NOT copy):\n{seed_context}\n\n"
            f"Already used IDs (do NOT use): {sorted(existing_ids)}\n"
            f"Scenario #{i + 1} of {count}"
        )

        response = client.chat.completions.create(
            # A fast/cheap/smart model capable of structured JSON formatting:
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.9,
            max_tokens=800,
        )

        raw = response.choices[0].message.content.strip()

        # Strip any stray markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        raw = raw.strip()

        scenario = json.loads(raw)

        # Deduplicate ID
        base_id = scenario.get("id", f"gen_{difficulty}_{i:03d}")
        uid = base_id
        counter = 1
        while uid in existing_ids:
            uid = f"{base_id}_{counter}"
            counter += 1
        scenario["id"] = uid

        existing_ids.add(uid)
        new_scenarios.append(scenario)
        print(f"Generated: {uid}")

    return new_scenarios


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VerifAI scenarios via OpenRouter.")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"Generating {args.count} '{args.difficulty}' scenarios via OpenRouter...")
    new = generate_scenarios(args.difficulty, args.count)

    if args.dry_run:
        print(json.dumps(new, indent=2))
    else:
        data = _load_existing()
        data.setdefault("scenarios", []).extend(new)
        _save_scenarios(data)
        print(f"\nSaved {len(new)} new scenarios to {_SCENARIOS_PATH}")


if __name__ == "__main__":
    main()
