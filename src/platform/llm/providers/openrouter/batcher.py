"""Compatibility shim for platform.llm.providers.openrouter.batcher imports.

Re-exports batcher module from openrouter_service subdirectory.
"""

# Re-export everything from the actual batcher module
from platform.llm.providers.openrouter.openrouter_service import batcher as _mod
from platform.llm.providers.openrouter.openrouter_service.batcher import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
