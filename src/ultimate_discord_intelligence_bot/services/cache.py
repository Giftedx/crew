"""Simple in-memory caches for LLM calls and retrieval results."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from core.cache.bounded_cache import DEFAULT_MAX_SIZE, BoundedLRUCache, create_llm_cache


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


try:  # optional Redis-backed cache adapter
    from core.cache.redis_cache import RedisCache
except Exception:  # pragma: no cover
    RedisCache = None

LLMCache = create_llm_cache()


def make_key(prompt: str, model: str) -> StepResult:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"{model}:{digest}"


class RedisLLMCache(BoundedLRUCache):  # pragma: no cover - networked cache, exercised in integration
    """LLMCache-compatible adapter backed by Redis."""

    def __init__(self, url: str, ttl: int = 300, namespace: str = "llm") -> StepResult:
        if RedisCache is None:
            raise RuntimeError("redis not available")
        self._rc = RedisCache(url=url, ttl=ttl, namespace=namespace)
        super().__init__(max_size=DEFAULT_MAX_SIZE, ttl=ttl, name=namespace)
        self._namespace = namespace

    def get(self, key: str) -> StepResult:
        return self._rc.get_json(key)

    def set(self, key: str, value: dict[str, Any]) -> StepResult:
        self._rc.set_json(key, value)
