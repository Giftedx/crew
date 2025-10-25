"""Test-friendly site customizations for this repository.

This module is automatically imported by Python's site module if present
on sys.path. We use it to:
- Ensure the src/ directory is importable without setting PYTHONPATH
- Prevent third-party pytest plugin auto-loading that often breaks
  hermetic test runs (e.g., chromadb/lancedb exporting pytest plugins)

Both behaviors are safe for local development and CI, and can be overridden
via environment variables.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# 1) Make sure src/ is importable (so `import ultimate_discord_intelligence_bot` works)
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if SRC.exists():
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

# 2) Disable auto-loading of external pytest plugins by default.
# This avoids ImportPathMismatch and binary-dep import errors during collection.
# You can re-enable plugin autoload by setting PYTEST_DISABLE_PLUGIN_AUTOLOAD=0.
if os.getenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD") is None:
    # Only set the guard if not explicitly configured by the environment
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
