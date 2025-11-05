# Cache Invalidation Strategies

**Last Updated**: November 5, 2025  
**Status**: Production Ready

## Overview

This document describes cache invalidation strategies for the multi-level cache system used across tool result caching. Proper invalidation ensures data freshness while maintaining performance benefits.

---

## Table of Contents

1. [Invalidation Triggers](#invalidation-triggers)
2. [Invalidation Methods](#invalidation-methods)
3. [Namespace Patterns](#namespace-patterns)
4. [Best Practices](#best-practices)
5. [Code Examples](#code-examples)
6. [Troubleshooting](#troubleshooting)

---

## Invalidation Triggers

### When to Invalidate Cache

#### 1. Data Updates

Invalidate when underlying data changes that would affect cached results:

- **User data changes**: Profile updates, preference changes
- **Content updates**: Transcript corrections, metadata updates
- **Configuration changes**: Analysis thresholds, routing rules

**Example**: When a video transcript is corrected, invalidate:

- `tool:transcript_index:{video_id}`
- `tool:vector_search:*` (if transcript content is indexed)

#### 2. Schema Changes

Invalidate when data structures or output formats change:

- **Tool output schema changes**: New fields added, field types changed
- **Analysis model updates**: Sentiment analysis algorithm upgraded
- **Embedding model changes**: Different embedding dimensions

**Example**: When upgrading sentiment analysis model:

- Invalidate all `tool:sentiment:*` entries
- Consider versioned cache keys (see [Versioning](#cache-key-versioning))

#### 3. Time-Based Expiration

Rely on TTL for automatic invalidation of time-sensitive data:

- **High volatility**: Short TTL (1 hour) for frequently changing data
- **Medium volatility**: Medium TTL (2-4 hours) for stable analysis
- **Low volatility**: Long TTL (24 hours) for deterministic operations

**Current TTL Configuration**:

- `SentimentTool`: 7200s (2 hours)
- `EnhancedAnalysisTool`: 3600s (1 hour)
- `TextAnalysisTool`: 3600s (1 hour)
- `EmbeddingService`: 7200s (2 hours)
- `TranscriptIndexTool`: 7200s (2 hours)
- `VectorSearchTool`: 3600s (1 hour)

#### 4. Tenant/Workspace Context Changes

Invalidate when tenant or workspace configuration changes:

- **Feature flag changes**: New features enabled/disabled
- **Tenant-specific rules**: Content filtering rules updated
- **Access control changes**: Permissions modified

---

## Invalidation Methods

### 1. Manual Invalidation (Programmatic)

#### Invalidate Specific Key

```python
from platform.cache.multi_level_cache import MultiLevelCache

cache = MultiLevelCache(max_memory_size=1000, default_ttl=3600)

# Invalidate specific cache entry
namespace = "tool:sentiment"
operation_data = {"text": "specific input"}
cache.invalidate(namespace, operation_data)
```

#### Invalidate by Namespace

```python
# Invalidate all entries in a namespace
cache.invalidate_namespace("tool:sentiment")

# Or with tenant/workspace scoping
from ultimate_discord_intelligence_bot.tenancy import current_tenant

tenant = current_tenant()
if tenant:
    cache.invalidate_by_tenant_workspace(tenant.tenant, tenant.workspace)
```

### 2. Redis CLI Invalidation

#### Clear All Cache

```bash
# Clear entire Redis cache (use with caution)
redis-cli FLUSHDB
```

#### Clear Specific Pattern

```bash
# Clear all sentiment tool cache entries
redis-cli KEYS "cache:tool:sentiment:*" | xargs redis-cli DEL

# Clear specific tenant cache
redis-cli KEYS "cache:tenant_123:*" | xargs redis-cli DEL
```

### 3. HTTP API Invalidation

```bash
# Invalidate specific pattern (if cache endpoints are enabled)
curl -X POST http://localhost:8000/cache/invalidate \
  -H "Content-Type: application/json" \
  -d '{"pattern": "tool:sentiment:*"}'

# Clear all cache
curl -X POST http://localhost:8000/cache/clear
```

### 4. Scheduled Invalidation

Implement periodic cache cleanup for stale entries:

```python
import asyncio
from datetime import datetime, timedelta

async def scheduled_cache_cleanup():
    """Run daily cache cleanup for stale entries."""
    cache = MultiLevelCache()
    
    while True:
        # Wait until 2 AM
        now = datetime.now()
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        
        # Perform cleanup
        print("Running scheduled cache cleanup...")
        
        # Clear old analytics cache (keep last 24 hours)
        cache.invalidate_namespace("tool:sentiment")
        cache.invalidate_namespace("tool:enhanced_analysis")
        
        print("Cache cleanup completed")
```

---

## Namespace Patterns

### Standard Namespace Format

```
tool:{tool_name}:{tenant}:{workspace}:{operation_hash}
```

**Components**:

- `tool` - Fixed prefix for tool result caching
- `{tool_name}` - Tool identifier (e.g., `sentiment`, `text_analysis`)
- `{tenant}` - Tenant ID (if multi-tenant)
- `{workspace}` - Workspace ID (if multi-workspace)
- `{operation_hash}` - SHA256 hash of operation parameters

### Examples

```python
# Sentiment analysis cache key
"cache:tool:sentiment:tenant_123:workspace_456:a1b2c3d4..."

# Vector search cache key
"cache:tool:vector_search:tenant_123:workspace_456:e5f6g7h8..."

# Embedding service cache key (deterministic, longer TTL)
"cache:tool:embedding:tenant_123:workspace_456:i9j0k1l2..."
```

### Wildcard Patterns for Bulk Invalidation

```bash
# All sentiment tool entries
"cache:tool:sentiment:*"

# All entries for specific tenant
"cache:*:tenant_123:*"

# All entries for specific workspace
"cache:*:*:workspace_456:*"

# All tool cache entries (across all tenants)
"cache:tool:*"
```

---

## Best Practices

### 1. Prefer TTL Over Manual Invalidation

**Do**:

```python
# Set appropriate TTL based on data volatility
@cache_tool_result(namespace="tool:sentiment", ttl=7200)  # 2 hours for stable analysis
def _run(self, text: str) -> StepResult:
    ...
```

**Don't**:

```python
# Over-relying on manual invalidation
cache.invalidate_namespace("tool:sentiment")  # Too frequent, negates cache benefits
```

### 2. Use Versioned Cache Keys for Schema Changes

**Recommended Pattern**:

```python
# Include version in namespace to auto-invalidate on upgrades
CACHE_VERSION = "v2"  # Increment when schema changes

@cache_tool_result(namespace=f"tool:sentiment:{CACHE_VERSION}", ttl=7200)
def _run(self, text: str) -> StepResult:
    ...
```

### 3. Invalidate Narrowly, Not Broadly

**Do**:

```python
# Invalidate specific video's transcript cache
cache.invalidate("tool:transcript_index", {"video_id": "abc123"})
```

**Don't**:

```python
# Avoid blanket invalidation
cache.invalidate_namespace("tool:*")  # Too broad, hurts performance
```

### 4. Log Invalidation Events

```python
import logging

logger = logging.getLogger(__name__)

def invalidate_video_cache(video_id: str):
    """Invalidate all cache entries for a video."""
    logger.info(f"Invalidating cache for video {video_id}")
    
    cache.invalidate("tool:transcript_index", {"video_id": video_id})
    cache.invalidate_namespace(f"tool:vector_search:*:{video_id}:*")
    
    logger.info(f"Cache invalidation completed for video {video_id}")
```

### 5. Test Invalidation Logic

```python
def test_cache_invalidation():
    """Test that cache invalidation works correctly."""
    cache = MultiLevelCache()
    
    # Set cache entry
    cache.set("test", {"key": "value"}, "test_data", ttl=60)
    
    # Verify entry exists
    result = cache.get("test", {"key": "value"})
    assert result == "test_data"
    
    # Invalidate
    cache.invalidate("test", {"key": "value"})
    
    # Verify entry is gone
    result = cache.get("test", {"key": "value"})
    assert result is None
```

---

## Code Examples

### Example 1: Invalidate After Data Update

```python
from platform.cache.multi_level_cache import MultiLevelCache

def update_video_transcript(video_id: str, new_transcript: str):
    """Update video transcript and invalidate related cache."""
    # Update database
    db.update_transcript(video_id, new_transcript)
    
    # Invalidate transcript-related cache
    cache = MultiLevelCache()
    cache.invalidate("tool:transcript_index", {"video_id": video_id})
    
    # Also invalidate vector search results that may have included this transcript
    cache.invalidate_namespace(f"tool:vector_search:*")  # Broad, but necessary
    
    logger.info(f"Updated transcript and invalidated cache for video {video_id}")
```

### Example 2: Tenant-Specific Invalidation

```python
from ultimate_discord_intelligence_bot.tenancy import with_tenant, TenantContext

def invalidate_tenant_cache(tenant_id: str, workspace_id: str):
    """Invalidate all cache for a specific tenant/workspace."""
    with with_tenant(TenantContext(tenant_id, workspace_id)):
        cache = MultiLevelCache()
        cache.invalidate_by_tenant_workspace(tenant_id, workspace_id)
        
        logger.info(f"Invalidated cache for tenant={tenant_id}, workspace={workspace_id}")
```

### Example 3: Conditional Invalidation

```python
def update_analysis_settings(setting_key: str, new_value: Any):
    """Update analysis settings and conditionally invalidate cache."""
    old_value = config.get(setting_key)
    config.set(setting_key, new_value)
    
    # Only invalidate cache if the change affects analysis results
    cache_affecting_settings = {
        "sentiment_threshold": "tool:sentiment",
        "content_routing_rules": "tool:enhanced_analysis",
        "text_analysis_model": "tool:text_analysis",
    }
    
    if setting_key in cache_affecting_settings:
        namespace = cache_affecting_settings[setting_key]
        cache = MultiLevelCache()
        cache.invalidate_namespace(namespace)
        
        logger.warning(
            f"Setting {setting_key} changed from {old_value} to {new_value}. "
            f"Invalidated cache namespace: {namespace}"
        )
```

### Example 4: Batch Invalidation

```python
def invalidate_multiple_videos(video_ids: list[str]):
    """Invalidate cache for multiple videos efficiently."""
    cache = MultiLevelCache()
    
    for video_id in video_ids:
        cache.invalidate("tool:transcript_index", {"video_id": video_id})
        # Note: Individual invalidations, could be optimized with batch API
    
    # Invalidate vector search once for all videos
    cache.invalidate_namespace("tool:vector_search")
    
    logger.info(f"Invalidated cache for {len(video_ids)} videos")
```

---

## Troubleshooting

### Problem: Cache Not Invalidating

**Symptoms**: Changes to data not reflected in tool outputs

**Solutions**:

1. Check namespace matches exactly (case-sensitive)
2. Verify operation hash generation is consistent
3. Confirm Redis connection is active
4. Check if cache is using memory-only mode (Redis unavailable)

```python
# Debug cache state
cache = MultiLevelCache()
stats = cache.get_stats()
print(f"Redis available: {stats.get('redis_available')}")
print(f"Memory cache size: {stats.get('memory_size')}")
```

### Problem: Over-Invalidation Hurting Performance

**Symptoms**: Low cache hit rates, high latency

**Solutions**:

1. Review invalidation patterns - are they too broad?
2. Check invalidation frequency - too often?
3. Consider increasing TTL instead of manual invalidation
4. Use versioned cache keys for schema changes

```python
# Monitor cache hit rate
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

metrics = get_metrics()
# Check tool_cache_hits_total vs tool_cache_misses_total
```

### Problem: Stale Data After Invalidation

**Symptoms**: Old data still returned after invalidation

**Solutions**:

1. Check if both memory and Redis caches are being cleared
2. Verify tenant/workspace context is correct
3. Confirm operation parameters match exactly
4. Check for multiple cache instances (singleton pattern)

```python
# Force cache health check
cache = MultiLevelCache()
health = cache.check_health()
print(f"Cache health: {health}")
```

### Problem: Tenant Isolation Issues

**Symptoms**: Tenant A seeing cached data from Tenant B

**Solutions**:

1. Ensure tenant context is set correctly: `with_tenant(TenantContext(...))`
2. Verify cache keys include tenant/workspace in namespace
3. Check decorator is using `current_tenant()` for key generation
4. Review tenant isolation in cache implementation

```python
# Verify tenant context
from ultimate_discord_intelligence_bot.tenancy import current_tenant

tenant = current_tenant()
print(f"Current tenant: {tenant.tenant if tenant else 'None'}")
print(f"Current workspace: {tenant.workspace if tenant else 'None'}")
```

---

## Cache Key Versioning

### Strategy

Include version identifier in cache namespace to automatically invalidate entries when tool logic changes:

```python
# Tool implementation
TOOL_VERSION = "v2"  # Increment on breaking changes

class SentimentTool(BaseTool):
    @cache_tool_result(namespace=f"tool:sentiment:{TOOL_VERSION}", ttl=7200)
    def _run(self, text: str) -> StepResult:
        # Analysis logic...
        pass
```

### Migration Process

1. **Increment version**: Change `TOOL_VERSION = "v2"` to `TOOL_VERSION = "v3"`
2. **Deploy**: New deployments use new namespace automatically
3. **Old cache expires**: Previous version entries expire via TTL (no manual cleanup needed)
4. **Monitor**: Track cache miss rate spike during transition

### Versioning Guidelines

- **Patch changes** (bug fixes, no output change): No version increment
- **Minor changes** (new optional fields): No version increment (backward compatible)
- **Major changes** (schema changes, algorithm changes): Increment version

---

## Related Documentation

- [Cache Usage Guide](cache_usage_guide.md) - Developer documentation for using cache decorators
- [Multi-Level Cache Implementation](../src/platform/cache/multi_level_cache.py) - Technical implementation details
- [Tool Cache Decorator](../src/platform/cache/tool_cache_decorator.py) - Decorator source code
- [ADR-0001: Cache Strategy](../docs/adr/ADR-0001-cache-strategy.md) - Architecture decision record (if exists)

---

## Support

For questions or issues with cache invalidation:

- Check [Troubleshooting](#troubleshooting) section above
- Review cache health: `python scripts/validate_cache_health.py`
- Monitor metrics in Grafana: `dashboards/cache_performance.json`
- Check logs: `tail -f logs/cache.log`

**Last Updated**: November 5, 2025
