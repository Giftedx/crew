# Quick Start: Optional Enhancements (Shadow-safe)

These flags enable cost and quality improvements without changing code paths. They default to OFF. You can flip them on per-run via environment variables or your `.env`.

All features are tenant-aware and respect existing guardrails (StepResult, retries, HTTP wrappers, metrics). If a dependency is absent, they degrade gracefully.

## 1) Semantic cache (GPTCache-backed)

- Purpose: Reduce repeated LLM calls via semantic similarity.
- Modes:
  - ENABLE_SEMANTIC_CACHE=1 → Active global cache
  - ENABLE_GPTCACHE=1 → Tenant-scoped semantic cache directories under `cache/semantic/<tenant:workspace>`
  - ENABLE_SEMANTIC_CACHE_SHADOW=1 → Shadow lookups (no promotion)

  - ENABLE_SEMANTIC_CACHE_PROMOTION=1 → Allow high-similarity shadow hits to short-circuit network

Minimal .env snippet:

```bash

ENABLE_GPTCACHE=true
ENABLE_SEMANTIC_CACHE_SHADOW=true
ENABLE_GPTCACHE_ANALYSIS_SHADOW=true
SEMANTIC_CACHE_PROMOTION_THRESHOLD=0.9
```

Verification:

- Run tests or a single pipeline job and observe metrics:
  - `LLM_CACHE_HITS`, `LLM_CACHE_MISSES`, `SEMANTIC_CACHE_SHADOW_HITS/MISSES`, `SEMANTIC_CACHE_SIMILARITY`

## 2) Prompt compression (LLMLingua optional)

- Purpose: Cut token usage for long prompts/transcripts while keeping meaning.
- Flags:
  - ENABLE_PROMPT_COMPRESSION=true → Enables PromptEngine compression stages
  - ENABLE_LLMLINGUA=true → Enables LLMLingua stage (if package available)
  - ENABLE_LLMLINGUA_SHADOW=true → Runs LLMLingua in shadow, records tokens only

Optional tuning (defaults are sensible):

```bash
PROMPT_COMPRESSION_MAX_TOKENS=1500
LLMLINGUA_TARGET_RATIO=0.35
LLMLINGUA_MIN_TOKENS=600
```

Verification: watch `PROMPT_COMPRESSION_RATIO`, `PROMPT_EMERGENCY_TRUNCATIONS` metrics.

## 3) Graph memory (lightweight GraphRAG-style)

- Purpose: Persist a simple knowledge graph from summaries per tenant namespace.
- Flags:
  - ENABLE_GRAPH_MEMORY=true

Artifacts: JSON graphs under `crew_data/Processing/graph_memory/<tenant__workspace__index>/<graph_id>.json`.

Verification: run pipeline; in final payload, see `graph_memory` section with `graph_id` and `storage_path`.

## 3b) HippoRAG 2 Continual Memory (experimental)

- Purpose: Neurobiologically-inspired continual memory consolidation for long-term context.
- Flags:
  - ENABLE_HIPPORAG_MEMORY=true

Artifacts: Consolidated memory under `crew_data/Processing/hipporag_memory/<tenant__workspace__index>/<memory_id>.json`.

Verification: run pipeline; in final payload, see `hipporag_memory` section with `memory_id` and `storage_path`.

## 4) Adaptive routing (Ax shadow-ready)

- Purpose: Explore/model-select with Bayesian optimization.
- Flags:
  - ENABLE_AX_ROUTING=true

Notes:

- If `ax-platform` is not installed, the manager disables itself without affecting routing.
- Events are logged via analytics store and `ACTIVE_BANDIT_POLICY` gauge.

## 4b) Vowpal Wabbit Online Bandit (experimental)

- Purpose: Enable an online bandit via Vowpal Wabbit (future CB/ADF integration). Currently a safe wrapper that falls back to Thompson Sampling when VW isn't installed.
- Flags:
  - ENABLE_VW_BANDIT=true (or ENABLE_VOWPAL_WABBIT_BANDIT=true)

Behavior: If the `vowpalwabbit` package isn't present, routing remains identical to the Thompson bandit path. No code changes are required.

## Safe rollback

- All flags are default-off. Toggle off to instantly revert to baseline.
- No schema changes to external APIs; StepResult contracts remain unchanged.

## Troubleshooting

- Missing deps: features degrade to fallbacks. Check logs for “disabled”, “fallback”, or “shadow” markers.
- Tenancy: ensure runs are inside a tenant context to get per-tenant namespaces in cache and graphs.
