## AI Agent Guide

```instructions
- Architecture: Multi-agent Discord intelligence system; main app under `src/ultimate_discord_intelligence_bot/`; platform services in `src/core/` (routing/cache/resilience), `src/ai/` (LLM routing), `src/memory/` (vector/graph), `src/obs/` (metrics/tracing), `src/server/` (FastAPI).
- Pipeline: `ContentPipeline` (`src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`) runs download → transcription → content routing → quality gate → analysis (fallacy + perspective in parallel) → finalization (memory/Discord fan-out). Each phase returns `StepResult`; on failure, downstream tasks are cancelled.
- Early exits: Post-download and post-transcription checkpoints (`_check_early_exit_condition`) use `src/ultimate_discord_intelligence_bot/config/early_exit_checkpoints.yaml` to skip low-value content (saves ~75–90%).
- StepResult pattern: Use `src/ultimate_discord_intelligence_bot/step_result.py` with `.ok()/.skip()/.fail()/.uncertain()/.with_context()` and `error_category` from `ErrorCategory`. Prefer returning structured `data` and fill `metadata` for observability and retries.
- Tools: Subclass `tools/_base.BaseTool`; implement `run()` returning `StepResult`; export via module `__all__`, register in `MAPPING`, and increment `obs.metrics.get_metrics().counter("tool_runs_total", labels={"tool": self.name})` inside `run()`.
- HTTP & downloads: Use `core/http_utils.resilient_get/resilient_post/retrying_*`; never `requests.*` directly (guarded by `scripts/validate_http_wrappers_usage.py`). Use `tools/acquisition/multi_platform_download_tool.MultiPlatformDownloadTool`; don’t shell out to `yt-dlp`.
- Tenancy: Wrap storage/cache/metrics with `with_tenant(TenantContext(...))` (`src/ultimate_discord_intelligence_bot/tenancy/context.py`); read via `current_tenant()`; namespace keys with `mem_ns(ctx, "collection")`. Tenant configs live under `tenants/<slug>/` (created by setup wizard).
- API service: `src/server/app.py::create_app()` wires CORS → metrics (`add_metrics_middleware`) → API cache → Prometheus `/metrics` (flag: `ENABLE_PROMETHEUS_ENDPOINT`) → rate limiting. Keep `/metrics` and `/health` outside tenant/rate-limit guards.
- LLM routing & cache: `services/openrouter_service.py` selects models (LinUCB/VW) under `src/ai/`, tracks spend with TokenMeter, consults semantic caches (`cache/semantic/`). Respect `ENABLE_SEMANTIC_CACHE*` flags.
- Memory & caching: Get Qdrant via `memory/qdrant_provider.get_qdrant_client()` (pooled/dummy in tests). Prefer unified multi-level cache (`core/cache/multi_level_cache.py`); see ADR `docs/architecture/adr-0001-cache-platform.md`.
- Content routing & quality: `ContentTypeRoutingTool` + `config/content_types.yaml` set thresholds (`QUALITY_MIN_*`) per content type. Orchestrator falls back to env defaults if disabled.
- Developer workflow: `make init-env` → `make first-run` → `make doctor`. Daily: `make quick-check` or `make full-check`; run `make guards` after changing HTTP/tools; `make compliance` for HTTP/StepResult audits.
- Run targets: `make run-discord`, `make run-discord-enhanced`, `make run-crew`, `make run-mcp`, `python -m server.app`.
- Tests: `make test-fast`, `make test-a2a`, `make test-mcp` (or run pytest with repo’s config). CI uses `ci-all` (doctor + format-check + lint + type + guards + test + compliance + deprecations-strict).
- Guardrails: No new code in `src/core/routing/`, `src/ai/routing/`, `src/performance/`; avoid legacy cache optimizers (enforced by `scripts/guards/deprecated_directories_guard.py`).
- Feature flags: Use `src/core/settings.py` + `core/secure_config.get_config()`; document new flags in `.env.example`. Key: `ENABLE_CONTENT_ROUTING`, `ENABLE_SEMANTIC_CACHE*`, `ENABLE_GRAPH_MEMORY`, `ENABLE_HIPPORAG_MEMORY`, `ENABLE_PROMETHEUS_ENDPOINT`.
- Data & config: Runtime artifacts in `crew_data/`; archives in `archive/` + `benchmarks/`. YAML config in `src/ultimate_discord_intelligence_bot/config/` (e.g., `content_types.yaml`, `early_exit_checkpoints.yaml`).
- References: `README.md`, `CLAUDE.md`, `docs/dev_assistants/`, ADRs under `docs/architecture/`.
```
