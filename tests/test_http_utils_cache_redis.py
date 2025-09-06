from __future__ import annotations

from types import SimpleNamespace

from core import http_utils as hu


class _FakeRedisCache:
    _GLOBAL: dict[str, dict[str, str]] = {}

    def __init__(self, url: str, namespace: str, ttl: int) -> None:  # noqa: D401 - simple stub
        self.url = url
        self.namespace = namespace
        self.ttl = ttl
        self._store = self._GLOBAL.setdefault(namespace, {})

    # API compatible with expected get_str/set_str
    def get_str(self, key: str) -> str | None:
        return self._store.get(key)

    def set_str(self, key: str, value: str) -> None:
        self._store[key] = value


class _Resp:
    def __init__(self, status_code: int = 200, text: str = "ok") -> None:
        self.status_code = status_code
        self.text = text


def test_cached_get_uses_redis_when_configured(monkeypatch):
    # Pretend Redis is available by patching symbol and settings
    monkeypatch.setattr(hu, "_RedisCache", _FakeRedisCache)
    monkeypatch.setattr(
        hu,
        "get_settings",
        lambda: SimpleNamespace(enable_http_cache=True, http_cache_ttl_seconds=10, rate_limit_redis_url="redis://fake"),
    )

    calls = {"n": 0}

    def fake_get(url: str, **_):
        calls["n"] += 1
        return _Resp(200, f"val{calls['n']}")

    monkeypatch.setattr(hu, "resilient_get", fake_get)

    r1 = hu.cached_get("https://cache")
    r2 = hu.cached_get("https://cache")
    assert r1.text == "val1"
    assert r2.text == "val1"  # came from Redis cache
    assert calls["n"] == 1
