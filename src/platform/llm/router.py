"""Compatibility shim for LLM router.

Re-exports from platform.llm for backward compatibility.
"""

from platform.llm.llm_router import LLMRouter
from platform.llm.routing.base_router import BaseRouter


__all__ = ["BaseRouter", "LLMRouter"]
