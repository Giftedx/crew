"""Compatibility shim for platform.llm.providers.openrouter.refactored_service imports.

Re-exports refactored_service module from openrouter_service subdirectory.
"""

# Re-export everything from the actual refactored_service module
from platform.llm.providers.openrouter.openrouter_service import refactored_service as _mod
from platform.llm.providers.openrouter.openrouter_service.refactored_service import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
