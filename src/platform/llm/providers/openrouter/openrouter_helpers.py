"""Compatibility shim for platform.llm.providers.openrouter.openrouter_helpers imports.

Re-exports openrouter_helpers module from openrouter_service subdirectory.
"""

# Re-export everything from the actual openrouter_helpers module
from platform.llm.providers.openrouter.openrouter_service import openrouter_helpers as _mod
from platform.llm.providers.openrouter.openrouter_service.openrouter_helpers import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
