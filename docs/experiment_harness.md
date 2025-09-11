# Experiment Harness & Contextual Bandit Extensions

## Overview

The experiment harness enables controlled, feature-flagged online experimentation for model & policy routing decisions. It sits in front of the `LearningEngine` bandit policies and can transparently:

* Allocate traffic deterministically to variants (e.g. different bandit policies or parameterizations) using a stable hash of `(domain, key, variant_id)`.
* Run in SHADOW mode (collect metrics only) or ACTIVE mode (influence recommendations) to de‑risk rollouts.
* Record per‑variant statistics (pulls, reward_sum, mean_reward, regret_sum) for lightweight evaluation without external infra.

Two new flags gate functionality:

| Flag | Purpose |
|------|---------|
| `ENABLE_EXPERIMENT_HARNESS` | Globally enable experiment manager wrapping `LearningEngine`. |
| `ENABLE_RL_LINTS` | Enable the Linear Thompson Sampling (diagonal covariance) policy as a selectable option. |

Related observability: existing RL selection metrics (e.g. counts per chosen model) continue to function; variant stats are stored in‑memory (process lifetime) and can be surfaced via future admin/report endpoints.

## Variant Allocation

Deterministic allocation prevents user/session flapping.

1. A stable hash is computed from an identifier (often the routing domain + candidate model set + optional user key).
1. The hash is modulo'd by the sum of variant weights.
1. Cumulative bucket boundaries assign a single variant id.

This ensures:

* Reproducible splits across process restarts (given consistent inputs).
* Simple reweighting by adjusting per‑variant weight config.

## Shadow vs Active Phases

| Phase | Behavior |
|-------|----------|
| SHADOW | Core policy decides; all variants receive synthetic "would have been pulled" accounting plus optional counterfactual regret tracking. |
| ACTIVE | Chosen variant's policy output is used for actual routing decisions. Non‑chosen variants still collect counterfactual stats for evaluation. |

Migration path: start SHADOW → validate no regressions → flip to ACTIVE for gradual traffic ramp.

## Linear Thompson Sampling (LinTS Diagonal)

Enabled by `ENABLE_RL_LINTS` the `LinTSDiagPolicy` maintains per‑arm feature mean & variance estimates assuming diagonal covariance for efficiency.

Characteristics:

* O(d) update per pull (d = feature dimension).
* Naturally balances exploration vs exploitation via sampled parameter vectors.
* Suitable when contextual feature vectors are moderately sized and feature independence is an acceptable approximation.

Fallback: If the flag is disabled, existing policies (epsilon greedy, UCB1, standard Thompson) remain available unchanged.

## Minimal Usage Flow

```python
from core.learning_engine import LearningEngine

# Normally constructed inside services (e.g. OpenRouterService)
engine = LearningEngine()

# Recommendation (domain = routing task, candidates = model list)
model = engine.select_model("analysis", ["modelA", "modelB", "modelC"])  # harness may interpose

# After serving the response, a reward is computed (e.g. cost-normalized latency)
engine.record_outcome("analysis", model, reward=0.72)
```

Environment variables (or settings) control harness activation and LinTS availability:

```bash
export ENABLE_EXPERIMENT_HARNESS=1
export ENABLE_RL_LINTS=1  # optionally enable LinTS policy
```

## Reward Shape Guidance

A composite reward (latency, cost, success quality proxy) is recommended. Current defaults:

* `reward_cost_weight`
* `reward_latency_weight`
* `reward_latency_ms_window`

Weights are applied to normalized components prior to bandit update; tune cautiously to avoid destabilizing selection.

## Safety & Determinism Principles

* Deterministic hashing ensures stable variants.
* Shadow-first rollout avoids live traffic influence until validated.
* Feature flags provide instant disable path.
* No external state writes: all experiment accounting in-process (stateless horizontally; future work: external aggregation via metrics or snapshotting).

## Future Extensions (Roadmap)

* Persistent variant stats export (Prometheus gauges or periodic snapshot).
* Automatic early stopping (statistical confidence check).
* Multi-objective Pareto frontier exploration.
* Per-tenant experiment segmentation.

## Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| No variant stats changing | Harness disabled | Set `ENABLE_EXPERIMENT_HARNESS=1` and restart process. |
| LinTS never selected | `ENABLE_RL_LINTS` off or policy not chosen for domain | Enable flag; ensure domain policy configuration references LinTS variant. |
| High regret accumulation | Poor exploration balance or mis-specified reward weights | Revisit reward scaling; validate latency window & cost weight. |

---

Last updated: (auto) – add to feature flag docs digest if required.
