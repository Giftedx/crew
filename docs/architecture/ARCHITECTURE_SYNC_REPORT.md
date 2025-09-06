---
title: Architecture & Codebase Sync Report
origin: ARCHITECTURE_SYNC_REPORT.md (root)
status: migrated
last_moved: 2025-09-02
---

<!-- Original file relocated from repository root during documentation restructure. -->

## Overview

This report aligns current implementation with documented architecture and establishes a prioritized remediation backlog.

## 1. Architectural Conformance Snapshot

| Area | Documented Intent | Observed Implementation | Status | Action |
|------|-------------------|-------------------------|--------|--------|
| Content Pipeline | Sequential media ingest → drive → transcription → analysis → post | `pipeline.py` monolith (~500 LOC) performing sequential awaits | Partially aligned | Extract step executors + enable DAG batching (P1) |
| Tool Isolation | Each external interaction a discrete tool | Tools present under `ultimate_discord_intelligence_bot.tools.*` | Aligned | Add domain subpackages (P3) |
| StepResult Normalisation | Uniform success/error contract | Implemented in `step_result.py`, used widely | Aligned | None |
| Prompt/Token Services | Single canonical modules | Duplicated (`core.prompt_engine` & `services.prompt_engine`; `core.token_meter` & `services.token_meter`) | Drift | Consolidate via re-exports then remove duplicates (P0) |
| Learning Engine | Core implementation + deprecated shim | `core.learning_engine` plus `services.learning_engine` (warns) | Managed | Remove shim after grace (post 2025-12-31) |
| Evaluation Harness | Single harness | Duplicate `eval_harness.py` vs `evaluation_harness.py` | Drift | Keep `eval_harness.py`, deprecate the other (P1) |
| Retry Governance | Config / env precedence | Logic present but failing tests (`_RETRY_CONFIG_CACHE` misuse) | Broken | Fix cache sentinel & None handling (P0) |
| Rate Limiting | RPS + burst enforced via middleware | Tests show no 429s (middleware ineffective) | Broken | Investigate limiter state init (P0) |
| Budget Enforcement | Per-request, per-task, cumulative | Offline path not rejecting expensive prompts | Broken | Enforce limit before reward calc (P0) |
| OpenRouter Headers | Include Referer/Title when configured | Missing `HTTP-Referer` in headers test | Minor drift | Ensure both spellings when configured (P1) |
| Offline LLM Reward | Deterministic uppercase echo for test | Returns UPPERCASE (expected) but reward skew | Acceptable | None |
| Caching | Bounded LRU with TTL | New `BoundedLRUCache` integrated; ttl may be None in usage path | Edge case | Default ttl fallback when None (P1) |
| NLTK Dependency | Optional with graceful fallback | Tests require full NLTK; failing due to binary mismatch | Environment issue | Pin compatible numpy/nltk or add pure-Python fallback (P0 env) |

## 2. Test Failure Root Causes (Summary)

1. Retry Precedence (6 tests): `_RETRY_CONFIG_CACHE` set to `None` in tests; code assumes dict → TypeError. Need sentinel & reset helper.
2. Rate Limiting (2 tests): No 429s. Likely limiter global not initialised or flags not read early; verify middleware order and token bucket logic.
3. NLTK Required (2 tests): Environment mismatch (numpy/Scipy). Provide lightweight analysis fallback that satisfies tests or adjust tool init to skip raising when in test mode with env flag.
4. OpenRouter Headers (1): `HTTP-Referer` absent. Add alias when `Referer` set.
5. OpenRouter Retry (2): Offline path uppercases prompt so retry tests expecting network echo mismatch; tests patch `resilient_post` but `is_retry_enabled()` false or reward path returning success prematurely. Ensure retry wrappers propagate failures and offline mode disabled when API key set (even dummy).
6. Budget Enforcement (4): Token/cost limits not triggering error because affordable fallback selected / effective_max becomes inf. Need stricter enforcement when projected_cost > effective_max and no cheaper model within limit.
7. Cache TTL None (1): Reward cache sets TTL using `time.time() + self.ttl` where `self.ttl` may be None.
8. Security Events (2): Moderation action logged as `moderation.review` instead of `moderation` for block path.
9. Secret Rotation Grace (1): `validate_grace` logic returning False—likely grace window calc or timestamp mutation.
10. Qdrant URL (1): Setting not reflected; environment variable read path maybe mismatched name (`QDRANT_URL` vs config attr) or cached settings not invalidated.

## 3. Prioritized Remediation Backlog

### P0 (Fix before new feature work)

1. Retry precedence cache sentinel + reset util.
2. Rate limiting middleware producing 429 (verify bucket depletion & config load ordering).
3. Budget enforcement corrections (per-request & per-task) in OpenRouter offline path.
4. NLTK test compatibility fallback (skip raising if minimal mode) to unblock pipeline tests.
5. Duplicate core/service prompt & token modules (introduce re-export + deprecation note, remove service duplicates or mark).
6. OpenRouter retry path correctness (ensure failures propagate until success, uppercase echo not interfering when API key provided).

### P1

1. Header completeness (Referer + HTTP-Referer always when configured).
2. Bounded cache None TTL guard.
3. Evaluation harness duplication cleanup.
4. Moderation logging consistency.
5. Qdrant URL settings cache invalidation helper.
6. Secret rotation grace logic audit.

### P2

1. Pipeline modular extraction (steps & DAG execution scaffolding).
2. Tool domain subpackages & auto-discovery.
3. Flag/doc sync test.

### P3

1. Parallel ingest/transcription concurrency.
2. Transcript caching layer.
3. Performance benchmarking harness integration into CI.

## 4. Execution Wave Plan

Wave 1 (P0): Implement retry cache fix, rate limit fix, budget enforcement patch, NLTK fallback, de-dupe prompt/token, retry correctness. Target: restore failing tests to <5.
Wave 2 (Remaining P0 + P1): Headers, cache TTL guard, evaluation harness, moderation/Qdrant/secret fixes.
Wave 3 (P2): Structural improvements (pipeline modularity, discovery, docs sync test).
Wave 4 (P3): Performance & caching enhancements.

## 5. Metrics & Verification Artifacts

| Fix | Verification | Artifact |
|-----|-------------|----------|
| Retry precedence | tests/test_retry_* pass | Updated `http_utils`, new reset function |
| Rate limiting | tests_rate_limit* achieve >=1 rejection | Middleware diff + test screenshot |
| Budget enforcement | tenant budget tests error correctly | Service diff |
| NLTK fallback | rate_limit tests no longer fail due to NLTK | Tool init guard |
| Prompt/token consolidation | No imports from `services.prompt_engine` in code/tests (except deprecation) | Deprecation log + grep results |
| Header completeness | openrouter headers test passes | Service diff |
| Cache TTL guard | rl cache safety test passes | Cache diff |
| Moderation logging | security events tests pass | Log schema update |

## 6. Risk & Mitigation

- Changing budget enforcement may alter model selection reward distribution → capture before/after metrics.
- Rate limiter changes risk over-throttling → add temporary debug counters.
- Consolidation of duplicate modules may break external imports → provide shim with DeprecationWarning until removal date.

## 7. Immediate Next Commit Scope (Wave 1)

- Implement retry cache sentinel & reset util.
- Add NLTK graceful fallback (do not raise in test env if minimal analyzer path available).
- Enforce per-request cost limit strictly (return error if projected_cost > limit even when affordable model same id).
- Ensure rate limiter initialization; if absent, create simple token bucket per-process.

---
Generated 2025-09-02
