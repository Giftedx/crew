## 🤖 Copilot Instructions (Project-Specific, ~50 lines)
Goal: Enable fast, correct edits. Reuse existing abstractions; do not invent new layers unless explicitly requested.

### 1. Architecture (mental model)
Ingestion (multi‑platform download dispatcher) → optional Drive upload → Whisper transcription → light analysis (sentiment / fallacy / claims / perspectives) → memory (Qdrant or in‑mem) → grounded answer / Discord output. Crew/agent orchestration: `src/ultimate_discord_intelligence_bot/crew.py` (+ any `config/agents|tasks*.yaml`). Pipeline tools live under `.../tools/` and return `StepResult`.

### 2. Core Directories (where things live)
`core/` flags, http retry, learning & routing helpers
`memory/` vector + namespace isolation (`tenant:workspace`)
`obs/` tracing + metrics; init once per entrypoint
`scheduler/` job types & handlers (deterministic job key)
`security/`, `policy/` moderation + governance
`analysis/`, `grounding/`, `debate/`, `kg/`, `eval/` advanced reasoning subsystems

### 3. Tool & Result Pattern
Every external/system step should yield `StepResult.ok|fail|skip`; avoid raising for recoverable issues (bad URL, empty index). Legacy dict → wrap via `StepResult.from_dict`. Consistent shapes: vector search = list of `{text, score}` (no wrapper); monitoring tools often `StepResult.ok(matches=[...])`. Treat unknown / unexpected exceptions as real failures (let them raise after metrics increment).

### 4. Tenancy & Isolation
Always carry explicit `TenantContext` (`with_tenant`). Never mix tenant data; memory namespaces and metrics labels must exclude raw user text/high cardinality. New stateful code: add namespace parameter up‑front.

### 5. Feature Flags & Deprecations
Gate new behavior with `ENABLE_<AREA>_<FEATURE>` (default off). Prefer `ENABLE_HTTP_RETRY` (legacy `ENABLE_ANALYSIS_HTTP_RETRY` warns until 2025-12-31). Privacy filters use flexible casing (`enable_pii_detection` also accepted). On deprecation: emit `DeprecationWarning`, update README table, run `make docs` (regen badge & report).

### 6. Routing & RL (minimal rules)
`PromptEngine.build` → candidate filter (cost, capability) → ε‑greedy choose via `LearningEngine` (requires both `ENABLE_RL_GLOBAL` and domain flag e.g. `ENABLE_RL_ROUTING`) → `OpenRouterService.call` (budget via `TokenMeter`) → reward 0–1 recorded (`record(model, reward, cached=bool, error_type=? )`). Failures = 0; cached still logged; negative only for policy violations (increment moderation metrics).

### 7. Scheduler & Profiles
Jobs: add dataclass under `scheduler/jobs/` + handler under `scheduler/handlers/` + registry mapping update (search existing handler map). Job key must be deterministic (typically URL + bucket) to dedupe. Intended backpressure: drop lowest priority when max queue exceeded (preserve metric naming consistency if adding). `profiles.yaml` seeds creators; resolution utilities enrich ingestion payloads.

### 8. Conventions / Determinism
UTC only (`datetime.now(timezone.utc)`); normalise naive via `core.time.ensure_utc`. Deterministic seams: uppercase summariser outputs, injectable time providers. Guard heavy / slow paths with flags. Maintain `mypy_baseline.json` (never regress). Always use `core.http_utils` wrappers (`resilient_*` / `retrying_*`) not direct `requests.*`.

### 9. Observability
One span per logical operation; increment metrics before returning. New counters/ histograms: define in central metrics module (avoid hot‑loop creation). Label sets: tenant/workspace + low‑cardinality fields (never raw text, IDs, or URLs). Emit deprecation structured log once per flag (see `core.http_utils`).

### 10. Where to Add
Ingestion: `ingest/sources/<platform>.py` + dispatcher update. Analysis: extend `analysis/` or focused tool under `tools/`. Crew tool: add under `tools/` + register in `crew.py`. Scheduler job: dataclass + handler + registry mapping + tests (dedupe, ordering). HTTP retry config override: add `retry.yaml` (tenant or global) with `max_attempts:` (no YAML lib required; simple parse).

### 11. Testing & Workflows
Install: `pip install -e '.[dev]'` or `make ensure-venv`. Quality: `make format lint type`. Tests: `pytest -q` or `make test-fast` (focused subset). Eval: `make eval`. Deprecations/status/docs: `make docs`. Guards (fail fast): `make guards` (enforces dispatcher + HTTP wrapper usage). Run bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`.

### 12. Data & Storage Nuances
Qdrant memory fallback: when `QDRANT_URL` unset, `:memory:` or `memory://*` or client missing → in‑memory stub (sufficient for unit tests; avoid benchmarking on it). Privacy filter: detection & redaction individually flag‑controlled (see `core/privacy/privacy_filter.py`). Cached GET: `cached_get` auto‑selects Redis vs in‑mem.

### 13. Do / Avoid
Do: thread tenant, use `StepResult`, gate features, reuse retry + cache helpers, maintain deterministic outputs, surface structured deprecation logs. Avoid: ad‑hoc HTTP retries, direct `requests.*`, global implicit tenant, naive time, bespoke vector schemas, heavy imports in hot paths, raising for expected miss/empty conditions.

When unsure: search (`rg <keyword>`), mirror closest pattern, keep scope minimal, document flags. For deep dives see `README.md` + `docs/*.md`.