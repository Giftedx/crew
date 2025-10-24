"""
Compatibility wrapper for core/resilience/circuit_breaker.py

This module provides backward compatibility for the old circuit breaker implementation.
All functionality has been migrated to the canonical implementation.
"""

from core.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
)
from core.circuit_breaker_canonical import (
    CircuitBreakerConfig as CircuitConfig,
)
from core.circuit_breaker_canonical import (
    CircuitBreakerError as CircuitBreakerOpenError,
)
from core.circuit_breaker_canonical import (
    CircuitBreakerManager as CircuitBreakerRegistry,
)
from core.circuit_breaker_canonical import (
    CircuitBreakerMetrics as CircuitStats,
)
from core.circuit_breaker_canonical import (
    get_circuit_breaker as get_circuit_breaker_sync,
)
from core.circuit_breaker_canonical import (
    get_circuit_breaker_manager as get_circuit_breaker_registry,
)


__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "CircuitConfig",
    "CircuitState",
    "CircuitStats",
    "circuit_breaker",
    "get_circuit_breaker_registry",
    "get_circuit_breaker_sync",
]
