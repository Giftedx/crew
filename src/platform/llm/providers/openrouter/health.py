"""Compatibility shim for platform.llm.providers.openrouter.health imports.

Re-exports health module from openrouter_service subdirectory.
"""

# Re-export everything from the actual health module
from platform.llm.providers.openrouter.openrouter_service import health as _mod
from platform.llm.providers.openrouter.openrouter_service.health import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
