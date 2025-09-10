# Quality & Alignment Matrix

Purpose: Track alignment between documentation and implementation, and drive prioritized remediation. This matrix complements docs like `docs/observability.md`, `docs/feature_flags.md`, `docs/tenancy.md`, `docs/retries.md`, and the project conventions (StepResult contract, HTTP wrappers, tenancy threading, determinism, and feature flags).

## How to Use

1. Populate “Current Evidence” with concrete references (file:line or summary).
1. Record drift risk and the chosen remediation.
1. Link PRs/commits in the Verification column.
1. Keep labels low-cardinality; do not paste raw user text or URLs into this document.

## Matrix

| Domain | Key Doc(s) | Expected Code Locus | Current Evidence | Drift Risk | Remediation | Verification |
|--------|------------|---------------------|------------------|-----------|-------------|--------------|
| Ingestion | `docs/ingestion.md` | `src/ingest/` | Present (`src/ingest/`) – not yet audited | TBI | Audit dispatcher + sources; verify StepResult + metrics | TBI |
| Memory / Retention | `docs/memory.md`, `docs/retention.md` | `src/ultimate_discord_intelligence_bot/services/memory_service.py` | Memory service present with tenant namespace derivation (`src/ultimate_discord_intelligence_bot/services/memory_service.py`) | Lower (mitigated) | Strict tenancy mode added: when `ENABLE_TENANCY_STRICT=1` (or `ENABLE_INGEST_STRICT=1`) a missing tenant raises; non‑strict logs a warning and defaults | Done (file: `src/ultimate_discord_intelligence_bot/services/memory_service.py`; flags: `ENABLE_TENANCY_STRICT`, `ENABLE_INGEST_STRICT`; metric: `tenancy_fallback_total`) |
| Grounding / RAG | `docs/grounding.md`, `docs/rag.md` | `src/grounding/`, `src/kg/` | Present – not yet audited | TBI | Verify vector search StepResult and deterministic IDs | TBI |
| RL / Routing | `docs/rl_overview.md` | `src/core/rl/`, `src/core/router.py`, `src/core/learning_engine.py` | Present – not yet audited | TBI | Confirm reward recording, ε-greedy, failure reward 0 | TBI |
| Feature Flags | `docs/feature_flags.md` | Code flags + `scripts/generate_feature_flags_doc.py` | `src/core/flags.py` simple env helper; retries flags read in `src/core/http_utils.py` | Medium | Re-run flag doc generator; ensure all `ENABLE_*` are documented | TBI |
| Observability | `docs/observability.md` | `src/obs/`, otel usage in core | OTEL spans in `src/core/http_utils.py`; metrics via `src/ultimate_discord_intelligence_bot/obs/` | Low | Ensure one span per logical unit; label hygiene | TBI |
| Tenancy | `docs/tenancy.md` | Pervasive (constructors, handlers) | `src/ultimate_discord_intelligence_bot/tenancy/context.py` present; services use current tenant with default fallback | Medium → Lower | Partial remediation: strict mode + fallback warning + counter; remaining: add tests and extend pattern to other services | Partially Done (see `src/ultimate_discord_intelligence_bot/services/memory_service.py`; metric: `tenancy_fallback_total`) |
| OpenRouter Service Tenancy | `docs/tenancy.md#service-behavior-openrouter-tenancy`, `docs/observability.md#tenancy-fallback-visibility-new` | `src/ultimate_discord_intelligence_bot/services/openrouter_service.py` | Tenancy helper `_ctx_or_fallback()` enforces strict mode; non‑strict increments `tenancy_fallback_total` with `component="openrouter_service"`; cache namespacing uses tenant/workspace | Low | Tests added for strict vs non‑strict behavior; function deduplicated and verified; temporary lint suppressions on `route()` complexity with a planned helper extraction refactor | Done (tests: `tests/test_openrouter_tenancy.py`; metrics: `src/ultimate_discord_intelligence_bot/obs/metrics.py`) |
| Scheduler | `docs/scheduler.md` | `src/scheduler/` | Present – not yet audited | TBI | Verify deterministic job keys & metrics | TBI |
| Privacy / Security | `docs/privacy.md`, `config/security.yaml` | `src/security/` | Present – not yet audited | Medium | Audit guards and policy enforcement | TBI |
| Deprecations | `config/deprecations.yaml` | Cross-cutting | Present – not yet audited | Medium | Ensure one-time warnings + docs sync | TBI |
| HTTP & Caching | `docs/retries.md`, `docs/caching.md`, `docs/network_conventions.md` | `src/core/http_utils.py` | Central wrappers present; auditor confirms src/ compliant. Scripts updated to use wrappers (`scripts/verify_external_api_contracts.py`, `scripts/diagnostics/api_diagnostic.py`) | Lower | Enforce via auditor in CI; prefer `cached_get` for docs fetch; avoid direct `requests/httpx` in utilities | Done (auditor run: All files comply) |
| Determinism & Time | `docs/observability.md`, `docs/slo.md` | `src/core/time.py` | Module present – not yet audited | Medium | Verify `ensure_utc` usage; stable hashing for IDs | TBI |
| Cost & Token Metering | `docs/cost_and_caching.md` | `src/core/token_meter.py` | Present – not yet audited | TBI | Confirm metering on model calls and caching policy | TBI |

Legend: TBI = To Be Investigated.

## Contract Compliance Checklist

- StepResult:
  - [ ] All external/system operations return `StepResult.ok|fail|skip`.
  - [ ] Recoverable issues (404, empty transcript) return `fail` or `skip`, not raised.
  - [ ] Unexpected exceptions allowed to raise after metrics/logging.

- Tenancy:
  - [ ] Thread `TenantContext` through stateful components.
  - [ ] Stateful classes accept `(tenant, workspace)` early.
  - [ ] No raw user text/URLs in metric labels or namespaces.

- HTTP & Caching:
  - [ ] No direct `requests`/`httpx` calls; use `src/core/http_utils.py` wrappers.
  - [ ] Use `cached_get` for cacheable GETs.
  - [ ] Retry config via `config/retry.yaml` respected.

- Feature Flags & Deprecations:
  - [ ] `ENABLE_*` flags default off; documented.
  - [ ] Deprecation warnings emitted (once), docs updated.

- Observability:
  - [ ] One span per logical unit.
  - [ ] Metrics incremented before returning `StepResult`.
  - [ ] Labels low-cardinality only.

- Determinism & Time:
  - [ ] UTC-only time via `core.time.ensure_utc`.
  - [ ] Deterministic identifiers (stable hashing), especially for ingestion episodes.
  - [ ] Heavy/experimental code paths behind flags.

## Evidence Collection Commands

Run these locally and paste outputs (or enable automation) to populate the matrix:

```sh
tree -L 3 src
rg "StepResult" -t py src | wc -l
rg -t py "requests\\." src || true
rg -t py "httpx\\." src || true
rg -t py "TenantContext" src | wc -l
rg -t py "with_tenant" src
rg -t py "ENABLE_[A-Z0-9_]+" src | sort | uniq -c
rg -t py "tenancy_fallback_total" src || true
rg -t py "metric" src
rg -t py "labels=" src
rg -t py "uuid|random|time.time\\(\\)" src
rg -t py "^import " src/ultimate_discord_intelligence_bot/crew.py || true
rg -t py "^from .* import" src/ultimate_discord_intelligence_bot/crew.py || true
make format && make lint && make type && make test-fast && make compliance
```

## Prioritization Rubric

Score(action) = 0.4·Impact + 0.3·RiskReduction + 0.2·Alignment + 0.1·(6 − Effort)

Use this to order remediation items in the backlog.

## Reporting Format for Findings

For each confirmed item, record:

- Location: `file.py:line`
- Finding: concise description
- Thinking (#think): rationale and trade-offs
- Sequential Plan (#sequentialthinking): discrete steps to fix
- Context (#Context7): relevant excerpts from docs or conventions
- Solution: patch or code block
- Tests: added/updated tests
- Verification: commands and results
