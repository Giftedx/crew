# Cache Platform Migration Guide

**ADR Reference**: ADR-0001 (Cache Platform Standardization)
**Status**: In Progress
**Target Completion**: Phase 1

## Overview

This guide documents the migration from legacy cache implementations to the unified cache facade backed by `core.cache.multi_level_cache.MultiLevelCache`.

## Migration Checklist

### Phase 1A: Foundation (Complete)

- [x] Create `ENABLE_CACHE_V2` feature flag
- [x] Implement `UnifiedCache` facade in `ultimate_discord_intelligence_bot/cache/__init__.py`
- [x] Update `OpenRouterService` to support unified cache mode
- [x] Document flag in `docs/configuration.md`
- [x] Fix cache key generation to use `combine_keys` + `generate_key_from_params`

### Phase 1B: Service Migrations (In Progress)

- [ ] Migrate `services/cache_optimizer.py` → use `UnifiedCache` API
- [ ] Migrate `services/rl_cache_optimizer.py` → integrate with multi-level cache
- [ ] Migrate `performance/cache_optimizer.py` → deprecate or adapt
- [ ] Migrate `performance/cache_warmer.py` → use multi-level promotion
- [ ] Update `tools/unified_cache_tool.py` → consume `UnifiedCache`

### Phase 1C: Shadow Mode & Validation

- [ ] Implement shadow traffic harness comparing legacy vs. unified hit rates
- [ ] Add metrics for cache_v2 performance (`obs.metrics`)
- [ ] Run A/B test: ENABLE_CACHE_V2=false vs. true for 1 week
- [ ] Validate hit rate improvement target (>60%)

### Phase 1D: Cutover & Cleanup

- [ ] Enable `ENABLE_CACHE_V2=true` in production
- [ ] Remove fallback to legacy cache after 2 weeks stable
- [ ] Archive deprecated modules

## API Examples

### Legacy (Deprecated)

```python
from ultimate_discord_intelligence_bot.services.cache import make_key, RedisLLMCache

cache = RedisLLMCache(url="redis://localhost", ttl=300)
key = make_key(prompt, model)
cached = cache.get(key)
```

### Unified (Current)

```python
from ultimate_discord_intelligence_bot.cache import (
    get_unified_cache,
    get_cache_namespace,
    generate_key_from_params,
)

cache = get_unified_cache()
namespace = get_cache_namespace(tenant="default", workspace="main")
key = generate_key_from_params(prompt=prompt, model=model)

result = await cache.get(namespace, "llm", key)
if result.success and result.data["hit"]:
    value = result.data["value"]
```

## Migration Patterns

### Pattern 1: Simple Cache Replacement

**Before**:

```python
self.cache = RedisLLMCache(url=redis_url, ttl=3600)
cached = self.cache.get(key)
```

**After**:

```python
from ultimate_discord_intelligence_bot.cache import get_unified_cache, get_cache_namespace

self.cache_namespace = get_cache_namespace(tenant, workspace)
self.unified_cache = get_unified_cache()

result = await self.unified_cache.get(self.cache_namespace, "llm", key)
cached = result.data["value"] if result.success and result.data["hit"] else None
```

### Pattern 2: Cache Optimizer Migration

**Before** (`services/cache_optimizer.py`):

```python
optimizer = CacheOptimizer()
optimizer.optimize_cache_policies()
```

**After** (use multi-level cache built-in optimization):

```python
from core.cache.multi_level_cache import get_multi_level_cache

cache = get_multi_level_cache("llm")
# Multi-level cache has automatic promotion/demotion
# No manual optimization needed
```

## Testing

### Unit Tests

```python
@pytest.fixture
def unified_cache():
    from ultimate_discord_intelligence_bot.cache import get_unified_cache
    return get_unified_cache()

async def test_cache_get_miss(unified_cache):
    namespace = CacheNamespace(tenant="test", workspace="test")
    result = await unified_cache.get(namespace, "test", "nonexistent")
    assert result.success
    assert not result.data["hit"]
```

### Integration Tests

Test shadow mode metrics collection and hit rate comparison.

## Rollback Plan

If issues arise:

1. Set `ENABLE_CACHE_V2=false` to revert to legacy cache
2. Monitor metrics for degradation
3. File incident report with ADR reference
4. Fix issues before re-enabling

## Timeline

- Week 1-2: Complete service migrations (Phase 1B)
- Week 3: Shadow mode validation (Phase 1C)
- Week 4: Production cutover (Phase 1D)
