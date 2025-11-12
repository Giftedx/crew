"""Compatibility shim for platform.llm.providers.openrouter.cache_warmer imports.

Re-exports cache_warmer module from openrouter_service subdirectory.
"""

# Re-export everything from the actual cache_warmer module
from platform.llm.providers.openrouter.openrouter_service import cache_warmer as _mod
from platform.llm.providers.openrouter.openrouter_service.cache_warmer import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
