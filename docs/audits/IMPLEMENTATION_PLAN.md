# Architecture Consolidation Implementation Plan

**Date**: October 19, 2025
**Project**: Ultimate Discord Intelligence Bot
**Objective**: Complete consolidation of 60+ deprecated modules across 5 subsystems
**Timeline**: 12 weeks (Weeks 1-12)
**Status**: EXECUTING

---

## Executive Summary

This plan executes the comprehensive codebase review findings to eliminate technical debt through systematic migration of deprecated modules to unified facades. The work is organized into 8 phases with clear dependencies, success criteria, and risk mitigation strategies.

### Key Deliverables

- ✅ **Phase 0**: Archive isolation verified, .deprecated files removed
- 🔄 **Phase 1-2**: Cache migration to UnifiedCache facade (Week 1-2)
- **Phase 3-4**: Enhanced bandit plugins + prompt compression (Week 3-4)
- **Phase 5-6**: Memory + Orchestration migrations (Week 5-8)
- **Phase 7-8**: Routing + Analytics migrations (Week 9-12)

### Risk Mitigation

- **Shadow Mode Testing**: Run legacy + new implementations in parallel
- **Feature Flags**: Gradual rollout with `ENABLE_CACHE_V2`, etc.
- **Metrics**: Track hit rates, latency, error rates for regression detection
- **Rollback Plan**: Feature flags allow instant revert to legacy behavior

---

## Week 1-2: Foundation & Cache Migration

### Phase 0: Foundation ✅ COMPLETE

**Status**: Completed October 19, 2025

**Tasks Completed**:

1. ✅ Verified archive isolation (zero imports from `archive/`)
2. ✅ Removed 8 .deprecated files
3. ✅ Migrated `unified_cache_tool.py` to use UnifiedCache facade

**Outcome**: Clean foundation for remaining migrations

---

### Phase 1: Cache Migration (ADR-0001) 🔄 IN PROGRESS

**Objective**: Consolidate 20+ cache implementations to 2 (UnifiedCache + MultiLevelCache)

**Priority**: CRITICAL (lowest complexity, highest impact)

#### Task 1.1: Migrate Remaining Cache Services

**Files to Update**:

```
src/ultimate_discord_intelligence_bot/services/
├── cache.py → migrate to UnifiedCache facade
└── cache_shadow_harness.py → update for new API

src/performance/ (deprecated directory)
├── cache_optimizer.py → mark for deletion
└── cache_warmer.py → mark for deletion

src/ultimate_discord_intelligence_bot/caching/
├── unified_cache.py → mark as deprecated (prototype)
└── cache_optimizer.py → mark for deletion
```

**Migration Pattern**:

```python
# BEFORE (deprecated)
from ultimate_discord_intelligence_bot.services.cache import RedisLLMCache
cache = RedisLLMCache()
result = cache.get(key)

# AFTER (unified)
from ultimate_discord_intelligence_bot.cache import get_unified_cache, get_cache_namespace
cache = get_unified_cache()
namespace = get_cache_namespace(tenant="acme", workspace="main")
result = await cache.get(namespace, "llm", key)
```

**Commands**:

```bash
# 1. Find all imports of deprecated cache modules
grep -r "from ultimate_discord_intelligence_bot.services.cache import" src/ --include="*.py"
grep -r "from ultimate_discord_intelligence_bot.caching import" src/ --include="*.py"
grep -r "from performance.cache" src/ --include="*.py"

# 2. Update imports systematically
# (Manual review + replace_string_in_file for each occurrence)

# 3. Verify no deprecated imports remain
make guards
```

**Success Criteria**:

- ✅ Zero imports from `services/cache.py`, `services/rl_cache_optimizer.py`, `performance/cache_*`
- ✅ All cache operations use `get_unified_cache()` + namespaces
- ✅ `unified_cache_tool.py` operational (already migrated)

**Timeline**: 3 days

---

#### Task 1.2: Implement Shadow Harness for Cache Validation

**Objective**: Run legacy + unified caches in parallel to validate hit rate parity

**Implementation**:

```python
# src/ultimate_discord_intelligence_bot/cache/shadow_harness.py

import asyncio
from typing import Any
from ultimate_discord_intelligence_bot.cache import UnifiedCache, CacheNamespace
# Legacy cache import (temporary)
from ultimate_discord_intelligence_bot.services.cache import RedisLLMCache

class CacheShadowHarness:
    """Runs legacy and unified caches in parallel for validation"""

    def __init__(self):
        self.unified = UnifiedCache()
        self.legacy = RedisLLMCache()  # temporary
        self.stats = {"unified_hits": 0, "legacy_hits": 0, "mismatches": 0}

    async def get(self, namespace: CacheNamespace, cache_name: str, key: str) -> Any:
        """Get from both caches and compare results"""
        # Run both in parallel
        unified_result, legacy_result = await asyncio.gather(
            self.unified.get(namespace, cache_name, key),
            asyncio.to_thread(self.legacy.get, key),
            return_exceptions=True
        )

        # Track hits
        if unified_result.data.get("hit"):
            self.stats["unified_hits"] += 1
        if legacy_result is not None:
            self.stats["legacy_hits"] += 1

        # Detect mismatches
        if (unified_result.data.get("value") != legacy_result):
            self.stats["mismatches"] += 1
            logger.warning(f"Cache mismatch for key {key}")

        # Return unified result (it's the production path)
        return unified_result

    def get_stats(self):
        return self.stats
```

**Deployment**:

1. Enable shadow mode via `ENABLE_CACHE_SHADOW_MODE=true`
2. Run in staging for 1 week
3. Monitor metrics: `cache_shadow_mismatch_total`, `cache_shadow_hit_rate_diff`
4. Acceptable threshold: <5% hit rate variance

**Timeline**: 2 days implementation + 1 week validation

---

#### Task 1.3: Add Cache V2 Metrics

**Objective**: Instrument UnifiedCache with Prometheus metrics

**Implementation**:

```python
# Add to src/obs/metrics.py

from prometheus_client import Counter, Histogram

# Cache V2 metrics
cache_v2_operations_total = Counter(
    "cache_v2_operations_total",
    "Total cache V2 operations",
    ["operation", "cache_name", "tenant", "hit"]
)

cache_v2_latency_seconds = Histogram(
    "cache_v2_latency_seconds",
    "Cache V2 operation latency",
    ["operation", "cache_name"]
)

cache_v2_namespace_size = Gauge(
    "cache_v2_namespace_size",
    "Number of keys per namespace",
    ["tenant", "workspace", "cache_name"]
)
```

**Integration**:

```python
# Update src/ultimate_discord_intelligence_bot/cache/__init__.py

from obs.metrics import cache_v2_operations_total, cache_v2_latency_seconds

class UnifiedCache:
    async def get(self, namespace: CacheNamespace, cache_name: str, key: str):
        start = time.time()
        try:
            result = await self._do_get(namespace, cache_name, key)
            hit = result.data.get("hit", False)
            cache_v2_operations_total.labels(
                operation="get",
                cache_name=cache_name,
                tenant=namespace.tenant,
                hit=str(hit)
            ).inc()
            return result
        finally:
            cache_v2_latency_seconds.labels(
                operation="get",
                cache_name=cache_name
            ).observe(time.time() - start)
```

**Dashboards**:

- Update `dashboards/grafana_dashboard.json` with Cache V2 panels
- Alert on: hit rate drop >10%, latency increase >2x, mismatch rate >5%

**Timeline**: 1 day

---

#### Task 1.4: Production Rollout

**Strategy**: Gradual percentage-based rollout

**Steps**:

1. **Week 1**: Enable `ENABLE_CACHE_V2=true` in staging (shadow mode active)
2. **Week 2**: 10% production traffic with shadow mode
3. **Week 3**: 50% production traffic
4. **Week 4**: 100% production traffic
5. **Week 5**: Remove shadow mode, deprecate legacy cache modules

**Rollback Trigger**: Any of:

- Hit rate drop >5%
- Latency increase >50%
- Error rate increase >1%
- Mismatch rate >5%

**Timeline**: 4 weeks (overlaps with other phases)

---

### Phase 2: Quick Wins - Extract Enhanced Bandit Plugins

**Objective**: Preserve RL research from deprecated modules without blocking other migrations

**Priority**: HIGH (low effort, high value)

#### Task 2.1: Extract Enhanced Bandit Logic

**Source Modules** (all deprecated):

```
src/ai/advanced_contextual_bandits.py
src/ai/advanced_bandits_router.py
src/core/routing/strategies/bandit_strategy.py
```

**Target Location**:

```
src/ultimate_discord_intelligence_bot/services/openrouter_service/plugins/
├── __init__.py
├── base_plugin.py (interface)
├── linucb_plugin.py (enhanced LinUCB)
├── thompson_sampling_plugin.py (enhanced Thompson)
└── cost_aware_plugin.py (cost optimization)
```

**Plugin Interface**:

```python
# src/ultimate_discord_intelligence_bot/services/openrouter_service/plugins/base_plugin.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BanditPlugin(ABC):
    """Base interface for routing bandit plugins"""

    @abstractmethod
    def select_action(self, context: Dict[str, Any], available_models: List[str]) -> str:
        """Select model based on context and RL policy"""
        pass

    @abstractmethod
    def update(self, context: Dict[str, Any], model: str, reward: float):
        """Update bandit with observed reward"""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current bandit state for serialization"""
        pass
```

**Enhanced LinUCB Plugin**:

```python
# Extract from src/ai/advanced_contextual_bandits.py

import numpy as np
from .base_plugin import BanditPlugin

class EnhancedLinUCBPlugin(BanditPlugin):
    """Enhanced LinUCB with advanced contextual features"""

    def __init__(self, alpha: float = 1.0, context_dim: int = 10):
        self.alpha = alpha
        self.context_dim = context_dim
        self.A = {}  # Model → inverse covariance matrix
        self.b = {}  # Model → reward vector

    def select_action(self, context: Dict[str, Any], available_models: List[str]) -> str:
        """Select model using UCB with confidence bounds"""
        context_vec = self._extract_context_features(context)

        ucb_scores = {}
        for model in available_models:
            if model not in self.A:
                self._initialize_model(model)

            # Compute UCB score
            A_inv = np.linalg.inv(self.A[model])
            theta = A_inv @ self.b[model]
            ucb = theta @ context_vec + self.alpha * np.sqrt(context_vec @ A_inv @ context_vec)
            ucb_scores[model] = ucb

        return max(ucb_scores, key=ucb_scores.get)

    def _extract_context_features(self, context: Dict[str, Any]) -> np.ndarray:
        """Extract enhanced contextual features"""
        features = []

        # Task complexity (prompt length, tokens)
        features.append(len(context.get("prompt", "")) / 1000.0)
        features.append(context.get("max_tokens", 1000) / 4000.0)

        # Temporal features (time of day, day of week)
        import datetime
        now = datetime.datetime.now()
        features.append(now.hour / 24.0)
        features.append(now.weekday() / 7.0)

        # Cost constraints
        features.append(context.get("budget_remaining", 1.0))

        # Quality requirements
        features.append(context.get("min_quality", 0.5))

        # Pad to context_dim
        while len(features) < self.context_dim:
            features.append(0.0)

        return np.array(features[:self.context_dim])

    def update(self, context: Dict[str, Any], model: str, reward: float):
        """Update model parameters with observed reward"""
        context_vec = self._extract_context_features(context)

        self.A[model] += np.outer(context_vec, context_vec)
        self.b[model] += reward * context_vec

    def _initialize_model(self, model: str):
        """Initialize parameters for new model"""
        self.A[model] = np.eye(self.context_dim)
        self.b[model] = np.zeros(self.context_dim)

    def get_state(self) -> Dict[str, Any]:
        return {
            "A": {k: v.tolist() for k, v in self.A.items()},
            "b": {k: v.tolist() for k, v in self.b.items()},
            "alpha": self.alpha
        }
```

**Integration into AdaptiveRoutingManager**:

```python
# Update src/ultimate_discord_intelligence_bot/services/openrouter_service/adaptive_routing.py

from .plugins import EnhancedLinUCBPlugin, ThompsonSamplingPlugin

class AdaptiveRoutingManager:
    def __init__(self, settings):
        self.settings = settings

        # Load plugin based on configuration
        plugin_type = settings.routing_plugin or "linucb"
        if plugin_type == "enhanced_linucb":
            self.plugin = EnhancedLinUCBPlugin(alpha=settings.ucb_alpha)
        elif plugin_type == "thompson":
            self.plugin = ThompsonSamplingPlugin()
        else:
            self.plugin = None  # Use default routing

    async def select_model(self, context: dict, available_models: list) -> str:
        if self.plugin:
            return self.plugin.select_action(context, available_models)
        else:
            # Fallback to default routing
            return available_models[0]
```

**Feature Flag**:

```bash
# .env
ENABLE_ENHANCED_BANDITS=true
ROUTING_PLUGIN=enhanced_linucb
UCB_ALPHA=1.0
```

**Success Criteria**:

- ✅ 3 plugins extracted and tested
- ✅ Integration tests pass
- ✅ A/B test shows ≥0% performance delta (no regression)

**Timeline**: 1 week

---

### Phase 3: Enhance Prompt Compression

**Objective**: Add adaptive compression strategies to reduce token costs by 20-40%

**Priority**: HIGH (quick win, immediate ROI)

#### Task 3.1: Implement Adaptive Compression Strategies

**Current State**: `src/core/prompt_compression.py` has basic compression

**Enhancement**:

```python
# Update src/core/prompt_compression.py

from enum import Enum
from typing import Protocol

class CompressionStrategy(Enum):
    SYNTAX_AWARE = "syntax_aware"  # Preserve code structure
    SEMANTIC_CLUSTERING = "semantic_clustering"  # Group similar content
    PRIORITY_BASED = "priority_based"  # Keep high-value content
    ADAPTIVE = "adaptive"  # Choose strategy based on content

class CompressorProtocol(Protocol):
    def compress(self, text: str, target_ratio: float) -> str:
        ...

class SyntaxAwareCompressor:
    """Preserve code structure during compression"""

    def compress(self, text: str, target_ratio: float) -> str:
        # Detect code blocks
        import re
        code_blocks = re.findall(r'```[\s\S]*?```', text)

        # Compress prose aggressively, code lightly
        prose = re.sub(r'```[\s\S]*?```', '<<CODE_BLOCK>>', text)
        compressed_prose = self._compress_prose(prose, target_ratio * 0.7)

        # Reinsert code blocks (lightly compressed)
        for block in code_blocks:
            compressed_block = self._compress_code(block, target_ratio * 1.2)
            compressed_prose = compressed_prose.replace('<<CODE_BLOCK>>', compressed_block, 1)

        return compressed_prose

    def _compress_prose(self, text: str, ratio: float) -> str:
        # Remove filler words, redundant whitespace
        words = text.split()
        target_words = int(len(words) * ratio)
        return ' '.join(words[:target_words])

    def _compress_code(self, code: str, ratio: float) -> str:
        # Preserve syntax, remove comments only if needed
        lines = code.split('\n')
        if ratio < 1.0:
            # Remove comments first
            lines = [l for l in lines if not l.strip().startswith('#')]
        return '\n'.join(lines)

class SemanticClusteringCompressor:
    """Group similar content and deduplicate"""

    def compress(self, text: str, target_ratio: float) -> str:
        sentences = text.split('. ')

        # Simple similarity clustering (can enhance with embeddings)
        clusters = self._cluster_sentences(sentences)

        # Keep one representative per cluster
        compressed = []
        for cluster in clusters:
            compressed.append(self._select_representative(cluster))

        return '. '.join(compressed)

    def _cluster_sentences(self, sentences: list) -> list:
        # Placeholder: simple word overlap clustering
        clusters = []
        used = set()

        for i, sent in enumerate(sentences):
            if i in used:
                continue
            cluster = [sent]
            used.add(i)

            for j, other in enumerate(sentences[i+1:], i+1):
                if j in used:
                    continue
                if self._similarity(sent, other) > 0.5:
                    cluster.append(other)
                    used.add(j)

            clusters.append(cluster)

        return clusters

    def _similarity(self, s1: str, s2: str) -> float:
        words1 = set(s1.lower().split())
        words2 = set(s2.lower().split())
        return len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0

    def _select_representative(self, cluster: list) -> str:
        # Return longest (most informative) sentence
        return max(cluster, key=len)

class AdaptiveCompressor:
    """Choose strategy based on content analysis"""

    def __init__(self):
        self.syntax_aware = SyntaxAwareCompressor()
        self.semantic = SemanticClusteringCompressor()

    def compress(self, text: str, target_ratio: float) -> str:
        # Detect content type
        if '```' in text or 'def ' in text or 'class ' in text:
            # Code-heavy content
            return self.syntax_aware.compress(text, target_ratio)
        else:
            # Prose content
            return self.semantic.compress(text, target_ratio)

# Update public API
def compress_prompt(text: str, target_ratio: float = 0.7, strategy: str = "adaptive") -> str:
    """Compress prompt using specified strategy"""
    compressors = {
        "syntax_aware": SyntaxAwareCompressor(),
        "semantic_clustering": SemanticClusteringCompressor(),
        "adaptive": AdaptiveCompressor()
    }

    compressor = compressors.get(strategy, AdaptiveCompressor())
    return compressor.compress(text, target_ratio)
```

**Metrics**:

```python
# Add to src/obs/metrics.py

prompt_compression_ratio = Histogram(
    "prompt_compression_ratio",
    "Prompt compression ratio achieved",
    ["strategy"]
)

prompt_compressed_tokens_saved_total = Counter(
    "prompt_compressed_tokens_saved_total",
    "Total tokens saved by compression",
    ["strategy"]
)
```

**A/B Testing**:

- Run adaptive vs fixed compression for 1 week
- Measure: token savings, quality score (via eval harness)
- Target: 20-40% token reduction with <5% quality drop

**Timeline**: 1 week

---

## Week 5-8: Memory & Orchestration Migrations

### Phase 4: Memory Migration (ADR-0002)

**Objective**: Consolidate 10 memory implementations to 2 (UnifiedMemoryService + plugins)

**Priority**: CRITICAL (moderate complexity, high impact)

#### Task 4.1: Create UnifiedMemoryService Facade

**Implementation**:

```python
# Create src/ultimate_discord_intelligence_bot/memory/__init__.py

from __future__ import annotations
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from memory.vector_store import VectorStore
from ultimate_discord_intelligence_bot.step_result import StepResult

@dataclass
class MemoryRecord:
    """Represents a memory record with metadata"""
    id: str
    content: str
    embedding: Optional[List[float]]
    metadata: Dict[str, Any]
    tenant: str
    workspace: str

class MemoryPlugin(Protocol):
    """Protocol for specialty memory backends"""

    async def store(self, records: List[MemoryRecord]) -> StepResult:
        ...

    async def retrieve(self, query: str, tenant: str, workspace: str, limit: int) -> StepResult:
        ...

class UnifiedMemoryService:
    """Unified memory service with pluggable backends"""

    def __init__(self):
        self._vector_store = VectorStore()
        self._plugins: Dict[str, MemoryPlugin] = {}

    def register_plugin(self, name: str, plugin: MemoryPlugin):
        """Register specialty memory backend"""
        self._plugins[name] = plugin

    async def upsert(
        self,
        tenant: str,
        workspace: str,
        records: List[Dict[str, Any]],
        creator: str = "pipeline",
        plugin: Optional[str] = None
    ) -> StepResult:
        """Store records in memory"""
        try:
            if plugin and plugin in self._plugins:
                # Use specialty backend
                memory_records = [MemoryRecord(**r, tenant=tenant, workspace=workspace) for r in records]
                return await self._plugins[plugin].store(memory_records)
            else:
                # Use default vector store
                namespace = f"{tenant}:{workspace}"
                await self._vector_store.upsert(
                    records=records,
                    namespace=namespace,
                    creator=creator
                )
                return StepResult.ok(data={"stored": len(records)})

        except Exception as e:
            return StepResult.fail(f"Memory upsert failed: {e}")

    async def search(
        self,
        tenant: str,
        workspace: str,
        query: str,
        limit: int = 10,
        plugin: Optional[str] = None
    ) -> StepResult:
        """Search memory for relevant records"""
        try:
            if plugin and plugin in self._plugins:
                return await self._plugins[plugin].retrieve(query, tenant, workspace, limit)
            else:
                namespace = f"{tenant}:{workspace}"
                results = await self._vector_store.search(
                    query=query,
                    namespace=namespace,
                    limit=limit
                )
                return StepResult.ok(data={"results": results})

        except Exception as e:
            return StepResult.fail(f"Memory search failed: {e}")

_unified_memory: Optional[UnifiedMemoryService] = None

def get_unified_memory() -> UnifiedMemoryService:
    global _unified_memory
    if _unified_memory is None:
        _unified_memory = UnifiedMemoryService()
    return _unified_memory

__all__ = [
    "MemoryRecord",
    "MemoryPlugin",
    "UnifiedMemoryService",
    "get_unified_memory",
]
```

**Timeline**: 2 days

---

#### Task 4.2: Implement Memory Plugins

**Mem0 Plugin**:

```python
# src/ultimate_discord_intelligence_bot/memory/plugins/mem0_plugin.py

from ultimate_discord_intelligence_bot.services.mem0_service import Mem0Service
from ..import MemoryPlugin, MemoryRecord, StepResult

class Mem0Plugin(MemoryPlugin):
    """Plugin for Mem0 long-term memory backend"""

    def __init__(self):
        self.service = Mem0Service()

    async def store(self, records: List[MemoryRecord]) -> StepResult:
        try:
            for record in records:
                await self.service.add_memory(
                    content=record.content,
                    user_id=f"{record.tenant}:{record.workspace}",
                    metadata=record.metadata
                )
            return StepResult.ok(data={"stored": len(records)})
        except Exception as e:
            return StepResult.fail(f"Mem0 store failed: {e}")

    async def retrieve(self, query: str, tenant: str, workspace: str, limit: int) -> StepResult:
        try:
            results = await self.service.search_memory(
                query=query,
                user_id=f"{tenant}:{workspace}",
                limit=limit
            )
            return StepResult.ok(data={"results": results})
        except Exception as e:
            return StepResult.fail(f"Mem0 retrieve failed: {e}")
```

**HippoRAG Plugin**:

```python
# src/ultimate_discord_intelligence_bot/memory/plugins/hipporag_plugin.py

# Similar structure for HippoRAG continual learning
```

**Graph Memory Plugin**:

```python
# src/ultimate_discord_intelligence_bot/memory/plugins/graph_plugin.py

# Graph-based memory operations
```

**Timeline**: 3 days (all plugins)

---

#### Task 4.3: Migrate Memory Tools

**Tools to Migrate**:

```
src/ultimate_discord_intelligence_bot/tools/
├── mem0_memory_tool.py → update to use facade + Mem0Plugin
├── graph_memory_tool.py → update to use facade + GraphPlugin
├── hipporag_continual_memory_tool.py → update to use facade + HippoRAGPlugin
└── memory_v2_tool.py → merge into unified tool
```

**Migration Pattern**:

```python
# BEFORE
from services.mem0_service import Mem0Service
mem0 = Mem0Service()
result = await mem0.add_memory(content, user_id)

# AFTER
from ultimate_discord_intelligence_bot.memory import get_unified_memory
memory = get_unified_memory()
result = await memory.upsert(
    tenant="acme",
    workspace="main",
    records=[{"content": content}],
    plugin="mem0"
)
```

**Success Criteria**:

- ✅ All 5 memory tools migrated
- ✅ Integration tests pass
- ✅ End-to-end memory workflow test passes

**Timeline**: 2 days

---

### Phase 5: Orchestration Migration (ADR-0004)

**Objective**: Consolidate 9 orchestrators to 1 with strategy pattern

**Priority**: HIGH (moderate complexity, moderate impact)

#### Task 5.1: Extract Strategy Classes

**Target Structure**:

```
src/ultimate_discord_intelligence_bot/orchestration/
├── facade.py (existing OrchestrationFacade)
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py (protocol)
│   ├── fallback_strategy.py (from fallback_orchestrator.py)
│   ├── hierarchical_strategy.py (from hierarchical_orchestrator.py)
│   ├── monitoring_strategy.py (from monitoring_orchestrator.py)
│   └── resilience_strategy.py (from resilience_orchestrator.py)
```

**Base Strategy Protocol**:

```python
# src/ultimate_discord_intelligence_bot/orchestration/strategies/base_strategy.py

from typing import Protocol, List, Any, Dict
from ultimate_discord_intelligence_bot.step_result import StepResult

class OrchestrationStrategy(Protocol):
    """Protocol for orchestration strategies"""

    async def execute_workflow(
        self,
        tasks: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> StepResult:
        """Execute workflow with strategy-specific logic"""
        ...

    def get_strategy_name(self) -> str:
        """Return strategy identifier"""
        ...
```

**Extract Fallback Strategy**:

```python
# Extract from src/ultimate_discord_intelligence_bot/fallback_orchestrator.py

from .base_strategy import OrchestrationStrategy

class FallbackStrategy:
    """Fallback orchestration with automatic retry and degradation"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def execute_workflow(self, tasks: List[Dict], context: Dict) -> StepResult:
        """Execute with fallback on failure"""
        for attempt in range(self.max_retries):
            try:
                result = await self._execute_tasks(tasks, context)
                if result.success:
                    return result

                # Try degraded version
                logger.warning(f"Attempt {attempt+1} failed, trying fallback")
                result = await self._execute_degraded(tasks, context)
                if result.success:
                    return result

            except Exception as e:
                if attempt == self.max_retries - 1:
                    return StepResult.fail(f"All fallback attempts exhausted: {e}")

        return StepResult.fail("Workflow failed with fallback")

    def get_strategy_name(self) -> str:
        return "fallback"
```

**Timeline**: 1 week (extract all 4 strategies)

---

#### Task 5.2: Update OrchestrationFacade

**Enhancement**:

```python
# Update src/ultimate_discord_intelligence_bot/orchestration/facade.py

from enum import Enum
from typing import Dict
from .strategies import (
    FallbackStrategy,
    HierarchicalStrategy,
    MonitoringStrategy,
    ResilienceStrategy
)

class OrchestrationStrategy(Enum):
    DEFAULT = "default"
    FALLBACK = "fallback"
    HIERARCHICAL = "hierarchical"
    MONITORING = "monitoring"
    RESILIENCE = "resilience"

class OrchestrationFacade:
    """Unified orchestration with pluggable strategies"""

    def __init__(self):
        self._strategies: Dict[OrchestrationStrategy, Any] = {
            OrchestrationStrategy.FALLBACK: FallbackStrategy(),
            OrchestrationStrategy.HIERARCHICAL: HierarchicalStrategy(),
            OrchestrationStrategy.MONITORING: MonitoringStrategy(),
            OrchestrationStrategy.RESILIENCE: ResilienceStrategy(),
        }
        self._default_strategy = OrchestrationStrategy.DEFAULT

    async def execute_workflow(
        self,
        tasks: List[Dict],
        context: Dict,
        strategy: Optional[OrchestrationStrategy] = None
    ) -> StepResult:
        """Execute workflow using specified strategy"""
        strategy = strategy or self._default_strategy

        if strategy == OrchestrationStrategy.DEFAULT:
            # Use autonomous_orchestrator.py
            from ..autonomous_orchestrator import AutonomousIntelligenceOrchestrator
            orchestrator = AutonomousIntelligenceOrchestrator()
            return await orchestrator.execute(tasks, context)

        elif strategy in self._strategies:
            strategy_impl = self._strategies[strategy]
            return await strategy_impl.execute_workflow(tasks, context)

        else:
            return StepResult.fail(f"Unknown strategy: {strategy}")
```

**Timeline**: 2 days

---

#### Task 5.3: Migrate Orchestrator Callers

**Commands**:

```bash
# Find all direct orchestrator imports
grep -r "from.*fallback_orchestrator import" src/ --include="*.py"
grep -r "from.*hierarchical_orchestrator import" src/ --include="*.py"
grep -r "from.*monitoring_orchestrator import" src/ --include="*.py"

# Replace with facade
# (Manual review + multi_replace_string_in_file)
```

**Migration Pattern**:

```python
# BEFORE
from fallback_orchestrator import FallbackOrchestrator
orch = FallbackOrchestrator()
result = await orch.execute(tasks)

# AFTER
from ultimate_discord_intelligence_bot.orchestration import (
    get_orchestrator,
    OrchestrationStrategy
)
orch = get_orchestrator(OrchestrationStrategy.FALLBACK)
result = await orch.execute_workflow(tasks, context)
```

**Success Criteria**:

- ✅ Zero direct orchestrator imports
- ✅ All workflows use facade
- ✅ Integration tests pass

**Timeline**: 3 days

---

## Week 9-12: Routing & Analytics Completion

### Phase 6: Routing Migration (ADR-0003)

**Objective**: Consolidate 15+ routers to 2 (OpenRouterService + ModelRouter)

**Priority**: CRITICAL (high complexity, high impact)

#### Task 6.1: Extract RL Logic to Plugins

**(Already covered in Phase 2 - Enhanced Bandit Plugins)**

---

#### Task 6.2: Migrate Router Callers

**Files with Deprecated Router Imports**:

```bash
# Audit command
grep -r "from core.routing" src/ --include="*.py" > /tmp/routing_audit.txt
grep -r "from ai.routing" src/ --include="*.py" >> /tmp/routing_audit.txt
grep -r "from core.router import" src/ --include="*.py" >> /tmp/routing_audit.txt
grep -r "from core.llm_router import" src/ --include="*.py" >> /tmp/routing_audit.txt
```

**Migration Pattern**:

```python
# BEFORE
from ai.routing import LinUCBRouter
router = LinUCBRouter()
model = router.select_model(context)

# AFTER
from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
service = OpenRouterService(tenant_ctx=ctx)
result = await service.route(
    prompt=prompt,
    task_type=task_type,
    tenant_context=ctx
)
model = result.data["selected_model"]
```

**Commands**:

```bash
# For each file in routing_audit.txt:
# 1. Read file
# 2. Identify router usage
# 3. Replace with OpenRouterService
# 4. Update tests
# 5. Verify with make test-fast
```

**Success Criteria**:

- ✅ Zero imports from `core/routing/`, `ai/routing/`, `core/router.py`, `core/llm_router.py`
- ✅ All routing via OpenRouterService
- ✅ RL capabilities preserved in plugins
- ✅ Shadow mode shows quality parity

**Timeline**: 2 weeks (complex dependency graph)

---

#### Task 6.3: Shadow Mode Validation

**Implementation**:

```python
# src/ultimate_discord_intelligence_bot/services/routing_shadow_harness.py

class RoutingShadowHarness:
    """Runs legacy and unified routing in parallel"""

    def __init__(self):
        self.unified_service = OpenRouterService()
        # Keep ONE legacy router for comparison
        from ai.routing import LinUCBRouter
        self.legacy_router = LinUCBRouter()
        self.stats = {"agreement": 0, "disagreement": 0, "unified_wins": 0}

    async def select_model(self, prompt: str, context: dict) -> str:
        """Select model using both approaches and compare"""
        unified_result = await self.unified_service.route(prompt, context)
        legacy_result = self.legacy_router.select_model(context)

        if unified_result.data["selected_model"] == legacy_result:
            self.stats["agreement"] += 1
        else:
            self.stats["disagreement"] += 1

        # Return unified result (production path)
        return unified_result.data["selected_model"]
```

**Deployment**:

1. Enable `ENABLE_ROUTING_SHADOW_MODE=true`
2. Run in staging for 1 week
3. Monitor: agreement rate, quality scores, latency
4. Acceptable: >80% agreement, <10% quality variance

**Timeline**: 1 week validation

---

### Phase 7: Analytics Migration (ADR-0005)

**Objective**: Consolidate 12+ performance modules to 2 (obs/metrics + AnalyticsService)

**Priority**: HIGH (moderate complexity, moderate impact)

#### Task 7.1: Consolidate AgentPerformanceMonitor

**Choose Canonical**:

```
src/ultimate_discord_intelligence_bot/agent_training/performance_monitor_final.py
```

**Deprecate Duplicates**:

```
src/ultimate_discord_intelligence_bot/agent_training/performance_monitor.py
src/ai/ai_enhanced_performance_monitor.py
```

**Commands**:

```bash
# Find imports
grep -r "from.*performance_monitor import" src/ --include="*.py" | grep -v "performance_monitor_final"

# Replace with canonical
# (Manual multi_replace)

# Delete duplicates
rm src/ultimate_discord_intelligence_bot/agent_training/performance_monitor.py
rm src/ai/ai_enhanced_performance_monitor.py
```

**Timeline**: 1 day

---

#### Task 7.2: Migrate Dashboard Callers to AnalyticsService

**Files to Update**:

```
src/ultimate_discord_intelligence_bot/
├── performance_dashboard.py → migrate to AnalyticsService
├── performance_optimization_engine.py → migrate to AnalyticsService
├── advanced_performance_analytics*.py (7 files) → deprecate
```

**Migration Pattern**:

```python
# BEFORE (accesses StepResult internals - anti-pattern)
from performance_dashboard import PerformanceDashboard
dashboard = PerformanceDashboard()
metrics = dashboard.compute_health_score(step_result._internal_metrics)

# AFTER (uses obs/metrics)
from ultimate_discord_intelligence_bot.observability import get_analytics_service
from obs.metrics import get_metrics

analytics = get_analytics_service()
metrics_data = get_metrics().get_all()
health = analytics.compute_system_health(metrics_data)
```

**Remove StepResult Internals Access**:

```bash
# Find anti-patterns
grep -r "step_result\._" src/ --include="*.py"
grep -r "result\._internal" src/ --include="*.py"

# All should use obs.metrics instead
```

**Success Criteria**:

- ✅ Zero StepResult internals access
- ✅ All dashboards use AnalyticsService
- ✅ 7 advanced_performance_analytics* files deprecated

**Timeline**: 1 week

---

#### Task 7.3: Update Tools

**AdvancedPerformanceAnalyticsTool Migration**:

```python
# Update src/ultimate_discord_intelligence_bot/tools/advanced_performance_analytics_tool.py

# BEFORE
from advanced_performance_analytics import AdvancedPerformanceAnalytics
analytics = AdvancedPerformanceAnalytics()

# AFTER
from ultimate_discord_intelligence_bot.observability import get_analytics_service
analytics = get_analytics_service()
```

**Timeline**: 1 day

---

### Phase 8: Final Cleanup & Documentation

**Objective**: Remove deprecated modules, update documentation, validate completion

#### Task 8.1: Delete Deprecated Modules

**Directories to Remove**:

```bash
rm -rf src/core/routing/
rm -rf src/ai/routing/
rm -rf src/performance/
rm -rf src/ultimate_discord_intelligence_bot/caching/
```

**Files to Remove**:

```bash
# Cache
rm src/ultimate_discord_intelligence_bot/services/cache.py
rm src/ultimate_discord_intelligence_bot/services/rl_cache_optimizer.py
rm src/ultimate_discord_intelligence_bot/services/cache_shadow_harness.py

# Memory
rm src/ultimate_discord_intelligence_bot/services/memory_service.py
rm src/ultimate_discord_intelligence_bot/knowledge/unified_memory.py

# Routing
rm src/core/router.py
rm src/core/llm_router.py
rm src/ultimate_discord_intelligence_bot/services/rl_model_router.py
rm src/ultimate_discord_intelligence_bot/services/semantic_router_service.py
rm src/ultimate_discord_intelligence_bot/routing/unified_router.py

# Orchestration
rm src/ultimate_discord_intelligence_bot/enhanced_autonomous_orchestrator.py
rm src/ultimate_discord_intelligence_bot/fallback_orchestrator.py
rm src/ultimate_discord_intelligence_bot/orchestration/unified_orchestrator.py
rm src/ultimate_discord_intelligence_bot/services/hierarchical_orchestrator.py
rm src/ultimate_discord_intelligence_bot/services/monitoring_orchestrator.py
rm src/core/resilience_orchestrator.py

# Analytics
rm src/ultimate_discord_intelligence_bot/performance_dashboard.py
rm src/ultimate_discord_intelligence_bot/performance_optimization_engine.py
rm src/ultimate_discord_intelligence_bot/advanced_performance_analytics*.py

# AI routing
rm src/ai/enhanced_ai_router.py
rm src/ai/adaptive_ai_router.py
rm src/ai/performance_router.py
rm src/ai/advanced_bandits_router.py
rm src/ai/advanced_contextual_bandits.py
```

**Verification**:

```bash
# Should return zero deprecated imports
make guards
make compliance

# All tests should pass
make test

# Type checking should pass
make type
```

**Timeline**: 2 days

---

#### Task 8.2: Update Documentation

**Files to Update**:

```
docs/
├── architecture/
│   ├── consolidation-status.md → mark 100% complete
│   ├── adr-0001-cache-platform.md → update status to "Implemented"
│   ├── adr-0002-memory-unification.md → update status
│   ├── adr-0003-routing-consolidation.md → update status
│   ├── adr-0004-orchestrator-unification.md → update status
│   └── adr-0005-analytics-consolidation.md → update status
├── tools_reference.md → update for unified APIs
└── configuration.md → document new feature flags
```

**New Documentation**:

```
docs/
├── migration_guides/
│   ├── cache_migration.md (already exists)
│   ├── memory_migration.md
│   ├── routing_migration.md
│   ├── orchestration_migration.md
│   └── analytics_migration.md
```

**Timeline**: 2 days

---

#### Task 8.3: Performance Benchmarking

**Baseline vs Post-Consolidation**:

```bash
# Run performance benchmarks
python benchmarks/performance_benchmarks.py --mode=before_after

# Compare metrics:
# - Cache hit rates
# - Routing decision quality
# - Memory retrieval accuracy
# - Orchestration latency
# - Overall system health score
```

**Expected Outcomes**:

- Cache hit rate: ≥0% delta (parity)
- Routing quality: ≥0% delta
- Memory accuracy: ≥0% delta
- Latency: ≤+10% (acceptable overhead)
- Code complexity: -50% (60 modules removed)

**Timeline**: 2 days

---

## Success Criteria & Acceptance

### Technical Metrics

- ✅ **Code Reduction**: 60+ modules deprecated and removed
- ✅ **Import Compliance**: Zero imports from deprecated paths
- ✅ **Test Coverage**: All 281+ tests passing
- ✅ **Type Safety**: make type-guard passes (no regressions)
- ✅ **Performance**: <10% latency delta, parity on hit rates/quality

### Operational Metrics

- ✅ **Feature Flags**: All 5 flags (ENABLE_CACHE_V2, etc.) operational
- ✅ **Observability**: All metrics instrumented and dashboards updated
- ✅ **Documentation**: All ADRs marked "Implemented", migration guides complete
- ✅ **CI/CD**: Guards enforce no new deprecated code

### Business Metrics

- ✅ **Maintainability**: -50% code complexity, single APIs per subsystem
- ✅ **Onboarding**: -50% ramp-up time (simpler architecture)
- ✅ **Cost**: 20-40% token savings from prompt compression
- ✅ **Quality**: ≥0% delta on all quality metrics

---

## Risk Management

### High-Risk Items

1. **Routing Migration Complexity**
   - **Risk**: 15+ routers with complex dependencies
   - **Mitigation**: Shadow mode testing, gradual rollout, instant rollback
   - **Contingency**: Keep ONE legacy router active for 1 month post-migration

2. **Cache Hit Rate Variance**
   - **Risk**: New cache might have different hit rates
   - **Mitigation**: Shadow harness validates <5% variance before cutover
   - **Contingency**: Instant rollback via ENABLE_CACHE_V2=false

3. **Incomplete Migration Discovery**
   - **Risk**: Missed deprecated imports cause runtime failures
   - **Mitigation**: Automated grep audits + CI guards
   - **Contingency**: Fast-track import fixes (<1 day)

### Medium-Risk Items

1. **Performance Regression**
   - **Mitigation**: Benchmark before/after, <10% delta threshold
   - **Contingency**: Performance profiling + optimization sprint

2. **Integration Test Gaps**
   - **Mitigation**: Expand integration test coverage during migration
   - **Contingency**: Manual end-to-end testing pre-production

### Rollback Plan

**Per-Phase Rollback**:

- Phase 1 (Cache): `ENABLE_CACHE_V2=false`
- Phase 6 (Routing): `ENABLE_UNIFIED_ROUTING=false`
- Phase 7 (Analytics): `ENABLE_ANALYTICS_V2=false`

**Full Rollback**:

1. Revert all feature flags to false
2. Restore deleted modules from git history
3. Rollback imports via automated script
4. Re-run full test suite
5. Deploy rollback to production (ETA: <2 hours)

---

## Timeline Summary

| Week | Phase | Tasks | Outcome |
|------|-------|-------|---------|
| 1-2 | Cache + Bandits | Migrate cache, extract plugins | UnifiedCache operational |
| 3-4 | Prompt Compression | Adaptive strategies | 20-40% token savings |
| 5-6 | Memory | Facade + plugins | UnifiedMemoryService operational |
| 7-8 | Orchestration | Strategies extraction | OrchestrationFacade complete |
| 9-10 | Routing | Migrate callers, shadow test | OpenRouterService unified |
| 11-12 | Analytics + Cleanup | Consolidate monitors, delete deprecated | 100% consolidation complete |

**Total Duration**: 12 weeks
**Estimated Effort**: ~400 hours (split across team)
**Go-Live Date**: Week of January 6, 2026

---

## Appendix A: Command Reference

```bash
# Audit deprecated imports
grep -r "from core.routing" src/ --include="*.py"
grep -r "from ai.routing" src/ --include="*.py"
grep -r "from performance" src/ --include="*.py"

# Run guards
make guards
make compliance
make type-guard

# Test workflows
make test-fast      # 8s quick validation
make test           # 10s full suite
make test-integration  # Slow end-to-end tests

# Enable feature flags (staging)
export ENABLE_CACHE_V2=true
export ENABLE_ENHANCED_BANDITS=true
export ENABLE_UNIFIED_ROUTING=true
export ENABLE_ANALYTICS_V2=true

# Performance benchmarking
python benchmarks/performance_benchmarks.py --mode=consolidation_progress

# Documentation generation
make docs
make docs-flags-write
```

---

## Appendix B: Migration Checklists

### Cache Migration Checklist

- [x] unified_cache_tool.py migrated to UnifiedCache
- [ ] services/cache.py callers migrated
- [ ] caching/ module callers migrated
- [ ] performance/cache_* callers migrated
- [ ] Shadow harness implemented
- [ ] Metrics instrumented
- [ ] Staging validation (1 week)
- [ ] Production rollout (10% → 50% → 100%)
- [ ] Legacy cache modules deleted

### Memory Migration Checklist

- [ ] UnifiedMemoryService facade created
- [ ] Mem0Plugin implemented
- [ ] HippoRAGPlugin implemented
- [ ] GraphPlugin implemented
- [ ] mem0_memory_tool migrated
- [ ] graph_memory_tool migrated
- [ ] hipporag_continual_memory_tool migrated
- [ ] memory_v2_tool merged
- [ ] Integration tests pass
- [ ] Legacy memory modules deleted

### Routing Migration Checklist

- [ ] Enhanced bandit plugins extracted
- [ ] core/routing/ callers migrated
- [ ] ai/routing/ callers migrated
- [ ] services/rl_model_router callers migrated
- [ ] Shadow mode validation
- [ ] Integration tests pass
- [ ] Legacy routing modules deleted

### Orchestration Migration Checklist

- [ ] FallbackStrategy extracted
- [ ] HierarchicalStrategy extracted
- [ ] MonitoringStrategy extracted
- [ ] ResilienceStrategy extracted
- [ ] OrchestrationFacade updated
- [ ] Orchestrator callers migrated
- [ ] Integration tests pass
- [ ] Legacy orchestrators deleted

### Analytics Migration Checklist

- [ ] AgentPerformanceMonitor consolidated (choose one)
- [ ] performance_dashboard migrated to AnalyticsService
- [ ] performance_optimization_engine migrated
- [ ] advanced_performance_analytics* files deprecated
- [ ] StepResult internals access removed
- [ ] Tools migrated to AnalyticsService
- [ ] Metrics instrumented
- [ ] Legacy analytics modules deleted

---

## Appendix C: Contact & Escalation

**Project Lead**: Architecture Group
**Technical Questions**: See ADRs in `docs/architecture/`
**Blockers**: Create GitHub issue with label `consolidation-blocker`
**Daily Standups**: Review progress via todo list
**Weekly Review**: Update consolidation-status.md

---

**Document Status**: ACTIVE
**Last Updated**: October 19, 2025
**Next Review**: Weekly during execution
