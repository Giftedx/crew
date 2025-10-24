"""
Test suite for the canonical circuit breaker implementation.

This module tests all aspects of the consolidated circuit breaker functionality,
including failure detection, recovery, metrics, and platform API integration.
"""

import asyncio

import pytest

from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import (
    PLATFORM_CONFIGS,
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitConfig,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker_registry,
    get_platform_circuit_breaker,
    with_circuit_breaker,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestCircuitConfig:
    """Test circuit breaker configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CircuitConfig()

        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60.0
        assert config.success_threshold == 3
        assert config.call_timeout == 30.0
        assert config.failure_rate_threshold == 0.5
        assert config.minimum_requests == 10
        assert config.sliding_window_size == 100
        assert config.max_concurrent_calls == 10
        assert config.half_open_max_calls == 3
        assert config.enable_metrics is True
        assert config.log_failures is True
        assert config.log_state_changes is True
        assert config.expected_exceptions == (Exception,)

    def test_custom_config(self):
        """Test custom configuration values."""
        config = CircuitConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            success_threshold=2,
            call_timeout=15.0,
            failure_rate_threshold=0.3,
            minimum_requests=5,
            sliding_window_size=50,
            max_concurrent_calls=5,
            half_open_max_calls=2,
            enable_metrics=False,
            log_failures=False,
            log_state_changes=False,
            expected_exceptions=(ValueError, RuntimeError),
        )

        assert config.failure_threshold == 3
        assert config.recovery_timeout == 30.0
        assert config.success_threshold == 2
        assert config.call_timeout == 15.0
        assert config.failure_rate_threshold == 0.3
        assert config.minimum_requests == 5
        assert config.sliding_window_size == 50
        assert config.max_concurrent_calls == 5
        assert config.half_open_max_calls == 2
        assert config.enable_metrics is False
        assert config.log_failures is False
        assert config.log_state_changes is False
        assert config.expected_exceptions == (ValueError, RuntimeError)


class TestCircuitStats:
    """Test circuit breaker statistics."""

    def test_initial_stats(self):
        """Test initial statistics values."""
        from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import (
            CircuitStats,
        )

        stats = CircuitStats()

        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.timeouts == 0
        assert stats.circuit_open_count == 0
        assert stats.circuit_half_open_count == 0
        assert stats.circuit_closed_count == 0
        assert stats.last_failure_time is None
        assert stats.last_success_time is None
        assert stats.failure_rate == 0.0
        assert stats.success_rate == 0.0

    def test_stats_calculation(self):
        """Test statistics calculation."""
        from ultimate_discord_intelligence_bot.core.circuit_breaker_canonical import (
            CircuitStats,
        )

        stats = CircuitStats()

        # Add some test data
        stats.total_requests = 10
        stats.successful_requests = 7
        stats.failed_requests = 3

        assert stats.failure_rate == 0.3
        assert stats.success_rate == 0.7


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.circuit = CircuitBreaker("test_circuit")
        self.config = CircuitConfig(failure_threshold=2, recovery_timeout=0.1)

    @pytest.mark.asyncio
    async def test_initial_state(self):
        """Test initial circuit breaker state."""
        assert self.circuit.state == CircuitState.CLOSED
        assert self.circuit.name == "test_circuit"
        assert self.circuit.failure_count == 0
        assert self.circuit.success_count == 0

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful function call."""

        async def success_func():
            return "success"

        result = await self.circuit.call(success_func)

        assert result == "success"
        assert self.circuit.state == CircuitState.CLOSED
        assert self.circuit.stats.successful_requests == 1
        assert self.circuit.stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_failed_call(self):
        """Test failed function call."""

        async def fail_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await self.circuit.call(fail_func)

        assert self.circuit.state == CircuitState.CLOSED
        assert self.circuit.stats.failed_requests == 1
        assert self.circuit.stats.total_requests == 1

    @pytest.mark.asyncio
    async def test_circuit_opening(self):
        """Test circuit breaker opening after threshold failures."""
        circuit = CircuitBreaker("test_circuit", CircuitConfig(failure_threshold=2))

        async def fail_func():
            raise ValueError("test error")

        # First failure
        with pytest.raises(ValueError):
            await circuit.call(fail_func)
        assert circuit.state == CircuitState.CLOSED

        # Second failure should open circuit
        with pytest.raises(ValueError):
            await circuit.call(fail_func)
        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_open_error(self):
        """Test circuit breaker open error."""
        circuit = CircuitBreaker("test_circuit", CircuitConfig(failure_threshold=1))

        async def fail_func():
            raise ValueError("test error")

        # Trigger circuit opening
        with pytest.raises(ValueError):
            await circuit.call(fail_func)

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await circuit.call(fail_func)

    @pytest.mark.asyncio
    async def test_fallback_function(self):
        """Test fallback function when circuit is open."""

        async def fail_func():
            raise ValueError("test error")

        async def fallback_func():
            return "fallback"

        circuit = CircuitBreaker("test_circuit", CircuitConfig(failure_threshold=1), fallback_func)

        # Trigger circuit opening
        with pytest.raises(ValueError):
            await circuit.call(fail_func)

        # Next call should use fallback
        result = await circuit.call(fail_func)
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_half_open_recovery(self):
        """Test circuit breaker recovery through half-open state."""
        circuit = CircuitBreaker(
            "test_circuit",
            CircuitConfig(failure_threshold=1, recovery_timeout=0.1, success_threshold=2),
        )

        async def fail_func():
            raise ValueError("test error")

        async def success_func():
            return "success"

        # Trigger circuit opening
        with pytest.raises(ValueError):
            await circuit.call(fail_func)

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # First successful call should transition to half-open
        result = await circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitState.HALF_OPEN

        # Second successful call should close circuit
        result = await circuit.call(success_func)
        assert result == "success"
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        circuit = CircuitBreaker("test_circuit", CircuitConfig(call_timeout=0.1))

        async def slow_func():
            await asyncio.sleep(0.2)
            return "slow"

        with pytest.raises(TimeoutError):
            await circuit.call(slow_func)

        assert circuit.stats.timeouts == 1

    @pytest.mark.asyncio
    async def test_call_with_result(self):
        """Test call_with_result method."""

        async def success_func():
            return StepResult.ok(data="success")

        async def fail_func():
            return StepResult.fail("test error")

        # Successful call
        result = await self.circuit.call_with_result(success_func)
        assert result.success
        assert result.data["data"] == "success"

        # Failed call
        result = await self.circuit.call_with_result(fail_func)
        assert not result.success
        assert "test error" in result.error

    def test_force_open_close(self):
        """Test manual circuit control."""
        # Force open
        self.circuit.force_open()
        assert self.circuit.state == CircuitState.OPEN

        # Force close
        self.circuit.force_close()
        assert self.circuit.state == CircuitState.CLOSED

    def test_reset(self):
        """Test circuit breaker reset."""
        # Add some state
        self.circuit.failure_count = 5
        self.circuit.success_count = 3
        self.circuit.state = CircuitState.OPEN

        # Reset
        self.circuit.reset()

        assert self.circuit.state == CircuitState.CLOSED
        assert self.circuit.failure_count == 0
        assert self.circuit.success_count == 0
        assert len(self.circuit.request_history) == 0

    def test_get_health_status(self):
        """Test health status retrieval."""
        status = self.circuit.get_health_status()

        assert "name" in status
        assert "state" in status
        assert "stats" in status
        assert "config" in status
        assert status["name"] == "test_circuit"
        assert status["state"] == CircuitState.CLOSED.value


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CircuitBreakerRegistry()

    def test_get_circuit_breaker_sync(self):
        """Test synchronous circuit breaker retrieval."""
        circuit1 = self.registry.get_circuit_breaker_sync("test1")
        circuit2 = self.registry.get_circuit_breaker_sync("test1")
        circuit3 = self.registry.get_circuit_breaker_sync("test2")

        # Should return same instance for same name
        assert circuit1 is circuit2
        # Should return different instance for different name
        assert circuit1 is not circuit3

    @pytest.mark.asyncio
    async def test_get_circuit_breaker_async(self):
        """Test asynchronous circuit breaker retrieval."""
        circuit1 = await self.registry.get_circuit_breaker("test1")
        circuit2 = await self.registry.get_circuit_breaker("test1")
        circuit3 = await self.registry.get_circuit_breaker("test2")

        # Should return same instance for same name
        assert circuit1 is circuit2
        # Should return different instance for different name
        assert circuit1 is not circuit3

    def test_get_all_stats(self):
        """Test getting statistics for all circuit breakers."""
        self.registry.get_circuit_breaker_sync("test1")
        self.registry.get_circuit_breaker_sync("test2")

        stats = self.registry.get_all_stats()

        assert len(stats) == 2
        assert "test1" in stats
        assert "test2" in stats

    def test_get_health_status(self):
        """Test getting health status for all circuit breakers."""
        self.registry.get_circuit_breaker_sync("test1")
        self.registry.get_circuit_breaker_sync("test2")

        health = self.registry.get_health_status()

        assert "total_circuit_breakers" in health
        assert "overall_health" in health
        assert health["total_circuit_breakers"] == 2
        assert health["overall_health"] == "healthy"

    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        circuit1 = self.registry.get_circuit_breaker_sync("test1")
        circuit2 = self.registry.get_circuit_breaker_sync("test2")

        # Add some state
        circuit1.failure_count = 5
        circuit2.failure_count = 3

        # Reset all
        self.registry.reset_all()

        assert circuit1.failure_count == 0
        assert circuit2.failure_count == 0

    def test_force_open_all(self):
        """Test forcing all circuit breakers open."""
        circuit1 = self.registry.get_circuit_breaker_sync("test1")
        circuit2 = self.registry.get_circuit_breaker_sync("test2")

        # Force all open
        self.registry.force_open_all()

        assert circuit1.state == CircuitState.OPEN
        assert circuit2.state == CircuitState.OPEN


class TestDecorators:
    """Test circuit breaker decorators."""

    def test_circuit_breaker_decorator_sync(self):
        """Test circuit breaker decorator for sync functions."""

        @circuit_breaker("test_sync")
        def sync_func():
            return "sync_result"

        result = sync_func()
        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator_async(self):
        """Test circuit breaker decorator for async functions."""

        @circuit_breaker("test_async")
        async def async_func():
            return "async_result"

        result = await async_func()
        assert result == "async_result"

    def test_with_circuit_breaker_decorator(self):
        """Test with_circuit_breaker decorator."""

        @with_circuit_breaker("test_with", failure_threshold=1)
        def test_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            test_func()


class TestPlatformConfigurations:
    """Test platform-specific configurations."""

    def test_platform_configs_exist(self):
        """Test that all platform configurations exist."""
        expected_platforms = [
            "youtube",
            "twitch",
            "tiktok",
            "instagram",
            "x",
            "openrouter",
            "qdrant",
        ]

        for platform in expected_platforms:
            assert platform in PLATFORM_CONFIGS
            config = PLATFORM_CONFIGS[platform]
            assert isinstance(config, CircuitConfig)

    def test_platform_config_values(self):
        """Test platform configuration values."""
        youtube_config = PLATFORM_CONFIGS["youtube"]

        assert youtube_config.failure_threshold == 3
        assert youtube_config.recovery_timeout == 30.0
        assert youtube_config.call_timeout == 15.0

    def test_get_platform_circuit_breaker(self):
        """Test getting platform-specific circuit breaker."""
        breaker = get_platform_circuit_breaker("youtube")

        assert breaker.name == "youtube_api"
        assert breaker.config.failure_threshold == 3

    def test_get_platform_circuit_breaker_with_fallback(self):
        """Test getting platform circuit breaker with fallback."""

        def fallback_func():
            return "fallback"

        # Clear any existing circuit breakers to ensure fresh instance
        registry = get_circuit_breaker_registry()
        registry.circuit_breakers.clear()

        breaker = get_platform_circuit_breaker("youtube", fallback_func)

        assert breaker.name == "youtube_api"
        assert breaker.fallback is not None


class TestGlobalRegistry:
    """Test global circuit breaker registry."""

    def test_get_circuit_breaker_registry(self):
        """Test getting global registry."""
        registry1 = get_circuit_breaker_registry()
        registry2 = get_circuit_breaker_registry()

        # Should return same instance
        assert registry1 is registry2

    def test_global_registry_persistence(self):
        """Test that global registry persists across calls."""
        registry = get_circuit_breaker_registry()
        circuit = registry.get_circuit_breaker_sync("global_test")

        # Get registry again
        registry2 = get_circuit_breaker_registry()
        circuit2 = registry2.get_circuit_breaker_sync("global_test")

        # Should return same circuit breaker instance
        assert circuit is circuit2


class TestIntegration:
    """Integration tests for circuit breaker."""

    @pytest.mark.asyncio
    async def test_full_circuit_breaker_cycle(self):
        """Test complete circuit breaker cycle: closed -> open -> half-open -> closed."""
        circuit = CircuitBreaker(
            "integration_test",
            CircuitConfig(failure_threshold=2, recovery_timeout=0.1, success_threshold=2),
        )

        async def fail_func():
            raise ValueError("integration error")

        async def success_func():
            return "integration success"

        # Start in closed state
        assert circuit.state == CircuitState.CLOSED

        # Fail twice to open circuit
        with pytest.raises(ValueError):
            await circuit.call(fail_func)
        assert circuit.state == CircuitState.CLOSED

        with pytest.raises(ValueError):
            await circuit.call(fail_func)
        assert circuit.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # First success should transition to half-open
        result = await circuit.call(success_func)
        assert result == "integration success"
        assert circuit.state == CircuitState.HALF_OPEN

        # Second success should close circuit
        result = await circuit.call(success_func)
        assert result == "integration success"
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_concurrent_calls(self):
        """Test concurrent calls with circuit breaker."""
        circuit = CircuitBreaker("concurrent_test", CircuitConfig(max_concurrent_calls=2))

        async def slow_func():
            await asyncio.sleep(0.1)
            return "slow_result"

        # Make multiple concurrent calls
        tasks = [circuit.call(slow_func) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All calls should succeed
        assert all(result == "slow_result" for result in results)
        assert circuit.stats.successful_requests == 5


if __name__ == "__main__":
    pytest.main([__file__])
