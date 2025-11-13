"""Compatibility shim for token meter.

Re-exports from platform.llm.token_meter for backward compatibility.
"""

from platform.llm.token_meter import TokenMeter, cost_guard, estimate_tokens


__all__ = ["TokenMeter", "cost_guard", "estimate_tokens"]
