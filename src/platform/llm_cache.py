"""Compatibility shim for LLM cache.

Re-exports from platform.cache.llm_cache for backward compatibility.
"""

from platform.cache.llm_cache import get_llm_cache


__all__ = ["get_llm_cache"]
