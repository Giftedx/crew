## Feature Flags & Environment Toggles

This document centralizes every `ENABLE_*` (and related) feature flag discovered in the codebase. Flags allow selective activation of subsystems, experiments, and cost / privacy guards. Unless otherwise noted, a flag is treated as **disabled** when unset or set to `"0"`, and **enabled** for any other non-empty value (typically `"1"`).

### Conventions

- Boolean flags: Read via `os.getenv("FLAG_NAME")` or the `Settings` model (`core/settings.py`).
- Settings model flags (preferred going forward) expose a snake_case attribute (e.g. `enable_http_metrics`) mapped to the env var (e.g. `ENABLE_HTTP_METRICS`).
- Legacy / direct checks (e.g. `ENABLE_ANALYSIS_HTTP_RETRY`) will be migrated over time to the unified settings flag (`ENABLE_HTTP_RETRY`).
- RL (reinforcement learning / routing) flags use scoped names: `ENABLE_RL_GLOBAL` + a domain‑specific flag must both be truthy.

### Core Runtime / API

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `ENABLE_API` | off | Enable FastAPI server instantiation (app factory builds routes & middleware). | `server/app.py`, `core/settings.py` | `test_rate_limit_middleware.py` |
| `ENABLE_PROMETHEUS_ENDPOINT` | off | Expose `/metrics` endpoint (bypasses rate limiting) serving Prometheus exposition if `prometheus_client` installed. | `server/app.py`, `obs/metrics.py` | `test_http_metrics.py`, `test_rate_limit_metrics.py` |
| `ENABLE_HTTP_METRICS` | off | Instrument inbound HTTP request latency & counts and rejection metrics. | `server/app.py`, `obs/metrics.py` | `test_http_metrics.py`, `test_rate_limit_metrics.py` |
| `ENABLE_RATE_LIMITING` | off | Activate in‑process token bucket (per client IP) middleware. | `server/app.py` | `test_rate_limit_middleware.py`, `test_rate_limit_metrics.py` |
| `ENABLE_TRACING` | off | Activate OpenTelemetry tracing spans (no‑op if OTel libs absent). | `server/app.py`, `core/http_utils.py` | (implicit; spans not asserted) |

### HTTP Resilience / Outbound

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `ENABLE_HTTP_RETRY` | off | Unified flag (preferred) for enabling exponential backoff & jitter retries in resilient HTTP helpers. | `core/settings.py`, `core/http_utils.py` | `test_http_utils_retry.py`, `test_http_retry_metrics.py` |
| `ENABLE_ANALYSIS_HTTP_RETRY` | off | Legacy precursor for retry logic; still referenced by some tools (fact check, OpenRouter). Honored but deprecated; superseded by `ENABLE_HTTP_RETRY` which takes precedence if both set. | `core/http_utils.py`, `ultimate_discord_intelligence_bot/tools/*` | `test_http_utils_wrappers.py`, `test_openrouter_retry_integration.py`, `test_fact_check_retry_integration.py` |

Retry metrics (`http_retry_attempts_total`, `http_retry_giveups_total`) are only emitted when retry flag(s) active and the Prometheus metrics layer is enabled.

### Reinforcement Learning / Routing

RL behaviors require the global flag plus a domain flag.

| Flag Pattern | Example | Purpose | Key Modules | Related Tests |
|--------------|---------|---------|-------------|---------------|
| `ENABLE_RL_GLOBAL` + `ENABLE_RL_<DOMAIN>` | `ENABLE_RL_GLOBAL` + `ENABLE_RL_ROUTING` | Enable epsilon‑greedy model selection & reward logging for a domain. | `core/learn.py`, `ultimate_discord_intelligence_bot/plugins/*` | `test_rl_core.py`, `test_plugin_rl.py`, `test_tool_planner.py` |

### Caching

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `ENABLE_CACHE` | on (implicit True if unset in some usages) | Enable LLM & retrieval cache layers (skips writes & reads when disabled). | `core/cache/llm_cache.py`, `core/cache/retrieval_cache.py` | `test_cost_and_cache.py` |

### Ingestion Pipeline

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `ENABLE_INGEST_CONCURRENT` | off | Run transcript metadata fetch & transcript retrieval concurrently for speedup. | `ingest/pipeline.py` | `test_ingest_concurrent.py` |

### Archiver / Discord

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `ENABLE_DISCORD_ARCHIVER` | on (`"1"` default in code) | Allow Discord archive ingestion endpoints & logic. | `archive/discord_store/api.py` | `test_discord_archiver.py` |

### Privacy / PII (Case‑Insensitive Flags via Flag Service)

These are accessed through a flag service supporting lower‑case names.

| Flag | Default | Purpose | Key Modules | Related Tests |
|------|---------|---------|-------------|---------------|
| `enable_pii_detection` | on | Enable detection (classification) phase of privacy filter. | `core/privacy/privacy_filter.py` | `test_privacy_flags.py` |
| `enable_pii_redaction` | on | Enable redaction phase (masking sensitive spans). | `core/privacy/privacy_filter.py` | `test_privacy_flags.py` |

### Observability Metrics (Defined Counters / Histograms)

Activated by combinations of flags:

- Inbound HTTP metrics: require `ENABLE_HTTP_METRICS` (and optionally `ENABLE_PROMETHEUS_ENDPOINT` to expose externally).
- Retry metrics: require retry flag(s) plus metrics flag.
- Rate limit rejection metric: requires `ENABLE_HTTP_METRICS` + `ENABLE_RATE_LIMITING`.

### Deprecations / Migration Notes

- `ENABLE_ANALYSIS_HTTP_RETRY` → superseded by `ENABLE_HTTP_RETRY` (precedence in `core/http_utils._is_retry_enabled`).
  - Phase 1 (current): Both supported; legacy emits `DeprecationWarning` if unified flag absent.
  - Phase 2 (planned): Update all tools/tests to set only `ENABLE_HTTP_RETRY`; add CI check forbidding legacy usage.
  - Phase 3 (removal): Delete legacy checks & warning path; update this document & CHANGELOG.
- Transition env sourcing to centralized `Settings` model for consistency & testability.

### Adding a New Flag

1. Define in `core/settings.py` (if general) with `Field(..., validation_alias=AliasChoices("FLAG", "snake_case"), alias="FLAG")`.
2. Gate logic in code (avoid broad module import side effects when disabled).
3. Add tests toggling the flag for both on/off behaviors.
4. Document here (purpose, modules, tests).
5. If observability changes, update `CHANGELOG.md` & `MERGE_REPORT.md`.

### Future Improvements

- Auto-generate this table from static analysis (script scanning for `ENABLE_` patterns + mapping to tests) to prevent rot.
- Remove legacy retry flag after deprecation window closes (see timeline above).
- Introduce `ENABLE_DISTRIBUTED_RATE_LIMITING` (proposed) once Redis / external store design lands.

---
Generated as part of observability & resilience polish effort.

### Automation & Drift Prevention

This document is validated in CI by `scripts/validate_feature_flags.py` and the
test `tests/test_feature_flag_sync.py`. The validator statically scans `src/`
for:

1. `ENABLE_*` occurrences (env lookups, constants, Field aliases)
2. `flags.enabled("<name>")` calls (including lower‑case privacy flags)
3. RL dynamic pattern usage (`f"ENABLE_RL_{domain.upper()}"`) – represented
   here as the placeholder pattern `ENABLE_RL_<DOMAIN>`

It then diffs the discovered set against the flags listed in this document.

Validation rules:
- Undocumented flags: cause failure (must be added here with description).
- Stale flags (documented but absent in code): cause failure unless listed in
  the deprecated allow‑list inside the script.
- Pattern placeholders (e.g. `ENABLE_RL_<DOMAIN>`) are exempt from code
  presence requirements; they document families of dynamic flags.

To run manually:

```
python scripts/validate_feature_flags.py
```

Exit code 0 indicates sync; non‑zero prints a diff of issues. Update this file
and/or code to resolve drift, then re‑run tests.

#### Deprecated Flag Enforcement

Stray usage of deprecated flags (currently `ENABLE_ANALYSIS_HTTP_RETRY`) is
guarded by `scripts/validate_deprecated_flags.py` + `test_deprecated_flag_usage.py`.
Only whitelisted legacy references (core implementation, docs, changelog, and
explicit retry tests) are allowed until full removal.

#### Deprecation Schedule Governance

Long‑lived deprecated flags are tracked in `config/deprecations.yaml` with a
planned `remove_after` (UTC, inclusive). CI invokes
`scripts/validate_deprecation_schedule.py` (see new test
`test_deprecation_schedule.py`) which:

- Lists upcoming removals (informational) before the cutoff date.
- After the cutoff, fails if the deprecated flag still appears outside an
  allow‑list (archival docs, changelog, schedule file, validator scripts).

Current schedule (subset):

| Flag | Stage | Remove After | Replacement |
|------|-------|--------------|-------------|
| `ENABLE_ANALYSIS_HTTP_RETRY` | deprecated | 2025-12-31 | `ENABLE_HTTP_RETRY` |

Add new entries when deprecating flags to make removal dates explicit and
auditable. Avoid extending removal dates without a changelog entry.

Simulation / CI override:

Set `DEPRECATION_AS_OF=YYYY-MM-DD` when invoking
`scripts/validate_deprecation_schedule.py` (or running its test) to simulate
validation as of a future (or past) date—useful for previewing imminent
enforcement before the real cutoff.
