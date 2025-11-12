"""Compatibility shim for platform.llm.providers.openrouter.context imports.

Re-exports context module from openrouter_service subdirectory.
"""

# Re-export everything from the actual context module - wildcard import necessary for compat
# Get __all__ from the actual module
from platform.llm.providers.openrouter.openrouter_service import context as _ctx
from platform.llm.providers.openrouter.openrouter_service.context import *  # noqa: F403


__all__ = getattr(_ctx, "__all__", [])
