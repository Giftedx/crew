from __future__ import annotations

from ai.routing.bandit_router import ThompsonBanditRouter


def test_bandit_deterministic_when_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_BANDIT_ROUTING", raising=False)
    r = ThompsonBanditRouter()
    arm = r.select(["a", "b", "c"])
    assert arm == "a"  # first arm fallback


def test_bandit_updates_bias(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    r = ThompsonBanditRouter()
    arms = ["slow", "fast"]
    # Simulate higher reward for 'fast'
    for _ in range(40):
        chosen = r.select(arms)
        reward = 0.9 if chosen == "fast" else 0.1
        r.update(chosen, reward)
    # After training, multiple selections should skew toward 'fast'
    fast_count = sum(1 for _ in range(100) if r.select(arms) == "fast")
    assert fast_count > 60  # biased toward fast
