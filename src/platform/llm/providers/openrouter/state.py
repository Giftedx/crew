"""Compatibility shim for platform.llm.providers.openrouter.state imports.

Re-exports state module from openrouter_service subdirectory.
"""

# Re-export everything from the actual state module
from platform.llm.providers.openrouter.openrouter_service import state as _mod
from platform.llm.providers.openrouter.openrouter_service.state import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
