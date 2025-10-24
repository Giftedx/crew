from __future__ import annotations

import pathlib

from core import rl
from ultimate_discord_intelligence_bot.core.rl.policies.bandit_base import (
    EpsilonGreedyBandit,
)
from ultimate_discord_intelligence_bot.plugins.runtime.executor import PluginExecutor


class DummyLLM:
    def generate(self, text: str) -> str:  # pragma: no cover - trivial
        return f"summary:{text[:5]}"


def test_plugin_executor_rl_updates(monkeypatch, tmp_path: pathlib.Path) -> None:
    monkeypatch.setenv("ENABLE_RL_GLOBAL", "1")
    monkeypatch.setenv("ENABLE_RL_PLUGIN", "1")

    plugin_dir = pathlib.Path("src/ultimate_discord_intelligence_bot/plugins/example_summarizer")
    schema = pathlib.Path("src/ultimate_discord_intelligence_bot/plugins/manifest.schema.json")
    executor = PluginExecutor(schema)
    reg = rl.registry.PolicyRegistry()
    policy = EpsilonGreedyBandit(epsilon=0.0)
    reg.register("plugin", policy)

    result = executor.run(
        plugin_dir,
        granted_scopes={"llm.call"},
        adapters={"svc_llm": DummyLLM()},
        args={"text": "hello world"},
        policy_registry=reg,
    )
    assert result.success, result.error
    assert sum(policy.counts.values()) == 1
    rl.feature_store._cost_usd_history.clear()
    rl.feature_store._latency_history.clear()
