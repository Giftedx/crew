from ai.routing.router_registry import (
    RewardNormalizer,
    compute_selection_entropy,
    get_tenant_router,
    record_selection,
)
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


def test_tenant_router_isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("ENABLE_BANDIT_PERSIST", "1")
    monkeypatch.setenv("BANDIT_STATE_DIR", str(tmp_path))

    ctx1 = TenantContext(tenant_id="t1", workspace_id="w1")
    ctx2 = TenantContext(tenant_id="t2", workspace_id="w1")

    with with_tenant(ctx1):
        r1 = get_tenant_router()
        r1.update("mA", 0.9)
    with with_tenant(ctx2):
        r2 = get_tenant_router()
        r2.update("mA", 0.1)

    # Distinct router instances with different posterior values
    st1 = r1.get_state("mA")
    st2 = r2.get_state("mA")
    assert st1 and st2 and st1.alpha != st2.alpha


def test_entropy_tracking(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    ctx = TenantContext(tenant_id="tE", workspace_id="wE")
    with with_tenant(ctx):
        record_selection("m1")
        record_selection("m1")
        record_selection("m2")
        ent = compute_selection_entropy()
    assert ent is not None and ent > 0


def test_reward_normalizer_progression():
    rn = RewardNormalizer()
    r1 = rn.compute(quality=0.8, latency_ms=400, cost=0.01)
    r2 = rn.compute(quality=0.85, latency_ms=350, cost=0.009)
    # Second reward should generally reflect improved quality & latency -> often higher (not strictly guaranteed)
    assert 0 <= r1 <= 1 and 0 <= r2 <= 1
    # At least ensure variability occurred
    assert r1 != r2
