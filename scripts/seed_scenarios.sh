#!/usr/bin/env bash
# seed_scenarios.sh — Regenerate the scenario bank using the LLM generator
# Usage: bash scripts/seed_scenarios.sh [--difficulty easy|medium|hard] [--count N]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

DIFFICULTY="${1:-medium}"
COUNT="${2:-5}"

echo "=== VerifAI — Scenario Seeder ==="
echo "Difficulty : $DIFFICULTY"
echo "Count      : $COUNT"
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY is not set."
  exit 1
fi

python data/scenario_generator.py --difficulty "$DIFFICULTY" --count "$COUNT"

echo ""
echo "Seeding complete. Updated: data/scenarios.yaml"
