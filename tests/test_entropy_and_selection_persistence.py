from ai.routing.bandit_router import ThompsonBanditRouter
from ai.routing.router_registry import _compute_posterior_mean_entropy as compute_post_entropy  # type: ignore
from ai.routing.router_registry import (  # type: ignore
    _selection_counts,  # type: ignore
    load_selection_counts,
    record_selection,
    save_selection_counts,
)
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext, with_tenant


def test_posterior_mean_entropy_changes_with_updates():
    r = ThompsonBanditRouter()
    # Create two arms via selection/update
    r.update("A", 0.9)
    r.update("B", 0.1)
    ent_initial = compute_post_entropy(r)
    assert ent_initial is not None
    # Push one arm to be clearly dominant
    for _ in range(20):
        r.update("A", 1.0)
    ent_after = compute_post_entropy(r)
    assert ent_after is not None
    assert ent_after < ent_initial  # convergence reduces entropy


def test_selection_count_persistence_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_PERSIST", "1")
    monkeypatch.setenv("BANDIT_STATE_DIR", str(tmp_path))
    ctx = TenantContext(tenant_id="pt", workspace_id="ws")
    with with_tenant(ctx):
        record_selection("m1")
        record_selection("m2")
        record_selection("m2")
    save_selection_counts()
    # Clear in-memory and reload
    _selection_counts.clear()  # type: ignore
    load_selection_counts()
    with with_tenant(ctx):
        # Access internal structure to confirm counts
        key = (ctx.tenant_id, ctx.workspace_id)
        counts = _selection_counts.get(key)  # type: ignore
        assert counts["m1"] == 1
        assert counts["m2"] == 2
