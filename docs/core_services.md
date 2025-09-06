# Core Services

This repository exposes a comprehensive set of global utilities under `core` that form
the foundation for higher level agents and reinforcement learning.

## Core Modules

### Essential Services
- `prompt_engine.build_prompt` — deterministic prompt builder with safety
  preamble, optional context injection, and tool manifests.
- `token_meter.measure` — rough token and cost estimator based on model
  pricing.
- `learning_engine.LearningEngine` — registry-backed interface for bandit
  policies and reinforcement learning.
- `router.Router` — chooses a model/provider combination by consulting the
  learning engine.

### Evaluation & Testing
- `eval_harness.bakeoff` — lightweight A/B testing harness that computes
  composite rewards via the reward pipeline.
- `reward_pipe` — reward calculation and aggregation pipeline for RL feedback.

### System Management
- `src/core/alerts.py` — system alerting and notification management.
- `src/core/reliability.py` — circuit breakers, retries, and reliability patterns.
- `src/core/rollout.py` — feature rollout management and canary deployments.
- `src/core/tool_planner.py` — intelligent tool selection and execution planning.

### Infrastructure
- `flags.enabled` — helper to toggle features via environment variables.
- `log_schema` — dataclasses describing structured logs for calls and rewards.
- `src/core/learn.py` — convenience helpers for integrating learning into decision loops.

### Caching & Performance
- `cache/` — caching subsystem with LRU, TTL, and distributed caching support.

### Security & Privacy  
- `privacy/` — privacy filtering, PII detection, and data anonymization.

### Reinforcement Learning
- `rl/` — core reinforcement learning algorithms and bandit policies.

## Architecture Patterns

These modules are intended to be small and composable so that future PRs can
wire them into agents, pipelines, and dashboards. They follow consistent patterns:

- **Tenant awareness** — All operations respect tenant context when available
- **Observability** — Built-in tracing, metrics, and structured logging
- **Error handling** — Graceful degradation and comprehensive error reporting
- **Configuration** — Environment-based configuration with sensible defaults
- **Testing** — Comprehensive test coverage with mocked dependencies

### HTTP Utility Monkeypatch Preservation (Testing Note)
`core.http_utils` includes a lightweight shim that preserves externally
monkeypatched `resilient_post` / `resilient_get` objects across a module reload.
This supports legacy tests that patch, then reload the module (which would
otherwise restore the original implementations). Prefer patching *after* import
in new tests to keep the surface minimal; the shim can be safely removed once
all reload-after-patch patterns are retired.
