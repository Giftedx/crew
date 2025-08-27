# Reinforcement Learning Overview

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
- **Policies** (`core.rl.policies.bandit_base`) – epsilon‑greedy and UCB1
  bandits with pluggable implementations for routing, prompts and retrieval.
- **Registry** (`core.rl.registry`) – dependency injection for policy
  instances.
- **Shields** (`core.rl.shields`) – enforce budget and latency limits before
  actions execute.

Policies begin in **shadow mode** with conservative priors so learning can only
match or improve deterministic behaviour.

## Feature Flags

Set `ENABLE_RL_GLOBAL=1` together with per‑domain flags such as
`ENABLE_RL_ROUTING=1` or `ENABLE_RL_PROMPT=1` to activate learning. When flags
are off the first candidate executes and policy state is unchanged.
