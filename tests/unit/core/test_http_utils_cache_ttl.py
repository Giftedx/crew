from __future__ import annotations

from types import SimpleNamespace

from core import http_utils as hu


class _Resp:
    def __init__(self, status_code: int = 200, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text


def test_cached_get_caches_until_ttl(monkeypatch):
    # Enable in-memory cache with 1s TTL and no Redis
    monkeypatch.setattr(
        hu,
        "get_settings",
        lambda: SimpleNamespace(enable_http_cache=True, http_cache_ttl_seconds=1, rate_limit_redis_url=None),
    )

    # Deterministic clock
    now = {"t": 1000.0}
    monkeypatch.setattr(hu.time, "time", lambda: now["t"])  # type: ignore[arg-type]

    # Reset module cache
    hu._MEM_HTTP_CACHE.clear()

    calls = {"n": 0}

    def fake_get(url: str, **_):
        calls["n"] += 1
        return _Resp(200, f"v{calls['n']}")

    monkeypatch.setattr(hu, "resilient_get", fake_get)

    # First call populates cache
    r1 = hu.cached_get("https://x")
    assert r1.text == "v1"
    # Second call before TTL returns cached value (no extra calls)
    r2 = hu.cached_get("https://x")
    assert r2.text == "v1"
    assert calls["n"] == 1

    # Advance just under TTL → still cached
    now["t"] += 0.9
    r3 = hu.cached_get("https://x")
    assert r3.text == "v1"
    assert calls["n"] == 1

    # Advance past TTL → new fetch
    now["t"] += 0.2
    r4 = hu.cached_get("https://x")
    assert r4.text == "v2"
    assert calls["n"] == 2


def test_cached_get_ignores_non_2xx(monkeypatch):
    monkeypatch.setattr(
        hu,
        "get_settings",
        lambda: SimpleNamespace(enable_http_cache=True, http_cache_ttl_seconds=5, rate_limit_redis_url=None),
    )
    hu._MEM_HTTP_CACHE.clear()

    calls = {"n": 0}

    def fake_get(url: str, **_):
        calls["n"] += 1
        # Always 500 so it shouldn't be cached
        return _Resp(500, "err")

    monkeypatch.setattr(hu, "resilient_get", fake_get)

    r1 = hu.cached_get("https://y")
    r2 = hu.cached_get("https://y")
    assert r1.status_code == 500 and r2.status_code == 500
    # Because 500 is not cached, underlying callable called twice
    assert calls["n"] == 2
