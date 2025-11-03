"""
Compatibility wrapper for circuit breaker functionality.

This module provides backward compatibility for the old circuit breaker implementation.
All functionality has been migrated to the canonical implementation at
platform.http.circuit_breaker_canonical.
"""

from platform.http.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitConfig,
    CircuitState,
    CircuitStats,
    circuit_breaker,
    get_circuit_breaker_registry,
)


# Alias for backward compatibility
def get_circuit_breaker_sync(name: str, config: CircuitConfig | None = None):
    """Get a circuit breaker synchronously."""
    return get_circuit_breaker_registry().get_circuit_breaker_sync(name, config)


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
