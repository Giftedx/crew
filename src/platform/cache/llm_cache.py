from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast


if TYPE_CHECKING:
    from collections.abc import Callable

from ..config import flags
from ..rl.learning_engine import LearningEngine
from .bounded_cache import create_llm_cache


def make_key(parts: dict[str, Any]) -> str:
    return ":".join(f"{k}={parts[k]}" for k in sorted(parts))


P = ParamSpec("P")
R = TypeVar("R")


def memo_llm(
    key_builder: Callable[P, dict[str, Any]], *, learning: LearningEngine | None = None, domain: str = "cache"
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
                    return cast("R", hit)
            result = func(*args, **kwargs)
            if arm == "use":
                llm_cache.set(key, result)
            if registered:
                engine.record(domain, {}, arm, 1.0)
            return result

        return wrapper

    return decorator


def _get_cache_ttl() -> int:
    """Resolve LLM cache TTL with unified config precedence.

    Precedence:
      1) unified cache config domain 'llm'
      2) secure_config.cache_ttl_llm
      3) env CACHE_TTL_LLM
      4) default 3600
    """
    try:
        from platform.cache.unified_config import get_unified_cache_config

        return int(get_unified_cache_config().get_ttl_for_domain("llm"))
    except Exception:
        ...
    try:
        from ..secure_config import get_config

        val = getattr(get_config(), "cache_ttl_llm", None)
        if isinstance(val, (int, float)) and int(val) > 0:
            return int(val)
    except Exception:
        ...
    try:
        return int(os.getenv("CACHE_TTL_LLM", "3600"))
    except Exception:
        return 3600


llm_cache = create_llm_cache(ttl=_get_cache_ttl())

# Alias for backward compatibility
get_llm_cache = create_llm_cache


def reset_llm_cache_for_tests():
    """Reset LLM cache for testing (placeholder)."""
    global llm_cache
    llm_cache = create_llm_cache(ttl=_get_cache_ttl())


__all__ = ["get_llm_cache", "llm_cache", "make_key", "memo_llm", "reset_llm_cache_for_tests"]
