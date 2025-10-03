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
    # Tenant prefers gpt-4 by default but pricing pushes down to gpt-4o-mini under cost cap
    acme = tmp_path / "acme"
    _write_yaml(acme / "tenant.yaml", {"name": "Acme", "workspaces": {"main": {}}})
    _write_yaml(
        acme / "routing.yaml",
        {"models": {"default": "openai/gpt-4"}, "allowed_models": ["gpt-4o-mini", "gpt-4"]},
    )
    # Expensive gpt-4, cheap gpt-4o-mini, strict request cap
    # Pricing is per 1000 tokens: gpt-4 = $0.03/1k tokens, gpt-4o-mini = $0.00015/1k tokens
    _write_yaml(
        acme / "budgets.yaml",
        {"limits": {"max_per_request": 0.01}, "pricing": {"openai/gpt-4": 0.03, "openai/gpt-4o-mini": 0.00015}},
    )

    reg = TenantRegistry(tmp_path)
    reg.load()

    meter = TokenMeter(model_prices={})  # rely on tenant pricing only
    svc = OpenRouterService(api_key="", tenant_registry=reg, token_meter=meter)

    # Create a prompt whose gpt-4 cost would exceed the cap under tenant pricing
    # ~2500 tokens -> gpt-4 cost ~0.075 (above 0.01 cap), gpt-4o-mini cost ~0.000375 (below cap)
    prompt = "x" * 10000
    with with_tenant(TenantContext("acme", "main")):
        res = svc.route(prompt)
    assert res["status"] == "success"
    assert res["model"].startswith("openai/gpt-4o-mini")
