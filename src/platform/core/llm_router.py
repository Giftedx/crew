"""Compatibility shim for platform.core.llm_router."""

from platform.llm.routing.base_router import BaseRouter as LLMRouter


__all__ = ["LLMRouter"]
