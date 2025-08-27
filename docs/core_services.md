# Core Services

This repository exposes a small set of global utilities under `core` that form
the foundation for higher level agents and reinforcement learning.

## Modules
- `prompt_engine.build_prompt` — deterministic prompt builder with safety
  preamble, optional context injection, and tool manifests.
- `token_meter.measure` — rough token and cost estimator based on model
  pricing.
- `learning_engine.LearningEngine` — registry-backed interface for bandit
  policies.
- `router.Router` — chooses a model/provider combination by consulting the
  learning engine.
- `eval_harness.bakeoff` — lightweight A/B testing harness that computes
  composite rewards via the reward pipeline.
- `log_schema` — dataclasses describing structured logs for calls and rewards.
- `flags.enabled` — helper to toggle features via environment variables.

These modules are intended to be small and composable so that future PRs can
wire them into agents, pipelines, and dashboards.
