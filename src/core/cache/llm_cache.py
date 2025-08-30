from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ParamSpec, TypeVar, cast

from .. import flags
from ..learning_engine import LearningEngine


@dataclass
class LLMCache:
    """A tiny in-memory TTL cache for LLM outputs."""

    ttl: int
    store: dict[str, tuple[Any, float]] = field(default_factory=dict)

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


def make_key(parts: dict[str, Any]) -> str:
    return ":".join(f"{k}={parts[k]}" for k in sorted(parts))


P = ParamSpec("P")
R = TypeVar("R")


def memo_llm(
    key_builder: Callable[P, dict[str, Any]],
    *,
    learning: LearningEngine | None = None,
    domain: str = "cache",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache LLM calls with RL-controlled policy.

    ``learning`` is consulted to decide whether to use the cache or bypass it.
    The domain defaults to ``"cache"``.
    """

    engine = learning or LearningEngine()

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not flags.enabled("ENABLE_CACHE", True):
                return func(*args, **kwargs)

            try:
                arm = engine.recommend(domain, {}, ["use", "bypass"])
                registered = True
            except KeyError:
                arm = "use"
                registered = False
            key = make_key(key_builder(*args, **kwargs))
            if arm == "use":
                hit = llm_cache.get(key)
                if hit is not None:
                    engine.record(domain, {}, arm, 1.0)
                    return cast(R, hit)

            result = func(*args, **kwargs)
            if arm == "use":
                llm_cache.set(key, result)
            if registered:
                engine.record(domain, {}, arm, 1.0)
            return result

        return wrapper

    return decorator


llm_cache = LLMCache(ttl=int(os.getenv("CACHE_TTL_LLM", "3600")))

__all__ = ["LLMCache", "llm_cache", "memo_llm", "make_key"]
