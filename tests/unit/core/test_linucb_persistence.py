from ai.routing.linucb_router import LinUCBRouter


def test_linucb_persistence_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setenv("ENABLE_CONTEXTUAL_BANDIT", "1")
    monkeypatch.setenv("ENABLE_BANDIT_PERSIST", "1")
    monkeypatch.setenv("BANDIT_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("LINUCB_ALPHA", "0.1")
    r1 = LinUCBRouter(dimension=3)
    # arms implicit via update calls
    feat = [1.0, 0.5, -0.2]
    # Update some arms
    for _ in range(5):
        r1.update("a", 0.9, feat)
    for _ in range(2):
        r1.update("b", 0.3, feat)
    path = tmp_path / "linucb_d3.json"
    assert path.is_file(), "State file not written"

    # New instance should load prior state
    r2 = LinUCBRouter(dimension=3)
    st_a = r2._arms.get("a")  # accessing internal for test
    st_b = r2._arms.get("b")
    assert st_a is not None and st_b is not None
    # A matrix diagonal should have grown from identity due to outer products
    assert st_a.A[0][0] > 1.0
    assert st_b.A[0][0] > 1.0
