"""Compatibility shim for platform.llm.providers.openrouter.route_components imports.

Re-exports route_components module from openrouter_service subdirectory.
"""

# Re-export everything from the actual route_components module
from platform.llm.providers.openrouter.openrouter_service import route_components as _mod
from platform.llm.providers.openrouter.openrouter_service.route_components import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
