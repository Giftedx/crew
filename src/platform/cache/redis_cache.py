"""Minimal Redis cache helper.

Provides string/JSON get/set with TTL and namespacing. Optional dependency;
callers should guard construction with availability checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


try:  # optional
    import redis
except Exception:  # pragma: no cover
    redis = None  # type: ignore[assignment]


@dataclass
class RedisCache:
    url: str
    namespace: str = "app"
    ttl: int = 300

    def __post_init__(self) -> None:  # pragma: no cover
        if redis is None:
            raise RuntimeError("redis package not installed")
        self._r = redis.Redis.from_url(self.url, decode_responses=True)

    def _k(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def get_str(self, key: str) -> str | None:
        # redis-py returns Optional[str] with decode_responses=True
        return self._r.get(self._k(key))

    def set_str(self, key: str, value: str) -> None:
        self._r.setex(self._k(key), self.ttl, value)

    def get_json(self, key: str) -> dict[str, Any] | None:
        raw = self.get_str(key)
        if raw is None:
            return None
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
        return None

    def set_json(self, key: str, obj: dict[str, Any]) -> None:
        self.set_str(key, json.dumps(obj))
