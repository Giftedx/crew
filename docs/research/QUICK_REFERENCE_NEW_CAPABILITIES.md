# Quick Reference: New Capabilities & Enhancements

**Quick access guide for developers implementing new capabilities**

---

## 🚀 Quick Start - Top 3 Priorities

### 1. Mem0 Integration

**Install:**

```bash
pip install mem0ai
```

**Basic Usage:**

```python
from mem0 import Memory

memory = Memory()

# Store preference
memory.add("User prefers bullet points", user_id="tenant:workspace")

# Recall preference
results = memory.search("How to format output?", user_id="tenant:workspace")
```

**Integration Points:**

- `mission_orchestrator` - persistent mission preferences
- `persona_archivist` - learn creator patterns
- `community_liaison` - user interaction history

---

### 2. DSPy Prompt Optimization

**Install:**

```bash
pip install dspy-ai
```

**Basic Usage:**

```python
import dspy

# Define signature
class TaskSignature(dspy.Signature):
    """Task description"""
    input_field: str -> output_field: str

# Optimize automatically
optimizer = dspy.MIPROv2(metric=your_metric, auto="medium")
optimized = optimizer.compile(module, trainset=examples)
```

**Priority Agents to Optimize:**

1. mission_orchestrator
2. verification_director
3. analysis_cartographer
4. fact_check_tool
5. claim_extractor_tool

---

### 3. LangGraph Checkpointing

**Install:**

```bash
pip install langgraph
```

**Basic Usage:**

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# Define stateful workflow
workflow = StateGraph(StateClass)
# ... add nodes and edges ...

# Enable checkpointing
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# Run with resume capability
config = {"configurable": {"thread_id": "mission_123"}}
result = graph.invoke(input_data, config)
```

---

## 🛠️ New Tools

### Mem0 Memory Tool

```python
from tools.mem0_memory_tool import Mem0MemoryTool

tool = Mem0MemoryTool()
result = tool._run(
    action="remember",
    content="User prefers concise outputs",
    tenant="tenant_id",
    workspace="workspace_id"
)
```

**Actions:** `remember`, `recall`, `update`, `delete`

---

### DSPy Optimization Tool

```python
from tools.dspy_optimization_tool import DSPyOptimizationTool

tool = DSPyOptimizationTool()
result = tool._run(
    agent_name="my_agent",
    signature="input -> output",
    training_examples=examples,
    metric_name="accuracy"
)
```

**Optimization Levels:** `light`, `medium`, `heavy`

---

### Checkpoint Management Tool

```python
from tools.checkpoint_management_tool import CheckpointManagementTool

tool = CheckpointManagementTool()
result = tool._run(
    action="save",
    thread_id="mission_123",
    state_data=current_state
)
```

**Actions:** `save`, `load`, `resume`, `list`

---

## 📖 Configuration

### Feature Flags

Add to `.env`:

```bash
# Mem0 Integration
ENABLE_MEM0_MEMORY=true
MEM0_QDRANT_URL=http://localhost:6333

# DSPy Optimization
ENABLE_DSPY_OPTIMIZATION=true
DSPY_OPTIMIZATION_LEVEL=medium

# LangGraph Checkpointing
ENABLE_LANGGRAPH_CHECKPOINTS=true
CHECKPOINT_STORAGE_PATH=/data/checkpoints

# AutoGen Conversational
ENABLE_AUTOGEN_DISCORD=true
AUTOGEN_MAX_TURNS=10

# Langfuse Observability
ENABLE_LANGFUSE=true
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
```

---

## 🎯 Agent Enhancements

### Adding Mem0 to an Agent

```yaml
my_agent:
  role: "My Custom Agent"
  goal: "Achieve specific objective"
  tools:
    - Mem0MemoryTool  # Add this
    - ExistingTool1
    - ExistingTool2
  memory: true  # Enable built-in memory
```

### Optimizing Agent Prompts

```python
# In your agent file
from services.dspy_optimization import optimize_agent

# Define your agent's task
@optimize_agent(metric=accuracy_metric)
class MyAgent(Agent):
    # ... agent definition ...
```

---

## 📊 Monitoring

### Mem0 Metrics

```python
# Track memory operations
metrics.counter("mem0.remember.count")
metrics.counter("mem0.recall.count")
metrics.histogram("mem0.recall.latency_ms")
```

### DSPy Metrics

```python
# Track optimization results
metrics.gauge("dspy.agent_accuracy", value=0.95, labels={"agent": "my_agent"})
metrics.counter("dspy.optimization.runs")
```

### LangGraph Metrics

```python
# Track checkpoint operations
metrics.counter("langgraph.checkpoint.save")
metrics.counter("langgraph.resume.success")
metrics.histogram("langgraph.execution.duration_s")
```

---

## 🧪 Testing

### Testing Mem0 Integration

```python
def test_mem0_preference_storage():
    memory = Mem0MemoryService()

    # Store preference
    result = memory.remember_preference(
        "User likes concise output",
        tenant="test_tenant",
        workspace="test_workspace"
    )
    assert result.success

    # Recall preference
    memories = memory.recall_preferences(
        "How should I format output?",
        tenant="test_tenant",
        workspace="test_workspace"
    )
    assert len(memories) > 0
    assert "concise" in memories[0]["memory"].lower()
```

### Testing DSPy Optimization

```python
def test_agent_optimization():
    optimizer = AgentOptimizer()

    # Create test examples
    examples = [
        {"input": "test1", "expected_output": "result1"},
        {"input": "test2", "expected_output": "result2"},
    ]

    # Optimize
    optimized = optimizer.optimize_agent_prompt(
        agent_signature="input -> output",
        training_examples=examples,
        metric=test_metric
    )

    # Verify improvement
    baseline_score = evaluate_baseline(examples)
    optimized_score = evaluate_optimized(optimized, examples)
    assert optimized_score > baseline_score
```

---

## 🔍 Debugging

### Mem0 Debugging

```python
# Enable debug logging
import logging
logging.getLogger("mem0").setLevel(logging.DEBUG)

# Check memory contents
all_memories = memory.get_all(user_id="tenant:workspace")
print(f"Total memories: {len(all_memories)}")
```

### DSPy Debugging

```python
# Enable DSPy verbose mode
import dspy
dspy.settings.configure(trace=True, verbose=True)

# Inspect optimization process
optimizer = dspy.MIPROv2(metric=metric, track_stats=True)
result = optimizer.compile(module, trainset=data)
print(result.detailed_results)
```

### LangGraph Debugging

```python
# Visualize graph
graph.get_graph().draw_mermaid()

# Inspect checkpoint
checkpoint = graph.get_state(config)
print(f"Current state: {checkpoint.values}")
print(f"Next nodes: {checkpoint.next}")
```

---

## 📚 Documentation Links

**Internal:**

- [Full Research Report](CAPABILITY_ENHANCEMENT_RESEARCH_2025.md)
- [Executive Summary](EXECUTIVE_SUMMARY_CAPABILITY_ENHANCEMENTS.md)
- [Agent Reference](../agent_reference.md)
- [Tools Reference](../tools_reference.md)

**External:**

- [Mem0 Docs](https://docs.mem0.ai)
- [DSPy Docs](https://dspy-docs.vercel.app)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph)
- [AutoGen Docs](https://microsoft.github.io/autogen)
- [Langfuse Docs](https://langfuse.com/docs)

---

## ⚠️ Common Pitfalls

### Mem0

- ❌ Don't forget to set `user_id` for tenant isolation
- ❌ Don't store PII without proper consent
- ✅ Always use tenant:workspace format for user_id
- ✅ Add metadata for better filtering

### DSPy

- ❌ Don't optimize without sufficient training examples (need 50+)
- ❌ Don't use "heavy" optimization in production (too slow)
- ✅ Start with "light" or "medium" optimization
- ✅ A/B test optimized vs baseline

### LangGraph

- ❌ Don't use checkpointing for simple workflows
- ❌ Don't forget to handle checkpoint expiration
- ✅ Use for long-running missions only
- ✅ Set appropriate checkpoint retention policy

---

## 🆘 Troubleshooting

### Mem0 Issues

**Problem:** "Cannot connect to Qdrant"
**Solution:** Check `QDRANT_URL` in config, ensure Qdrant is running

**Problem:** "Memory not recalled"
**Solution:** Check user_id format matches store format

### DSPy Issues

**Problem:** "Optimization taking too long"
**Solution:** Reduce training set size or use "light" mode

**Problem:** "Optimized model worse than baseline"
**Solution:** Check metric function, may need more examples

### LangGraph Issues

**Problem:** "Checkpoint not found"
**Solution:** Check thread_id matches, checkpoint may have expired

**Problem:** "State too large to checkpoint"
**Solution:** Reduce state size, store large objects externally

---

**Last Updated:** October 17, 2025
**Version:** 1.0
**Maintained By:** Development Team
