"""Thin wrappers around requests to enforce timeouts and tracing."""

from __future__ import annotations

import inspect
import os
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

import requests

from .config import REQUEST_TIMEOUT_SECONDS


if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


@runtime_checkable
class ResponseLike(Protocol):
    status_code: int
    text: str

    def json(self) -> Any: ...
    def raise_for_status(self) -> Any: ...
    def iter_content(self, chunk_size: int = ...) -> Any: ...


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


_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
    return _SESSION


def _is_pooling_enabled() -> bool:
    raw = os.getenv("ENABLE_CONNECTION_POOLING")
    return bool(raw) and str(raw).lower() in {"1", "true", "yes", "on"}


def resilient_post(
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
) -> ResponseLike:
    if request_fn is None:
        request_fn = _get_session().post if _is_pooling_enabled() else requests.post
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.post") as span:
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", "POST")
        try:
            return cast(
                "ResponseLike",
                request_fn(
                    url,
                    json=json_payload,
                    headers=headers,
                    files=files,
                    timeout=timeout_seconds,
                ),
            )
        except TypeError as exc:
            if allow_legacy_timeout_fallback and "unexpected keyword argument" in str(exc):
                return cast(
                    "ResponseLike",
                    request_fn(
                        url,
                        json=json_payload,
                        headers=headers,
                        files=files,
                    ),
                )
            raise


def resilient_get(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
    stream: bool | None = None,
) -> ResponseLike:
    if request_fn is None:
        request_fn = _get_session().get if _is_pooling_enabled() else requests.get
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.get") as span:
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", "GET")
        try:
            return cast(
                "ResponseLike",
                request_fn(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout_seconds,
                    stream=stream,
                ),
            )
        except TypeError as exc:
            if allow_legacy_timeout_fallback and "unexpected keyword argument" in str(exc):
                try:
                    sig = inspect.signature(request_fn)
                    allowed = set(sig.parameters.keys())
                except (TypeError, ValueError, AttributeError):
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
                return cast("ResponseLike", request_fn(url, **retry_kwargs))
            raise


def resilient_delete(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: Callable[..., Any] | None = None,
) -> ResponseLike:
    if request_fn is None:
        # Use pooled session when enabled
        request_fn = _get_session().delete if _is_pooling_enabled() else requests.delete
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.delete") as span:
        span.set_attribute("http.url", url)
        span.set_attribute("http.method", "DELETE")
        try:
            return cast(
                "ResponseLike",
                request_fn(
                    url,
                    params=params,
                    headers=headers,
                    timeout=timeout_seconds,
                ),
            )
        except TypeError as exc:
            if allow_legacy_timeout_fallback and "unexpected keyword argument" in str(exc):
                try:
                    sig = inspect.signature(request_fn)
                    allowed = set(sig.parameters.keys())
                except (TypeError, ValueError, AttributeError):
                    allowed = {"url"}
                retry_kwargs: dict[str, Any] = {}
                if "params" in allowed and params is not None:
                    retry_kwargs["params"] = params
                if "headers" in allowed and headers is not None:
                    retry_kwargs["headers"] = headers
                if "timeout" in allowed:
                    retry_kwargs["timeout"] = timeout_seconds
                return cast("ResponseLike", request_fn(url, **retry_kwargs))
            raise


__all__ = ["ResponseLike", "resilient_delete", "resilient_get", "resilient_post"]
