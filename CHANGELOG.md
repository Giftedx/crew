## Changelog

All notable changes will be documented in this file. Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

### Unreleased
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

#### Fixed
- Resolved test failures in multi‑platform download tests caused by legacy monkeypatch signatures missing `params`/`timeout` by enhancing fallback.
- Stale settings cache causing rate limit tests to ignore updated env vars (now instantiate fresh `Settings()` in app factory and lifespan).
- Ensured `/metrics` endpoint bypasses rate limiting to preserve observability under load.
- Graceful degradation when `prometheus_client` absent (no-op metrics) with tests adapting accordingly.

#### Removed
- Redundant ad hoc timeout handling in refactored tools.

#### Notes
- Future enhancements may introduce standardized retry/backoff or tracing integration inside `http_utils` once patterns stabilize.
- Pydantic deprecation warnings (use of `env=` on Field) intentionally deferred; planned alias migration tracked as optional.
