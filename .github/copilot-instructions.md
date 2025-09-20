`````instructions
## 🤖 Copilot Instructions (project‑specific)
Goal: Make correct edits using existing seams; don’t invent new abstractions unless asked.

1) Big picture
- Tenant‑aware Discord intelligence on CrewAI: ingest → analyze → store/recall (Qdrant vectors + local state) → RL‑aware routing → deliver via Discord/API.
- Orchestrator: `src/ultimate_discord_intelligence_bot/crew.py` (agents/tasks via `_agent_from_config`/`_task_from_config`). Agent YAML: `src/ultimate_discord_intelligence_bot/config/{agents.yaml,tasks.yaml}`.

2) Where things live (edit here)
- Core: `src/core/` (HTTP `resilient_get/post`, feature‑flagged `retrying_get/post`, `cached_get`, time `ensure_utc`, secure config `secure_config.py`, `settings.py`).
- Tools: `src/ultimate_discord_intelligence_bot/tools/` (typed shim `tools/_base.py`; tools return `StepResult`). yt‑dlp centralized in `tools/yt_dlp_download_tool.py`.
- Tenancy: `src/ultimate_discord_intelligence_bot/tenancy/` (`TenantContext`, `with_tenant`, `mem_ns`).
- Memory & vectors: `src/memory/` (`vector_store.py`, `api.py`, `qdrant_provider.py`), logical namespaces map to physical names.
- Observability: `src/obs/` and `src/ultimate_discord_intelligence_bot/obs/` (metrics facade `get_metrics()`, optional OTel tracing).
- Evaluations: `src/eval/` (`trajectory_evaluator.py`, scorers, runner) and `tests/`.

3) Critical contracts & conventions
- StepResult: `from ultimate_discord_intelligence_bot.step_result import StepResult`; return `StepResult.ok|fail|skip|uncertain` (don’t raise for recoverables). Mapping/equality shims let tests compare to lists (`results`/`hits`).
- Tenant namespaces: `f"{tenant_id}:{workspace_id}:{name}"` (see `tenancy/context.py`, `VectorStore.namespace`); Qdrant physical names replace `:` with `__`; dimension mismatches raise.
- HTTP: never import `requests` directly. Use `core.http_utils` wrappers. Retries via `ENABLE_HTTP_RETRY`; attempts resolved by `resolve_retry_attempts()` (call arg > config/tenant `config/retry.yaml` > env > default). Prefer `cached_get` for idempotent GETs.
- Time/config: use `core.time.ensure_utc`; secrets/flags via `core.secure_config.get_config()` (API keys, webhooks, feature flags).

4) Daily workflows (zsh‑friendly)
- First‑run: `make setup` (wizard in `setup_cli.py`) → `make doctor` (env + ffmpeg + yt‑dlp checks).
- Run: Discord bot `make run-discord`; crew demo `make run-crew`.
- Quick checks: `make quick-check` or `make test-fast`; clean env variant `make test-fast-clean-env`.
- Lint/format/type: `make format lint type`; regression guard `make type-guard` (baseline `reports/mypy_snapshot.json`).
- Compliance/guards: `make compliance` (HTTP + StepResult audits), `make compliance-fix`, `make compliance-summary`, `make guards`.
- Env bootstrap: `make ensure-venv` or `make uv-bootstrap`; lock/sync: `make uv-lock` / `make uv-sync`.

5) Extending the system
- New tool: subclass `tools/_base.BaseTool`; implement `run/_run` returning `StepResult`; register in `crew.py`, wire in `config/agents.yaml`.
- Memory: prefer `memory/api.py`; if using `VectorStore` directly, always build namespaces via `VectorStore.namespace(tenant, workspace, name)`.
- Enhanced crew: see `enhanced_crew_integration.py` (`EnhancedCrewExecutor.execute_with_comprehensive_monitoring`). Flags: `ENABLE_TRAJECTORY_EVALUATION`, `ENABLE_ENHANCED_CREW_EVALUATION`.

6) Observability patterns
- One tracing span per logical op (see `core/http_utils`). Metrics via `ultimate_discord_intelligence_bot.obs.metrics.get_metrics()`; keep labels low‑cardinality (no tenant text).

7) Gotchas (repo‑specific)
- Feature flags can no‑op paths; run `make doctor`. Migration: `ENABLE_ANALYSIS_HTTP_RETRY` → `ENABLE_HTTP_RETRY` (grace until 2025‑12‑31; helper `scripts/migrate_http_retry_flag.py`).
- Don’t bypass wrappers: no raw `requests`, no `datetime.now()` without UTC, no direct Qdrant calls without namespace sanitation, no direct `yt_dlp` imports outside `tools/yt_dlp_download_tool.py`.
- Vector store enforces batch sizing/dimensions; mismatched dims raise (`memory/vector_store.py`).

### Reference touchpoints
- **Orchestrator**: `src/ultimate_discord_intelligence_bot/crew.py`.
- **Setup/runners**: `src/ultimate_discord_intelligence_bot/setup_cli.py`.
- **HTTP + retry/caching**: `src/core/http_utils.py`.
- **Tenancy helpers**: `src/ultimate_discord_intelligence_bot/tenancy/context.py`.
- **Metrics facade**: `src/ultimate_discord_intelligence_bot/obs/metrics.py`.
- **Enhanced performance**: `src/ultimate_discord_intelligence_bot/enhanced_crew_integration.py`.
- **A2A JSON-RPC**: `src/server/app.py` (API routes), Postman/Insomnia collections in `docs/`.
`````
