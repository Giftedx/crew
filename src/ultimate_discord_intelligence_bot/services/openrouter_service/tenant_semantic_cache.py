"""Tenant-scoped semantic cache manager leveraging GPTCache backends.

This wrapper composes ``core.cache.semantic_cache`` instances per tenant/workspace
namespace so cached responses remain isolated between customers. Each namespace is
stored under a dedicated sub-directory (``<cache_root>/semantic/<namespace>``)
with names sanitised for filesystem safety. Calls proxy directly to the
underlying cache implementation, preserving async semantics and optional
parameters such as ``namespace`` so existing metrics and promotion logic continue
working without modification.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from core.cache.enhanced_semantic_cache import create_enhanced_semantic_cache
from core.cache.semantic_cache import CacheStats, SemanticCacheInterface, create_semantic_cache
from core.secure_config import get_config

SanitiseNamespaceFn = Callable[[str | None], str]
SemanticCacheFactory = Callable[..., SemanticCacheInterface]


def _default_sanitise(namespace: str | None) -> str:
    if namespace is None or str(namespace).strip() == "":
        return "global"
    cleaned = []
    for ch in str(namespace):
        if ch.isalnum() or ch in {"-", "_"}:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "".join(cleaned)


class TenantSemanticCache(SemanticCacheInterface):
    """Dispatches semantic cache calls to tenant-specific instances."""

    def __init__(
        self,
        *,
        cache_root: str | None = None,
        similarity_threshold: float | None = None,
        fallback_enabled: bool = True,
        fallback_ttl_seconds: int | None = None,
        factory: SemanticCacheFactory | None = None,
        sanitise: SanitiseNamespaceFn | None = None,
    ) -> None:
        config = get_config()
        base_dir = cache_root or getattr(config, "cache_dir", "./cache")
        self._root = Path(base_dir).expanduser().resolve() / "semantic"
        self._root.mkdir(parents=True, exist_ok=True)

        # Use enhanced semantic cache if GPTCache is not available
        try:
            # Try to import GPTCache to check availability
            from importlib.util import find_spec

            if find_spec("gptcache") is not None:
                self._factory = factory or create_semantic_cache
            else:
                raise ImportError("gptcache not available")
        except ImportError:
            # Fall back to enhanced semantic cache
            self._factory = factory or create_enhanced_semantic_cache
        self._similarity_threshold = similarity_threshold
        self._fallback_enabled = fallback_enabled
        self._fallback_ttl_seconds = fallback_ttl_seconds
        self._sanitise = sanitise or _default_sanitise

        self._lock = threading.RLock()
        self._caches: dict[str, SemanticCacheInterface] = {}

    # ------------------------------------------------------------------
    def _get_cache(self, namespace: str | None) -> SemanticCacheInterface:
        key = self._sanitise(namespace)
        with self._lock:
            cache = self._caches.get(key)
            if cache is None:
                cache_dir = self._root / key
                cache_dir.mkdir(parents=True, exist_ok=True)
                # Check if we're using enhanced semantic cache
                from importlib.util import find_spec

                if find_spec("gptcache") is not None:
                    # Using GPTCache - use original parameters
                    cache = self._factory(
                        similarity_threshold=self._similarity_threshold or 0.8,
                        cache_dir=str(cache_dir),
                        fallback_enabled=self._fallback_enabled,
                        fallback_ttl_seconds=self._fallback_ttl_seconds or 3600,
                    )
                else:
                    # Using enhanced semantic cache - adapt parameters
                    cache = self._factory(
                        similarity_threshold=self._similarity_threshold or 0.8,
                        max_cache_size=1000,  # Default size for enhanced cache
                        cache_ttl_seconds=self._fallback_ttl_seconds or 3600,
                        enable_embeddings=True,
                        enable_tfidf=True,
                        namespace=key,  # Use sanitized namespace
                    )
                self._caches[key] = cache
            return cache

    # ------------------------------------------------------------------
    async def get(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any] | None:  # noqa: D401
        cache = self._get_cache(kwargs.get("namespace"))
        cache_kwargs = dict(kwargs)
        cache_kwargs.setdefault("namespace", kwargs.get("namespace"))
        return await cache.get(prompt, model, **cache_kwargs)

    async def set(self, prompt: str, model: str, response: dict[str, Any], **kwargs: Any) -> None:  # noqa: D401
        cache = self._get_cache(kwargs.get("namespace"))
        cache_kwargs = dict(kwargs)
        cache_kwargs.setdefault("namespace", kwargs.get("namespace"))
        await cache.set(prompt, model, response, **cache_kwargs)

    # ------------------------------------------------------------------
    def get_stats(self) -> CacheStats:  # noqa: D401
        aggregate = CacheStats()
        weighted_similarity = 0.0
        with self._lock:
            caches = list(self._caches.values())
        for cache in caches:
            try:
                stats = cache.get_stats()
            except Exception:  # pragma: no cover - defensive; underlying cache should conform
                continue
            aggregate.total_requests += stats.total_requests
            aggregate.cache_hits += stats.cache_hits
            aggregate.cache_misses += stats.cache_misses
            aggregate.cache_stores += stats.cache_stores
            aggregate.total_cost_saved += stats.total_cost_saved
            if stats.cache_hits > 0:
                weighted_similarity += stats.average_similarity * stats.cache_hits
        if aggregate.cache_hits > 0:
            aggregate.average_similarity = weighted_similarity / aggregate.cache_hits
        return aggregate


__all__ = ["TenantSemanticCache"]
