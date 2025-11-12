"""Compatibility shim for token meter.

Re-exports from platform.llm.token_meter for backward compatibility.
"""

from platform.llm.token_meter import *  # noqa: F403


__all__ = ["TokenMeter", "cost_guard", "estimate_tokens"]
