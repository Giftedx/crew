# Semantic Cache Prefetch & Instrumentation

**Implementation**: `src/platform/cache/multi_level_cache.py` (verified November 3, 2025)
**Integration**: `src/platform/llm/` (LLM routing layer with semantic cache support)
**Feature Flag**: `ENABLE_SEMANTIC_CACHE` (environment variable)

This document explains the semantic cache integration and related metrics introduced in `OpenRouterService`.

## Overview

When `ENABLE_SEMANTIC_CACHE` is set (truthy: `1|true|yes|on`) the router will attempt a *semantic* lookup prior to normal LLM invocation and classic response cache checks. The semantic cache stores model responses keyed by approximate embedding similarity rather than exact prompt text.

## Flow

1. Build tenant/workspace namespace: `tenant:workspace`.
1. If semantic cache instance available and flag enabled:
   1. Issue async `get(prompt, model, namespace)` inside a lightweight thread wrapper (allows usage both with & without an active event loop).
   1. On HIT:
      - Return cached response immediately.
      - Mark `cached=True`, `cache_type="semantic"`.
      - Record similarity (bucketed) & increment `llm_cache_hits_total`.
      - Increment `semantic_cache_prefetch_used_total`.
   1. On MISS:
      - Increment `llm_cache_misses_total`.
      - Increment `semantic_cache_prefetch_issued_total` (signals a downstream set will follow if call succeeds).
1. If miss, continue to normal offline/network path.
1. After a successful model call, the result is asynchronously stored (`set()`) for future reuse.

## Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `semantic_cache_similarity` | Histogram | tenant, workspace, bucket | Observed similarity value for hits; bucket label is coarse (`>=0.9`, `0.75-0.9`, `<0.75`). |
| `semantic_cache_prefetch_issued_total` | Counter | tenant, workspace | Prefetch attempts (misses) issued before model call. |
| `semantic_cache_prefetch_used_total` | Counter | tenant, workspace | Prefetched entries actually used (hits). |

Existing cache metrics (`llm_cache_hits_total`, `llm_cache_misses_total`) differentiate semantic vs traditional via the `cache_type` field in the response (the metric itself does not add a `cache_type` label to avoid cardinality growth).

## Configuration

| Setting | Source | Default | Purpose |
|---------|--------|---------|---------|
| `ENABLE_SEMANTIC_CACHE` | Environment | off | Enables semantic cache integration. |
| `enable_semantic_cache` | Settings attribute | False | Internal attribute (env presence overrides). |
| `semantic_cache_threshold` | Settings | 0.85 | Similarity threshold for retrieval (enforced by cache layer). |
| `semantic_cache_ttl_seconds` | Settings | 3600 | Expiration horizon for stored entries. |

## Similarity Bucketing Strategy

We emit the raw similarity value while labeling with a coarse qualitative bucket. This provides distribution insight without high cardinality. Future enhancements may adopt dynamic quantile buckets if needed.

## Failure Tolerance

All semantic cache operations are wrapped in broad try/except blocks. Any exception results in silent fallback to normal routing (no user-visible error). Metric emission attempts are also guarded.

## Tests

`tests/test_semantic_cache_instrumentation.py` covers:

- MISS then HIT flow (issued vs used counters behavior).
- Disabled flag: ensures cache factory is ignored and no semantic lookup occurs.

## Future Enhancements

- TTL-aware pruning feedback metric (e.g. `semantic_cache_expired_total`).
- Similarity decay scoring to bias fresher content.
- Partial match assembly (merge multiple near hits into context augmentation pre-call).
- Adaptive threshold tuning via reward feedback loops.

---
See `docs/memory.md` for broader context retrieval strategy and `docs/prompt_compression.md` for concurrent prompt optimization.
