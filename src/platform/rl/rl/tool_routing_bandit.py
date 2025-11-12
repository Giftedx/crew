"""Compatibility shim for tool routing bandit.

Re-exports from platform.rl for backward compatibility.
"""

from platform.rl.tool_routing_bandit import *  # noqa: F403, F401

__all__ = [
    "ToolRoutingBandit",
    "ToolCapability",
    "ToolContextualBandit",
    "get_tool_router",
]
