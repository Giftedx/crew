from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

from .. import flags
from ..learning_engine import LearningEngine
from .bounded_cache import create_llm_cache


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


# Use lazy import to avoid circular dependencies
def _get_cache_ttl() -> int:
    try:
        from ..secure_config import get_config

        return get_config().cache_ttl_llm
    except ImportError:
        return int(os.getenv("CACHE_TTL_LLM", "3600"))


llm_cache = create_llm_cache(ttl=_get_cache_ttl())

__all__ = ["llm_cache", "memo_llm", "make_key"]
