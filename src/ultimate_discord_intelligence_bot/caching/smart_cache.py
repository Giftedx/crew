"""Smart Caching System with Adaptive Strategies.

This module provides intelligent caching that adapts to usage patterns
and automatically determines optimal caching strategies for different tools.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.caching.result_cache import ResultCache
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class ToolUsagePattern:
    """Track usage patterns for a tool."""

    tool_name: str
    call_count: int = 0
    total_execution_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_called: datetime | None = None
    avg_execution_time: float = 0.0
    hit_rate: float = 0.0

    def update_call(self, execution_time: float, cache_hit: bool = False):
        """Update usage statistics."""
        self.call_count += 1
        self.total_execution_time += execution_time
        self.avg_execution_time = self.total_execution_time / self.call_count
        self.last_called = datetime.now(timezone.utc)

        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        total_cache_attempts = self.cache_hits + self.cache_misses
        self.hit_rate = (self.cache_hits / total_cache_attempts * 100) if total_cache_attempts > 0 else 0


@dataclass
class CachingStrategy:
    """Caching strategy for a tool."""

    tool_name: str
    enabled: bool = True
    ttl: int = 3600  # 1 hour default
    priority: int = 5  # 1-10 scale
    adaptive_ttl: bool = True
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


class SmartCache:
    """Intelligent caching system with adaptive strategies."""

    def __init__(self, base_cache: ResultCache | None = None):
        """Initialize the smart cache."""
        self.base_cache = base_cache or ResultCache()
        self.usage_patterns: dict[str, ToolUsagePattern] = {}
        self.caching_strategies: dict[str, CachingStrategy] = {}
        self.adaptive_ttl_enabled = True
        self.learning_period = 100  # calls before adapting
        self.min_ttl = 60  # 1 minute minimum
        self.max_ttl = 86400  # 24 hours maximum

    def get_usage_pattern(self, tool_name: str) -> ToolUsagePattern:
        """Get or create usage pattern for a tool."""
        if tool_name not in self.usage_patterns:
            self.usage_patterns[tool_name] = ToolUsagePattern(tool_name=tool_name)
        return self.usage_patterns[tool_name]

    def get_caching_strategy(self, tool_name: str) -> CachingStrategy:
        """Get or create caching strategy for a tool."""
        if tool_name not in self.caching_strategies:
            self.caching_strategies[tool_name] = CachingStrategy(tool_name=tool_name)
        return self.caching_strategies[tool_name]

    def analyze_tool_performance(self, tool_name: str) -> dict[str, Any]:
        """Analyze tool performance and suggest caching strategy."""
        pattern = self.get_usage_pattern(tool_name)
        strategy = self.get_caching_strategy(tool_name)

        # Determine if caching should be enabled
        should_cache = (
            pattern.call_count > 5  # Called multiple times
            and pattern.avg_execution_time > 0.1  # Takes some time
            and pattern.hit_rate < 80  # Not already well cached
        )

        # Calculate optimal TTL based on usage patterns
        optimal_ttl = self._calculate_optimal_ttl(pattern)

        # Determine priority based on usage
        priority = self._calculate_priority(pattern)

        return {
            "tool_name": tool_name,
            "should_cache": should_cache,
            "current_ttl": strategy.ttl,
            "optimal_ttl": optimal_ttl,
            "priority": priority,
            "usage_stats": {
                "call_count": pattern.call_count,
                "avg_execution_time": pattern.avg_execution_time,
                "hit_rate": pattern.hit_rate,
                "last_called": pattern.last_called.isoformat() if pattern.last_called else None,
            },
            "recommendations": self._generate_recommendations(pattern, strategy),
        }

    def _calculate_optimal_ttl(self, pattern: ToolUsagePattern) -> int:
        """Calculate optimal TTL based on usage patterns."""
        if not self.adaptive_ttl_enabled:
            return 3600  # Default 1 hour

        # Base TTL on how often the tool is called
        if pattern.call_count < 10:
            return 1800  # 30 minutes for rarely used tools
        elif pattern.call_count < 50:
            return 3600  # 1 hour for moderately used tools
        else:
            return 7200  # 2 hours for frequently used tools

    def _calculate_priority(self, pattern: ToolUsagePattern) -> int:
        """Calculate caching priority based on usage patterns."""
        # Higher execution time = higher priority
        # More frequent calls = higher priority
        # Lower hit rate = higher priority

        execution_score = min(pattern.avg_execution_time * 10, 5)  # 0-5 scale
        frequency_score = min(pattern.call_count / 20, 3)  # 0-3 scale
        hit_rate_score = max(0, (80 - pattern.hit_rate) / 20)  # 0-4 scale (inverse)

        priority = int(execution_score + frequency_score + hit_rate_score)
        return max(1, min(10, priority))

    def _generate_recommendations(self, pattern: ToolUsagePattern, strategy: CachingStrategy) -> list[str]:
        """Generate caching recommendations."""
        recommendations = []

        if pattern.call_count < 5:
            recommendations.append("Tool called infrequently - consider disabling cache")
        elif pattern.avg_execution_time < 0.1:
            recommendations.append("Tool executes quickly - cache may not be beneficial")
        elif pattern.hit_rate > 80:
            recommendations.append("Tool already well cached - current strategy is good")
        else:
            if strategy.ttl < 1800:
                recommendations.append("Consider increasing TTL for better cache efficiency")
            if pattern.avg_execution_time > 1.0:
                recommendations.append("High execution time - prioritize caching this tool")
            if pattern.call_count > 50:
                recommendations.append("Frequently called tool - ensure cache is enabled")

        return recommendations

    def update_strategy(self, tool_name: str, **updates):
        """Update caching strategy for a tool."""
        strategy = self.get_caching_strategy(tool_name)

        for key, value in updates.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)

    def auto_optimize(self):
        """Automatically optimize caching strategies based on usage patterns."""
        for tool_name, pattern in self.usage_patterns.items():
            if pattern.call_count >= self.learning_period:
                # Analyze and update strategy
                analysis = self.analyze_tool_performance(tool_name)

                if analysis["should_cache"]:
                    self.update_strategy(
                        tool_name, enabled=True, ttl=analysis["optimal_ttl"], priority=analysis["priority"]
                    )
                else:
                    self.update_strategy(tool_name, enabled=False)

    def get_smart_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive smart cache statistics."""
        base_stats = self.base_cache.get_stats()

        # Analyze all tools
        tool_analyses = {}
        for tool_name in self.usage_patterns:
            tool_analyses[tool_name] = self.analyze_tool_performance(tool_name)

        # Calculate overall metrics
        total_tools = len(self.usage_patterns)
        cached_tools = sum(1 for strategy in self.caching_strategies.values() if strategy.enabled)
        avg_hit_rate = (
            sum(pattern.hit_rate for pattern in self.usage_patterns.values()) / total_tools if total_tools > 0 else 0
        )

        return {
            "base_cache": base_stats,
            "smart_cache": {
                "total_tools": total_tools,
                "cached_tools": cached_tools,
                "cache_coverage": (cached_tools / total_tools * 100) if total_tools > 0 else 0,
                "avg_hit_rate": avg_hit_rate,
                "adaptive_ttl_enabled": self.adaptive_ttl_enabled,
            },
            "tool_analyses": tool_analyses,
            "strategies": {
                name: {
                    "enabled": strategy.enabled,
                    "ttl": strategy.ttl,
                    "priority": strategy.priority,
                    "adaptive_ttl": strategy.adaptive_ttl,
                }
                for name, strategy in self.caching_strategies.items()
            },
        }


# Global smart cache instance
_global_smart_cache = SmartCache()


def get_smart_cache() -> SmartCache:
    """Get the global smart cache instance."""
    return _global_smart_cache


def smart_cache_tool_result(ttl: int | None = None, adaptive: bool = True, priority: int = 5):
    """Smart caching decorator that adapts to tool usage patterns."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            smart_cache = get_smart_cache()
            tool_name = getattr(self, "name", self.__class__.__name__)

            # Get usage pattern and strategy
            pattern = smart_cache.get_usage_pattern(tool_name)
            strategy = smart_cache.get_caching_strategy(tool_name)

            # Record call start
            start_time = time.time()

            # Check if caching is enabled for this tool
            if not strategy.enabled:
                # Execute without caching
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                pattern.update_call(execution_time, cache_hit=False)
                return result

            # Generate cache key
            cache_key = smart_cache.base_cache._generate_key(f"{tool_name}_{func.__name__}", args, kwargs)

            # Try to get from cache
            cached_result = smart_cache.base_cache.get(cache_key)
            if cached_result is not None:
                execution_time = time.time() - start_time
                pattern.update_call(execution_time, cache_hit=True)
                return cached_result

            # Execute function
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            pattern.update_call(execution_time, cache_hit=False)

            # Cache successful results
            if isinstance(result, StepResult) and result.success:
                effective_ttl = ttl or strategy.ttl
                smart_cache.base_cache.set(
                    cache_key, result, ttl=effective_ttl, metadata={"tool_name": tool_name, "priority": priority}
                )

            return result

        return wrapper

    return decorator


def analyze_cache_performance() -> dict[str, Any]:
    """Analyze overall cache performance and provide recommendations."""
    smart_cache = get_smart_cache()
    return smart_cache.get_smart_cache_stats()


def auto_optimize_cache():
    """Automatically optimize cache strategies based on usage patterns."""
    smart_cache = get_smart_cache()
    smart_cache.auto_optimize()


def get_cache_recommendations() -> dict[str, Any]:
    """Get caching recommendations for all tools."""
    smart_cache = get_smart_cache()
    recommendations = {}

    for tool_name in smart_cache.usage_patterns:
        analysis = smart_cache.analyze_tool_performance(tool_name)
        recommendations[tool_name] = {
            "should_cache": analysis["should_cache"],
            "optimal_ttl": analysis["optimal_ttl"],
            "priority": analysis["priority"],
            "recommendations": analysis["recommendations"],
        }

    return recommendations
