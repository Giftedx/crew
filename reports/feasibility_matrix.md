# Feasibility Matrix

Legend (1–5):

- Architecture Fit (AF): Alignment with existing modular seams & flag patterns
- Impact Potential (IP): Expected improvement to quality, cost, latency, or accuracy
- Effort (EF): Implementation effort (5 = low effort / fast)
- Maintainability (MT): Long‑term upkeep cost (5 = low overhead)
- Risk (RK): Operational & regression risk (5 = low risk)
- Dependency Complexity (DC): New external deps / infra (5 = none or already present)
- Strategic Leverage (SL): Enables future roadmap acceleration (5 = high leverage)

Weighted Score formula:
WS = 0.2*(AF + IP) + 0.15*(EF + MT) + 0.1*(RK + DC + SL)

| # | Feature | Flag (proposed) | AF | IP | EF | MT | RK | DC | SL | WS | Minimal Steps (condensed) | Migration & Rollback Notes |
|---|---------|-----------------|----|----|----|----|----|----|----|----|---------------------------|----------------------------|
| 1 | LinTS Bandit Policy | ENABLE_RL_LINTS | 5 | 4 | 5 | 5 | 5 | 5 | 4 | 4.70 | (1) Add LinTS policy class leveraging existing posterior update pattern (2) Register in `LearningEngine` (3) Flag gate selection path | Safe: flag off reverts to current policies; snapshot/restore unchanged. Rollback: remove registration & flag. |
| 2 | Dynamic Context Trimming | ENABLE_CONTEXT_TRIMMING | 5 | 4 | 4 | 5 | 5 | 5 | 5 | 4.65 | (1) Insert trimming middleware before LLM call (2) Heuristic token budget calculation (3) Metrics for tokens removed | Passive when disabled; rollback = remove middleware import. Ensure StepResult unaffected. |
| 3 | A/B Harness & Dashboard | ENABLE_EXPERIMENT_HARNESS | 5 | 5 | 3 | 4 | 4 | 5 | 5 | 4.45 | (1) Experiment allocator wrapper (2) Metrics label for variant (3) Grafana dashboard JSON panels | Ensure low-cardinality variant names; rollback by disabling flag & dropping allocator wrapper. |
| 4 | Adaptive Cost-Aware Routing | ENABLE_COST_AWARE_ROUTING | 5 | 5 | 3 | 4 | 4 | 5 | 5 | 4.45 | (1) Extend model scoring with cost/latency utility (2) Incorporate into `select_model` pipeline (3) Metrics: cost_per_success | Fallback path: keep legacy selection if flag off. Rollback: remove cost utility term. |
| 5 | Semantic Cache | ENABLE_SEMANTIC_CACHE | 5 | 4 | 4 | 4 | 4 | 5 | 5 | 4.40 | (1) Embedding hash + ANN lookup pre-LLM (2) Cache write on success (3) Hit/miss metrics | Rollback: clear cache namespace & disable flag; no persistent schema changes beyond optional table/collection. |
| 6 | Retrieval Fusion (Vector+Lexical+Graph scoring) | ENABLE_MEMORY_FUSION | 5 | 5 | 3 | 4 | 4 | 4 | 5 | 4.35 | (1) Add BM25/BM42 lightweight scorer (2) Weighted combine + rerank (3) Metrics: fusion_gain@k | Disable flag to revert to current vector-first retrieval. Rollback: remove scoring module. |
| 7 | Memory Pruning & Summarization | ENABLE_MEMORY_PRUNE | 5 | 4 | 3 | 4 | 4 | 4 | 5 | 4.15 | (1) Usage/recency decay job (2) Cluster + summarization pass (3) Archive & pin exceptions | Rollback: stop scheduled job, retain existing vectors; archived copies allow restore. |
| 8 | Bootstrapped UCB Policy | ENABLE_RL_BOOTSTRAPPED_UCB | 4 | 4 | 3 | 4 | 4 | 5 | 4 | 3.95 | (1) Implement ensemble of UCB heads (2) Register policy (3) Flag gating | Coexists with LinTS; rollback by deregistering. |
| 9 | Prompt Compression (Hierarchical) | ENABLE_PROMPT_COMPRESSION | 4 | 4 | 3 | 4 | 4 | 4 | 5 | 3.95 | (1) Segment + summarize long context (2) Token guard rails (3) Quality ratio metrics | Rollback: bypass compression step; keep summarizer utility for other tasks. |
| 10 | Knowledge Graph Retrieval Augmentation | ENABLE_KG_AUGMENT | 3 | 5 | 2 | 3 | 3 | 2 | 5 | 3.35 | (1) Entity extraction → KG lookup (2) Merge KG facts into retrieval context (3) Confidence gating | Rollback: disable flag; ensure KG store untouched. Higher complexity due to new store ops. |
| 11 | Speculative Decoding | ENABLE_SPECULATIVE_DECODING | 3 | 4 | 2 | 3 | 3 | 2 | 4 | 3.05 | (1) Draft + verify calls if provider supports (2) Latency/quality metrics (3) Fallback to normal decode on mismatch | Risk: provider support variability; rollback: disable feature path. |
| 12 | NeuralUCB (Future) | ENABLE_RL_NEURALUCB | 3 | 5 | 1 | 2 | 2 | 3 | 5 | 3.05 | (1) Torch model for feature embedding (2) Uncertainty estimation layer (3) Training loop integration | Pilot offline first; rollback: keep behind experimental flag until stable. |

## Observations

- Top immediate wins (score ≥4.4) combine low friction with broad leverage: LinTS, Dynamic Context Trimming, A/B Harness, Cost-Aware Routing, Semantic Cache.
- Retrieval Fusion slightly higher impact than Semantic Cache for accuracy uplift but slightly more effort & dependency complexity.
- Lower scoring items (Speculative Decoding, NeuralUCB) deferred due to provider constraints & engineering complexity.
- KG Augmentation’s impact potential is high but infra & modeling complexity reduce initial score.

## Recommended Sequencing Snapshot

1. LinTS → 2. Dynamic Context Trimming → 3. Semantic Cache → 4. A/B Harness (could be #2 if experimentation infra needed earlier) → 5. Cost-Aware Routing → 6. Retrieval Fusion → 7. Memory Pruning → 8. Prompt Compression → 9. Bootstrapped UCB → 10. KG Augmentation → 11. Speculative Decoding → 12. NeuralUCB.

(Full roadmap & prioritization details will be expanded in subsequent tasks.)
