from __future__ import annotations

import os
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from .. import flags
from .bounded_cache import create_retrieval_cache


P = ParamSpec('P')
R = TypeVar('R')

def memo_retrieval(key_builder: Callable[P, str]) -> Callable[[Callable[P, R]], Callable[P, R]]:

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not flags.enabled('ENABLE_CACHE', True):
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

def _get_cache_ttl() -> int:
    """Resolve retrieval cache TTL with unified config precedence.

    Precedence:
      1) unified cache config domain 'tool'
      2) secure_config.cache_ttl_retrieval
      3) env CACHE_TTL_RETRIEVAL
      4) default 300
    """
    try:
        from platform.cache.unified_config import get_unified_cache_config
        return int(get_unified_cache_config().get_ttl_for_domain('tool'))
    except Exception:
        ...
    try:
        from ..secure_config import get_config
        val = getattr(get_config(), 'cache_ttl_retrieval', None)
        if isinstance(val, (int, float)) and int(val) > 0:
            return int(val)
    except Exception:
        ...
    try:
        return int(os.getenv('CACHE_TTL_RETRIEVAL', '300'))
    except Exception:
        return 300
retrieval_cache = create_retrieval_cache(ttl=_get_cache_ttl())
__all__ = ['memo_retrieval', 'retrieval_cache']
