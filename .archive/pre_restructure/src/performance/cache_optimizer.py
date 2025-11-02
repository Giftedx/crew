"""Cache Performance Optimizer and Monitor.

This module provides comprehensive cache optimization tools including:
- Real-time performance monitoring
- Automatic threshold adjustment
- Cost savings analysis
- Performance recommendations
- Cache health checks
- Optimization reporting
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from core.cache.adaptive_semantic_cache import get_adaptive_semantic_cache
from core.vector_search.optimized_vector_store import get_optimized_vector_store
from obs.metrics import generate_latest


logger = logging.getLogger(__name__)

# Performance targets
TARGET_CACHE_HIT_RATE = 0.60  # 60% hit rate
TARGET_VECTOR_SEARCH_LATENCY_MS = 50  # 50ms vector search
TARGET_COST_SAVINGS = 0.20  # 20% cost savings
MONITORING_INTERVAL_SECONDS = 60  # Monitor every minute
OPTIMIZATION_INTERVAL_SECONDS = 300  # Optimize every 5 minutes


@dataclass
class OptimizationReport:
    """Comprehensive optimization report."""

    timestamp: float = field(default_factory=time.time)
    cache_performance: dict[str, Any] = field(default_factory=dict)
    vector_search_performance: dict[str, Any] = field(default_factory=dict)
    cost_savings: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    optimizations_applied: list[str] = field(default_factory=list)
    targets_met: dict[str, bool] = field(default_factory=dict)
    overall_score: float = 0.0


class CacheOptimizer:
    """Comprehensive cache optimization and monitoring system."""

    def __init__(
        self,
        monitoring_interval: int = MONITORING_INTERVAL_SECONDS,
        optimization_interval: int = OPTIMIZATION_INTERVAL_SECONDS,
        enable_auto_optimization: bool = True,
        enable_cost_tracking: bool = True,
    ):
        """Initialize cache optimizer.

        Args:
            monitoring_interval: Interval for performance monitoring (seconds)
            optimization_interval: Interval for automatic optimization (seconds)
            enable_auto_optimization: Enable automatic optimization
            enable_cost_tracking: Enable cost savings tracking
        """
        self.monitoring_interval = monitoring_interval
        self.optimization_interval = optimization_interval
        self.enable_auto_optimization = enable_auto_optimization
        self.enable_cost_tracking = enable_cost_tracking

        # Performance tracking
        self.performance_history: list[OptimizationReport] = []
        self.monitoring_task: asyncio.Task[None] | None = None
        self.optimization_task: asyncio.Task[None] | None = None

        # Cost tracking
        self.total_cost_saved = 0.0
        self.total_requests_processed = 0

        logger.info(
            f"Initialized cache optimizer with monitoring every {monitoring_interval}s, optimization every {optimization_interval}s"
        )

    async def start_monitoring(self) -> None:
        """Start continuous monitoring and optimization."""
        if self.monitoring_task is None or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self.enable_auto_optimization and (self.optimization_task is None or self.optimization_task.done()):
            self.optimization_task = asyncio.create_task(self._optimization_loop())

        logger.info("Started cache monitoring and optimization")

    async def stop_monitoring(self) -> None:
        """Stop monitoring and optimization tasks."""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.monitoring_task

        if self.optimization_task and not self.optimization_task.done():
            self.optimization_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.optimization_task

        logger.info("Stopped cache monitoring and optimization")

    async def _monitoring_loop(self) -> None:
        """Continuous monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)

                # Collect performance data
                report = await self._collect_performance_data()

                # Store in history
                self.performance_history.append(report)

                # Keep only recent history (last 24 hours)
                cutoff_time = time.time() - (24 * 60 * 60)
                self.performance_history = [r for r in self.performance_history if r.timestamp > cutoff_time]

                # Log performance summary
                logger.info(
                    f"Performance monitoring - "
                    f"Cache hit rate: {report.cache_performance.get('hit_rate', 0):.3f}, "
                    f"Vector search latency: {report.vector_search_performance.get('avg_latency_ms', 0):.1f}ms, "
                    f"Cost savings: {report.cost_savings.get('total_cost_saved', 0):.2f}"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def _optimization_loop(self) -> None:
        """Automatic optimization loop."""
        while True:
            try:
                await asyncio.sleep(self.optimization_interval)

                # Run optimization
                await self._run_optimization()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _collect_performance_data(self) -> OptimizationReport:
        """Collect comprehensive performance data."""
        report = OptimizationReport()

        try:
            # Get semantic cache performance
            semantic_cache = await get_adaptive_semantic_cache()
            report.cache_performance = semantic_cache.get_performance_summary()

            # Get vector search performance
            vector_store = await get_optimized_vector_store()
            report.vector_search_performance = vector_store.get_performance_summary()

            # Calculate cost savings
            report.cost_savings = await self._calculate_cost_savings(report.cache_performance)

            # Generate recommendations
            report.recommendations = await self._generate_recommendations(report)

            # Check targets
            report.targets_met = self._check_performance_targets(report)

            # Calculate overall score
            report.overall_score = self._calculate_overall_score(report)

        except Exception as e:
            logger.error(f"Error collecting performance data: {e}")
            report.recommendations.append(f"Error collecting performance data: {e}")

        return report

    async def _calculate_cost_savings(self, cache_performance: dict[str, Any]) -> dict[str, Any]:
        """Calculate cost savings from cache performance."""
        if not self.enable_cost_tracking:
            return {"enabled": False}

        try:
            hit_rate = cache_performance.get("hit_rate", 0.0)
            total_requests = cache_performance.get("total_requests", 0)
            total_cost_saved = cache_performance.get("total_cost_saved", 0.0)

            # Calculate additional metrics
            estimated_total_cost = total_requests * 0.01  # Assume $0.01 per request
            cost_savings_ratio = total_cost_saved / max(1.0, estimated_total_cost)

            # Update running totals
            self.total_cost_saved += total_cost_saved
            self.total_requests_processed += total_requests

            return {
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "total_cost_saved": total_cost_saved,
                "cost_savings_ratio": cost_savings_ratio,
                "estimated_total_cost": estimated_total_cost,
                "cumulative_cost_saved": self.total_cost_saved,
                "cumulative_requests": self.total_requests_processed,
                "enabled": True,
            }

        except Exception as e:
            logger.error(f"Error calculating cost savings: {e}")
            return {"error": str(e), "enabled": True}

    async def _generate_recommendations(self, report: OptimizationReport) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        try:
            # Cache performance recommendations
            cache_hit_rate = report.cache_performance.get("hit_rate", 0.0)
            if cache_hit_rate < TARGET_CACHE_HIT_RATE:
                recommendations.append(
                    f"Cache hit rate {cache_hit_rate:.3f} below target {TARGET_CACHE_HIT_RATE}. "
                    "Consider lowering similarity threshold or increasing cache size."
                )

            # Vector search performance recommendations
            vector_latency = report.vector_search_performance.get("avg_latency_ms", 0.0)
            if vector_latency > TARGET_VECTOR_SEARCH_LATENCY_MS:
                recommendations.append(
                    f"Vector search latency {vector_latency:.1f}ms above target {TARGET_VECTOR_SEARCH_LATENCY_MS}ms. "
                    "Consider enabling batch processing or optimizing indexing."
                )

            # Cost savings recommendations
            cost_savings_ratio = report.cost_savings.get("cost_savings_ratio", 0.0)
            if cost_savings_ratio < TARGET_COST_SAVINGS:
                recommendations.append(
                    f"Cost savings ratio {cost_savings_ratio:.3f} below target {TARGET_COST_SAVINGS}. "
                    "Consider improving cache hit rate or reducing LLM API calls."
                )

            # Positive feedback
            if cache_hit_rate >= TARGET_CACHE_HIT_RATE:
                recommendations.append(f"Excellent cache hit rate: {cache_hit_rate:.3f}")

            if vector_latency <= TARGET_VECTOR_SEARCH_LATENCY_MS:
                recommendations.append(f"Excellent vector search latency: {vector_latency:.1f}ms")

            if cost_savings_ratio >= TARGET_COST_SAVINGS:
                recommendations.append(f"Excellent cost savings: {cost_savings_ratio:.3f}")

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append(f"Error generating recommendations: {e}")

        return recommendations

    def _check_performance_targets(self, report: OptimizationReport) -> dict[str, bool]:
        """Check if performance targets are met."""
        cache_hit_rate = report.cache_performance.get("hit_rate", 0.0)
        vector_latency = report.vector_search_performance.get("avg_latency_ms", float("inf"))
        cost_savings_ratio = report.cost_savings.get("cost_savings_ratio", 0.0)

        return {
            "cache_hit_rate_target": cache_hit_rate >= TARGET_CACHE_HIT_RATE,
            "vector_search_latency_target": vector_latency <= TARGET_VECTOR_SEARCH_LATENCY_MS,
            "cost_savings_target": cost_savings_ratio >= TARGET_COST_SAVINGS,
        }

    def _calculate_overall_score(self, report: OptimizationReport) -> float:
        """Calculate overall performance score (0.0 to 1.0)."""
        targets_met = report.targets_met

        # Weight each target equally
        score = sum(targets_met.values()) / len(targets_met)

        # Bonus for exceeding targets
        cache_hit_rate = report.cache_performance.get("hit_rate", 0.0)
        if cache_hit_rate > TARGET_CACHE_HIT_RATE:
            score += min(0.1, (cache_hit_rate - TARGET_CACHE_HIT_RATE) * 2)

        vector_latency = report.vector_search_performance.get("avg_latency_ms", float("inf"))
        if vector_latency < TARGET_VECTOR_SEARCH_LATENCY_MS:
            score += min(0.1, (TARGET_VECTOR_SEARCH_LATENCY_MS - vector_latency) / 100)

        return min(1.0, score)

    async def _run_optimization(self) -> None:
        """Run automatic optimization."""
        try:
            logger.info("Running automatic cache optimization...")

            # Optimize semantic cache
            semantic_cache = await get_adaptive_semantic_cache()
            cache_recommendation = await semantic_cache.force_optimization()

            # Optimize vector store
            vector_store = await get_optimized_vector_store()
            vector_optimization = await vector_store.optimize_performance()

            # Log optimizations
            if cache_recommendation:
                logger.info(f"Cache optimization applied: {cache_recommendation.action}")

            if vector_optimization.get("optimizations_applied"):
                logger.info(f"Vector store optimizations: {vector_optimization['optimizations_applied']}")

        except Exception as e:
            logger.error(f"Error during optimization: {e}")

    async def get_performance_report(self) -> OptimizationReport:
        """Get current performance report."""
        return await self._collect_performance_data()

    def get_performance_history(self, hours: int = 24) -> list[OptimizationReport]:
        """Get performance history for specified hours."""
        cutoff_time = time.time() - (hours * 60 * 60)
        return [r for r in self.performance_history if r.timestamp > cutoff_time]

    def get_performance_trends(self, hours: int = 24) -> dict[str, Any]:
        """Analyze performance trends over time."""
        history = self.get_performance_history(hours)

        if not history:
            return {"error": "No performance history available"}

        # Extract trends
        hit_rates = [r.cache_performance.get("hit_rate", 0.0) for r in history]
        latencies = [r.vector_search_performance.get("avg_latency_ms", 0.0) for r in history]
        scores = [r.overall_score for r in history]

        return {
            "period_hours": hours,
            "data_points": len(history),
            "hit_rate_trend": {
                "current": hit_rates[-1] if hit_rates else 0.0,
                "average": sum(hit_rates) / len(hit_rates) if hit_rates else 0.0,
                "min": min(hit_rates) if hit_rates else 0.0,
                "max": max(hit_rates) if hit_rates else 0.0,
                "trend": "improving" if len(hit_rates) > 1 and hit_rates[-1] > hit_rates[0] else "declining",
            },
            "latency_trend": {
                "current": latencies[-1] if latencies else 0.0,
                "average": sum(latencies) / len(latencies) if latencies else 0.0,
                "min": min(latencies) if latencies else 0.0,
                "max": max(latencies) if latencies else 0.0,
                "trend": "improving" if len(latencies) > 1 and latencies[-1] < latencies[0] else "declining",
            },
            "overall_score_trend": {
                "current": scores[-1] if scores else 0.0,
                "average": sum(scores) / len(scores) if scores else 0.0,
                "min": min(scores) if scores else 0.0,
                "max": max(scores) if scores else 0.0,
                "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "declining",
            },
        }

    async def export_metrics(self) -> bytes:
        """Export Prometheus metrics."""
        try:
            return generate_latest()  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return b""


# Global optimizer instance
_optimizer: CacheOptimizer | None = None


def get_cache_optimizer() -> CacheOptimizer:
    """Get global cache optimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = CacheOptimizer()
    return _optimizer


async def start_cache_optimization() -> None:
    """Start global cache optimization."""
    optimizer = get_cache_optimizer()
    await optimizer.start_monitoring()


async def stop_cache_optimization() -> None:
    """Stop global cache optimization."""
    optimizer = get_cache_optimizer()
    await optimizer.stop_monitoring()


async def get_optimization_report() -> OptimizationReport:
    """Get current optimization report."""
    optimizer = get_cache_optimizer()
    return await optimizer.get_performance_report()


__all__ = [
    "CacheOptimizer",
    "OptimizationReport",
    "get_cache_optimizer",
    "get_optimization_report",
    "start_cache_optimization",
    "stop_cache_optimization",
]
