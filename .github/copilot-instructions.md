## 🤖 Copilot Instructions (Project-Specific, ~50 lines)
Goal: Accelerate correct edits. Reuse existing seams; never invent parallel abstractions unless explicitly requested. Pair with `copilot-quickref.md` for command cheatsheet.

### 1. Mental Model
Ingestion (multi‑platform dispatcher) → transcription (Whisper / faster‑whisper fallback) → analysis (sentiment / claims / topics / fallacies) → memory (Qdrant or in‑mem) → grounding & routing → Discord / API response. Orchestrated in `src/ultimate_discord_intelligence_bot/crew.py` with agent/task YAML under `config/`.

### 2. Directory Landmarks
`core/` feature flags, HTTP wrappers (`resilient_*`, `retrying_*`), routing + RL helpers, time utils.
`analysis/` segmentation + sentiment/claims/topics/fallacies modules (all return `StepResult`).
`ingest/` source adapters & dispatcher (`ingest/sources/<platform>.py`).
`memory/` vector + metadata stores (namespace = `tenant:workspace`).
`obs/` tracing + metrics bootstrap (init exactly once per entrypoint).
`scheduler/` job dataclasses + handlers; deterministic job keys dedupe.
`grounding/`, `debate/`, `kg/`, `eval/` higher‑order reasoning.
`policy/`, `security/` moderation, rate limits, governance.

### 3. StepResult Contract
Return `StepResult.ok|fail|skip` for external/system ops. Recoverable issues (404, empty transcript) => `fail` or `skip`, not raise. Legacy dict tools → wrap with `StepResult.from_dict`. Vector search returns raw `[ {text, score}, ... ]` (no wrapper). Log/increment metrics BEFORE returning. Raise only for programmer errors.

### 4. Tenancy
Always pass `TenantContext` (use `with_tenant`). Never place raw user text / URLs in metric labels or namespaces. New stateful components MUST accept `(tenant, workspace)` early.

### 5. Feature Flags & Deprecations
Flags: `ENABLE_<AREA>_<FEATURE>` (default off). Examples: `ENABLE_HTTP_RETRY`, `ENABLE_INGEST_CONCURRENT`, `ENABLE_RL_GLOBAL`, `ENABLE_RL_ROUTING`. Strict ingest: `ENABLE_INGEST_STRICT=1`. Privacy flags tolerate flexible casing (e.g. `enable_pii_detection`). When touching deprecated surfaces: emit `DeprecationWarning` + run `make docs` to refresh reports/badge. Respect replacements shown in root README.

### 6. Routing & RL
`PromptEngine.build` → capability/cost filter → ε‑greedy explore (flags on) → `OpenRouterService.call` (metered by `TokenMeter`) → `LearningEngine.record(model, reward, cached=?, error_type=?)`. Failure reward = 0; negative only for policy / safety violations.

### 7. Scheduler
Add job: dataclass in `scheduler/jobs/`; handler in `scheduler/handlers/`; update registry mapping. Deterministic key (URL + bucket) prevents dupes. Backpressure: drop lowest priority (emits existing metric; do not rename labels).

### 8. Determinism & Time
UTC only via `core.time.ensure_utc`. Use stable hashing of URLs for IDs; normalize case before diffing. Guard heavy/experimental paths with flags to keep reproducible tests.

### 9. HTTP & Caching
Do NOT call `requests` directly; use wrappers in `core/http_utils.py`. Cached fetch: `cached_get` (auto Redis/in‑mem). Retry config: `retry.yaml` (tenant or global) with `max_attempts:`; parser is built‑in—no extra deps.

### 10. Observability
One tracing span per logical op. Increment metrics before returning. Define metrics centrally (avoid dynamic/high cardinality). Labels limited to tenant/workspace/enums. Deprecation flags: log once pattern (see `core.http_utils`). Use tracing + metrics; no `print` for runtime signaling.

### 11. Memory Layer
Interact through `memory/api.py` (store + vector_store). Enforce retention; prune with `api.prune`. Qdrant missing ⇒ in‑mem fallback (good for tests, not perf). Archive/pin via archiver facade—do not bypass.

### 12. Testing & CI Routines
Bootstrap: `make ensure-venv` then `pip install -e '.[dev]'` (or `make uv-bootstrap`).
Quality sweep: `make format lint type`.
Fast tests: `make test-fast`; Full: `make test`.
Type regression guard: `make type-guard` / update snapshot after reductions.
Docs & deprecations: `make docs` (writes reports + badge).
Compliance audits: `make compliance` | auto-fix `make compliance-fix`.
Eval golden set: `make eval`.

### 13. Adding Functionality
Ingestion source: add under `ingest/sources/`, update dispatcher registry, test normal + empty/failure fallback.
Analysis step: new module returning `StepResult`; integrate into pipeline orchestrator.
New tool: implement under `tools/`, return `StepResult`, register in `crew.py`.

### 14. Do / Avoid
Do: thread tenant context; return `StepResult`; gate new behavior behind flags; reuse HTTP + cache helpers; keep deterministic IDs; respect mypy snapshot (update only after reductions).
Avoid: raw `requests`, bespoke retry loops, leaking user text into metrics, raising on expected empties, ad‑hoc vector schema, heavy imports in hot paths.

### 15. Debug / Utilities
Quick ingest: `python -m ingest <url> --tenant default --workspace main` (`ENABLE_INGEST_CONCURRENT=1` for parallel fetch).
Discord bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`.
Crew run: `python -m ultimate_discord_intelligence_bot.setup_cli run crew`.
Health: `make doctor`; Queue snapshot: `make ops-queue DB=path/to/sched.db`.
Search patterns: `rg <keyword>`; prefer adapting closest existing module.
Keep PRs scoped; document flag interactions in commit message.

When unsure: replicate the nearest proven seam instead of inventing a new abstraction.

### 16. Gotchas & Migration Patterns
Flags not set: Most silent skips are due to missing `ENABLE_*`; confirm env (see examples in `docs/feature_flags.md`).
Deprecated LearningEngine path: Prefer `core.learning_engine.LearningEngine` (replacement referenced in root `README.md` deprecations table).
StepResult migration: Legacy dicts with `status` → convert via `src/ultimate_discord_intelligence_bot/tools/batch_stepresult_migration.py` (`make compliance-fix`).
Retry precedence: Tenant `retry.yaml` (e.g. `tenants/<tenant>/retry.yaml`) overrides global `config/retry.yaml`; explicit function arg overrides both—maintain this order.
Mypy regression: Guard with `make type-guard` before updating snapshot (`reports/mypy_snapshot.json`).
Vector namespace drift: Compose `f"{tenant}:{workspace}"`; review usages in `memory/api.py`.
Grounding citations: Ensure monotonic `[n]` in grounding output; see patterns in `grounding/` modules.
