from platform.core.rl.policies.lints import LinTSDiagBandit


def test_lints_recommend_and_update_basic():
    bandit = LinTSDiagBandit(dim=6, sigma=0.3)
    arms = ["a", "b"]
    choice = bandit.recommend({}, arms)
    assert choice in arms
    for _ in range(20):
        for arm, reward in [("a", 0.2), ("b", 0.8)]:
            bandit.update(arm, reward, {"iter": _})
    b_count = 0
    for _ in range(50):
        if bandit.recommend({}, arms) == "b":
            b_count += 1
    assert b_count > 25


def test_lints_state_round_trip():
    bandit = LinTSDiagBandit(dim=4, sigma=0.4)
    for i in range(10):
        bandit.update("x", reward=0.5, context={"i": i})
        bandit.update("y", reward=0.9, context={"i": i})
    snap = bandit.state_dict()
    clone = LinTSDiagBandit()
    clone.load_state(snap)
    assert set(clone.A_diag.keys()) == set(bandit.A_diag.keys())
    assert clone.q_values["y"] >= clone.q_values["x"]
