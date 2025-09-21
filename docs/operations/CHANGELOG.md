---
title: Changelog
origin: CHANGELOG.md (root)
status: migrated
last_moved: 2025-09-02
---

All notable changes will be documented in this file. Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## Unreleased

_No unreleased changes yet._

## 0.1.1 — 2025-09-21

### Added (Unreleased historical)

* Optional FastMCP servers suite: memory, router, obs, kg, ingest, http, and a2a; all mounted via feature flags.
* Crew in-process bridge tool `MCPCallTool` (enable via `ENABLE_MCP_CALL_TOOL=1`) exposing a curated allowlist of MCP tools without transport.
* Tests for MCP server behavior (safe, stubbed) and a smoke test for `MCPCallTool`.
* Documentation: `docs/mcp.md` (servers, flags, usage), flags section in `docs/configuration.md`, assistant config in `docs/dev_assistants.md`, README MCP quickstart and CI badge, and index link.
* CI: dedicated workflow `.github/workflows/ci-mcp.yml` running lint, fast tests, and MCP tests with dev+mcp extras; added pip caching.

### Changed (Unreleased historical)

* Makefile `test-mcp` now skips gracefully when `fastmcp` is not installed (exit 0 with message).

### Added

* Public helper `is_retry_enabled()` in `core.http_utils` exposing consolidated HTTP retry flag state.
* Integrate `http_request_with_retry` into `OpenRouterService` (feature-flagged).
* Integrate retry helper into `FactCheckTool` backend GET calls (feature-flagged).
* Added integration tests for OpenRouterService retry success + give-up scenarios.
* In-memory Qdrant fallback (`_DummyClient`) auto-enabled when `QDRANT_URL` is unset, empty, `:memory:` or `memory://*`—removes external dependency for unit tests.
* README section documenting in-memory Qdrant fallback and tool contract changes.
* UTC normalization audit: replaced remaining naive timestamp usage (`datetime.utcnow()` / naive `datetime.now()`) with `datetime.now(timezone.utc)`.
* `core.time.ensure_utc` helper for safe normalization of parsed datetimes.
* Test `test_tenancy_timezone.py` verifying tenant `created_at` normalization to UTC.
* Test `test_memory_dummy_qdrant.py` ensuring in-memory Qdrant fallback triggers for blank / `:memory:` URLs.
* README "Typing & Timezone Practices" section with audit commands & guidelines.
* Pull request template enforcing typing, UTC, and flag hygiene checklist.
* Light tracing instrumentation added to `resilient_post` / `resilient_get` (no-op without tracing provider).
* Centralized HTTP helpers (`core.http_utils`) providing resilient_get/post plus feature-flagged exponential backoff retry wrappers.
* In-process rate limiting middleware (feature flag: `ENABLE_RATE_LIMITING`) using token bucket; exposed Prometheus counter `rate_limit_rejections_total`.
* Server HTTP metrics: histogram `http_request_latency_ms` and counter `http_requests_total` with route/method/status labels.
* Retry metrics: `http_retry_attempts_total` (excluding first attempt) and `http_retry_giveups_total` when retry feature flag set.
* Expanded test coverage: rate limit rejection metrics, HTTP utils retry/backoff paths, streaming GET handling, vector store dimension validation.
* Feature flags reference documentation (`docs/feature_flags.md`).
* Distributed rate limiting design stub (`docs/distributed_rate_limiting.md`).
* Future work backlog (`FUTURE_WORK.md`).
* Retry flag precedence & Prometheus exposition tests.
* Automated feature flag documentation drift validator (`scripts/validate_feature_flags.py`) with CI test (`test_feature_flag_sync.py`).
* Extended `docs/feature_flags.md` with automation & drift prevention section.
* Deprecated flag usage validator (`scripts/validate_deprecated_flags.py`) + enforcement test (`test_deprecated_flag_usage.py`).
* Central citation formatting helper (`grounding.citation_utils.append_numeric_citations`) enforcing ordered numeric `[n]` tail.
* Governance test `test_citation_utils.py` ensuring citation tail idempotence & formatting invariants.
* Deprecation schedule config (`config/deprecations.yaml`) + validator (`scripts/validate_deprecation_schedule.py`) and test (`test_deprecation_schedule.py`).
* `DEPRECATION_AS_OF` date override for schedule validator to simulate future enforcement.
* Grounding citation integration test (`test_grounding_citation_integration.py`) ensuring `build_contract` applies numeric citation tail.
* Privacy feature flag matrix tests (`test_privacy_flags.py`) covering detection vs redaction enablement, and RL `strict` arm override forcing both behaviors.
* AI assistant guidance deep dives (Sections 13–16: RL routing, scheduler/profiles, observability example, cheat sheet) in `.github/copilot-instructions.md`.
* New condensed quick reference file `.github/copilot-quickref.md` (snippets, troubleshooting ladder, anti-patterns, commands).
* README links to full instructions and quick reference.
* Environment flags: `CREW_DISABLE_DOTENV` (skip .env load), `CREW_ENABLE_SECURE_QDRANT_FALLBACK` (opt-in secure-config Qdrant URL/API key resolution), `CREW_QDRANT_SECURE_TEST_URL` (test seam for deterministic fallback), and single-load `.env` sentinel logic in `settings`.

### Changed

* Refactored `FactCheckTool` and `OpenRouterService` to use `is_retry_enabled()` instead of direct environment variable checks for `ENABLE_HTTP_RETRY` / legacy `ENABLE_HTTP_RETRY` (no behavior change intended).
* Consolidated HTTP retry flag logic: `ENABLE_HTTP_RETRY` now preferred over legacy `ENABLE_HTTP_RETRY` (which still works but emits `DeprecationWarning`).
* Reduced mypy errors from 42 to 0; strengthened `TypedDict`s; removed obsolete type ignores.
* `VectorSearchTool.run()` returns flat `list[dict]` (replacing `{status, hits}` wrapper).
* `DiscordQATool` updated to consume simplified vector search output.
* `PerspectiveSynthesizerTool` varargs `_run` with deterministic uppercase summary for stable tests.
* `MemoryStorageTool` initialization refactored to avoid pydantic required-field validation with injected mock clients.
* Consolidated duplicate RL implementations: `services.learning_engine.LearningEngine` now a thin shim over `core.learning_engine.LearningEngine` (SQLite + JSON persistence removed; use snapshot/restore externally if needed).
* Internal services now import `core.learning_engine.LearningEngine` directly; `services.learning_engine` retained only as a deprecated compatibility shim.
* Mypy Phase 2: enabled `warn_unused_ignores`, `no_implicit_optional`, `strict_equality`; removed stale ignores; hardened `MemoryStorageTool` optional handling and legacy learning shim types (baseline remains clean).
* Removed duplicated condensed instructions block from `.github/copilot-instructions.md` in favor of dedicated quick reference file.

### Deprecated

* `ENABLE_HTTP_RETRY` (use `ENABLE_HTTP_RETRY` going forward). Removal planned after a transition period once all external references migrate.
* Legacy vector search wrapper structure expecting `result['hits']`.
* `services.learning_engine.LearningEngine` (import `core.learning_engine.LearningEngine` directly; shim will be removed after deprecation window).

### Fixed

* Resolved test failures in multi‑platform download tests caused by legacy monkeypatch signatures missing `params`/`timeout` by enhancing fallback.
* Stale settings cache causing rate limit tests to ignore updated env vars (now instantiate fresh `Settings()` in app factory and lifespan).
* Ensured `/metrics` endpoint bypasses rate limiting to preserve observability under load.
* Graceful degradation when `prometheus_client` absent (no-op metrics) with tests adapting accordingly.
* Multiple unit tests previously failing due to Qdrant URL parse errors now pass via in-memory fallback.
* Eliminated pydantic `ValidationError` in `MemoryStorageTool` during tests with mock client.

### Removed

* Redundant ad hoc timeout handling in refactored tools.

### Notes

* Pydantic settings migration completed (deprecated `env=` usages replaced with `validation_alias` / `alias`).
* Future enhancements may introduce standardized retry/backoff or tracing integration inside `http_utils` once patterns further stabilize.
* Consider optional flag to disable uppercase transformation in `PerspectiveSynthesizerTool` if user-facing casing matters.
