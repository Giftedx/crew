"""Compatibility shim for platform.llm.providers.openrouter.connection_pool imports.

Re-exports connection_pool module from openrouter_service subdirectory.
"""

# Re-export everything from the actual connection_pool module
from platform.llm.providers.openrouter.openrouter_service import connection_pool as _mod
from platform.llm.providers.openrouter.openrouter_service.connection_pool import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
