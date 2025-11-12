"""Compatibility shim for platform.llm.providers.openrouter.request_budget imports.

Re-exports request_budget module from openrouter_service subdirectory.
"""

# Re-export everything from the actual request_budget module
from platform.llm.providers.openrouter.openrouter_service import request_budget as _rb
from platform.llm.providers.openrouter.openrouter_service.request_budget import *  # noqa: F403


__all__ = getattr(_rb, "__all__", [])
