"""Memory Optimization System for the Ultimate Discord Intelligence Bot.

This package provides comprehensive memory optimization capabilities including:
- Memory pooling for resource management
- Intelligent memory optimization strategies
- Memory usage analysis and profiling
- Automatic resource cleanup and management
"""

from __future__ import annotations

from ultimate_discord_intelligence_bot.optimization.memory_optimizer import (
    MemoryOptimizer,
    analyze_memory_usage,
    get_memory_optimizer,
    get_memory_stats,
    optimize_memory,
)
from ultimate_discord_intelligence_bot.optimization.memory_pool import (
    MemoryPool,
    MemoryStats,
    PooledResource,
    ResourceContext,
    ResourceManager,
    get_pooled_resource,
    get_resource_manager,
    register_resource_type,
    return_pooled_resource,
    with_pooled_resource,
)
from ultimate_discord_intelligence_bot.optimization.memory_pool import (
    get_memory_stats as get_pool_stats,
)


__all__ = [
    # Memory optimizer
    "MemoryOptimizer",
    # Memory pool
    "MemoryPool",
    "MemoryStats",
    "PooledResource",
    "ResourceContext",
    "ResourceManager",
    "analyze_memory_usage",
    "get_memory_optimizer",
    "get_memory_stats",
    "get_pool_stats",
    "get_pooled_resource",
    "get_resource_manager",
    "optimize_memory",
    "register_resource_type",
    "return_pooled_resource",
    "with_pooled_resource",
]
