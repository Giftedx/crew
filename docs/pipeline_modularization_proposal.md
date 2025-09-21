# Pipeline Modularization Proposal

Date: 2025-09-21

Owner: Engineering

Status: Draft (for review)

## Goals

- Improve maintainability and testability of the pipeline by separating orchestration from step implementations.
- Enable cross-cutting concerns (metrics, retries, time, tenancy) via composable middleware.
- Ensure backward compatibility with existing `pipeline.py`/`crew.py` entry points.

## Overview

Introduce a small set of interfaces and a pluggable execution engine:

- Step interface: a single unit of work with typed inputs/outputs and idempotency marker.
- Executor: runs Steps with uniform observability and error handling.
- Middleware: cross-cutting concerns layered around Step execution (metrics, retries, caching, tracing, tenancy context).
- Registry: declarative wiring of Steps and Middleware per pipeline or agent.

## Contracts (concise)

- Step
  - inputs: dict[str, Any] (or pydantic model)
  - outputs: dict[str, Any] (or pydantic model)
  - run(context) -> outputs
  - idempotent: bool
- Executor
  - execute(step, context) -> outputs
  - applies middleware chain around step.run
- Middleware
  - before(context)
  - after(context, result)
  - on_error(context, error)

## Minimal API Sketch

- `src/pipeline/core/step.py` Step base class
- `src/pipeline/core/executor.py` Executor with middleware chain
- `src/pipeline/core/middleware.py` Middleware protocol and built-ins
- `src/pipeline/registry.py` declarative wiring

## Built-in Middleware

- Metrics/tracing (re-use `ultimate_discord_intelligence_bot.obs.metrics.get_metrics()` and core tracing patterns)
- Retry (use `core.http_utils.resolve_retry_attempts()` and ENABLE_HTTP_RETRY flag conventions)
- UTC time enforcement (use `core.time.ensure_utc`/`default_utc_now` guards)
- Tenancy scoping (use `ultimate_discord_intelligence_bot.tenancy` helpers)
- Caching (reuse `core.http_utils.cached_get` when applicable)

## Migration Plan (safe, incremental)

1. Carve interfaces and a thin executor into `src/pipeline/core/` (no behavior change).
1. Wrap one low-risk existing pipeline segment as a Step (adapter layer keeps old call sites working).
1. Add metrics + UTC middleware only; keep retries/caching off by default.
1. Add tests (unit for Step contract + integration smoke) and run under `make test-fast`.
1. Expand to additional steps; enable retry middleware via feature flag per pipeline.

## Testing Strategy

- Unit tests: Step run semantics, Middleware hooks, error propagation.
- Integration: execute a small composed pipeline, assert metrics/tracing and UTC timestamps.
- Backward-compatible: preserve existing CLI/entry points; adapters verify equivalent outputs.

## Risks & Mitigations

- Risk: Over-abstraction. Mitigation: Keep API minimal; only 3 core files; zero required dependencies.
- Risk: Behavior drift. Mitigation: Golden tests and contract tests for adapted steps.
- Risk: Perf overhead from middleware chain. Mitigation: short-circuit no-op middleware when disabled.

## Rollout

- Phase A: land core interfaces and no-op executor; docs and examples.
- Phase B: migrate one step + metrics/UTC middleware; run behind feature flag.
- Phase C: adopt retries/tenancy middleware for high-value pipelines; monitor.

## Appendix

- Aligns with existing contracts:
  - HTTP wrappers and feature flags
  - UTC utilities
  - Tenancy namespace rules
  - Metrics/tracing facade
