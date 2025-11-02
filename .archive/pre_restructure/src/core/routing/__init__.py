"""Unified routing system for the Ultimate Discord Intelligence Bot.

This module provides a unified router architecture with strategy pattern,
consolidating multiple routing approaches into a single, extensible system.
"""

from .base_router import (
    BanditRouter,
    BaseRouter,
    CostAwareRouter,
    FallbackRouter,
    LatencyOptimizedRouter,
    RoutingDecision,
    RoutingRequest,
    UnifiedRouter,
)
from .llm_adapter import RouterLLMAdapter, create_router_llm


__all__ = [
    "BanditRouter",
    "BaseRouter",
    "CostAwareRouter",
    "FallbackRouter",
    "LatencyOptimizedRouter",
    "RouterLLMAdapter",
    "RoutingDecision",
    "RoutingRequest",
    "UnifiedRouter",
    "create_router_llm",
]
