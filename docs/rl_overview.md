# Reinforcement Learning Overview

**Current Implementation** (verified November 3, 2025):

- **Primary Policy**: `LinUCBDiagBandit` in `src/platform/rl/core/policies/linucb.py` (154 lines)
- **RL Layer**: `src/platform/rl/` (contextual bandits for LLM routing)
- **Integration**: Active in LLM provider selection and model routing
- **Feature Flags**: `ENABLE_TRAJECTORY_EVALUATION`, `ENABLE_TRAJECTORY_FEEDBACK_LOOP`

The system learns from usage to improve model routing, prompting and retrieval
while respecting safety, cost and latency constraints.

## Stack Components

- **Feature Store** (`core.rl.feature_store`) – extracts numeric context and
  tracks sliding averages for cost and latency.
- **Reward Engine** (`core.rl.reward_engine`) – combines quality,
  groundedness, cost, latency and safety into a weighted scalar reward.
- **Reward Pipe** (`core.reward_pipe`) – collects raw signals for a decision
  domain and returns a `RewardResult` used for logging and updates.
- **Learn Helper** (`core.learn`) – runs the recommend → act → reward loop
  using the registered policy and reward pipeline.
- **Policies** (`core.rl.policies.bandit_base`) – epsilon‑greedy, UCB1, and
  Thompson Sampling bandits with pluggable implementations for routing,
  prompts and retrieval. Policies accept an optional RNG for deterministic
  tests without affecting production behaviour.
- **Registry** (`core.rl.registry`) – dependency injection for policy
  instances.
- **Shields** (`core.rl.shields`) – enforce budget and latency limits before
  actions execute.

Policies begin in **shadow mode** with conservative priors so learning can only
match or improve deterministic behaviour. Domains currently wired include
model routing, prompt selection, retrieval scoring, **tool planning** and the
**plugin runtime** which adjusts execution budgets for sandboxed extensions.

## Operations

The learning engine supports basic operational controls:

- **Snapshots** – ``LearningEngine.snapshot()`` returns a serialisable mapping
  of policy state. Policies expose ``state_dict()``/``load_state()`` for richer
  persistence (e.g. UCB1 ``total_pulls``, Thompson Sampling Beta parameters).
  Persist the snapshot to create a checkpoint.
- **Restore** – pass a snapshot to ``LearningEngine.restore()`` to roll back to
  the saved state.
- **Status** – ``LearningEngine.status()`` exposes the current policies and
  arm statistics for debugging and monitoring.

### Example: Snapshot and Restore

```python
import random
from core.learning_engine import LearningEngine
from core.rl.policies.bandit_base import ThompsonSamplingBandit
from core.rl.registry import PolicyRegistry

rng = random.Random(42)  # deterministic recommend()
reg = PolicyRegistry()
eng = LearningEngine(reg)
eng.register_domain("route", policy=ThompsonSamplingBandit(rng=rng))

# ... learning occurs ...
snap = eng.snapshot()

# Later
eng2 = LearningEngine(PolicyRegistry())
eng2.register_domain("route", policy=ThompsonSamplingBandit(rng=random.Random(42)))
eng2.restore(snap)
assert eng2.recommend("route", {}, ["a", "b"]) in ("a", "b")
```

### Operational CLI: rl_snapshot

An operational CLI is provided for exporting and importing RL state without writing custom Python scripts.

Dump current learning state to a JSON file:

```bash
rl_snapshot dump \
  --tenant default \
  --workspace main \
  --output /tmp/rl_state.json
```

Restore from a previously saved snapshot:

```bash
rl_snapshot restore \
  --tenant default \
  --workspace main \
  --input /tmp/rl_state.json
```

Options:

- `--policies route,prompt` limit to a subset (defaults to all registered domains)
- `--verbose` emit per‑policy diagnostics to stderr

Snapshot Safety:

- Includes RNG seeds where policies expose them so restored exploration remains reproducible in tests.
- Unknown domains in the snapshot are ignored; missing domains retain their fresh initialisation.
- A `version` field per policy (future‑facing) enables schema evolution; mismatches are skipped gracefully.

Recommended Practice: take periodic (e.g. hourly or daily) snapshots when rolling out major prompt/routing changes to allow rapid rollback if reward regressions are detected.

## Feature Flags

Set `ENABLE_RL_GLOBAL=1` together with per‑domain flags such as
`ENABLE_RL_ROUTING=1` or `ENABLE_RL_PROMPT=1` to activate learning. When flags
are off the first candidate executes and policy state is unchanged.
