"""
Resilience patterns for pipeline optimization.

This module provides comprehensive resilience patterns including circuit breakers,
adaptive batching, and intelligent retry mechanisms for improved system reliability
and performance.
"""

from .adaptive_batching import (
    AdaptiveBatcher,
    BatchConfig,
    BatchManager,
    BatchMetrics,
    BatchStrategy,
    create_batcher,
    get_batch_manager,
    get_batcher,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitBreakerMetrics,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker,
    get_circuit_breaker_manager,
)
from .intelligent_retry import (
    IntelligentRetry,
    RetryCondition,
    RetryConfig,
    RetryError,
    RetryManager,
    RetryMetrics,
    RetryStrategy,
    create_retry_system,
    get_retry_manager,
    retry,
)


__all__ = [
    # Adaptive batching exports
    "AdaptiveBatcher",
    "BatchConfig",
    "BatchManager",
    "BatchMetrics",
    "BatchStrategy",
    # Circuit breaker exports
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerManager",
    "CircuitBreakerMetrics",
    "CircuitState",
    # Intelligent retry exports
    "IntelligentRetry",
    "RetryCondition",
    "RetryConfig",
    "RetryError",
    "RetryManager",
    "RetryMetrics",
    "RetryStrategy",
    "circuit_breaker",
    "create_batcher",
    "create_retry_system",
    "get_batch_manager",
    "get_batcher",
    "get_circuit_breaker",
    "get_circuit_breaker_manager",
    "get_retry_manager",
    "retry",
]
