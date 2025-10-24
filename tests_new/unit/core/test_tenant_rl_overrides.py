from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from ultimate_discord_intelligence_bot.services.openrouter_service import (
    OpenRouterService,
)
from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


if TYPE_CHECKING:
    from pathlib import Path


class StubEngine:
    def __init__(self) -> None:
        self.updated: list[tuple[str, str, float]] = []

    def select_model(self, task_type: str, candidates: list[str]) -> str:
        return candidates[0]

    def update(self, task_type: str, action: str, reward: float) -> None:
        self.updated.append((task_type, action, reward))


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_tenant_rl_overrides_from_flags(tmp_path: Path) -> None:
    # Create tenant with RL overrides preferring cost weight = 1.0, latency = 0.0
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(
        acme / "flags.yaml",
        {
            "rl": {
                "reward_cost_weight": 1.0,
                "reward_latency_weight": 0.0,
                "reward_latency_ms_window": 2000,
            }
        },
    )

    reg = TenantRegistry(tmp_path)
    reg.load()

    # Token pricing: set to any positive so projected_cost > 0
    meter = TokenMeter(model_prices={"openai/gpt-4": 0.1})
    engine = StubEngine()
    svc = OpenRouterService(
        models_map={"general": ["openai/gpt-4"]},
        learning_engine=engine,
        api_key="",
        tenant_registry=reg,
        token_meter=meter,
    )

    # Long prompt to cause cost>0; with w_cost=1 and denom=projected_cost => cost_norm=1 -> reward near 0
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route("hello world " * 2000)
    assert res["status"] == "success"
    assert engine.updated, "engine not updated"
    _, _, reward = engine.updated[-1]
    assert 0.0 <= reward <= 0.2
