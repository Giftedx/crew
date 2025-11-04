# AI/ML/RL System - Quick Start Guide

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Introduction

The AI/ML/RL Unified System provides intelligent routing, continuous learning, and adaptive optimization for the Ultimate Discord Intelligence Bot. It connects trajectory evaluation, tool/agent routing, RAG quality feedback, and prompt optimization through interconnected feedback loops and contextual bandits.

### Key Benefits

- **Intelligent Routing**: Automatically select the best tool or agent for each task based on context and past performance
- **Continuous Learning**: System improves over time through feedback loops and online learning
- **Multi-Objective Optimization**: Balance quality, speed, and cost based on requirements
- **Health Monitoring**: Automatically detect and disable underperforming components
- **Unified Metrics**: Centralized observability across all AI/ML components

## Installation

The AI/ML/RL system is part of the main codebase. No additional installation required.

### Prerequisites

- Python 3.9+
- NumPy (for contextual bandits)
- Existing system components (RLModelRouter, UnifiedMemoryService, etc.)

### Environment Setup

Add these to your `.env` file:

```bash
# Enable AI/ML/RL components
ENABLE_UNIFIED_FEEDBACK=1
ENABLE_TOOL_ROUTING_BANDIT=1
ENABLE_AGENT_ROUTING_BANDIT=1
ENABLE_RAG_QUALITY_FEEDBACK=1
ENABLE_PROMPT_AB_TESTING=1

# Bandit configuration
BANDIT_EXPLORATION_RATE=0.1
BANDIT_LEARNING_RATE=0.01

# Processing intervals (in seconds)
FEEDBACK_PROCESSING_INTERVAL_S=10.0
CONSOLIDATION_INTERVAL_S=3600.0
HEALTH_CHECK_INTERVAL_S=300.0
```

## Quick Start

### Basic Usage

```python
import asyncio
from ai.integration.ai_ml_rl_integration import get_ai_integration

async def main():
    # Get and start the system
    ai_system = get_ai_integration()
    await ai_system.start()

    # Route a tool request
    result = await ai_system.route_tool(
        task_description="Analyze sentiment",
        context={"complexity": 0.7},
        task_type="analysis"
    )

    if result.success:
        tool_id = result.data.tool_id
        print(f"Selected: {tool_id}")

    # Stop when done
    await ai_system.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### With Feedback

```python
# After executing a task, submit feedback
ai_system.submit_tool_feedback(
    tool_id="sentiment_tool",
    context={"complexity": 0.7},
    success=True,
    latency_ms=850,
    quality_score=0.91
)
```

## Core Concepts

### 1. Contextual Bandits

The system uses contextual bandits (LinUCB algorithm) to make routing decisions:

- **Context**: Features describing the task (complexity, urgency, etc.)
- **Arms**: Available options (tools, agents, prompts)
- **Reward**: Quality score from task execution
- **Exploration vs Exploitation**: Balances trying new options vs using known good ones

### 2. Feedback Loops

Four main feedback loops:

1. **Trajectory → Model**: Maps task outcomes to model performance
2. **Tool Execution → Tool Router**: Improves tool selection
3. **Agent Execution → Agent Router**: Optimizes agent assignment
4. **RAG Retrieval → Memory**: Enhances memory quality

### 3. Health Monitoring

Components are monitored for:

- Success rate
- Average quality
- Error rate
- Latency

Components with health < threshold are automatically disabled.

### 4. Multi-Objective Optimization

Prompt selection can optimize for:

- **Quality**: Maximize accuracy
- **Speed**: Minimize latency
- **Cost**: Minimize token usage
- **Balanced**: Weighted combination

## Usage Examples

### Example 1: Tool Routing

```python
# Context describes the task
context = {
    "complexity": 0.8,          # 0.0-1.0
    "data_size": 10000,         # bytes/tokens
    "urgency": 0.7,             # 0.0-1.0
    "required_accuracy": 0.95,  # 0.0-1.0
    "budget_limit": 100,        # arbitrary units
}

result = await ai_system.route_tool(
    task_description="Deep semantic analysis",
    context=context,
    task_type="analysis"
)

if result.success:
    selection = result.data
    # Use selected tool
    execute_tool(selection.tool_id)

    # Submit feedback after execution
    ai_system.submit_tool_feedback(
        tool_id=selection.tool_id,
        context=context,
        success=True,
        latency_ms=1200,
        quality_score=0.94
    )
```

### Example 2: Agent Routing

```python
context = {
    "complexity": 0.9,
    "urgency": 0.8,
    "required_accuracy": 0.95,
    "data_volume": 0.7,
}

result = await ai_system.route_agent(
    task_description="Verify complex claims",
    context=context,
    task_type="verification"
)

if result.success:
    agent_id = result.data.agent_id
    # Execute with agent
    # ... then submit feedback
    ai_system.submit_agent_feedback(
        agent_id=agent_id,
        context=context,
        success=True,
        duration_s=45.2,
        quality_score=0.93
    )
```

### Example 3: Prompt Selection

```python
result = await ai_system.select_prompt(
    prompt_type="analysis",
    context={"complexity": 0.7},
    optimization_target="balanced"  # or "quality", "speed", "cost"
)

if result.success:
    template = result.data.template
    prompt = template.format(content="Your content here")

    # After using prompt
    ai_system.submit_prompt_feedback(
        variant_id=result.data.variant_id,
        context={"complexity": 0.7},
        quality_score=0.92,
        latency_ms=1500,
        cost_usd=0.02
    )
```

### Example 4: RAG Feedback

```python
# After retrieval
ai_system.submit_rag_feedback(
    query_id="query_123",
    query_text="What is machine learning?",
    retrieved_chunks=[
        {"id": "chunk_1", "content": "..."},
        {"id": "chunk_2", "content": "..."}
    ],
    relevance_scores=[0.95, 0.78]
)
```

## Configuration

### Bandit Parameters

```bash
# Exploration rate: higher = more exploration
# 0.0 = pure exploitation, 1.0 = pure exploration
BANDIT_EXPLORATION_RATE=0.1

# Learning rate for gradient descent
# Higher = faster adaptation, but less stable
BANDIT_LEARNING_RATE=0.01
```

### Processing Intervals

```bash
# How often to process feedback batches
FEEDBACK_PROCESSING_INTERVAL_S=10.0

# How often to trigger memory consolidation
CONSOLIDATION_INTERVAL_S=3600.0

# How often to check component health
HEALTH_CHECK_INTERVAL_S=300.0
```

### Quality Thresholds

```bash
# Minimum chunk quality before pruning
RAG_PRUNING_THRESHOLD=0.3

# Average quality before triggering consolidation
RAG_CONSOLIDATION_THRESHOLD=0.6

# Minimum health score before disabling
TOOL_HEALTH_THRESHOLD=0.3
AGENT_HEALTH_THRESHOLD=0.4
```

## Monitoring

### Get Metrics

```python
metrics = await ai_system.get_aggregate_metrics()

# Metrics structure:
# {
#   "orchestrator": {...},
#   "tool_router": {...},
#   "agent_router": {...},
#   "rag_feedback": {...},
#   "prompt_library": {...}
# }
```

### Key Metrics to Monitor

**Orchestrator**:

- `signals_processed`: Total feedback processed
- `consolidations_triggered`: Memory consolidations
- `average_reward_by_component`: EMA rewards

**Tool Router**:

- `total_tools`: Discovered tools
- `tool_statistics.*.success_rate`: Per-tool success
- `tool_statistics.*.avg_quality`: Per-tool quality

**Agent Router**:

- `total_agents`: Discovered agents
- `agent_statistics.*.current_load`: Current task load
- `agent_statistics.*.avg_quality`: Per-agent quality

**RAG Feedback**:

- `avg_quality`: Average chunk quality
- `pruning_candidates`: Chunks needing removal
- `recent_relevance_trend`: Recent performance

**Prompt Library**:

- `total_variants`: Registered prompts
- `performance_by_variant.*.avg_quality`: Per-variant quality

### Health Reports

```python
from ai.rl.unified_feedback_orchestrator import get_orchestrator

orchestrator = get_orchestrator()
health_report = orchestrator.get_component_health_report()

# Returns: {ComponentType: {component_id: health_score}}
```

## Troubleshooting

### Problem: No Tools/Agents Selected

**Symptoms**: Routing always returns same default option

**Solutions**:

1. Check feature flags are enabled
2. Verify tools/agents are registered
3. Ensure system is started with `await ai_system.start()`

### Problem: Poor Selection Quality

**Symptoms**: System selects wrong tools/agents

**Solutions**:

1. Increase exploration rate temporarily
2. Submit more feedback with accurate quality scores
3. Check if better options are available
4. Review context feature extraction

### Problem: Components Disabled

**Symptoms**: Health monitoring disables components

**Solutions**:

1. Check component health scores
2. Review recent feedback for error patterns
3. Lower health threshold if too strict
4. Fix underlying component issues

### Problem: High Memory Usage

**Symptoms**: Memory grows over time

**Solutions**:

1. Enable RAG quality feedback
2. Lower consolidation threshold
3. Increase consolidation frequency
4. Reduce feedback queue sizes

### Problem: Slow Routing

**Symptoms**: High latency in routing decisions

**Solutions**:

1. Reduce number of tools/agents
2. Simplify context feature extraction
3. Use caching for repeated contexts
4. Profile and optimize bandit selection

## Advanced Topics

### Custom Context Features

Add custom features to context:

```python
context = {
    # Standard features
    "complexity": 0.7,
    "urgency": 0.8,

    # Custom features
    "domain": "medical",           # Categorical
    "user_expertise": 0.9,         # Continuous
    "multimodal": True,            # Boolean
}
```

The system automatically encodes these into numeric vectors.

### Batch Feedback Processing

Submit multiple feedback items:

```python
for i in range(10):
    ai_system.submit_tool_feedback(...)

# Background task processes in batches
await asyncio.sleep(11)  # Wait for processing
```

### Integration with Existing Systems

```python
# In trajectory_evaluator.py
from ai.integration.ai_ml_rl_integration import get_ai_integration

ai_system = get_ai_integration()
if ai_system:
    ai_system.submit_trajectory_feedback(trajectory, evaluation)

# In retrieval_engine.py
if ai_system:
    ai_system.submit_rag_feedback(query_id, text, chunks, scores)
```

## Next Steps

- Read full documentation: `docs/ai_ml_rl_system.md`
- Run examples: `examples/ai_ml_rl/`
- Review tests: `tests_new/unit/ai/`
- Monitor metrics in production
- Tune configuration for your workload

## Support

For issues or questions:

1. Check troubleshooting section
2. Review full documentation
3. Check test cases for usage patterns
4. File an issue in repository
