"""Compatibility shim for platform.llm.providers.openrouter.async_execution imports.

Re-exports async_execution module from openrouter_service subdirectory.
"""

# Re-export everything from the actual async_execution module
from platform.llm.providers.openrouter.openrouter_service import async_execution as _mod
from platform.llm.providers.openrouter.openrouter_service.async_execution import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
