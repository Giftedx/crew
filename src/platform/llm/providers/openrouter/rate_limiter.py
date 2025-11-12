"""Compatibility shim for platform.llm.providers.openrouter.rate_limiter imports.

Re-exports rate_limiter module from openrouter_service subdirectory.
"""

# Re-export everything from the actual rate_limiter module
from platform.llm.providers.openrouter.openrouter_service import rate_limiter as _mod
from platform.llm.providers.openrouter.openrouter_service.rate_limiter import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
