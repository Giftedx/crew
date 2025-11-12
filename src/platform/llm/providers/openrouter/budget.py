"""Compatibility shim for platform.llm.providers.openrouter.budget imports.

Re-exports budget module from openrouter_service subdirectory.
"""

# Re-export everything from the actual budget module
from platform.llm.providers.openrouter.openrouter_service import budget as _mod
from platform.llm.providers.openrouter.openrouter_service.budget import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
