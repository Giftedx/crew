## Changelog

All notable changes will be documented in this file. Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

### Unreleased
#### Changed
- Consolidated HTTP retry flag logic: `ENABLE_HTTP_RETRY` now preferred over legacy `ENABLE_ANALYSIS_HTTP_RETRY` (which still works but emits `DeprecationWarning`).
- Updated `openrouter_service` & `fact_check_tool` to honor unified flag precedence.

#### Deprecated
- `ENABLE_ANALYSIS_HTTP_RETRY` (use `ENABLE_HTTP_RETRY` going forward). Removal planned after a transition period once all external references migrate.

#### Added
- Integrate http_request_with_retry into OpenRouterService (feature-flagged)
- Integrate retry helper into FactCheckTool backend GET calls (feature-flagged)
- Added integration tests for OpenRouterService retry success + give-up scenarios

- Added light tracing instrumentation to `resilient_post` / `resilient_get` (no-op without tracing provider).
- Centralized HTTP helpers (`core.http_utils`) providing resilient_get/post plus feature-flagged exponential backoff retry wrappers.
- In-process rate limiting middleware (feature flag: `ENABLE_RATE_LIMITING`) using token bucket; exposed Prometheus counter `rate_limit_rejections_total`.
- Server HTTP metrics: histogram `http_request_latency_ms` and counter `http_requests_total` with route/method/status labels.
- Retry metrics: `http_retry_attempts_total` (excluding first attempt) and `http_retry_giveups_total` when retry feature flag set.
- Expanded test coverage: rate limit rejection metrics, HTTP utils retry/backoff paths, streaming GET handling, vector store dimension validation.
- Feature flags reference documentation (`docs/feature_flags.md`).
- Distributed rate limiting design stub (`docs/distributed_rate_limiting.md`).
- Future work backlog (`FUTURE_WORK.md`).
- Retry flag precedence & Prometheus exposition tests.

#### Fixed
- Resolved test failures in multi‑platform download tests caused by legacy monkeypatch signatures missing `params`/`timeout` by enhancing fallback.
- Stale settings cache causing rate limit tests to ignore updated env vars (now instantiate fresh `Settings()` in app factory and lifespan).
- Ensured `/metrics` endpoint bypasses rate limiting to preserve observability under load.
- Graceful degradation when `prometheus_client` absent (no-op metrics) with tests adapting accordingly.

#### Removed
- Redundant ad hoc timeout handling in refactored tools.

#### Notes
- Pydantic settings migration completed (deprecated `env=` usages replaced with `validation_alias` / `alias`).
- Future enhancements may introduce standardized retry/backoff or tracing integration inside `http_utils` once patterns further stabilize.
