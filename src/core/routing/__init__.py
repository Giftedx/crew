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
    "BaseRouter",
    "RoutingRequest",
    "RoutingDecision",
    "UnifiedRouter",
    "BanditRouter",
    "CostAwareRouter",
    "LatencyOptimizedRouter",
    "FallbackRouter",
    "RouterLLMAdapter",
    "create_router_llm",
]
