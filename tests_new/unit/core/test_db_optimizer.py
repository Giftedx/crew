"""Tests for database optimization utilities."""

import asyncio

import pytest

from ultimate_discord_intelligence_bot.core.db_optimizer import (
    ConnectionPoolMetrics,
    ConnectionPoolOptimizer,
    DatabaseOptimizer,
    DatabaseOptimizerManager,
    QueryMetrics,
    QueryOptimizer,
    get_database_optimization_report,
    get_database_optimizer,
)


class TestQueryMetrics:
    """Test QueryMetrics dataclass."""

    def test_creation(self):
        """Test QueryMetrics creation with default timestamp."""
        metrics = QueryMetrics(
            query="SELECT * FROM users",
            execution_time=0.5,
            rows_affected=10,
            connection_id="conn_123",
        )

        assert metrics.query == "SELECT * FROM users"
        assert metrics.execution_time == 0.5
        assert metrics.rows_affected == 10
        assert metrics.connection_id == "conn_123"
        assert isinstance(metrics.timestamp, float)
        assert metrics.timestamp > 0

    def test_custom_timestamp(self):
        """Test QueryMetrics with custom timestamp."""
        custom_time = 1234567890.0
        metrics = QueryMetrics(
            query="SELECT * FROM users",
            execution_time=0.5,
            rows_affected=10,
            timestamp=custom_time,
        )

        assert metrics.timestamp == custom_time


class TestConnectionPoolMetrics:
    """Test ConnectionPoolMetrics dataclass."""

    def test_creation(self):
        """Test ConnectionPoolMetrics creation."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=7,
            idle_connections=3,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        assert metrics.pool_size == 10
        assert metrics.active_connections == 7
        assert metrics.idle_connections == 3
        assert metrics.waiting_clients == 0
        assert metrics.total_connections_created == 15
        assert metrics.connections_destroyed == 5
        assert isinstance(metrics.timestamp, float)

    def test_utilization_rate(self):
        """Test utilization rate calculation."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=7,
            idle_connections=3,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        assert metrics.utilization_rate == 70.0

    def test_efficiency_score_optimal(self):
        """Test efficiency score for optimal utilization."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=8,  # 80% utilization
            idle_connections=2,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        assert metrics.efficiency_score == 1.0

    def test_efficiency_score_under_utilized(self):
        """Test efficiency score for under-utilized pool."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=5,  # 50% utilization
            idle_connections=5,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        assert metrics.efficiency_score == 0.8

    def test_efficiency_score_over_utilized(self):
        """Test efficiency score for over-utilized pool."""
        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=10,  # 100% utilization - over-utilized
            idle_connections=0,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        assert metrics.efficiency_score < 1.0


class TestQueryOptimizer:
    """Test QueryOptimizer class."""

    def test_initialization(self):
        """Test QueryOptimizer initialization."""
        optimizer = QueryOptimizer(slow_query_threshold=2.0)

        assert optimizer.slow_query_threshold == 2.0
        assert optimizer.query_history == []
        assert optimizer.max_history_size == 1000

    @pytest.mark.asyncio
    async def test_monitor_query_context_manager(self):
        """Test monitor_query context manager."""
        optimizer = QueryOptimizer()

        async with optimizer.monitor_query("SELECT * FROM users", "conn_123") as record_metrics:
            # Simulate some work
            await asyncio.sleep(0.01)
            record_metrics()  # Record metrics with default values

        assert len(optimizer.query_history) == 1
        metrics = optimizer.query_history[0]
        assert metrics.query == "SELECT * FROM users"
        assert metrics.connection_id == "conn_123"
        assert metrics.rows_affected == 5
        assert metrics.execution_time >= 0.01

    def test_get_slow_queries(self):
        """Test get_slow_queries method."""
        optimizer = QueryOptimizer(slow_query_threshold=0.1)

        # Add some queries
        optimizer.query_history = [
            QueryMetrics("FAST QUERY", 0.05, 1),
            QueryMetrics("SLOW QUERY 1", 0.2, 5),
            QueryMetrics("SLOW QUERY 2", 0.3, 10),
            QueryMetrics("FAST QUERY 2", 0.08, 2),
        ]

        slow_queries = optimizer.get_slow_queries(limit=2)
        assert len(slow_queries) == 2
        assert slow_queries[0].execution_time == 0.3
        assert slow_queries[1].execution_time == 0.2

    def test_get_query_stats_no_history(self):
        """Test get_query_stats with no history."""
        optimizer = QueryOptimizer()

        stats = optimizer.get_query_stats()
        assert stats["total_queries"] == 0
        assert "No query history available" in stats["message"]

    def test_get_query_stats_with_history(self):
        """Test get_query_stats with query history."""
        optimizer = QueryOptimizer(slow_query_threshold=0.15)

        optimizer.query_history = [
            QueryMetrics("QUERY 1", 0.1, 1, timestamp=1000.0),
            QueryMetrics("QUERY 2", 0.2, 5, timestamp=1001.0),
            QueryMetrics("QUERY 3", 0.05, 2, timestamp=1002.0),
        ]

        stats = optimizer.get_query_stats()
        assert stats["total_queries"] == 3
        assert abs(stats["average_execution_time"] - 0.11666666666666667) < 1e-10
        assert stats["slow_queries_count"] == 1
        # Use abs comparison instead of pytest.approx to avoid numpy 2.0 compatibility issues
        assert abs(stats["slow_query_percentage"] - 33.33) < 0.01


class TestConnectionPoolOptimizer:
    """Test ConnectionPoolOptimizer class."""

    def test_initialization(self):
        """Test ConnectionPoolOptimizer initialization."""
        optimizer = ConnectionPoolOptimizer(min_pool_size=5, max_pool_size=20, optimal_utilization=0.8)

        assert optimizer.min_pool_size == 5
        assert optimizer.max_pool_size == 20
        assert optimizer.optimal_utilization == 0.8
        assert optimizer.pool_history == []

    def test_record_pool_metrics(self):
        """Test recording pool metrics."""
        optimizer = ConnectionPoolOptimizer()

        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=7,
            idle_connections=3,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        optimizer.record_pool_metrics(metrics)

        assert len(optimizer.pool_history) == 1
        assert optimizer.pool_history[0] == metrics

    def test_get_pool_recommendations_no_history(self):
        """Test get_pool_recommendations with no history."""
        optimizer = ConnectionPoolOptimizer()

        recommendations = optimizer.get_pool_recommendations()
        assert len(recommendations) == 1
        assert "No pool metrics available" in recommendations[0]

    def test_get_pool_recommendations_high_utilization(self):
        """Test recommendations for high utilization."""
        optimizer = ConnectionPoolOptimizer()

        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=9,  # 90% utilization
            idle_connections=1,
            waiting_clients=0,
            total_connections_created=15,
            connections_destroyed=5,
        )

        optimizer.record_pool_metrics(metrics)
        recommendations = optimizer.get_pool_recommendations()

        assert any("High pool utilization" in rec for rec in recommendations)

    def test_calculate_optimal_pool_size_no_history(self):
        """Test calculate_optimal_pool_size with no history."""
        optimizer = ConnectionPoolOptimizer(min_pool_size=5)

        optimal_size = optimizer.calculate_optimal_pool_size()
        assert optimal_size == 5

    def test_calculate_optimal_pool_size_with_history(self):
        """Test calculate_optimal_pool_size with history."""
        optimizer = ConnectionPoolOptimizer(min_pool_size=5, max_pool_size=20)

        # Add some metrics
        optimizer.pool_history = [
            ConnectionPoolMetrics(10, 8, 2, 0, 15, 5),
            ConnectionPoolMetrics(10, 6, 4, 0, 16, 6),
            ConnectionPoolMetrics(10, 9, 1, 0, 17, 7),
        ]

        optimal_size = optimizer.calculate_optimal_pool_size()
        # Should be max(peak=9, avg=7.67) * 1.2 = ~10.4, capped at max_pool_size
        assert optimal_size == 10

    def test_get_pool_stats_no_history(self):
        """Test get_pool_stats with no history."""
        optimizer = ConnectionPoolOptimizer()

        stats = optimizer.get_pool_stats()
        assert "No pool metrics available" in stats["message"]

    def test_get_pool_stats_with_history(self):
        """Test get_pool_stats with history."""
        optimizer = ConnectionPoolOptimizer()

        metrics = ConnectionPoolMetrics(
            pool_size=10,
            active_connections=7,
            idle_connections=3,
            waiting_clients=2,
            total_connections_created=15,
            connections_destroyed=5,
        )

        optimizer.record_pool_metrics(metrics)
        stats = optimizer.get_pool_stats()

        assert stats["current_pool_size"] == 10
        assert stats["active_connections"] == 7
        assert stats["utilization_rate"] == 70.0
        assert stats["recommended_pool_size"] == 8  # max(7, 7) * 1.2 = 8.4 -> 8


class TestDatabaseOptimizer:
    """Test DatabaseOptimizer class."""

    def test_initialization(self):
        """Test DatabaseOptimizer initialization."""
        optimizer = DatabaseOptimizer()

        assert isinstance(optimizer.query_optimizer, QueryOptimizer)
        assert isinstance(optimizer.pool_optimizer, ConnectionPoolOptimizer)
        assert optimizer._monitoring_task is None
        assert not optimizer._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        optimizer = DatabaseOptimizer()

        # Start monitoring
        await optimizer.start_monitoring(interval_seconds=1)

        assert optimizer._monitoring_task is not None
        assert not optimizer._shutdown_event.is_set()

        # Stop monitoring
        await optimizer.stop_monitoring()

        assert optimizer._monitoring_task is None
        assert optimizer._shutdown_event.is_set()

    def test_get_optimization_report(self):
        """Test get_optimization_report method."""
        optimizer = DatabaseOptimizer()

        # Add some test data
        optimizer.query_optimizer.query_history = [
            QueryMetrics("SELECT * FROM users", 0.1, 5),
        ]

        optimizer.pool_optimizer.record_pool_metrics(ConnectionPoolMetrics(10, 7, 3, 0, 15, 5))

        report = optimizer.get_optimization_report()

        assert "query_performance" in report
        assert "connection_pool" in report
        assert "slow_queries" in report
        assert "recommendations" in report

        assert report["query_performance"]["total_queries"] == 1
        assert report["connection_pool"]["current_pool_size"] == 10


class TestDatabaseOptimizerManager:
    """Test DatabaseOptimizerManager class."""

    def test_get_optimizer_singleton(self):
        """Test that get_optimizer returns singleton instance."""
        optimizer1 = DatabaseOptimizerManager.get_optimizer()
        optimizer2 = DatabaseOptimizerManager.get_optimizer()

        assert optimizer1 is optimizer2
        assert isinstance(optimizer1, DatabaseOptimizer)


class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_database_optimizer(self):
        """Test get_database_optimizer function."""
        optimizer = get_database_optimizer()
        assert isinstance(optimizer, DatabaseOptimizer)

    def test_get_database_optimization_report(self):
        """Test get_database_optimization_report function."""
        report = get_database_optimization_report()
        assert isinstance(report, dict)
        assert "query_performance" in report
        assert "connection_pool" in report
        assert "slow_queries" in report
        assert "recommendations" in report


if __name__ == "__main__":
    pytest.main([__file__])
