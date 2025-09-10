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

from .error_handling import log_error

try:
    # Import settings lazily/optionally to avoid requiring pydantic during
    # lightweight unit tests that only exercise HTTP helpers.
    from core.settings import get_settings
except (ImportError, ModuleNotFoundError) as e:  # More specific exception types
    # Log the import failure for debugging
    from .error_handling import log_error

    log_error(e, message="Failed to import settings module, using fallback", context={"module": "core.settings"})

    def get_settings():  # type: ignore[misc]
        class _S:
            enable_http_cache = False
            http_cache_ttl_seconds = 300
            rate_limit_redis_url = None

        return _S()


from obs import metrics as _metrics

try:  # optional cache
    from core.cache.redis_cache import RedisCache as _RedisCache
except Exception:  # pragma: no cover
    _RedisCache = None  # type: ignore[assignment,misc]

# Import secure config for centralized settings
_config: Any | None = None
try:
    from .secure_config import get_config

    _config = get_config()
except ImportError:
    # Fallback for circular import during initialization
    _config = None


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


# Exported constants - use function for dynamic timeout resolution
def get_request_timeout() -> int:
    """Get HTTP request timeout, preferring environment override.

    Precedence:
    1) Environment variable `HTTP_TIMEOUT`
    2) Secure config setting (if available)
    3) Default of 15 seconds
    """
    # 1) Raw environment (ensures patched env in tests takes immediate effect)
    raw = os.getenv("HTTP_TIMEOUT")
    if raw is not None and str(raw).strip() != "":
        try:
            return int(raw)
        except ValueError:
            ...
    # 2) Secure config
    if _config and getattr(_config, "http_timeout", None):
        try:
            return int(_config.http_timeout)
        except Exception:
            ...
    return 15


# Backward compatibility constant
REQUEST_TIMEOUT_SECONDS = get_request_timeout()
HTTP_SUCCESS_NO_CONTENT = 204
HTTP_RATE_LIMITED = 429
DEFAULT_RATE_LIMIT_RETRY = 60
DEFAULT_HTTP_RETRY_ATTEMPTS = 3

__all__ = [
    "REQUEST_TIMEOUT_SECONDS",
    "get_request_timeout",
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
    "resolve_retry_attempts",
]


def validate_public_https_url(url: str) -> str:
    """Validate a URL is HTTPS and not a private / loopback IP.

    Accepts hostnames (DNS) or globally routable IPs. Raises ``ValueError``
    for invalid or insecure values.
    """
    # Check for empty or invalid URL first
    if not url or not isinstance(url, str) or not url.strip():
        raise ValueError(f"URL cannot be empty or None (got: '{url}')")

    parsed = urlparse(url)

    if parsed.scheme != "https":  # security requirement
        raise ValueError(f"URL must use https (got: '{parsed.scheme}' for URL: '{url}')")
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
            return cast(
                ResponseLike,
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
                    ResponseLike,
                    request_fn(
                        url,
                        json=json_payload,
                        headers=headers,
                        files=files,
                    ),
                )
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
            return cast(
                ResponseLike,
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
                except (TypeError, ValueError, AttributeError) as e:  # More specific exception types
                    # Handle signature inspection errors
                    log_error(
                        e,
                        message="Failed to inspect request function signature for fallback",
                        context={"url": url, "function": getattr(request_fn, "__name__", "unknown")},
                    )
                    allowed = {"url"}  # Minimal fallback
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
    # 1) Explicit environment variable (respects patched env in tests)
    raw_env = os.getenv("ENABLE_HTTP_RETRY")
    if raw_env is not None:
        return str(raw_env).lower() in ("1", "true", "yes", "on")

    # 2) Legacy flag support (deprecated)
    legacy_flag = os.getenv("ENABLE_ANALYSIS_HTTP_RETRY")

    # Handle string values from environment variables
    if legacy_flag and str(legacy_flag).lower() in ("1", "true", "yes", "on"):
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
            # Extract host label for metrics (low-cardinality: netloc only)
            try:
                host_label = urlparse(url).hostname or "unknown"
            except Exception:
                host_label = "unknown"
            try:
                resp = request_callable(url, **call_kwargs)
            except requests.RequestException as exc:
                span.set_attribute("error", True)
                span.set_attribute("exception.type", exc.__class__.__name__)
                if attempts >= max_attempts or not _is_retry_enabled():
                    if attempts > 1:  # count only retries (not first attempt) on give up
                        _metrics.HTTP_RETRY_GIVEUPS.labels(**_metrics.label_ctx(), method=method, host=host_label).inc()
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
                _metrics.HTTP_RETRY_ATTEMPTS.labels(**_metrics.label_ctx(), method=method, host=host_label).inc()
                time.sleep(sleep_for)
                continue
            status = getattr(resp, "status_code", None)
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


def retrying_post(  # noqa: PLR0913 - convenience wrapper exposes key retry parameters
    url: str,
    *,
    json_payload: Any | None = None,
    headers: Mapping[str, str] | None = None,
    files: Mapping[str, Any] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    max_attempts: int | None = None,
    request_callable: Callable[..., Any] | None = None,
    **kwargs: Any,
):  # noqa: PLR0913 - convenience wrapper exposes key retry parameters
    """Convenience helper: resilient_post wrapped in feature-flagged retry.

    Falls back to single attempt if retry flag disabled.

    If ``max_attempts`` is ``None`` we resolve it via ``resolve_retry_attempts`` which
    consults (in order) explicit call override (not provided here), config, environment,
    then the library default constant.
    """
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


def retrying_get(  # noqa: PLR0913 - explicit parameters preferred over opaque options dict
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    stream: bool | None = None,
    max_attempts: int | None = None,
    request_callable: Callable[..., Any] | None = None,
    **kwargs: Any,
):  # noqa: PLR0913 - explicit parameters preferred over opaque options dict
    """Convenience helper: resilient_get wrapped in feature-flagged retry.

    ``max_attempts`` of ``None`` triggers dynamic resolution (config/env/default).
    """
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


# ---------------------------------------------------------------------------
# Safe GET cache (idempotent endpoints only)
# ---------------------------------------------------------------------------
_MEM_HTTP_CACHE: dict[str, tuple[float, str, int]] = {}


class _CachedResponse:
    def __init__(self, text: str, status_code: int) -> None:
        self.text = text
        self.status_code = status_code

    def json(self) -> Any:
        try:
            return json.loads(self.text)
        except Exception:
            return {}

    def raise_for_status(self) -> Any:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")
        return None

    def iter_content(self, chunk_size: int = 8192) -> Any:  # pragma: no cover - not used for cached responses
        yield self.text.encode("utf-8")


def _cache_key(url: str, params: Mapping[str, Any] | None) -> str:
    if not params:
        return url
    try:
        items = sorted((str(k), str(v)) for k, v in params.items())
    except Exception:
        items = []
    return url + "?" + "&".join(f"{k}={v}" for k, v in items)


def cached_get(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: int | None = None,
    ttl_seconds: int | None = None,
) -> ResponseLike:
    """Idempotent GET with TTL cache.

    Uses Redis when configured; otherwise in-memory. Only caches non-streaming,
    successful (2xx) responses. If cache disabled via settings, behaves like
    ``resilient_get``.
    """
    settings = get_settings()
    if not getattr(settings, "enable_http_cache", False):
        return resilient_get(
            url,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds or REQUEST_TIMEOUT_SECONDS,
            stream=False,
        )
    key = _cache_key(url, params)
    now = time.time()
    ttl = int(ttl_seconds if ttl_seconds is not None else getattr(settings, "http_cache_ttl_seconds", 300) or 300)
    # Try Redis first
    redis_url = getattr(settings, "rate_limit_redis_url", None)
    if _RedisCache is not None and redis_url:
        try:
            rc = _RedisCache(url=str(redis_url), namespace="http", ttl=ttl)
            raw = rc.get_str(key)
            if raw:
                try:
                    obj = json.loads(raw)
                    return _CachedResponse(text=str(obj.get("text", "")), status_code=int(obj.get("status", 200)))
                except Exception:
                    ...
            resp = resilient_get(
                url, params=params, headers=headers, timeout_seconds=timeout_seconds or REQUEST_TIMEOUT_SECONDS
            )
            if 200 <= resp.status_code < 300:
                rc.set_str(key, json.dumps({"status": resp.status_code, "text": getattr(resp, "text", "")}))
            return resp
        except Exception:
            ...
    # In-memory fallback
    exp, text, status = _MEM_HTTP_CACHE.get(key, (0.0, "", 0))
    if exp > now:
        return _CachedResponse(text=text, status_code=status)
    resp = resilient_get(
        url, params=params, headers=headers, timeout_seconds=timeout_seconds or REQUEST_TIMEOUT_SECONDS
    )
    if 200 <= resp.status_code < 300:
        _MEM_HTTP_CACHE[key] = (now + ttl, getattr(resp, "text", ""), int(resp.status_code))
    return resp


# ---------------------------------------------------------------------------
# Retry attempt resolution (precedence logic)
# ---------------------------------------------------------------------------
from pathlib import Path  # placed after earlier functions to avoid E402 reordering churn

try:
    # Optional: tenant-aware retry override
    from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
except (ImportError, ModuleNotFoundError) as e:  # More specific exception types
    # Log the import failure for debugging
    from .error_handling import log_error

    log_error(
        e,
        message="Failed to import tenancy context, using fallback",
        context={"module": "ultimate_discord_intelligence_bot.tenancy.context"},
    )

    def current_tenant():  # type: ignore[misc]
        return None


# Retry config cache: may be force-reset to None by tests; treat None as empty sentinel.
_RETRY_CONFIG_CACHE: dict[str, dict[str, int | None]] | None = {}
_MAX_REASONABLE_HTTP_RETRY_ATTEMPTS = 20  # guard rails – avoid unbounded backoff explosions


def _load_retry_config() -> dict[str, int | None]:  # pragma: no cover - trivial IO glue
    """Best-effort parse of optional config/retry.yaml.

    We intentionally avoid introducing a YAML parser dependency; instead we support
    a single line of the form ``max_attempts: <int>``. Additional lines are ignored.
    """
    # Derive a cache key per-tenant (tenant_id or 'global'). This ensures tenant override
    # tests see their specific retry.yaml without being masked by a previously cached
    # global value loaded earlier in the test session.
    global _RETRY_CONFIG_CACHE  # ensure we can read/update sentinel safely
    try:
        ctx = current_tenant()
    except Exception:
        ctx = None
    tenant_id = getattr(ctx, "tenant_id", None) or "global"
    cache = _RETRY_CONFIG_CACHE
    if cache is None:
        cache = {}
        # Do not assign back yet; only persist after successful load below.
    if tenant_id in cache:
        return cache[tenant_id]
    root = Path(__file__).resolve().parents[2]  # project root (.. / .. from src/core/file.py)
    cfg_paths: list[Path] = []
    # 1) tenant-specific override if TenantContext present
    # ctx already resolved above
    if ctx and getattr(ctx, "tenant_id", None):
        cfg_paths.append(root / "tenants" / ctx.tenant_id / "retry.yaml")
    # 2) global fallback
    cfg_paths.append(root / "config" / "retry.yaml")
    max_attempts: int | None = None
    try:
        for cfg_path in cfg_paths:
            if cfg_path.exists():
                for line in cfg_path.read_text(encoding="utf-8").splitlines():
                    if "max_attempts:" in line:
                        try:
                            cand = int(line.split(":", 1)[1].strip())
                            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
                                max_attempts = cand
                        except ValueError:
                            pass
                        break
            if max_attempts is not None:
                break
    except Exception:  # safety – config loading should never hard fail retries
        max_attempts = None
    if _RETRY_CONFIG_CACHE is None:
        _RETRY_CONFIG_CACHE = {}
    _RETRY_CONFIG_CACHE[tenant_id] = {"max_attempts": max_attempts}
    return _RETRY_CONFIG_CACHE[tenant_id]


def resolve_retry_attempts(call_arg: int | None = None) -> int:
    """Resolve effective retry attempts with explicit precedence.

    Precedence (highest first):
        1. Explicit *call_arg* (sanitized to reasonable range)
        2. Value in ``config/retry.yaml`` (key: ``max_attempts``)
        3. Environment variable ``RETRY_MAX_ATTEMPTS``
        4. Library constant ``DEFAULT_HTTP_RETRY_ATTEMPTS``

    Any non-positive / out-of-range integers fall back to the next source.
    """
    # 1. Explicit argument
    if call_arg is not None:
        if 1 <= call_arg <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
            return call_arg
        logging.getLogger(__name__).warning(
            "Ignoring out-of-range explicit retry attempts (%s); falling back.", call_arg
        )

    # 2. Config file (cached)
    cfg = _load_retry_config()
    cfg_val = cfg.get("max_attempts") if cfg else None
    if isinstance(cfg_val, int) and 1 <= cfg_val <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
        return cfg_val

    # 3. Environment variable (live read to respect test monkeypatch)
    raw_env = os.getenv("RETRY_MAX_ATTEMPTS")
    if raw_env is not None and raw_env.strip():
        try:
            cand = int(raw_env)
            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
                return cand
        except ValueError:
            logging.getLogger(__name__).warning("Invalid RETRY_MAX_ATTEMPTS=%s; falling back to defaults", raw_env)

    # 4. Secure config object (may reflect startup value; lower precedence than live env)
    env_val = getattr(_config, "retry_max_attempts", None) if _config else None
    if env_val is not None:
        try:
            cand = int(env_val)
            if 1 <= cand <= _MAX_REASONABLE_HTTP_RETRY_ATTEMPTS:
                return cand
        except ValueError:
            pass

    # 5. Fallback constant
    return DEFAULT_HTTP_RETRY_ATTEMPTS


# ---------------------------------------------------------------------------
# Test helper / external hook (used by tests to ensure clean precedence state)
# ---------------------------------------------------------------------------
def reset_retry_config_cache() -> None:
    """Reset the internal retry config cache.

    Tests previously mutated the private ``_RETRY_CONFIG_CACHE`` directly to ``None``
    which caused TypeErrors when membership tests were performed. This helper
    provides a supported reset path and shields the loader from ``None`` states.
    """
    global _RETRY_CONFIG_CACHE  # noqa: PLW0603
    _RETRY_CONFIG_CACHE = {}
