# Observability

**Current Implementation** (verified November 3, 2025):

- **Metrics Module**: `src/ultimate_discord_intelligence_bot/obs/metrics.py`
- **Metric Specs**: `src/ultimate_discord_intelligence_bot/obs/metric_specs.py`
- **Tracing**: `src/platform/observability/tracing.py`
- **Langfuse Service**: `src/platform/observability/langfuse_service.py`
- **Observability Tools**: 26 tools in Observability category (23% of 111 total tools)
- **Prometheus Endpoint**: `/metrics` (enabled via `ENABLE_PROMETHEUS_ENDPOINT=1`)

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

## Tenancy Fallback Visibility (new)

When services operate in non‑strict tenancy mode and no `TenantContext` is set, a fallback to the default
namespace (`default:main`) is recorded via:

- `tenancy_fallback_total{tenant,workspace,component}`

The `component` label identifies the emitting subsystem (e.g. `openrouter_service`, `memory_service`).

Example PromQL to track fallbacks by component over 1 day:

```bash
sum by (component)(increase(tenancy_fallback_total[1d]))
```

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
1. Use `skipped` (not a separate status code) by returning `StepResult.skip(...)` with contextual metadata.
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
      return StepResult.skip(state="skipped", reason="empty payload")
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

Use `StepResult.skip(...)` for intentional skip paths so the pipeline automatically records a `skipped` outcome and the serialized payload surfaces `status="skipped"`.

When including additional metadata, avoid embedding another `status` key inside the data payload; prefer neutral fields such as `state` or `reason`:

```python
return StepResult.skip(state="skipped", reason="No XYZ provided")
```

Downstream dashboards rely on the StepResult's own status field, so keeping the payload free of conflicting `status` values prevents ambiguity while still communicating context.

### Enforcement Guard

CI runs `scripts/metrics_instrumentation_guard.py` which:

- Scans each tool module under `src/ultimate_discord_intelligence_bot/tools/`
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

## Segmentation & Embedding Metrics (new)

The transcript segmentation and embedding pipeline now emit dedicated low‑cardinality metrics:

- `segment_chunk_size_chars{tenant,workspace}` (histogram) — distribution of final chunk sizes in characters.
- `segment_chunk_size_tokens{tenant,workspace}` (histogram) — approximate distribution of chunk sizes in tokens (heuristic: 4 chars ≈ 1 token). Emitted only when token‑aware mode is enabled.
- `segment_chunk_merges_total{tenant,workspace}` — number of flush/merge operations performed during segmentation (helps tune `max_chars` / target tokens).
- `embed_deduplicates_skipped_total{tenant,workspace}` — count of duplicate chunk texts skipped before embedding (cost avoidance signal).

Token‑aware chunking is gated by `ENABLE_TOKEN_AWARE_CHUNKER=1` and uses `TOKEN_CHUNK_TARGET_TOKENS` (default 220) to derive an internal `max_chars` (`target_tokens / 0.25`). Overlap logic preserves context while keeping per‑chunk token budgets bounded.

Example PromQL panels:

```promql
histogram_quantile(0.95, sum by (le)(rate(segment_chunk_size_chars_bucket[15m])))
sum(increase(segment_chunk_merges_total[1h])) by (tenant,workspace)
sum(increase(embed_deduplicates_skipped_total[1h])) by (tenant,workspace)
```

Use merges + size distributions to iteratively right‑size token targets: excessive merges or very large p95 suggests lowering `TOKEN_CHUNK_TARGET_TOKENS`; no merges and very small p95 may indicate under‑utilisation.

## Degradation Reporter Metrics (new)

Feature‑flag: `ENABLE_DEGRADATION_REPORTER=1`

When enabled, structured fallback / partial failure signals record:

- `degradation_events_total{tenant,workspace,component,event_type,severity}` — categorical count of degradation/fallback incidents.
- `degradation_impact_latency_ms{tenant,workspace,component,event_type}` (histogram) — attributed added latency (when callers pass `added_latency_ms`).

An in‑memory ring buffer (default 500 events) retains recent detail strings without inflating metric label cardinality. Access via:

```python
from core.degradation_reporter import get_degradation_reporter
events = get_degradation_reporter().snapshot()
```

Grafana ideas:

```promql
sum by (component,event_type)(increase(degradation_events_total[30m]))
histogram_quantile(0.90, sum by (le,component)(rate(degradation_impact_latency_ms_bucket[15m])))
```

## HTTP Negative Caching (new)

Feature‑flag: `ENABLE_HTTP_NEGATIVE_CACHE=1` (requires also `enable_http_cache` setting true)

Adds in‑memory negative caching in `cached_get` for 404 and 429 responses:

- 404: cached for `min(60s, http_cache_ttl * 0.2)`
- 429: respects `Retry-After` header (delta seconds or HTTP date); falls back to same heuristic when absent/malformed.

Synthetic cache hits return status 404 with empty text to short‑circuit upstream calls, reducing load during transient upstream unavailability or rate limiting.

Operational tip: Track reduction in outbound calls by comparing request counters before/after enabling flag, and correlate with upstream 404/429 rates.

## Summary of New Feature Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `ENABLE_TOKEN_AWARE_CHUNKER` | Derive chunk size from token target rather than static char count | off |
| `TOKEN_CHUNK_TARGET_TOKENS` | Target tokens per chunk (heuristic conversion to chars) | 220 |
| `ENABLE_DEGRADATION_REPORTER` | Enable structured degradation event recording + metrics | off |
| `ENABLE_HTTP_NEGATIVE_CACHE` | Cache 404/429 responses to reduce redundant calls | off |

All flags are environment variable toggles; for staging validation enable individually and observe metrics before production rollout.
