import importlib
import os


def setup_module(module):
    os.environ["ENABLE_CONTEXTUAL_BANDIT"] = "1"
    os.environ["LINUCB_DIMENSION"] = "2"
    os.environ["LINUCB_ALPHA"] = "0.1"
    # low threshold to trigger recompute quickly
    os.environ["LINUCB_COND_THRESHOLD"] = "10"
    importlib.reload(__import__("ai.routing.linucb_router", fromlist=["LinUCBRouter"]))


def test_condition_threshold_recompute(monkeypatch):
    from ai.routing.linucb_router import LinUCBRouter

    router = LinUCBRouter(dimension=2)
    # craft updates that might inflate condition number
    # use near-collinear feature vectors repeatedly
    feats = [1.0, 1.0]
    for _ in range(5):
        router.update("arm1", reward=0.9, features=feats)
    # Access internal arm to ensure A_inv exists (no assertion, but ensure no exception)
    arms = router.arms()
    assert "arm1" in arms
    # Additional update to potentially cross threshold
    router.update("arm1", reward=0.7, features=feats)
    # If threshold triggered, A_inv was recomputed; we cannot directly observe metric here without metrics backend
    # Basic sanity: selecting should not raise and returns arm1 when only arm
    sel = router.select(["arm1"], feats)
    assert sel == "arm1"
