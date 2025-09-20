import pytest
from ai.routing.linucb_router import LinUCBRouter


def test_linucb_dimension_validation():
    with pytest.raises(ValueError):
        LinUCBRouter(0)


def test_linucb_learns_preference(monkeypatch):
    monkeypatch.setenv("ENABLE_CONTEXTUAL_BANDIT", "1")
    monkeypatch.setenv("LINUCB_ALPHA", "0.1")  # lower exploration for faster convergence
    r = LinUCBRouter(dimension=2)
    arms = ["fast", "slow"]
    # Features: x0=1 bias, x1 = synthetic speed indicator (fast=1, slow=0)
    fast_feat = [1.0, 1.0]
    slow_feat = [1.0, 0.0]
    # Provide rewards: fast arm gets higher reward when chosen
    for _ in range(50):
        chosen = r.select(arms, fast_feat)  # use same query features
        if chosen == "fast":
            r.update("fast", 0.9, fast_feat)
        else:
            r.update("slow", 0.2, slow_feat)
    # After training, selecting again should strongly prefer fast
    counts = {"fast": 0, "slow": 0}
    for _ in range(20):
        c = r.select(arms, fast_feat)
        counts[c] += 1
    assert counts["fast"] > counts["slow"]
