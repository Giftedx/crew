from ai.routing.linucb_router import LinUCBRouter


def test_linucb_cached_inverse_parity(monkeypatch):
    monkeypatch.setenv("ENABLE_CONTEXTUAL_BANDIT", "1")
    monkeypatch.setenv("LINUCB_ALPHA", "0.2")
    monkeypatch.setenv("LINUCB_RECOMPUTE_INTERVAL", "0")  # disable periodic recompute
    r = LinUCBRouter(dimension=3)
    # arms implicitly referenced via direct updates
    feat_a = [1.0, 0.5, -0.3]
    feat_b = [1.0, -0.2, 0.4]
    # Perform updates to populate and update cached inverses
    for _ in range(15):
        r.update("a", 0.8, feat_a)
        r.update("b", 0.4, feat_b)

    # Fresh scoring via manual inversion vs cached path
    # Access internals for parity test
    a_ctx = r._arms["a"]
    b_ctx = r._arms["b"]
    # Force manual recompute
    a_inv_manual = r._mat_inv(a_ctx.A)
    b_inv_manual = r._mat_inv(b_ctx.A)

    # Compute scores manually
    def score(ctx, A_inv, x):
        theta = r._mat_vec(A_inv, ctx.b)
        mean = sum(theta[i] * x[i] for i in range(r._d))
        Ax = r._mat_vec(A_inv, x)
        import math

        conf = math.sqrt(max(0.0, sum(x[i] * Ax[i] for i in range(r._d))))
        return mean + float(r._ALPHA if hasattr(r, "_ALPHA") else 0.2) * conf

    manual_a = score(a_ctx, a_inv_manual, feat_a)
    manual_b = score(b_ctx, b_inv_manual, feat_b)

    # Use public API which relies on cached inverse
    _, cached_a = r.select_with_score(["a"], feat_a)
    _, cached_b = r.select_with_score(["b"], feat_b)

    # parity within a small tolerance
    assert abs(manual_a - cached_a) < 1e-6
    assert abs(manual_b - cached_b) < 1e-6
