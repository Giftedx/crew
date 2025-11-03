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


def test_pricing_overlay_downshifts_model(tmp_path: Path) -> None:
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(
        acme / "routing.yaml", {"models": {"default": "openai/gpt-4"}, "allowed_models": ["gpt-4o-mini", "gpt-4"]}
    )
    _write_yaml(
        acme / "budgets.yaml",
        {"limits": {"max_per_request": 0.01}, "pricing": {"openai/gpt-4": 0.03, "openai/gpt-4o-mini": 0.00015}},
    )
    reg = TenantRegistry(tmp_path)
    reg.load()
    meter = TokenMeter(model_prices={})
    svc = OpenRouterService(api_key="", tenant_registry=reg, token_meter=meter)
    prompt = "x" * 10000
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route(prompt)
    assert res["status"] == "success"
    assert res["model"].startswith("openai/gpt-4o-mini")
