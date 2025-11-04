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
import os
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Iterable
try:
    from platform.cache.redis_cache import RedisCache
except Exception:
    RedisCache = None


def _env_cfg() -> Any:
    """Lightweight, dependency-free config shim for first-run and tests.

    Avoids importing the heavy configuration system (and pydantic) so this
    module can be used in minimal environments like the doctor command.
    """

    class _Cfg:
        enable_cache_vector = os.getenv("ENABLE_CACHE_VECTOR", "1").strip().lower() in {"1", "true", "yes", "on"}
        rate_limit_redis_url = os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL")
        default_embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "memory:sha256")
        cache_ttl_retrieval = int(os.getenv("CACHE_TTL_RETRIEVAL", "300"))

    return _Cfg()


def embed(texts: Iterable[str], model_hint: str | None = None) -> list[list[float]]:
    # Use lightweight env-based cfg to prevent import-time errors if optional deps are missing
    cfg = _env_cfg()
    use_cache = bool(
        getattr(cfg, "enable_cache_vector", True) and getattr(cfg, "rate_limit_redis_url", None) and RedisCache
    )
    selected_model = model_hint or getattr(cfg, "default_embedding_model", "memory:sha256")
    rc = None
    if use_cache and callable(RedisCache):
        try:
            try:
                from platform.cache.unified_config import get_unified_cache_config

                _ttl = int(get_unified_cache_config().get_ttl_for_domain("tool"))
            except Exception:
                _ttl = int(getattr(cfg, "cache_ttl_retrieval", 300))
            rc = RedisCache(url=str(cfg.rate_limit_redis_url), namespace="emb", ttl=_ttl)
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
