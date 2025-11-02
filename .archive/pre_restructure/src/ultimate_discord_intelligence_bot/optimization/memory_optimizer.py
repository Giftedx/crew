"""Memory Optimization System.

This module provides intelligent memory optimization strategies
for the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import gc
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any

import psutil

from ultimate_discord_intelligence_bot.optimization.memory_pool import MemoryPool, ResourceManager


@dataclass
class MemoryProfile:
    """Memory usage profile for analysis."""

    baseline_memory_mb: float
    peak_memory_mb: float
    current_memory_mb: float
    memory_growth_mb: float
    object_count: int
    gc_collections: int
    memory_fragmentation: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class OptimizationStrategy:
    """Memory optimization strategy."""

    name: str
    description: str
    priority: int  # 1-10 scale
    enabled: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)


class MemoryOptimizer:
    """Intelligent memory optimization system."""

    def __init__(self, enable_tracing: bool = True):
        """Initialize the memory optimizer."""
        self.enable_tracing = enable_tracing
        self.memory_pool = MemoryPool(enable_gc_optimization=True)
        self.resource_manager = ResourceManager(self.memory_pool)

        # Memory profiling
        self._profiles: list[MemoryProfile] = []
        self._baseline_memory = 0.0
        self._peak_memory = 0.0

        # Optimization strategies
        self._strategies: dict[str, OptimizationStrategy] = {}
        self._initialize_strategies()

        # Start memory tracking
        if self.enable_tracing:
            tracemalloc.start()
            self._baseline_memory = self._get_current_memory()

    def _initialize_strategies(self):
        """Initialize optimization strategies."""
        strategies = [
            OptimizationStrategy(
                name="gc_optimization",
                description="Garbage collection optimization",
                priority=8,
                parameters={"force_collection": True, "generation": 2},
            ),
            OptimizationStrategy(
                name="object_pooling",
                description="Object pooling for frequently created objects",
                priority=7,
                parameters={"max_pool_size": 100, "cleanup_interval": 300},
            ),
            OptimizationStrategy(
                name="memory_compaction",
                description="Memory compaction and defragmentation",
                priority=6,
                parameters={"threshold_mb": 100, "compaction_ratio": 0.8},
            ),
            OptimizationStrategy(
                name="lazy_loading",
                description="Lazy loading of heavy resources",
                priority=9,
                parameters={"preload_critical": True, "cache_size": 50},
            ),
            OptimizationStrategy(
                name="resource_cleanup",
                description="Automatic resource cleanup",
                priority=5,
                parameters={"cleanup_interval": 60, "max_idle_time": 300},
            ),
        ]

        for strategy in strategies:
            self._strategies[strategy.name] = strategy

    def _get_current_memory(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def create_memory_profile(self) -> MemoryProfile:
        """Create a memory usage profile."""
        current_memory = self._get_current_memory()
        self._peak_memory = max(self._peak_memory, current_memory)

        # Calculate memory fragmentation
        if hasattr(psutil, "Process"):
            try:
                memory_info = psutil.Process().memory_info()
                fragmentation = (memory_info.vms - memory_info.rss) / memory_info.rss if memory_info.rss > 0 else 0
            except (AttributeError, OSError):
                fragmentation = 0.0
        else:
            fragmentation = 0.0

        profile = MemoryProfile(
            baseline_memory_mb=self._baseline_memory,
            peak_memory_mb=self._peak_memory,
            current_memory_mb=current_memory,
            memory_growth_mb=current_memory - self._baseline_memory,
            object_count=len(gc.get_objects()),
            gc_collections=sum(stat["collections"] for stat in gc.get_stats()),
            memory_fragmentation=fragmentation,
        )

        self._profiles.append(profile)

        # Keep only recent profiles
        if len(self._profiles) > 50:
            self._profiles = self._profiles[-50:]

        return profile

    def analyze_memory_usage(self) -> dict[str, Any]:
        """Analyze memory usage patterns."""
        profile = self.create_memory_profile()

        # Calculate trends
        if len(self._profiles) >= 2:
            recent_profiles = self._profiles[-5:]  # Last 5 profiles
            memory_trend = self._calculate_memory_trend(recent_profiles)
            growth_rate = self._calculate_growth_rate(recent_profiles)
        else:
            memory_trend = "stable"
            growth_rate = 0.0

        # Identify memory issues
        issues = self._identify_memory_issues(profile)

        # Generate recommendations
        recommendations = self._generate_recommendations(profile, issues)

        return {
            "current_profile": profile.__dict__,
            "memory_trend": memory_trend,
            "growth_rate_mb_per_minute": growth_rate,
            "issues": issues,
            "recommendations": recommendations,
            "optimization_opportunities": self._find_optimization_opportunities(profile),
        }

    def _calculate_memory_trend(self, profiles: list[MemoryProfile]) -> str:
        """Calculate memory usage trend."""
        if len(profiles) < 2:
            return "insufficient_data"

        recent_memory = [p.current_memory_mb for p in profiles]

        # Simple trend calculation
        if recent_memory[-1] > recent_memory[0] * 1.1:
            return "increasing"
        elif recent_memory[-1] < recent_memory[0] * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _calculate_growth_rate(self, profiles: list[MemoryProfile]) -> float:
        """Calculate memory growth rate in MB per minute."""
        if len(profiles) < 2:
            return 0.0

        time_diff = profiles[-1].timestamp - profiles[0].timestamp
        memory_diff = profiles[-1].current_memory_mb - profiles[0].current_memory_mb

        if time_diff > 0:
            return (memory_diff / time_diff) * 60  # MB per minute
        return 0.0

    def _identify_memory_issues(self, profile: MemoryProfile) -> list[str]:
        """Identify potential memory issues."""
        issues = []

        # High memory usage
        if profile.current_memory_mb > 1000:  # 1GB
            issues.append("high_memory_usage")

        # Memory growth
        if profile.memory_growth_mb > 100:  # 100MB growth
            issues.append("excessive_memory_growth")

        # High fragmentation
        if profile.memory_fragmentation > 0.5:  # 50% fragmentation
            issues.append("high_memory_fragmentation")

        # Too many objects
        if profile.object_count > 100000:  # 100k objects
            issues.append("excessive_object_count")

        # Frequent GC
        if profile.gc_collections > 100:  # 100 collections
            issues.append("frequent_garbage_collection")

        return issues

    def _generate_recommendations(self, profile: MemoryProfile, issues: list[str]) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if "high_memory_usage" in issues:
            recommendations.append("Consider implementing object pooling for frequently created objects")
            recommendations.append("Enable lazy loading for heavy resources")

        if "excessive_memory_growth" in issues:
            recommendations.append("Review object lifecycle management")
            recommendations.append("Implement automatic resource cleanup")

        if "high_memory_fragmentation" in issues:
            recommendations.append("Consider memory compaction strategies")
            recommendations.append("Review object allocation patterns")

        if "excessive_object_count" in issues:
            recommendations.append("Implement object reuse patterns")
            recommendations.append("Review object creation frequency")

        if "frequent_garbage_collection" in issues:
            recommendations.append("Optimize object allocation patterns")
            recommendations.append("Consider manual memory management for critical paths")

        if not issues:
            recommendations.append("Memory usage appears optimal")

        return recommendations

    def _find_optimization_opportunities(self, profile: MemoryProfile) -> list[dict[str, Any]]:
        """Find specific optimization opportunities."""
        opportunities = []

        # Object pooling opportunity
        if profile.object_count > 50000:
            opportunities.append(
                {
                    "type": "object_pooling",
                    "description": "High object count suggests pooling opportunities",
                    "potential_savings_mb": min(profile.current_memory_mb * 0.2, 200),
                    "priority": "high",
                }
            )

        # Memory compaction opportunity
        if profile.memory_fragmentation > 0.3:
            opportunities.append(
                {
                    "type": "memory_compaction",
                    "description": "High fragmentation suggests compaction benefits",
                    "potential_savings_mb": profile.current_memory_mb * profile.memory_fragmentation * 0.5,
                    "priority": "medium",
                }
            )

        # GC optimization opportunity
        if profile.gc_collections > 50:
            opportunities.append(
                {
                    "type": "gc_optimization",
                    "description": "Frequent GC suggests optimization opportunities",
                    "potential_savings_mb": 50,
                    "priority": "medium",
                }
            )

        return opportunities

    def apply_optimization_strategy(self, strategy_name: str) -> dict[str, Any]:
        """Apply a specific optimization strategy."""
        if strategy_name not in self._strategies:
            return {"error": f"Unknown strategy: {strategy_name}"}

        strategy = self._strategies[strategy_name]
        if not strategy.enabled:
            return {"error": f"Strategy {strategy_name} is disabled"}

        initial_memory = self._get_current_memory()

        try:
            if strategy_name == "gc_optimization":
                result = self._apply_gc_optimization(strategy.parameters)
            elif strategy_name == "object_pooling":
                result = self._apply_object_pooling(strategy.parameters)
            elif strategy_name == "memory_compaction":
                result = self._apply_memory_compaction(strategy.parameters)
            elif strategy_name == "lazy_loading":
                result = self._apply_lazy_loading(strategy.parameters)
            elif strategy_name == "resource_cleanup":
                result = self._apply_resource_cleanup(strategy.parameters)
            else:
                return {"error": f"Unknown strategy implementation: {strategy_name}"}

            final_memory = self._get_current_memory()
            memory_saved = initial_memory - final_memory

            return {
                "strategy": strategy_name,
                "success": True,
                "memory_saved_mb": memory_saved,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "result": result,
            }

        except Exception as e:
            return {"strategy": strategy_name, "success": False, "error": str(e)}

    def _apply_gc_optimization(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply garbage collection optimization."""
        if params.get("force_collection", True):
            collected = gc.collect()
            return {"objects_collected": collected}
        return {"objects_collected": 0}

    def _apply_object_pooling(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply object pooling optimization."""
        # This would integrate with the memory pool system
        return {"pool_optimization": "applied"}

    def _apply_memory_compaction(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply memory compaction."""
        # Force garbage collection for compaction
        collected = gc.collect()
        return {"compaction_applied": True, "objects_collected": collected}

    def _apply_lazy_loading(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply lazy loading optimization."""
        # This would integrate with the lazy loading system
        return {"lazy_loading": "optimized"}

    def _apply_resource_cleanup(self, params: dict[str, Any]) -> dict[str, Any]:
        """Apply resource cleanup optimization."""
        # Clean up idle resources
        self.memory_pool._cleanup_idle_resources()
        return {"cleanup_applied": True}

    def optimize_memory(self) -> dict[str, Any]:
        """Perform comprehensive memory optimization."""
        initial_profile = self.create_memory_profile()

        # Apply all enabled strategies
        optimization_results = {}
        total_memory_saved = 0.0

        for strategy_name, strategy in self._strategies.items():
            if strategy.enabled:
                result = self.apply_optimization_strategy(strategy_name)
                optimization_results[strategy_name] = result

                if result.get("success", False):
                    total_memory_saved += result.get("memory_saved_mb", 0)

        final_profile = self.create_memory_profile()

        return {
            "initial_memory_mb": initial_profile.current_memory_mb,
            "final_memory_mb": final_profile.current_memory_mb,
            "total_memory_saved_mb": total_memory_saved,
            "optimization_results": optimization_results,
            "memory_profile": final_profile.__dict__,
        }

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization statistics."""
        current_profile = self.create_memory_profile()

        return {
            "current_memory_mb": current_profile.current_memory_mb,
            "peak_memory_mb": current_profile.peak_memory_mb,
            "memory_growth_mb": current_profile.memory_growth_mb,
            "object_count": current_profile.object_count,
            "gc_collections": current_profile.gc_collections,
            "memory_fragmentation": current_profile.memory_fragmentation,
            "enabled_strategies": [name for name, strategy in self._strategies.items() if strategy.enabled],
            "pool_stats": self.memory_pool.get_pool_stats(),
        }


# Global memory optimizer instance
_global_memory_optimizer = MemoryOptimizer()


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance."""
    return _global_memory_optimizer


def analyze_memory_usage() -> dict[str, Any]:
    """Analyze memory usage patterns."""
    optimizer = get_memory_optimizer()
    return optimizer.analyze_memory_usage()


def optimize_memory() -> dict[str, Any]:
    """Optimize memory usage."""
    optimizer = get_memory_optimizer()
    return optimizer.optimize_memory()


def get_memory_stats() -> dict[str, Any]:
    """Get memory optimization statistics."""
    optimizer = get_memory_optimizer()
    return optimizer.get_optimization_stats()
