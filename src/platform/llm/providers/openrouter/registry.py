"""Compatibility shim for platform.llm.providers.openrouter.registry imports.

Re-exports registry module from openrouter_service subdirectory.
"""

# Re-export everything from the actual registry module
from platform.llm.providers.openrouter.openrouter_service import registry as _mod
from platform.llm.providers.openrouter.openrouter_service.registry import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
