# Framework Switching Demo

This example demonstrates how UnifiedWorkflowState enables seamless framework switching while preserving conversation history, context, and checkpoints.

## Overview

The demo simulates a customer support refund workflow that transitions through four different AI frameworks:

1. **LangGraph** → Query analysis & intent detection
2. **CrewAI** → Multi-agent team collaboration
3. **AutoGen** → Conversational refund processing
4. **LlamaIndex** → Knowledge-enhanced follow-up

## Running the Demo

```bash
# From the project root
PYTHONPATH=src python examples/framework_switching_demo.py
```

## What It Demonstrates

### State Preservation

- Messages are maintained across all framework transitions
- Context accumulates throughout the workflow (21 keys total)
- Checkpoints are created at each framework boundary
- All data remains intact and accessible

### Framework Conversions

Each framework sees state in its native format:

- **LangGraph**: `{"messages": [...], "context_key": value, ...}`
- **CrewAI**: `{"conversation_history": "...", "context_key": value, ...}`
- **AutoGen**: `[{"role": "user", "content": "..."}, ...]`
- **LlamaIndex**: `[{"role": "user", "content": "..."}, ...]`

### Persistence

The demo shows state persistence across:

- **MemoryBackend**: In-memory storage for development
- **SQLiteBackend**: File-based storage with process restart simulation

## Workflow Flow

```
User Query
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 1: LangGraph - Intent Analysis            │
│  • Convert state to LangGraph format            │
│  • Analyze customer sentiment & urgency         │
│  • Detect intent (refund_request)               │
│  • Create checkpoint: post_langgraph_analysis   │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 2: CrewAI - Team Decision                 │
│  • Convert state to CrewAI format               │
│  • Multi-agent collaboration:                   │
│    - Refund Analyst: Check eligibility          │
│    - Policy Checker: Review policy              │
│    - Customer Success: Evaluate LTV             │
│  • Team decision: APPROVE refund                │
│  • Create checkpoint: post_crewai_decision      │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 3: AutoGen - Refund Processing            │
│  • Convert state to AutoGen format              │
│  • Multi-turn conversation:                     │
│    - Request payment details                    │
│    - Confirm refund amount                      │
│    - Process transaction                        │
│  • Create checkpoint: post_autogen_processing   │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│ Stage 4: LlamaIndex - Retention Offer           │
│  • Convert state to LlamaIndex format           │
│  • Query knowledge base (RAG)                   │
│  • Generate retention offer:                    │
│    - 15% discount on next purchase              │
│    - Dedicated CSM for 90 days                  │
│  • Create checkpoint: workflow_complete         │
└─────────────────────────────────────────────────┘
    ↓
Persistence Demo
    ↓
Final Summary
```

## Key Achievements

✅ **State Preserved**: 8 messages + 21 context keys maintained across all transitions
✅ **Lossless Conversion**: Framework-specific formats preserve all data
✅ **Checkpoint System**: 4 checkpoints enable workflow resumption
✅ **Persistence**: State survives process restarts (SQLite demo)
✅ **Multi-Backend**: Works with Memory, SQLite, Redis, PostgreSQL

## Output Sample

```
================================================================================
  Framework Switching Demo: Customer Support Workflow
================================================================================

Initialized workflow: 17945dff-7c83-42b2-a596-390039c880c0

Stage 1: LangGraph - Query Analysis
  Intent detected: refund_request
  Sentiment: frustrated
  Urgency: high
  Checkpoint created: post_langgraph_analysis

Stage 2: CrewAI - Team Collaboration
  Decision: APPROVE_REFUND
  Refund amount: $299.99
  Customer LTV: $2500.0
  Checkpoint created: post_crewai_decision

Stage 3: AutoGen - Refund Processing Conversation
  4 conversation turns completed
  Transaction ID: TXN-20251101-8472
  Checkpoint created: post_autogen_processing

Stage 4: LlamaIndex - Knowledge Retrieval & Follow-up
  Knowledge applied: Customer retention best practices
  Offer: 15% discount + dedicated CSM
  Checkpoint created: workflow_complete

Persistence Demo:
  ✅ Saved to Memory backend
  ✅ Saved to SQLite (/tmp/framework_demo.db)
  ✅ Restored after simulated restart
  ✅ 8 messages preserved
  ✅ 21 context keys preserved
  ✅ 1 checkpoint preserved

Workflow Execution Complete!
```

## Code Structure

The demo is organized into clear stages:

- `simulate_langgraph_processing()` - LangGraph intent analysis
- `simulate_crewai_processing()` - CrewAI team collaboration
- `simulate_autogen_processing()` - AutoGen conversation
- `simulate_llamaindex_processing()` - LlamaIndex RAG
- `demonstrate_persistence()` - Multi-backend persistence
- `print_final_summary()` - Comprehensive workflow report

## Technical Details

### State Conversions

Each framework conversion is **bidirectional** and **lossless**:

```python
# LangGraph
langgraph_state = state.to_langgraph_state()
state = UnifiedWorkflowState.from_langgraph_state(langgraph_state, workflow_id)

# CrewAI
crewai_context = state.to_crewai_context()
state = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id)

# AutoGen
autogen_messages = state.to_autogen_messages()
state = UnifiedWorkflowState.from_autogen_messages(autogen_messages, workflow_id, context)

# LlamaIndex
llamaindex_chat = state.to_llamaindex_chat_history()
state = UnifiedWorkflowState.from_llamaindex_chat_history(llamaindex_chat, workflow_id, context)
```

### Persistence Backends

The demo showcases two backends:

```python
# Memory (in-memory)
memory_backend = MemoryBackend()
await memory_backend.save(workflow_id, state.to_dict())
loaded = await memory_backend.load(workflow_id)

# SQLite (persistent)
sqlite_backend = SQLiteBackend("/tmp/framework_demo.db")
await sqlite_backend.save(workflow_id, state.to_dict())
loaded = await sqlite_backend.load(workflow_id)
```

Also available: **RedisBackend**, **PostgreSQLBackend**

## Use Cases

This pattern is useful for:

1. **Framework Migration**: Gradually migrate from one framework to another
2. **Specialized Processing**: Use each framework's strengths for specific tasks
3. **A/B Testing**: Compare framework performance on the same workflow
4. **Hybrid Workflows**: Combine multiple frameworks in a single workflow
5. **Disaster Recovery**: Resume workflows from checkpoints after failures

## Extension Ideas

- Add error handling and retry logic
- Implement rollback to previous checkpoints
- Add metrics/telemetry for each transition
- Create branching workflows with conditional framework selection
- Add human-in-the-loop approval gates between stages
- Implement parallel framework execution with result merging

## Related Files

- Implementation: `src/ai/frameworks/state/unified_state.py`
- Persistence: `src/ai/frameworks/state/persistence/`
- Tests: `tests/frameworks/state/`
- Documentation: `TASK_14_COMPLETION_SUMMARY.md`, `TASK_15_COMPLETION_SUMMARY.md`
