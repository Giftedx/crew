# Observability Panels

This folder contains a minimal set of PromQL-based panels you can import into Grafana (or any compatible dashboarding system) to monitor key behaviors:

- Semantic cache shadow hit ratio
- Semantic cache promotions (rate)
- Prefetch issued vs used (semantic cache)
- Ingest concurrency fallbacks
- AgentEvals fallbacks
- Semantic cache similarity average
- Pilot pipeline duration average (5m)
- Pilot step duration average (5m) and quantiles (p95/p99)
- Pilot runs rate (5m)
- Pilot total duration avg by orchestrator (5m)
- Pilot error ratio by orchestrator (10m)
- Pilot step failures (15m)
- Pilot step skips (15m)
- Pilot inflight (current)
- Pilot step failure ratio (10m)

## Prerequisites

- Prometheus scraping your service's metrics endpoint.
- Enable the metrics endpoint in this service:

```bash
ENABLE_PROMETHEUS_ENDPOINT=1
# Optional: customize path
# PROMETHEUS_ENDPOINT_PATH=/metrics
```

## Importing

- Option A (panels only): Open Grafana → Dashboards → Import → Upload `observability_panels.json` and bind queries to your Prometheus datasource.
- Option B (full dashboard): Import `grafana_dashboard.json` for a pre-arranged dashboard layout with templating for tenant/workspace.

## Alerts

- Sample Prometheus alerting rules are provided in `alerts.yml`.
- To use them, include the file in your Prometheus config (e.g., `rule_files: ['dashboards/alerts.yml']`).
- Alerts include:
  - Low semantic cache shadow hit ratio
  - Ingest concurrency fallback spikes
  - AgentEvals fallback frequency
  - Persistent LangGraph pilot fallback
  - LangGraph pilot step failures spike (segment/embed)
  - LangGraph pilot slow duration (avg over time)
  - LangGraph pilot ingest step slow (avg over time)
  - Cost spikes correlated with low cache effectiveness

## Tracing (optional)

If you enable tracing (`ENABLE_TRACING=1`) and initialize a tracer (see `obs/tracing.init_tracing` or the server setup), the pilot emits spans:

- Parent span: `langgraph_pilot.run`
  - Attributes: `orchestrator`, `segment_enabled`, `embed_enabled`, `pipeline_duration_seconds`, `outcome`
- Child spans per step: `langgraph_pilot.step.ingest|segment|embed|analyze`
  - Attributes: `step` (one of the step names), `orchestrator`, `outcome`

Tips:

- Correlate with Prometheus metrics by comparing `pipeline_duration_seconds` and the span attribute `pipeline_duration_seconds`.
- Fallbacks and failures are also visible via the `degradation_events_total{component="langgraph_pilot",...}` counter in Prometheus.

To compute p95/p99 for step durations, use PromQL histogram_quantile over the per-step bucket rates, for example:

```promql
histogram_quantile(0.95, sum by (le,tenant,workspace,step,orchestrator) (rate(pipeline_step_duration_seconds_bucket[5m])))
```

Similarly, for total duration by orchestrator quantiles (e.g., p95):

```promql
histogram_quantile(0.95, sum by (le,tenant,workspace,orchestrator) (rate(pipeline_total_duration_seconds_bucket[5m])))
```

## Notes

- If `prometheus_client` is not installed in your environment, metrics are no-ops and panels will show no data.
- Labels are kept low-cardinality (tenant/workspace) to limit metric series explosion.
- Semantic cache shadow-to-prod promotions are counted via `cache_promotions_total{cache_name="semantic"}`.
- Optional pilot endpoint (for quick runs): set `ENABLE_LANGGRAPH_PILOT_API=1` and call `GET /pilot/run?tenant=...&workspace=...`.
- Demo runner: execute `demo_langgraph_pilot.py` with `DEMO_ENABLE_SEGMENT`/`DEMO_ENABLE_EMBED` to generate pilot activity and surface duration in both metrics and the endpoint response.
