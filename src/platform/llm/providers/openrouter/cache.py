"""Compatibility shim for platform.llm.providers.openrouter.cache imports.

Re-exports cache module from openrouter_service subdirectory.
"""

# Re-export everything from the actual cache module
from platform.llm.providers.openrouter.openrouter_service import cache as _mod
from platform.llm.providers.openrouter.openrouter_service.cache import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
