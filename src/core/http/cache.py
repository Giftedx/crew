"""HTTP GET caching utilities (idempotent endpoints only)."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from .config import REQUEST_TIMEOUT_SECONDS
from .requests_wrappers import ResponseLike, resilient_get


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


def _cache_key(url: str, params: dict[str, Any] | None) -> str:
    if not params:
        return url
    try:
        items = sorted((str(k), str(v)) for k, v in params.items())
    except Exception:
        items = []
    return url + "?" + "&".join(f"{k}={v}" for k, v in items)


_MEM_HTTP_CACHE: dict[str, tuple[float, str, int]] = {}
_MEM_HTTP_NEG_CACHE: dict[str, object] = {}


class _SettingsLike:
    enable_http_cache: bool
    http_cache_ttl_seconds: int
    enable_http_negative_cache: bool
    rate_limit_redis_url: str | None


try:
    from core.settings import get_settings as _real_get_settings

    def get_settings() -> _SettingsLike:  # type: ignore[override]
        return _real_get_settings()  # type: ignore[return-value]
except Exception:  # pragma: no cover

    class _FallbackSettings:
        enable_http_cache: bool = False
        http_cache_ttl_seconds: int = 300
        enable_http_negative_cache: bool = False
        rate_limit_redis_url: str | None = None

    def get_settings() -> _SettingsLike:  # type: ignore[override]
        return _FallbackSettings()


try:  # optional Redis cache
    from core.cache.redis_cache import RedisCache as _RedisCache
except Exception:  # pragma: no cover
    _RedisCache = None


def cached_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_seconds: int | None = None,
    ttl_seconds: int | None = None,
) -> ResponseLike:
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
    exp_text = _MEM_HTTP_CACHE.get(key, (0.0, "", 0))
    exp, text, status = exp_text
    if exp > now:
        return _CachedResponse(text=text, status_code=status)
    # Negative cache
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
    resp = resilient_get(
        url, params=params, headers=headers, timeout_seconds=timeout_seconds or REQUEST_TIMEOUT_SECONDS
    )
    if 200 <= resp.status_code < 300:
        _MEM_HTTP_CACHE[key] = (time.time() + ttl, getattr(resp, "text", ""), int(resp.status_code))
    else:
        if getattr(settings, "enable_http_negative_cache", False) and resp.status_code in {404, 429}:
            retry_after_s: float | None = None
            try:
                headers_obj = getattr(resp, "headers", None)
                ra = headers_obj.get("Retry-After") if headers_obj else None
                if ra:
                    if ra.isdigit():
                        retry_after_s = float(ra)
                    else:
                        from email.utils import parsedate_to_datetime

                        try:
                            dt = parsedate_to_datetime(ra)
                            retry_after_s = max(0.0, (dt.timestamp() - time.time()))
                        except Exception:
                            retry_after_s = None
            except Exception:
                retry_after_s = None
            neg_ttl = min(60.0, ttl * 0.2) if retry_after_s is None else float(retry_after_s)
            _MEM_HTTP_NEG_CACHE[key] = (time.time() + float(neg_ttl), 404)
    return resp


__all__ = ["cached_get"]
