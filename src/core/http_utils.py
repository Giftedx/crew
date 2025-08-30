"""HTTP helper utilities.

Centralized helpers for:
- URL validation (public HTTPS host, reject private/reserved IPs)
- Resilient POST/GET wrappers with optional fallback for legacy monkeypatched tests
- Feature-flagged retry helpers with metrics and tracing
- Standard timeout constants

Import ordering: docstring precedes future import (Ruff E402), then stdlib,
third-party, and local imports.
"""

from __future__ import annotations

import inspect
import ipaddress
import json
import logging
import os
import time
import warnings
from collections.abc import Callable, Mapping
from datetime import date
from typing import Any, Protocol, TypeVar, cast, runtime_checkable
from urllib.parse import urlparse

import requests

from obs import metrics as _metrics


# ---------------------------------------------------------------------------
# Lightweight structural protocol for responses (requests.Response compatible)
# ---------------------------------------------------------------------------
@runtime_checkable
class ResponseLike(Protocol):  # minimal surface we rely upon across helpers
    status_code: int
    text: str
    def json(self) -> Any: ...  # pragma: no cover - structural only
    def raise_for_status(self) -> Any: ...  # pragma: no cover
    def iter_content(self, chunk_size: int = ...) -> Any: ...  # streaming downloads

RResp = TypeVar("RResp", bound=ResponseLike)


class _TracerProtocol(Protocol):  # minimal structural contract we rely on
    def start_as_current_span(self, *args: Any, **kwargs: Any): ...  # noqa: D401,E701 - concise protocol

class _TraceAPIProtocol(Protocol):
    def get_tracer(self, *args: Any, **kwargs: Any) -> _TracerProtocol: ...  # noqa: D401,E701

try:  # optional dependency import – unify to a single symbol 'trace'
    from opentelemetry import trace  # pragma: no cover
except Exception:  # pragma: no cover - fallback when opentelemetry missing
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
# NOTE: metrics import intentionally placed with other third-party/local imports so
# that later references do not trigger E402. We import the module (not individual
# counters) so test-time resets that rebind metric globals propagate here.

# Exported constants
REQUEST_TIMEOUT_SECONDS = 15
HTTP_SUCCESS_NO_CONTENT = 204
HTTP_RATE_LIMITED = 429
DEFAULT_RATE_LIMIT_RETRY = 60
DEFAULT_HTTP_RETRY_ATTEMPTS = 3

__all__ = [
    "REQUEST_TIMEOUT_SECONDS",
    "HTTP_SUCCESS_NO_CONTENT",
    "HTTP_RATE_LIMITED",
    "DEFAULT_RATE_LIMIT_RETRY",
    "DEFAULT_HTTP_RETRY_ATTEMPTS",
    "validate_public_https_url",
    "resilient_post",
    "resilient_get",
    "http_request_with_retry",
    "retrying_post",
    "retrying_get",
    "is_retry_enabled",
]


def validate_public_https_url(url: str) -> str:
    """Validate a URL is HTTPS and not a private / loopback IP.

    Accepts hostnames (DNS) or globally routable IPs. Raises ``ValueError``
    for invalid or insecure values.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":  # security requirement
        raise ValueError("URL must use https")
    if not parsed.hostname:
        raise ValueError("URL must include a host")
    host = parsed.hostname
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Host is a DNS name; allow (resolution security handled elsewhere)
        return url
    if not ip.is_global:
        raise ValueError("IP must be globally routable")
    return url


_patched_resilient_post = globals().get("resilient_post")
def resilient_post(  # noqa: PLR0913 - explicit keyword params surface HTTP semantics clearly
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
) -> ResponseLike:  # noqa: PLR0913 - explicit keyword params surface HTTP semantics clearly
    """POST wrapper adding timeout & legacy monkeypatch fallback.

    If a test monkeypatch provides a simplified signature (missing ``timeout``)
    we detect the resulting ``TypeError`` and retry without the argument to
    preserve existing lightweight fixtures.
    """
    if request_fn is None:  # defer binding so tests monkeypatching requests.post take effect
        request_fn = requests.post
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.post") as span:
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", "POST")
        try:
            return cast(ResponseLike, request_fn(
                url,
                json=json_payload,
                headers=headers,
                files=files,
                timeout=timeout_seconds,
            ))
        except TypeError as exc:
            if allow_legacy_timeout_fallback and "unexpected keyword argument" in str(exc):
                return cast(ResponseLike, request_fn(
                    url,
                    json=json_payload,
                    headers=headers,
                    files=files,
                ))
            raise


_patched_resilient_get = globals().get("resilient_get")
def resilient_get(  # noqa: PLR0913 - explicit knobs aid test monkeypatch ergonomics
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
    stream: bool | None = None,
) -> ResponseLike:  # noqa: PLR0913 - explicit knobs aid test monkeypatch ergonomics
    """GET wrapper mirroring resilient_post lazy binding & legacy fallback.

    Provides consistent timeout handling and supports fixtures that omit
    the ``timeout`` argument. ``stream`` is passed through when provided
    (used for large file downloads like Discord attachments)."""
    if request_fn is None:
        request_fn = requests.get
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.get") as span:
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", "GET")
        try:
            return cast(ResponseLike, request_fn(
                url,
                params=params,
                headers=headers,
                timeout=timeout_seconds,
                stream=stream,
            ))
        except TypeError as exc:
            if allow_legacy_timeout_fallback and "unexpected keyword argument" in str(exc):
                try:
                    sig = inspect.signature(request_fn)
                    allowed = set(sig.parameters.keys())
                except Exception:  # pragma: no cover - very unlikely path
                    allowed = {"url"}
                retry_kwargs: dict[str, Any] = {}
                if "params" in allowed and params is not None:
                    retry_kwargs["params"] = params
                if "headers" in allowed and headers is not None:
                    retry_kwargs["headers"] = headers
                if "timeout" in allowed:
                    retry_kwargs["timeout"] = timeout_seconds
                if "stream" in allowed and stream is not None:
                    retry_kwargs["stream"] = stream
                return cast(ResponseLike, request_fn(url, **retry_kwargs))
            raise

# If the module was reloaded after an external test monkeypatch (function defined outside this module)
# preserve the patched version so tests that patch then reload still exercise their stub. This is a
# narrow compatibility shim for the test pattern `monkeypatch.setattr('core.http_utils.resilient_get', ...)` followed
# by `importlib.reload(core.http_utils)`, which would normally overwrite the patched attribute.
if _patched_resilient_post and getattr(_patched_resilient_post, "__module__", __name__) != __name__:
    resilient_post = _patched_resilient_post  # noqa: F401
if _patched_resilient_get and getattr(_patched_resilient_get, "__module__", __name__) != __name__:
    resilient_get = _patched_resilient_get  # noqa: F401


_HTTP_RETRY_LEGACY_REMOVAL = date.fromisoformat("2025-12-31")
_DEPRECATION_LOG_EMITTED: dict[str, bool] = {}


def _is_retry_enabled() -> bool:
    """Return True if HTTP retry logic is enabled.

    Supports both the new unified flag ``ENABLE_HTTP_RETRY`` and the legacy
    ``ENABLE_ANALYSIS_HTTP_RETRY`` (deprecated). The unified flag takes
    precedence when both are set. A future cleanup will remove the legacy
    flag once all callers are migrated.

    Deprecation timeline:
        - Introduced unified flag: 2025-Q2
        - Dual-support grace period ends: 2025-12-31 (planned)
        - Removal target (subject to CHANGELOG confirmation): first minor
          release after grace period. After removal, only ``ENABLE_HTTP_RETRY``
          (or settings-driven equivalent) will be honored and references to
          ``ENABLE_ANALYSIS_HTTP_RETRY`` will raise a ``KeyError`` in tests.
    """
    if os.getenv("ENABLE_HTTP_RETRY"):
        return True
    if os.getenv("ENABLE_ANALYSIS_HTTP_RETRY"):
        if date.today() > _HTTP_RETRY_LEGACY_REMOVAL:
            raise RuntimeError(
                "ENABLE_ANALYSIS_HTTP_RETRY exceeded deprecation window (removal after 2025-12-31). "
                "Remove this variable and set ENABLE_HTTP_RETRY if retries are desired."
            )
        warnings.warn(
            "ENABLE_ANALYSIS_HTTP_RETRY is deprecated; use ENABLE_HTTP_RETRY instead (grace until 2025-12-31).",
            DeprecationWarning,
            stacklevel=2,
        )
        # Structured one-time info log for observability dashboards
        if not _DEPRECATION_LOG_EMITTED.get("ENABLE_ANALYSIS_HTTP_RETRY"):
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
    """Public helper exposing consolidated retry flag state.

    Preferred over ad-hoc environment variable checks. Internally delegates
    to the legacy/env compatible ``_is_retry_enabled`` until all call sites
    migrate to settings-driven configuration.
    """
    return _is_retry_enabled()


def http_request_with_retry(  # noqa: PLR0913 - retry behaviour requires multiple tuned parameters
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
) -> Any:  # noqa: PLR0913 - retry behaviour requires multiple tuned parameters
    """Feature-flagged generic HTTP retry with exponential backoff.

    Retries on network exceptions and selected status codes while retry
    feature flag(s) are enabled (``ENABLE_HTTP_RETRY`` preferred, legacy
    ``ENABLE_ANALYSIS_HTTP_RETRY`` still honored). Backoff doubles each
    attempt (base * 2^(n-1)) with proportional jitter.
    """
    tracer = trace.get_tracer(__name__)
    attempts = 0
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
                if attempts >= max_attempts or not _is_retry_enabled():
                    if attempts > 1:  # count only retries (not first attempt) on give up
                        _metrics.HTTP_RETRY_GIVEUPS.labels(**_metrics.label_ctx(), method=method).inc()
                    if on_give_up:
                        on_give_up(exc, attempts)
                    span.set_attribute("retry.give_up", True)
                    span.set_attribute("retry.final_attempts", attempts)
                    raise
                # Treat connection refused / DNS errors with shorter initial backoff
                is_conn_refused = isinstance(exc, requests.ConnectionError) and "Connection refused" in str(exc)
                effective_base = base_backoff * (0.3 if is_conn_refused else 1.0)
                sleep_for = effective_base * (2 ** (attempts - 1))
                sleep_for += jitter * sleep_for
                _metrics.HTTP_RETRY_ATTEMPTS.labels(**_metrics.label_ctx(), method=method).inc()
                time.sleep(sleep_for)
                continue
            status = getattr(resp, "status_code", None)
            if (
                status in statuses_to_retry
                and attempts < max_attempts
                and _is_retry_enabled()
            ):
                sleep_for = base_backoff * (2 ** (attempts - 1))
                sleep_for += jitter * sleep_for
                _metrics.HTTP_RETRY_ATTEMPTS.labels(**_metrics.label_ctx(), method=method).inc()
                time.sleep(sleep_for)
                span.set_attribute("retry.scheduled_backoff", sleep_for)
                continue
            span.set_attribute("retry.give_up", False)
            span.set_attribute("retry.final_attempts", attempts)
            return resp


def retrying_post(  # noqa: PLR0913 - convenience wrapper exposes key retry parameters
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_HTTP_RETRY_ATTEMPTS,
    **kwargs: Any,
) :  # noqa: PLR0913 - convenience wrapper exposes key retry parameters
    """Convenience helper: resilient_post wrapped in feature-flagged retry.

    Falls back to single attempt if retry flag disabled.
    """
    if _is_retry_enabled():
        return http_request_with_retry(
            "POST",
            url,
            request_callable=lambda u, **_: resilient_post(
                u,
                json_payload=json_payload,
                headers=headers,
                files=files,
                timeout_seconds=timeout_seconds,
            ),
            max_attempts=max_attempts,
        )
    return resilient_post(
        url,
        json_payload=json_payload,
        headers=headers,
        files=files,
        timeout_seconds=timeout_seconds,
    )


def retrying_get(  # noqa: PLR0913 - explicit parameters preferred over opaque options dict
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    stream: bool | None = None,
    max_attempts: int = DEFAULT_HTTP_RETRY_ATTEMPTS,
    **kwargs: Any,
) :  # noqa: PLR0913 - explicit parameters preferred over opaque options dict
    """Convenience helper: resilient_get wrapped in feature-flagged retry."""
    if _is_retry_enabled():
        return http_request_with_retry(
            "GET",
            url,
            request_callable=lambda u, **_: resilient_get(
                u,
                params=params,
                headers=headers,
                timeout_seconds=timeout_seconds,
                stream=stream,
            ),
            max_attempts=max_attempts,
        )
    return resilient_get(
        url,
        params=params,
        headers=headers,
        timeout_seconds=timeout_seconds,
        stream=stream,
    )

