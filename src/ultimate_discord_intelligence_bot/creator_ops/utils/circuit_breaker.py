"""
Compatibility wrapper for creator_ops/utils/circuit_breaker.py

This module provides backward compatibility for the creator ops circuit breaker implementation.
All functionality has been migrated to the canonical implementation.
"""

from core.circuit_breaker_canonical import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    get_circuit_breaker_registry,
    with_circuit_breaker,
)
from core.circuit_breaker_canonical import (
    CircuitBreakerManager as CircuitBreakerRegistry,
)

# Legacy compatibility
circuit_manager = get_circuit_breaker_registry()

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "CircuitBreakerRegistry",
    "circuit_manager",
    "with_circuit_breaker",
]
