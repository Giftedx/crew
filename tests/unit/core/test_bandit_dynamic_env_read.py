from ai.routing.bandit_router import ThompsonBanditRouter


def test_dynamic_epsilon_read(monkeypatch):
    # Enable bandit routing but start with no forced exploration
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("BANDIT_MIN_EPSILON", "0.0")

    r = ThompsonBanditRouter()
    arms = ["A", "B"]

    # Prime A to be argmax under Thompson
    for _ in range(20):
        r.update("A", 1.0)
        r.update("B", 0.0)

    # With epsilon 0.0, should always pick A across several trials
    seen = {r.select(arms) for _ in range(20)}
    assert seen == {"A"}

    # Now flip epsilon dynamically; router should start exploring without reload
    monkeypatch.setenv("BANDIT_MIN_EPSILON", "1.0")
    seen2 = {r.select(arms) for _ in range(20)}
    # With epsilon=1.0 and strong A prior, overlay always picks a non-argmax arm.
    # In a 2-arm case this should result in choosing B; allow rare Thompson flips.
    assert "B" in seen2
    assert "A" not in seen2  # overlay should avoid argmax when it triggers every time
