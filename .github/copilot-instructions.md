## Copilot Instructions — Crew Quickstart (concise)

Use this 1-page cheat sheet to work productively in this repo. For full details, see `docs/copilot-beast-mode.md` and the top-level `README.md`.

Big picture
- Main app: `src/ultimate_discord_intelligence_bot/` (pipelines, tools, tenancy). Orchestrator: `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` (download → transcription → content routing → quality → analysis → finalization; early-exit via `config/early_exit.yaml`).
- Platform layer: `src/platform/` (HTTP, cache, LLM routing, observability). Domains: `src/domains/` (ingest, memory, analysis). App/API: `src/app/` (Discord bot), `src/server/` (FastAPI; Prometheus `/metrics` when `ENABLE_PROMETHEUS_ENDPOINT=1`).

Guardrails (must-follow)
- Always return `StepResult` (see `src/ultimate_discord_intelligence_bot/step_result.py`): use `.ok()/.skip()/.uncertain()/.fail()` and set `error_category` + `metadata` when relevant.
- HTTP: never call `requests.*`. Use `src/platform/http/http_utils.py` (`resilient_get/resilient_post/retrying_*`; compat shim at `src/ultimate_discord_intelligence_bot/core/http_utils.py`). Enforced by `scripts/validate_http_wrappers_usage.py`.
- Tools: subclass `src/ultimate_discord_intelligence_bot/tools/_base.py::BaseTool`, export in `__all__`, and register in `src/ultimate_discord_intelligence_bot/tools/__init__.py` MAPPING. Instrument metrics via `src/ultimate_discord_intelligence_bot/obs/metrics.py` (counter `tool_runs_total`).
- Tenancy: use `with_tenant/current_tenant/mem_ns` from `src/ultimate_discord_intelligence_bot/tenancy/context.py` to scope storage, cache, metrics, and thread hops.
- No new modules under `src/core/routing/`, `src/ai/routing/`, or `src/performance/` (see `scripts/guards/deprecated_directories_guard.py`).

Developer workflows
- First time: `make first-run` → `make init-env` (creates `.env`) → `make doctor`.
- Daily: `make quick-check` (format + lint + test-fast) or `make full-check`.
- Run Discord: `make run-discord` (or `make run-discord-enhanced`), Crew mode: `make run-crew`.
- API server: `python -m server.app`. Tests: `make test-fast`, `make test`, `make test-a2a`, `make test-mcp` or `PYTHONPATH=src pytest -c .config/pytest.ini -k "..."`.
- Compliance/guards: `make guards` (HTTP/tools/metrics/deprecations) and `make compliance` (HTTP + StepResult audits).

Config & flags
- Copy `.env.example` → `.env`; set `DISCORD_BOT_TOKEN`, one of `OPENAI_API_KEY`/`OPENROUTER_API_KEY`, and Qdrant settings. Content routing thresholds live in `config/content_types.yaml`; early exits in `config/early_exit.yaml`.
- HTTP retry precedence lives in `src/platform/http/retry_config.py` (call arg → config/tenant → `RETRY_MAX_ATTEMPTS` env → secure config).
- Common flags: `ENABLE_CONTENT_ROUTING`, `ENABLE_QUALITY_FILTERING`, `ENABLE_EARLY_EXIT`, `ENABLE_SEMANTIC_CACHE*`, `ENABLE_GRAPH_MEMORY`, `ENABLE_PROMPT_COMPRESSION`, `ENABLE_PROMETHEUS_ENDPOINT`.

Pointers you’ll use a lot
- StepResult: `src/ultimate_discord_intelligence_bot/step_result.py`. Tools registry: `src/ultimate_discord_intelligence_bot/tools/__init__.py`.
- HTTP wrappers: `src/platform/http/http_utils.py`. Metrics: `src/ultimate_discord_intelligence_bot/obs/metrics.py`. Server: `src/server/app.py`.
- Guard scripts: `scripts/validate_http_wrappers_usage.py`, `scripts/metrics_instrumentation_guard.py`, `scripts/validate_tools_exports.py`, `scripts/guards/deprecated_directories_guard.py`.

Examples (inline)
- StepResult: return `StepResult.ok(result={...})` or `StepResult.fail("timeout", error_category=ErrorCategory.TIMEOUT, retryable=True)`.
- HTTP: `resp = resilient_get(url, params=..., timeout_seconds=...)`.

More details: see `docs/copilot-beast-mode.md` for the full operating manual and advanced practices.
