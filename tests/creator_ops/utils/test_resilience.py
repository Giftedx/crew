"""
Tests for resilience utilities including circuit breakers, idempotency, rate limiting, and backpressure.
"""

import asyncio
import time
from unittest.mock import patch

import pytest
from core.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker_registry,
    with_circuit_breaker,
)

from ultimate_discord_intelligence_bot.creator_ops.utils.backpressure import (
    BackpressureHandler,
    BackpressureManager,
    backpressure_manager,
    with_backpressure,
)
from ultimate_discord_intelligence_bot.creator_ops.utils.idempotency import (
    IdempotencyManager,
    idempotency_manager,
    with_idempotency,
    with_result_idempotency,
)
from ultimate_discord_intelligence_bot.creator_ops.utils.rate_limiter import (
    RateLimiter,
    SlidingWindowRateLimiter,
    TokenBucket,
    rate_limiter_manager,
    with_rate_limit,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestCircuitBreaker:
    """Test suite for CircuitBreaker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,
            name="test_breaker",
        )

    @pytest.mark.asyncio
    async def test_circuit_closed_normal_operation(self):
        """Test normal operation when circuit is closed."""

        async def successful_operation():
            return "success"

        result = await self.breaker.call(successful_operation)
        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test circuit opens after reaching failure threshold."""

        async def failing_operation():
            raise ValueError("Test error")

        # Execute failing operations
        for i in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(failing_operation)
            assert self.breaker.failure_count == i + 1

        # Circuit should now be open
        assert self.breaker.state == CircuitState.OPEN
        assert self.breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_fails_fast_when_open(self):
        """Test circuit fails fast when open."""
        # Open the circuit
        self.breaker.state = CircuitState.OPEN
        self.breaker.failure_count = 3

        async def any_operation():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenError):
            await self.breaker.call(any_operation)

    @pytest.mark.asyncio
    async def test_circuit_recovery_after_timeout(self):
        """Test circuit recovers after timeout."""
        # Open the circuit
        self.breaker.state = CircuitState.OPEN
        self.breaker.failure_count = 3
        self.breaker.last_failure_time = time.time() - 2.0  # 2 seconds ago

        async def successful_operation():
            return "recovered"

        result = await self.breaker.call(successful_operation)
        assert result == "recovered"
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_half_open_state(self):
        """Test circuit half-open state behavior."""
        # Set to half-open
        self.breaker.state = CircuitState.HALF_OPEN

        async def successful_operation():
            return "success"

        result = await self.breaker.call(successful_operation)
        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_half_open_failure(self):
        """Test circuit returns to open on failure in half-open state."""
        # Set to half-open
        self.breaker.state = CircuitState.HALF_OPEN

        async def failing_operation():
            raise ValueError("Still failing")

        with pytest.raises(ValueError):
            await self.breaker.call(failing_operation)

        assert self.breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_call_with_result(self):
        """Test call_with_result method."""

        async def successful_operation():
            return StepResult.ok(data={"test": "data"})

        result = await self.breaker.call_with_result(successful_operation)
        assert result.success
        assert result.data == {"test": "data"}

        # Test with circuit open
        self.breaker.state = CircuitState.OPEN
        result = await self.breaker.call_with_result(successful_operation)
        assert not result.success
        assert "Circuit breaker" in result.error

    def test_get_state(self):
        """Test get_state method."""
        state = self.breaker.get_state()
        assert state["name"] == "test_breaker"
        assert state["state"] == CircuitState.CLOSED.value
        assert state["failure_count"] == 0

    def test_manual_reset(self):
        """Test manual reset."""
        self.breaker.state = CircuitState.OPEN
        self.breaker.failure_count = 3

        self.breaker.reset()
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker.failure_count == 0

    def test_force_open(self):
        """Test force open."""
        self.breaker.force_open()
        assert self.breaker.state == CircuitState.OPEN


class TestCircuitBreakerManager:
    """Test suite for CircuitBreakerManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = CircuitBreakerRegistry()

    def test_get_breaker(self):
        """Test getting or creating circuit breakers."""
        breaker1 = self.registry.get_circuit_breaker_sync("test_service")
        breaker2 = self.registry.get_circuit_breaker_sync("test_service")

        assert breaker1 is breaker2
        assert "test_service" in self.registry.circuit_breakers

    def test_get_all_states(self):
        """Test getting all breaker states."""
        self.registry.get_circuit_breaker_sync("service1")
        self.registry.get_circuit_breaker_sync("service2")

        stats = self.registry.get_all_stats()
        assert "service1" in stats
        assert "service2" in stats

    def test_reset_all(self):
        """Test resetting all breakers."""
        breaker1 = self.registry.get_circuit_breaker_sync("service1")
        breaker2 = self.registry.get_circuit_breaker_sync("service2")

        breaker1.force_open()
        breaker2.force_open()

        self.registry.reset_all()
        assert breaker1.get_state() == CircuitState.CLOSED
        assert breaker2.get_state() == CircuitState.CLOSED


class TestIdempotencyManager:
    """Test suite for IdempotencyManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = IdempotencyManager(default_ttl=1.0)

    @pytest.mark.asyncio
    async def test_execute_with_idempotency_success(self):
        """Test successful idempotent execution."""

        async def test_operation():
            return "result"

        # First execution
        result1 = await self.registry.execute_with_idempotency(test_operation, "test_key")
        assert result1 == "result"

        # Second execution with same key should return cached result
        result2 = await self.registry.execute_with_idempotency(test_operation, "test_key")
        assert result2 == "result"

    @pytest.mark.asyncio
    async def test_execute_with_idempotency_different_keys(self):
        """Test different keys execute separately."""
        execution_count = 0

        async def counting_operation():
            nonlocal execution_count
            execution_count += 1
            return f"result_{execution_count}"

        # Execute with different keys
        result1 = await self.registry.execute_with_idempotency(counting_operation, "key1")
        result2 = await self.registry.execute_with_idempotency(counting_operation, "key2")

        assert result1 == "result_1"
        assert result2 == "result_2"
        assert execution_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_idempotency_expiration(self):
        """Test idempotency key expiration."""
        execution_count = 0

        async def counting_operation():
            nonlocal execution_count
            execution_count += 1
            return f"result_{execution_count}"

        # Execute with short TTL
        result1 = await self.registry.execute_with_idempotency(counting_operation, "test_key", ttl=0.1)
        assert result1 == "result_1"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Execute again - should run again
        result2 = await self.registry.execute_with_idempotency(counting_operation, "test_key")
        assert result2 == "result_2"
        assert execution_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_result_idempotency(self):
        """Test StepResult idempotent execution."""

        async def test_operation():
            return StepResult.ok(data={"test": "data"})

        # First execution
        result1 = await self.registry.execute_with_result_idempotency(test_operation, "test_key")
        assert result1.success
        assert result1.data == {"test": "data"}

        # Second execution should return cached result
        result2 = await self.registry.execute_with_result_idempotency(test_operation, "test_key")
        assert result2.success
        assert result2.data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup of expired keys."""
        # Create expired key
        await self.registry.execute_with_idempotency(lambda: "test", "expired_key", ttl=0.1)
        await asyncio.sleep(0.2)

        # Cleanup
        cleaned = await self.registry.cleanup_expired()
        assert cleaned == 1

    def test_get_stats(self):
        """Test getting manager statistics."""
        stats = self.registry.get_stats()
        assert "total_keys" in stats
        assert "expired_keys" in stats
        assert "active_keys" in stats

    @pytest.mark.asyncio
    async def test_clear_all(self):
        """Test clearing all keys."""
        await self.registry.execute_with_idempotency(lambda: "test", "key1")
        await self.registry.execute_with_idempotency(lambda: "test", "key2")

        assert len(self.registry._store) == 2
        await self.registry.clear_all()
        assert len(self.registry._store) == 0


class TestTokenBucket:
    """Test suite for TokenBucket."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bucket = TokenBucket(capacity=10, refill_rate=2.0, name="test_bucket")

    @pytest.mark.asyncio
    async def test_acquire_tokens_success(self):
        """Test successful token acquisition."""
        success = await self.bucket.acquire(5)
        assert success
        assert self.bucket.tokens == 5

    @pytest.mark.asyncio
    async def test_acquire_tokens_failure(self):
        """Test failed token acquisition."""
        success = await self.bucket.acquire(15)  # More than capacity
        assert not success
        assert self.bucket.tokens == 10  # Unchanged

    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test token refill over time."""
        # Use all tokens
        await self.bucket.acquire(10)
        assert self.bucket.tokens == 0

        # Wait for refill
        await asyncio.sleep(0.6)  # Should refill 1.2 tokens

        success = await self.bucket.acquire(1)
        assert success

    @pytest.mark.asyncio
    async def test_wait_for_tokens(self):
        """Test waiting for tokens."""
        # Use all tokens
        await self.bucket.acquire(10)

        # Wait for tokens with timeout
        success = await self.bucket.wait_for_tokens(1, timeout=1.0)
        assert success

    @pytest.mark.asyncio
    async def test_wait_for_tokens_timeout(self):
        """Test waiting for tokens with timeout."""
        # Use all tokens
        await self.bucket.acquire(10)

        # Wait with short timeout
        success = await self.bucket.wait_for_tokens(1, timeout=0.1)
        assert not success

    def test_get_status(self):
        """Test getting bucket status."""
        status = self.bucket.get_health_status()
        assert status["name"] == "test_bucket"
        assert status["tokens"] == 10
        assert status["capacity"] == 10


class TestSlidingWindowRateLimiter:
    """Test suite for SlidingWindowRateLimiter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1.0, name="test_limiter")

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful request acquisition."""
        for _i in range(5):
            success = await self.limiter.acquire()
            assert success

    @pytest.mark.asyncio
    async def test_acquire_failure(self):
        """Test failed request acquisition."""
        # Use up all requests
        for _i in range(5):
            await self.limiter.acquire()

        # Next request should fail
        success = await self.limiter.acquire()
        assert not success

    @pytest.mark.asyncio
    async def test_window_sliding(self):
        """Test window sliding behavior."""
        # Use up all requests
        for _i in range(5):
            await self.limiter.acquire()

        # Wait for window to slide
        await asyncio.sleep(1.1)

        # Should be able to acquire again
        success = await self.limiter.acquire()
        assert success

    def test_get_status(self):
        """Test getting limiter status."""
        status = self.limiter.get_health_status()
        assert status["name"] == "test_limiter"
        assert status["max_requests"] == 5
        assert status["window_seconds"] == 1.0


class TestRateLimiter:
    """Test suite for RateLimiter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.token_bucket = TokenBucket(capacity=5, refill_rate=1.0)
        self.sliding_window = SlidingWindowRateLimiter(max_requests=3, window_seconds=1.0)
        self.limiter = RateLimiter(
            token_bucket=self.token_bucket,
            sliding_window=self.sliding_window,
            name="test_limiter",
        )

    @pytest.mark.asyncio
    async def test_acquire_both_limits(self):
        """Test acquisition with both limits."""
        # Should succeed
        success = await self.limiter.acquire()
        assert success

        # Use up token bucket
        for _i in range(4):
            await self.limiter.acquire()

        # Next should fail (token bucket exhausted)
        success = await self.limiter.acquire()
        assert not success

    @pytest.mark.asyncio
    async def test_acquire_only_token_bucket(self):
        """Test acquisition with only token bucket."""
        limiter = RateLimiter(token_bucket=self.token_bucket)

        success = await limiter.acquire()
        assert success

    @pytest.mark.asyncio
    async def test_acquire_only_sliding_window(self):
        """Test acquisition with only sliding window."""
        limiter = RateLimiter(sliding_window=self.sliding_window)

        success = await limiter.acquire()
        assert success

    def test_get_status(self):
        """Test getting limiter status."""
        status = self.limiter.get_health_status()
        assert status["name"] == "test_limiter"
        assert "token_bucket" in status
        assert "sliding_window" in status


class TestBackpressureHandler:
    """Test suite for BackpressureHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = BackpressureHandler(
            max_queue_depth=10,
            warning_threshold=0.7,
            critical_threshold=0.9,
            name="test_handler",
        )

    @pytest.mark.asyncio
    async def test_acquire_success(self):
        """Test successful slot acquisition."""
        success = await self.handler.acquire(5)
        assert success
        assert self.handler.current_depth == 5

    @pytest.mark.asyncio
    async def test_acquire_failure(self):
        """Test failed slot acquisition."""
        success = await self.handler.acquire(15)  # More than max depth
        assert not success
        assert self.handler.current_depth == 0

    @pytest.mark.asyncio
    async def test_release_slots(self):
        """Test releasing slots."""
        await self.handler.acquire(5)
        await self.handler.release(3)
        assert self.handler.current_depth == 2

    @pytest.mark.asyncio
    async def test_release_more_than_acquired(self):
        """Test releasing more slots than acquired."""
        await self.handler.acquire(3)
        await self.handler.release(5)  # Release more than acquired
        assert self.handler.current_depth == 0  # Should not go negative

    @pytest.mark.asyncio
    async def test_wait_for_slots(self):
        """Test waiting for slots."""
        # Use up most slots
        await self.handler.acquire(9)

        # Wait for slots with timeout
        success = await self.handler.wait_for_slots(1, timeout=1.0)
        assert success

    @pytest.mark.asyncio
    async def test_wait_for_slots_timeout(self):
        """Test waiting for slots with timeout."""
        # Use up all slots
        await self.handler.acquire(10)

        # Wait with short timeout
        success = await self.handler.wait_for_slots(1, timeout=0.1)
        assert not success

    @pytest.mark.asyncio
    async def test_throttling(self):
        """Test throttling behavior."""
        # Set high load to trigger throttling
        self.handler.current_depth = 9  # Above critical threshold

        # Mock time to trigger throttling adjustment
        with patch("time.time") as mock_time:
            mock_time.return_value = time.time() + 10  # Advance time
            await self.handler._adjust_throttling()

        # Should have some throttling
        assert self.handler.throttle_factor < 1.0

    def test_get_status(self):
        """Test getting handler status."""
        status = self.handler.get_health_status()
        assert status["name"] == "test_handler"
        assert status["max_depth"] == 10
        assert status["current_depth"] == 0

    def test_get_status_level(self):
        """Test status level calculation."""
        # Normal
        assert self.handler._get_status_level() == "normal"

        # Warning
        self.handler.current_depth = 8
        assert self.handler._get_status_level() == "warning"

        # Critical
        self.handler.current_depth = 10
        assert self.handler._get_status_level() == "critical"


class TestBackpressureManager:
    """Test suite for BackpressureManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = BackpressureManager()

    def test_get_handler(self):
        """Test getting or creating handlers."""
        handler1 = self.registry.get_handler("test_service")
        handler2 = self.registry.get_handler("test_service")

        assert handler1 is handler2
        assert "test_service" in self.registry.handlers

    def test_get_all_status(self):
        """Test getting all handler statuses."""
        self.registry.get_handler("service1")
        self.registry.get_handler("service2")

        statuses = self.registry.get_all_status()
        assert "service1" in statuses
        assert "service2" in statuses

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup of old depth history."""
        handler = self.registry.get_handler("test_service")

        # Add some depth history
        handler.depth_history.append((time.time() - 400, 5))  # Old entry
        handler.depth_history.append((time.time(), 3))  # Recent entry

        await self.registry.cleanup()

        # Should only have recent entry
        assert len(handler.depth_history) == 1


class TestDecorators:
    """Test suite for resilience decorators."""

    @pytest.mark.asyncio
    async def test_with_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""

        @with_circuit_breaker("test_service", failure_threshold=2)
        async def failing_operation():
            raise ValueError("Test error")

        # First failure
        with pytest.raises(ValueError):
            await failing_operation()

        # Second failure should open circuit
        with pytest.raises(CircuitBreakerOpenError):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_with_idempotency_decorator(self):
        """Test idempotency decorator."""
        execution_count = 0

        @with_idempotency("test_key")
        async def counting_operation():
            nonlocal execution_count
            execution_count += 1
            return f"result_{execution_count}"

        # First execution
        result1 = await counting_operation()
        assert result1 == "result_1"

        # Second execution should return cached result
        result2 = await counting_operation()
        assert result2 == "result_1"  # Cached result
        assert execution_count == 1  # Only executed once

    @pytest.mark.asyncio
    async def test_with_rate_limit_decorator(self):
        """Test rate limit decorator."""

        @with_rate_limit("test_limiter")
        async def limited_operation():
            return "success"

        # Should work with default rate limiter
        result = await limited_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_backpressure_decorator(self):
        """Test backpressure decorator."""

        @with_backpressure("test_handler", required_slots=1)
        async def pressured_operation():
            return "success"

        # Should work with default backpressure handler
        result = await pressured_operation()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_result_decorators(self):
        """Test StepResult decorators."""

        @with_result_idempotency("result_key")
        async def result_operation():
            return StepResult.ok(data={"test": "data"})

        # First execution
        result1 = await result_operation()
        assert result1.success
        assert result1.data == {"test": "data"}

        # Second execution should return cached result
        result2 = await result_operation()
        assert result2.success
        assert result2.data == {"test": "data"}


class TestGlobalManagers:
    """Test suite for global managers."""

    def test_circuit_manager(self):
        """Test global circuit breaker manager."""
        breaker = get_circuit_breaker_registry().get_circuit_breaker_sync("global_test")
        assert breaker.name == "global_test"

    def test_idempotency_manager(self):
        """Test global idempotency manager."""
        stats = idempotency_manager.get_stats()
        assert "total_keys" in stats

    def test_rate_limiter_manager(self):
        """Test global rate limiter manager."""
        limiter = rate_limiter_manager.get_limiter("global_test")
        assert limiter.name == "global_test"

    def test_backpressure_manager(self):
        """Test global backpressure manager."""
        handler = backpressure_manager.get_handler("global_test")
        assert handler.name == "global_test"
