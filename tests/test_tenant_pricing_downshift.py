from __future__ import annotations

from pathlib import Path

import yaml

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.services.token_meter import TokenMeter
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_pricing_overlay_downshifts_model(tmp_path: Path) -> None:
    # Tenant prefers gpt-4 by default but pricing pushes down to gpt-3.5 under cost cap
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(
        acme / "routing.yaml",
        {"models": {"default": "openai/gpt-4"}, "allowed_models": ["gpt-3.5", "gpt-4"]},
    )
    # Expensive gpt-4, cheap gpt-3.5, strict request cap
    _write_yaml(
        acme / "budgets.yaml",
        {"limits": {"max_per_request": 0.001}, "pricing": {"openai/gpt-4": 0.2, "openai/gpt-3.5": 0.001}},
    )

    reg = TenantRegistry(tmp_path)
    reg.load()

    meter = TokenMeter(model_prices={})  # rely on tenant pricing only
    svc = OpenRouterService(api_key="", tenant_registry=reg, token_meter=meter)

    # Create a prompt whose gpt-4 cost would exceed the cap under tenant pricing
    prompt = "x" * 10000  # ~2500 tokens -> gpt-4 cost ~0.5 under 0.2/1k; above 0.001 cap
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route(prompt)
    assert res["status"] == "success"
    assert res["model"].startswith("openai/gpt-3.5")
