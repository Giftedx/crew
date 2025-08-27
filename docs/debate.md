# Multi-Agent Debate

The debate module runs multiple roles in parallel and aggregates their
responses. Each role can be routed to a different model. The simple
`run_panel` helper executes a single round and selects a final answer via
voting.

```python
from debate.panel import PanelConfig, run_panel
from core.router import Router

cfg = PanelConfig(roles=["steelman", "skeptic"])
report = run_panel("Why?", router, call_model, cfg)
print(report.final)
```

Debate sessions can also be triggered via the ops helper:

```python
from discord import commands
res = commands.ops_debate_run("Is this good?", ["steelman", "skeptic"])
print(res["final"])
```
The helper records basic rewards in the reinforcement-learning engine so that
future debates can adapt routing and role weights.
