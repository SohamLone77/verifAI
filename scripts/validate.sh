#!/usr/bin/env bash
# validate.sh — Run openenv validate locally
# Usage: bash scripts/validate.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=== VerifAI — OpenEnv Spec Validation ==="
echo ""

# Check that openenv.yaml exists
if [ ! -f "openenv.yaml" ]; then
  echo "ERROR: openenv.yaml not found in $PROJECT_ROOT"
  exit 1
fi

echo "Found openenv.yaml ✓"

# Try openenv CLI if installed
if command -v openenv &> /dev/null; then
  echo "Running: openenv validate openenv.yaml"
  openenv validate openenv.yaml
else
  echo "openenv CLI not found — running Python-based spec check instead."
  python -c "
import yaml, sys
from pathlib import Path

spec_path = Path('openenv.yaml')
with open(spec_path) as f:
    spec = yaml.safe_load(f)

required_keys = {'name', 'version', 'tasks', 'action_schema'}
missing = required_keys - set(spec.keys())
if missing:
    print(f'FAIL: Missing keys: {missing}')
    sys.exit(1)

task_names = {t['name'] for t in spec['tasks']}
required_tasks = {'classify', 'rewrite', 'iterative'}
missing_tasks = required_tasks - task_names
if missing_tasks:
    print(f'FAIL: Missing tasks: {missing_tasks}')
    sys.exit(1)

print(f'PASS: openenv.yaml is valid ✓')
print(f'  Tasks: {sorted(task_names)}')
print(f'  Version: {spec[\"version\"]}')
"
fi

echo ""
echo "=== Running pytest spec tests ==="
pytest tests/test_spec.py -v

echo ""
echo "Validation complete."
