# Reinforcement Learning Overview

The repository includes a minimal bandit-based learning engine located at
`services/learning_engine.py`.  It implements an epsilon-greedy policy that can
be used by any component to adapt decisions based on observed rewards.

## Usage

```python
from ultimate_discord_intelligence_bot.services.learning_engine import LearningEngine

engine = LearningEngine()
engine.register_policy("route.model.select::general", ["model-a", "model-b"])
action = engine.recommend("route.model.select::general")
engine.record_outcome("route.model.select::general", action, reward=1.0)
```

The `OpenRouterService` already employs the learning engine to choose between
candidate models.  As rewards are logged, the engine gradually favours models
with higher estimated value.

The implementation is intentionally lightweight; policies and reward recipes can
be extended in future PRs.
