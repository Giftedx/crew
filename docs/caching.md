# StructuredLLMService Caching Documentation

## Overview

The StructuredLLMService now includes intelligent response caching to reduce API costs and improve response times. The caching system is designed to be transparent, configurable, and efficient.

## Key Features

- **Automatic Cache Key Generation**: Deterministic keys based on request parameters
- **TTL-Based Expiration**: Task-specific time-to-live values
- **Cache Metrics**: Comprehensive monitoring with Prometheus integration
- **Background Maintenance**: Automatic cleanup of expired entries
- **Streaming Support**: Full caching support for streaming requests
- **Memory Efficient**: Configurable cache sizes and cleanup policies

## Cache Key Generation

Cache keys are generated deterministically from request parameters using SHA256 hashing:

```python
key_components = {
    "prompt_hash": hashlib.sha256(normalized_prompt.encode()).hexdigest()[:16],
    "model": model_name,
    "task_type": task_type,
    "model_spec": model_spec,
    "provider_opts": json.dumps(provider_opts, sort_keys=True),
}
```

### Key Properties

- **Deterministic**: Same inputs always generate the same key
- **Unique**: Different parameters generate different keys
- **Secure**: Uses cryptographic hashing for consistency
- **Compact**: 32-character final key for efficient storage

## TTL Configuration

Different task types have different TTL values to optimize cache effectiveness:

| Task Type | TTL | Use Case |
|-----------|-----|----------|
| `general` | 1 hour | General queries, profiles |
| `analysis` | 2 hours | Data analysis, reports |
| `code` | 30 minutes | Code generation, debugging |
| `creative` | 30 minutes | Creative writing, brainstorming |
| `factual` | 24 hours | Factual information, reference data |
| `search` | 1 hour | Search results, listings |

## Usage Examples

### Basic Caching

```python
from core.structured_llm_service import StructuredLLMService, StructuredRequest

# Create service (cache is enabled by default)
service = StructuredLLMService(openrouter_service)

# First request - cache miss, calls API
request = StructuredRequest(
    prompt="Generate a user profile",
    response_model=UserProfile,
    task_type="general"
)
result1 = service.route_structured(request)

# Second identical request - cache hit, returns cached result
result2 = service.route_structured(request)

# Results are identical, but only one API call was made
assert result1.name == result2.name
```

### Streaming Caching

```python
from core.structured_llm_service import StreamingStructuredRequest

# Streaming requests also use caching
request = StreamingStructuredRequest(
    prompt="Analyze this dataset",
    response_model=AnalysisResult,
    task_type="analysis"
)

# First streaming call
responses1 = [r async for r in service.route_structured_streaming(request)]

# Second streaming call - uses cached result
responses2 = [r async for r in service.route_structured_streaming(request)]
```

### Cache Management

```python
# Get cache statistics
stats = service.cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1%}")
print(f"Total entries: {stats['total_entries']}")

# Manually clear expired entries
expired_count = service.cache.clear_expired()

# Get detailed size information
size_info = service.cache.get_size_info()
print(f"Memory usage: {size_info['approximate_size_bytes']} bytes")
```

## Metrics

The caching system provides comprehensive Prometheus metrics:

### Cache Performance Metrics

- `structured_llm_cache_hits_total`: Total cache hits by task type
- `structured_llm_cache_misses_total`: Total cache misses by task type

### General Cache Metrics

- `cache_hits_total`: Total cache hits across the system
- `cache_misses_total`: Total cache misses across the system
- `cache_evictions_total`: Total entries evicted due to expiration
- `cache_size_bytes`: Current cache size in bytes
- `cache_entries_count`: Current number of cache entries

## Configuration

### Cache TTL Settings

The cache uses task-specific TTL values, but you can customize them:

```python
# Create cache with custom TTL
cache = ResponseCache(default_ttl_seconds=1800)  # 30 minutes default

# Override TTL for specific requests
cache.set("key", value, ttl_seconds=3600)  # 1 hour for this entry
```

### Maintenance Settings

```python
# Configure maintenance interval (default: 5 minutes)
service._cleanup_interval = 300

# Manual maintenance
service._perform_cache_maintenance()
```

## Best Practices

### 1. Cache Key Consistency

- Use consistent parameter naming in requests
- Avoid including timestamps or random values in prompts
- Consider normalizing prompts (lowercase, remove extra whitespace)

### 2. TTL Optimization

- Use shorter TTLs for dynamic content
- Use longer TTLs for stable, factual information
- Monitor cache hit rates and adjust TTLs accordingly

### 3. Memory Management

- Monitor cache size and memory usage
- Set appropriate cleanup intervals
- Consider cache size limits for high-traffic applications

### 4. Monitoring

- Track cache hit rates to measure effectiveness
- Monitor cache size to prevent memory issues
- Use metrics to identify optimization opportunities

## Performance Benefits

### Cost Reduction

- **API Call Reduction**: Cache hits eliminate redundant API calls
- **Cost Savings**: Significant reduction in LLM API costs
- **Scalability**: Better performance under load

### Response Time Improvement

- **Instant Responses**: Cache hits return results immediately
- **Reduced Latency**: No network round-trips for cached content
- **Consistent Performance**: Stable response times for repeated queries

## Troubleshooting

### Low Cache Hit Rate

- Check if prompts are being normalized consistently
- Verify that request parameters are identical for similar queries
- Consider adjusting TTL values

### Memory Issues

- Monitor cache size with `get_size_info()`
- Increase cleanup frequency
- Implement cache size limits

### Cache Not Working

- Verify that requests are truly identical
- Check cache key generation with `CacheKeyGenerator.generate_key()`
- Ensure service is properly initialized with caching enabled

## Semantic (LLM) Cache Namespace Isolation

When the semantic cache feature (`ENABLE_SEMANTIC_CACHE`) is enabled the system can operate in one of three progressively simpler modes depending on dependency availability and initialization success:

1. Full GPTCache mode (vector similarity store operational)
1. GPTCache degraded simple key/value mode (GPTCache imported but vector backend init failed ⇒ in-memory simple store)
1. Fallback semantic cache implementation (pure Python lightweight embedding / fuzzy match)

To prevent cross‑tenant leakage, all modes scope entries by a composed namespace `tenant_id:workspace_id` provided through an active `TenantContext`.

Isolation mechanisms:

- Prompt prefix injection: a leading marker (e.g. `[ns:tenant:workspace]`) included in the normalized prompt prior to hashing
- Model scoping: internal model identifier (or synthetic model key) suffixed with `@@ns=<tenant:workspace>` ensuring separation even if prompts collide

Recent hardening ensured that the degraded GPTCache simple store and the pure fallback path BOTH apply the same namespacing rules, eliminating a previously observed cross‑tenant hit scenario when GPTCache silently downgraded.

Operational guidance:

- Always enter a `TenantContext` (use `with_tenant(...)`) before invoking semantic cache dependent code paths.
- Do not reuse service singletons across tenants without proper context switching; namespacing relies on the context at key construction time.
- If cross‑tenant anomalies are suspected enable debug logging for `core.cache.semantic_cache` and confirm distinct `@@ns=` suffixes in emitted keys.

Testing/Regression:

- A regression test will (or already does, depending on commit history) force the degraded / fallback mode and assert that tenant A misses while tenant B hits only its own prior insertion.
- Multi‑tenant tests also assert no leakage when GPTCache backend initialization is intentionally failed.

Future enhancements under consideration:

- Admin/ops endpoint to expose per‑namespace semantic cache statistics
- Configurable eviction / size limits per namespace
- Optional cryptographic hashing of namespace marker for additional obscurity

If you modify semantic cache internals, ensure any new fast paths or fallbacks apply BOTH prompt prefix and model scoping to preserve isolation guarantees.

## Implementation Details

### Cache Storage

- In-memory storage using Python dictionaries
- Thread-safe for concurrent access
- No external dependencies required

### Cache Invalidation

- TTL-based automatic expiration
- Manual invalidation with `invalidate()` method
- Background cleanup of expired entries

### Concurrency

- Safe for concurrent read/write operations
- No locks or blocking operations
- Optimized for high-throughput scenarios

## Migration Guide

### From Non-Cached Service

No code changes required! Caching is automatically enabled and transparent to existing code.

### Custom Cache Implementation

If you need custom caching logic, you can:

- Extend the `ResponseCache` class
- Implement custom key generation
- Override TTL determination logic

## Examples

See `examples/caching_examples.py` for comprehensive usage examples including:

- Basic caching workflows
- TTL configuration
- Streaming with caching
- Cache key generation
- Maintenance and monitoring
