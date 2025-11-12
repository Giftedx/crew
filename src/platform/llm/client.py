"""Compatibility shim for LLM client.

Re-exports from platform.llm.llm_client for backward compatibility.
"""

from platform.llm.llm_client import *  # noqa: F403


__all__ = ["LLMCallResult", "LLMClient", "ProviderFn"]
