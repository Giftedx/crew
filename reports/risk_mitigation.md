# Risk Mitigation Catalog

## Legend

- Sev: High (H) / Medium (M) / Low (L)
- Likelihood: High / Medium / Low (qualitative)
- Rollback Trigger: Condition that forces immediate flag disable & incident note

## 1. Consolidated Risk Table

| Feature | Category | Risk | Sev | Likelihood | Detection Metric / Signal | Mitigation | Rollback Trigger |
|---------|----------|------|-----|------------|----------------------------|------------|------------------|
| LinTS | Reliability | Posterior numerical instability | M | L | NaN/Inf in reward logs | Clamp variance; unit tests for update | Any NaN/Inf detected >0 |
| LinTS | Performance | Selection latency spike | L | L | routing_latency_ms p95 | Pre-allocate arrays | p95 +20% 24h |
| A/B Harness | Observability | Metric cardinality explosion | M | M | exp_active_variants count | Validate variant names set | >10 active variants simultaneously |
| A/B Harness | Data Integrity | Biased variant allocation | M | M | variant distribution chi-square | Hash + salt; periodic balance audit | p-value <0.01 imbalance persistent |
| Dynamic Trimming | Quality | Over-trimming harms relevance | H | M | answer_relevance_delta | Shadow diff & guard min relevance | Relevance Δ < -2% 12h |
| Dynamic Trimming | Reliability | Incorrect token counts | M | L | trimming_ratio erratic spikes | Fallback to original context | Ratio variance >3σ baseline |
| Semantic Cache | Data Integrity | Stale / concept drift answers | M | M | cache_hit_ratio with rising complaint rate | Add TTL & freshness score | Quality complaints > baseline +50% |
| Semantic Cache | Performance | Cache lookup latency growth | M | L | cache_latency_ms p95 | Index optimization, limit k | p95 > 10ms 24h |
| Cost-Aware Routing | Cost | Overfavor cheap low-quality model | H | M | cost_per_success & quality drop | Quality floor threshold | Quality metric Δ < -2% while cost ↓ |
| Cost-Aware Routing | Reliability | Misconfigured cost metadata | M | L | missing cost metadata counter | Validation on startup | Missing metadata >0 |
| Retrieval Fusion | Performance | Latency increase from extra scorers | M | M | retrieval_latency_ms p95 | Cap lexical docs; parallel scoring | p95 +15% 24h |
| Retrieval Fusion | Quality | Weight miscalibration reduces relevance | H | M | nDCG@10 delta negative | A/B tuning; weight fallback | nDCG@10 Δ < -1pt 24h |
| Memory Pruning | Data Integrity | Deleting important content | H | M | manual spot check failures | Dry-run & whitelist pins | Critical content loss incident |
| Memory Pruning | Reliability | Summaries drift semantic meaning | M | M | summarization_quality_sample | Periodic sample review | Drift rate >5% samples |
| Prompt Compression | Quality | Information loss in compression | H | M | answer_relevance_delta | Two-pass hierarchical summary | Relevance Δ < -2% 24h |
| Prompt Compression | Performance | Additional summarization latency | M | M | compression_latency_ms | Cache summaries; early exit | p95 +15% 24h without token savings |
| Bootstrapped UCB | Performance | Extra compute per selection | M | M | routing_latency_ms | Limit heads; reuse features | p95 +15% 24h |
| Bootstrapped UCB | Reliability | Ensemble variance collapse | L | M | rl_ensemble_variance ~0 | Re-seed / ensemble size adjust | Variance < ε for 24h |
| KG Augmentation | Quality | Hallucination amplification | H | M | hallucination_rate | Confidence gating; attribution tags | Hallucination rate +2% absolute |
| KG Augmentation | Performance | KG lookup latency | M | M | kg_lookup_latency_ms p95 | Batch lookups; cache edges | p95 > 30ms 24h |
| Speculative Decoding | Reliability | Provider API mismatch | M | L | draft_acceptance_rate near 0 | Capability probe fallback | Acceptance <5% 24h |
| Speculative Decoding | Quality | Draft token errors | M | M | quality regression metrics | Partial decode verification | Relevance Δ < -1% 24h |
| NeuralUCB | Reliability | Training instability | H | M | loss oscillation; gradient norms | Gradient clipping & early stop | Loss divergence (>2x min) |
| NeuralUCB | Maintainability | Model drift & dependency bloat | M | M | model_version_count | Scheduled retrain policy | >3 stale models retained |

## 2. High-Severity Risk Deep Dives

### Dynamic Trimming Over-Reduction

Scenario: Aggressive heuristic discards context with latent relevance.
Mitigation Stack: Shadow evaluation -> dynamic threshold -> feedback metric guard.
Additional Control: Auto-disable if cumulative negative relevance impact >1% over 48h.

### Cost-Aware Routing Quality Regression

Scenario: Utility function overweighting cost leading to quality degradation.
Mitigation Stack: Quality floor; blended score: utility = reward_est *alpha - cost_weight* cost.
Additional Control: Adaptive alpha tuned via experiment harness.

### Memory Pruning Critical Data Loss

Scenario: High-value memory archived accidentally.
Mitigation Stack: Dry-run candidate list; pinning interface; reversible archive store.
Additional Control: Weekly audit sample N=50 high-score memories pre/post prune.

### Prompt Compression Information Loss

Scenario: Excessive summarization harming downstream accuracy.
Mitigation Stack: Two-tier summarization (chunk -> section); keep tail of original context.
Additional Control: Failure sampling with diff scoring (BLEU/ROUGE vs baseline subset).

### KG Augmentation Hallucination Amplification

Scenario: Low-confidence facts inserted appear authoritative.
Mitigation Stack: Confidence threshold + provenance tags + per-fact max injection count.
Additional Control: Strip KG facts in evaluation variant to measure net contribution.

## 3. Cross-Cutting Risks

| Risk | Sev | Likelihood | Affected Features | Mitigation | Detection |
|------|-----|-----------|-------------------|------------|-----------|
| Flag Sprawl & Complexity | M | M | All | Periodic flag audit; consolidation after stabilization | Count of active flags |
| Metric Cardinality Explosion | M | M | A/B, Fusion, KG | Pre-approved label whitelist | Metrics backend alerts |
| Cache Poisoning (Semantic) | H | L | Semantic Cache | Hash input normalization; source trust scoring | Spike in contradictory hits |
| Model Drift (LLM / Summarizer) | M | M | Trimming, Compression | Scheduled eval set regression tests | Relevance delta trends |
| Privacy Leakage via Logs | H | L | All | PII filter before logging; sampling | Log scan tool alerts |
| Latency Budget Erosion | M | M | Routing, Fusion, Cache | Budget per layer; regression CI test | p95 latency aggregate |
| Cost Regression Hidden by Optimization | M | L | Cost Routing, Cache | Unified cost_per_success panel | Divergence between cost & reward curves |

## 4. Detection & Alerting Guidelines

- All rollback triggers integrate into alert rules (PagerDuty / on-call) with severity mapped to feature category.
- Shadow phases emit synthetic "would_rollback" metrics for dry-run of alarm thresholds.

## 5. Incident Response Template (Abbreviated)

1. Identify feature and flag state.
2. Capture last 1h metrics snapshot (latency, primary metric, error rate).
3. Flip flag off; record timestamp.
4. Verify stabilization (15 min) then open RCA document.
5. Add regression test if bug originated from logic gap.

## 6. Maintenance Cadence

| Activity | Frequency | Owner | Artifact |
|----------|-----------|-------|----------|
| Flag Audit | Quarterly | Platform Lead | flag_audit.md |
| Metric Cardinality Review | Monthly | Observability | metrics_cardinality_report.json |
| Semantic Cache Freshness Sample | Weekly | Memory Team | cache_freshness_sample.csv |
| Pruning Sample Audit | Weekly | Memory Team | pruning_audit.csv |
| RL Policy Performance Review | Bi-weekly | RL SME | rl_policy_report.md |
| KG Fact Confidence Calibration | Monthly | KG/Graph | kg_confidence_calibration.md |

## 7. Future Enhancements

- Automated dynamic weighting for Retrieval Fusion with Bayesian optimization (adds risk category: Auto-tuning Drift).
- Privacy-preserving semantic cache encryption at-rest (reduces potential leakage severity).
- Unified rollback orchestrator script referencing flags & dashboards.

---
Prepared as part of comprehensive review (Risk Mitigation phase). Next: performance improvement estimates.
