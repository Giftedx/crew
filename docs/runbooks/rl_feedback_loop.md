# RL Feedback Loop Runbook

## Overview

The RL (Reinforcement Learning) feedback loop processes trajectory evaluation feedback to continuously improve model routing decisions. This runbook covers operational procedures, troubleshooting, and recovery.

## Architecture

- **Evaluator**: `src/eval/trajectory_evaluator.py` emits `TrajectoryFeedback` into the shared router's queue
- **Registry**: `src/ultimate_discord_intelligence_bot/services/rl_router_registry.py` provides thread-safe singleton access
- **Processor**: `src/obs/enhanced_monitoring.py` background loop drains queue via `process_rl_feedback_once()`
- **Router**: `src/ultimate_discord_intelligence_bot/services/rl_model_router.py` updates bandit parameters

## Metrics

### Primary Metrics

- `rl_feedback_processed_total{tenant,workspace}` - Successfully processed feedback items
- `rl_feedback_failed_total{tenant,workspace}` - Failed feedback items
- `rl_feedback_queue_depth{tenant,workspace}` - Current queue size
- `rl_feedback_processing_latency_ms{tenant,workspace}` - Batch latency distribution (ms)

### Derived Metrics

- **Success rate**: `processed / (processed + failed)`
- **Processing rate**: `rate(processed_total[5m])`
- **Avg queue depth**: `avg_over_time(queue_depth[15m])`

## Activation

### Environment Flags

```bash
# Required for trajectory evaluation (emits feedback)
export ENABLE_TRAJECTORY_EVALUATION=true

# Required for background processing loop
export ENABLE_TRAJECTORY_FEEDBACK_LOOP=true

# Optional tuning knobs
export RL_FEEDBACK_BATCH_SIZE=25
export RL_FEEDBACK_LOOP_INTERVAL_SECONDS=15
```

### Tuning Guidelines

- **Increase `RL_FEEDBACK_BATCH_SIZE`** when queue depth grows faster than it drains.
- **Decrease `RL_FEEDBACK_BATCH_SIZE`** in low-volume environments to reduce bursty load.
- **Lower `RL_FEEDBACK_LOOP_INTERVAL_SECONDS`** to achieve faster convergence when feedback is latency-sensitive.
- **Raise `RL_FEEDBACK_LOOP_INTERVAL_SECONDS`** to reduce background work during quiet periods.

### Verification

```bash
# Check if loop is enabled
curl -s http://localhost:8000/health | jq '.rl_feedback_enabled'

# Check current queue depth
curl -s http://localhost:9090/api/v1/query?query=rl_feedback_queue_depth | jq '.data.result'
```

## Alert Response

### RLFeedbackProcessingFailures

**Severity**: Page
**Trigger**: Failures detected in last 15 minutes

**Investigation**:

1. Check recent logs for errors:

   ```bash
   kubectl logs -n crew deployment/crew-api --since=30m | grep -i "rl feedback"
   ```

1. Look for common failure patterns:
   - Router import failures
   - Malformed feedback payloads
   - Bandit update exceptions

1. Check if router is registered:

   ```python
   from ultimate_discord_intelligence_bot.services.rl_router_registry import get_rl_model_router
   router = get_rl_model_router(create_if_missing=False)
   print(f"Router present: {router is not None}")
   ```

**Mitigation**:

- If transient: monitor for auto-recovery
- If persistent: restart service to reinitialize router
- If malformed data: drain queue and investigate upstream evaluator

### RLFeedbackQueueDepthHigh / RLFeedbackQueueDepthCritical

**Severity**: Ticket / Page
**Trigger**: Queue depth > 25 (ticket) or > 100 (page) for 15/10 minutes

**Investigation**:

1. Check processing rate:

   ```promql
   rate(rl_feedback_processed_total[5m])
   ```

1. Compare to emission rate (from evaluator):

   ```promql
   rate(trajectory_feedback_emissions_total[5m])
   ```

1. Check for processing bottleneck:
   - Slow bandit updates
   - Lock contention
   - Resource exhaustion

**Mitigation**:

- **Short-term**: Increase batch size in `process_rl_feedback_once()` (default 25)
- **Medium-term**: Reduce loop interval (default 15s)
- **Long-term**: If emission rate consistently exceeds processing capacity, consider:
  - Sampling trajectory evaluations
  - Async/parallel processing
  - Persistent queue with workers

### RLFeedbackProcessingStalled

**Severity**: Page
**Trigger**: Queue depth > 0 but no items processed in 30 minutes

**Investigation**:

1. Check if background loop is running:

   ```bash
   # Look for periodic "RL feedback loop" log entries
   kubectl logs -n crew deployment/crew-api --tail=500 | grep "RL feedback"
   ```

1. Check flag status:

   ```bash
   kubectl exec -it deployment/crew-api -- env | grep ENABLE_TRAJECTORY_FEEDBACK_LOOP
   ```

1. Check for deadlock or exception in loop:

   ```bash
   kubectl logs -n crew deployment/crew-api --since=1h | grep -i "error\|exception"
   ```

**Mitigation**:

- Restart service to reinitialize loop
- If repeated: investigate underlying cause (router lock, unhandled exception)
- Temporarily disable evaluation to stop queue growth while fixing

## Manual Operations

### One-Shot Processing

```python
from obs.enhanced_monitoring import EnhancedMonitoringSystem

ems = EnhancedMonitoringSystem()
result = ems.process_rl_feedback_once(labels={"tenant": "system", "workspace": "manual"})
print(f"Processed: {result['processed']}, Failed: {result['failed']}, Remaining: {result['queue_depth']}")
```

### Queue Inspection

```python
from ultimate_discord_intelligence_bot.services.rl_router_registry import get_rl_model_router

router = get_rl_model_router(create_if_missing=False)
if router:
    queue = router.trajectory_feedback_queue
    print(f"Queue size: {len(queue)}")
    if queue:
        print(f"First item: {queue[0]}")
```

### Force Drain Queue

```python
# WARNING: Processes entire queue in one call; may take time
router = get_rl_model_router(create_if_missing=False)
if router:
    result = router.process_trajectory_feedback(batch_size=1000)
    print(result)
```

### Purge Queue (Emergency)

```python
# WARNING: Discards all feedback without processing
router = get_rl_model_router(create_if_missing=False)
if router:
    discarded = len(router.trajectory_feedback_queue)
    router.trajectory_feedback_queue.clear()
    print(f"Discarded {discarded} items")
```

## Performance Tuning

### Batch Size

Default: 25 items per tick

```python
# In enhanced_monitoring.py process_rl_feedback_once()
result = router.process_trajectory_feedback(batch_size=50)  # Increase
```

**Trade-offs**:

- Larger batch: Higher throughput, longer per-tick latency
- Smaller batch: Lower latency, more loop iterations

### Loop Interval

Default: 15 seconds

```python
# In enhanced_monitoring.py start_monitoring()
self._rl_feedback_task = asyncio.create_task(self._rl_feedback_loop(interval_seconds=10))
```

**Trade-offs**:

- Shorter interval: Lower queue depth, higher CPU usage
- Longer interval: Higher queue depth, lower overhead

### Recommendations

| Scenario | Batch Size | Interval |
|----------|-----------|----------|
| Low volume (<10 items/min) | 10 | 30s |
| Medium volume (10-50 items/min) | 25 | 15s |
| High volume (>50 items/min) | 50 | 10s |

## Monitoring Best Practices

1. **Dashboard**: Import `docs/grafana/rl_feedback_loop_dashboard.json`
1. **Alerts**: Load `docs/prometheus/rl_feedback_alerts.yml` into Prometheus
1. **SLOs**:
   - Success rate > 99%
   - Queue depth < 10 (95th percentile)
   - Processing latency < 5s (per batch)

1. **Regular Reviews**:
   - Weekly: Check success rate trends
   - Monthly: Tune batch size/interval based on volume
   - Quarterly: Validate bandit convergence metrics

## Troubleshooting Checklist

- [ ] Flag `ENABLE_TRAJECTORY_FEEDBACK_LOOP` is set to `1`
- [ ] Router is registered in registry (not `None`)
- [ ] Background loop is running (check logs)
- [ ] No recent exceptions in logs
- [ ] Queue depth is stable or decreasing
- [ ] Processing rate matches emission rate
- [ ] Success rate > 95%

## Recovery Procedures

### Service Restart

```bash
kubectl rollout restart deployment/crew-api -n crew
kubectl rollout status deployment/crew-api -n crew
```

### Configuration Change

```bash
# Edit ConfigMap
kubectl edit configmap crew-config -n crew

# Restart to pick up changes
kubectl rollout restart deployment/crew-api -n crew
```

### Gradual Recovery

1. Disable evaluation to stop queue growth:

   ```bash
   kubectl set env deployment/crew-api ENABLE_TRAJECTORY_EVALUATION=false
   ```

1. Drain existing queue via one-shot processing

1. Re-enable evaluation:

   ```bash
   kubectl set env deployment/crew-api ENABLE_TRAJECTORY_EVALUATION=true
   ```

## Contact

- **Team**: AI/ML Platform
- **Slack**: #ml-routing-support
- **On-call**: PagerDuty rotation "ML Infrastructure"
