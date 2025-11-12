"""Compatibility shim for platform.llm.providers.openrouter.circuit_breaker imports.

Re-exports circuit_breaker module from openrouter_service subdirectory.
"""

# Re-export everything from the actual circuit_breaker module
from platform.llm.providers.openrouter.openrouter_service import circuit_breaker as _mod
from platform.llm.providers.openrouter.openrouter_service.circuit_breaker import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
