from __future__ import annotations

from pathlib import Path

from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


def test_openrouter_respects_tenant_allowed_models_offline(tmp_path: Path) -> None:
    # Point registry at real tenants dir in repo to load allowed_models
    tenants_dir = Path("tenants")
    assert (tenants_dir / "default" / "routing.yaml").exists()
    reg = TenantRegistry(tenants_dir)
    reg.load()

    svc = OpenRouterService(api_key="", tenant_registry=reg)  # offline mode
    with with_tenant(TenantContext("default", "main")):
        res = svc.route("hello", task_type="analysis")
    assert res["status"] == "success"
    # Ensure chosen model aligns with allowlist intent (substring check)
    model = res["model"]
    assert any(tok in model for tok in ("gpt-3.5", "gpt-4"))

