# Performance Improvement Estimates

## 1. Baseline Metric Definitions

| Metric | Definition | Unit | Current Baseline Status (Placeholder) |
|--------|------------|------|---------------------------------------|
| cost_per_success | (Total LLM + infra cost) / successful tasks | USD | TBD (collect Week 0) |
| nDCG@10 | Normalized DCG for retrieval top-10 vs labeled relevance | score (0-1) | TBD |
| MAP@10 | Mean Average Precision at 10 for retrieval | score (0-1) | TBD |
| p95_latency_ms | 95th percentile end-to-end response latency | ms | TBD |
| token_per_completion | Average tokens (prompt+completion) per task | tokens | TBD |
| storage_growth_rate | Weekly delta of vector store size | % / week | TBD |
| cache_hit_ratio | Semantic cache hits / lookups | % | 0% (pre-cache) |
| regret | Sum(optimal_reward - chosen_reward) | reward units | TBD |
| compression_ratio | (Original tokens - compressed tokens)/original | % | 0% (pre-compression) |
| trimming_ratio | (Original context - trimmed)/original | % | 0% (pre-trimming) |
| draft_acceptance_rate | Accepted draft tokens / proposed draft tokens | % | 0% (pre-speculative) |
| hallucination_rate | Flagged hallucinations / responses (entity queries) | % | TBD |

## 2. Feature Impact Estimates

|min = Minimum acceptable improvement for continued rollout; target = expected central estimate; stretch = optimistic bound.

| Feature | Primary Metrics Impacted | Min | Target | Stretch | Confidence |
|---------|--------------------------|-----|--------|---------|------------|
| LinTS | regret ↓, reward ↑ | 2% regret reduction | 3–5% regret reduction | 6–8% | High |
| A/B Harness | experiment velocity | 1 active exp / wk | 2 / wk | 3+ / wk | High |
| Dynamic Trimming | trimming_ratio, token_per_completion ↓, p95_latency_ms ↓ | 10% trim, 5% token ↓ | 15% trim, 8–10% token ↓, 3% p95 ↓ | 20% trim, 12–15% token ↓, 5% p95 ↓ | High |
| Semantic Cache | cache_hit_ratio, cost_per_success ↓, p95_latency_ms ↓ | 15% hit, 5% cost ↓ | 25% hit, 8–10% cost ↓, 5% p95 ↓ | 35% hit, 12–15% cost ↓, 8% p95 ↓ | Medium |
| Cost-Aware Routing | cost_per_success ↓, reward stable | 5% cost ↓ | 10% cost ↓ | 15% cost ↓ | Medium |
| Retrieval Fusion | nDCG@10 ↑, MAP@10 ↑ | +3 pts nDCG, +2 pts MAP | +5 pts nDCG, +3–4 pts MAP | +7 pts nDCG, +5 pts MAP | Medium |
| Memory Pruning | storage_growth_rate ↓, nDCG stable | 20% slope ↓ | 30% slope ↓ | 40% slope ↓ | Medium |
| Prompt Compression | compression_ratio, token_per_completion ↓ | 20% compression | 30% compression, + extra 5% token ↓ (post-trim) | 40% compression, +8% token ↓ | Medium |
| Bootstrapped UCB | reward variance ↑ (desired exploration), reward stable | Non-degraded reward | Maintains reward, increases variance 5–10% | Maintains reward, variance +15% | Low |
| KG Augmentation | nDCG@10 (entity queries), hallucination_rate stable | +2 pts nDCG entity | +3 pts | +5 pts | Low |
| Speculative Decoding | p95_latency_ms ↓ | 8% p95 ↓ | 15% p95 ↓ | 20% p95 ↓ | Low |
| NeuralUCB | regret ↓ (vs LinTS) | 2% | 5% | 8% | Low |

## 3. Measurement Methodology

### 3.1 Experiment Design

- Primary test: Two-sample difference in means (or proportions) with Welch's t-test (continuous) or Chi-square (proportions).
- Power Target: 0.8 with α = 0.05 (two-tailed) for primary metric uplift.
- Minimum Detectable Effect (MDE) per feature derived from historical variance (to be gathered in Week 0).

### 3.2 Sample Size Heuristic

n ≈ 2 *( (Z_{1-α/2} + Z_{power})^2* σ^2 ) / δ^2  (for continuous)
Where δ = target effect size; σ = baseline std dev.
For proportions (e.g., cache_hit_ratio):
n ≈ 2 *( Z_{1-α/2}* √(2p(1-p)) + Z_{power} * √(p1(1-p1) + p2(1-p2)) )^2 / (p1 - p2)^2

### 3.3 Variance Control

- Stratify by query type (entity vs general) when evaluating KG Augmentation.
- Use paired difference (before/after) for trimming & compression where feasible.
- Exclude warm-up period (first 10% of time buckets) for cache metrics.

### 3.4 Sequential Testing Guard

- Limit interim looks to daily; apply Bonferroni or alpha spending (Pocock) if early stopping.
- Early Stop Rule: If effect >1.5x target with p<0.01 at first interim, escalate to full rollout readiness review.

## 4. Attribution & Data Pipeline

| Aspect | Approach |
|--------|----------|
| Variant Tagging | Append `variant` label to all core metrics through harness |
| Time Window Alignment | Use aligned UTC hour buckets; require ≥90% bucket coverage |
| Outlier Handling | Winsorize top 0.5% latency & token counts before aggregation |
| Missing Data | Emit explicit `missing=1` metric to distinguish absence vs zero |
| Quality Ground Truth | Daily sampling set (N≈200) manually / semi-automatically labeled for retrieval & answer relevance |
| Storage Growth | Derive from vector collection size snapshots (daily) |

## 5. Estimation Assumptions & Confidence

| Feature | Key Assumptions | Confidence Basis |
|---------|-----------------|------------------|
| LinTS | Reward distribution approximately stationary | Prior bandit literature & internal reward stability |
| Dynamic Trimming | Salience scores correlate with eventual relevance | Early heuristic analysis on sample transcripts |
| Semantic Cache | Query repetition >25% in active workloads | Observed duplicate patterns in logs (sampling) |
| Cost-Aware Routing | Cost differences > quality differences for subset models | Model pricing sheet & prior success parity |
| Retrieval Fusion | Lexical + vector errors partially uncorrelated | Empirical IR research baseline |
| Memory Pruning | Long-tail items rarely retrieved | Access frequency histogram (to collect) |
| Prompt Compression | Summaries preserve intent at chunk level | LLM summarization eval small set |
| KG Augmentation | Entity-rich queries form ≥15% of volume | Preliminary domain analysis |
| Speculative Decoding | Provider supports draft tokens with good acceptance | Vendor roadmap indication |
| NeuralUCB | Non-linear features add incremental predictive power | Literature; unverified internally |

## 6. Post-Rollout Verification Checklist

1. Confirm primary metric effect within Target band (not just above min).
2. Verify no secondary regression (latency, error rate) beyond thresholds.
3. Ensure dashboards updated & documentation of outcome stored (`/reports/outcomes/<feature>.md`).
4. Retrospective: Did observed effect match estimate? Log delta for calibration.
5. Update confidence levels for future forecasting.

## 7. Calibration Feedback Loop

- Maintain accuracy log: (Predicted Target vs Actual) absolute % error.
- After 5 features, compute mean absolute percentage error (MAPE); if MAPE >40%, refine estimation heuristics.

## 8. Future Refinements

- Bayesian A/B framework for continuous monitoring of posterior uplift.
- Drift detection on token cost per model to auto-adjust expected savings.
- Multi-objective optimization (Pareto frontier between cost & quality).

---
Prepared as part of comprehensive review (Performance Estimates phase). Next: Final summary & success criteria.
