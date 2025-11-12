"""Compatibility shim for platform.llm.providers.openrouter.cache_layer imports.

Re-exports cache_layer module from openrouter_service subdirectory.
"""

# Re-export everything from the actual cache_layer module
from platform.llm.providers.openrouter.openrouter_service import cache_layer as _mod
from platform.llm.providers.openrouter.openrouter_service.cache_layer import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
