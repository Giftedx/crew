from platform.core.rollout import RolloutController

def test_rollout_promotes_candidate():
    rc = RolloutController()
    rc.start('demo', 'a', 'b', canary_pct=0.5, min_trials=3)
    rc.record('demo', 'a', 0.1)
    rc.record('demo', 'b', 1.0)
    rc.record('demo', 'b', 1.0)
    assert rc.choose('demo') == 'b'