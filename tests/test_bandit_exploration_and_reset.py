from ai.routing.bandit_router import ThompsonBanditRouter


def test_epsilon_exploration(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("BANDIT_MIN_EPSILON", "1.0")  # force exploration every time
    r = ThompsonBanditRouter()
    arms = ["A", "B", "C"]
    # prime states
    for _ in range(5):
        r.update("A", 1.0)
    # With epsilon=1 we should not always pick Thompson argmax (A); ensure diversity
    seen = set()
    for _ in range(10):
        chosen = r.select(arms)
        seen.add(chosen)
    assert len(seen) > 1  # exploration happened


def test_entropy_reset(monkeypatch):
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    # Very low threshold, window=1 to trigger immediate reset after low entropy situation
    monkeypatch.setenv("BANDIT_RESET_ENTROPY_THRESHOLD", "10")  # high threshold ensures condition met
    monkeypatch.setenv("BANDIT_RESET_ENTROPY_WINDOW", "1")
    r = ThompsonBanditRouter()
    # create two arms strongly skewed
    for _ in range(30):
        r.update("A", 1.0)
    r.update("B", 0.0)
    # Next update should trigger reset due to configured threshold/window
    pre_state_a = r.get_state("A")
    assert pre_state_a is not None
    r.update("A", 1.0)
    post_state_a = r.get_state("A")
    # After reset alpha should be close to prior (exactly prior + last update since reset sets then update adds?)
    # Because reset happens inside update flow after applying update logic, we detect by reduced magnitude.
    assert post_state_a.alpha <= pre_state_a.alpha  # reset reduced accumulated alpha
