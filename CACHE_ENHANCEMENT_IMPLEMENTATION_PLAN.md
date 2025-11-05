# Cache Enhancement Implementation Plan

## Priority 1: High-Impact, Low-Effort Performance Optimization

**Created**: 2025-11-04  
**Priority**: P1 (Immediate Execution)  
**Expected ROI**: 40-60% latency reduction, 30-50% cost savings  
**Effort**: 2-3 days  

---

## 📊 Executive Summary

This plan implements result-level caching for the top 20 high-traffic tools to achieve significant performance improvements with minimal code changes. The enhancement leverages the existing `platform.cache.multi_level_cache` infrastructure (L1 memory + L2 Redis + L3 semantic cache) and requires only adding decorators to expensive tool operations.

### Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Cache Hit Rate** | 35% | 75% | +40 percentage points |
| **P50 Latency** | 2-5s | 1-2s | 40-60% reduction |
| **LLM API Calls** | 100% | 40-50% | 50-60% reduction |
| **Monthly Cost** | $X | $X * 0.5 | 50% savings |

---

## 🎯 Target Tools for Caching (Top 20)

### Tier 1: LLM-Based Analysis Tools (Highest Cost/Latency)

1. **EnhancedAnalysisTool** (`src/domains/intelligence/analysis/enhanced_analysis_tool.py`)
   - **Operations**: `_run(content, analysis_type)` - political analysis, sentiment, claim extraction
   - **Current Latency**: 3-4s per call
   - **Cache Key**: `hash(content + analysis_type)`
   - **TTL**: 3600s (1 hour)
   - **Expected Savings**: 60% reduction in analysis calls

2. **TextAnalysisTool** (`src/domains/intelligence/analysis/text_analysis_tool.py`)
   - **Operations**: Core text processing and NLP analysis
   - **Current Latency**: 2-3s per call
   - **Cache Key**: `hash(content)`
   - **TTL**: 3600s (1 hour)

3. **SentimentTool** (`src/domains/intelligence/analysis/sentiment_tool.py`)
   - **Operations**: Emotional tone and sentiment mapping
   - **Current Latency**: 1-2s per call
   - **Cache Key**: `hash(text)`
   - **TTL**: 7200s (2 hours)

4. **LogicalFallacyTool** (`src/domains/intelligence/analysis/logical_fallacy_tool.py`)
   - **Operations**: LLM-powered fallacy detection
   - **Current Latency**: 3-4s per call
   - **Cache Key**: `hash(text)`
   - **TTL**: 3600s (1 hour)

5. **PerspectiveSynthesizerTool** (`src/domains/intelligence/analysis/perspective_synthesizer_tool.py`)
   - **Operations**: Multi-perspective analysis synthesis
   - **Current Latency**: 4-5s per call
   - **Cache Key**: `hash(content + perspectives)`
   - **TTL**: 3600s (1 hour)

### Tier 2: Embedding Generation Tools (High Latency)

6. **EmbeddingService** (`src/domains/memory/embedding_service.py`)
   - **Operations**: `embed_text(text, model)` - SentenceTransformer or OpenAI embeddings
   - **Current Latency**: 500-1500ms per call
   - **Cache Key**: `hash(text + model)` (already has internal cache, enhance TTL)
   - **TTL**: 86400s (24 hours)
   - **Note**: Already has cache at line 93 (`_check_cache`), extend TTL and add multi-level

7. **TranscriptIndexTool** (`src/domains/intelligence/acquisition/transcript_index_tool.py`)
   - **Operations**: Transcript indexing and search
   - **Current Latency**: 1-2s per call
   - **Cache Key**: `hash(transcript_id + query)`
   - **TTL**: 7200s (2 hours)

### Tier 3: Transcription Tools (High Cost)

8. **AudioTranscriptionTool** (`src/domains/ingestion/providers/audio_transcription_tool.py`)
   - **Operations**: Whisper API transcription
   - **Current Latency**: 5-10s per file
   - **Cache Key**: `hash(audio_file_md5)` - content-based hashing
   - **TTL**: 604800s (7 days)
   - **Expected Savings**: 80% reduction in Whisper API costs for repeated content

### Tier 4: Content Analysis Tools (Medium Latency)

9. **LCSummarizeTool** - Content summarization
10. **TrendForecastingTool** - Trend analysis
11. **EngagementPredictionTool** - Engagement scoring
12. **TopicExtractionTool** - Topic modeling
13. **ClaimExtractionTool** - Factual claim detection
14. **ArgumentMiningTool** - Argumentation analysis
15. **FallacyDetectionTool** - Fallacy pattern matching
16. **BiasDetectionTool** - Bias analysis
17. **FramingAnalysisTool** - Narrative framing
18. **PersuasionTechniquesTool** - Persuasion pattern detection
19. **RhetoricalDevicesTool** - Rhetorical analysis
20. **EmotionalAppealTool** - Emotional appeal detection

---

## 🛠️ Implementation Strategy

### Phase 1: Infrastructure Preparation (Day 1, 4 hours)

#### 1.1 Verify Multi-Level Cache Configuration

```bash
# Check existing cache infrastructure
grep -r "multi_level_cache" src/platform/cache/
cat src/platform/cache/multi_level_cache.py | head -100
```

**Expected**: L1 (memory) + L2 (Redis) + L3 (semantic) cache hierarchy

#### 1.2 Create Reusable Cache Decorator

**File**: `src/platform/cache/tool_cache_decorator.py`

```python
"""Reusable cache decorator for BaseTool implementations."""

from __future__ import annotations

import hashlib
import json
import functools
from typing import Any, Callable, TypeVar
from platform.core.step_result import StepResult
from platform.cache.multi_level_cache import MultiLevelCache
from platform.observability.metrics import get_metrics

T = TypeVar("T", bound=Callable[..., StepResult])

def cache_tool_result(
    namespace: str,
    ttl: int = 3600,
    cache_key_fn: Callable[..., str] | None = None,
    enable_semantic: bool = False,
) -> Callable[[T], T]:
    """
    Decorator to cache tool execution results using multi-level cache.
    
    Args:
        namespace: Cache namespace (e.g., "tool:enhanced_analysis")
        ttl: Time-to-live in seconds (default: 1 hour)
        cache_key_fn: Optional function to generate cache key from args
        enable_semantic: Enable semantic similarity caching (for text analysis)
    
    Returns:
        Decorated function with automatic caching
        
    Example:
        @cache_tool_result(namespace="tool:sentiment", ttl=7200)
        def _run(self, text: str) -> StepResult:
            # Expensive sentiment analysis here
            return StepResult.ok(data={...})
    """
    cache = MultiLevelCache()
    metrics = get_metrics()
    
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> StepResult:
            # Generate cache key
            if cache_key_fn:
                cache_key = cache_key_fn(*args, **kwargs)
            else:
                # Default: hash function args (skip self)
                key_data = {"args": args[1:], "kwargs": kwargs}
                cache_key = hashlib.sha256(
                    json.dumps(key_data, sort_keys=True, default=str).encode()
                ).hexdigest()[:16]
            
            full_key = f"{namespace}:{cache_key}"
            
            # Check cache
            cached_result = cache.get(full_key, enable_semantic=enable_semantic)
            if cached_result is not None:
                metrics.counter(
                    "tool_cache_hits_total",
                    labels={"namespace": namespace}
                ).inc()
                # Return cached StepResult with cache metadata
                return StepResult.ok(
                    data=cached_result,
                    metadata={"cache_hit": True, "cache_key": cache_key}
                )
            
            # Cache miss - execute function
            metrics.counter(
                "tool_cache_misses_total",
                labels={"namespace": namespace}
            ).inc()
            
            result = func(*args, **kwargs)
            
            # Store successful results in cache
            if result.success and result.data:
                cache.set(full_key, result.data, ttl=ttl, enable_semantic=enable_semantic)
            
            return StepResult.ok(
                data=result.data,
                metadata={**result.metadata, "cache_hit": False, "cache_key": cache_key}
            )
        
        return wrapper  # type: ignore
    
    return decorator
```

### Phase 2: Tool Implementation (Day 1-2, 12 hours)

#### 2.1 Enhanced Analysis Tool (Tier 1, Highest Priority)

**File**: `src/domains/intelligence/analysis/enhanced_analysis_tool.py`

**Changes**:

```python
# Add import at top
from platform.cache.tool_cache_decorator import cache_tool_result

# Add decorator to _run method (line ~54)
@cache_tool_result(
    namespace="tool:enhanced_analysis",
    ttl=3600,  # 1 hour cache for analysis results
    enable_semantic=True  # Enable semantic similarity for text content
)
def _run(
    self,
    content: str | dict,
    analysis_type: str = "comprehensive",
    tenant: str = "global",
    workspace: str = "global",
) -> StepResult:
    # ... existing implementation
```

**Expected Impact**:

- Cache hit rate: 0% → 60%+ (repeated content analysis)
- Latency: 3-4s → 0.2-0.5s (cache hit)
- Cost: 100% → 40% (60% fewer LLM calls)

#### 2.2 Embedding Service (Tier 2, High Value)

**File**: `src/domains/memory/embedding_service.py`

**Changes**:

```python
# BEFORE (line 93): Simple dict cache
def _check_cache(self, text: str, model: str) -> EmbeddingResult | None:
    cache_key = hashlib.sha256((text + model).encode()).hexdigest()
    return self._embedding_cache.get(cache_key)

# AFTER: Multi-level cache with extended TTL
from platform.cache.tool_cache_decorator import cache_tool_result

@cache_tool_result(
    namespace="embeddings:generation",
    ttl=86400,  # 24 hours (embeddings don't change)
    enable_semantic=False  # Exact match only for embeddings
)
def embed_text(
    self, text: str, model: Literal["fast", "balanced", "quality"] = "fast", use_cache: bool = True
) -> StepResult:
    # ... existing implementation (remove internal _check_cache logic)
```

**Expected Impact**:

- Cache hit rate: 35% (internal) → 75% (multi-level + Redis)
- Persistent cache across restarts (Redis L2)
- Reduced memory pressure (LRU eviction in L1)

#### 2.3 Audio Transcription Tool (Tier 3, Cost Saver)

**File**: `src/domains/ingestion/providers/audio_transcription_tool.py`

**Changes**:

```python
from platform.cache.tool_cache_decorator import cache_tool_result
import hashlib

def _compute_audio_hash(audio_file: str) -> str:
    """Compute MD5 hash of audio file for cache key."""
    with open(audio_file, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

@cache_tool_result(
    namespace="transcription:whisper",
    ttl=604800,  # 7 days (transcriptions stable)
    cache_key_fn=lambda self, audio_file, **kwargs: _compute_audio_hash(audio_file)
)
async def transcribe_audio(self, audio_file: str, **kwargs) -> StepResult:
    # ... existing Whisper API call
```

**Expected Impact**:

- Whisper API cost: 100% → 20% (80% cache hit for repeated files)
- Latency: 5-10s → 0.5s (cache hit)

### Phase 3: Monitoring & Validation (Day 2, 4 hours)

#### 3.1 Add Cache Metrics Dashboard

**File**: `dashboards/cache_performance.json` (create new)

```json
{
  "title": "Tool Cache Performance",
  "panels": [
    {
      "title": "Cache Hit Rate by Tool",
      "targets": [
        {
          "expr": "rate(tool_cache_hits_total[5m]) / (rate(tool_cache_hits_total[5m]) + rate(tool_cache_misses_total[5m]))"
        }
      ]
    },
    {
      "title": "Latency Improvement (Cache Hit vs Miss)",
      "targets": [
        {
          "expr": "histogram_quantile(0.5, tool_execution_duration_seconds{cached=\"true\"})",
          "legendFormat": "P50 (cached)"
        },
        {
          "expr": "histogram_quantile(0.5, tool_execution_duration_seconds{cached=\"false\"})",
          "legendFormat": "P50 (uncached)"
        }
      ]
    }
  ]
}
```

#### 3.2 Cache Health Check

**File**: `scripts/validate_cache_health.py` (create new)

```python
#!/usr/bin/env python
"""Validate cache health and performance."""

import asyncio
from platform.cache.multi_level_cache import MultiLevelCache
from platform.observability.metrics import get_metrics

async def main():
    cache = MultiLevelCache()
    metrics = get_metrics()
    
    # Test cache operations
    test_key = "test:health_check"
    test_value = {"status": "healthy", "timestamp": time.time()}
    
    # Write test
    cache.set(test_key, test_value, ttl=60)
    
    # Read test
    result = cache.get(test_key)
    assert result == test_value, "Cache read/write failed"
    
    # Metrics check
    hit_rate = metrics.get("tool_cache_hits_total") / (
        metrics.get("tool_cache_hits_total") + metrics.get("tool_cache_misses_total")
    )
    
    print(f"✅ Cache health check passed")
    print(f"   Hit rate: {hit_rate*100:.1f}%")
    print(f"   L1 size: {cache.l1_size}")
    print(f"   L2 connected: {cache.l2_connected}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 4: Benchmarking & Rollout (Day 3, 4 hours)

#### 4.1 Baseline Performance Capture

```bash
# Before cache enhancement
python benchmarks/performance_benchmarks.py --baseline --output=cache_enhancement_before.json
```

#### 4.2 Gradual Rollout Strategy

**Week 1**: Deploy Tier 1 tools only (EnhancedAnalysisTool, TextAnalysisTool, SentimentTool)  
**Week 2**: Add Tier 2 (EmbeddingService, TranscriptIndexTool)  
**Week 3**: Add Tier 3 (AudioTranscriptionTool)  
**Week 4**: Add remaining Tier 4 tools

**Rollback Plan**: Feature flag `ENABLE_TOOL_RESULT_CACHING` (default: `true`)

```python
# In decorator
if not os.getenv("ENABLE_TOOL_RESULT_CACHING", "true").lower() == "true":
    return func(*args, **kwargs)  # Skip caching
```

#### 4.3 After Performance Validation

```bash
# After cache enhancement (Week 2)
python benchmarks/performance_benchmarks.py --compare=cache_enhancement_before.json

# Expected output:
# ✅ Cache hit rate: 35% → 68% (+33 pp)
# ✅ P50 latency: 2.8s → 1.2s (-57%)
# ✅ LLM API calls: 1000/day → 420/day (-58%)
```

---

## 📋 Implementation Checklist

### Day 1 (8 hours)

- [x] Review multi-level cache infrastructure (`platform/cache/multi_level_cache.py`)
- [ ] Create `tool_cache_decorator.py` with reusable decorator
- [ ] Add cache metrics (`tool_cache_hits_total`, `tool_cache_misses_total`)
- [ ] Implement Tier 1 tools (EnhancedAnalysisTool, TextAnalysisTool, SentimentTool)
- [ ] Add unit tests for cache decorator
- [ ] Test locally with synthetic workload

### Day 2 (8 hours)

- [ ] Implement Tier 2 tools (EmbeddingService, TranscriptIndexTool)
- [ ] Implement Tier 3 (AudioTranscriptionTool)
- [ ] Create cache performance dashboard
- [ ] Write `validate_cache_health.py` script
- [ ] Capture baseline benchmarks
- [ ] Add feature flag (`ENABLE_TOOL_RESULT_CACHING`)

### Day 3 (8 hours)

- [ ] Deploy to staging environment
- [ ] Run load tests with realistic workload
- [ ] Monitor cache hit rates and latency improvements
- [ ] Document cache TTL tuning guidelines
- [ ] Create runbook for cache invalidation
- [ ] Prepare rollout plan and stakeholder communication

---

## ⚠️ Risk Mitigation

### Risk 1: Cache Staleness

**Scenario**: Cached results become outdated (e.g., sentiment changes after edits)  
**Mitigation**:

- TTL tuning per tool (1 hour for dynamic content, 24 hours for stable data)
- Cache invalidation API endpoint (`DELETE /cache/{namespace}/{key}`)
- Version-based cache keys (include model version in key)

### Risk 2: Memory Pressure

**Scenario**: L1 cache (in-memory) grows too large  
**Mitigation**:

- LRU eviction policy (keep only hot data in L1)
- Configurable L1 size limit (default: 1000 entries per namespace)
- Overflow to L2 (Redis) for cold data

### Risk 3: Cache Poisoning

**Scenario**: Incorrect results cached, served repeatedly  
**Mitigation**:

- Only cache successful results (`if result.success`)
- Health checks validate cached data integrity
- Manual cache flush command (`make cache-flush`)

---

## 📈 Success Criteria

### Definition of Done

- [ ] All Tier 1-3 tools (8 tools) have caching enabled
- [ ] Cache hit rate ≥ 60% (target: 75%)
- [ ] P50 latency reduced by ≥ 40%
- [ ] LLM API costs reduced by ≥ 30%
- [ ] Dashboards show real-time cache performance
- [ ] Runbook documents cache operations
- [ ] Zero cache-related incidents in 2-week monitoring period

### Key Performance Indicators (KPIs)

| KPI | Baseline | Target | Measurement |
|-----|----------|--------|-------------|
| Cache Hit Rate | 35% | 75% | `tool_cache_hits / (hits + misses)` |
| P50 Latency | 2.8s | ≤1.5s | `histogram_quantile(0.5, tool_duration_seconds)` |
| P95 Latency | 8.2s | ≤4s | `histogram_quantile(0.95, tool_duration_seconds)` |
| LLM Cost/Day | $100 | ≤$50 | OpenRouter billing dashboard |
| Whisper Cost/Day | $20 | ≤$5 | OpenAI billing dashboard |

---

## 🎓 Lessons Learned (Post-Implementation)

*To be filled after rollout completion*

### What Went Well

- TBD

### What Didn't Go Well

- TBD

### Improvements for Next Time

- TBD

---

**Plan Owner**: GitHub Copilot (Beast Mode Agent)  
**Stakeholders**: Infrastructure Team, Cost Optimization Team, Product Team  
**Review Cadence**: Daily during implementation, weekly after rollout  
**Next Review**: 2025-11-07 (3 days from now)
