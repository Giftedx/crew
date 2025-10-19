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
    # Circuit breaker exports
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerManager",
    "CircuitBreakerMetrics",
    "CircuitState",
    "get_circuit_breaker",
    "get_circuit_breaker_manager",
    "circuit_breaker",
    # Adaptive batching exports
    "AdaptiveBatcher",
    "BatchConfig",
    "BatchManager",
    "BatchMetrics",
    "BatchStrategy",
    "get_batch_manager",
    "get_batcher",
    "create_batcher",
    # Intelligent retry exports
    "IntelligentRetry",
    "RetryConfig",
    "RetryCondition",
    "RetryError",
    "RetryManager",
    "RetryMetrics",
    "RetryStrategy",
    "get_retry_manager",
    "create_retry_system",
    "retry",
]
