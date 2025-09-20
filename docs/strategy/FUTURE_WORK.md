---
title: Future Work Backlog
origin: FUTURE_WORK.md (root)
status: migrated
last_moved: 2025-09-02
---

<!-- Original file relocated from repository root during documentation restructure. -->

## Future Work & Deferred Enhancements

This file tracks intentional deferrals identified during the observability, resilience, and configuration polish cycle. Each item lists rationale, proposed approach, and rough priority (H/M/L).

### 1. Consolidate Retry Flags (H)

Current dual flags: `ENABLE_HTTP_RETRY` (legacy) and `ENABLE_HTTP_RETRY` (new unified). Some tools (fact check, OpenRouter) still look at the legacy flag. Migrate all callers to settings attribute `enable_http_retry`, deprecate legacy env lookups, update docs, then remove legacy references after a grace period.

### 2. Distributed Rate Limiting (H)

Implement Redis-backed token bucket (see `docs/distributed_rate_limiting.md`). Phased rollout with shadow comparison, metrics (`rate_limit_backend_errors_total`, divergence counter), and new enabling flag `ENABLE_DISTRIBUTED_RATE_LIMITING`.

### 3. Auto-Generated Feature Flags Doc (M)

Generate `docs/feature_flags.md` via script scanning for `ENABLE_` patterns + mapping to tests (e.g., extend `scripts/validate_docs.py`). Reduces drift and enforces documentation completeness.

### 4. Metrics Test Hardening (M)

Add explicit scrape text assertions for retry metrics (`http_retry_attempts_total`, `http_retry_giveups_total`) when metrics + retry flags enabled to ensure exposition formatting stability.

### 5. Observability Dashboard Templates (M)

Provide example Grafana (or Prometheus alert rules) snippets for rate limit saturation, high retry give‑ups, and latency SLO burn rate detection. Commit under `docs/observability_dashboards/`.

### 6. Adaptive Rate Limiting (L)

Explore dynamic refill adjustments based on moving average of rejection ratios (could integrate with RL engine for cost optimization). Requires new metrics for decision justification.

### 7. Privacy Filter Coverage Tests (M)

Add focused tests asserting behavior when `enable_pii_detection` / `enable_pii_redaction` flags toggled independently (currently only indirectly covered).

### 8. HTTP Client Telemetry Enrichment (L)

Add span attributes: `http.retry_attempt`, `http.retry_backoff_ms`, sanitized URL host. Emit structured logs at final give‑up with correlation IDs.

### 9. Circuit Breaker for Flaky Upstreams (M)

Layer a simple half‑open circuit around specific external APIs (e.g., search providers) to cut cost blast radius when persistent failures detected.

### 10. Request Timeout Configuration (L)

Expose `REQUEST_TIMEOUT_SECONDS` as a settings value (env override) with per‑category defaults (short for metadata endpoints, longer for content upload/download).

### 11. Replace Sleep-Based Retry Decorators (L)

`fact_check_tool` local decorator uses blocking `time.sleep`; refactor to async-capable strategy or integrate with shared retry helper uniformly.

### 12. Structured Error Taxonomy (M)

Expand `StepResult` / error handling to ensure consistent `status` classification (`bad_request`, `retryable`, `partial`) across tools; add tests asserting mapping.

### 13. Security Hardening: URL Validation Everywhere (M)

Audit all external URL entry points to ensure usage of `validate_public_https_url`; add tests rejecting private / file / local network addresses.

### 14. Performance Benchmarks Automation (L)

Add minimal benchmark harness measuring retry overhead and rate limit hot path micro‑latency to catch regressions.

### 15. Settings Schema Documentation Sync (M)

Generate documentation for each `Settings` field (description, env, default) into `docs/configuration.md` to avoid stale manual edits.

### 16. Codebase Lint Hygiene Pass (M)

Resolve accumulated Ruff violations (notably E402 import ordering, F841 unused vars in tests, E741 ambiguous loop vars, E501 long lines) in a staged approach to minimize noisy diffs:

1. Imports: reorder to eliminate E402 without altering semantics (module docstrings preserved).
2. Tests: remove unused variables or prefix with underscore where semantically helpful.
3. Rename ambiguous single-letter loop vars (`l`, `O`, `I`) to descriptive names.
4. Long lines: wrap metrics constant groupings & server bucket construction; prefer parentheses over backslashes.
Add a temporary CI job running `ruff check --select E,F --diff` to prevent regression once baseline clean.

### 17. Mypy Debt Reduction Roadmap (H → M)

Current snapshot ~140 errors across 49 files. Phased plan:
Phase 1 (H): Eliminate unused/incorrect `# type: ignore` (quick wins, improves signal). Add `warn_unused_ignores = True` enforcement project-wide after cleanup.
Phase 2 (H): Provide minimal stub packages or `types-` dependencies for external libs (`nltk`, `yt_dlp`, `jsonschema`, `prometheus_client`).
Phase 3 (M): Annotate public function boundaries in `ingest`, `memory`, `grounding` modules (inputs/outputs) to reduce Any leakage.
Phase 4 (M): Introduce Protocols / TypedDicts for frequently passed dict payloads (e.g., StepResult-like data) and enable `disallow_any_generics`.
Phase 5 (L): Tighten config with `disallow_untyped_defs = True` for new/modified files via per-file overrides; gradually expand.
Track progress metric: mypy error count trend in CI (simple badge or log summary).

### 18. Remove Deprecated Logical Fallacy Stub (M)

Delete `logical_fallacy_tool_backup.py` once two consecutive releases occur with zero import attempts (instrumented via grep in CI + optional runtime guard). Update any docs referencing prior duplication.

### 19. Developer Tooling / Pre-Commit Enhancements (M)

Add optional `.pre-commit-config.yaml` with hooks:

* Ruff (lint + format if adopting `ruff format`).
* Mypy (changed files only via `--cache-fine-grained`).
* Pyproject toml sort (ensure deterministic dependency/order formatting).
Provide `scripts/dev.sh` convenience wrapper (already added) – extend to offer `./scripts/dev.sh lint|type|test` subcommands. Document in README contributing section.

### 20. Incremental Type Enforcement Guard (M)

Add a CI script that fails if mypy error count increases relative to a stored baseline JSON (updated only when errors decrease). Prevents regression while allowing staged improvements.

---
Legend: Priority H (High) – next cycle; M (Medium) – upcoming; L (Low) – opportunistic.

Maintained as a living backlog; prune items once delivered or superseded.
