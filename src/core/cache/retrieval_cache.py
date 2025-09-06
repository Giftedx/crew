from __future__ import annotations
import os
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar
from .. import flags
from .bounded_cache import create_retrieval_cache


P = ParamSpec("P")
R = TypeVar("R")


def memo_retrieval(key_builder: Callable[P, str]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not flags.enabled("ENABLE_CACHE", True):
                return func(*args, **kwargs)
            key = key_builder(*args, **kwargs)
            hit = retrieval_cache.get(key)
            if hit is not None:
                # Cache stores Any; cast to expected return type R
                return hit  # casting implicit; retrieval cache preserves type discipline by convention
            result = func(*args, **kwargs)
            retrieval_cache.set(key, result)
            return result

        return wrapper

    return decorator


# Use lazy import to avoid circular dependencies
def _get_cache_ttl() -> int:
    try:
        from ..secure_config import get_config
        return get_config().cache_ttl_retrieval
    except ImportError:
        return int(os.getenv("CACHE_TTL_RETRIEVAL", "300"))

retrieval_cache = create_retrieval_cache(ttl=_get_cache_ttl())

__all__ = ["retrieval_cache", "memo_retrieval"]