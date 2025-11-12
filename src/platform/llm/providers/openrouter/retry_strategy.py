"""Compatibility shim for platform.llm.providers.openrouter.retry_strategy imports.

Re-exports retry_strategy module from openrouter_service subdirectory.
"""

# Re-export everything from the actual retry_strategy module
from platform.llm.providers.openrouter.openrouter_service import retry_strategy as _mod
from platform.llm.providers.openrouter.openrouter_service.retry_strategy import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
