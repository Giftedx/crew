"""Compatibility shim for platform.core.llm_client."""

from platform.llm.client import LLMCallResult, LLMClient


__all__ = ["LLMCallResult", "LLMClient"]
