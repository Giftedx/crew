"""Cache utilities for OpenRouter service."""
from __future__ import annotations

import hashlib
from platform.cache.bounded_cache import BoundedLRUCache, create_llm_cache
from typing import Any


try:
    from platform.cache.redis_cache import RedisCache
except Exception:
    RedisCache = None

def make_key(prompt: str, model: str) -> str:
    """Generate cache key for prompt and model."""
    digest = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
    return f'{model}:{digest}'

class RedisLLMCache(BoundedLRUCache):
    """LLMCache-compatible adapter backed by Redis."""

    def __init__(self, url: str, ttl: int=300, namespace: str='llm') -> None:
        if RedisCache is None:
            raise RuntimeError('redis not available')
        self._rc = RedisCache(url=url, ttl=ttl, namespace=namespace)
        super().__init__(max_size=1000, ttl=ttl, name=namespace)
        self._namespace = namespace

    def get(self, key: str) -> Any:
        """Get value from Redis cache."""
        return self._rc.get_json(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set value in Redis cache."""
        self._rc.set_json(key, value)
LLMCache = create_llm_cache()
