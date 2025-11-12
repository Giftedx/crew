"""Compatibility shim for platform.llm.providers.openrouter.execution imports.

Re-exports execution module from openrouter_service subdirectory.
"""

# Re-export everything from the actual execution module
from platform.llm.providers.openrouter.openrouter_service import execution as _mod
from platform.llm.providers.openrouter.openrouter_service.execution import *  # noqa: F403

# Explicitly import private functions needed by tests
from platform.llm.providers.openrouter.openrouter_service.execution import _compute_reward


__all__ = getattr(_mod, "__all__", []) + ["_compute_reward"]
