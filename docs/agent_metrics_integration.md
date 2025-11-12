# Agent Metrics Integration Guide

## Overview

The `AgentMetricsCollector` provides Prometheus instrumentation for all 31 specialized agents in the Ultimate Discord Intelligence Bot system. This enables real-time monitoring of agent executions, performance, errors, and resource usage.

## Metrics Exposed

### Counters

- **`agent_executions_total{agent, status}`**: Total agent executions
  - Labels: `agent` (agent name), `status` (success/fail/skip)
  - Use: Track execution counts and success rates

- **`agent_errors_total{agent, category}`**: Total agent errors
  - Labels: `agent` (agent name), `category` (ErrorCategory enum value)
  - Use: Monitor error patterns and identify failing agents

- **`agent_tokens_used_total{agent}`**: Total tokens consumed
  - Labels: `agent` (agent name)
  - Use: Track LLM token usage and costs per agent

### Histograms

- **`agent_execution_duration_seconds{agent}`**: Execution duration distribution
  - Labels: `agent` (agent name)
  - Buckets: 0.1s, 0.5s, 1s, 2.5s, 5s, 10s, 30s, 60s, 120s, 300s
  - Use: Track latency distribution and identify slow agents

## Basic Usage

### Manual Recording

```python
from platform.observability.agent_metrics import AgentMetricsCollector

collector = AgentMetricsCollector.get_instance()

# Record successful execution
collector.record_execution(
    agent_name="Acquisition Specialist",
    status="success",
    duration_seconds=2.5,
    tokens_used=1500,
)

# Record failed execution
collector.record_execution(
    agent_name="Verification Director",
    status="fail",
    duration_seconds=1.0,
    error_category=ErrorCategory.TIMEOUT,
)
```

### Context Manager (Recommended)

```python
from platform.observability.agent_metrics import AgentMetricsCollector

collector = AgentMetricsCollector.get_instance()

# Automatic execution tracking
with collector.track_execution("Analysis Cartographer") as ctx:
    result = perform_analysis(content)
    
    # Optionally populate context for richer metrics
    if result.success:
        ctx["tokens_used"] = result.meta.get("resource_usage", {}).get("tokens_in", 0)
    else:
        ctx["error_category"] = result.error_category
```

### From StepResult (Best Practice)

```python
from platform.observability.agent_metrics import AgentMetricsCollector

collector = AgentMetricsCollector.get_instance()

# Execute agent and capture StepResult
result = agent.execute(task)

# Automatically extract metrics from StepResult
collector.record_from_step_result(
    agent_name="Mission Orchestrator",
    result=result,
)
```

## Integration Patterns

### Pattern 1: BaseAgent Integration

Instrument at the agent base class level for automatic tracking:

```python
# src/ultimate_discord_intelligence_bot/agents/base.py

from platform.observability.agent_metrics import AgentMetricsCollector
from platform.core.feature_flags import FeatureFlagRegistry

class BaseAgent(ABC):
    def execute(self, task: Task) -> StepResult:
        """Execute agent task with automatic metrics."""
        collector = AgentMetricsCollector.get_instance()
        
        # Skip if metrics disabled
        if not FeatureFlagRegistry.get("ENABLE_AGENT_METRICS"):
            return self._run(task)
        
        # Track execution with context manager
        with collector.track_execution(self.role) as ctx:
            result = self._run(task)
            
            # Populate context from result
            if result.success:
                meta = result.meta or {}
                if "resource_usage" in meta:
                    tokens = meta["resource_usage"].get("tokens_in", 0) + \
                             meta["resource_usage"].get("tokens_out", 0)
                    if tokens:
                        ctx["tokens_used"] = tokens
            else:
                ctx["error_category"] = result.error_category
            
            return result
```

### Pattern 2: Crew Execution Wrapper

Instrument at the crew execution level for orchestration metrics:

```python
# src/domains/orchestration/crew/executor.py

from platform.observability.agent_metrics import AgentMetricsCollector

class UnifiedCrewExecutor(CrewExecutor):
    def execute(self, config: CrewConfig) -> CrewExecutionResult:
        """Execute crew with agent metrics."""
        collector = AgentMetricsCollector.get_instance()
        
        for agent_task in config.tasks:
            agent_name = agent_task.agent_role
            
            with collector.track_execution(agent_name) as ctx:
                result = self._execute_task(agent_task)
                
                # Record from StepResult if available
                if hasattr(result, "meta"):
                    collector.record_from_step_result(agent_name, result)
```

### Pattern 3: Tool Execution Tracking

Track tool usage within agents:

```python
from platform.observability.agent_metrics import AgentMetricsCollector

class AcquisitionSpecialist(BaseAgent):
    def _run(self, url: str) -> StepResult:
        collector = AgentMetricsCollector.get_instance()
        
        # Track acquisition tool execution
        with collector.track_execution(f"{self.role}:download") as ctx:
            result = self.download_tool.run(url)
            ctx["tokens_used"] = 0  # Downloads don't use tokens
            
        return result
```

## Querying Metrics

### Prometheus Queries

```promql
# Agent success rate (last 5 minutes)
sum(rate(agent_executions_total{status="success"}[5m])) by (agent) /
sum(rate(agent_executions_total[5m])) by (agent)

# Agent error rate by category
sum(rate(agent_errors_total[5m])) by (agent, category)

# Agent p95 latency
histogram_quantile(0.95, sum(rate(agent_execution_duration_seconds_bucket[5m])) by (agent, le))

# Token usage per agent (last hour)
sum(increase(agent_tokens_used_total[1h])) by (agent)

# Top 5 slowest agents
topk(5, avg(rate(agent_execution_duration_seconds_sum[5m])) by (agent) /
         avg(rate(agent_execution_duration_seconds_count[5m])) by (agent))
```

### Grafana Dashboards

Example dashboard panel configurations:

**Agent Execution Rate**:

```json
{
  "expr": "sum(rate(agent_executions_total[5m])) by (agent)",
  "legendFormat": "{{agent}}"
}
```

**Error Heatmap**:

```json
{
  "expr": "sum(rate(agent_errors_total[5m])) by (agent, category)",
  "format": "heatmap"
}
```

**Latency Distribution**:

```json
{
  "expr": "histogram_quantile(0.50, sum(rate(agent_execution_duration_seconds_bucket[5m])) by (agent, le))",
  "legendFormat": "{{agent}} p50"
}
```

## Feature Flag Control

Control agent metrics via feature flag:

```bash
# Enable (default)
ENABLE_AGENT_METRICS=true

# Disable
ENABLE_AGENT_METRICS=false
```

Check at runtime:

```python
from platform.core.feature_flags import FeatureFlagRegistry

if FeatureFlagRegistry.get("ENABLE_AGENT_METRICS"):
    collector.record_execution(...)
```

## Performance Considerations

### Low Overhead

- No-op when Prometheus unavailable
- Singleton pattern (single collector instance)
- Async-safe (context manager handles exceptions)
- Low cardinality labels (agent name only)

### Label Cardinality

**Good** (low cardinality):

```python
collector.record_execution(agent_name="Acquisition Specialist", ...)
```

**Bad** (high cardinality):

```python
# DON'T: Include user IDs, URLs, or unique identifiers in agent_name
collector.record_execution(agent_name=f"Acquisition-{user_id}", ...)
```

### Batch Recording

For high-throughput scenarios, batch metrics where possible:

```python
# Collect results
results = []
for task in batch:
    results.append(agent.execute(task))

# Record in batch
for result in results:
    collector.record_from_step_result(agent_name, result)
```

## Troubleshooting

### Metrics Not Appearing

1. **Check Prometheus availability**:

   ```python
   from platform.observability.agent_metrics import PROMETHEUS_AVAILABLE
   print(f"Prometheus: {PROMETHEUS_AVAILABLE}")
   ```

2. **Verify feature flag**:

   ```python
   from platform.core.feature_flags import FeatureFlagRegistry
   print(f"Enabled: {FeatureFlagRegistry.get('ENABLE_AGENT_METRICS')}")
   ```

3. **Check collector initialization**:

   ```python
   collector = AgentMetricsCollector.get_instance()
   print(f"Collector enabled: {collector._enabled}")
   ```

### High Cardinality Warnings

If Prometheus complains about high cardinality:

- Ensure agent names are static (31 agents max)
- Don't include dynamic values in labels
- Use metadata/exemplars for high-cardinality data

### Missing Duration Data

If durations are missing:

- Use context manager (`track_execution`) for automatic timing
- Ensure `elapsed_ms` is in StepResult.meta when using `record_from_step_result`

## Best Practices

1. **Use StepResult integration**: Automatically extracts all metrics
2. **Enable feature flag**: Control in production via `ENABLE_AGENT_METRICS`
3. **Keep labels static**: Only use agent name as label
4. **Instrument at boundaries**: BaseAgent.execute() or Crew.execute()
5. **Handle failures gracefully**: Collector degrades to no-op if Prometheus unavailable
6. **Monitor token usage**: Track LLM costs per agent
7. **Set up alerts**: Alert on error rate spikes or latency regressions

## Examples

### Complete Agent Integration

```python
from platform.core.step_result import ErrorCategory, StepResult
from platform.observability.agent_metrics import AgentMetricsCollector
from platform.core.feature_flags import FeatureFlagRegistry

class VerificationDirector(BaseAgent):
    def execute(self, claim: str) -> StepResult:
        """Execute fact-checking with metrics."""
        if not FeatureFlagRegistry.get("ENABLE_AGENT_METRICS"):
            return self._verify_claim(claim)
        
        collector = AgentMetricsCollector.get_instance()
        
        with collector.track_execution("Verification Director") as ctx:
            result = self._verify_claim(claim)
            
            # Populate metrics context
            if result.success:
                meta = result.meta or {}
                if "resource_usage" in meta:
                    usage = meta["resource_usage"]
                    tokens = usage.get("tokens_in", 0) + usage.get("tokens_out", 0)
                    ctx["tokens_used"] = tokens
            else:
                ctx["error_category"] = result.error_category
            
            return result
    
    def _verify_claim(self, claim: str) -> StepResult:
        try:
            # Perform verification
            verdict = self.fact_checker.verify(claim)
            
            return StepResult.ok(
                result={"verdict": verdict},
                meta={
                    "elapsed_ms": 2500,
                    "resource_usage": {
                        "tokens_in": 500,
                        "tokens_out": 1000,
                    },
                },
            )
        except TimeoutError:
            return StepResult.fail(
                error="Verification timeout",
                error_category=ErrorCategory.TIMEOUT,
                retryable=True,
            )
```

### Crew Execution with Metrics

```python
from platform.observability.agent_metrics import AgentMetricsCollector

class MissionOrchestrator:
    def execute_mission(self, mission: Mission) -> StepResult:
        """Execute multi-agent mission with tracking."""
        collector = AgentMetricsCollector.get_instance()
        
        results = {}
        for agent_name, task in mission.tasks.items():
            with collector.track_execution(agent_name) as ctx:
                result = self._execute_agent_task(agent_name, task)
                results[agent_name] = result
                
                # Record from StepResult
                collector.record_from_step_result(agent_name, result)
        
        return StepResult.ok(result={"mission_results": results})
```

## Migration Guide

### Before (No Metrics)

```python
class MyAgent(BaseAgent):
    def execute(self, task):
        return self._run(task)
```

### After (With Metrics)

```python
from platform.observability.agent_metrics import AgentMetricsCollector

class MyAgent(BaseAgent):
    def execute(self, task):
        collector = AgentMetricsCollector.get_instance()
        
        with collector.track_execution(self.role) as ctx:
            result = self._run(task)
            
            if result.success:
                ctx["tokens_used"] = result.meta.get("tokens", 0)
            else:
                ctx["error_category"] = result.error_category
            
            return result
```

## Related Documentation

- [StepResult Contract](../platform/core/step_result.py)
- [Feature Flags Registry](../platform/core/feature_flags.py)
- [Prometheus Metrics](../platform/observability/metrics.py)
- [Agent Reference](../docs/agent_reference.md)
