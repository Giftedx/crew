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


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_budget_limit_blocks_expensive_prompt(tmp_path: Path) -> None:
    # Create tenant with strict per-request limit
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(acme / "routing.yaml", {"models": {"default": "openai/gpt-4"}})
    _write_yaml(acme / "budgets.yaml", {"limits": {"max_per_request": 0.001}})

    reg = TenantRegistry(tmp_path)
    reg.load()

    # Model pricing: make gpt-4 expensive enough for a long prompt
    meter = TokenMeter(model_prices={"openai/gpt-4": 0.1})
    svc = OpenRouterService(api_key="", tenant_registry=reg, token_meter=meter)

    # Build a long prompt to exceed cost threshold
    prompt = "x" * 100000  # ~25k tokens under heuristic -> ~$10 cost at 0.1/1k
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route(prompt, task_type="analysis")
    assert res["status"] == "error"
    assert "exceeds" in res["error"]
