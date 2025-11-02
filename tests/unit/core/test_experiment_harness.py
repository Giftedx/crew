import os
from platform.core.rl.experiment import Experiment, ExperimentManager

def enable_flag():
    os.environ['ENABLE_EXPERIMENT_HARNESS'] = '1'

def test_shadow_mode_returns_control():
    enable_flag()
    mgr = ExperimentManager()
    exp = Experiment(experiment_id='exp:model_select', control='baseline', variants={'alt': 0.5}, phase='shadow', auto_activate_after=None)
    mgr.register(exp)
    for _ in range(10):
        chosen = mgr.recommend('exp:model_select', {}, ['baseline', 'alt'])
        assert chosen == 'baseline'

def test_auto_activation_flips_phase():
    enable_flag()
    mgr = ExperimentManager()
    exp = Experiment(experiment_id='exp:auto_act', control='c', variants={'v1': 0.7}, phase='shadow', auto_activate_after=5)
    mgr.register(exp)
    for _i in range(5):
        chosen = mgr.recommend('exp:auto_act', {}, ['c', 'v1'])
        assert chosen == 'c'
        mgr.record('exp:auto_act', 'c', reward=1.0)
    assert mgr._experiments['exp:auto_act'].phase == 'active'

def test_stats_accumulate_rewards():
    enable_flag()
    mgr = ExperimentManager()
    exp = Experiment(experiment_id='exp:stats', control='control', variants={'var': 0.5}, phase='active')
    mgr.register(exp)
    total_rewards = [0.5, 1.0, 0.0]
    chosen_arms = []
    for r in total_rewards:
        arm = mgr.recommend('exp:stats', {}, ['control', 'var'])
        chosen_arms.append(arm)
        mgr.record('exp:stats', arm, r)
    snap = mgr.snapshot()['experiments']['exp:stats']
    pulls_sum = sum((snap['stats'][a]['pulls'] for a in snap['stats']))
    assert pulls_sum == float(len(total_rewards))
    recorded_reward_sum = 0.0
    for arm, r in zip(chosen_arms, total_rewards, strict=False):
        recorded_reward_sum += r
    aggregate_reward_sum = sum((snap['stats'][a]['reward_sum'] for a in snap['stats']))
    assert aggregate_reward_sum == recorded_reward_sum