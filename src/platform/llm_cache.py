"""Compatibility shim for LLM cache.

Re-exports from platform.cache.llm_cache for backward compatibility.
"""

from platform.cache.llm_cache import *  # noqa: F403


__all__ = ["LLMCache", "get_llm_cache"]
