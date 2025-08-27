from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple, Callable

from .. import flags


@dataclass
class LLMCache:
    """A tiny in-memory TTL cache for LLM outputs."""

    ttl: int
    store: Dict[str, Tuple[Any, float]] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        item = self.store.get(key)
        if not item:
            return None
        value, expires = item
        if expires < time.time():
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self.store[key] = (value, time.time() + self.ttl)


def make_key(parts: Dict[str, Any]) -> str:
    return ":".join(f"{k}={parts[k]}" for k in sorted(parts))


def memo_llm(key_builder: Callable[..., Dict[str, Any]]) -> Callable:
    """Decorator to cache LLM calls based on key parts."""

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            if not flags.enabled("ENABLE_CACHE", True):
                return func(*args, **kwargs)
            key = make_key(key_builder(*args, **kwargs))
            hit = llm_cache.get(key)
            if hit is not None:
                return hit
            result = func(*args, **kwargs)
            llm_cache.set(key, result)
            return result

        return wrapper

    return decorator


llm_cache = LLMCache(ttl=int(os.getenv("CACHE_TTL_LLM", "3600")))

__all__ = ["LLMCache", "llm_cache", "memo_llm", "make_key"]
