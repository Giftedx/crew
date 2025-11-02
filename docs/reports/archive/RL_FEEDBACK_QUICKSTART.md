# RL Feedback Loop - Quick Start

## TL;DR

The RL feedback loop is **operationalized** with:

- ✅ 3 predeclared Prometheus metrics
- ✅ Background processor in enhanced monitoring
- ✅ 4 passing tests
- ✅ Complete docs + dashboard + alerts + runbook

## Run It

### Enable

```bash
export ENABLE_TRAJECTORY_EVALUATION=true
export ENABLE_TRAJECTORY_FEEDBACK_LOOP=true
```

### Test

```bash
PYTHONPATH=src pytest -q tests/obs/test_rl_feedback_loop*.py
```

### Monitor

```promql
# Queue depth
rl_feedback_queue_depth

# Processing rate (5m)
rate(rl_feedback_processed_total[5m])

# Failure rate (5m)
rate(rl_feedback_failed_total[5m])
```

## Import Dashboards/Alerts

1. **Grafana**: Import `docs/grafana/rl_feedback_loop_dashboard.json`
2. **Prometheus**: Load `docs/prometheus/rl_feedback_alerts.yml`

## Read More

- **Observability**: `docs/observability.md#rl-feedback-loop-metrics-new`
- **Runbook**: `docs/runbooks/rl_feedback_loop.md`
- **Implementation**: `RL_FEEDBACK_IMPLEMENTATION_COMPLETE.md`

## What Changed

| File | Change |
|------|--------|
| `src/obs/metrics.py` | Added 3 predeclared collectors + factory enhancements |
| `docs/observability.md` | Added RL metrics section |
| `tests/obs/test_rl_feedback_loop*.py` | Created 4 tests (2 files) |
| `docs/grafana/rl_feedback_loop_dashboard.json` | Created 6-panel dashboard |
| `docs/prometheus/rl_feedback_alerts.yml` | Created 6 alert rules |
| `docs/runbooks/rl_feedback_loop.md` | Created operational runbook |

**Unchanged** (already present):

- `src/obs/enhanced_monitoring.py` - loop + `process_rl_feedback_once()`
- `src/obs/metric_specs.py` - RL metric specs
- `env.example` - flags with defaults

## Done ✅

All items complete. Production-ready.
