"""OpenRouter service package with refactored components."""

from __future__ import annotations

from .facade import OpenRouterServiceFacade
from .refactored_service import RefactoredOpenRouterService
from .registry import OpenRouterServiceRegistry, ServiceRegistry
from .route_components import (
    CacheManager,
    CostCalculator,
    MetricsRecorder,
    NetworkExecutor,
    OfflineExecutor,
    RewardCalculator,
    RouteContext,
    RouteResult,
    TenantResolver,
)


# Alias for backward compatibility
OpenRouterService = RefactoredOpenRouterService


__all__ = [
    "CacheManager",
    "CostCalculator",
    "MetricsRecorder",
    "NetworkExecutor",
    "OfflineExecutor",
    "OpenRouterService",
    "OpenRouterServiceFacade",
    "OpenRouterServiceRegistry",
    "RefactoredOpenRouterService",
    "RewardCalculator",
    "RouteContext",
    "RouteResult",
    "ServiceRegistry",
    "TenantResolver",
]
