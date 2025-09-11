"""Deterministic text embedding helper.

This module provides a tiny embedding function suitable for tests and
local development without external model dependencies.  Each text is
hashed with SHA-256 and the resulting bytes are converted into a fixed
-length list of floats in the range [0, 1).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from core.secure_config import get_config

try:
    from core.cache.redis_cache import RedisCache  # optional
except Exception:  # pragma: no cover
    RedisCache = None  # fallback sentinel when cache layer unavailable


def embed(texts: Iterable[str], model_hint: str | None = None) -> list[list[float]]:
    cfg = get_config()
    use_cache = bool(
        getattr(cfg, "enable_cache_vector", True) and getattr(cfg, "rate_limit_redis_url", None) and RedisCache
    )
    rc = None
    if use_cache and callable(RedisCache):
        try:
            rc = RedisCache(  # runtime optional dependency
                url=str(cfg.rate_limit_redis_url), namespace="emb", ttl=int(getattr(cfg, "cache_ttl_retrieval", 300))
            )
        except Exception:
            rc = None
    vectors: list[list[float]] = []
    for text in texts:
        vec: list[float] | None = None
        key = None
        if rc is not None:
            key = hashlib.sha256(text.encode("utf-8")).hexdigest()
            data = rc.get_str(key)
            if data:
                try:
                    vec = [float(x) for x in json.loads(data)]
                except Exception:
                    vec = None
        if vec is None:
            h = hashlib.sha256(text.encode("utf-8")).digest()
            vec = [int.from_bytes(h[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)]
            if rc is not None and key is not None:
                try:
                    rc.set_str(key, json.dumps(vec))
                except Exception:
                    ...
        vectors.append(vec)
    return vectors
