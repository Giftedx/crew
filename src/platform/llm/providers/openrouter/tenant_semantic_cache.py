"""Compatibility shim for platform.llm.providers.openrouter.tenant_semantic_cache imports.

Re-exports tenant_semantic_cache module from openrouter_service subdirectory.
"""

# Re-export everything from the actual tenant_semantic_cache module
from platform.llm.providers.openrouter.openrouter_service import tenant_semantic_cache as _mod
from platform.llm.providers.openrouter.openrouter_service.tenant_semantic_cache import *  # noqa: F403


__all__ = getattr(_mod, "__all__", [])
