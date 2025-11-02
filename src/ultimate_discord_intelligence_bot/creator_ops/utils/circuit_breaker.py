"""
Compatibility wrapper for creator_ops/utils/circuit_breaker.py

This module provides backward compatibility for the creator ops circuit breaker implementation.
All functionality has been migrated to the canonical implementation.
"""

from platform.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker_registry,
    with_circuit_breaker,
)


circuit_manager = get_circuit_breaker_registry()
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "CircuitState",
    "circuit_manager",
    "with_circuit_breaker",
]
