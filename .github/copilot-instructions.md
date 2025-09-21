`````instructions
## 🤖 Copilot Instructions (project‑specific)
Goal: Make correct edits using existing seams; don’t invent new abstractions unless asked.

1) Big picture
- Tenant‑aware Discord intelligence on CrewAI: ingest → analyze → store/recall (Qdrant vectors + local state) → RL‑aware routing → deliver via Discord/API.
- Orchestrator lives in `src/ultimate_discord_intelligence_bot/crew.py` (AST‑inspected by tests). Agent/task config helpers and CLI live in `setup_cli.py`.

2) Where things live (edit here)
- Core (`src/core/`): HTTP wrappers `resilient_get/post`, retry helpers `retrying_get/post`, `cached_get`, time `ensure_utc`, config `secure_config.py`, flags/settings in `settings.py`.
- Tools (`src/ultimate_discord_intelligence_bot/tools/`): typed shim `tools/_base.py`; tools must return `StepResult`. yt‑dlp concentrated in `yt_dlp_download_tool.py` and platform resolvers under `tools/platform_resolver/`.
- Tenancy (`src/ultimate_discord_intelligence_bot/tenancy/`): `TenantContext`, `with_tenant`, `mem_ns`.
- Memory (`src/memory/`): `vector_store.py`, `api.py`, `qdrant_provider.py` (logical namespaces → physical names).
- Observability: `src/obs/` and shim `src/ultimate_discord_intelligence_bot/obs/metrics.py` (use `get_metrics()`), optional OTel in core.
- API/Integrations: `src/server/app.py` (A2A JSON‑RPC), MCP server (`make run-mcp`).

3) Critical contracts & conventions
- StepResult: import `from ultimate_discord_intelligence_bot.step_result import StepResult`; return `StepResult.ok|fail|skip|uncertain` (don’t raise for recoverables). Mapping/equality shims let tests compare to lists (keys: `results`/`hits`).
- HTTP: never import `requests` directly; use `core.http_utils`. Enable retries with `ENABLE_HTTP_RETRY`; attempts via `resolve_retry_attempts()` (precedence: call arg > tenants/<id>/retry.yaml or config/retry.yaml > env `RETRY_MAX_ATTEMPTS` > secure_config > default). Prefer `cached_get` for idempotent GETs.
- Tenancy: namespaces are `"{tenant}:{workspace}:{name}"` (see `tenancy/context.py`, `VectorStore.namespace`). Qdrant physical names replace `:` with `__`. Always derive namespaces via helpers.
- Time: normalize with `core.time.ensure_utc`. Secrets/flags via `core.secure_config.get_config()` (never hardcode tokens).
- Metrics: obtain via `ultimate_discord_intelligence_bot/obs/metrics.get_metrics()`; keep labels low‑cardinality (don’t include tenant text).

4) Daily workflows (verified Makefile targets)
- First‑run: `make setup` (wizard) → `make doctor` (env + ffmpeg + yt‑dlp checks).
- Run: Discord bot `make run-discord`; crew demo `make run-crew`; MCP `make run-mcp`.
- Quick checks: `make quick-check` or `make test-fast`; clean env variant `make test-fast-clean-env`.
- Lint/format/type: `make format lint type`; regression guard `make type-guard` (baseline `reports/mypy_snapshot.json`).
- Compliance/guards: `make compliance` (HTTP + StepResult audits), `make compliance-fix`, `make compliance-summary`, `make guards`.
- Env bootstrap: `make ensure-venv` or `make uv-bootstrap`; lock/sync: `make uv-lock` / `make uv-sync`.

5) Extending the system
- New tool: subclass `tools/_base.BaseTool`; implement `run()` returning `StepResult`; register with agents/tasks in crew or config where appropriate.
- Memory: prefer `memory/api.py`. If using `VectorStore` directly, build namespaces with `VectorStore.namespace(tenant, workspace, name)`; dimension mismatches raise.
- Enhanced crew: `enhanced_crew_integration.py` (see `EnhancedCrewExecutor.execute_with_comprehensive_monitoring`). Feature flags exist for trajectory/enhanced evaluation.

6) Gotchas (repo‑specific)
- Tests parse `crew.py` and assert specific kwargs exist (e.g., `planning=True`, `memory=True`, `cache=True`, `embedder=`); don’t remove those strings.
- Migration: `ENABLE_ANALYSIS_HTTP_RETRY` → `ENABLE_HTTP_RETRY` (grace until 2025‑12‑31; helper `scripts/migrate_http_retry_flag.py`).
- Don’t bypass wrappers: no raw `requests`, no naive `datetime.now()` (use UTC), no direct Qdrant calls without sanitized namespaces, no direct `yt_dlp` imports outside `tools/yt_dlp_download_tool.py`.
- Vector store enforces batch sizing/dimensions and will raise on mismatches (`src/memory/vector_store.py`).

7) Reference touchpoints
- Orchestrator `src/ultimate_discord_intelligence_bot/crew.py`; Setup `setup_cli.py`; HTTP `src/core/http_utils.py`; Tenancy `tenancy/context.py`; Metrics `obs/metrics.py`; Enhanced `enhanced_crew_integration.py`; A2A `src/server/app.py`; Tests config `config/pytest.ini`.
\n+8) Do / Don’t quick guide
- Do: return `StepResult.ok|fail|skip|uncertain` from tools; use `core.http_utils` for HTTP; build vector namespaces via `VectorStore.namespace`; use `ensure_utc` for datetimes; fetch metrics via `obs/metrics.get_metrics()`.
- Don’t: import `requests` directly; import `yt_dlp` outside `tools/yt_dlp_download_tool.py`; call Qdrant directly with raw names; remove required strings from `crew.py`.
- Tools importability: all tools are lazily exported from `ultimate_discord_intelligence_bot.tools` with stub fallbacks for optional deps (stubs return `StepResult.fail` on `run()`).

Troubleshooting:
- In environments without FAISS, semantic cache automatically degrades to scalar-only mode; no auto-install attempts occur. Enable FAISS to restore vector similarity.
- MCP import safety: MCP modules (including the core aggregator) import successfully even when FastMCP isn’t installed. They expose stub `.tool`/`.resource` decorators and a `.mount` no‑op; attempting to run them without `.[mcp]` raises a clear error.
`````
