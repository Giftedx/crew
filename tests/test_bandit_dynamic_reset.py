from ai.routing.bandit_router import ThompsonBanditRouter


def test_dynamic_reset_env_read(monkeypatch):
    # Enable routing and configure reset to trigger after 1 low-entropy step
    monkeypatch.setenv("ENABLE_BANDIT_ROUTING", "1")
    monkeypatch.setenv("BANDIT_RESET_ENTROPY_THRESHOLD", "10")  # very high so any distribution is low entropy
    monkeypatch.setenv("BANDIT_RESET_ENTROPY_WINDOW", "1000")  # start high to avoid immediate reset

    r = ThompsonBanditRouter()

    # Create highly skewed state toward A
    for _ in range(50):
        r.update("A", 1.0)
    r.update("B", 0.0)

    pre_state_a = r.get_state("A")
    assert pre_state_a is not None
    pre_alpha = pre_state_a.alpha

    # Flip window dynamically to 1 so the very next low-entropy update triggers reset
    monkeypatch.setenv("BANDIT_RESET_ENTROPY_WINDOW", "1")
    r.update("A", 1.0)

    post_state_a = r.get_state("A")
    assert post_state_a is not None

    # After reset, alpha should be reduced back near the prior (plus the last update)
    # We assert that a reset occurred by checking the magnitude decreased
    assert post_state_a.alpha <= pre_alpha
