"""Retry and circuit breaker logic for HTTP requests."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import warnings
from datetime import date
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import requests

from obs import metrics as _metrics

from .config import (
    DEFAULT_HTTP_RETRY_ATTEMPTS,
    HTTP_RATE_LIMITED,
    REQUEST_TIMEOUT_SECONDS,
)
from .requests_wrappers import resilient_get, resilient_post


if TYPE_CHECKING:
    from collections.abc import Callable


try:  # optional opentelemetry
    from opentelemetry import trace  # pragma: no cover
except Exception:  # pragma: no cover - fallback

    class _NoopSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *_, **__):
            return None

    class _NoopTracer:
        def start_as_current_span(self, *_a, **_k):
            return _NoopSpan()

    class _NoopTraceAPI:
        def get_tracer(self, *_a, **_k) -> _NoopTracer:
            return _NoopTracer()

    trace = _NoopTraceAPI()  # type: ignore[assignment]


_HTTP_RETRY_LEGACY_REMOVAL = date.fromisoformat("2025-12-31")
_DEPRECATION_LOG_EMITTED: dict[str, bool] = {}


def _is_retry_enabled() -> bool:
    raw_env = os.getenv("ENABLE_HTTP_RETRY")
    if raw_env is not None:
        return str(raw_env).lower() in ("1", "true", "yes", "on")
    legacy_flag = os.getenv("ENABLE_ANALYSIS_HTTP_RETRY")
    if legacy_flag and str(legacy_flag).lower() in ("1", "true", "yes", "on"):
        if date.today() > _HTTP_RETRY_LEGACY_REMOVAL:
            raise RuntimeError(
                "ENABLE_HTTP_RETRY exceeded deprecation window (removal after 2025-12-31). "
                "Remove this variable and set ENABLE_HTTP_RETRY if retries are desired."
            )
        warnings.warn(
            "ENABLE_ANALYSIS_HTTP_RETRY is deprecated; use ENABLE_HTTP_RETRY instead (grace until 2025-12-31).",
            DeprecationWarning,
            stacklevel=2,
        )
        if not _DEPRECATION_LOG_EMITTED.get("ENABLE_HTTP_RETRY"):
            logging.getLogger("deprecations").info(
                json.dumps(
                    {
                        "event": "deprecated_flag_used",
                        "flag": "ENABLE_ANALYSIS_HTTP_RETRY",
                        "replacement": "ENABLE_HTTP_RETRY",
                        "removal_date": str(_HTTP_RETRY_LEGACY_REMOVAL),
                    }
                )
            )
            _DEPRECATION_LOG_EMITTED["ENABLE_ANALYSIS_HTTP_RETRY"] = True
        return True
    return False


def is_retry_enabled() -> bool:
    return _is_retry_enabled()


class _CircuitBreaker:
    """Enhanced circuit breaker with configurable thresholds and monitoring.

    Protects against cascading failures by temporarily stopping requests
    to failing services and allowing them to recover.
    """

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[BaseException] = requests.RequestException,
        success_threshold: int = 3,  # consecutive successes needed to close
        half_open_max_calls: int = 3,  # max calls allowed in half-open state
    ) -> None:
        self.name = name
        self.failure_threshold = max(1, int(failure_threshold))
        self.recovery_timeout = float(recovery_timeout)
        self.expected_exception = expected_exception
        self.success_threshold = max(1, int(success_threshold))
        self.half_open_max_calls = max(1, int(half_open_max_calls))
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state: str = "closed"
        self.success_count = 0  # consecutive successes in half-open state
        self.half_open_call_count = 0  # calls made in half-open state
        self.lock = threading.Lock()

    def _update_state_on_success(self) -> None:
        with self.lock:
            if self.state == "half_open":
                self.success_count += 1
                self.half_open_call_count += 1

                # Close circuit breaker after sufficient consecutive successes
                if self.success_count >= self.success_threshold:
                    self.state = "closed"
                    self.success_count = 0
                    self.half_open_call_count = 0
            elif self.state == "closed":
                # Reset failure count on success in closed state
                self.failure_count = 0

    def _update_state_on_failure(self) -> None:
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            # Open circuit breaker after failure threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                # Reset counters when opening circuit
                self.success_count = 0
                self.half_open_call_count = 0

    def _can_attempt(self) -> bool:
        with self.lock:
            if self.state == "open":
                if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                    # Transition to half-open state for testing recovery
                    self.state = "half_open"
                    self.failure_count = 0
                    self.success_count = 0
                    self.half_open_call_count = 0
                    return True
                return False
            elif self.state == "half_open":
                # Allow limited calls in half-open state for testing recovery
                if self.half_open_call_count < self.half_open_max_calls:
                    self.half_open_call_count += 1
                    return True
                return False
            return True

    def get_status(self) -> dict[str, Any]:
        """Get current circuit breaker status for monitoring."""
        with self.lock:
            return {
                "name": self.name,
                "state": self.state,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "half_open_call_count": self.half_open_call_count,
                "last_failure_time": self.last_failure_time,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            }


_BREAKERS: dict[str, _CircuitBreaker] = {}


def get_circuit_breaker_status() -> dict[str, dict[str, Any]]:
    """Get status of all active circuit breakers for monitoring."""
    return {name: breaker.get_status() for name, breaker in _BREAKERS.items()}


def reset_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    global _BREAKERS
    _BREAKERS.clear()


def _breaker_for(url: str) -> tuple[str, _CircuitBreaker]:
    """Get or create circuit breaker for a URL host with enhanced configuration."""
    host = urlparse(url).hostname or "unknown"
    br = _BREAKERS.get(host)
    if br is None:
        # Enhanced circuit breaker configuration for different service types
        if "openrouter" in host.lower():
            # OpenRouter API - more tolerant due to rate limits
            br = _CircuitBreaker(
                name=host,
                failure_threshold=10,
                recovery_timeout=120.0,
                success_threshold=5,
                half_open_max_calls=5,
            )
        elif "qdrant" in host.lower():
            # Vector database - more strict for data consistency
            br = _CircuitBreaker(
                name=host,
                failure_threshold=3,
                recovery_timeout=30.0,
                success_threshold=3,
                half_open_max_calls=2,
            )
        else:
            # Default configuration for other services
            br = _CircuitBreaker(
                name=host,
                failure_threshold=5,
                recovery_timeout=60.0,
                success_threshold=3,
                half_open_max_calls=3,
            )
        _BREAKERS[host] = br
    return host, br


def http_request_with_retry(
    method: str,
    url: str,
    *,
    request_callable: Callable[..., Any],
    statuses_to_retry: tuple[int, ...] = (500, 502, 503, 504, HTTP_RATE_LIMITED),
    max_attempts: int = DEFAULT_HTTP_RETRY_ATTEMPTS,
    base_backoff: float = 0.5,
    jitter: float = 0.05,
    on_give_up: Callable[[Exception | None, int], None] | None = None,
    **call_kwargs: Any,
) -> Any:
    tracer = trace.get_tracer(__name__)
    attempts = 0
    try:
        host_label = urlparse(url).hostname or "unknown"
    except Exception:
        host_label = "unknown"
    br_host = host_label
    br_inst: _CircuitBreaker | None = None
    if is_circuit_breaker_enabled():
        br_host, br_inst = _breaker_for(url)
        if br_inst and not br_inst._can_attempt():
            _metrics.CIRCUIT_BREAKER_REQUESTS.labels(
                **_metrics.label_ctx(), circuit=br_host, result="short_circuit"
            ).inc()
            _metrics.CIRCUIT_BREAKER_STATE.labels(**_metrics.label_ctx(), circuit=br_host).set(1.0)
            raise requests.RequestException(f"circuit_open:{br_host}")
    while True:
        attempts += 1
        with tracer.start_as_current_span("http.retry_attempt") as span:
            span.set_attribute("http.url", url)
            span.set_attribute("http.method", method)
            span.set_attribute("retry.attempt", attempts)
            try:
                resp = request_callable(url, **call_kwargs)
            except requests.RequestException as exc:
                span.set_attribute("error", True)
                span.set_attribute("exception.type", exc.__class__.__name__)
                if br_inst is not None:
                    br_inst._update_state_on_failure()
                    state_val = 1.0 if br_inst.state == "open" else (0.5 if br_inst.state == "half_open" else 0.0)
                    _metrics.CIRCUIT_BREAKER_REQUESTS.labels(
                        **_metrics.label_ctx(), circuit=br_host, result="failure"
                    ).inc()
                    _metrics.CIRCUIT_BREAKER_STATE.labels(**_metrics.label_ctx(), circuit=br_host).set(state_val)
                if attempts >= max_attempts or not _is_retry_enabled():
                    if attempts > 1:
                        _metrics.HTTP_RETRY_GIVEUPS.labels(**_metrics.label_ctx(), method=method, host=host_label).inc()
                    if on_give_up:
                        on_give_up(exc, attempts)
                    span.set_attribute("retry.give_up", True)
                    span.set_attribute("retry.final_attempts", attempts)
                    raise
                sleep_for = base_backoff * (2 ** (attempts - 1))
                sleep_for += jitter * sleep_for
                _metrics.HTTP_RETRY_ATTEMPTS.labels(**_metrics.label_ctx(), method=method, host=host_label).inc()
                time.sleep(sleep_for)
                continue
            status = getattr(resp, "status_code", None)
            if is_circuit_breaker_enabled() and br_inst is not None:
                if status is None or int(status) >= 500:
                    br_inst._update_state_on_failure()
                    _metrics.CIRCUIT_BREAKER_REQUESTS.labels(
                        **_metrics.label_ctx(), circuit=br_host, result="failure"
                    ).inc()
                else:
                    br_inst._update_state_on_success()
                    _metrics.CIRCUIT_BREAKER_REQUESTS.labels(
                        **_metrics.label_ctx(), circuit=br_host, result="success"
                    ).inc()
                state_val = 1.0 if br_inst.state == "open" else (0.5 if br_inst.state == "half_open" else 0.0)
                _metrics.CIRCUIT_BREAKER_STATE.labels(**_metrics.label_ctx(), circuit=br_host).set(state_val)
            if status in statuses_to_retry and attempts < max_attempts and _is_retry_enabled():
                sleep_for = base_backoff * (2 ** (attempts - 1))
                sleep_for += jitter * sleep_for
                _metrics.HTTP_RETRY_ATTEMPTS.labels(**_metrics.label_ctx(), method=method, host=host_label).inc()
                time.sleep(sleep_for)
                span.set_attribute("retry.scheduled_backoff", sleep_for)
                continue
            span.set_attribute("retry.give_up", False)
            span.set_attribute("retry.final_attempts", attempts)
            return resp


from .retry_config import resolve_retry_attempts  # noqa: E402


def retrying_post(
    url: str,
    *,
    json_payload: Any | None = None,
    headers: dict[str, str] | None = None,
    files: dict[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    max_attempts: int | None = None,
    request_callable: Callable[..., Any] | None = None,
    **kwargs: Any,
):
    effective_max = max_attempts if max_attempts is not None else resolve_retry_attempts()
    if _is_retry_enabled():
        if request_callable is None:
            request_callable = lambda u, **_: resilient_post(  # noqa: E731
                u,
                json_payload=json_payload,
                headers=headers,
                files=files,
                timeout_seconds=timeout_seconds,
            )
        return http_request_with_retry(
            "POST",
            url,
            request_callable=request_callable,
            max_attempts=effective_max,
        )
    return resilient_post(
        url,
        json_payload=json_payload,
        headers=headers,
        files=files,
        timeout_seconds=timeout_seconds,
    )


def retrying_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    stream: bool | None = None,
    max_attempts: int | None = None,
    request_callable: Callable[..., Any] | None = None,
    **kwargs: Any,
):
    effective_max = max_attempts if max_attempts is not None else resolve_retry_attempts()
    if _is_retry_enabled():
        if request_callable is None:
            request_callable = lambda u, **_: resilient_get(  # noqa: E731
                u,
                params=params,
                headers=headers,
                timeout_seconds=timeout_seconds,
                stream=stream,
            )
        return http_request_with_retry(
            "GET",
            url,
            request_callable=request_callable,
            max_attempts=effective_max,
        )
    return resilient_get(
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        stream=stream,
    )


def is_circuit_breaker_enabled() -> bool:
    """Enable circuit breakers for critical external services by default.

    Circuit breakers protect against cascading failures and provide graceful
    degradation when external services are unavailable.
    """
    # Check explicit environment variable override
    raw = os.getenv("ENABLE_HTTP_CIRCUIT_BREAKER")
    if raw is not None:
        return str(raw).lower() in {"1", "true", "yes", "on"}

    # Default: enable circuit breakers for production environments
    # This provides resilience against external service failures
    return os.getenv("ENV") in {"production", "prod"} or os.getenv("CREW_ENV") == "production"


__all__ = [
    "get_circuit_breaker_status",
    "http_request_with_retry",
    "is_circuit_breaker_enabled",
    "is_retry_enabled",
    "reset_circuit_breakers",
    "retrying_get",
    "retrying_post",
]
