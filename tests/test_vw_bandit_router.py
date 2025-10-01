from __future__ import annotations

from ai.routing.vw_bandit_router import VWBanditRouter


def test_vw_router_fallback_select_first_when_disabled(monkeypatch):
    # Ensure classical bandit routing is disabled to force deterministic first-arm selection
    monkeypatch.delenv("ENABLE_BANDIT_ROUTING", raising=False)
    # Enable VW wrapper (even if VW package is not installed)
    monkeypatch.setenv("ENABLE_VW_BANDIT", "1")

    r = VWBanditRouter()
    arm = r.select(["a", "b", "c"])
    assert arm == "a"  # Thompson fallback picks first when routing disabled


def test_vw_router_update_no_crash(monkeypatch):
    # Enable both VW wrapper and bandit routing (fallback will be Thompson)
    monkeypatch.setenv("ENABLE_VW_BANDIT", "1")
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")

    r = VWBanditRouter()
    arms = ["x", "y"]

    # Perform a few selections and updates; this should not raise
    for _ in range(10):
        chosen = r.select(arms)
        reward = 1.0 if chosen == "x" else 0.0
        r.update(chosen, reward)

    # A selection should still return a valid arm
    final_choice = r.select(arms)
    assert final_choice in arms
