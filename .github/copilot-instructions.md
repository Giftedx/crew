## 🤖 Copilot Instructions (Project-Specific, ~45 lines)
Goal: Accelerate correct edits. Reuse existing seams; never invent parallel abstractions unless requested.

### 1. Mental Model
Ingestion (multi‑platform dispatcher) → transcription (Whisper / faster‑whisper fallback) → light analysis (sentiment / claims / topics / fallacies) → memory (Qdrant or in‑mem) → grounding & routing → Discord / API response. Orchestration lives in `src/ultimate_discord_intelligence_bot/crew.py` with agent/task YAML under `config/`.

### 2. Directory Landmarks
`core/` flags, HTTP wrappers (`resilient_*`, `retrying_*`), routing + RL helpers.
`analysis/` pipelines (segment, sentiment, claims, topics).
`ingest/` source adapters + dispatcher (`ingest/sources/<platform>.py`).
`memory/` vector + metadata stores (namespaced by `tenant:workspace`).
`obs/` tracing + metrics init (init once per entrypoint).
`scheduler/` job dataclasses + handlers; deterministic keys dedupe.
`grounding/`, `debate/`, `kg/`, `eval/` higher‑order reasoning & evaluation.
`policy/`, `security/` moderation, rate limits, governance.

### 3. StepResult Contract
All external/system operations return `StepResult.ok|fail|skip`. Recoverable issues (404, empty transcript) → `fail` or `skip`, not raised. Legacy dict tools: wrap with `StepResult.from_dict`. Vector search returns raw list of `{text, score}` (no wrapper). Unexpected exceptions: allow raise after metrics/logging.

### 4. Tenancy
Always thread `TenantContext` (helpers: `with_tenant`). Do not leak raw user text into metric labels or namespace strings. New stateful components MUST accept `(tenant, workspace)` or a composed namespace param early.

### 5. Feature Flags & Deprecations
Pattern: `ENABLE_<AREA>_<FEATURE>` (default off). Key examples: `ENABLE_HTTP_RETRY`, `ENABLE_INGEST_CONCURRENT`, `ENABLE_RL_GLOBAL`, domain‑specific RL flags (`ENABLE_RL_ROUTING`). Emit `DeprecationWarning` + run `make docs` after modifying deprecated surfaces. Strict ingest mode: `ENABLE_INGEST_STRICT=1` (fails on missing creator/id). Privacy flags accept flexible casing (`enable_pii_detection`).

### 6. Routing & RL
`PromptEngine.build` → filter candidates → ε‑greedy via `LearningEngine` (needs global + domain flag) → `OpenRouterService.call` (cost metered by `TokenMeter`) → `record(model, reward, cached=?, error_type=?)`. Failure reward = 0; negative only for policy violations.

### 7. Scheduler
Add job: dataclass under `scheduler/jobs/`, handler under `scheduler/handlers/`, update registry mapping. Key: deterministic job key (URL + bucket) prevents duplicates. Backpressure: drop lowest priority (preserve existing metric naming).

### 8. Determinism & Time
UTC only: use `core.time.ensure_utc`. Keep summarizer / analysis deterministic (uppercase normalization, stable hashing of URLs for episode IDs). Guard heavy / experimental code paths with flags.

### 9. HTTP & Caching
Never call `requests.*` directly—use wrappers in `core/http_utils.py`. For GET with caching use `cached_get` (auto Redis vs in‑mem). Add retry config by placing `retry.yaml` (tenant or global) with `max_attempts:` (simple parser, no extra lib).

### 10. Observability
One span per logical unit; increment metrics BEFORE returning a `StepResult`. New metrics: declare centrally (avoid dynamic label explosion). Labels: tenant, workspace, low‑cardinality enums only—never raw text/URLs. Deprecation flags log once (see pattern in `core.http_utils`).

### 11. Memory Layer
Use API in `memory/api.py` plus `store` + `vector_store`. Respect retention policies; pruning via `api.prune`. Qdrant absent → in‑mem fallback (ok for tests; avoid perf benchmarking). Archive/pin via archiver facade.

### 12. Testing & CI Routines
Env/bootstrap: `make ensure-venv` or `pip install -e '.[dev]'`.
Quality sweep: `make format lint type`. Focused fast tests: `make test-fast` (targets HTTP + guards + vector store). Full tests: `make test`. Eval harness: `make eval`. Docs + deprecation scan: `make docs`. Compliance (HTTP + StepResult): `make compliance` / auto-fix: `make compliance-fix`.

### 13. Adding Functionality
Ingestion source: new file under `ingest/sources/` + dispatcher update + tests for fallback paths. New analysis step: module under `analysis/` returning `StepResult`; wire into orchestrator. New tool for crew: create under `tools/`, ensure it returns `StepResult`, register in `crew.py`.

### 14. Do / Avoid
Do: thread tenant context, return `StepResult`, gate new behavior, reuse retry + cache helpers, maintain mypy baseline (`config/mypy_baseline.json`), deterministic identifiers.
Avoid: direct `requests`, ad‑hoc retries, leaking raw user inputs into metrics, raising for expected empty results, creating bespoke vector schemas, heavy imports in hot paths.

### 15. Debug / Utilities
Quick ingest: `python -m ingest <url> --tenant default --workspace main` (optionally `ENABLE_INGEST_CONCURRENT=1`). Run Discord bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`. Doctor checks: `make doctor`. Queue snapshot: `make ops-queue DB=path/to/sched.db`.

When unsure: search (`rg <keyword>`), mirror nearest existing pattern, keep PR scope small, document involved flags in code comments + commit message.
