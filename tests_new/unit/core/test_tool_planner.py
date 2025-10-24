from __future__ import annotations

from core import rl
from ultimate_discord_intelligence_bot.core.rl.policies.bandit_base import (
    EpsilonGreedyBandit,
)
from ultimate_discord_intelligence_bot.core.tool_planner import execute_plan


def test_tool_planner_bandit_updates(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_RL_GLOBAL", "1")
    monkeypatch.setenv("ENABLE_RL_TOOL_PLANNING", "1")
    reg = rl.registry.PolicyRegistry()
    policy = EpsilonGreedyBandit(epsilon=0.0)
    reg.register("tool_planning", policy)

    def fast_tool():
        return {"cost_usd": 0.1, "latency_ms": 10}, {"success": 1.0}

    def slow_tool():
        return {"cost_usd": 0.2, "latency_ms": 20}, {"success": 1.0}

    plans = {"fast": [fast_tool], "slow": [slow_tool]}
    execute_plan(plans, {"task": "demo"}, policy_registry=reg)
    assert policy.counts["fast"] == 1
    rl.feature_store._cost_usd_history.clear()
    rl.feature_store._latency_history.clear()
