from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple, Callable

from .. import flags


@dataclass
class RetrievalCache:
    ttl: int
    store: Dict[str, Tuple[Any, float]] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        item = self.store.get(key)
        if not item:
            return None
        value, exp = item
        if exp < time.time():
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self.store[key] = (value, time.time() + self.ttl)


def memo_retrieval(key_builder: Callable[..., str]) -> Callable:
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            if not flags.enabled("ENABLE_CACHE", True):
                return func(*args, **kwargs)
            key = key_builder(*args, **kwargs)
            hit = retrieval_cache.get(key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            retrieval_cache.set(key, result)
            return result

        return wrapper

    return decorator


retrieval_cache = RetrievalCache(ttl=int(os.getenv("CACHE_TTL_RETRIEVAL", "300")))

__all__ = ["RetrievalCache", "retrieval_cache", "memo_retrieval"]
