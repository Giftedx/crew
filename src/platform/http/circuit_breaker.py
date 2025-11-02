"""
Compatibility wrapper for circuit breaker functionality.

This module provides backward compatibility for the old circuit breaker implementation.
All functionality has been migrated to the canonical implementation at
platform.http.circuit_breaker_canonical.
"""
from platform.http.circuit_breaker_canonical import CircuitBreaker, CircuitBreakerOpenError, CircuitConfig, CircuitState, circuit_breaker
from platform.http.circuit_breaker_canonical import CircuitBreakerManager as CircuitBreakerRegistry
from platform.http.circuit_breaker_canonical import CircuitBreakerMetrics as CircuitStats
from platform.http.circuit_breaker_canonical import get_circuit_breaker as get_circuit_breaker_sync
from platform.http.circuit_breaker_canonical import get_circuit_breaker_manager as get_circuit_breaker_registry
__all__ = ['CircuitBreaker', 'CircuitBreakerOpenError', 'CircuitBreakerRegistry', 'CircuitConfig', 'CircuitState', 'CircuitStats', 'circuit_breaker', 'get_circuit_breaker_registry', 'get_circuit_breaker_sync']