"""Compatibility facade for legacy imports.

This module used to contain a large monolithic implementation. It now
exposes a stable facade that forwards to the modular ``core.http``
implementation while preserving monkeypatch seams relied upon by tests
(`get_settings`, `_RedisCache`, `_load_retry_config`, and `time`). It also
wraps selected functions to ensure environment-driven defaults (like
HTTP_TIMEOUT) are re-resolved after reloads and that facade-level monkeypatches
affect behavior (e.g. retrying_* uses facade `resilient_*`).
"""

from __future__ import annotations

import contextlib
import random as random
import time as time
from pathlib import Path

import requests as requests

from . import requests_wrappers as _rq
from . import retry_config as _retry_cfg
from .config import (
    DEFAULT_HTTP_RETRY_ATTEMPTS,
    DEFAULT_RATE_LIMIT_RETRY,
    HTTP_RATE_LIMITED,
    HTTP_SUCCESS_NO_CONTENT,
    REQUEST_TIMEOUT_SECONDS,
    get_request_timeout,
)
from .retry import is_circuit_breaker_enabled, is_retry_enabled
from .validators import validate_public_https_url


try:
    from platform.cache.redis_cache import RedisCache as _RedisCache
except Exception:
    _RedisCache = None
try:
    from app.config.settings import Settings

    def get_settings():
        return Settings()
except Exception:

    class _FallbackSettings:
        enable_http_cache: bool = False
        http_cache_ttl_seconds: int = 300
        enable_http_negative_cache: bool = False
        rate_limit_redis_url: str | None = None

    def get_settings():
        return _FallbackSettings()


# Capture any pre-existing monkeypatched functions after imports but before defining new ones
_patched_resilient_post = globals().get("resilient_post")
_patched_resilient_get = globals().get("resilient_get")


def _load_retry_config() -> dict[str, int | None]:
    try:
        return _retry_cfg._load_retry_config()
    except Exception:
        return {"max_retries": 3, "backoff_factor": 1.0, "retry_statuses": (429, 500, 502, 503, 504)}


_MEM_HTTP_CACHE: dict[str, tuple[float, str, int]] = {}
_MEM_HTTP_NEG_CACHE: dict[str, object] = {}
_config = None
_RETRY_CONFIG_CACHE: dict[str, dict[str, int | None]] | None = {}


def resilient_post(
    url: str,
    *,
    json_payload: object | None = None,
    headers: dict[str, str] | None = None,
    files: dict[str, object] | None = None,
    timeout_seconds: int | None = None,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: object | None = None,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    return _rq.resilient_post(
        url,
        json_payload=json_payload,
        headers=headers,
        files=files,
        timeout_seconds=eff_timeout,
        allow_legacy_timeout_fallback=allow_legacy_timeout_fallback,
        request_fn=request_fn,
    )


def resilient_get(
    url: str,
    *,
    params: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: object | None = None,
    stream: bool | None = None,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    return _rq.resilient_get(
        url,
        params=params or None,
        headers=headers,
        timeout_seconds=eff_timeout,
        allow_legacy_timeout_fallback=allow_legacy_timeout_fallback,
        request_fn=request_fn,
        stream=stream,
    )


def resilient_delete(
    url: str,
    *,
    params: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    allow_legacy_timeout_fallback: bool = True,
    request_fn: object | None = None,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    return _rq.resilient_delete(
        url,
        params=params or None,
        headers=headers,
        timeout_seconds=eff_timeout,
        allow_legacy_timeout_fallback=allow_legacy_timeout_fallback,
        request_fn=request_fn,
    )


def http_request_with_retry(
    method: str,
    url: str,
    *,
    request_callable,
    statuses_to_retry: tuple[int, ...] = (500, 502, 503, 504, HTTP_RATE_LIMITED),
    max_attempts: int = DEFAULT_HTTP_RETRY_ATTEMPTS,
    base_backoff: float = 0.5,
    jitter: float = 0.05,
    on_give_up=None,
    **call_kwargs,
):
    """Facade retry with backoff compatible with legacy tests.

    Differences from core.http.retry.http_request_with_retry:
    - When encountering requests.ConnectionError we apply a 0.3 scaling factor
      to the computed backoff (historical behavior relied upon by tests).
    - Sleeps via this module's ``time.sleep`` to allow test monkeypatching.
    - If the HTTP circuit breaker is enabled, we delegate to the modular
      implementation to enforce open/half-open semantics (short-circuiting
      when appropriate) while keeping retry/backoff behavior otherwise.
    """
    if is_circuit_breaker_enabled():
        from .http.retry import http_request_with_retry as _cb_retry

        return _cb_retry(
            method,
            url,
            request_callable=request_callable,
            statuses_to_retry=statuses_to_retry,
            max_attempts=max_attempts,
            base_backoff=base_backoff,
            jitter=jitter,
            on_give_up=on_give_up,
            **call_kwargs,
        )
    attempts = 0
    while True:
        attempts += 1
        try:
            return request_callable(url, **call_kwargs)
        except requests.RequestException as exc:
            if attempts >= max_attempts or not is_retry_enabled():
                if on_give_up:
                    with contextlib.suppress(Exception):
                        on_give_up(exc, attempts)
                raise
            sleep_for = base_backoff * 2 ** (attempts - 1)
            if isinstance(exc, requests.ConnectionError):
                sleep_for *= 0.3
            jitter_delta = random.uniform(0, jitter) if jitter else 0.0
            time.sleep(sleep_for + jitter_delta)


def resolve_retry_attempts(call_arg: int | None = None) -> int:
    """Resolve retry attempts with precedence matching tests.

    Precedence:
      1) explicit call_arg (1..20)
      2) repo-root tenants/<id>/retry.yaml or config/retry.yaml (http_utils-local cache)
      3) environment RETRY_MAX_ATTEMPTS (if not equal to library default)
      4) secure_config.retry_max_attempts (when present)
      5) DEFAULT_HTTP_RETRY_ATTEMPTS
    """
    if call_arg is not None:
        try:
            ival = int(call_arg)
            if 1 <= ival <= 20:
                return ival
        except Exception:
            pass
    try:
        loaded = _load_retry_config()
        if isinstance(loaded, dict):
            la = loaded.get("max_attempts")
            if isinstance(la, int) and 1 <= la <= 20:
                return la
    except Exception:
        pass
    try:
        tenant_id = "global"
        try:
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant as _ct

            ctx = _ct()
            if ctx and getattr(ctx, "tenant_id", None):
                tenant_id = str(ctx.tenant_id)
        except Exception:
            tenant_id = "global"
        global _RETRY_CONFIG_CACHE
        cache = _RETRY_CONFIG_CACHE or {}
        if tenant_id in cache:
            cfg_val = cache[tenant_id].get("max_attempts")
        else:
            repo_root = Path(__file__).resolve().parents[2]
            paths: list[Path] = []
            if tenant_id != "global":
                paths.append(repo_root / "tenants" / tenant_id / "retry.yaml")
            paths.append(repo_root / "config" / "retry.yaml")
            max_attempts: int | None = None
            for p in paths:
                try:
                    if p.exists():
                        for line in p.read_text(encoding="utf-8").splitlines():
                            if "max_attempts:" in line:
                                try:
                                    cand = int(line.split(":", 1)[1].strip())
                                    if 1 <= cand <= 20:
                                        max_attempts = cand
                                except Exception:
                                    pass
                                break
                    if max_attempts is not None:
                        break
                except Exception:
                    pass
            if _RETRY_CONFIG_CACHE is None:
                _RETRY_CONFIG_CACHE = {}
            _RETRY_CONFIG_CACHE[tenant_id] = {"max_attempts": max_attempts}
            cfg_val = max_attempts
        if isinstance(cfg_val, int) and 1 <= cfg_val <= 20:
            return cfg_val
    except Exception:
        pass
    import os as _os

    raw_env = _os.getenv("RETRY_MAX_ATTEMPTS")
    if raw_env is not None and raw_env.strip():
        try:
            val = int(raw_env)
            if 1 <= val <= 20 and val != DEFAULT_HTTP_RETRY_ATTEMPTS:
                return val
        except ValueError:
            ...
    global _config
    if _config is not None:
        try:
            env_val = getattr(_config, "retry_max_attempts", None)
            if env_val is not None:
                val = int(env_val)
                if 1 <= val <= 20:
                    return val
        except Exception:
            ...
    try:
        from platform.config.configuration import get_config as _get_cfg

        sc = _get_cfg()
        env_val2 = getattr(sc, "retry_max_attempts", None)
        if env_val2 is not None:
            val2 = int(env_val2)
            if 1 <= val2 <= 20:
                return val2
    except Exception:
        ...
    return DEFAULT_HTTP_RETRY_ATTEMPTS


def retrying_post(
    url: str,
    *,
    json_payload: object | None = None,
    headers: dict[str, str] | None = None,
    files: dict[str, object] | None = None,
    timeout_seconds: int | None = None,
    max_attempts: int | None = None,
    request_callable=None,
    **kwargs,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    effective_max = max_attempts if max_attempts is not None else resolve_retry_attempts()
    if is_retry_enabled():
        if request_callable is None:
            request_callable = lambda u, **__: resilient_post(
                u, json_payload=json_payload, headers=headers, files=files, timeout_seconds=eff_timeout
            )
        return http_request_with_retry(
            "POST", url, request_callable=request_callable, max_attempts=effective_max, **kwargs
        )
    return resilient_post(url, json_payload=json_payload, headers=headers, files=files, timeout_seconds=eff_timeout)


def retrying_get(
    url: str,
    *,
    params: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    stream: bool | None = None,
    max_attempts: int | None = None,
    request_callable=None,
    **kwargs,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    effective_max = max_attempts if max_attempts is not None else resolve_retry_attempts()
    if is_retry_enabled():
        if request_callable is None:
            request_callable = lambda u, **__: resilient_get(
                u, params=params, headers=headers, timeout_seconds=eff_timeout, stream=stream
            )
        return http_request_with_retry(
            "GET", url, request_callable=request_callable, max_attempts=effective_max, **kwargs
        )
    return resilient_get(url, params=params, headers=headers, timeout_seconds=eff_timeout, stream=stream)


def retrying_delete(
    url: str,
    *,
    params: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    max_attempts: int | None = None,
    request_callable=None,
    **kwargs,
):
    eff_timeout = int(timeout_seconds if timeout_seconds is not None else get_request_timeout())
    effective_max = max_attempts if max_attempts is not None else resolve_retry_attempts()
    if is_retry_enabled():
        if request_callable is None:
            request_callable = lambda u, **__: resilient_delete(
                u, params=params, headers=headers, timeout_seconds=eff_timeout
            )
        return http_request_with_retry(
            "DELETE", url, request_callable=request_callable, max_attempts=effective_max, **kwargs
        )
    return resilient_delete(url, params=params, headers=headers, timeout_seconds=eff_timeout)


def cached_get(
    url: str,
    *,
    params: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    ttl_seconds: int | None = None,
):
    """Facade caching wrapper honoring facade-level get_settings and _RedisCache.

    Mirrors ``core.http.cache.cached_get`` with dependencies routed through this
    module so tests can monkeypatch here.
    """
    import json as _json
    import time as _t

    class _CachedResponse:
        def __init__(self, text: str, status_code: int) -> None:
            self.text = text
            self.status_code = status_code

        def json(self):
            try:
                return _json.loads(self.text)
            except Exception:
                return {}

        def raise_for_status(self):
            if self.status_code >= 400:
                import requests as _requests

                raise _requests.HTTPError(f"status={self.status_code}")
            return None

        def iter_content(self, chunk_size: int = 8192):
            yield self.text.encode("utf-8")

    def _cache_key(u: str, p: dict[str, object] | None) -> str:
        if not p:
            return u
        try:
            items = sorted(((str(k), str(v)) for k, v in p.items()))
        except Exception:
            items = []
        return u + "?" + "&".join((f"{k}={v}" for k, v in items))

    settings = get_settings()
    if not getattr(settings, "enable_http_cache", False):
        return resilient_get(
            url, params=params, headers=headers, timeout_seconds=timeout_seconds or get_request_timeout(), stream=False
        )
    key = _cache_key(url, params)
    now = _t.time()
    if ttl_seconds is not None:
        ttl = int(ttl_seconds)
    else:
        ttl_from_settings = getattr(settings, "http_cache_ttl_seconds", None)
        if isinstance(ttl_from_settings, int | float) and int(ttl_from_settings) > 0:
            ttl = int(ttl_from_settings)
        else:
            try:
                from platform.cache.unified_config import get_unified_cache_config

                ttl = int(get_unified_cache_config().get_ttl_for_domain("tool"))
            except Exception:
                ttl = 300
    redis_url = getattr(settings, "rate_limit_redis_url", None)
    if _RedisCache is not None and redis_url:
        try:
            rc = _RedisCache(url=str(redis_url), namespace="http", ttl=ttl)
            raw = rc.get_str(key)
            if raw:
                try:
                    obj = _json.loads(raw)
                    return _CachedResponse(text=str(obj.get("text", "")), status_code=int(obj.get("status", 200)))
                except Exception:
                    ...
            resp = resilient_get(
                url, params=params, headers=headers, timeout_seconds=timeout_seconds or get_request_timeout()
            )
            if 200 <= getattr(resp, "status_code", 0) < 300:
                rc.set_str(key, _json.dumps({"status": resp.status_code, "text": getattr(resp, "text", "")}))
            return resp
        except Exception:
            ...
    exp_text = _MEM_HTTP_CACHE.get(key, (0.0, "", 0))
    exp, text, status = exp_text
    if exp > now:
        return _CachedResponse(text=text, status_code=status)
    if getattr(settings, "enable_http_negative_cache", False):
        neg_meta = _MEM_HTTP_NEG_CACHE.get(key)
        if isinstance(neg_meta, tuple):
            neg_exp, neg_status = neg_meta
        elif neg_meta:
            neg_exp, neg_status = (float(neg_meta), 404)
        else:
            neg_exp, neg_status = (0.0, 404)
        if neg_exp > now:
            return _CachedResponse(text="", status_code=int(neg_status))
    resp = resilient_get(url, params=params, headers=headers, timeout_seconds=timeout_seconds or get_request_timeout())
    if 200 <= getattr(resp, "status_code", 0) < 300:
        _MEM_HTTP_CACHE[key] = (_t.time() + ttl, getattr(resp, "text", ""), int(resp.status_code))
    elif getattr(settings, "enable_http_negative_cache", False) and getattr(resp, "status_code", 0) in {404, 429}:
        retry_after_s: float | None = None
        try:
            headers_obj = getattr(resp, "headers", None)
            ra = headers_obj.get("Retry-After") if headers_obj else None
            if ra:
                if str(ra).isdigit():
                    retry_after_s = float(ra)
                else:
                    from email.utils import parsedate_to_datetime

                    try:
                        dt = parsedate_to_datetime(ra)
                        retry_after_s = max(0.0, dt.timestamp() - _t.time())
                    except Exception:
                        retry_after_s = None
        except Exception:
            retry_after_s = None
        neg_ttl = min(60.0, ttl * 0.2) if retry_after_s is None else float(retry_after_s)
        _MEM_HTTP_NEG_CACHE[key] = (_t.time() + float(neg_ttl), 404)
    return resp


if _patched_resilient_post and getattr(_patched_resilient_post, "__module__", __name__) != __name__:
    resilient_post = _patched_resilient_post
if _patched_resilient_get and getattr(_patched_resilient_get, "__module__", __name__) != __name__:
    resilient_get = _patched_resilient_get
__all__ = [
    "DEFAULT_HTTP_RETRY_ATTEMPTS",
    "DEFAULT_RATE_LIMIT_RETRY",
    "HTTP_RATE_LIMITED",
    "HTTP_SUCCESS_NO_CONTENT",
    "REQUEST_TIMEOUT_SECONDS",
    "_RedisCache",
    "_load_retry_config",
    "cached_get",
    "get_request_timeout",
    "get_settings",
    "http_request_with_retry",
    "is_circuit_breaker_enabled",
    "is_retry_enabled",
    "resilient_delete",
    "resilient_get",
    "resilient_post",
    "resolve_retry_attempts",
    "retrying_delete",
    "retrying_get",
    "retrying_post",
    "time",
    "validate_public_https_url",
]
