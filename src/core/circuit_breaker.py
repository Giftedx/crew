"""
Circuit breaker pattern implementation for resilient system operation.

This module provides circuit breaker functionality to protect against cascading failures
and enable automatic rollback capabilities for the Ultimate Discord Intelligence Bot.
"""
from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast
from platform.observability import metrics
from .error_handling import log_error
if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
logger = logging.getLogger(__name__)
T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

@dataclass
class CircuitConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: float = 30.0
    failure_rate_threshold: float = 0.5
    minimum_requests: int = 10
    sliding_window_size: int = 100

@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_open_count: int = 0
    last_failure_time: float | None = None
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

class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation with advanced failure detection and recovery.

    Supports both simple failure counting and sliding window failure rate calculation.
    """

    def __init__(self, name: str, config: CircuitConfig | None=None, fallback: Callable[[], T | Awaitable[T]] | None=None):
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
        self.request_history: list[tuple[float, bool]] = []
        self.half_open_successes = 0
        logger.info(f"Circuit breaker '{name}' initialized")

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
        window_start = current_time - 300
        self.request_history = [(ts, result) for ts, result in self.request_history if ts > window_start]
        if len(self.request_history) > self.config.sliding_window_size:
            self.request_history = self.request_history[-self.config.sliding_window_size:]

    def _calculate_failure_rate(self) -> float:
        """Calculate failure rate from sliding window."""
        if len(self.request_history) < self.config.minimum_requests:
            return 0.0
        failures = sum((1 for _, success in self.request_history if not success))
        return failures / len(self.request_history)

    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure criteria."""
        if self.stats.failed_requests >= self.config.failure_threshold:
            return True
        if len(self.request_history) >= self.config.minimum_requests:
            failure_rate = self._calculate_failure_rate()
            if failure_rate >= self.config.failure_rate_threshold:
                return True
        return False

    def _on_success(self):
        """Handle successful request."""
        self.stats.successful_requests += 1
        self.stats.total_requests += 1
        self._update_sliding_window(success=True)
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.success_threshold:
                self._close_circuit()
        try:
            metrics.CIRCUIT_BREAKER_REQUESTS.labels(**metrics.label_ctx(), circuit=self.name, result='success').inc()
        except (AttributeError, TypeError, ValueError) as e:
            log_error(e, message='Failed to update success metrics - invalid metrics configuration', context={'circuit': self.name, 'state': self.state.value, 'operation': 'metrics_update'})
        except Exception as e:
            log_error(e, message='Failed to update success metrics', context={'circuit': self.name, 'state': self.state.value})

    def _on_failure(self, error: Exception | None=None):
        """Handle failed request."""
        self.stats.failed_requests += 1
        self.stats.total_requests += 1
        self.stats.last_failure_time = time.time()
        self._update_sliding_window(success=False)
        logger.warning(f"Circuit breaker '{self.name}' recorded failure: {error}")
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.state == CircuitState.CLOSED and self._should_open_circuit():
            self._open_circuit()
        try:
            metrics.CIRCUIT_BREAKER_REQUESTS.labels(**metrics.label_ctx(), circuit=self.name, result='failure').inc()
        except (AttributeError, TypeError, ValueError) as e:
            log_error(e, message='Failed to update failure metrics - invalid metrics configuration', context={'circuit': self.name, 'state': self.state.value, 'operation': 'metrics_update'})
        except Exception as e:
            log_error(e, message='Failed to update failure metrics', context={'circuit': self.name, 'state': self.state.value})

    def _open_circuit(self):
        """Transition circuit to open state."""
        self.state = CircuitState.OPEN
        self.stats.circuit_open_count += 1
        self.stats.last_state_change = time.time()
        self.half_open_successes = 0
        logger.warning(f"Circuit breaker '{self.name}' opened due to failures")
        try:
            metrics.CIRCUIT_BREAKER_STATE.labels(**metrics.label_ctx(), circuit=self.name).set(1)
        except (AttributeError, TypeError, ValueError) as e:
            log_error(e, message='Failed to update circuit open metrics - invalid metrics configuration', context={'circuit': self.name, 'operation': 'metrics_update'})
        except Exception as e:
            log_error(e, message='Failed to update circuit open metrics', context={'circuit': self.name})

    def _close_circuit(self):
        """Transition circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.stats.last_state_change = time.time()
        self.half_open_successes = 0
        self.stats.failed_requests = 0
        logger.info(f"Circuit breaker '{self.name}' closed - normal operation resumed")
        try:
            metrics.CIRCUIT_BREAKER_STATE.labels(**metrics.label_ctx(), circuit=self.name).set(0)
        except (AttributeError, TypeError, ValueError) as e:
            log_error(e, message='Failed to update circuit closed metrics - invalid metrics configuration', context={'circuit': self.name, 'operation': 'metrics_update'})
        except Exception as e:
            log_error(e, message='Failed to update circuit closed metrics', context={'circuit': self.name})

    def _half_open_circuit(self):
        """Transition circuit to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = time.time()
        self.half_open_successes = 0
        logger.info(f"Circuit breaker '{self.name}' half-open - testing recovery")
        try:
            metrics.CIRCUIT_BREAKER_STATE.labels(**metrics.label_ctx(), circuit=self.name).set(0.5)
        except (AttributeError, TypeError, ValueError) as e:
            log_error(e, message='Failed to update circuit half-open metrics - invalid metrics configuration', context={'circuit': self.name, 'operation': 'metrics_update'})
        except Exception as e:
            log_error(e, message='Failed to update circuit half-open metrics', context={'circuit': self.name})

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
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._half_open_circuit()
            elif self.fallback:
                logger.info(f"Circuit breaker '{self.name}' open, using fallback")
                result = self.fallback(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    awaited = await result
                    return awaited
                return cast('T', result)
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open - service unavailable")
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                awaited = await asyncio.wait_for(result, timeout=self.config.timeout)
                self._on_success()
                return awaited
            self._on_success()
            return cast('T', result)
        except TimeoutError:
            self.stats.timeouts += 1
            self._on_failure(error=Exception('Timeout'))
            raise
        except (AttributeError, TypeError, ValueError) as e:
            self._on_failure(error=e)
            raise
        except Exception as e:
            self._on_failure(error=e)
            raise

    def get_stats(self) -> CircuitStats:
        """Get current circuit breaker statistics."""
        return self.stats

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

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
        self.half_open_successes = 0
        logger.info(f"Circuit breaker '{self.name}' reset")

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, name: str, config: CircuitConfig | None=None, fallback: Callable | None=None) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config, fallback)
        return self.circuit_breakers[name]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: {'state': cb.get_state().value, 'stats': cb.get_stats().__dict__, 'config': cb.config.__dict__} for name, cb in self.circuit_breakers.items()}

    def get_health_status(self) -> dict[str, Any]:
        """Get overall health status of all circuit breakers."""
        total_breakers = len(self.circuit_breakers)
        open_breakers = sum((1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.OPEN))
        half_open_breakers = sum((1 for cb in self.circuit_breakers.values() if cb.get_state() == CircuitState.HALF_OPEN))
        return {'total_circuit_breakers': total_breakers, 'open_circuit_breakers': open_breakers, 'half_open_circuit_breakers': half_open_breakers, 'healthy_circuit_breakers': total_breakers - open_breakers - half_open_breakers, 'overall_health': 'healthy' if open_breakers == 0 else 'degraded' if open_breakers < total_breakers else 'critical'}
_circuit_registry: CircuitBreakerRegistry | None = None

def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _circuit_registry
    if _circuit_registry is None:
        _circuit_registry = CircuitBreakerRegistry()
    return _circuit_registry

def circuit_breaker(name: str, config: CircuitConfig | None=None, fallback: Callable | None=None):
    """Decorator to protect functions with circuit breaker."""

    def decorator(func):
        cb = get_circuit_breaker_registry().get_circuit_breaker(name, config, fallback)
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                return await cb.call(func, *args, **kwargs)
            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                return asyncio.run(cb.call(func, *args, **kwargs))
            return sync_wrapper
    return decorator
__all__ = ['CircuitBreaker', 'CircuitBreakerOpenError', 'CircuitBreakerRegistry', 'CircuitConfig', 'CircuitState', 'CircuitStats', 'circuit_breaker', 'get_circuit_breaker_registry']