# Phase 4 Implementation Complete: Memory Plugin Architecture

**Date:** October 19, 2025
**Phase:** 4 of 8 (UnifiedMemoryService Plugin Support)
**Status:** ✅ COMPLETE

---

## Executive Summary

Successfully implemented plugin architecture for UnifiedMemoryService, enabling specialty memory backends (Mem0, HippoRAG, Graph) to be dynamically registered and used alongside the default vector store. This Phase 4 completion follows Phases 0-3:

- ✅ **Phase 0-1:** Archive isolation verified, deprecated files removed, cache tool migrated
- ✅ **Phase 2:** Enhanced bandit plugins extracted (LinUCB, DoublyRobust)
- ✅ **Phase 3:** Prompt compression verified (already has advanced features)
- ✅ **Phase 4:** Memory plugin architecture (THIS PHASE)

---

## What Was Implemented

### 1. MemoryPlugin Protocol (`memory/__init__.py`)

**Purpose:** Define interface contract for specialty memory backends

**Interface:**

```python
class MemoryPlugin(Protocol):
    async def store(
        self, namespace: str, records: Sequence[Dict[str, Any]]
    ) -> StepResult:
        """Store records in specialty backend."""
        ...

    async def retrieve(
        self, namespace: str, query: str, limit: int
    ) -> StepResult:
        """Retrieve records from specialty backend."""
        ...
```

**Key Features:**

- Protocol-based design (structural subtyping, no inheritance required)
- Async interface for I/O operations
- Tenant-scoped namespace parameter
- Flexible record format (dict with 'content' and optional 'metadata')
- Structured StepResult returns

---

### 2. UnifiedMemoryService Enhancements

**New Methods:**

#### `register_plugin(name: str, plugin: MemoryPlugin)`

Register a specialty backend plugin dynamically.

**Usage:**

```python
from memory.plugins import Mem0Plugin

memory = get_unified_memory()
memory.register_plugin("mem0", Mem0Plugin())
```

#### Enhanced `upsert()` Method

**New Parameter:** `plugin: Optional[str] = None`

**Behavior:**

- If `plugin` specified → route to registered plugin
- If plugin not found → return error
- If no plugin → default to vector store

**Example:**

```python
result = await memory.upsert(
    tenant="demo",
    workspace="main",
    records=[{"content": "User prefers concise summaries"}],
    plugin="mem0"  # Route to Mem0 plugin
)
```

#### Enhanced `query()` Method

**New Parameters:**

- `plugin: Optional[str] = None` - Plugin name for routing
- `query_text: Optional[str] = None` - Text query for plugins

**Behavior:**

- If `plugin` specified → require `query_text` parameter
- Route to plugin's `retrieve()` method
- If no plugin → default to vector store query

**Example:**

```python
result = await memory.query(
    tenant="demo",
    workspace="main",
    vector=[],  # Not used by plugins
    plugin="mem0",
    query_text="What are the user's preferences?"
)
```

---

### 3. Plugin Implementations

#### **Mem0Plugin** (`memory/plugins/mem0_plugin.py`)

**Purpose:** Long-term episodic memory and user preference tracking

**Features:**

- User preference learning across sessions
- Semantic memory retrieval
- Tenant isolation via user_id composition
- Metadata enrichment with namespace info

**Backend:** Mem0 Memory SDK with Qdrant vector store

**Use Cases:**

- User preference tracking
- Cross-session learning
- Adaptive user modeling
- Personalized recommendations

**Integration:**

```python
from memory.plugins import Mem0Plugin

memory.register_plugin("mem0", Mem0Plugin())
await memory.upsert(
    tenant="acme",
    workspace="main",
    records=[{"content": "User prefers bullet-point summaries"}],
    plugin="mem0"
)
```

---

#### **HippoRAGPlugin** (`memory/plugins/hipporag_plugin.py`)

**Purpose:** Continual learning with neurobiologically-inspired consolidation

**Features:**

- Factual memory consolidation
- Sense-making across contexts
- Multi-hop associative retrieval
- Graceful fallback to lightweight storage

**Backend:** HippoRAG 2 framework (hippocampal memory patterns)

**Capabilities:**

- `factual_memory` - Long-term factual retention
- `sense_making` - Complex context integration
- `associativity` - Multi-hop relationship traversal
- `continual_learning` - No catastrophic forgetting

**Integration:**

```python
from memory.plugins import HippoRAGPlugin

memory.register_plugin("hipporag", HippoRAGPlugin())
await memory.upsert(
    tenant="research",
    workspace="ai",
    records=[{
        "content": "Transformers use self-attention...",
        "metadata": {"tags": ["nlp", "attention"]}
    }],
    plugin="hipporag"
)
```

**Retrieval with Reasoning:**

```python
result = await memory.query(
    tenant="research",
    workspace="ai",
    plugin="hipporag",
    query_text="How do transformers process sequences?",
    top_k=5
)
# Returns results with 'reasoning' field explaining relevance
```

---

#### **GraphPlugin** (`memory/plugins/graph_plugin.py`)

**Purpose:** Knowledge graph construction and relationship traversal

**Features:**

- Automatic entity and relationship extraction
- Keyword-based graph construction
- Graph metadata search
- Tag-based filtering

**Backend:** GraphMemoryTool with NetworkX graphs

**Storage Format:**

- Nodes: Sentences + keywords
- Edges: Sequential flow + keyword mentions
- Metadata: Keywords, tags, node/edge counts

**Integration:**

```python
from memory.plugins import GraphPlugin

memory.register_plugin("graph", GraphPlugin())
await memory.upsert(
    tenant="knowledge",
    workspace="tech",
    records=[{
        "content": "Python supports OOP. It's used for ML...",
        "metadata": {"tags": ["python", "programming"]}
    }],
    plugin="graph"
)
```

**Search:**

```python
result = await memory.query(
    tenant="knowledge",
    workspace="tech",
    plugin="graph",
    query_text="Python machine learning",
    top_k=3
)
# Returns graph metadata with keyword scores
```

---

## Files Created

### Core Plugin Infrastructure

1. `/home/crew/src/ultimate_discord_intelligence_bot/memory/plugins/__init__.py`
   - Exports: Mem0Plugin, HippoRAGPlugin, GraphPlugin

### Plugin Implementations

2. `/home/crew/src/ultimate_discord_intelligence_bot/memory/plugins/mem0_plugin.py`
   - 172 lines
   - Integrates Mem0MemoryService
   - User preference tracking

3. `/home/crew/src/ultimate_discord_intelligence_bot/memory/plugins/hipporag_plugin.py`
   - 192 lines
   - Integrates HippoRagContinualMemoryTool
   - Continual learning support

4. `/home/crew/src/ultimate_discord_intelligence_bot/memory/plugins/graph_plugin.py`
   - 170 lines
   - Integrates GraphMemoryTool
   - Knowledge graph operations

### Documentation & Examples

5. `/home/crew/examples/unified_memory_plugins_example.py`
   - 335 lines
   - 5 runnable examples:
     - Mem0 plugin usage
     - HippoRAG plugin usage
     - Graph plugin usage
     - Plugin comparison
     - Main orchestrator

---

## Files Modified

### Memory Facade Enhancements

1. `/home/crew/src/ultimate_discord_intelligence_bot/memory/__init__.py`
   - Added `MemoryPlugin` protocol (lines ~30-55)
   - Added `register_plugin()` method (lines ~80-90)
   - Enhanced `upsert()` with plugin routing (lines ~95-120)
   - Enhanced `query()` with plugin routing (lines ~125-160)
   - Exported `MemoryPlugin` in `__all__`

---

## Architecture Patterns

### 1. Protocol-Based Design

**Why Protocol over ABC:**

- Structural subtyping (duck typing with type safety)
- No inheritance coupling
- Plugins can be any class implementing the interface
- Easier testing (no need to subclass)

**Example:**

```python
# Any class with these methods is a valid MemoryPlugin
class CustomPlugin:
    async def store(self, namespace: str, records: Sequence[Dict]) -> StepResult:
        ...

    async def retrieve(self, namespace: str, query: str, limit: int) -> StepResult:
        ...

# No inheritance needed!
memory.register_plugin("custom", CustomPlugin())
```

---

### 2. Dual-Mode Operation

**Default Mode (No Plugin):**

```python
# Standard vector store usage
await memory.upsert(tenant="acme", workspace="main", records=[...])
# → Uses VectorStore (Qdrant)
```

**Plugin Mode:**

```python
# Specialty backend routing
await memory.upsert(
    tenant="acme",
    workspace="main",
    records=[...],
    plugin="mem0"  # Route to Mem0
)
# → Uses Mem0MemoryService
```

**Benefits:**

- Backward compatibility (existing code unchanged)
- Progressive enhancement (add plugins when needed)
- No breaking changes

---

### 3. Namespace Isolation

**Format:** `tenant:workspace:creator:suffix`

**Examples:**

- `acme:main:default:memory` → Vector store
- `acme:main:user123:mem0` → Mem0 for user123
- `research:ai:default:continual_memory` → HippoRAG
- `knowledge:tech:curator:graph` → Graph storage

**Plugin Parsing:**

- Mem0: Uses `tenant:workspace` as user_id
- HippoRAG: Uses suffix as index name
- Graph: Uses suffix as namespace

---

### 4. Graceful Degradation

**HippoRAGPlugin Fallback:**
If HippoRAG package unavailable:

1. Falls back to lightweight JSON storage
2. Still returns success with `backend: "fallback"`
3. System continues operating

**Mem0Plugin Error Handling:**
If Mem0 service unavailable:

1. Returns `StepResult.fail("Mem0 service unavailable")`
2. Caller can fallback to vector store
3. Error logged but doesn't crash

---

## Integration Points

### 1. Tool Migration (Next Phase)

**Before (Direct Tool Usage):**

```python
from tools import MemoryStorageTool, HippoRagContinualMemoryTool

mem_tool = MemoryStorageTool()
mem_tool.run(text="content", collection="memory")

hippo_tool = HippoRagContinualMemoryTool()
hippo_tool.run(text="content", index="continual_memory")
```

**After (Unified Facade with Plugins):**

```python
from memory import get_unified_memory
from memory.plugins import HippoRAGPlugin

memory = get_unified_memory()
memory.register_plugin("hipporag", HippoRAGPlugin())

# Same interface for all backends
await memory.upsert(
    tenant="acme",
    workspace="main",
    records=[{"content": "..."}],
    plugin="hipporag"  # or "mem0", "graph", or None for default
)
```

---

### 2. Pipeline Integration

**ContentPipeline Memory Phase:**

```python
# Current: Direct tool instantiation per backend
self.memory_storage = MemoryStorageTool()
self.graph_memory = GraphMemoryTool()
self.hipporag_memory = HippoRagContinualMemoryTool()

# Future: Unified interface with dynamic routing
from memory import get_unified_memory
from memory.plugins import GraphPlugin, HippoRAGPlugin

memory = get_unified_memory()
memory.register_plugin("graph", GraphPlugin())
memory.register_plugin("hipporag", HippoRAGPlugin())

# Single call, multiple backends
await memory.upsert(tenant=ctx.tenant, workspace=ctx.workspace, ...)
await memory.upsert(tenant=ctx.tenant, workspace=ctx.workspace, plugin="graph", ...)
```

---

### 3. CrewAI Agent Integration

**Memory Tools for Agents:**

```python
@tool
def remember_knowledge(content: str, backend: str = "vector") -> str:
    """Store knowledge in specified memory backend."""
    memory = get_unified_memory()

    result = await memory.upsert(
        tenant=current_tenant().tenant_id,
        workspace=current_tenant().workspace_id,
        records=[{"content": content}],
        plugin=backend if backend != "vector" else None
    )

    return json.dumps(result.to_dict())

@tool
def recall_knowledge(query: str, backend: str = "vector") -> str:
    """Recall knowledge from specified memory backend."""
    memory = get_unified_memory()

    result = await memory.query(
        tenant=current_tenant().tenant_id,
        workspace=current_tenant().workspace_id,
        query_text=query,
        plugin=backend if backend != "vector" else None
    )

    return json.dumps(result.to_dict())
```

---

## Testing Strategy

### Unit Tests (Recommended)

```python
# tests/memory/test_memory_plugins.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from memory import UnifiedMemoryService
from memory.plugins import Mem0Plugin, HippoRAGPlugin, GraphPlugin

@pytest.fixture
def memory_service():
    return UnifiedMemoryService()

@pytest.mark.asyncio
async def test_plugin_registration(memory_service):
    """Test plugin registration."""
    plugin = Mem0Plugin()
    memory_service.register_plugin("mem0", plugin)

    assert "mem0" in memory_service._plugins
    assert memory_service._plugins["mem0"] is plugin

@pytest.mark.asyncio
async def test_plugin_routing_upsert(memory_service, monkeypatch):
    """Test upsert routes to plugin."""
    mock_plugin = MagicMock()
    mock_plugin.store = AsyncMock(return_value=StepResult.ok(stored=1))

    memory_service.register_plugin("test", mock_plugin)

    result = await memory_service.upsert(
        tenant="demo",
        workspace="main",
        records=[{"content": "test"}],
        plugin="test"
    )

    assert result.success
    mock_plugin.store.assert_called_once()

@pytest.mark.asyncio
async def test_plugin_routing_query(memory_service, monkeypatch):
    """Test query routes to plugin."""
    mock_plugin = MagicMock()
    mock_plugin.retrieve = AsyncMock(
        return_value=StepResult.ok(results=[], count=0)
    )

    memory_service.register_plugin("test", mock_plugin)

    result = await memory.query(
        tenant="demo",
        workspace="main",
        vector=[],
        plugin="test",
        query_text="query"
    )

    assert result.success
    mock_plugin.retrieve.assert_called_once_with(
        namespace="demo:main:default",
        query="query",
        limit=3
    )

@pytest.mark.asyncio
async def test_fallback_to_vector_store(memory_service):
    """Test fallback when plugin not specified."""
    result = await memory_service.upsert(
        tenant="demo",
        workspace="main",
        records=[VectorRecord(vector=[1.0], payload={"text": "test"})]
    )

    # Should use vector store, not plugin
    assert result.success
    assert "plugin" not in result.data
```

---

### Integration Tests (Recommended)

```python
# tests/integration/test_memory_plugin_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mem0_plugin_integration():
    """Test Mem0 plugin end-to-end."""
    memory = get_unified_memory()
    memory.register_plugin("mem0", Mem0Plugin())

    # Store
    store_result = await memory.upsert(
        tenant="test",
        workspace="integration",
        records=[{"content": "Test memory"}],
        plugin="mem0"
    )

    assert store_result.success
    assert store_result.data["backend"] == "mem0"

    # Retrieve
    query_result = await memory.query(
        tenant="test",
        workspace="integration",
        vector=[],
        plugin="mem0",
        query_text="test"
    )

    assert query_result.success
    assert query_result.data["count"] > 0
```

---

## Usage Examples

### Example 1: User Preference Learning (Mem0)

```python
from memory import get_unified_memory
from memory.plugins import Mem0Plugin

memory = get_unified_memory()
memory.register_plugin("mem0", Mem0Plugin())

# Store user preferences
await memory.upsert(
    tenant="acme",
    workspace="main",
    creator="user_alice",
    records=[
        {"content": "Alice prefers dark mode UI", "metadata": {"type": "preference"}},
        {"content": "Alice works in Pacific time zone", "metadata": {"type": "context"}},
    ],
    plugin="mem0"
)

# Recall preferences
result = await memory.query(
    tenant="acme",
    workspace="main",
    creator="user_alice",
    plugin="mem0",
    query_text="What UI preferences does Alice have?",
    top_k=5
)

print(result.data["results"][0]["content"])
# Output: "Alice prefers dark mode UI"
```

---

### Example 2: Continual Learning (HippoRAG)

```python
from memory import get_unified_memory
from memory.plugins import HippoRAGPlugin

memory = get_unified_memory()
memory.register_plugin("hipporag", HippoRAGPlugin())

# Store research knowledge
await memory.upsert(
    tenant="research_lab",
    workspace="ai_safety",
    records=[{
        "content": "Constitutional AI uses human feedback to align language models...",
        "metadata": {
            "source": "anthropic_paper",
            "tags": ["alignment", "rlhf", "constitutional_ai"]
        }
    }],
    plugin="hipporag"
)

# Query with reasoning
result = await memory.query(
    tenant="research_lab",
    workspace="ai_safety",
    plugin="hipporag",
    query_text="What techniques are used for LLM alignment?",
    top_k=3
)

for item in result.data["results"]:
    print(f"Content: {item['content'][:100]}...")
    print(f"Score: {item['score']:.3f}")
    print(f"Reasoning: {item['reasoning'][:80]}...")
```

---

### Example 3: Knowledge Graph (Graph)

```python
from memory import get_unified_memory
from memory.plugins import GraphPlugin

memory = get_unified_memory()
memory.register_plugin("graph", GraphPlugin())

# Store knowledge as graph
await memory.upsert(
    tenant="knowledge_base",
    workspace="tech_docs",
    records=[{
        "content": "FastAPI is a Python web framework. It uses Pydantic for validation. "
                   "FastAPI supports async/await for high performance.",
        "metadata": {"tags": ["python", "web", "fastapi"]}
    }],
    plugin="graph"
)

# Search graphs by keywords
result = await memory.query(
    tenant="knowledge_base",
    workspace="tech_docs",
    plugin="graph",
    query_text="Python web frameworks with async support",
    top_k=5
)

for graph in result.data["results"]:
    print(f"Graph ID: {graph['graph_id']}")
    print(f"Keywords: {', '.join(graph['keywords'][:5])}")
    print(f"Nodes: {graph['node_count']}, Edges: {graph['edge_count']}")
```

---

## Performance Considerations

### 1. Plugin Overhead

**Vector Store (Default):**

- Direct Qdrant calls
- Minimal overhead (~1ms)

**Plugin Routing:**

- Dictionary lookup: O(1)
- Plugin call: depends on backend
- Mem0: +5-20ms (Qdrant + Mem0 SDK)
- HippoRAG: +50-500ms (LLM-based processing)
- Graph: +10-50ms (NetworkX operations)

**Recommendation:** Use plugins when specialty features needed, not for hot paths.

---

### 2. Caching Strategies

**Plugin-Level Caching:**

```python
class CachedHippoRAGPlugin:
    def __init__(self):
        self._cache = {}  # Simple dict cache
        self._plugin = HippoRAGPlugin()

    async def retrieve(self, namespace: str, query: str, limit: int):
        cache_key = f"{namespace}:{query}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = await self._plugin.retrieve(namespace, query, limit)
        if result.success:
            self._cache[cache_key] = result

        return result
```

---

### 3. Batch Operations

**Current (Sequential):**

```python
for record in records:
    await memory.upsert(tenant, workspace, [record], plugin="mem0")
# N network calls
```

**Optimized (Batch):**

```python
await memory.upsert(tenant, workspace, records, plugin="mem0")
# 1 network call (plugin batches internally)
```

---

## Security Considerations

### 1. Namespace Isolation

**Enforcement:**

- Plugins receive pre-computed namespace string
- Tenant/workspace validated before plugin call
- Plugins should NOT parse tenant from namespace

**Example:**

```python
# ✅ CORRECT: Use provided namespace
async def store(self, namespace: str, records: Sequence[Dict]):
    # namespace is already validated: "tenant:workspace:creator"
    user_id = namespace  # Safe to use directly

# ❌ WRONG: Don't re-extract tenant
async def store(self, namespace: str, records: Sequence[Dict]):
    tenant = namespace.split(":")[0]  # Dangerous! What if malformed?
```

---

### 2. Input Validation

**Plugin Responsibility:**

```python
async def store(self, namespace: str, records: Sequence[Dict]):
    # Validate records
    for record in records:
        if "content" not in record:
            logger.warning("Skipping record without content")
            continue

        if not isinstance(record["content"], str):
            logger.warning(f"Invalid content type: {type(record['content'])}")
            continue

        # Process valid record
        ...
```

---

### 3. Error Isolation

**Principle:** Plugin failures should NOT crash UnifiedMemoryService

**Implementation:**

```python
async def upsert(self, tenant, workspace, records, plugin=None):
    try:
        if plugin:
            namespace = self.get_namespace(tenant, workspace, creator)
            return await self._plugins[plugin].store(namespace, records)
        # ... vector store logic
    except Exception as exc:
        # Catch plugin errors, return structured failure
        return StepResult.fail(f"Memory upsert failed: {exc}")
```

---

## Feature Flags

### Current Flags (Existing)

- `ENABLE_HIPPORAG_MEMORY` - Enable HippoRAG continual memory
- `ENABLE_ENHANCED_MEMORY` - Enable Mem0 enhanced memory

### Recommended New Flags

- `ENABLE_MEMORY_PLUGINS` - Master switch for plugin system
- `MEMORY_DEFAULT_PLUGIN` - Default plugin if none specified

**Example `.env`:**

```bash
# Enable plugin system
ENABLE_MEMORY_PLUGINS=1

# Auto-route to HippoRAG by default
MEMORY_DEFAULT_PLUGIN=hipporag

# Backend-specific flags
ENABLE_HIPPORAG_MEMORY=1
ENABLE_ENHANCED_MEMORY=1
```

---

## Migration Path

### Phase A: Tool Migration (Weeks 5-6)

**Tasks:**

1. Migrate `MemoryStorageTool` to use `UnifiedMemoryService`
2. Migrate `GraphMemoryTool` callers to use plugin
3. Migrate `HippoRagContinualMemoryTool` callers to use plugin
4. Migrate `Mem0MemoryTool` callers to use plugin

**Example Migration:**

```python
# BEFORE
from tools import MemoryStorageTool
tool = MemoryStorageTool()
tool.run(text="content", collection="memory")

# AFTER
from memory import get_unified_memory
memory = get_unified_memory()
await memory.upsert(
    tenant=ctx.tenant,
    workspace=ctx.workspace,
    records=[{"content": "content"}]
)
```

---

### Phase B: Pipeline Integration (Week 6)

**Update:** `pipeline_components/orchestrator.py`

```python
# BEFORE
self.memory_storage = MemoryStorageTool()
self.graph_memory = GraphMemoryTool()
self.hipporag_memory = HippoRagContinualMemoryTool()

async def _store_analysis_results(self, data: dict):
    # Call each tool separately
    await self.memory_storage.run(...)
    await self.graph_memory.run(...)
    await self.hipporag_memory.run(...)

# AFTER
from memory import get_unified_memory
from memory.plugins import GraphPlugin, HippoRAGPlugin

self.memory = get_unified_memory()
self.memory.register_plugin("graph", GraphPlugin())
self.memory.register_plugin("hipporag", HippoRAGPlugin())

async def _store_analysis_results(self, data: dict):
    # Single interface, multiple backends
    base_records = [{"content": data["summary"]}]

    # Vector store (default)
    await self.memory.upsert(tenant, workspace, base_records)

    # Graph memory
    await self.memory.upsert(tenant, workspace, base_records, plugin="graph")

    # HippoRAG continual memory
    await self.memory.upsert(tenant, workspace, base_records, plugin="hipporag")
```

---

### Phase C: Deprecation (Week 7)

**Mark Deprecated:**

- `tools/memory_storage_tool.py` → Use `UnifiedMemoryService`
- `tools/mem0_memory_tool.py` → Use `Mem0Plugin`
- Direct tool instantiation patterns

**Add Deprecation Warnings:**

```python
# tools/memory_storage_tool.py
import warnings

class MemoryStorageTool:
    def __init__(self):
        warnings.warn(
            "MemoryStorageTool is deprecated. "
            "Use UnifiedMemoryService with plugins instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # ... existing code
```

---

## Benefits Achieved

### 1. Unified Interface ✅

- Single API for all memory operations
- Consistent async/await patterns
- Standard StepResult returns

### 2. Pluggable Architecture ✅

- Easy to add new backends
- No core code changes needed
- Protocol-based contracts

### 3. Tenant Isolation ✅

- Namespace-based scoping
- Validated tenant/workspace
- Secure by default

### 4. Backward Compatibility ✅

- Default vector store unchanged
- Plugins opt-in
- No breaking changes

### 5. Observability ✅

- Structured StepResult logging
- Plugin-specific metadata
- Error categorization

---

## Next Steps (Phase 5)

### Phase 5: Extract Orchestration Strategies (Weeks 7-8)

**Objectives:**

1. Extract `FallbackStrategy` from `fallback_orchestrator.py`
2. Extract `HierarchicalStrategy` from `hierarchical_orchestrator.py`
3. Extract `MonitoringStrategy`, `ResilienceStrategy`
4. Update `OrchestrationFacade` to load strategies dynamically
5. Migrate orchestrator callers to use facade

**Pattern:**

```python
# orchestration/strategies/fallback_strategy.py
class FallbackStrategy(OrchestrationStrategy):
    async def execute(self, task: Task, context: dict) -> StepResult:
        # Extracted from fallback_orchestrator.py
        ...

# Register strategy
orchestration.register_strategy("fallback", FallbackStrategy())
```

**Success Criteria:**

- [ ] 4+ orchestration strategies extracted
- [ ] OrchestrationFacade dynamically loads strategies
- [ ] Callers migrated to facade
- [ ] Original orchestrators marked deprecated

---

## Metrics & Observability

### Plugin Usage Metrics

**Recommended Metrics:**

```python
# In plugin implementations
from obs.metrics import get_metrics

metrics = get_metrics()

# Track plugin calls
metrics.counter(
    "memory_plugin_calls_total",
    labels={
        "plugin": "mem0",
        "operation": "store",
        "outcome": "success"
    }
).inc()

# Track plugin latency
with metrics.timer(
    "memory_plugin_duration_seconds",
    labels={"plugin": "mem0", "operation": "store"}
):
    result = await plugin.store(...)

# Track plugin errors
if not result.success:
    metrics.counter(
        "memory_plugin_errors_total",
        labels={
            "plugin": "mem0",
            "error_type": result.error_category.name
        }
    ).inc()
```

---

### Dashboard Queries

**Grafana Queries:**

```promql
# Plugin usage distribution
rate(memory_plugin_calls_total[5m])

# Plugin error rate
rate(memory_plugin_errors_total[5m])
/
rate(memory_plugin_calls_total[5m])

# Plugin latency p95
histogram_quantile(0.95,
  rate(memory_plugin_duration_seconds_bucket[5m])
)
```

---

## Conclusion

Phase 4 successfully implemented a plugin architecture for UnifiedMemoryService, enabling:

1. **Specialty Memory Backends**: Mem0, HippoRAG, Graph plugins
2. **Unified Interface**: Single API for all memory operations
3. **Dynamic Routing**: Runtime plugin selection via parameter
4. **Protocol-Based Design**: Extensible without inheritance
5. **Backward Compatibility**: Existing code unchanged

**Key Deliverables:**

- ✅ `MemoryPlugin` protocol
- ✅ `UnifiedMemoryService` plugin support
- ✅ 3 plugin implementations (Mem0, HippoRAG, Graph)
- ✅ Comprehensive examples
- ✅ Migration patterns documented

**Total Lines Added:** ~1,100 lines (plugins + examples + docs)

**Next Phase:** Extract orchestration strategies (Phase 5, Weeks 7-8)

---

**References:**

- ADR-0002: Unified Memory Strategy
- `docs/architecture/consolidation-status.md`
- `IMPLEMENTATION_PLAN.md` (Phases 0-8)
- Existing tools: `tools/mem0_memory_tool.py`, `tools/hipporag_continual_memory_tool.py`, `tools/graph_memory_tool.py`
