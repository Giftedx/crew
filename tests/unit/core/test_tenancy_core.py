from pathlib import Path
from platform.core.learning_engine import LearningEngine

import pytest

from core import router as router_mod
from core import token_meter
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry


def make_registry(tmp_path: Path) -> TenantRegistry:
    tenant_dir = tmp_path / "tenants" / "t1"
    tenant_dir.mkdir(parents=True)
    (tenant_dir / "tenant.yaml").write_text(
        "id: 1\nname: T1\nworkspaces:\n  main:\n    discord_guild_id: 1\n", encoding="utf-8"
    )
    (tenant_dir / "budgets.yaml").write_text("daily_cap_usd: 1.0\nmax_per_request: 0.6\n", encoding="utf-8")
    (tenant_dir / "routing.yaml").write_text("allowed_models:\n  - gpt-3.5\n", encoding="utf-8")
    reg = TenantRegistry(tmp_path / "tenants")
    reg.load()
    return reg


def test_budget_is_tenant_scoped(tmp_path: Path):
    reg = make_registry(tmp_path)
    token_meter.budget.registry = reg
    ctx = TenantContext("t1", "main")
    with with_tenant(ctx):
        token_meter.budget.preflight(0.5)
        token_meter.budget.charge(0.5)
        with pytest.raises(token_meter.BudgetError):
            token_meter.budget.preflight(0.6)
    ctx2 = TenantContext("t2", "main")
    with with_tenant(ctx2):
        token_meter.budget.preflight(0.8)


def test_router_respects_allowed_models(tmp_path: Path):
    reg = make_registry(tmp_path)
    engine = LearningEngine()
    r = router_mod.Router(engine, registry=reg)
    ctx = TenantContext("t1", "main")
    with with_tenant(ctx):
        model = r.route("task", ["gpt-3.5", "gpt-4"], {"prompt": "hi", "expected_output_tokens": 0})
        assert model == "gpt-3.5"
        with pytest.raises(ValueError):
            r.route("task", ["gpt-4"], {"prompt": "hi", "expected_output_tokens": 0})
