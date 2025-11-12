"""Compatibility shim for platform.llm.providers.openrouter.object_pool imports.

Re-exports object_pool module from openrouter_service subdirectory.
"""

# Re-export everything from the actual object_pool module
from platform.llm.providers.openrouter.openrouter_service import object_pool as _mod
from platform.llm.providers.openrouter.openrouter_service.object_pool import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
