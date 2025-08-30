### GitHub Copilot / AI Agent Instructions

Goal: Precise, safe edits to a multi‑tenant Discord ingestion + grounding + RL routing platform. Keep work tenant‑scoped, config‑driven, observable, and cheap.

Architecture & Layout: Domain packages under `src/` (`ingest/`, `analysis/`, `grounding/`, `memory/`, `policy/`, `security/`, `scheduler/`, `archive/`, `debate/`, `obs/`). Shared infra/services/agents/tools in `src/ultimate_discord_intelligence_bot/`. Core async pipeline: URL -> `multi_platform_download_tool` -> typed downloader (yt‑dlp, optional `quality`) -> `audio_transcription_tool` -> analysis (sentiment/claims/fallacies) -> grounding (citations) -> Discord post / alerts. Each stage returns `StepResult`.

Tenancy: Always pass `(tenant, workspace)` or wrap with `with_tenant(TenantContext(...))`. Vector namespaces via `VectorStore.namespace(t, w, source)`. Never mix tenants in memory, cache, traces, or metrics labels.

Tools & Agents: New tool? ONLY if: (a) external system not covered, (b) materially different side‑effects, or (c) interface change would bloat existing class. Else extend. Place in `.../tools/`, add to `crew.py`, declare in `config/agents.yaml` + `config/tasks.yaml`, then `pytest -k agent_config_audit`.

Memory & RAG: Use `MemoryService` (Qdrant or in‑memory fallback). Reject blank queries, non‑positive limits. Grounded answers MUST append ordered numeric citations: `...[1][2]`. Use provided citation helper pattern (see tests) not ad‑hoc formats.

Model Routing & Cost: Only via `PromptEngine` + `OpenRouterService` + `TokenMeter` + `LLMCache`. Enforce `COST_MAX_PER_REQUEST` (else `StepResult(status="bad_request", error="cost_budget")`). After deterministic scoring: `LearningEngine.record(model=model, reward=score)`.

Feature Flags: Guard all new areas with `ENABLE_<AREA>_<FEATURE>`. If disabled, return `StepResult(status="skipped")` early. Mirror patterns in `README.md` and `docs/configuration.md`.

Profiles & Collaboration: Resolve creator/show/staff via `profiles.yaml` helpers before persisting. Use existing store methods for cross‑profile links; do not introduce parallel schemas.

Privacy / Policy / Security: Run content through policy + security filters before storage/posting. Reuse redaction utilities; do NOT invent new PII regexes. Respect rate limiting helpers.

Observability: Use `obs.tracing` context + `metrics` helpers; never `print`. If adding metric types, extend enums sparingly to control cardinality.

Error Handling: Recoverable issues return `StepResult(error=..., status="bad_request"|"retryable"|"partial")`. Raise only for programmer errors, then add/adjust a test. Missing citations or tenant context should surface explicit errors.

Config First: New knobs go in `config/*.yaml` + docs. Avoid magic numbers; reference constants or config values. Update docs & run `make docs` when adding keys.

Testing & Quality: Core: `pytest`. Golden eval: `python -m eval.runner datasets/golden/core/v1 baselines/golden/core/v1/summary.json`. Plugin testkit: `python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin <plugin>`. Keep tests deterministic (inject time/random providers). Use in‑memory Qdrant fallback (unset or `:memory:` `QDRANT_URL`) for unit tests only.

Performance & Determinism: Use controlled concurrency (e.g. parallel Drive upload + transcription) without changing downstream order. Always timezone‑aware UTC helpers; avoid `utcnow()`. Keep ordering/case stable for asserted values.

Anti‑Patterns: Raw model calls, unguarded subsystems (no feature flag), tenancy leakage, duplicated download logic, silent exception swallowing, global mutable singletons, ad‑hoc prints, broad `Any` types, missing citations, naive UTC handling (`utcnow()`), adding new schema/dir without justification.

Commit & PR Style: Conventional Commits; focused diffs (logic vs typing vs docs). Do not rewrite history. Update progress / docs when adding features.

Quick Snippets:
```python
class MyTool:  # src/ultimate_discord_intelligence_bot/tools/my_tool.py
    name = "my_tool"
    def run(self, url: str) -> StepResult:
        if not url.startswith("https://"):
            return StepResult(error="invalid_url", status="bad_request")
        # ... logic ...
        return StepResult(data={"ok": True})
```
Flag guard: `if not os.getenv("ENABLE_ANALYSIS_MY_FEATURE"): return StepResult(status="skipped")`
Citation append: `answer + " " + "".join(f"[{i+1}]" for i,_ in enumerate(docs))`
RL reward (after deterministic score):
```python
score = score_answer(prediction, ref)  # pure function -> float
LearningEngine.record(model=chosen_model, reward=score)
```
Timezone / typing audit (spot issues): `grep -R "utcnow(" -n src || true`; add precise types instead of widening to `Any`.

Troubleshooting Ladder: (1) Feature flag off? (2) Tenant context missing/mismatch? (3) Empty vector namespace? (4) Missing `[n]` citations? (5) Agent/task config sync failing? (6) Cost over budget? (7) Cache key canonical? (8) Policy filter rejecting content?

Extended references: `README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `docs/agent_reference.md`, plus subsystem docs in `docs/*.md`. Only add new patterns here once enforced by tests or multiple usages.