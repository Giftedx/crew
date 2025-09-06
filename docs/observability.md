# Observability

This repository exposes tracing, metrics, logging, and incident helpers under
`src/obs/`.  A tiny OpenTelemetry configuration is provided:

```python
from obs import tracing
tracing.init_tracing("crew-dev")
```promql

Functions can then be decorated with `@tracing.trace_call("span")` to emit
spans.  Metrics use `prometheus_client` (install via the `[metrics]` extra) and can be reset or rendered for
scraping:

```python
from obs import metrics
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant

with with_tenant(TenantContext("t", "w")):
    metrics.ROUTER_DECISIONS.labels(**metrics.label_ctx()).inc()
print(metrics.render().decode())
```bash

Structured logs are emitted via `obs.logging.logger` which applies the privacy
filter before serialising to JSON and automatically tags each entry with the
active tenant and workspace when available.

## Ingest Metrics (new)

Two counters expose resilience decisions taken during ingestion:

- `ingest_transcript_fallbacks_total{tenant,workspace,source}` — increments when the pipeline falls back to Whisper transcription because a transcript fetch failed or was unavailable.
- `ingest_missing_id_fallbacks_total{tenant,workspace,source}` — increments when the pipeline derives an episode id from the URL because the provider omitted it.

Example PromQL to track daily counts by source:

```bash
sum by (source)(increase(ingest_transcript_fallbacks_total[1d]))
sum by (source)(increase(ingest_missing_id_fallbacks_total[1d]))
```yaml

## Metrics Endpoint

Enable the Prometheus endpoint and HTTP request metrics via settings:

```bash
export ENABLE_PROMETHEUS_ENDPOINT=1
export ENABLE_HTTP_METRICS=1
# Optional: change path (default is /metrics)
export PROMETHEUS_ENDPOINT_PATH=/metrics
```yaml

Run the API server (example using uvicorn):

```bash
python -m uvicorn server.app:create_app --factory --host 0.0.0.0 --port 8080
```yaml

Then scrape:

```bash
curl -s http://localhost:8080/metrics | head
```yaml

Prometheus scrape config snippet:

```yaml
scrape_configs:
  - job_name: crew-api
    static_configs:
      - targets: ["crew-api:8080"]
    metrics_path: /metrics
```

Sample Grafana dashboard JSON for ingest fallback counters is available at `docs/grafana/ingest_fallbacks_dashboard.json`. Import it in Grafana and set the Prometheus datasource. Dashboards expose `tenant` and `workspace` variables for filtering.

An additional HTTP retries dashboard is provided at `docs/grafana/http_retries_dashboard.json` to visualise retry attempts and give‑ups by method over the past day. It supports `tenant`, `workspace`, `method`, and `host` variables and includes Top‑5 tables (methods and hosts for attempts/give‑ups) plus a route rejections panel.

The HTTP dashboard also includes a Top‑5 table of routes by rate‑limit rejections over the last day to quickly spot throttling hotspots.

## Scheduler Metrics (new)

The scheduler exposes lightweight counters:

- `scheduler_enqueued_total{tenant,workspace,source}` — incremented when a job is enqueued.
- `scheduler_processed_total{tenant,workspace,source}` — incremented when a job is processed successfully.
- `scheduler_errors_total{tenant,workspace,source}` — incremented when the worker encounters an error running a job.

Use these with simple panels (stat/table) or combine with ingest duration to validate end‑to‑end pacing.

## SLO Dashboards

A minimal SLO dashboard JSON is available at `docs/grafana/slo_dashboard.json` with:

- Ingest Duration P95 (30m window)
- Scheduler Error Rate (15m window)

Import into Grafana and set `tenant`/`workspace` as needed.

## Alerting Hints

Prometheus alert rules (example):

```yaml
groups:
  - name: ingest-fallbacks
    rules:
      - alert: IngestTranscriptFallbackSpike
        expr: sum(increase(ingest_transcript_fallbacks_total[15m])) > 25
        for: 10m
        labels: {severity: page}
        annotations:
          summary: Transcript fallback spike
          description: Ingest transcript fallbacks spiking in the last 15m.

      - alert: IngestMissingIdFallbackSpike
        expr: sum(increase(ingest_missing_id_fallbacks_total[15m])) > 25
        for: 10m
        labels: {severity: page}
        annotations:
          summary: Missing id fallback spike
          description: Provider id missing, URL-hash fallback used too often.

  - name: http-retries
    rules:
      - alert: HttpRetryGiveupsRising
        expr: sum(increase(http_retry_giveups_total[10m])) > 5
        for: 5m
        labels: {severity: ticket}
        annotations:
          summary: HTTP retry give-ups elevated
          description: Investigate upstream availability or timeout configuration.
```

## Tool Metrics Instrumentation (new)

All production tools that return a `StepResult` are instrumented with a single counter:

```text
tool_runs_total{tool="<tool_name>", outcome="success|error|skipped"}
```

Guidelines:

1. Always increment exactly one outcome per invocation (including skips).
1. Use `skipped` (not a separate status code) by returning `StepResult.ok(skipped=True, reason=...)`.
1. Add a latency histogram *only* for materially expensive operations (network/multi‑step / long CPU). Current name:

- `tool_run_seconds{tool="<tool_name>"}`

1. Do not emit histograms for trivial in‑memory helpers to keep cardinality + storage low.
1. When adding a new StepResult tool: obtain a metrics handle once (e.g. `self._metrics = get_metrics()` in `__init__`) then increment counters just before each return.

Minimal pattern:

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

class ExampleTool:
  def __init__(self):
    self._metrics = get_metrics()

  def run(self, payload: str) -> StepResult:
    if not payload:
      self._metrics.counter("tool_runs_total", labels={"tool": "example", "outcome": "skipped"}).inc()
      return StepResult.ok(skipped=True, reason="empty payload")
    try:
      # ... work ...
      self._metrics.counter("tool_runs_total", labels={"tool": "example", "outcome": "success"}).inc()
      return StepResult.ok(result="done")
    except Exception as e:
      self._metrics.counter("tool_runs_total", labels={"tool": "example", "outcome": "error"}).inc()
      return StepResult.fail(error=str(e))
```

Latency variant (only for heavy tools):

```python
start = time.time()
try:
  ...
  duration = time.time() - start
  self._metrics.counter("tool_runs_total", labels={"tool": "video_download", "outcome": "success"}).inc()
  self._metrics.histogram("tool_run_seconds", duration, labels={"tool": "video_download"})
  return StepResult.ok(...)
except Exception as e:
  duration = time.time() - start
  self._metrics.counter("tool_runs_total", labels={"tool": "video_download", "outcome": "error"}).inc()
  self._metrics.histogram("tool_run_seconds", duration, labels={"tool": "video_download"})
  return StepResult.fail(error=str(e))
```

### Skip Semantics

Legacy `StepResult.skip(...)` is deprecated. Always express skips as:

```python
return StepResult.ok(skipped=True, reason="No XYZ provided")
```

This keeps the success path uniform while still allowing downstream logic / dashboards to distinguish skipped executions via a boolean flag or the `outcome="skipped"` counter label.

### Enforcement Guard

CI runs `scripts/metrics_instrumentation_guard.py` which:

- Scans each `tools/*.py` file
- Detects classes suffixed `Tool` that actually return or call `StepResult`
- Verifies presence of metrics usage (`get_metrics()` / counter / histogram patterns)
- Fails if any StepResult tool lacks instrumentation (unless allow‑listed)

Local invocation:

```bash
python scripts/metrics_instrumentation_guard.py
```

If you intentionally exclude a diagnostic helper, add it to the small allow‑list inside the guard script with a code comment explaining the rationale.

### When to Add a Histogram

Add `tool_run_seconds` ONLY if at least one of:

- Average runtime consistently > 250ms
- Involves external I/O (network, subprocess, large file)
- Has meaningful tail latency you want to alert/SLO on

Otherwise the per‑call overhead + metric cardinality is not justified.

### Future Improvements

- Consider a lightweight decorator to wrap common counter + duration logic (behind a feature flag to avoid premature abstraction).
- Expand guard to optionally warn (not fail) about dict‑return tools that still import `StepResult` but do not use it (tech debt visibility).
