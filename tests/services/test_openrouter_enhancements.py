"""Comprehensive tests for OpenRouter service enhancements.

This module tests all the new components from Phases 2-4 including
facade pattern, registry, performance optimizations, and advanced features.
"""

import asyncio
import time
from platform.core.step_result import StepResult
from platform.llm.providers.openrouter.async_execution import AsyncExecutor, AsyncRouteManager
from platform.llm.providers.openrouter.batcher import BatchConfig, RequestBatcher
from platform.llm.providers.openrouter.cache_warmer import CacheCompressor, CacheWarmer, EnhancedCacheManager
from platform.llm.providers.openrouter.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from platform.llm.providers.openrouter.connection_pool import ConnectionPool, MockConnectionPool
from platform.llm.providers.openrouter.facade import (
    BudgetManager,
    CacheManager,
    MetricsCollector,
    OpenRouterServiceFacade,
)
from platform.llm.providers.openrouter.health import HealthChecker, HealthEndpoint
from platform.llm.providers.openrouter.monitoring import AlertManager, AlertThreshold, PerformanceMonitor
from platform.llm.providers.openrouter.monitoring import MetricsCollector as MonitoringMetricsCollector
from platform.llm.providers.openrouter.object_pool import ObjectPool, RouteStatePool
from platform.llm.providers.openrouter.rate_limiter import (
    OpenRouterRateLimiter,
    RateLimitConfig,
    RateLimitManager,
    SlidingWindowRateLimiter,
    TenantRateLimiter,
    TokenBucket,
)
from platform.llm.providers.openrouter.registry import OpenRouterServiceRegistry, ServiceRegistry
from platform.llm.providers.openrouter.retry_strategy import RetryConfig, RetryManager, RetryStrategy
from unittest.mock import Mock, patch

import pytest


class TestFacadePattern:
    """Test the unified service facade pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.cache = Mock()
        self.mock_service.cache.make_key.return_value = "test_key"
        self.mock_service.cache.get.return_value = None
        self.mock_service.cache.set.return_value = None
        self.mock_service.prompt_engine = Mock()
        self.mock_service.prompt_engine.count_tokens.return_value = 10
        self.mock_service.token_meter = Mock()
        self.mock_service.token_meter.estimate_cost.return_value = 0.01
        self.mock_service.request_tracker = Mock()
        self.mock_service.request_tracker.can_charge.return_value = True
        self.mock_service.route.return_value = StepResult.ok(data={"response": "test"})
        self.facade = OpenRouterServiceFacade(self.mock_service)

    def test_facade_initialization(self):
        """Test facade initialization."""
        assert self.facade.service == self.mock_service
        assert isinstance(self.facade.cache_manager, CacheManager)
        assert isinstance(self.facade.budget_manager, BudgetManager)
        assert isinstance(self.facade.metrics_collector, MetricsCollector)

    def test_facade_route_success(self):
        """Test successful routing through facade."""
        result = self.facade.route("test prompt", "general")
        assert result.success
        assert result.data["response"] == "test"
        self.mock_service.route.assert_called_once()

    def test_facade_route_with_cache_hit(self):
        """Test routing with cache hit."""
        cached_response = {"response": "cached"}
        self.mock_service.cache.get.return_value = cached_response
        result = self.facade.route("test prompt", "general")
        assert result.success
        assert result.data == cached_response
        self.mock_service.route.assert_not_called()

    def test_facade_health_check(self):
        """Test facade health check."""
        result = self.facade.health_check()
        assert result.success
        assert result.data["status"] == "healthy"

    def test_metrics_collector(self):
        """Test metrics collection."""
        collector = MetricsCollector()
        collector.record_request(100.0, 50, True)
        collector.record_request(200.0, 100, False)
        stats = collector.get_stats()
        assert stats["request_count"] == 2
        assert stats["total_latency_ms"] == 300.0
        assert stats["total_tokens"] == 150


class TestServiceRegistry:
    """Test the service registry pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        ServiceRegistry.clear()

    def teardown_method(self):
        """Clean up after tests."""
        ServiceRegistry.clear()

    def test_register_and_get_service(self):
        """Test service registration and retrieval."""
        mock_service = Mock()
        ServiceRegistry.register("test_service", mock_service)
        retrieved = ServiceRegistry.get("test_service")
        assert retrieved == mock_service

    def test_register_factory(self):
        """Test service factory registration."""

        def factory():
            return Mock()

        ServiceRegistry.register_factory("factory_service", factory)
        service = ServiceRegistry.get("factory_service")
        assert service is not None
        assert "factory_service" in ServiceRegistry.list_services()

    def test_get_or_create(self):
        """Test get or create functionality."""

        def factory():
            return "created_service"

        service = ServiceRegistry.get_or_create("new_service", factory)
        assert service == "created_service"
        service2 = ServiceRegistry.get_or_create("new_service", factory)
        assert service2 == service

    def test_openrouter_registry(self):
        """Test OpenRouter-specific registry."""
        mock_service = Mock()
        OpenRouterServiceRegistry.register_openrouter_service(mock_service)
        retrieved_service = OpenRouterServiceRegistry.get_openrouter_service()
        retrieved_facade = OpenRouterServiceRegistry.get_openrouter_facade()
        assert retrieved_service == mock_service
        assert retrieved_facade is not None

    def test_health_check(self):
        """Test registry health check."""
        result = OpenRouterServiceRegistry.health_check()
        assert not result.success


class TestConnectionPool:
    """Test HTTP connection pooling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pool = ConnectionPool(pool_size=5, max_retries=2)

    def teardown_method(self):
        """Clean up after tests."""
        self.pool.close()

    @patch("requests.Session")
    def test_connection_pool_creation(self, mock_session):
        """Test connection pool creation."""
        session = self.pool.get_session()
        assert session is not None

    @patch("requests.Session")
    def test_post_request(self, mock_session):
        """Test POST request through connection pool."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.post.return_value = mock_response
        response = self.pool.post("http://test.com", json={"test": "data"})
        assert response == mock_response

    def test_mock_connection_pool(self):
        """Test mock connection pool."""
        mock_pool = MockConnectionPool()
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            response = mock_pool.post("http://test.com", json={"test": "data"})
            assert response == mock_response

    def test_connection_pool_stats(self):
        """Test connection pool statistics."""
        stats = self.pool.get_stats()
        assert "total_requests" in stats
        assert "success_rate_percent" in stats
        assert "pool_size" in stats


class TestAsyncExecution:
    """Test async execution capabilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.api_key = "test_key"
        self.mock_service.prompt_engine = Mock()
        self.mock_service.prompt_engine.count_tokens.return_value = 10
        self.mock_service.get_settings.return_value = Mock()
        self.mock_service.learning = Mock()
        self.mock_service.learning.update.return_value = None
        self.async_executor = AsyncExecutor(self.mock_service)

    @pytest.mark.asyncio
    async def test_async_executor_initialization(self):
        """Test async executor initialization."""
        assert self.async_executor._service == self.mock_service

    @pytest.mark.asyncio
    async def test_async_route_manager(self):
        """Test async route manager."""
        route_manager = AsyncRouteManager(self.mock_service)
        self.mock_service.route.return_value = StepResult.ok(data={"response": "test"})
        result = await route_manager.route_async("test prompt")
        assert result["status"] == "success"
        assert result["response"] == "test"

    @pytest.mark.asyncio
    async def test_async_executor_close(self):
        """Test async executor cleanup."""
        await self.async_executor.close()


class TestCacheWarmer:
    """Test cache warming and compression."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.cache = Mock()
        self.mock_service.route.return_value = StepResult.ok(data={"response": "test"})
        self.cache_warmer = CacheWarmer(self.mock_service)

    def test_cache_compressor(self):
        """Test cache compression functionality."""
        compressor = CacheCompressor()
        data = {"test": "data", "number": 123}
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        compressor = CacheCompressor()
        data = {"test": "data" * 100}
        compressed = compressor.compress(data)
        ratio = compressor.get_compression_ratio(data, compressed)
        assert 0 <= ratio <= 1

    @pytest.mark.asyncio
    async def test_cache_warming(self):
        """Test cache warming functionality."""
        with patch.object(self.cache_warmer, "_feature_flags") as mock_flags:
            mock_flags.ENABLE_OPENROUTER_ADVANCED_CACHING = True
            result = await self.cache_warmer.warm_cache()
            assert result.success
            assert result.data["prompts_warmed"] > 0

    def test_enhanced_cache_manager(self):
        """Test enhanced cache manager."""
        cache_manager = EnhancedCacheManager(self.mock_service)
        cached_data = cache_manager.get_cached_response("test", "model")
        assert cached_data is None
        test_data = {"response": "test"}
        cache_manager.set_cached_response("test", "model", test_data)


class TestRequestBatcher:
    """Test request batching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.route.return_value = StepResult.ok(data={"response": "test"})
        config = BatchConfig(batch_size=2, wait_time_ms=10)
        self.batcher = RequestBatcher(self.mock_service, config)

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing."""
        with patch.object(self.batcher, "_feature_flags") as mock_flags:
            mock_flags.ENABLE_OPENROUTER_REQUEST_BATCHING = True
            futures = []
            for i in range(3):
                future = asyncio.create_task(self.batcher.add_request(f"prompt {i}", "general"))
                futures.append(future)
            results = await asyncio.gather(*futures)
            assert len(results) == 3
            for result in results:
                assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_batch_config(self):
        """Test batch configuration."""
        config = BatchConfig(batch_size=5, wait_time_ms=100, max_wait_time_ms=500, enable_batching=True)
        assert config.batch_size == 5
        assert config.wait_time_ms == 100
        assert config.max_wait_time_ms == 500
        assert config.enable_batching is True

    def test_batcher_stats(self):
        """Test batcher statistics."""
        stats = self.batcher.get_stats()
        assert "total_requests" in stats
        assert "batched_requests" in stats
        assert "individual_requests" in stats
        assert "config" in stats


class TestObjectPool:
    """Test object pooling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.pool = ObjectPool(factory=lambda: {"id": 1, "data": "test"}, max_size=5)

    def test_object_pool_basic_operations(self):
        """Test basic object pool operations."""
        obj1 = self.pool.get()
        assert obj1["id"] == 1
        self.pool.put(obj1)
        obj2 = self.pool.get()
        assert obj2["id"] == 1

    def test_object_pool_with_reset(self):
        """Test object pool with reset function."""

        def reset_func(obj):
            obj["data"] = "reset"

        pool = ObjectPool(factory=lambda: {"id": 1, "data": "original"}, max_size=5, reset_func=reset_func)
        obj = pool.get()
        obj["data"] = "modified"
        pool.put(obj)
        obj2 = pool.get()
        assert obj2["data"] == "reset"

    def test_route_state_pool(self):
        """Test RouteState object pool."""
        with patch(
            "ultimate_discord_intelligence_bot.services.openrouter_service.object_pool.FeatureFlags"
        ) as mock_flags:
            mock_flags.return_value.ENABLE_OPENROUTER_OBJECT_POOLING = True
            pool = RouteStatePool()
            state = pool.get_route_state()
            assert state is not None
            pool.return_route_state(state)

    def test_object_pool_stats(self):
        """Test object pool statistics."""
        obj = self.pool.get()
        self.pool.put(obj)
        stats = self.pool.get_stats()
        assert "objects_created" in stats
        assert "objects_reused" in stats
        assert "reuse_rate_percent" in stats


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1, success_threshold=1)
        self.breaker = CircuitBreaker("test_breaker", self.config)

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker initial state."""
        assert self.breaker.get_state() == CircuitState.CLOSED

    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful operations."""

        def success_func():
            return "success"

        result = self.breaker.execute(success_func)
        assert result == "success"
        assert self.breaker.get_state() == CircuitState.CLOSED

    def test_circuit_breaker_failure_and_open(self):
        """Test circuit breaker opening after failures."""

        def fail_func():
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            self.breaker.execute(fail_func)
        assert self.breaker.get_state() == CircuitState.CLOSED
        with pytest.raises(ConnectionError):
            self.breaker.execute(fail_func)
        assert self.breaker.get_state() == CircuitState.OPEN

    def test_circuit_breaker_blocked_requests(self):
        """Test that circuit breaker blocks requests when open."""

        def fail_func():
            raise ConnectionError("Connection failed")

        for _ in range(3):
            try:
                self.breaker.execute(fail_func)
            except ConnectionError:
                pass
        assert self.breaker.get_state() == CircuitState.OPEN
        with pytest.raises(Exception):
            self.breaker.execute(fail_func)

    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Test async circuit breaker."""

        async def async_success_func():
            return "async_success"

        result = await self.breaker.execute_async(async_success_func)
        assert result == "async_success"

    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics."""
        stats = self.breaker.get_stats()
        assert "total_requests" in stats
        assert "state" in stats
        assert "failure_count" in stats
        assert "success_count" in stats


class TestMonitoring:
    """Test monitoring and alerting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.monitor = PerformanceMonitor(self.mock_service)

    def test_metrics_collector(self):
        """Test metrics collection."""
        collector = MonitoringMetricsCollector()
        collector.record_request(100.0, 50, True)
        collector.record_request(200.0, 100, False)
        metrics = collector.get_current_metrics()
        assert metrics.latency_p50 > 0
        assert metrics.throughput_rps > 0
        assert metrics.error_rate > 0

    def test_alert_manager(self):
        """Test alert management."""
        alert_manager = AlertManager()
        from platform.llm.providers.openrouter.monitoring import PerformanceMetrics

        metrics = PerformanceMetrics(
            timestamp=time.time(),
            latency_p50=100.0,
            latency_p95=5000.0,
            latency_p99=10000.0,
            throughput_rps=1.0,
            error_rate=15.0,
            cache_hit_rate=80.0,
            memory_usage_mb=100.0,
            cpu_usage_percent=50.0,
        )
        alerts = alert_manager.check_alerts(metrics)
        assert len(alerts) > 0

    def test_alert_threshold(self):
        """Test alert threshold configuration."""
        threshold = AlertThreshold(metric_name="error_rate", threshold_value=10.0, comparison="gt", severity="high")
        assert threshold.metric_name == "error_rate"
        assert threshold.threshold_value == 10.0
        assert threshold.comparison == "gt"
        assert threshold.severity == "high"

    def test_performance_monitor(self):
        """Test performance monitor."""
        self.monitor.record_request_metrics(100.0, 50, 0.01, True, False)
        dashboard = self.monitor.get_performance_dashboard()
        assert "current_metrics" in dashboard
        assert "recent_alerts" in dashboard
        assert "alert_thresholds" in dashboard


class TestHealthChecks:
    """Test health check functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.api_key = "test_key"
        self.mock_service.models_map = {"test": ["model1"]}
        self.mock_service.prompt_engine = Mock()
        self.mock_service.token_meter = Mock()
        self.mock_service.offline_mode = False
        self.mock_service.route.return_value = StepResult.ok(data={"status": "success"})
        self.health_checker = HealthChecker(self.mock_service)

    @pytest.mark.asyncio
    async def test_health_checker_initialization(self):
        """Test health checker initialization."""
        assert self.health_checker._service == self.mock_service

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self):
        """Test comprehensive health check."""
        with patch.object(self.health_checker, "_feature_flags") as mock_flags:
            mock_flags.ENABLE_OPENROUTER_HEALTH_CHECKS = True
            health_status = await self.health_checker.check_health()
            assert "status" in health_status
            assert "timestamp" in health_status
            assert "checks" in health_status
            assert "overall_healthy" in health_status

    def test_quick_health_check(self):
        """Test quick health check."""
        health_status = self.health_checker.get_quick_health()
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "basic_checks_passed" in health_status

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health endpoint."""
        endpoint = HealthEndpoint(self.mock_service)
        with patch.object(endpoint, "_feature_flags") as mock_flags:
            mock_flags.ENABLE_OPENROUTER_HEALTH_CHECKS = True
            health_result = await endpoint.health_check(detailed=True)
            assert "status" in health_result
            readiness_result = await endpoint.readiness_check()
            assert "ready" in readiness_result
            liveness_result = await endpoint.liveness_check()
            assert "alive" in liveness_result


class TestRetryStrategy:
    """Test retry strategy functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RetryConfig(max_retries=2, base_delay=0.1, max_delay=1.0, exponential_base=2.0, jitter=True)
        self.retry_strategy = RetryStrategy(self.config)

    def test_retry_strategy_success(self):
        """Test retry strategy with successful operation."""

        def success_func():
            return "success"

        result = self.retry_strategy.execute_with_retry(success_func)
        assert result == "success"

    def test_retry_strategy_with_retries(self):
        """Test retry strategy with retries."""
        call_count = 0

        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = self.retry_strategy.execute_with_retry(fail_then_succeed)
        assert result == "success"
        assert call_count == 3

    def test_retry_strategy_max_retries_exceeded(self):
        """Test retry strategy when max retries exceeded."""

        def always_fail():
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            self.retry_strategy.execute_with_retry(always_fail)

    @pytest.mark.asyncio
    async def test_async_retry_strategy(self):
        """Test async retry strategy."""

        async def async_success_func():
            return "async_success"

        result = await self.retry_strategy.execute_async_with_retry(async_success_func)
        assert result == "async_success"

    def test_retry_strategy_stats(self):
        """Test retry strategy statistics."""
        stats = self.retry_strategy.get_stats()
        assert "total_attempts" in stats
        assert "successful_attempts" in stats
        assert "failed_attempts" in stats
        assert "retries_performed" in stats

    def test_retry_manager(self):
        """Test retry manager."""
        manager = RetryManager()
        strategy = manager.get_strategy("test_strategy")
        assert isinstance(strategy, RetryStrategy)
        all_stats = manager.get_all_stats()
        assert "test_strategy" in all_stats


class TestRateLimiter:
    """Test rate limiting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            requests_per_minute=10, requests_per_hour=100, requests_per_day=1000, burst_limit=5
        )

    def test_token_bucket(self):
        """Test token bucket implementation."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume(5) is True
        assert bucket.get_tokens() == 5
        assert bucket.consume(10) is False

    def test_sliding_window_rate_limiter(self):
        """Test sliding window rate limiter."""
        limiter = SlidingWindowRateLimiter(window_size_seconds=60)
        assert limiter.is_allowed(5) is True
        assert limiter.is_allowed(5) is True
        for _ in range(5):
            limiter.is_allowed(5)
        assert limiter.is_allowed(5) is False

    def test_tenant_rate_limiter(self):
        """Test tenant rate limiter."""
        limiter = TenantRateLimiter(self.config)
        assert limiter.is_allowed() is True
        status = limiter.get_status()
        assert "tokens_available" in status
        assert "bucket_capacity" in status
        assert "stats" in status

    def test_rate_limit_manager(self):
        """Test rate limit manager."""
        manager = RateLimitManager()
        assert manager.is_request_allowed("tenant1") is True
        status = manager.get_tenant_status("tenant1")
        assert "tenant" in status
        assert "limiter_exists" in status

    def test_openrouter_rate_limiter(self):
        """Test OpenRouter rate limiter wrapper."""
        mock_service = Mock()
        rate_limiter = OpenRouterRateLimiter(mock_service)
        result = rate_limiter.route_with_rate_limit("test prompt", tenant="test_tenant")
        assert result.success or "rate_limited" in str(result.error)


class TestIntegration:
    """Integration tests for enhanced OpenRouter service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock()
        self.mock_service.api_key = "test_key"
        self.mock_service.models_map = {"test": ["model1"]}
        self.mock_service.prompt_engine = Mock()
        self.mock_service.token_meter = Mock()
        self.mock_service.route.return_value = StepResult.ok(data={"response": "test"})

    def test_facade_with_registry(self):
        """Test facade integration with service registry."""
        OpenRouterServiceRegistry.register_openrouter_service(self.mock_service)
        facade = OpenRouterServiceRegistry.get_openrouter_facade()
        assert facade is not None
        result = facade.route("test prompt")
        assert result.success

    @pytest.mark.asyncio
    async def test_async_with_circuit_breaker(self):
        """Test async execution with circuit breaker."""
        from platform.llm.providers.openrouter.circuit_breaker import get_openrouter_circuit_breaker

        circuit_breaker = get_openrouter_circuit_breaker(self.mock_service)
        with patch.object(circuit_breaker, "_feature_flags") as mock_flags:
            mock_flags.ENABLE_OPENROUTER_CIRCUIT_BREAKER = True
            result = await circuit_breaker.route_async_with_circuit_breaker("test prompt")
            assert result["status"] == "success"

    def test_monitoring_with_health_checks(self):
        """Test monitoring integration with health checks."""
        from platform.llm.providers.openrouter.health import get_health_endpoint
        from platform.llm.providers.openrouter.monitoring import get_performance_monitor

        monitor = get_performance_monitor(self.mock_service)
        health_endpoint = get_health_endpoint(self.mock_service)
        monitor.record_request_metrics(100.0, 50, 0.01, True, False)
        dashboard = monitor.get_performance_dashboard()
        assert "current_metrics" in dashboard
        health_status = health_endpoint._health_checker.get_quick_health()
        assert "status" in health_status

    def test_retry_with_rate_limiting(self):
        """Test retry strategy with rate limiting."""
        from platform.llm.providers.openrouter.rate_limiter import get_openrouter_rate_limiter
        from platform.llm.providers.openrouter.retry_strategy import get_openrouter_retry_wrapper

        retry_wrapper = get_openrouter_retry_wrapper(self.mock_service)
        rate_limiter = get_openrouter_rate_limiter(self.mock_service)
        result = retry_wrapper.route_with_retry("test prompt")
        assert result.success
        result = rate_limiter.route_with_rate_limit("test prompt", tenant="test_tenant")
        assert result.success or "rate_limited" in str(result.error)


if __name__ == "__main__":
    pytest.main([__file__])
