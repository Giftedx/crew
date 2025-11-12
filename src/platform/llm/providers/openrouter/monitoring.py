"""Compatibility shim for platform.llm.providers.openrouter.monitoring imports.

Re-exports monitoring module from openrouter_service subdirectory.
"""

# Re-export everything from the actual monitoring module
from platform.llm.providers.openrouter.openrouter_service import monitoring as _mod
from platform.llm.providers.openrouter.openrouter_service.monitoring import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
