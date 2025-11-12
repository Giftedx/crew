"""Compatibility shim for platform.llm.providers.openrouter.adaptive_routing imports.

Re-exports adaptive_routing module from openrouter_service subdirectory.
"""

# Re-export everything from the actual adaptive_routing module
from platform.llm.providers.openrouter.openrouter_service import adaptive_routing as _mod
from platform.llm.providers.openrouter.openrouter_service.adaptive_routing import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
