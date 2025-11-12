"""Compatibility shim for platform.llm.providers.openrouter.service imports.

Re-exports service module from openrouter_service subdirectory.
"""

# Re-export everything from the actual service module
from platform.llm.providers.openrouter.openrouter_service import service as _mod
from platform.llm.providers.openrouter.openrouter_service.service import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
