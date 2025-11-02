import json

from ai.routing.bandit_router import ThompsonBanditRouter


def test_bandit_persistence_roundtrip(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setenv("ENABLE_BANDIT_PERSIST", "1")
    monkeypatch.setenv("BANDIT_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")

    r1 = ThompsonBanditRouter()
    # Force some updates
    r1.update("model_a", 0.75)
    r1.update("model_b", 0.25)

    # Ensure state file written
    path = state_dir / "bandit_state.json"
    assert path.is_file(), "state file missing after updates"
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    assert "model_a" in raw and "model_b" in raw
    a_before = raw["model_a"]["alpha"]

    # New router instance should load prior
    r2 = ThompsonBanditRouter()
    st_a = r2.get_state("model_a")
    assert st_a is not None
    assert abs(st_a.alpha - a_before) < 1e-9


def test_bandit_persistence_disabled_no_file(tmp_path, monkeypatch):
    state_dir = tmp_path / "state2"
    monkeypatch.setenv("BANDIT_STATE_DIR", str(state_dir))
    monkeypatch.setenv("ENABLE_BANDIT_PERSIST", "0")
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    r = ThompsonBanditRouter()
    r.update("x", 1.0)
    assert not (state_dir / "bandit_state.json").exists()


def test_deterministic_mode_no_selection_metrics(monkeypatch):
    # In deterministic mode (flag off) selection still works but we can't assert metrics easily
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "0")
    r = ThompsonBanditRouter()
    chosen = r.select(["m1", "m2"])  # should always be first
    assert chosen == "m1"
