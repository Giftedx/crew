"""Orchestration strategies for different execution patterns.

Strategies:
- FallbackStrategy: Degraded mode when CrewAI unavailable
- HierarchicalStrategy: Supervisor-worker coordination
- MonitoringStrategy: Platform monitoring orchestration
"""

from .base import (
    OrchestrationStrategyProtocol,
    StrategyRegistry,
    get_strategy_registry,
)
from .fallback_strategy import FallbackStrategy
from .hierarchical_strategy import HierarchicalStrategy
from .monitoring_strategy import MonitoringStrategy


__all__ = [
    "FallbackStrategy",
    "HierarchicalStrategy",
    "MonitoringStrategy",
    "OrchestrationStrategyProtocol",
    "StrategyRegistry",
    "get_strategy_registry",
]
