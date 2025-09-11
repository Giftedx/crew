# Prioritized Recommendations

Ordering reflects weighted feasibility scores plus dependency / leverage adjustments (see `feasibility_matrix.md`).

Legend of Categories:

- Quick Win: < 1 week
- Strategic: 1–4 weeks
- Deferred / Advanced: > 1 month or requires prior foundations

---

### 1. LinTS Bandit Policy

Category: Quick Win
Weighted Score: 4.70
Adjusted Priority Rationale: Highest score; immediate uplift in exploration quality with minimal code.
Flag: `ENABLE_RL_LINTS`
Rationale: Improves routing decision efficiency vs epsilon-greedy by leveraging posterior uncertainty.
Key Metrics:

- `rl_model_selection_reward{policy="LinTS"}`
- `rl_regret_total` (should trend down vs baseline)
- `routing_latency_ms` (no regression >5%)
Success Criteria:
- ≥3% improvement in average reward over 7-day rolling window
- No significant latency increase (p<0.05 test)
- Snapshot/restore works with new policy
Rollout Phases:
- Flag (off): implement & unit test posterior updates
- Shadow: run LinTS in parallel, log decisions (no effect)
- Canary: 10% of routing domains adopt LinTS
- Full: 100% after stable metrics 72h
Code Snippet:

```python
from core.flags import enabled
from core.learning_engine import LearningEngine

if enabled("ENABLE_RL_LINTS"):
    from core.rl.policies.lints import LinTS  # new module
    LearningEngine.register_policy("lints", LinTS)
```

Risks & Mitigations:

- Mis-specified priors → start with conservative variance
- Reward logging drift → add schema assertion in `record`
Dependencies:
- Existing reward pipeline only

---

### 2. Experiment A/B Harness & Dashboard

Category: Strategic
Weighted Score: 4.45
Adjusted Priority Rationale: Moved earlier to unlock validated measurement for subsequent optimizations.
Flag: `ENABLE_EXPERIMENT_HARNESS`
Rationale: Standardizes statistical comparison and reduces ad-hoc metric divergence.
Key Metrics:

- `exp_active_variants`
- `exp_sample_size{variant=...}`
- `exp_metric_diff{metric="reward"}`
Success Criteria:
- Ability to launch experiment with single config entry
- Automated power estimation & early stop rule implemented
Rollout Phases:
- Flag: Introduce allocator (no experiments)
- Shadow: Log hypothetical assignments
- Canary: First live experiment (LinTS vs baseline)
- Full: Template docs & Grafana panels published
Code Snippet:

```python
from core.flags import enabled

def choose_variant(key: str, variants: list[str]) -> str:
    if not enabled("ENABLE_EXPERIMENT_HARNESS"):
        return variants[0]
    # simple hash allocator (replace with stratified logic later)
    import hashlib
    h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
    return variants[h % len(variants)]
```

Risks & Mitigations:

- Metric cardinality → restrict variant labels set
- Biased assignment → plan stratification in v2
Dependencies:
- Metrics subsystem, Grafana provisioning

---

### 3. Dynamic Context Trimming

Category: Quick Win
Weighted Score: 4.65
Adjusted Priority Rationale: Slightly delayed to ensure A/B framework measures impact.
Flag: `ENABLE_CONTEXT_TRIMMING`
Rationale: Reduces token cost and tail latency by trimming low-salience context safely.
Key Metrics:

- `context_tokens_before` / `context_tokens_after`
- `trimming_ratio`
- `llm_latency_ms`
Success Criteria:
- ≥15% median context reduction with ≤1% drop in answer relevance (MAP@n)
Rollout Phases: Flag → Shadow (diff log) → Canary (10%) → Full
Code Snippet:

```python
from core.flags import enabled

def trim_context(chunks, max_tokens):
    if not enabled("ENABLE_CONTEXT_TRIMMING"):
        return chunks
    # naive heuristic: keep top-N by recency & semantic score
    sorted_chunks = sorted(chunks, key=lambda c: (c.score, c.recency), reverse=True)
    total = 0; kept = []
    for c in sorted_chunks:
        if total + c.tokens > max_tokens: break
        kept.append(c); total += c.tokens
    return kept
```

Risks & Mitigations:

- Over-trimming → monitor relevance delta
Dependencies:
- Access to per-chunk token counts & scores

---

### 4. Semantic Cache

Category: Strategic
Weighted Score: 4.40
Flag: `ENABLE_SEMANTIC_CACHE`
Rationale: Avoids redundant LLM calls for semantically equivalent queries.
Key Metrics:

- `semantic_cache_hit_ratio`
- `cache_latency_ms`
- `cost_per_success`
Success Criteria:
- ≥25% hit ratio on repeated queries after warm-up
- ≤5ms median cache lookup latency
Rollout Phases: Flag → Shadow (measure potential hits) → Canary (serve cached responses) → Full
Code Snippet:

```python
from core.flags import enabled
from memory.vector_store import VectorStore

_cache_ns = VectorStore.namespace("semantic", tenant, workspace)

def semantic_lookup(embedding, threshold=0.90):
    if not enabled("ENABLE_SEMANTIC_CACHE"):
        return None
    matches = vector_store.search(_cache_ns, embedding, limit=3)
    if matches and matches[0].score >= threshold:
        return matches[0].payload.get("response")
    return None
```

Risks & Mitigations:

- Stale answers → add TTL or freshness score
Dependencies:
- Embedding pipeline, vector_store

---

### 5. Adaptive Cost-Aware Routing

Category: Strategic
Weighted Score: 4.45
Flag: `ENABLE_COST_AWARE_ROUTING`
Rationale: Minimizes cost per successful task by factoring price & historical success.
Key Metrics:

- `cost_per_success`
- `model_selection_utility`
Success Criteria:
- ≥10% reduction in cost_per_success with neutral or improved success rate
Rollout Phases: Flag → Shadow scoring → Canary multi-model domains → Full
Code Snippet:

```python
if enabled("ENABLE_COST_AWARE_ROUTING"):
    utility = reward_estimate / max(1e-6, model_cost) * latency_weight
else:
    utility = reward_estimate
```

Risks & Mitigations:

- Overweight cheap low-quality models → enforce minimum quality floor
Dependencies:
- Existing model metadata (cost, latency)

---

### 6. Retrieval Fusion

Category: Strategic
Weighted Score: 4.35
Flag: `ENABLE_MEMORY_FUSION`
Rationale: Improves retrieval accuracy by combining lexical, vector, and (later) graph signals.
Key Metrics:

- `fusion_gain_at_k`
- `retrieval_latency_ms`
Success Criteria:
- ≥5 point nDCG@10 uplift vs vector-only in A/B
Rollout Phases: Flag → Shadow (compute fusion scores only) → Canary → Full
Code Snippet:

```python
if enabled("ENABLE_MEMORY_FUSION"):
    # simple linear blend; weights tunable
    score = 0.5*vec_score + 0.3*lex_score + 0.2*meta_score
else:
    score = vec_score
```

Risks & Mitigations:

- Latency inflation → cap lexical doc count
Dependencies:
- Lexical scorer implementation

---

### 7. Memory Pruning & Summarization

Category: Strategic
Weighted Score: 4.15
Flag: `ENABLE_MEMORY_PRUNE`
Rationale: Controls vector store growth and improves retrieval signal density.
Key Metrics:

- `memory_pruned_items`
- `memory_summarization_events`
Success Criteria:
- ≤5% retrieval relevance regression while reducing storage growth ≥30%
Rollout Phases: Flag (dry-run) → Shadow (log candidates) → Canary (prune subset) → Full
Code Snippet:

```python
if enabled("ENABLE_MEMORY_PRUNE"):
    # pseudo scheduling
    for item in candidates:
        if item.decay_score < THRESH:
            archive(item)
```

Risks & Mitigations:

- Accidental loss of critical memory → pin/whitelist support
Dependencies:
- Usage & recency metrics

---

### 8. Prompt Compression (Hierarchical)

Category: Strategic
Weighted Score: 3.95
Flag: `ENABLE_PROMPT_COMPRESSION`
Rationale: Reduces context size with multi-level summarization.
Key Metrics:

- `compression_ratio`
- `answer_relevance_delta`
Success Criteria:
- ≥30% token reduction with <2% relevance loss
Rollout Phases: Flag → Shadow (simulate compressed prompts) → Canary → Full
Code Snippet:

```python
if enabled("ENABLE_PROMPT_COMPRESSION") and total_tokens > limit:
    summary = summarize_blocks(blocks)
    blocks = [summary] + tail_blocks
```

Risks & Mitigations:

- Summarization drift → periodic quality sampling
Dependencies:
- Summarizer model or existing LLM

---

### 9. Bootstrapped UCB Policy

Category: Strategic
Weighted Score: 3.95
Flag: `ENABLE_RL_BOOTSTRAPPED_UCB`
Rationale: Adds ensemble uncertainty exploration alternative after LinTS.
Key Metrics:

- `rl_model_selection_reward{policy="BootstrappedUCB"}`
- `rl_ensemble_variance`
Success Criteria:
- On at least one domain: reward ≥ LinTS within CI, or improved exploration variance
Rollout Phases: Flag → Shadow → Canary (single domain) → Full (optional)
Code Snippet:

```python
if enabled("ENABLE_RL_BOOTSTRAPPED_UCB"):
    engine.register_policy("boot_ucb", BootstrappedUCB(heads=5))
```

Risks & Mitigations:

- Higher compute per selection → cap ensemble size
Dependencies:
- LinTS baseline data

---

### 10. Knowledge Graph Retrieval Augmentation

Category: Deferred
Weighted Score: 3.35
Flag: `ENABLE_KG_AUGMENT`
Rationale: Injects structured entity relations into context for complex queries.
Key Metrics:

- `kg_lookup_latency_ms`
- `kg_augmented_context_ratio`
Success Criteria:
- ≥3 point improvement nDCG@10 on entity-heavy queries
Rollout Phases: Flag → Shadow (log potential enrichments) → Canary → Full
Code Snippet:

```python
if enabled("ENABLE_KG_AUGMENT"):
    facts = kg.lookup(entities)
    context.extend(facts)
```

Risks & Mitigations:

- Hallucination amplification → confidence gating
Dependencies:
- Entity extraction & KG store

---

### 11. Speculative Decoding

Category: Deferred
Weighted Score: 3.05
Flag: `ENABLE_SPECULATIVE_DECODING`
Rationale: Potential latency reduction where provider supports draft tokens.
Key Metrics:

- `llm_speculative_speedup`
- `draft_acceptance_rate`
Success Criteria:
- ≥15% p95 latency reduction with ≤1% quality loss
Rollout Phases: Flag → Shadow (capture provider capability) → Canary → Full
Code Snippet:

```python
if enabled("ENABLE_SPECULATIVE_DECODING"):
    draft, meta = provider.draft(prompt)
    final = provider.verify(prompt, draft)
```

Risks & Mitigations:

- Provider API instability → capability check on startup
Dependencies:
- Provider feature support

---

### 12. NeuralUCB (Experimental)

Category: Deferred / Advanced
Weighted Score: 3.05
Flag: `ENABLE_RL_NEURALUCB`
Rationale: Non-linear contextual policy for long-term exploration gains.
Key Metrics:

- `rl_training_time_ms`
- `rl_model_selection_reward{policy="NeuralUCB"}`
Success Criteria:
- Offline eval shows ≥5% reward improvement vs LinTS before production
Rollout Phases: Flag (disabled) → Offline training harness → Shadow online inference → Canary
Code Snippet:

```python
if enabled("ENABLE_RL_NEURALUCB"):
    engine.register_policy("neural_ucb", NeuralUCB(model, alpha=0.1))
```

Risks & Mitigations:

- Training instability → early stopping and gradient clipping
Dependencies:
- Torch runtime, feature vector pipeline

---

## Cross-Cutting Implementation Notes

- All features gated by flags following existing pattern (`core.flags.enabled`).
- Shadow phases must emit metrics with variant labels but avoid altering user-facing outputs.
- Canary gates require: (a) stable latency (b) no error spike (c) metric uplift within predefined threshold.

## Summary

Early focus: Measurement + low-risk efficiency (LinTS, A/B Harness, Trimming, Semantic Cache) to produce rapid cost and quality wins while enabling data-driven validation for deeper retrieval and memory lifecycle changes.
