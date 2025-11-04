---
adr: 0005
title: Consolidate Performance Analytics
status: Accepted
date: 2025-10-18
implementation_date: 2025-10-31
implementation_status: Partially Complete
authors:
  - Ultimate Discord Intelligence Bot Architecture Group
---

## Context

Performance monitoring is scattered across multiple modules:

- `src/ultimate_discord_intelligence_bot/performance_dashboard.py`
- `src/ultimate_discord_intelligence_bot/performance_optimization_engine.py`
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_*.py` (5 files)
- `src/ultimate_discord_intelligence_bot/advanced_performance_analytics_impl/` (9 modules)
- `src/ultimate_discord_intelligence_bot/observability/` (3 modules)
- `src/ultimate_discord_intelligence_bot/monitoring/production_monitor.py`
- `src/performance/cache_optimizer.py`, `src/performance/cache_warmer.py`

This creates:

- Redundant metrics collection
- Inconsistent metric naming and labels
- Direct access to StepResult internals from dashboards
- Multiple "health score" calculations with different algorithms

## Decision

1. **Single Analytics Service** – Consolidate into `observability/analytics_service.py` that:
   - Consumes metrics from `obs/metrics` (canonical source)
   - Exposes dashboard queries, alerts, and health checks
   - Uses public StepResult APIs instead of reaching into internals
2. **Deprecate Standalone** – Archive `performance_dashboard.py`, `advanced_performance_analytics_*`, performance scripts outside `src/obs/`.
3. **Metrics Ownership** – `obs/metrics` is the single source of truth; analytics services query, never emit directly.
4. **Dashboard Integration** – `observability/dashboard_integration.py` and `observability/intelligent_alerts.py` remain as dashboard/alerting adapters.

## Consequences

- Single analytics API reduces duplication and drift
- Clearer separation: `obs/metrics` emits, `observability/*` queries and visualizes
- Dashboards no longer tightly coupled to internal Step Result structures
- Requires migrating `performance_dashboard` callers and cleaning up optimization scripts

## Implementation Status (Updated November 3, 2025)

**Canonical Implementation**: ✅ Complete

- `src/ultimate_discord_intelligence_bot/obs/metrics.py` - Metrics registry
- `src/ultimate_discord_intelligence_bot/obs/metric_specs.py` - Metric specifications
- `src/platform/observability/langfuse_service.py` - Tracing service
- Prometheus `/metrics` endpoint (enabled via `ENABLE_PROMETHEUS_ENDPOINT=1`)

**Metrics System**: ✅ Operational

- Required labels: `tool`, `operation`, `status`, `agent`, `tenant`
- Common metrics: `tool_runs_total`, `agent_operations_total`, `agent_duration_seconds`, `pipeline_stage_duration_seconds`
- Enforcement via `scripts/metrics_instrumentation_guard.py`

**Migration Status**: 🔄 In Progress

- Core metrics instrumentation complete
- Legacy performance modules still exist
- New tools use unified metrics API

**Next Steps**:

- Complete migration of performance dashboards
- Remove deprecated analytics modules
- Consolidate health score calculations
