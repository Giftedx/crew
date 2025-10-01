"""Environment flags and defaults for the scoped Discord bot.

Keeps imports optional-dependency safe and provides sensible default flags
for local runs.
"""

from __future__ import annotations

import os

# Mirror LIGHTWEIGHT_IMPORT semantics used elsewhere for import safety
LIGHTWEIGHT_IMPORT = os.getenv("LIGHTWEIGHT_IMPORT", "0") in {"1", "true", "yes", "on"}

# Default feature flags to enable a coherent minimal experience
DEFAULT_FEATURE_FLAGS = {
    "ENABLE_HTTP_RETRY": "1",
    "ENABLE_HTTP_CACHE": "1",
    "ENABLE_METRICS": "1",
    "ENABLE_TRACING": "1",
    "ENABLE_SEMANTIC_CACHE": "1",
}

__all__ = ["LIGHTWEIGHT_IMPORT", "DEFAULT_FEATURE_FLAGS"]
