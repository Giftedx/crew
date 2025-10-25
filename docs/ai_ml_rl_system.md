# AI/ML/RL Unified System Documentation

## Overview

This document describes the comprehensive AI/ML/RL enhancement system that connects and enhances the intelligence capabilities of the Ultimate Discord Intelligence Bot through interconnected feedback loops, contextual bandits, and continuous learning.

## Architecture

### Core Components

#### 1. Unified Feedback Orchestrator (`src/ai/rl/unified_feedback_orchestrator.py`)

**Purpose**: Central coordinator connecting all feedback loops

**Key Features**:

- Collects feedback from trajectories, tools, agents, RAG, governance, and cost systems
- Routes feedback to appropriate bandit models
- Triggers memory consolidation when quality degrades
- Monitors component health and auto-disables unhealthy ones
- Provides unified metrics and observability

**Usage**:

```python
from ai.rl.unified_feedback_orchestrator import get_orchestrator

# Get orchestrator instance
orchestrator = get_orchestrator()

# Start background processing
await orchestrator.start()

# Submit trajectory feedback
orchestrator.submit_trajectory_feedback(trajectory, evaluation_result)

# Get metrics
metrics = orchestrator.get_metrics()
```

#### 2. Tool Routing Bandit (`src/ai/rl/tool_routing_bandit.py`)

**Purpose**: Intelligent routing across 50+ tools using contextual bandits

**Key Features**:

- Auto-discovers available tools from registry
- Tracks performance metrics per tool
- Uses contextual bandit for context-aware selection
- Health monitoring with auto-disable
- Batch feedback processing

**Usage**:

```python
from ai.rl.tool_routing_bandit import get_tool_router

# Get router instance
tool_router = get_tool_router()

# Route a task to best tool
result = await tool_router.route_tool_request(
    task_description="Analyze sentiment of text",
    context={
        "complexity": 0.7,
        "data_size": 5000,
        "required_accuracy": 0.9
    },
    task_type="analysis"
)

if result.success:
    selection = result.data
    print(f"Selected: {selection.tool_id} (confidence: {selection.confidence})")

# Submit feedback after execution
tool_router.submit_tool_feedback(
    tool_id=selection.tool_id,
    context=context,
    success=True,
    latency_ms=1200,
    quality_score=0.92
)
```

#### 3. Agent Routing Bandit (`src/ai/rl/agent_routing_bandit.py`)

**Purpose**: Intelligent routing across 11 CrewAI agents

**Key Features**:

- Auto-discovers available agents
- Load balancing across agents
- Specialization-based routing
- Performance tracking with trajectory feedback
- Quality and duration optimization

**Usage**:

```python
from ai.rl.agent_routing_bandit import get_agent_router

# Get router instance
agent_router = get_agent_router()

# Route a task to best agent
result = await agent_router.route_agent_task(
    task_description="Verify claims in article",
    context={
        "complexity": 0.8,
        "urgency": 0.6,
        "required_accuracy": 0.95
    },
    task_type="verification"
)

# Mark task completion
agent_router.complete_agent_task(
    agent_id=result.data.agent_id,
    context=context,
    success=True,
    task_duration_s=45.2,
    quality_score=0.93
)
```

#### 4. RAG Quality Feedback (`src/ai/rag/rag_quality_feedback.py`)

**Purpose**: Instrument retrieval relevance → memory re-ranking/pruning

**Key Features**:

- Tracks chunk-level quality metrics
- Identifies candidates for pruning
- Provides re-ranking scores
- Triggers consolidation when quality degrades
- Comprehensive quality reporting

**Usage**:

```python
from ai.rag.rag_quality_feedback import get_rag_feedback

# Get feedback instance
rag_feedback = get_rag_feedback()

# Submit retrieval feedback
rag_feedback.submit_retrieval_feedback(
    query_id="query_123",
    query_text="What is the capital of France?",
    retrieved_chunks=[
        {"id": "chunk_1", "content": "Paris is the capital..."},
        {"id": "chunk_2", "content": "France is a country..."}
    ],
    relevance_scores=[0.95, 0.7]
)

# Get pruning candidates
candidates = rag_feedback.get_pruning_candidates(min_retrievals=5, limit=100)

# Check if consolidation needed
should_consolidate, reason = rag_feedback.should_trigger_consolidation()

# Get quality report
report = rag_feedback.get_quality_report()
```

#### 5. Prompt Library with A/B Testing (`src/ai/prompts/prompt_library_ab.py`)

**Purpose**: Centralized prompt variants with performance-based selection

**Key Features**:

- Store multiple variants per prompt type
- Track performance metrics (quality, speed, cost)
- Contextual bandit for variant selection
- Multi-objective optimization (quality/speed/cost)
- Auto-prune low-performing variants

**Usage**:

```python
from ai.prompts.prompt_library_ab import get_prompt_library, PromptType

# Get library instance
prompt_lib = get_prompt_library()

# Register a variant
prompt_lib.register_variant(
    prompt_type=PromptType.ANALYSIS,
    template="Analyze the following text carefully: {content}",
    performance_tags={"accuracy": 0.9, "speed": 0.7}
)

# Select best variant
result = prompt_lib.select_prompt(
    prompt_type=PromptType.ANALYSIS,
    context={
        "complexity": 0.8,
        "required_accuracy": 0.95
    },
    optimization_target="quality"  # or "speed", "cost", "balanced"
)

if result.success:
    selection = result.data
    prompt = selection.template.format(content="Your text here")

# Submit feedback
prompt_lib.submit_feedback(
    variant_id=selection.variant_id,
    context=context,
    quality_score=0.94,
    latency_ms=1500,
    cost_usd=0.02,
    success=True
)
```

#### 6. AI/ML/RL Integration Layer (`src/ai/integration/ai_ml_rl_integration.py`)

**Purpose**: Unified integration and management of all AI/ML/RL components

**Key Features**:

- Central configuration via environment variables
- Component lifecycle management
- Background feedback processing
- Aggregate metrics collection
- Simplified API for common operations

**Usage**:

```python
from ai.integration.ai_ml_rl_integration import get_ai_integration

# Get integration instance
ai_system = get_ai_integration()

# Start the system
await ai_system.start()

# Use unified APIs
tool_result = await ai_system.route_tool(task_desc, context, task_type)
agent_result = await ai_system.route_agent(task_desc, context, task_type)
prompt_result = await ai_system.select_prompt("analysis", context, "quality")

# Submit feedback
ai_system.submit_trajectory_feedback(trajectory, evaluation)
ai_system.submit_rag_feedback(query_id, query_text, chunks, scores)

# Get aggregate metrics
metrics = await ai_system.get_aggregate_metrics()

# Stop the system
await ai_system.stop()
```

## Configuration

### Environment Variables

```bash
# Feature flags
ENABLE_UNIFIED_FEEDBACK=1
ENABLE_TOOL_ROUTING_BANDIT=1
ENABLE_AGENT_ROUTING_BANDIT=1
ENABLE_RAG_QUALITY_FEEDBACK=1
ENABLE_PROMPT_AB_TESTING=1
ENABLE_THRESHOLD_TUNING=1
ENABLE_TOOL_HEALTH_MONITORING=1

# Bandit parameters
BANDIT_EXPLORATION_RATE=0.1  # 0.0-1.0, higher = more exploration
BANDIT_LEARNING_RATE=0.01

# Processing intervals
FEEDBACK_PROCESSING_INTERVAL_S=10.0
CONSOLIDATION_INTERVAL_S=3600.0  # 1 hour
HEALTH_CHECK_INTERVAL_S=300.0    # 5 minutes

# Quality thresholds
RAG_PRUNING_THRESHOLD=0.3
RAG_CONSOLIDATION_THRESHOLD=0.6
TOOL_HEALTH_THRESHOLD=0.4
AGENT_HEALTH_THRESHOLD=0.4
```

## Integration Points

### With Existing Trajectory Evaluator

```python
# In trajectory_evaluator.py
from ai.integration.ai_ml_rl_integration import get_ai_integration

# After evaluating trajectory
ai_system = get_ai_integration()
if ai_system:
    ai_system.submit_trajectory_feedback(trajectory, evaluation_result)
```

### With Memory/RAG Systems

```python
# In retrieval_engine.py
from ai.integration.ai_ml_rl_integration import get_ai_integration

# After retrieval
ai_system = get_ai_integration()
if ai_system:
    ai_system.submit_rag_feedback(
        query_id=query.query_id,
        query_text=query.text,
        retrieved_chunks=results,
        relevance_scores=[r.confidence for r in results]
    )
```

### With Pipeline Orchestrator

```python
# In orchestrator.py
from ai.integration.ai_ml_rl_integration import get_ai_integration

# Route tools dynamically
ai_system = get_ai_integration()
if ai_system:
    tool_result = await ai_system.route_tool(
        task_description="Analyze audio quality",
        context={"data_size": audio_size, "complexity": 0.7},
        task_type="analysis"
    )
```

## Metrics and Monitoring

### Key Metrics

**Orchestrator Metrics**:

- `signals_processed`: Total feedback signals processed
- `signals_by_source`: Breakdown by source (trajectory, tool, agent, etc.)
- `signals_by_component`: Breakdown by component type
- `average_reward_by_component`: EMA of rewards per component
- `consolidations_triggered`: Number of memory consolidations
- `health_checks_performed`: Health check count

**Tool Router Metrics**:

- `tool_statistics`: Per-tool usage, success rate, latency, quality
- `total_tools`: Number of discovered tools
- `feedback_queue_size`: Pending feedback count

**Agent Router Metrics**:

- `agent_statistics`: Per-agent usage, success rate, duration, load
- `total_agents`: Number of discovered agents
- `current_load_distribution`: Load across agents

**RAG Feedback Metrics**:

- `total_chunks`: Total memory chunks
- `total_retrievals`: Total retrieval operations
- `avg_quality`: Average chunk quality
- `quality_distribution`: Distribution of quality scores
- `pruning_candidates`: Number of candidates for pruning
- `recent_relevance_trend`: Recent relevance scores

**Prompt Library Metrics**:

- `variants_by_type`: Variants grouped by prompt type
- `total_variants`: Total registered variants
- `usage_distribution`: Usage counts per variant
- `performance_by_variant`: Quality, latency, cost per variant

### Accessing Metrics

```python
# Via integration layer
ai_system = get_ai_integration()
metrics = await ai_system.get_aggregate_metrics()

# Direct access
from ai.rl.unified_feedback_orchestrator import get_orchestrator
orchestrator = get_orchestrator()
orch_metrics = orchestrator.get_metrics()
health_report = orchestrator.get_component_health_report()
```

## Advanced Features

### Multi-Objective Optimization

The system supports optimizing for different objectives:

- **Quality**: Maximize accuracy and correctness
- **Speed**: Minimize latency
- **Cost**: Minimize token/API costs
- **Balanced**: Weighted combination of all three

### Health Monitoring and Auto-Disable

Components with:

- Health score < 0.3 (tools) or 0.4 (agents)
- Sample size > 10
- Are automatically disabled

### Memory Consolidation Triggers

Automatic consolidation when:

- Average relevance drops below 0.6
- More than 100 low-quality chunks (< 0.3)

### Context Feature Engineering

Extracted features include:

- Task complexity and urgency
- Data size and modality
- Quality requirements
- Resource constraints (budget, time)
- Historical performance

## Best Practices

1. **Start Simple**: Enable components incrementally
2. **Monitor Metrics**: Track performance before/after enabling features
3. **Tune Thresholds**: Adjust based on your workload
4. **Regular Consolidation**: Review and prune low-performing variants
5. **A/B Test Changes**: Use shadow mode before full rollout
6. **Feedback Quality**: Ensure quality scores are calibrated correctly

## Troubleshooting

### Components Not Routing

- Check feature flags are enabled
- Verify components are initialized via integration layer
- Confirm background tasks are running

### Low Performance

- Increase exploration rate for more discovery
- Lower quality thresholds if too strict
- Check if components are disabled due to health issues

### Memory Issues

- Enable RAG quality feedback
- Lower consolidation threshold
- Increase pruning frequency

## Future Enhancements

Planned features (not yet implemented):

- **Synthetic Data Generation**: Generate edge-case training data
- **Multi-Step Planning with MCTS**: Tree-search for complex tasks
- **Budget-Aware Routing**: Integrate TokenMeter cost models
- **Learned Governance**: Evolve heuristic governance to learned classifier
- **Shadow A/B Framework**: Parallel experiments with paired logging
- **Model Distillation**: Train lightweight models from GPT-4 outputs
- **Threshold Tuning Bandits**: Dynamic threshold adjustment
- **Real-Time Feature Engineering**: Advanced context feature extraction

## References

- RLModelRouter: `src/ultimate_discord_intelligence_bot/services/rl_model_router.py`
- Trajectory Evaluator: `src/eval/trajectory_evaluator.py`
- Unified Memory: `src/ultimate_discord_intelligence_bot/knowledge/unified_memory.py`
- Retrieval Engine: `src/ultimate_discord_intelligence_bot/knowledge/retrieval_engine.py`
- TokenMeter: `src/core/token_meter.py`

## Contributing

When adding new components:

1. Follow the contextual bandit pattern
2. Integrate with UnifiedFeedbackOrchestrator
3. Add metrics and health monitoring
4. Document in this file
5. Add tests in `tests_new/unit/ai/`

---

For questions or issues, see the development team or file an issue in the repository.
