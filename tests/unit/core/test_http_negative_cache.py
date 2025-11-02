from __future__ import annotations

import time

from core import http_utils


class _Resp:
    def __init__(self, status_code: int, text: str = "", headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):  # pragma: no cover - not needed
        return {}


class DummySettings:
    enable_http_cache = True
    http_cache_ttl_seconds = 300
    rate_limit_redis_url = None
    enable_http_negative_cache = True


def test_negative_cache_basic(monkeypatch):
    # Patch settings
    monkeypatch.setattr(http_utils, "get_settings", lambda: DummySettings())
    # Ensure in-memory caches start empty
    http_utils._MEM_HTTP_CACHE.clear()
    http_utils._MEM_HTTP_NEG_CACHE.clear()

    calls = {"count": 0}

    def fake_get(url, params=None, headers=None, timeout_seconds=None, stream=False):
        calls["count"] += 1
        return _Resp(404, "not found")

    monkeypatch.setattr(http_utils, "resilient_get", fake_get)

    r1 = http_utils.cached_get("https://example.com/missing")
    assert r1.status_code == 404
    assert calls["count"] == 1
    # Second call should be served from negative cache without invoking resilient_get
    r2 = http_utils.cached_get("https://example.com/missing")
    assert r2.status_code == 404
    assert calls["count"] == 1, "Second call should not hit network due to negative cache"


def test_negative_cache_retry_after(monkeypatch):
    monkeypatch.setattr(http_utils, "get_settings", lambda: DummySettings())
    http_utils._MEM_HTTP_CACHE.clear()
    http_utils._MEM_HTTP_NEG_CACHE.clear()

    calls = {"count": 0}

    def fake_get(url, params=None, headers=None, timeout_seconds=None, stream=False):
        calls["count"] += 1
        # First request returns 429 with Retry-After; subsequent should be cached until expiry
        if calls["count"] == 1:
            return _Resp(429, "rate limited", headers={"Retry-After": "1"})
        return _Resp(200, "ok")

    monkeypatch.setattr(http_utils, "resilient_get", fake_get)
    r1 = http_utils.cached_get("https://example.com/rate")
    assert r1.status_code == 429
    # Immediate second call should use negative cache (still 404 synthetic)
    r2 = http_utils.cached_get("https://example.com/rate")
    assert r2.status_code == 404
    assert calls["count"] == 1
    # After Retry-After expires, call should reach network again and succeed
    time.sleep(1.1)
    r3 = http_utils.cached_get("https://example.com/rate")
    assert r3.status_code == 200
    assert calls["count"] == 2
