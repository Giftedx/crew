"""Compatibility shim for platform.llm.providers.openrouter.workflow imports.

Re-exports workflow module from openrouter_service subdirectory.
"""

# Re-export everything from the actual workflow module
from platform.llm.providers.openrouter.openrouter_service import workflow as _mod
from platform.llm.providers.openrouter.openrouter_service.workflow import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
