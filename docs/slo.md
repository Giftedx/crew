# Service Level Objectives

`obs.slo` contains a minimal SLO evaluator used in tests and ops helpers.  Define
objectives in code or configuration and evaluate runtime metrics against them:

```python
from obs import slo
slos = [slo.SLO(metric="latency_ms", threshold=1000)]
status = slo.SLOEvaluator(slos).evaluate({"latency_ms": 850})
```

Each metric is considered passing when the observed value is less than or equal
to the configured threshold.
