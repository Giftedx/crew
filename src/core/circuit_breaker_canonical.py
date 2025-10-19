"""
Canonical Circuit Breaker Implementation

This module provides the definitive circuit breaker implementation for the Ultimate Discord Intelligence Bot,
consolidating features from all existing implementations into a single, comprehensive solution.

Features:
- Advanced failure detection (count + rate-based)
- Async/sync support
- Metrics integration
- Fallback mechanisms
- StepResult integration
- Platform API wrapping
- Registry management
- Health monitoring
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar, cast

from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, using fallback
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker behavior."""

    # Basic thresholds
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    success_threshold: int = 3  # Successes in half-open before closing
    call_timeout: float = 30.0  # Request timeout in seconds

    # Advanced failure detection
    failure_rate_threshold: float = 0.5  # 50% failure rate threshold
    minimum_requests: int = 10  # Minimum requests before calculating failure rate
    sliding_window_size: int = 100  # Size of sliding window for failure rate calculation

    # Concurrency control
    max_concurrent_calls: int = 10  # Maximum concurrent calls when circuit is open
    half_open_max_calls: int = 3  # Max calls allowed in half-open state

    # Monitoring and observability
    enable_metrics: bool = True
    log_failures: bool = True
    log_state_changes: bool = True

    # Exception handling
    expected_exceptions: tuple[type[Exception], ...] = (Exception,)


@dataclass
class CircuitStats:
    """Circuit breaker statistics and metrics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_open_count: int = 0
    circuit_half_open_count: int = 0
    circuit_closed_count: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    last_state_change: float = field(default_factory=time.time)

    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate current success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, state: CircuitState, last_failure: Exception | None = None):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.state = state
        self.last_failure = last_failure


class CircuitBreaker(Generic[T]):
    """
    Canonical circuit breaker implementation with advanced failure detection and recovery.

    Consolidates features from all existing implementations:
    - Advanced failure detection (count + rate-based)
    - Async/sync support with proper concurrency control
    - Metrics integration and health monitoring
    - Fallback mechanisms for graceful degradation
    - StepResult integration for consistent error handling
    - Platform API wrapping capabilities
    """

    def __init__(
        self,
        name: str,
        config: CircuitConfig | None = None,
        fallback: Callable[[], T | Awaitable[T]] | None = None,
    ):
        """Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            config: Circuit breaker configuration
            fallback: Optional fallback function to call when circuit is open
        """
        self.name = name
        self.config = config or CircuitConfig()
        self.fallback = fallback

        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()

        # State tracking
        self.failure_count = 0
        self.success_count = 0
        self.last_failure: Exception | None = None

        # Sliding window for failure rate calculation
        self.request_history: list[tuple[float, bool]] = []  # (timestamp, success)

        # Concurrency control
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_calls)
        self._lock = asyncio.Lock()

        # Half-open state tracking
        self.half_open_call_count = 0

        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from open to half-open."""
        if self.state != CircuitState.OPEN:
            return False

        if self.stats.last_failure_time is None:
            return True

        return time.time() - self.stats.last_failure_time >= self.config.recovery_timeout

    def _update_sliding_window(self, success: bool):
        """Update the sliding window of request history."""
        current_time = time.time()
        self.request_history.append((current_time, success))

        # Remove old entries outside the sliding window (last 5 minutes)
        window_start = current_time - 300  # 5 minutes
        self.request_history = [(ts, result) for ts, result in self.request_history if ts > window_start]

        # Limit window size
        if len(self.request_history) > self.config.sliding_window_size:
            self.request_history = self.request_history[-self.config.sliding_window_size :]

    def _calculate_failure_rate(self) -> float:
        """Calculate failure rate from sliding window."""
        if len(self.request_history) < self.config.minimum_requests:
            return 0.0

        failures = sum(1 for _, success in self.request_history if not success)
        return failures / len(self.request_history)

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure criteria."""
        # Simple failure count threshold
        if self.failure_count >= self.config.failure_threshold:
            return True

        # Failure rate threshold (only if we have enough samples)
        if len(self.request_history) >= self.config.minimum_requests:
            failure_rate = self._calculate_failure_rate()
            if failure_rate >= self.config.failure_rate_threshold:
                return True

        return False

    async def _record_success(self):
        """Handle successful request."""
        async with self._lock:
            self.stats.successful_requests += 1
            self.stats.total_requests += 1
            self.stats.last_success_time = time.time()
            self._update_sliding_window(success=True)

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                self.half_open_call_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._close_circuit()
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

            if self.config.log_state_changes and self.state == CircuitState.CLOSED:
                logger.info(f"Circuit breaker '{self.name}' recorded success")

    async def _record_failure(self, error: Exception | None = None):
        """Handle failed request."""
        async with self._lock:
            self.stats.failed_requests += 1
            self.stats.total_requests += 1
            self.stats.last_failure_time = time.time()
            self.last_failure = error
            self._update_sliding_window(success=False)

            if self.config.log_failures:
                logger.warning(f"Circuit breaker '{self.name}' recorded failure: {error}")

            self.failure_count += 1
            self.success_count = 0  # Reset success count on failure

            if self.state == CircuitState.HALF_OPEN:
                # Failure during half-open immediately opens circuit
                self._open_circuit()
            elif self.state == CircuitState.CLOSED:
                # Check if we should open circuit
                if self._should_open_circuit():
                    self._open_circuit()

    def _open_circuit(self):
        """Transition circuit to open state."""
        self.state = CircuitState.OPEN
        self.stats.circuit_open_count += 1
        self.stats.last_state_change = time.time()
        self.success_count = 0
        self.half_open_call_count = 0

        if self.config.log_state_changes:
            logger.warning(f"Circuit breaker '{self.name}' opened due to failures")

    def _close_circuit(self):
        """Transition circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.stats.circuit_closed_count += 1
        self.stats.last_state_change = time.time()
        self.failure_count = 0
        self.success_count = 0
        self.half_open_call_count = 0

        if self.config.log_state_changes:
            logger.info(f"Circuit breaker '{self.name}' closed - normal operation resumed")

    def _half_open_circuit(self):
        """Transition circuit to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.stats.circuit_half_open_count += 1
        self.stats.last_state_change = time.time()
        self.success_count = 0
        self.half_open_call_count = 0

        if self.config.log_state_changes:
            logger.info(f"Circuit breaker '{self.name}' half-open - testing recovery")

    async def call(self, func: Callable[[], T | Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute (sync or async)
            *args: Positional arguments to pass to function
            **kwargs: Keyword arguments to pass to function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: When circuit is open and no fallback available
        """
        async with self._lock:
            # Check circuit state and handle accordingly
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._half_open_circuit()
                else:
                    # Circuit is open, try fallback or raise error
                    if self.fallback:
                        logger.info(f"Circuit breaker '{self.name}' open, using fallback")
                        result = self.fallback(*args, **kwargs)
                        if asyncio.iscoroutine(result):
                            return await result
                        return cast(T, result)
                    else:
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker '{self.name}' is open - service unavailable",
                            self.name,
                            self.state,
                            self.last_failure,
                        )
            elif self.state == CircuitState.HALF_OPEN:
                # Check if we've exceeded half-open call limit
                if self.half_open_call_count >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' half-open call limit exceeded",
                        self.name,
                        self.state,
                        self.last_failure,
                    )

        # Execute with concurrency control and timeout
        async with self._semaphore:
            try:
                # Execute the function with timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.call_timeout)
                else:
                    result = func(*args, **kwargs)

                await self._record_success()
                return cast(T, result)

            except TimeoutError:
                self.stats.timeouts += 1
                await self._record_failure(error=Exception("Timeout"))
                raise

            except self.config.expected_exceptions as e:
                await self._record_failure(error=e)
                raise

            except Exception as e:
                await self._record_failure(error=e)
                raise

    async def call_with_result(self, func: Callable[[], StepResult], *args, **kwargs) -> StepResult:
        """
        Execute function returning StepResult with circuit breaker protection.

        Args:
            func: Function returning StepResult
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            StepResult from function or failure result if circuit is open
        """
        try:
            result = await self.call(func, *args, **kwargs)
            return result
        except CircuitBreakerOpenError as e:
            return StepResult.fail(f"Circuit breaker {self.name} is open: {str(e)}")
        except Exception as e:
            return StepResult.fail(f"Function failed: {str(e)}")

    def get_stats(self) -> CircuitStats:
        """Get current circuit breaker statistics."""
        return self.stats

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_requests": self.stats.total_requests,
                "success_rate": self.stats.success_rate,
                "failure_rate": self.stats.failure_rate,
                "timeouts": self.stats.timeouts,
                "circuit_open_count": self.stats.circuit_open_count,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
            },
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
        }

    def force_open(self):
        """Manually force circuit breaker to open state."""
        self._open_circuit()
        logger.warning(f"Circuit breaker '{self.name}' manually opened")

    def force_close(self):
        """Manually force circuit breaker to closed state."""
        self._close_circuit()
        logger.info(f"Circuit breaker '{self.name}' manually closed")

    def reset(self):
        """Reset circuit breaker statistics and state."""
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.request_history.clear()
        self.failure_count = 0
        self.success_count = 0
        self.half_open_call_count = 0
        self.last_failure = None

        logger.info(f"Circuit breaker '{self.name}' reset")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_circuit_breaker(
        self, name: str, config: CircuitConfig | None = None, fallback: Callable | None = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        async with self._lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name, config, fallback)
            return self.circuit_breakers[name]

    def get_circuit_breaker_sync(
        self, name: str, config: CircuitConfig | None = None, fallback: Callable | None = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker (synchronous)."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config, fallback)
        return self.circuit_breakers[name]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {
            name: {"state": cb.get_state().value, "stats": cb.get_stats().__dict__, "config": cb.config.__dict__}
            for name, cb in self.circuit_breakers.items()
        }

    def get_health_status(self) -> dict[str, Any]:
        """Get overall health status of all circuit breakers."""
        total_breakers = len(self.circuit_breakers)
        open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.OPEN)
        half_open_breakers = sum(1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.HALF_OPEN)

        return {
            "total_circuit_breakers": total_breakers,
            "open_circuit_breakers": open_breakers,
            "half_open_circuit_breakers": half_open_breakers,
            "healthy_circuit_breakers": total_breakers - open_breakers - half_open_breakers,
            "overall_health": "healthy"
            if open_breakers == 0
            else "degraded"
            if open_breakers < total_breakers
            else "critical",
            "breakers": {name: cb.get_health_status() for name, cb in self.circuit_breakers.items()},
        }

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.circuit_breakers.values():
            breaker.reset()

    def force_open_all(self):
        """Force all circuit breakers to open state."""
        for breaker in self.circuit_breakers.values():
            breaker.force_open()


# Global circuit breaker registry
_circuit_registry: CircuitBreakerRegistry | None = None


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _circuit_registry
    if _circuit_registry is None:
        _circuit_registry = CircuitBreakerRegistry()
    return _circuit_registry


def circuit_breaker(name: str, config: CircuitConfig | None = None, fallback: Callable | None = None):
    """Decorator to protect functions with circuit breaker."""

    def decorator(func):
        cb = get_circuit_breaker_registry().get_circuit_breaker_sync(name, config, fallback)

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                return await cb.call(func, *args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                return asyncio.run(cb.call(func, *args, **kwargs))

            return sync_wrapper

    return decorator


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Decorator to add circuit breaker protection to functions (legacy compatibility).

    Args:
        name: Circuit breaker name
        failure_threshold: Failure threshold
        recovery_timeout: Recovery timeout
        expected_exceptions: Exception types that count as failures
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        config = CircuitConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
        )
        cb = get_circuit_breaker_registry().get_circuit_breaker_sync(name, config)

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs) -> T:
                return await cb.call(func, *args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs) -> T:
                return asyncio.run(cb.call(func, *args, **kwargs))

            return sync_wrapper

    return decorator


# Platform-specific circuit breaker configurations
PLATFORM_CONFIGS = {
    "youtube": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=15.0,
        expected_exceptions=(Exception,),
    ),
    "twitch": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=15.0,
        expected_exceptions=(Exception,),
    ),
    "tiktok": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=15.0,
        expected_exceptions=(Exception,),
    ),
    "instagram": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=15.0,
        expected_exceptions=(Exception,),
    ),
    "x": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=15.0,
        expected_exceptions=(Exception,),
    ),
    "openrouter": CircuitConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        call_timeout=30.0,
        expected_exceptions=(Exception,),
    ),
    "qdrant": CircuitConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        call_timeout=10.0,
        expected_exceptions=(Exception,),
    ),
}


def get_platform_circuit_breaker(platform: str, fallback: Callable | None = None) -> CircuitBreaker:
    """Get a platform-specific circuit breaker."""
    config = PLATFORM_CONFIGS.get(platform, CircuitConfig())
    return get_circuit_breaker_registry().get_circuit_breaker_sync(f"{platform}_api", config, fallback)


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitConfig",
    "CircuitStats",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "get_circuit_breaker_registry",
    "circuit_breaker",
    "with_circuit_breaker",
    "get_platform_circuit_breaker",
    "PLATFORM_CONFIGS",
]
