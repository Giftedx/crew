# Bandit-Based LLM Routing

Adaptive model selection using Thompson Sampling.

## Feature Flag

`ENABLE_BANDIT_ROUTING=1` enables adaptive selection. When disabled, routing deterministically picks the first provided model.

Optional tenant scoping for bandit router reuse & per-tenant state: set `ENABLE_BANDIT_TENANT=1`.

Optional priors:

- `BANDIT_PRIOR_ALPHA` (default 1.0)
- `BANDIT_PRIOR_BETA` (default 1.0)
- `BANDIT_MIN_EPSILON` (default 0.0): Minimum random exploration probability (epsilon-greedy overlay on Thompson output).
- `BANDIT_RESET_ENTROPY_THRESHOLD` (default 0.05): Posterior mean entropy below which a low-entropy step is counted.
- `BANDIT_RESET_ENTROPY_WINDOW` (default 50): Number of consecutive low-entropy steps before automatic posterior reset to priors.

## Components

- `ThompsonBanditRouter`: Maintains Beta posterior per model (arm)
- `LLMRouter`: Wraps multiple `LLMClient` instances and delegates selection to bandit

## Workflow

1. Instantiate `LLMRouter` with a dict `{model_name: LLMClient}`
1. Call `model_name, result = router.chat(messages)`
1. Compute reward (e.g., blended quality metric in [0,1])
1. Call `router.update(model_name, reward)`

## Reward Design

Use a bounded scalar in [0,1]. Suggested composite:

```python
reward = 0.5*quality + 0.3*(1 - latency_norm) + 0.2*(1 - cost_norm)
```

Apply per-tenant weights if needed before passing to `router.update`.

## Persistence

Current implementation keeps in-memory posteriors only. Future enhancement: periodic snapshot + restore via a simple JSON file keyed by tenant.

### (Implemented) Optional JSON Persistence

Enable with:

`ENABLE_BANDIT_PERSIST=1`

Environment variables:

- `BANDIT_STATE_DIR` (default `./bandit_state`): Directory for a `bandit_state.json` file.

Behavior:

1. On initialization, router attempts to load existing JSON (if present) and applies per-arm alpha/beta.
1. After each `update`, state is serialized (best-effort) via atomic temp file replace.
1. Failures to load/save are silently ignored (defensive) to avoid impacting routing.

Schema example:

```json
{
 "gpt4": {"alpha": 12.4, "beta": 7.6},
 "haiku": {"alpha": 5.0, "beta": 11.0}
}
```

No tenant scoping is built-in yet; for multi-tenant operation provide distinct `BANDIT_STATE_DIR` per tenant (or extend file naming convention).

## Metrics

If the metrics subsystem is available, the following counters are emitted:

- `bandit_router_selections_total{arm,mode}`: Counts selections (mode is `deterministic` or `thompson`).
- `bandit_router_reward_total{arm}`: Accumulates fractional reward mass applied.
- `bandit_router_updates_total{arm}`: Number of posterior updates per arm.
- `llm_router_chats_total{model}`: Number of routed chat invocations per model.
- `bandit_router_selection_entropy`: Shannon entropy (nats) of selection distribution (higher = more exploration / balance). (No tenant/workspace labels to avoid high cardinality.)
- `bandit_router_posterior_mean_entropy`: Entropy of normalized expected success probabilities derived from per-arm Beta posterior means (captures informational uncertainty distinct from empirical selection spread).

Use these to build dashboards: selection share, reward per arm, exploration effectiveness (posterior entropy proxy), and drift detection (sudden selection skew).

## Testing

See `tests/test_bandit_router.py` for:

- Deterministic fallback when flag disabled
- Bias toward higher reward arm after updates

## Future Enhancements

1. LinUCB / contextual extensions with numeric feature vectors
1. Per-tenant isolated router instances inside a registry
1. Cold-start seeding from static performance heuristics
1. Metrics (selection counts, posterior entropy)

## Tenant-Scoped Router Registry (Implemented)

Module: `ai.routing.router_registry`

Helpers:

1. `get_tenant_router()` returns a `ThompsonBanditRouter` whose state file name encodes tenant & workspace.
1. `record_selection(model)` records a selection for entropy tracking (entropy gauge is global, no labels).
1. `compute_selection_entropy()` returns current Shannon entropy for that tenant.

## Convenience: chat_and_update

`LLMRouter.chat_and_update(messages, quality, latency_ms, cost)`

Performs routing, invokes the selected model, computes a normalized reward via `RewardNormalizer`, updates the bandit, and returns `(model_name, result, reward)`.

State file naming pattern: `bandit_state__<tenant>__<workspace>.json`

If no tenant context is active, a global fallback key `_global` is used.

## Reward Normalization Utility (Implemented)

Class: `RewardNormalizer`

Purpose: Convert raw (quality, latency_ms, cost) triplets into a bounded [0,1] reward using EMAs for latency & cost baselines.

Formula (after normalization):

```python
reward = 0.5 * quality + 0.3 * (1 - latency_norm) + 0.2 * (1 - cost_norm)
```

Where `latency_norm` and `cost_norm` are relative to double their EMA (clamped to [0,1]) to soften early variance.

Usage outline:

```python
normalizer = RewardNormalizer()
reward = normalizer.compute(quality=0.9, latency_ms=320, cost=0.004)
router.update(model_name, reward)
```

## Posterior Mean Entropy (Implemented)

Two notions of exploration health:

1. Selection entropy (`bandit_router_selection_entropy`): Empirical distribution of chosen arms.
1. Posterior mean entropy (`bandit_router_posterior_mean_entropy`): Entropy over normalized posterior mean success probabilities (alpha/(alpha+beta)). Higher values indicate the model still perceives arms as similarly promising; a decreasing trajectory suggests convergence.

Operational guidance:

- Sustained low selection entropy + low posterior entropy may signal exploitation lock-in; consider forced exploration or resetting priors.
- High selection entropy + very low posterior entropy may indicate noise / reward instability (investigate reward signal quality).

## Selection Count Persistence (Implemented)

When `ENABLE_BANDIT_PERSIST=1`, selection counts are also persisted to `selection_counts.json` alongside posterior state. This enables continuity of empirical exploration metrics across restarts.

File locations:

- Posterior state: `bandit_state.json` (or tenant-scoped names via registry)
- Selection counts: `selection_counts.json`

Both use atomic temp-file replace semantics and silently ignore load errors for resilience.

## Forced Exploration & Automatic Reset (Implemented)

Epsilon-Greedy Overlay:

- Controlled by `BANDIT_MIN_EPSILON`; when > 0 a random non-argmax arm is chosen with probability epsilon (if more than one arm available).
- Metric: `bandit_router_forced_explorations_total{arm}` increments on forced exploration selections.

Automatic Posterior Reset:

If posterior mean entropy stays below `BANDIT_RESET_ENTROPY_THRESHOLD` for `BANDIT_RESET_ENTROPY_WINDOW` consecutive updates, all arms are reset to prior (α=prior_alpha, β=prior_beta).

Metrics:

- `bandit_router_resets_total` increments each reset.

Operational Tips:

- Use a modest epsilon (e.g., 0.02–0.05) if selection entropy declines prematurely.
- Tune threshold upward (e.g., 0.15) temporarily to force earlier resets during initial experimentation.

## Contextual Bandit (LinUCB) (Implemented)

Enable with:

`ENABLE_CONTEXTUAL_BANDIT=1`

Required:

- `LINUCB_DIMENSION` (positive int): Feature vector dimension.

Optional:

- `LINUCB_ALPHA` (default 0.8): Exploration scaling factor in confidence term.

API Additions (when contextual mode enabled):

- `chat_with_features(messages, features)` -> `(model, result)`
- `update_with_features(model, reward, features)`
- `chat_with_features_and_update(messages, features, quality, latency_ms, cost)` convenience wrapper.

Feature Vector Guidance:

Design a stable, bounded feature vector capturing request attributes. Example components:

1. Normalized estimated output length
1. Recent latency EMA per model (difference or ratio)
1. Cost budget remaining fraction
1. Domain/task embedding bucket (one-hot or low-d hash)
1. User tier / SLA level indicator

Mapping quality to reward: reuse `RewardNormalizer` (quality, latency, cost) then pass reward to `update_with_features`.

Fallback Behavior:

If contextual flag disabled, classic Thompson (with optional tenant scoping) is used; contextual APIs raise errors.

### LinUCB Persistence (Implemented)

LinUCB state (per-arm A matrix and b vector) is snapshotted when `ENABLE_BANDIT_PERSIST=1` to:

`linucb_d<dimension>.json` within `BANDIT_STATE_DIR`.

Schema example:

```json
{
  "gpt4": {"A": [[1.5, 0.1],[0.1,1.3]], "b": [0.9, 0.4]},
  "haiku": {"A": [[1.2, 0.0],[0.0,1.1]], "b": [0.3, 0.1]}
}
```

Notes:

1. Load failures are ignored (resumes with fresh priors).
1. Matrix inversion cost grows cubically with dimension; keep `LINUCB_DIMENSION` modest (< 64) unless optimized.
1. Consider periodic pruning of stale arms (not yet implemented).

### LinUCB Performance Optimization (Implemented)

The LinUCB router maintains a cached inverse `A_inv` per arm and applies a Sherman–Morrison
rank-1 update on each observation:

`(A + x x^T)^{-1} = A_inv - (A_inv x x^T A_inv) / (1 + x^T A_inv x)`

Env variable:

- `LINUCB_RECOMPUTE_INTERVAL` (default 0 = disabled): When > 0, triggers a full recomputation of `A_inv` every N updates per arm to mitigate numerical drift.

Additional metrics:

- `linucb_recomputes_total` counts forced full inverse rebuilds.

Guidelines:

1. If dimension <= 32 and update rate is modest, interval can remain 0 (only rank-1 updates).
1. For higher dimensions or very long lifetimes, set interval (e.g., 250–500) to bound error accumulation.
1. Monitor divergence by spot-checking score parity against a periodic offline recompute (provided by test parity example).

### Hybrid Contextual Fallback & Stability Monitoring (Implemented)

Two production hardening features enhance contextual routing resilience.

#### 1. Hybrid Fallback

Environment:

- `ENABLE_CONTEXTUAL_HYBRID` (default `1` / enabled). When on and `ENABLE_CONTEXTUAL_BANDIT=1`, the router will transparently
  fallback to the classic Thompson bandit when feature vectors are missing or have the wrong dimensionality.

Behavior:

1. `chat_with_features(...)` attempts contextual selection; on feature length mismatch it routes via Thompson sampling.
1. `update_with_features(...)` similarly falls back—reward updates the classic bandit when features invalid.
1. Metrics: `llm_router_fallback_total{reason}` increments for each fallback (`feature_unavailable`, `update_feature_unavailable`).

Operational Benefits:

- Prevents request drops or exceptions if upstream feature generation service is degraded.
- Allows gradual rollout of feature computation (some requests contextual, others classic) without flipping global flags.

#### 2. Condition Number Monitoring

Environment:

- `LINUCB_COND_THRESHOLD` (default `0` = disabled). When > 0, after each LinUCB update the router estimates an inexpensive
  condition number approximation using `||A||_inf * ||A^{-1}||_inf`. If the estimate exceeds the threshold a full inverse
  recompute is performed immediately (emits the existing `linucb_recomputes_total` counter with `reason="cond_threshold"`).

Metric:

- `linucb_condition_number{arm}` gauge records last observed condition estimate per arm.

Guidelines:

1. Start with threshold 0 (disabled) unless you observe numerical instability (e.g., divergence from offline inverse comparisons).
1. For moderately sized dimensions (<= 32) and stable feature scaling you often do not need this; rely on periodic recompute interval instead.
1. If enabling, choose a threshold empirically (e.g., 1e5–1e7) after logging observed healthy ranges.
1. Large spikes may indicate poorly scaled or near-collinear features; consider feature normalization or dimensionality reduction.

Failure Modes Addressed:

- Runaway inverse drift due to accumulated floating-point error in repeated rank-1 updates.
- Feature pipeline intermittently emitting wrong length vectors causing hard exceptions (now softened by fallback).

Testing:

- `test_llm_router_hybrid.py` covers fallback activation on dimension mismatch and normal contextual path.
- `test_linucb_condition_threshold.py` exercises threshold-triggered recompute logic for near-collinear updates (sanity path).

Future Hardening Ideas:

1. Dynamic feature scaling / whitening with online covariance tracking.
1. Arm pruning based on low selection probability & high condition number contribution.
1. Multi-armed hybrid (choose contextual vs non-contextual per-request based on feature quality scores).

### Feature Quality Gating (Implemented)

Objective: Avoid poisoning contextual learning or incurring unstable score computations when feature vectors are malformed or poorly scaled.

Environment Variables:

- `FEATURE_QUALITY_MIN` (default 0.5): Minimum acceptable quality score; below triggers fallback (if hybrid enabled).
- `FEATURE_MIN_NORM` (default 0.0): Expected lower bound on L2 norm; values below incur proportional penalty.
- `FEATURE_MAX_NORM` (default 10.0): Upper bound; exceeding incurs proportional penalty.

Heuristic Scoring (score ∈ [0,1]):

1. Dimension mismatch or None ⇒ score = 0.
1. Any NaN/Inf / non-numeric element ⇒ multiplicative 0.7 penalty.
1. L2 norm outside [min_norm, max_norm] ⇒ multiplicative penalty up to 0.5 (scaled by distance beyond bound).

Metrics:

- `linucb_feature_quality` gauge: last computed feature quality per request (no labels) for aggregate distribution tracking.
- Fallbacks due to low quality recorded in `llm_router_fallback_total{reason="low_quality"}`.

Usage Guidance:

1. Start with a moderate `FEATURE_QUALITY_MIN` (0.5–0.7). Raise after observing stable feature stats.
1. Set tighter norm bounds once feature scaling is standardized; broad bounds reduce false fallbacks early.
1. Watch distribution of `linucb_feature_quality` (e.g., p50/p95) — if clustering near 1.0, consider increasing threshold to enforce stricter hygiene.
1. Sudden drops in median quality may indicate upstream feature extraction regression.

Limitations / Future Improvements:

1. Current score doesn't inspect covariance structure; adding whitening-based Mahalanobis checks could refine penalties.
1. Could incorporate per-dimension clip counts to surface systematic saturation.
1. Automatic adaptive thresholding (e.g., threshold = p10 - margin) for self-tuning gating.
