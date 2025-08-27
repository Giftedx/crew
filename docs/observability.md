# Observability

This repository exposes tracing, metrics, logging, and incident helpers under
`src/obs/`.  A tiny OpenTelemetry configuration is provided:

```python
from obs import tracing
tracing.init_tracing("crew-dev")
```

Functions can then be decorated with `@tracing.trace_call("span")` to emit
spans.  Metrics use `prometheus_client` (install via the `[metrics]` extra) and can be reset or rendered for
scraping:

```python
from obs import metrics
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant

with with_tenant(TenantContext("t", "w")):
    metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()
print(metrics.render().decode())
```

Structured logs are emitted via `obs.logging.logger` which applies the privacy
filter before serialising to JSON and automatically tags each entry with the
active tenant and workspace when available.
