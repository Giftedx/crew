# Service Level Objectives (SLOs)

This project exposes Prometheus metrics and a tiny `obs.slo` helper for local checks.
Below are practical SLO patterns and alerting examples to monitor ingest and scheduler health.

## Ingest Duration SLO

Target: 95% of ingest runs complete in ≤ 30s over 30 minutes.

PromQL (histogram quantile):

```
histogram_quantile(
  0.95,
  sum by (le)(rate(pipeline_duration_seconds_bucket[30m]))
) <= 30
```

Alert example:

```
- alert: IngestP95Slow
  expr: histogram_quantile(0.95, sum by (le)(rate(pipeline_duration_seconds_bucket[30m]))) > 30
  for: 15m
  labels: {severity: ticket}
  annotations:
    summary: Ingest P95 exceeded 30s
    description: Pipeline duration P95 is above target for 15 minutes.
```

## Scheduler Error Rate SLO

Target: Error rate < 1% over 15 minutes.

PromQL (ratio):

```
sum(increase(scheduler_errors_total[15m]))
/ clamp_min(sum(increase(scheduler_processed_total[15m])) + sum(increase(scheduler_errors_total[15m])), 1)
< 0.01
```

Alert example:

```
- alert: SchedulerErrorRateHigh
  expr: sum(increase(scheduler_errors_total[15m]))
        / clamp_min(sum(increase(scheduler_processed_total[15m])) + sum(increase(scheduler_errors_total[15m])), 1) > 0.01
  for: 10m
  labels: {severity: page}
  annotations:
    summary: Scheduler error rate > 1%
    description: Investigate failing jobs and provider health.
```

## Queue Backlog SLO

Target: Backlog < 100 jobs over 10 minutes.

PromQL:

```
max_over_time(scheduler_queue_backlog{tenant=~"$tenant",workspace=~"$workspace"}[10m]) < 100
```

Alert example:

```
- alert: SchedulerBacklogHigh
  expr: max_over_time(scheduler_queue_backlog[10m]) > 100
  for: 10m
  labels: {severity: ticket}
  annotations:
    summary: Scheduler backlog exceeds 100 jobs
    description: Investigate scheduling rate and worker capacity.
```

## Local SLO Checks (optional)

Use `obs.slo` for quick, in‑code checks:

```python
from obs import slo

slos = [
  slo.SLO(metric="pipeline_duration_p95_s", threshold=30.0),
  slo.SLO(metric="scheduler_error_rate", threshold=0.01),
]
observed = {"pipeline_duration_p95_s": 25.4, "scheduler_error_rate": 0.003}
status = slo.SLOEvaluator(slos).evaluate(observed)
assert status["pipeline_duration_p95_s"] and status["scheduler_error_rate"]
```

Notes:
- Prefer Prometheus for production enforcement; the Python helper is for smoke checks.
- Scope SLOs per‑tenant/workspace using label filters in PromQL where appropriate.
