"""Database optimization utilities for improved performance and monitoring.

This module provides tools for optimizing database operations, connection pooling,
and query performance in the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Constants for optimization thresholds
OPTIMAL_UTILIZATION_LOW = 0.7
OPTIMAL_UTILIZATION_HIGH = 0.9
HIGH_UTILIZATION_THRESHOLD = 95.0
WARNING_UTILIZATION_THRESHOLD = 85.0
LOW_UTILIZATION_THRESHOLD = 30.0
WAITING_CLIENTS_THRESHOLD = 5
MIN_HISTORY_FOR_ANALYSIS = 10
MONITORING_HIGH_UTILIZATION = 90.0
QUERY_PREVIEW_LENGTH = 100


@dataclass
class QueryMetrics:
    """Metrics for database query performance."""

    query: str
    execution_time: float
    rows_affected: int
    connection_id: str | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ConnectionPoolMetrics:
    """Metrics for database connection pool performance."""

    pool_size: int
    active_connections: int
    idle_connections: int
    waiting_clients: int
    total_connections_created: int
    connections_destroyed: int
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def utilization_rate(self) -> float:
        """Calculate connection pool utilization rate."""
        return self.active_connections / max(1, self.pool_size) * 100.0

    @property
    def efficiency_score(self) -> float:
        """Calculate connection pool efficiency score (0-1)."""
        if self.pool_size == 0:
            return 0.0

        # Optimal utilization is 70-90%
        utilization = self.active_connections / self.pool_size
        if OPTIMAL_UTILIZATION_LOW <= utilization <= OPTIMAL_UTILIZATION_HIGH:
            return 1.0
        elif utilization < OPTIMAL_UTILIZATION_LOW:
            # Under-utilized - some efficiency loss
            return 0.8
        else:
            # Over-utilized - significant efficiency loss
            return max(0.0, 1.0 - (utilization - OPTIMAL_UTILIZATION_HIGH) * 2)


class QueryOptimizer:
    """Database query optimization and monitoring."""

    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_history: list[QueryMetrics] = []
        self.max_history_size = 1000

    @asynccontextmanager
    async def monitor_query(
        self, query: str, connection_id: str | None = None
    ) -> AsyncGenerator[Callable[[], None], None]:
        """Context manager to monitor query execution time."""
        start_time = time.time()

        def record_metrics(rows_affected: int = 0) -> None:
            """Record query metrics after execution."""
            execution_time = time.time() - start_time
            metrics = QueryMetrics(
                query=query, execution_time=execution_time, rows_affected=rows_affected, connection_id=connection_id
            )

            self.query_history.append(metrics)

            # Keep history size manageable
            if len(self.query_history) > self.max_history_size:
                self.query_history = self.query_history[-self.max_history_size :]

            # Log slow queries
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:QUERY_PREVIEW_LENGTH]}...")

        try:
            yield record_metrics
        finally:
            pass

    def get_slow_queries(self, limit: int = 10) -> list[QueryMetrics]:
        """Get the slowest queries from history."""
        slow_queries = [q for q in self.query_history if q.execution_time > self.slow_query_threshold]
        slow_queries.sort(key=lambda q: q.execution_time, reverse=True)
        return slow_queries[:limit]

    def get_query_stats(self) -> dict[str, Any]:
        """Get comprehensive query performance statistics."""
        if not self.query_history:
            return {"total_queries": 0, "message": "No query history available"}

        total_queries = len(self.query_history)
        total_time = sum(q.execution_time for q in self.query_history)
        avg_time = total_time / total_queries

        # Calculate percentiles
        execution_times = sorted(q.execution_time for q in self.query_history)
        p50 = execution_times[int(total_queries * 0.5)]
        p95 = execution_times[int(total_queries * 0.95)]
        p99 = execution_times[int(total_queries * 0.99)]

        slow_queries = len([q for q in self.query_history if q.execution_time > self.slow_query_threshold])

        return {
            "total_queries": total_queries,
            "total_execution_time": total_time,
            "average_execution_time": avg_time,
            "p50_execution_time": p50,
            "p95_execution_time": p95,
            "p99_execution_time": p99,
            "slow_queries_count": slow_queries,
            "slow_query_percentage": (slow_queries / total_queries) * 100,
            "queries_per_second": total_queries / max(1, total_time),
        }


class ConnectionPoolOptimizer:
    """Database connection pool optimization and monitoring."""

    def __init__(self, min_pool_size: int = 5, max_pool_size: int = 20, optimal_utilization: float = 0.8):
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.optimal_utilization = optimal_utilization
        self.pool_history: list[ConnectionPoolMetrics] = []
        self.max_history_size = 500

    def record_pool_metrics(self, metrics: ConnectionPoolMetrics) -> None:
        """Record connection pool metrics."""
        self.pool_history.append(metrics)

        # Keep history size manageable
        if len(self.pool_history) > self.max_history_size:
            self.pool_history = self.pool_history[-self.max_history_size :]

    def get_pool_recommendations(self) -> list[str]:
        """Get recommendations for connection pool optimization."""
        if not self.pool_history:
            return ["No pool metrics available for analysis"]

        recommendations = []
        latest = self.pool_history[-1]

        # Analyze utilization
        utilization = latest.utilization_rate

        if utilization > HIGH_UTILIZATION_THRESHOLD:
            recommendations.append(
                f"Critical: Pool utilization at {utilization:.1f}% - consider increasing max_pool_size from {latest.pool_size}"
            )
        elif utilization > WARNING_UTILIZATION_THRESHOLD:
            recommendations.append(f"Warning: High pool utilization at {utilization:.1f}% - monitor closely")
        elif utilization < LOW_UTILIZATION_THRESHOLD:
            recommendations.append(
                f"Info: Low pool utilization at {utilization:.1f}% - consider reducing min_pool_size from {self.min_pool_size}"
            )

        # Analyze waiting clients
        if latest.waiting_clients > WAITING_CLIENTS_THRESHOLD:
            recommendations.append(
                f"Warning: {latest.waiting_clients} clients waiting for connections - increase pool size"
            )

        # Analyze connection churn
        if len(self.pool_history) > MIN_HISTORY_FOR_ANALYSIS:
            recent = self.pool_history[-10:]
            avg_created = sum(m.total_connections_created for m in recent) / len(recent)
            avg_destroyed = sum(m.connections_destroyed for m in recent) / len(recent)

            if avg_created > avg_destroyed * 2:
                recommendations.append("High connection churn detected - review connection lifecycle management")

        return recommendations

    def calculate_optimal_pool_size(self) -> int:
        """Calculate optimal pool size based on historical usage."""
        if not self.pool_history:
            return self.min_pool_size

        # Analyze peak usage patterns
        peak_usage = max(m.active_connections for m in self.pool_history)
        avg_usage = sum(m.active_connections for m in self.pool_history) / len(self.pool_history)

        # Calculate optimal size with 20% buffer
        optimal = int(max(peak_usage, avg_usage) * 1.2)

        # Constrain to configured limits
        return max(self.min_pool_size, min(self.max_pool_size, optimal))

    def get_pool_stats(self) -> dict[str, Any]:
        """Get comprehensive connection pool statistics."""
        if not self.pool_history:
            return {"message": "No pool metrics available"}

        latest = self.pool_history[-1]

        return {
            "current_pool_size": latest.pool_size,
            "active_connections": latest.active_connections,
            "idle_connections": latest.idle_connections,
            "waiting_clients": latest.waiting_clients,
            "utilization_rate": latest.utilization_rate,
            "efficiency_score": latest.efficiency_score,
            "total_connections_created": latest.total_connections_created,
            "connections_destroyed": latest.connections_destroyed,
            "recommended_pool_size": self.calculate_optimal_pool_size(),
            "recommendations": self.get_pool_recommendations(),
        }


class DatabaseOptimizer:
    """Comprehensive database optimization manager."""

    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.pool_optimizer = ConnectionPoolOptimizer()
        self._monitoring_task: asyncio.Task[None] | None = None
        self._shutdown_event = asyncio.Event()

    async def start_monitoring(self, interval_seconds: int = 60) -> None:
        """Start database monitoring."""
        if self._monitoring_task is not None:
            logger.warning("Database monitoring already running")
            return

        self._shutdown_event.clear()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info("Database optimization monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop database monitoring."""
        if self._monitoring_task is None:
            return

        self._shutdown_event.set()
        await self._monitoring_task
        self._monitoring_task = None
        logger.info("Database optimization monitoring stopped")

    async def _monitoring_loop(self, interval_seconds: int) -> None:
        """Main monitoring loop for database optimization."""
        while not self._shutdown_event.is_set():
            try:
                # Analyze query performance
                query_stats = self.query_optimizer.get_query_stats()
                pool_stats = self.pool_optimizer.get_pool_stats()

                # Log significant findings
                if query_stats.get("slow_queries_count", 0) > 0:
                    logger.info(
                        f"Database monitoring: {query_stats['slow_queries_count']} slow queries detected, "
                        f"P95: {query_stats.get('p95_execution_time', 0):.2f}s"
                    )

                pool_utilization = pool_stats.get("utilization_rate", 0)
                if pool_utilization > MONITORING_HIGH_UTILIZATION:
                    logger.warning(f"Database monitoring: High connection pool utilization: {pool_utilization:.1f}%")

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Database monitoring error: {e}")
                await asyncio.sleep(interval_seconds)

    def get_optimization_report(self) -> dict[str, Any]:
        """Get comprehensive database optimization report."""
        return {
            "query_performance": self.query_optimizer.get_query_stats(),
            "connection_pool": self.pool_optimizer.get_pool_stats(),
            "slow_queries": [
                {
                    "query": q.query[:QUERY_PREVIEW_LENGTH] + "..." if len(q.query) > QUERY_PREVIEW_LENGTH else q.query,
                    "execution_time": q.execution_time,
                    "rows_affected": q.rows_affected,
                    "timestamp": q.timestamp,
                }
                for q in self.query_optimizer.get_slow_queries(5)
            ],
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate database optimization recommendations."""
        recommendations = []

        # Query optimization recommendations
        query_stats = self.query_optimizer.get_query_stats()
        if query_stats.get("slow_queries_count", 0) > 0:
            slow_percentage = query_stats.get("slow_query_percentage", 0)
            recommendations.append(
                f"Optimize slow queries: {slow_percentage:.1f}% of queries exceed {self.query_optimizer.slow_query_threshold}s threshold"
            )

        # Connection pool recommendations
        pool_recommendations = self.pool_optimizer.get_pool_recommendations()
        recommendations.extend(pool_recommendations)

        # General recommendations
        if not recommendations:
            recommendations.append("Database performance is optimal - no immediate optimizations needed")

        return recommendations


class DatabaseOptimizerManager:
    """Manager for database optimizer instances."""

    _instance: DatabaseOptimizer | None = None

    @classmethod
    def get_optimizer(cls) -> DatabaseOptimizer:
        """Get or create database optimizer instance."""
        if cls._instance is None:
            cls._instance = DatabaseOptimizer()
        return cls._instance


def get_database_optimizer() -> DatabaseOptimizer:
    """Get or create global database optimizer instance."""
    return DatabaseOptimizerManager.get_optimizer()


async def start_database_monitoring(interval_seconds: int = 60) -> None:
    """Start global database monitoring."""
    optimizer = DatabaseOptimizerManager.get_optimizer()
    await optimizer.start_monitoring(interval_seconds)


async def stop_database_monitoring() -> None:
    """Stop global database monitoring."""
    optimizer = DatabaseOptimizerManager.get_optimizer()
    await optimizer.stop_monitoring()


def get_database_optimization_report() -> dict[str, Any]:
    """Get global database optimization report."""
    optimizer = DatabaseOptimizerManager.get_optimizer()
    return optimizer.get_optimization_report()
