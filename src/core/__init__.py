"""Core package.

Keep this module lightweight to avoid importing heavy dependencies during
``import core.http_utils`` or similar submodule imports in tests. Submodules
should be imported explicitly where needed, e.g., ``from core import router``
or ``from core import prompt_engine``.

This file intentionally does not eagerly import subpackages to prevent
unnecessary side effects and optional dependency requirements during import.
"""

# Public submodules may still be imported explicitly by consumers:
__all__ = [
    "alerts",
    "cache",
    "eval_harness",
    "flags",
    "learn",
    "learning_engine",
    "log_schema",
    "privacy",
    "prompt_engine",
    "reliability",
    "reward_pipe",
    "rl",
    "router",
    "token_meter",
    "tool_planner",
]
