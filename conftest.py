"""
conftest.py — Pytest configuration for VerifAI.

Adds the project root to sys.path so all packages can be imported
without installation when running `pytest tests/` from the project root.
"""

import sys
from pathlib import Path

# Insert project root at the start of sys.path
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
