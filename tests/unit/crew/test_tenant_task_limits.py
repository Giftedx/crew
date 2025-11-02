from __future__ import annotations

from platform.llm.providers.openrouter import OpenRouterService
from typing import TYPE_CHECKING

import yaml

from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


if TYPE_CHECKING:
    from pathlib import Path


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_per_task_limits_enforced(tmp_path: Path) -> None:
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(acme / "routing.yaml", {"models": {"default": "openai/gpt-4"}})
    _write_yaml(acme / "budgets.yaml", {"limits": {"by_task": {"analysis": 0.001, "default": 1.0}}})
    reg = TenantRegistry(tmp_path)
    reg.load()
    meter = TokenMeter(model_prices={"openai/gpt-4": 0.1})
    svc = OpenRouterService(api_key="", tenant_registry=reg, token_meter=meter)
    prompt = "x" * 50000
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route(prompt, task_type="analysis")
    assert res["status"] == "error" and "exceeds" in res["error"]
