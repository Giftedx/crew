from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "closed"  # closed, open, half_open


class EnhancedErrorRecovery:
    """Enhanced error recovery with circuit breaker and exponential backoff."""

    def __init__(self, max_failures: int = 5, reset_timeout: float = 60.0, base_delay: float = 1.0):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.base_delay = base_delay
        self.circuit_breakers: dict[str, CircuitBreakerState] = {}

    def _get_circuit_key(self, model: str | None, provider: str | None) -> str:
        return f"{model or 'default'}:{provider or 'default'}"

    def should_attempt_request(self, model: str | None = None, provider: str | None = None) -> bool:
        key = self._get_circuit_key(model, provider)
        state = self.circuit_breakers.get(key, CircuitBreakerState())
        if state.state == "open":
            if time.time() - state.last_failure_time >= self.reset_timeout:
                state.state = "half_open"
                self.circuit_breakers[key] = state
                return True
            return False
        return True

    def record_success(self, model: str | None = None, provider: str | None = None):
        key = self._get_circuit_key(model, provider)
        if key in self.circuit_breakers:
            state = self.circuit_breakers[key]
            state.failure_count = 0
            state.state = "closed"
            self.circuit_breakers[key] = state

    def record_failure(self, model: str | None = None, provider: str | None = None):
        key = self._get_circuit_key(model, provider)
        state = self.circuit_breakers.get(key, CircuitBreakerState())
        state.failure_count += 1
        state.last_failure_time = time.time()
        if state.failure_count >= self.max_failures:
            state.state = "open"
        self.circuit_breakers[key] = state

    def get_backoff_delay(self, attempt: int, max_delay: float = 30.0) -> float:
        delay = self.base_delay * (2**attempt)
        return min(delay, max_delay)

    def categorize_error(self, error: Exception) -> str:
        error_str = str(error).lower()
        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str or "connection" in error_str:
            return "timeout"
        elif "validation" in error_str or "pydantic" in error_str:
            return "validation"
        elif "parsing" in error_str or "json" in error_str:
            return "parsing"
        else:
            return "unknown"
