## Copilot Instructions — Ultimate Discord Intelligence Bot (Quickstart)

Use this as your operating cheat sheet when coding in this repo. A full-length manual remains available below and at `docs/copilot-beast-mode.md`.

Big picture architecture
- Primary app: `src/ultimate_discord_intelligence_bot/` (agents, tools, pipeline, tenancy)
- Supporting domains: `src/core/` (http_utils, cache, secure_config), `src/obs/` (metrics/tracing), `src/server/` (FastAPI API), `src/memory/` (Qdrant), `src/ai/` (routing/bandits)
- Pipeline: download → transcription → content routing → quality filter → analysis → finalization; orchestrator at `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` with early-exit checkpoints and Langfuse spans

Mandatory patterns and guardrails
- Always return `StepResult` (see `src/ultimate_discord_intelligence_bot/step_result.py`): use `.ok()/.skip()/.uncertain()/.fail()` and set `error_category`, `metadata` when relevant
- HTTP: never call `requests.*`; use `core/http_utils.py` (`resilient_get/post/delete`, `retrying_*`, `cached_get`). Guarded by `scripts/validate_http_wrappers_usage.py`
- Tools: subclass `tools/_base.BaseTool`, export in `ultimate_discord_intelligence_bot.tools.__all__`, and register in MAPPING. Add metrics instrumentation via `obs.metrics.get_metrics().counter('tool_runs_total', labels={'tool': self.name, 'outcome': ...})`. Guarded by `scripts/metrics_instrumentation_guard.py` and `scripts/validate_tools_exports.py`
- Tenancy: wrap storage/cache/metrics inside `with_tenant(...)`; derive names via `mem_ns(...)`; get Qdrant via `memory/qdrant_provider.get_qdrant_client()`
- Restricted: do not add new modules under `src/core/routing/`, `src/ai/routing/`, or `src/performance/` (see `scripts/guards/deprecated_directories_guard.py`)

Core workflows (Makefile)
- Bootstrap: `make first-run` → `make init-env` (copies `.env.example`) → `make doctor`
- Fast sweep: `make quick-check` (format + lint + test-fast); full: `make full-check`
- Run bot: `make run-discord` (or `make run-discord-enhanced` for feature flags); Crew-only: `make run-crew`
- API server: `python -m server.app` (Prometheus `/metrics` exposed when `ENABLE_PROMETHEUS_ENDPOINT=1`)
- Tests: `make test-fast` (http/cache/vector guards), or `PYTHONPATH=src pytest -c .config/pytest.ini` for focused runs
- Compliance: `make guards` (HTTP/tools/metrics guards) and `make compliance` (HTTP + StepResult audits)

Configuration and feature flags
- Copy `env.example` → `.env` and set required secrets: `DISCORD_BOT_TOKEN`, `OPENAI_API_KEY`/`OPENROUTER_API_KEY`, and Qdrant settings
- Useful flags: `ENABLE_CONTENT_ROUTING`, `ENABLE_QUALITY_FILTERING`, `ENABLE_EARLY_EXIT`, `ENABLE_SEMANTIC_CACHE*`, `ENABLE_GRAPH_MEMORY`, `ENABLE_PROMETHEUS_ENDPOINT`
- HTTP retries are resolved via `core/http_utils.resolve_retry_attempts()` with precedence (call arg → `config/retry.yaml`/tenant → `RETRY_MAX_ATTEMPTS` → secure config)

Pointers you’ll use a lot
- Orchestrator: `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`
- Results contract: `src/ultimate_discord_intelligence_bot/step_result.py`
- HTTP facade: `src/core/http_utils.py`
- Metrics: `src/obs/metrics.py` (+ `/server/app.py` for middleware and `/metrics` route)
- Guardrails: `scripts/validate_http_wrappers_usage.py`, `scripts/metrics_instrumentation_guard.py`, `scripts/guards/deprecated_directories_guard.py`

Example snippets
- StepResult: `return StepResult.ok(result={'score': 0.91})` or `return StepResult.fail('timeout', error_category=ErrorCategory.TIMEOUT, retryable=True)`
- HTTP: `resp = resilient_get(url, params=..., timeout_seconds=REQUEST_TIMEOUT_SECONDS)`

Full manual
- See `docs/copilot-beast-mode.md`. The legacy full guide is also retained below for continuity.

---

## Copilot Beast Mode — Operating Manual

### 0. Prime Directives
- Ship production-ready outcomes autonomously. Do not hand control back until the user goal is fully delivered, validated, and documented.
- Default to decisive action: investigate, plan, implement, test, and summarize unless you are legitimately blocked by missing secrets, approvals, or context.
- Operate transparently. Surface assumptions, dead ends, and recovery steps in real time; never conceal errors or partial work.
- Communicate with an upbeat, professional tone. Keep responses concise yet thorough, and follow the KaTeX math style requirements when presenting formulas.

### 1. Quick-Start Checklist (run every session)
- [ ] Ingest the latest context (issues, docs, diffs, terminals, instructions attachments).
- [ ] Build a task-focused plan and publish a checkbox to-do list before editing anything.
- [ ] Confirm guardrails and feature flags that apply to the work.
- [ ] Identify success criteria, expected validations, and any observability hooks.

### 2. Operating Loop — Plan → Build → Verify → Report
1. **Discover**: enumerate what success looks like, note open questions, and record assumptions.
2. **Plan**: refine the to-do list into executable steps. Update it as progress is made.
3. **Execute**: apply minimal, surgical diffs that preserve style and public APIs. Instrument as needed.
4. **Verify**: run targeted tests (unit → integration → regression). Re-run suites after significant changes; capture command output verbatim.
5. **Report**: produce a final summary that maps work to requirements, lists tests, notes follow-ups, and references modified files.

### 3. Research & Discovery Protocol
- Exhaust local knowledge first: READMEs, ADRs, runbooks, code comments, prior commits.
- When a URL is provided (or discovered in fetched content), you **must** retrieve it via the `fetch_webpage` tool, crawling relevant links recursively until you have the necessary data.
- Cross-check multiple sources; cite filenames, line numbers, or external references that justify decisions.
- Maintain an assumption ledger. Reconcile or flag unresolved assumptions before finalizing work.

### 4. Implementation Guardrails
- **Code boundaries**: do **not** add or modify code under `src/core/routing/`, `src/ai/routing/`, or `src/performance/` unless explicitly authorized.
- **HTTP & I/O**: never use `requests.*` directly. Rely on `core/http_utils.py` wrappers (`resilient_get`, `resilient_post`, `retrying_*`).
- **StepResult contract**: return `StepResult.ok/skip/fail/uncertain/with_context`, populate `metadata`, and set an `ErrorCategory` on failures.
- **Tenancy discipline**: wrap storage, cache, and metrics calls inside `with_tenant(TenantContext(...))`; derive namespace keys via `mem_ns(ctx, "collection")`.
- **Metrics**: declare Prometheus metrics in `src/obs/metrics.py`, register them in `src/obs/metric_specs.py`, and provide non-Prometheus fallbacks.
- **Configuration**: surface settings through `core/settings.py`, document defaults in `.env.example`, and mention them in relevant READMEs/runbooks.

### 5. Testing & Verification Ladder
- **Baseline**: `make quick-check` or `make full-check` for daily hygiene.
- **Targeted suites**:
	- `make test-fast` → fast regression sweep.
	- `make test-a2a`, `make test-mcp` → API/MCP coverage.
	- `pytest tests/...` → focused scope; prefer narrowing to relevant directories.
- **Quality gates**: when touching HTTP, tools, or governance flows, run `make guards` and `make compliance`.
- **Performance/observability**: leverage `run_observability_tests.py`, `run_safety_tests.py`, or custom benchmarks where changes affect telemetry or latency.
- Record every command and outcome in the final summary. Re-run suites after fixes to confirm stability.

### 6. Communication & Documentation Protocol
- Maintain and update the checkbox plan after each completed step; mark skipped items with justification.
- Provide intermediate status only when it unblocks understanding; focus on progress.
- Summaries must include: changes made, tests executed (with verdicts), impacted files/directories, follow-up work, and residual risks or TODOs.
- Explain major design decisions and reference supporting sources (file paths, ADRs, dashboards).
- Render equations with KaTeX syntax (`$inline$`, `$$block$$`) whenever formulas are required.

### 7. Risk, Assumptions & Escalation
- Track risks and mitigations as you work. Elevate high-variance or compliance-related risks early.
- Escalate immediately when secrets, credentials, approvals, or policy constraints block progress—provide suggested next steps.
- Convert open questions into explicit follow-ups in the final summary. Do not silently defer.

### 8. Observability & Tooling Expectations
- For new tools, subclass `tools/_base.BaseTool`, export via module `__all__`, register in the tool `MAPPING`, and increment `obs.metrics.get_metrics().counter("tool_runs_total", labels={"tool": self.name})` inside `run()`.
- For LLM routing changes, respect feature flags (`ENABLE_SEMANTIC_CACHE*`, contextual bandits) and integrate with `TokenMeter` for spend tracking.
- Memory integrations must obtain Qdrant clients via `memory/qdrant_provider.get_qdrant_client()` and prefer the unified multi-level cache (`core/cache/multi_level_cache.py`).
- Follow the multi-level cache ADR (`docs/architecture/adr-0001-cache-platform.md`) and RL telemetry runbooks when modifying observability paths.

### 9. Reference Atlas
- **Primary app**: `src/ultimate_discord_intelligence_bot/` (pipelines, orchestrators, tools, tenants).
- **Supporting domains**:
	- `src/core/` – routing, resilience, HTTP, configuration, storage.
	- `src/ai/` – bandits, routing logic, RL feedback orchestrators.
	- `src/memory/` – vector and graph memory providers.
	- `src/obs/` – metrics, dashboards, enhanced monitoring.
	- `src/server/` & `src/fastapi/` – API surface, middleware, rate limiting.
- **Configuration & data**: YAML in `src/ultimate_discord_intelligence_bot/config/`, runtime artifacts in `crew_data/`, long-term archives in `archive/` & `benchmarks/`.
- **Developer workflows**: `make init-env`, `make first-run`, `make doctor`, plus run targets (`make run-discord`, `make run-discord-enhanced`, `make run-crew`, `make run-mcp`, `python -m server.app`).

### Appendix — AI Agent Guide
```instructions
- Architecture: Multi-agent Discord intelligence system; main app under `src/ultimate_discord_intelligence_bot/`; platform services in `src/core/` (routing/cache/resilience), `src/ai/` (LLM routing), `src/memory/` (vector/graph), `src/obs/` (metrics/tracing), `src/server/` (FastAPI).
- Pipeline: `ContentPipeline` (`src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`) runs download → transcription → content routing → quality gate → analysis (fallacy + perspective in parallel) → finalization (memory/Discord fan-out). Each phase returns `StepResult`; on failure, downstream tasks are cancelled.
- Early exits: Post-download and post-transcription checkpoints (`_check_early_exit_condition`) use `src/ultimate_discord_intelligence_bot/config/early_exit_checkpoints.yaml` to skip low-value content (saves ~75–90%).
- StepResult pattern: Use `src/ultimate_discord_intelligence_bot/step_result.py` with `.ok()/.skip()/.fail()/.uncertain()/.with_context()` and `error_category` from `ErrorCategory`. Prefer returning structured `data` and fill `metadata` for observability and retries.
- Tools: Subclass `tools/_base.BaseTool`; implement `run()` returning `StepResult`; export via module `__all__`, register in `MAPPING`, and increment `obs.metrics.get_metrics().counter("tool_runs_total", labels={"tool": self.name})` inside `run()`.
- HTTP & downloads: Use `core/http_utils.resilient_get/resilient_post/retrying_*`; never `requests.*` directly (guarded by `scripts/validate_http_wrappers_usage.py`). Use `tools/acquisition/multi_platform_download_tool.MultiPlatformDownloadTool`; do not shell out to `yt-dlp`.
- Tenancy: Wrap storage/cache/metrics with `with_tenant(TenantContext(...))` (`src/ultimate_discord_intelligence_bot/tenancy/context.py`); read via `current_tenant()`; namespace keys with `mem_ns(ctx, "collection")`. Tenant configs live under `tenants/<slug>/` (created by the setup wizard).
- API service: `src/server/app.py::create_app()` wires CORS → metrics (`add_metrics_middleware`) → API cache → Prometheus `/metrics` (flag: `ENABLE_PROMETHEUS_ENDPOINT`) → rate limiting. Keep `/metrics` and `/health` outside tenant/rate-limit guards.
- LLM routing & cache: `services/openrouter_service.py` selects models (LinUCB/VW) under `src/ai/`, tracks spend with `TokenMeter`, consults semantic caches (`cache/semantic/`). Respect `ENABLE_SEMANTIC_CACHE*` flags.
- Memory & caching: Get Qdrant via `memory/qdrant_provider.get_qdrant_client()` (pooled/dummy in tests). Prefer unified multi-level cache (`core/cache/multi_level_cache.py`); see ADR `docs/architecture/adr-0001-cache-platform.md`.
- Content routing & quality: `ContentTypeRoutingTool` + `config/content_types.yaml` set thresholds (`QUALITY_MIN_*`) per content type. Orchestrator falls back to env defaults if disabled.
- Developer workflow: `make init-env` → `make first-run` → `make doctor`. Daily: `make quick-check` or `make full-check`; run `make guards` after changing HTTP/tools; `make compliance` for HTTP/StepResult audits.
- Run targets: `make run-discord`, `make run-discord-enhanced`, `make run-crew`, `make run-mcp`, `python -m server.app`.
- Tests: `make test-fast`, `make test-a2a`, `make test-mcp` (or run pytest with repo’s config). CI uses `ci-all` (doctor + format-check + lint + type + guards + test + compliance + deprecations-strict).
- Guardrails: No new code in `src/core/routing/`, `src/ai/routing/`, `src/performance/`; avoid legacy cache optimizers (enforced by `scripts/guards/deprecated_directories_guard.py`).
- Feature flags: Use `src/core/settings.py` + `core/secure_config.get_config()`; document new flags in `.env.example`. Key: `ENABLE_CONTENT_ROUTING`, `ENABLE_SEMANTIC_CACHE*`, `ENABLE_GRAPH_MEMORY`, `ENABLE_HIPPORAG_MEMORY`, `ENABLE_PROMETHEUS_ENDPOINT`.
- Data & config: Runtime artifacts in `crew_data/`; archives in `archive/` + `benchmarks/`. YAML config in `src/ultimate_discord_intelligence_bot/config/` (e.g., `content_types.yaml`, `early_exit_checkpoints.yaml`).
- Enhancements: New cutting-edge integrations in `src/enhancements/` — GraphRAG (`graphrag_integration.py`) for knowledge graph memory, DSPy (`dspy_prompt_optimizer.py`) for prompt optimization, Contextual Bandits (`contextual_bandits_router.py`) for intelligent model routing. Follow the `StepResult` patterns.
- References: `README.md`, `CLAUDE.md`, `docs/dev_assistants/`, ADRs under `docs/architecture/`.
```
