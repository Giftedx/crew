# Semantic LLM Cache

Optional feature-flagged prompt→response cache with semantic matching.

## Flags & Settings

| Variable | Purpose | Default |
|----------|---------|---------|
| ENABLE_SEMANTIC_LLM_CACHE | Master switch | 0 (disabled) |
| LLM_CACHE_TTL_SECONDS | Base TTL for entries | 1800 |
| LLM_CACHE_MAX_ENTRIES | In-memory LRU size | 512 |
| LLM_CACHE_SIMILARITY_THRESHOLD | Cosine threshold for semantic hits | 0.96 |

## Key Concepts

- Per-tenant isolation: Keys are prefixed with `tenant:workspace` (falls back to `global:global`).
- Two layers: in-memory LRU (always) + Redis (if `core.cache.redis_cache.RedisCache` available).
- Semantic fallback: If no exact key hit, a linear scan compares cheap hash embeddings (or supplied embeddings) and returns first response above threshold.
- Safe degradation: If flag off or Redis unavailable, behaves as no-op or LRU-only.

## API

```python
from core.llm_cache import get_llm_cache

cache = get_llm_cache()
value = cache.get(prompt, model)
cache.put(prompt, model, response, ttl_seconds=900)
value = cache.get_or_set(prompt, model, lambda: compute(), ttl_seconds=600)
```

## Embeddings

By default a lightweight hash-based embedding is used. To integrate a real embedder, compute an embedding vector externally and pass it via `embedding=` in `put` / `get_or_set`.

## When to Use

Enable for workloads with repeated, near-identical prompts (e.g., deterministic knowledge queries). Do not enable for highly user-specific or sensitive content without first applying prompt sanitization.

## Testing

Unit tests in `tests/test_llm_cache.py` cover:

- Disabled flag behavior
- Basic put/get
- TTL expiry
- Semantic approximation hit

## Future Enhancements

- Pluggable embedding provider abstraction
- Adaptive eviction policy with usage frequency weighting
- Metrics integration (hits/misses/degenerations)
