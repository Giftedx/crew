"""Deterministic text embedding helper.

This module provides a tiny embedding function suitable for tests and
local development without external model dependencies.  Each text is
hashed with SHA-256 and the resulting bytes are converted into a fixed
-length list of floats in the range [0, 1).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
from typing import TYPE_CHECKING

from core.secure_config import get_config


if TYPE_CHECKING:
    from collections.abc import Iterable


try:
    from core.cache.redis_cache import RedisCache  # optional
except Exception:  # pragma: no cover
    RedisCache = None  # fallback sentinel when cache layer unavailable


def embed(texts: Iterable[str], model_hint: str | None = None) -> list[list[float]]:
    cfg = get_config()
    use_cache = bool(
        getattr(cfg, "enable_cache_vector", True) and getattr(cfg, "rate_limit_redis_url", None) and RedisCache
    )
    selected_model = model_hint or getattr(cfg, "default_embedding_model", "memory:sha256")
    rc = None
    if use_cache and callable(RedisCache):
        try:
            # Prefer unified cache configuration for default TTL; fallback to secure_config
            try:
                from core.cache.unified_config import get_unified_cache_config  # local import to avoid cycles

                _ttl = int(get_unified_cache_config().get_ttl_for_domain("tool"))
            except Exception:
                _ttl = int(getattr(cfg, "cache_ttl_retrieval", 300))
            rc = RedisCache(  # runtime optional dependency
                url=str(cfg.rate_limit_redis_url),
                namespace="emb",
                ttl=_ttl,
            )
        except Exception:
            rc = None
    vectors: list[list[float]] = []
    for text in texts:
        vec: list[float] | None = None
        cache_key = None
        if rc is not None:
            cache_key = hashlib.sha256(f"{selected_model}:{text}".encode()).hexdigest()
            data = rc.get_str(cache_key)
            if data:
                try:
                    vec = [float(x) for x in json.loads(data)]
                except Exception:
                    vec = None
        if vec is None:
            h = hashlib.sha256(text.encode("utf-8")).digest()
            vec = [int.from_bytes(h[i : i + 4], "big") / 2**32 for i in range(0, 32, 4)]
            vec.append(hashlib.sha256(selected_model.encode("utf-8")).digest()[0] / 255.0)
            if rc is not None and cache_key is not None:
                with contextlib.suppress(Exception):
                    rc.set_str(cache_key, json.dumps(vec))
        vectors.append(vec)
    return vectors
