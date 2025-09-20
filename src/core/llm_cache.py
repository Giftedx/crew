"""Semantic LLM response cache.

Feature-flagged (ENABLE_SEMANTIC_LLM_CACHE) cache for prompt->response pairs with
optional semantic similarity matching. Per-tenant isolation is achieved by
prefixing keys with the active `TenantContext` identifiers when available.

Design goals:
- Safe default: disabled unless flag set.
- Namespace isolation via tenant + workspace.
- Two layers: in-memory LRU (always) + optional Redis backend if configured.
- Similarity threshold (cosine) to treat near-duplicate prompts as hits.
- TTL enforcement for freshness.
- Embedding abstraction kept minimal to avoid hard dependency; callers can
  supply an embedding vector or we fall back to a cheap hash embedding.

This module intentionally avoids *any* direct network model calls; it only
caches opaque response payloads (assumed JSON-serialisable or str convertible).
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

try:  # Optional tenancy context
    from ultimate_discord_intelligence_bot.tenancy import current_tenant
except Exception:  # pragma: no cover

    def current_tenant():  # type: ignore
        return None


try:  # Optional Redis cache (reuse HTTP cache Redis class if present)
    from core.cache.redis_cache import RedisCache  # type: ignore
except Exception:  # pragma: no cover
    RedisCache = None  # type: ignore

# ---------------------- Configuration & Flags ----------------------


def _flag_enabled() -> bool:
    return os.getenv("ENABLE_SEMANTIC_LLM_CACHE", "0").lower() in {"1", "true", "yes", "on"}


_DEFAULT_TTL_SECONDS = int(os.getenv("LLM_CACHE_TTL_SECONDS", "1800") or 1800)
_MAX_INMEM_ENTRIES = int(os.getenv("LLM_CACHE_MAX_ENTRIES", "512") or 512)
_SIM_THRESHOLD = float(os.getenv("LLM_CACHE_SIMILARITY_THRESHOLD", "0.96") or 0.96)
# NOTE: Threshold env vars may change during a test session. We therefore re-read them dynamically
# inside lookup paths rather than freezing at import-time. These module-level constants remain as
# fallbacks but live helpers below always take precedence.


def _similarity_threshold() -> float:
    try:
        return float(os.getenv("LLM_CACHE_SIMILARITY_THRESHOLD", str(_SIM_THRESHOLD)) or _SIM_THRESHOLD)
    except Exception:  # pragma: no cover
        return _SIM_THRESHOLD


def _overlap_threshold() -> float:
    try:
        return float(os.getenv("LLM_CACHE_OVERLAP_THRESHOLD", "0.45") or 0.45)
    except Exception:  # pragma: no cover
        return 0.45


# ---------------------- Utility Functions ----------------------


def _hash_embedding(text: str, dim: int = 64) -> list[float]:
    """Cheap deterministic embedding substitute using rolling hash buckets.

    Not intended for production semantics; replace with real embedder by
    providing `embedding` argument to `put()` / `get()` / `semantic_lookup()`.
    """
    buckets = [0] * dim
    # Normalize: lowercase and drop basic punctuation to increase overlap for paraphrases
    cleaned = [c for c in text.lower() if c.isalnum() or c.isspace()]
    norm_text = "".join(cleaned)
    for i, ch in enumerate(norm_text):
        buckets[i % dim] += ord(ch)
    # Normalize
    norm = math.sqrt(sum(v * v for v in buckets)) or 1.0
    return [v / norm for v in buckets]


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    num = 0.0
    a_sq = 0.0
    b_sq = 0.0
    for x, y in zip(a, b):
        num += x * y
        a_sq += x * x
        b_sq += y * y
    denom = (math.sqrt(a_sq) or 1.0) * (math.sqrt(b_sq) or 1.0)
    return num / denom


def _token_overlap(a_text: str, b_text: str) -> float:
    """Jaccard token overlap (very cheap) used as secondary semantic signal.

    Lowercases and splits on whitespace; ignores tokens of length < 2 to reduce noise.
    """
    a_tokens = {t for t in a_text.lower().split() if len(t) > 1}
    b_tokens = {t for t in b_text.lower().split() if len(t) > 1}
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return inter / union if union else 0.0


def _tenant_prefix() -> str:
    ctx = current_tenant()
    if not ctx:
        return "global:global"
    tid = getattr(ctx, "tenant_id", "global") or "global"
    wid = getattr(ctx, "workspace_id", getattr(ctx, "workspace", "global")) or "global"
    return f"{tid}:{wid}"


# ---------------------- Data Structures ----------------------


@dataclass
class CacheEntry:
    prompt_key: str
    response: Any
    embedding: list[float]
    created: float
    ttl: int
    snippet: str  # truncated original prompt text (or full if short) for cheap lexical fallback

    @property
    def expired(self) -> bool:
        return (time.time() - self.created) > self.ttl


class _LRU:
    def __init__(self, max_entries: int):
        self.max_entries = max_entries
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> CacheEntry | None:
        with self._lock:
            ent = self._store.get(key)
            if ent:
                self._store.move_to_end(key)
            return ent

    def put(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            self._store[key] = entry
            self._store.move_to_end(key)
            if len(self._store) > self.max_entries:
                self._store.popitem(last=False)

    def items(self):  # pragma: no cover - simple iteration helper
        with self._lock:
            return list(self._store.items())


# ---------------------- Core Cache ----------------------


class SemanticLLMCache:
    def __init__(self, *, ttl_seconds: int = _DEFAULT_TTL_SECONDS, similarity: float = _SIM_THRESHOLD):
        self.ttl_seconds = ttl_seconds
        self.similarity = similarity
        self._lru = _LRU(_MAX_INMEM_ENTRIES)
        self._redis = None
        if RedisCache is not None:
            try:  # Attempt constructing redis namespace 'llm'
                self._redis = RedisCache(namespace="llm")  # type: ignore
            except Exception:  # pragma: no cover
                self._redis = None

    # Key building (string-level exact cache)
    def _key(self, prompt: str, model: str | None) -> str:
        base = prompt.strip()
        model_part = model or "default"
        return f"{_tenant_prefix()}::{model_part}::{hash(base)}"

    def _serialize_entry(self, entry: CacheEntry) -> str:
        try:
            payload = {
                "prompt_key": entry.prompt_key,
                "response": entry.response,
                "embedding": entry.embedding,
                "created": entry.created,
                "ttl": entry.ttl,
                "snippet": entry.snippet,
            }
            return json.dumps(payload)
        except Exception:
            return "{}"

    def _deserialize_entry(self, raw: str) -> CacheEntry | None:
        try:
            obj = json.loads(raw)
            return CacheEntry(
                prompt_key=obj["prompt_key"],
                response=obj.get("response"),
                embedding=list(obj.get("embedding", [])),
                created=float(obj.get("created", time.time())),
                ttl=int(obj.get("ttl", self.ttl_seconds)),
                snippet=obj.get("snippet", ""),
            )
        except Exception:
            return None

    # Public API
    def get(self, prompt: str, model: str | None = None, *, embedding: list[float] | None = None) -> Any | None:
        if not _flag_enabled():
            return None
        # Refresh similarity threshold dynamically (tests may mutate env mid-run)
        self.similarity = _similarity_threshold()
        k = self._key(prompt, model)
        # 1. Exact LRU
        ent = self._lru.get(k)
        if ent and not ent.expired:
            return ent.response
        # 2. Redis exact
        if self._redis is not None:
            try:
                raw = self._redis.get_str(k)
                if raw:
                    ent = self._deserialize_entry(raw)
                    if ent and not ent.expired:
                        self._lru.put(k, ent)
                        return ent.response
            except Exception:  # pragma: no cover
                pass
        # 3. Semantic scan (LRU only for speed) if embedding provided / computed
        emb = embedding or _hash_embedding(prompt)
        for key, entry in self._lru.items():  # pragma: no cover - simple linear scan path
            if entry.expired:
                continue
            if key == k:
                continue
            sim = _cosine(entry.embedding, emb)
            if sim >= self.similarity:
                return entry.response
            # Secondary cheap fallback: if cosine moderately close (>= similarity*0.6) and lexical token overlap high.
            if sim >= (self.similarity * 0.6) and entry.snippet:
                overlap = _token_overlap(entry.snippet, prompt)
                if overlap >= _overlap_threshold():
                    return entry.response
        return None

    def put(
        self,
        prompt: str,
        model: str | None,
        response: Any,
        *,
        embedding: list[float] | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        if not _flag_enabled():
            return
        k = self._key(prompt, model)
        emb = embedding or _hash_embedding(prompt)
        # Store a truncated snippet (first 240 chars) for lexical overlap fallback.
        snippet = prompt if len(prompt) <= 240 else prompt[:240]
        ent = CacheEntry(
            prompt_key=k,
            response=response,
            embedding=emb,
            created=time.time(),
            ttl=ttl_seconds or self.ttl_seconds,
            snippet=snippet,
        )
        self._lru.put(k, ent)
        if self._redis is not None:
            try:
                self._redis.set_str(k, self._serialize_entry(ent), ttl=ent.ttl)  # type: ignore[arg-type]
            except Exception:  # pragma: no cover
                pass

    # Convenience combined lookup/store wrapper
    def get_or_set(
        self,
        prompt: str,
        model: str | None,
        compute_fn,
        *,
        embedding: list[float] | None = None,
        ttl_seconds: int | None = None,
    ) -> Any:
        hit = self.get(prompt, model, embedding=embedding)
        if hit is not None:
            return hit
        result = compute_fn()
        self.put(prompt, model, result, embedding=embedding, ttl_seconds=ttl_seconds)
        return result


# Singleton accessor (mirrors HTTP utils pattern)
_global_cache: SemanticLLMCache | None = None


def get_llm_cache() -> SemanticLLMCache:
    global _global_cache  # noqa: PLW0603
    if _global_cache is None:
        _global_cache = SemanticLLMCache()
    return _global_cache


def reset_llm_cache_for_tests() -> None:  # pragma: no cover - test utility
    """Reset the process singleton (used in tests to avoid cross-test leakage)."""
    global _global_cache  # noqa: PLW0603
    _global_cache = None


__all__ = ["SemanticLLMCache", "get_llm_cache", "reset_llm_cache_for_tests"]
