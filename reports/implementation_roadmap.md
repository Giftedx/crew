# Implementation Roadmap

## 0. Principles

- Flag Gating: Every feature behind `ENABLE_*` flag; default off until post-shadow validation.
- Shadow First: Compute & log metrics without user-facing effect to establish expected deltas.
- Single Attribution: Avoid overlapping canaries that target the same primary metric dimension (retrieval, cost, exploration) to preserve causal clarity.
- Metric Gates: Promotion requires pre-defined thresholds (see Exit Criteria) checked over stable observation windows (>=72h unless noted).
- Reversible: Rollback = flip flag + flush transient state (cache, temporary collections) without schema migrations.
- Observability: Each feature adds at least one new metric and/or trace span with low cardinality labels.

## 1. High-Level Timeline (Indicative Weeks)

| Week | Phase | Feature(s) | Dependencies | Gate (Enter Canary) | Exit Criteria (Full Rollout) |
|------|-------|------------|--------------|---------------------|------------------------------|
| 1 | Phase 0 | A/B Harness (shadow) | Metrics baseline | Harness emits variant logs | Successful dry-run experiment metadata + dashboards live |
| 1 | Phase 0 | LinTS (shadow) | A/B Harness | Reward logging parity | Posterior updates stable (no NaN); regret trending down in shadow |
| 2 | Phase 1 | LinTS (canary→full) | Shadow data | Regret < baseline by ≥3% | 7-day sustained improvement; no latency regression |
| 2 | Phase 1 | Dynamic Trimming (shadow) | LinTS stable | Accurate token diff logs | ≥15% median trimming, no relevance drop >1% |
| 3 | Phase 1 | Dynamic Trimming (canary) | Shadow metrics | Stable trimming ratio | Full after 72h stable relevance metrics |
| 3 | Phase 1 | Semantic Cache (shadow) | A/B Harness | Hit potential ≥15% | Projected hit ratio validated, no latency penalty |
| 4 | Phase 2 | Cost-Aware Routing (shadow) | LinTS full + Harness | Utility logs valid | Cost_per_success simulated reduction ≥5% |
| 4 | Phase 2 | Semantic Cache (canary) | Shadow data | Warming curve acceptable | Hit ratio ≥20%, p95 latency neutral |
| 5 | Phase 2 | Cost-Aware Routing (canary) | Shadow data | Utility uplift persists | ≥10% cost_per_success reduction stable |
| 5 | Phase 2 | Retrieval Fusion (shadow) | Baseline retrieval metrics | Fusion scores computed | nDCG@10 uplift ≥3 pts in shadow eval |
| 6 | Phase 2 | Retrieval Fusion (canary) | Shadow success | nDCG uplift persists | ≥5 pt uplift & latency delta <10% |
| 6 | Phase 3 | Memory Pruning (dry-run) | Fusion shadow (signals) | Candidate listing accurate | No critical items in prune set (manual spot check) |
| 7 | Phase 3 | Memory Pruning (canary) | Dry-run results | Safe archive operations | Storage growth slope ↓ ≥25%, relevance impact <2% |
| 7 | Phase 3 | Prompt Compression (shadow) | Trimming full | Compression logs consistent | Simulated compression ratio ≥30% |
| 8 | Phase 4 | Prompt Compression (canary) | Shadow results | Relevance delta <2% | Promote after 72h stability |
| 8 | Phase 4 | Bootstrapped UCB (shadow) | LinTS full | Ensemble variance logs | No API regressions, variance informative |
| 9 | Phase 4 | Bootstrapped UCB (canary) | Shadow results | Reward non-degraded | Optional full after justification |
| 9 | Phase 5 | KG Augmentation (shadow) | Fusion canary | Entity extraction stable | nDCG uplift on entity queries ≥3 pts |
| 10 | Phase 5 | KG Augmentation (canary) | Shadow results | Uplift persists | Hallucination rate neutral |
| 10 | Phase 5 | Speculative Decoding (shadow) | Provider capability | API feature present | Draft acceptance logs valid |
| 11 | Phase 5 | Speculative Decoding (canary) | Shadow results | ≥10% p95 latency gain | ≥15% gain & quality stable |
| 11+ | Phase 5 | NeuralUCB (offline) | LinTS data corpus | Offline eval harness | Offline reward ≥5% over LinTS |
| 12+ | Phase 5 | NeuralUCB (shadow online) | Offline success | Inference stable | Low variance predictions |

## 2. Phase Detail

### Phase 0 (Foundation)

- Implement A/B Harness; create baseline dashboards (reward, latency, cost, retrieval quality).
- LinTS shadow to gather posterior behavior & ensure reward interface consistency.

### Phase 1 (Exploration & Efficiency)

- Promote LinTS if improvement evident.
- Introduce Dynamic Context Trimming to cut early unnecessary tokens.
- Semantic Cache shadow to estimate prospective hit ratio with real embeddings.

### Phase 2 (Cost & Retrieval Quality)

- Cost-Aware Routing uses reward logs + cost metadata to optimize utility.
- Semantic Cache canary to realize cost savings.
- Retrieval Fusion lifts relevance—evaluate interplay with cache hit content variety.

### Phase 3 (Memory Lifecycle)

- Dry-run pruning ensures safe candidate identification; summarization ensures context preservation.
- Prompt Compression shadow so later compression leverages already trimmed context.

### Phase 4 (Advanced RL & Refinements)

- Bootstrapped UCB for variance-based exploration diversification.
- Prompt Compression production to further cost control after trimming stabilization.

### Phase 5 (Extended Intelligence & Latency)

- KG Augmentation for entity-rich queries.
- Speculative Decoding dependent on provider features; opportunistic latency improvement.
- NeuralUCB remains experimental; staged offline → shadow → canary.

## 3. Dependency Graph (Textual)

- A/B Harness → {LinTS measurement, Cost-Aware Routing, Semantic Cache evaluation}
- LinTS → {Bootstrapped UCB, NeuralUCB}
- Retrieval Fusion → Memory Pruning (needs fused signal importance)
- Dynamic Trimming → Prompt Compression (ensures no double work inefficiency)
- Semantic Cache (optional) independent of Fusion but synergistic for cost metrics attribution.

## 4. Concurrency & Change Management

- Max 2 simultaneous canaries; never 2 affecting retrieval scoring concurrently.
- Canary Duration: Minimum 72h or until 95% CI excludes zero for primary metric uplift.
- Abort Conditions: Error rate +50% relative, latency p95 +20%, or negative primary metric delta > predefined threshold.

## 5. Rollback Playbook

1. Flip feature flag off.
2. Purge temporary state (e.g., semantic cache collection) if corrupted.
3. Invalidate dashboards panel referencing feature to avoid misleading flatlines.
4. File incident note summarizing root cause & metrics deltas.

## 6. Ownership & Artifacts (Placeholders)

| Feature | Eng Owner | Reviewers | Primary Dashboard |
|---------|-----------|-----------|-------------------|
| LinTS | TBA | RL SME | rl_routing.json |
| A/B Harness | TBA | Platform | experiments.json |
| Dynamic Trimming | TBA | LLM Ops | context_efficiency.json |
| Semantic Cache | TBA | Memory Lead | cache_performance.json |
| Cost-Aware Routing | TBA | Finance/Cost | routing_cost.json |
| Retrieval Fusion | TBA | Retrieval SME | retrieval_quality.json |
| Memory Pruning | TBA | Memory Lead | memory_lifecycle.json |
| Prompt Compression | TBA | LLM Ops | compression.json |
| Bootstrapped UCB | TBA | RL SME | rl_variance.json |
| KG Augmentation | TBA | KG/Graph | kg_aug.json |
| Speculative Decoding | TBA | LLM Ops | latency_advanced.json |
| NeuralUCB | TBA | RL SME | rl_neural.json |

## 7. Exit Criteria Summary

| Feature | Primary Metric | Threshold |
|---------|----------------|-----------|
| LinTS | Reward | ≥3% uplift |
| Dynamic Trimming | Token Reduction | ≥15% median, relevance Δ ≤1% |
| Semantic Cache | Hit Ratio | ≥25% (steady) |
| Cost-Aware Routing | Cost per Success | ≥10% reduction |
| Retrieval Fusion | nDCG@10 | ≥5 pt uplift |
| Memory Pruning | Storage Growth | ≥30% slope reduction |
| Prompt Compression | Compression Ratio | ≥30% reduction, relevance Δ ≤2% |
| Bootstrapped UCB | Reward / Variance | Non-degraded reward + beneficial variance |
| KG Augmentation | nDCG@10 (Entity Queries) | ≥3 pt uplift |
| Speculative Decoding | p95 Latency | ≥15% reduction, quality stable |
| NeuralUCB | Offline Reward | ≥5% over LinTS |

## 8. Notes & Future Considerations

- Consider auto-disable watchdog if feature causes repeated abort cycles (≥2 in 30 days).
- After Phase 3, revisit weighting of context trimming vs compression synergy for potential consolidation.
- Evaluate adding adaptive thresholds (dynamic baselines) after harness maturity.

---
Prepared as part of comprehensive review; subsequent documents: risk catalog (`risk_mitigation.md`) & performance estimates (`performance_estimates.md`).
