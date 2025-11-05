# Cache Usage Guide for Developers

**Last Updated**: November 5, 2025  
**Status**: Production Ready

## Overview

This guide shows developers how to use the `@cache_tool_result` decorator to cache tool results, improving performance and reducing API costs. The multi-level cache (memory + Redis) provides fast access with automatic tenant isolation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Decorator Usage](#decorator-usage)
3. [TTL Selection Guidelines](#ttl-selection-guidelines)
4. [Performance Benchmarks](#performance-benchmarks)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Examples](#examples)

---

## Quick Start

### 1. Import the Decorator

```python
from platform.cache.tool_cache_decorator import cache_tool_result
```

### 2. Apply to Tool `_run` Method

```python
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult

class MyAnalysisTool(BaseTool):
    @cache_tool_result(namespace="tool:my_analysis", ttl=3600)  # 1 hour TTL
    def _run(self, text: str) -> StepResult:
        """Analyze text and return results."""
        # Expensive analysis logic here
        result = expensive_analysis(text)
        
        return StepResult.ok(result={"analysis": result})
```

### 3. That's It!

The decorator automatically:
- ✅ Generates cache keys from method parameters
- ✅ Handles tenant/workspace isolation
- ✅ Manages memory + Redis storage
- ✅ Emits metrics (`tool_cache_hits_total`, `tool_cache_misses_total`)
- ✅ Handles errors gracefully (cache failures don't break tool execution)

---

## Decorator Usage

### Basic Syntax

```python
@cache_tool_result(
    namespace: str,           # Required: Cache namespace (e.g., "tool:sentiment")
    ttl: int = 3600,         # Optional: Time-to-live in seconds (default 1 hour)
    exclude_params: list[str] = None  # Optional: Parameters to exclude from cache key
)
```

### Parameters

#### `namespace` (Required)

Unique identifier for this tool's cache entries. Convention: `"tool:{tool_name}"`

**Examples**:
- `"tool:sentiment"` - Sentiment analysis tool
- `"tool:vector_search"` - Vector search tool
- `"tool:transcript_index"` - Transcript indexing tool

**Best Practice**: Use lowercase with underscores, no spaces.

#### `ttl` (Optional, default: 3600)

Time-to-live in seconds. After this duration, cache entries expire and are re-computed.

**Common Values**:
- `3600` (1 hour) - Default, good for most tools
- `7200` (2 hours) - Stable, deterministic operations (sentiment analysis, embeddings)
- `1800` (30 minutes) - Frequently changing data
- `86400` (24 hours) - Rarely changing data (don't exceed this without good reason)

#### `exclude_params` (Optional, default: None)

List of parameter names to exclude from cache key generation. Useful for non-deterministic parameters like timestamps or request IDs.

**Example**:
```python
@cache_tool_result(
    namespace="tool:analysis",
    ttl=3600,
    exclude_params=["request_id", "timestamp"]  # Don't cache based on these
)
def _run(self, text: str, request_id: str = None, timestamp: str = None) -> StepResult:
    ...
```

---

## TTL Selection Guidelines

### Decision Tree

```
Is the operation deterministic (same input → same output)?
├─ Yes: Does the underlying data change?
│  ├─ Rarely (config, models): 7200s (2 hours) or higher
│  └─ Sometimes (user data): 3600s (1 hour)
└─ No: Is the result time-sensitive?
   ├─ Yes (real-time data): 1800s (30 minutes) or lower
   └─ No: 3600s (1 hour) default
```

### TTL by Operation Type

| Operation Type | TTL | Example Tools |
|---------------|-----|---------------|
| **Deterministic Analysis** | 7200s (2 hours) | SentimentTool, TextAnalysisTool |
| **Embedding Generation** | 7200s (2 hours) | EmbeddingService |
| **Data Indexing** | 7200s (2 hours) | TranscriptIndexTool |
| **Search Operations** | 3600s (1 hour) | VectorSearchTool |
| **User-Specific Analysis** | 3600s (1 hour) | EnhancedAnalysisTool |
| **Real-Time Data** | 1800s (30 min) | LiveDataTool |
| **Aggregations** | 3600s (1 hour) | StatisticsTool |

### Performance Benchmark Results

From **benchmarks/cache_performance_benchmark.py** (30 iterations per tool):

| Tool | Hit Rate | Cached Latency | Uncached Latency | Reduction |
|------|----------|----------------|------------------|-----------|
| **SentimentTool** | 83.3% | 0.01ms | 0.46ms | 97.9% |
| **EnhancedAnalysisTool** | 83.3% | 0.01ms | 0.59ms | 98.0% |
| **TextAnalysisTool** | 83.3% | 0.01ms | 89.50ms | 100% |

**Key Findings**:
- **83% hit rate** with realistic input patterns (5 unique inputs, 6 repetitions each)
- **97-100% latency reduction** for cached responses
- **2.26s total time saved** across 90 calls (TextAnalysisTool shows most dramatic improvement due to NLTK processing)
- **~$274/year cost savings** projected at 10x benchmark traffic

**Conclusion**: Cache is highly effective. Even 1-hour TTL yields excellent hit rates.

---

## Best Practices

### 1. Always Use the Decorator on `_run` Methods

**Do**:
```python
class MyTool(BaseTool):
    @cache_tool_result(namespace="tool:my_tool", ttl=3600)
    def _run(self, text: str) -> StepResult:
        ...
```

**Don't**:
```python
class MyTool(BaseTool):
    def _run(self, text: str) -> StepResult:
        # Missing decorator - no caching!
        ...
```

### 2. Return StepResult, Not Raw Values

The decorator caches `StepResult` objects. Always return `StepResult.ok(result=...)`.

**Do**:
```python
@cache_tool_result(namespace="tool:my_tool", ttl=3600)
def _run(self, text: str) -> StepResult:
    result = process(text)
    return StepResult.ok(result={"data": result})
```

**Don't**:
```python
@cache_tool_result(namespace="tool:my_tool", ttl=3600)
def _run(self, text: str) -> dict:  # Wrong return type
    return {"data": process(text)}
```

### 3. Use Descriptive Namespaces

**Do**:
```python
@cache_tool_result(namespace="tool:sentiment_analysis", ttl=7200)
```

**Don't**:
```python
@cache_tool_result(namespace="sa", ttl=7200)  # Too cryptic
@cache_tool_result(namespace="tool", ttl=7200)  # Too generic
```

### 4. Choose TTL Based on Data Volatility

**Do**:
```python
# Deterministic operation → longer TTL
@cache_tool_result(namespace="tool:text_analysis", ttl=7200)

# User-specific, may change → shorter TTL
@cache_tool_result(namespace="tool:user_preferences", ttl=1800)
```

**Don't**:
```python
# Using same TTL for everything
@cache_tool_result(namespace="tool:*", ttl=3600)  # Not tuned to operation
```

### 5. Test Cached vs Uncached Behavior

```python
def test_tool_caching():
    """Test that tool caching works correctly."""
    tool = MyAnalysisTool()
    
    # First call should miss cache
    result1 = tool._run(text="test input")
    assert result1.is_success()
    
    # Second call with same input should hit cache
    result2 = tool._run(text="test input")
    assert result2.is_success()
    assert result2.result == result1.result  # Same result
    
    # Check metrics
    metrics = get_metrics()
    hits = metrics.get_counter_value("tool_cache_hits_total")
    misses = metrics.get_counter_value("tool_cache_misses_total")
    assert hits >= 1  # At least one hit
    assert misses >= 1  # At least one miss
```

### 6. Monitor Cache Performance

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

# Check cache hit rate
metrics = get_metrics()
hits = metrics.get_counter_value("tool_cache_hits_total", labels={"tool": "my_tool"})
misses = metrics.get_counter_value("tool_cache_misses_total", labels={"tool": "my_tool"})

hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
print(f"Cache hit rate: {hit_rate:.1%}")
```

---

## Troubleshooting

### Problem: Cache Not Working (Always Missing)

**Symptoms**: Every call is a cache miss, no performance improvement

**Solutions**:

1. **Check decorator is applied**:
   ```python
   # Verify decorator is present
   assert hasattr(MyTool._run, '__wrapped__')  # Decorator applied
   ```

2. **Check namespace is unique**:
   ```python
   # Each tool should have distinct namespace
   @cache_tool_result(namespace="tool:my_unique_tool", ttl=3600)
   ```

3. **Check Redis connection**:
   ```bash
   redis-cli PING  # Should return PONG
   ```

4. **Check parameters are hashable**:
   ```python
   # Parameters must be JSON-serializable
   def _run(self, text: str, count: int) -> StepResult:  # ✅ Good
       ...
   
   def _run(self, data: MyCustomClass) -> StepResult:  # ❌ Bad (not serializable)
       ...
   ```

### Problem: Cache Hit Rate Lower Than Expected

**Symptoms**: Hit rate < 50%, despite repeated inputs

**Solutions**:

1. **Check input variation**:
   ```python
   # Are inputs actually repeating?
   # Log cache keys to verify
   logger.debug(f"Cache key: {generate_cache_key(params)}")
   ```

2. **Check TTL is long enough**:
   ```python
   # If data is accessed hours apart, increase TTL
   @cache_tool_result(namespace="tool:my_tool", ttl=7200)  # 2 hours instead of 1
   ```

3. **Check for excluded parameters**:
   ```python
   # Exclude non-deterministic params from cache key
   @cache_tool_result(
       namespace="tool:my_tool",
       ttl=3600,
       exclude_params=["timestamp", "request_id"]
   )
   ```

### Problem: Stale Data Returned

**Symptoms**: Cache returns old results after data update

**Solutions**:

1. **Invalidate cache after data changes**:
   ```python
   from platform.cache.multi_level_cache import MultiLevelCache
   
   def update_data(key: str, new_value: str):
       # Update database
       db.update(key, new_value)
       
       # Invalidate cache
       cache = MultiLevelCache()
       cache.invalidate_namespace("tool:my_tool")
   ```

2. **Use shorter TTL for volatile data**:
   ```python
   # Data changes frequently → shorter TTL
   @cache_tool_result(namespace="tool:my_tool", ttl=1800)  # 30 minutes
   ```

3. **Use versioned cache keys**:
   ```python
   CACHE_VERSION = "v2"  # Increment on schema changes
   
   @cache_tool_result(namespace=f"tool:my_tool:{CACHE_VERSION}", ttl=3600)
   ```

### Problem: Memory Usage Growing

**Symptoms**: Application memory increasing over time

**Solutions**:

1. **Check memory cache size limit**:
   ```python
   # Cache automatically evicts LRU entries when full
   cache = MultiLevelCache(max_memory_size=1000)  # Adjust limit
   ```

2. **Check Redis is available**:
   ```bash
   # If Redis is down, all caching happens in memory
   systemctl status redis
   ```

3. **Monitor cache size**:
   ```python
   cache = MultiLevelCache()
   stats = cache.get_stats()
   print(f"Memory cache size: {stats['memory_size']}")
   print(f"Redis available: {stats['redis_available']}")
   ```

### Problem: Tenant Isolation Issues

**Symptoms**: User A sees cached data from User B

**Solutions**:

1. **Ensure tenant context is set**:
   ```python
   from ultimate_discord_intelligence_bot.tenancy import with_tenant, TenantContext
   
   with with_tenant(TenantContext(tenant_id="123", workspace_id="456")):
       result = tool._run(text="test")  # Cache key includes tenant/workspace
   ```

2. **Verify cache key includes tenant/workspace**:
   ```python
   # Decorator automatically includes tenant/workspace from current_tenant()
   # No additional code needed
   ```

3. **Check tenant context in tests**:
   ```python
   def test_tenant_isolation():
       # Test different tenants get different cached results
       with with_tenant(TenantContext("tenant_a", "workspace_1")):
           result_a = tool._run(text="test")
       
       with with_tenant(TenantContext("tenant_b", "workspace_2")):
           result_b = tool._run(text="test")  # Should not reuse result_a's cache
   ```

---

## Examples

### Example 1: Basic Sentiment Analysis Tool

```python
from platform.cache.tool_cache_decorator import cache_tool_result
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult

class SentimentTool(BaseTool):
    """Analyze sentiment of text."""
    
    @cache_tool_result(namespace="tool:sentiment", ttl=7200)  # 2 hours
    def _run(self, text: str) -> StepResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            StepResult with sentiment analysis (positive/negative/neutral, score)
        """
        # Expensive LLM call here
        sentiment = llm_analyze_sentiment(text)
        
        return StepResult.ok(result={
            "sentiment": sentiment["label"],
            "score": sentiment["score"],
            "text_length": len(text)
        })
```

**Why 7200s TTL?** Sentiment analysis is deterministic (same text → same sentiment), so longer TTL is safe.

### Example 2: Vector Search Tool

```python
from platform.cache.tool_cache_decorator import cache_tool_result
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult

class VectorSearchTool(BaseTool):
    """Search for similar vectors in Qdrant."""
    
    @cache_tool_result(namespace="tool:vector_search", ttl=3600)  # 1 hour
    def _run(self, query: str, top_k: int = 10) -> StepResult:
        """
        Search for vectors similar to query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            StepResult with search results
        """
        # Generate embedding
        embedding = embedding_service.get_embedding(query)
        
        # Search Qdrant
        results = qdrant_client.search(
            collection_name="transcripts",
            query_vector=embedding,
            limit=top_k
        )
        
        return StepResult.ok(result={
            "query": query,
            "results": [
                {"id": r.id, "score": r.score, "text": r.payload["text"]}
                for r in results
            ]
        })
```

**Why 3600s TTL?** Search results may change as new documents are indexed, so medium TTL balances freshness with performance.

### Example 3: Tool with Excluded Parameters

```python
from platform.cache.tool_cache_decorator import cache_tool_result
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult
import time

class AnalysisToolWithTracking(BaseTool):
    """Analysis tool that tracks request metadata."""
    
    @cache_tool_result(
        namespace="tool:analysis_tracking",
        ttl=3600,
        exclude_params=["request_id", "timestamp"]  # Don't cache based on these
    )
    def _run(
        self,
        text: str,
        request_id: str = None,
        timestamp: float = None
    ) -> StepResult:
        """
        Analyze text with request tracking.
        
        Args:
            text: Text to analyze
            request_id: Request tracking ID (not used for caching)
            timestamp: Request timestamp (not used for caching)
            
        Returns:
            StepResult with analysis
        """
        # Log request metadata (but don't let it affect cache)
        logger.info(f"Request {request_id} at {timestamp}")
        
        # Analysis logic (deterministic based on text only)
        analysis = expensive_analysis(text)
        
        return StepResult.ok(result={
            "analysis": analysis,
            "request_id": request_id,
            "timestamp": timestamp
        })
```

**Why exclude parameters?** `request_id` and `timestamp` change every call but don't affect analysis output. Excluding them allows cache hits based on `text` alone.

### Example 4: Tool with Short TTL for Volatile Data

```python
from platform.cache.tool_cache_decorator import cache_tool_result
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult

class LiveDataTool(BaseTool):
    """Fetch live data from external API."""
    
    @cache_tool_result(namespace="tool:live_data", ttl=1800)  # 30 minutes
    def _run(self, symbol: str) -> StepResult:
        """
        Fetch live stock data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            StepResult with current price
        """
        # External API call
        data = stock_api.get_current_price(symbol)
        
        return StepResult.ok(result={
            "symbol": symbol,
            "price": data["price"],
            "volume": data["volume"],
            "timestamp": data["timestamp"]
        })
```

**Why 1800s TTL?** Data changes frequently (real-time stock prices), so shorter TTL ensures fresher results while still providing some caching benefit.

### Example 5: Tool with Versioned Cache

```python
from platform.cache.tool_cache_decorator import cache_tool_result
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from platform.core.step_result import StepResult

# Increment CACHE_VERSION when tool logic changes
CACHE_VERSION = "v2"  # Changed from v1 when we upgraded sentiment model

class VersionedSentimentTool(BaseTool):
    """Sentiment analysis with versioned cache."""
    
    @cache_tool_result(
        namespace=f"tool:sentiment:{CACHE_VERSION}",  # Auto-invalidates on upgrade
        ttl=7200
    )
    def _run(self, text: str) -> StepResult:
        """Analyze sentiment with version tracking."""
        sentiment = llm_analyze_sentiment_v2(text)  # New model
        
        return StepResult.ok(result={
            "sentiment": sentiment["label"],
            "score": sentiment["score"],
            "model_version": CACHE_VERSION
        })
```

**Why version cache?** When upgrading analysis models, old cached results may be incorrect. Versioning automatically invalidates old cache without manual cleanup.

---

## Performance Monitoring

### Check Cache Hit Rate

```bash
# Run benchmarks to measure hit rate
python benchmarks/cache_performance_benchmark.py --iterations 30

# Expected output:
# Overall hit rate: ~83% (with realistic input patterns)
# Latency reduction: 97-100%
# Time saved: 2+ seconds (for 90 calls)
```

### View Cache Metrics in Code

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

def print_cache_stats():
    """Print cache performance statistics."""
    metrics = get_metrics()
    
    # Get hit/miss counts
    hits = metrics.get_counter_value("tool_cache_hits_total")
    misses = metrics.get_counter_value("tool_cache_misses_total")
    
    # Calculate hit rate
    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0
    
    print(f"Cache Statistics:")
    print(f"  Hits: {hits}")
    print(f"  Misses: {misses}")
    print(f"  Hit Rate: {hit_rate:.1f}%")
    print(f"  Total Requests: {total}")
```

### Monitor via Prometheus/Grafana

If `ENABLE_PROMETHEUS_ENDPOINT=1`, cache metrics are exposed at `http://localhost:8000/metrics`:

```prometheus
# Cache hit rate
rate(tool_cache_hits_total[5m]) / 
(rate(tool_cache_hits_total[5m]) + rate(tool_cache_misses_total[5m]))

# Cache latency (when instrumented)
histogram_quantile(0.95, rate(tool_cache_latency_seconds_bucket[5m]))
```

---

## Related Documentation

- [Cache Invalidation Strategies](cache_invalidation.md) - When and how to invalidate cache
- [Multi-Level Cache Implementation](../src/platform/cache/multi_level_cache.py) - Technical details
- [Tool Cache Decorator Source](../src/platform/cache/tool_cache_decorator.py) - Decorator implementation
- [Performance Benchmarks](../benchmarks/cache_performance_benchmark.py) - Benchmark tool

---

## Support

For cache-related issues:
- Check [Troubleshooting](#troubleshooting) section
- Run cache health check: `python scripts/validate_cache_health.py` (if exists)
- Review cache logs: `tail -f logs/cache.log`
- Monitor metrics in Grafana: `dashboards/cache_performance.json`

**Last Updated**: November 5, 2025
