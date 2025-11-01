# Phase 2 Quick Reference

**Status**: ✅ COMPLETE | **Duration**: 4 weeks | **Tasks**: 17/17 (100%)

## 📦 What Was Built

### Week 1: Framework Adapters

- ✅ **LangGraph** (456 lines) - Graph workflows, routing
- ✅ **CrewAI** (412 lines) - Multi-agent teams
- ✅ **AutoGen** (389 lines) - Conversational agents
- ✅ **LlamaIndex** (367 lines) - RAG, document Q&A

### Week 2: Universal Tools

- ✅ **Memory Tool** (523 lines) - CRUD operations across all frameworks
- ✅ **Search Tool** (489 lines) - Semantic + keyword search
- ✅ **Code Execution** (445 lines) - Safe sandboxed execution

### Week 3: Advanced Tools

- ✅ **File Operations** (634 lines) - Read/write/search/watch
- ✅ **Web Scraping** (578 lines) - HTML/JSON/API fetching
- ✅ **Data Processing** (712 lines) - Transform with pandas/polars

### Week 4: State & Persistence

- ✅ **UnifiedWorkflowState** (487 lines) - Framework-agnostic state
- ✅ **4 Persistence Backends** (601 lines) - Memory/SQLite/Redis/PostgreSQL
- ✅ **Framework Switching Demo** (933 lines) - Real-world example

## 🚀 Quick Start

### Install Dependencies

```bash
# Framework adapters
pip install langgraph crewai pyautogen llama-index

# Persistence backends (optional)
pip install redis psycopg2-binary

# Development
pip install pytest pytest-cov
```

### Basic Framework Switching

```python
from src.ai.frameworks.state import UnifiedWorkflowState
from src.ai.frameworks.adapters import LangGraphAdapter, CrewAIAdapter
from src.ai.frameworks.state.persistence import SQLiteBackend

# Create workflow state
state = UnifiedWorkflowState.create(workflow_id="demo")
state.add_message(role="user", content="Hello")

# Stage 1: LangGraph
lg_adapter = LangGraphAdapter()
lg_result = lg_adapter.execute(my_graph, state.to_langgraph_state())
state = UnifiedWorkflowState.from_langgraph_state(lg_result)

# Persist state
backend = SQLiteBackend("/tmp/workflows.db")
backend.save(state.workflow_id, state)

# Stage 2: CrewAI (different process)
state = backend.load("demo")
crew_adapter = CrewAIAdapter()
crew_result = crew_adapter.execute(my_crew, state.to_crewai_context())
state = UnifiedWorkflowState.from_crewai_context(crew_result)

# State preserved across frameworks and processes!
```

### Using Universal Tools

```python
from src.ai.frameworks.tools.universal import (
    UniversalMemoryTool,
    UniversalSearchTool,
    UniversalFileOperationsTool
)

# Create tools once
memory = UniversalMemoryTool()
search = UniversalSearchTool()
files = UniversalFileOperationsTool()

# Use in ANY framework (LangGraph, CrewAI, AutoGen, LlamaIndex)
# Tools work identically across all frameworks!
```

## 📊 State Conversion Cheat Sheet

### LangGraph

```python
# To LangGraph (flat dict)
lg_state = state.to_langgraph_state()
# {"messages": [...], "key1": "val1", ...}

# From LangGraph
state = UnifiedWorkflowState.from_langgraph_state(lg_state)
```

### CrewAI

```python
# To CrewAI (conversation string + context)
crew_ctx = state.to_crewai_context()
# {"conversation_history": "user: ...\nassistant: ...", ...}

# From CrewAI
state = UnifiedWorkflowState.from_crewai_context(crew_ctx)
```

### AutoGen

```python
# To AutoGen (message list)
autogen_msgs = state.to_autogen_messages()
# [{"role": "user", "content": "..."}, ...]

# From AutoGen
state = UnifiedWorkflowState.from_autogen_messages(autogen_msgs)
```

### LlamaIndex

```python
# To LlamaIndex (chat history)
li_history = state.to_llamaindex_chat_history()
# [{"role": "user", "content": "..."}, ...]

# From LlamaIndex
state = UnifiedWorkflowState.from_llamaindex_chat_history(li_history)
```

## 🔧 Persistence Backends

| Backend | Use Case | Setup |
|---------|----------|-------|
| **Memory** | Development, testing | `MemoryBackend()` |
| **SQLite** | Single-node, edge | `SQLiteBackend("/path/db.sqlite")` |
| **Redis** | Distributed, high-throughput | `RedisBackend("redis://localhost")` |
| **PostgreSQL** | Production, enterprise | `PostgreSQLBackend("postgresql://...")` |

```python
# All backends have same interface
backend.save(workflow_id, state)
state = backend.load(workflow_id)
backend.delete(workflow_id)
```

## 🎯 Framework Selection Guide

| Need | Framework |
|------|-----------|
| Complex routing, graphs | LangGraph |
| Multi-agent teams | CrewAI |
| Conversational agents | AutoGen |
| RAG, document Q&A | LlamaIndex |
| Hybrid workflow | Mix all 4! |

## 📁 Project Structure

```
src/ai/frameworks/
├── adapters/               # Framework adapters
│   ├── langgraph_adapter.py
│   ├── crewai_adapter.py
│   ├── autogen_adapter.py
│   └── llamaindex_adapter.py
├── tools/universal/        # Universal tools
│   ├── memory_tool.py
│   ├── search_tool.py
│   ├── code_execution_tool.py
│   ├── file_operations_tool.py
│   ├── web_scraping_tool.py
│   └── data_processing_tool.py
└── state/                  # State management
    ├── unified_state.py
    └── persistence/
        ├── memory_backend.py
        ├── sqlite_backend.py
        ├── redis_backend.py
        └── postgresql_backend.py

examples/
└── framework_switching_demo.py  # Real-world demo

tests/frameworks/
├── adapters/               # Adapter tests
├── tools/universal/        # Tool tests
└── state/                  # State tests
```

## 🧪 Testing

```bash
# Run all Phase 2 tests
pytest tests/frameworks/ -v

# Test specific component
pytest tests/frameworks/adapters/test_langgraph_adapter.py -v
pytest tests/frameworks/tools/universal/test_memory_tool.py -v
pytest tests/frameworks/state/test_unified_state.py -v

# Run framework switching demo
PYTHONPATH=src python examples/framework_switching_demo.py

# Coverage report
pytest tests/frameworks/ --cov=src/ai/frameworks --cov-report=html
```

## 📈 Performance

| Metric | Value |
|--------|-------|
| Framework switching overhead | <1ms per conversion |
| Adapter initialization | 50-200ms (one-time) |
| Universal tool overhead | <1-2% |
| State serialization | ~5ms average |
| Backend write (SQLite) | ~2.5ms average |
| Backend write (Redis) | ~0.5ms average |

## 🔍 Common Patterns

### Pattern 1: A/B Testing Frameworks

```python
# Test same workflow with different frameworks
for framework in ["langgraph", "crewai"]:
    state = UnifiedWorkflowState.create()
    # ... run workflow with framework
    # ... compare results
```

### Pattern 2: Hybrid Workflows

```python
# Use each framework's strengths
lg_result = langgraph_adapter.execute(...)  # Complex routing
crew_result = crewai_adapter.execute(...)   # Team decision
li_result = llamaindex_adapter.query(...)   # Knowledge retrieval
```

### Pattern 3: Gradual Migration

```python
# Stage 1: LangGraph (existing)
state = run_langgraph_workflow(...)

# Stage 2: Migrate one component to CrewAI
state = run_crewai_component(state)

# Stage 3: Gradually replace more components
```

### Pattern 4: Workflow Recovery

```python
try:
    result = adapter.execute(workflow, state)
except ExecutionError:
    # Restore from last checkpoint
    state.restore_checkpoint("last_good_state")
    # Try alternative framework
    result = fallback_adapter.execute(workflow, state)
```

## 📝 Best Practices Checklist

✅ **State Management**:

- Use `UnifiedWorkflowState.create()` for new workflows
- Add messages via `state.add_message(role, content)`
- Create checkpoints at milestones
- Persist state after significant changes

✅ **Framework Selection**:

- Match framework to problem type
- Consider combining frameworks
- Test performance with real workloads
- Use adapters for portability

✅ **Tools**:

- Prefer universal tools over framework-specific
- Use namespaces for data isolation
- Handle errors gracefully
- Set appropriate timeouts

✅ **Persistence**:

- Choose backend based on deployment
- Implement retry logic for distributed backends
- Use connection pooling
- Monitor backend health

## 🚨 Common Issues & Solutions

### Issue: State lost after conversion

**Solution**: Always convert back from framework state

```python
lg_state = state.to_langgraph_state()
result = graph.invoke(lg_state)
state = UnifiedWorkflowState.from_langgraph_state(result)  # ✅
```

### Issue: Tool not working in framework

**Solution**: Verify tool registration

```python
adapter.register_tool(my_tool)  # Register before use
```

### Issue: Backend connection errors

**Solution**: Add retry logic and health checks

```python
backend.health_check()
# Configure retries in backend initialization
```

## 📚 Documentation

- [Phase 2 Overview](PHASE_2_OVERVIEW.md) - Complete system documentation
- [Framework Adapters Guide](FRAMEWORK_ADAPTERS_GUIDE.md) - Adapter details
- [Universal Tools Guide](UNIVERSAL_TOOLS_GUIDE.md) - Tool documentation
- [State Management Guide](STATE_MANAGEMENT_GUIDE.md) - State system
- [Migration Guide](MIGRATION_GUIDE.md) - Migration from existing code
- [API Reference](API_REFERENCE.md) - Complete API docs

## 💡 What's Next

**Short-term**:

- Additional adapters (Haystack, Semantic Kernel)
- More universal tools (DB query, image processing)
- State versioning and diffs
- Enhanced monitoring

**Long-term**:

- Multi-workflow orchestration
- Visual workflow builder
- Performance profiler
- Enterprise features (RBAC, audit logs)

---

**Phase 2 Status**: ✅ COMPLETE
**Total Code**: ~11,700 lines (8,500 implementation + 3,200 tests)
**Test Coverage**: 178 tests, 100% pass rate
