"""Enhanced tests for experiment harness with metrics and logging."""

import os
from platform.core.rl.experiment import Experiment, ExperimentManager
from unittest.mock import MagicMock, patch


def enable_flag():
    os.environ["ENABLE_EXPERIMENT_HARNESS"] = "1"


def test_experiment_registration_logging():
    """Test that experiment registration is properly logged."""
    enable_flag()
    mgr = ExperimentManager()
    with patch("core.rl.experiment.logger") as mock_logger:
        exp = Experiment(
            experiment_id="exp:logging_test",
            control="baseline",
            variants={"variant_a": 0.3, "variant_b": 0.2},
            phase="shadow",
            auto_activate_after=10,
        )
        mgr.register(exp)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        log_message = call_args[0][0]
        log_args = call_args[0][1:]
        assert "Experiment registered" in log_message
        assert "exp:logging_test" in log_args


def test_allocation_with_logging():
    """Test that allocations are properly logged."""
    enable_flag()
    mgr = ExperimentManager()
    with patch("core.rl.experiment.logger") as mock_logger:
        exp = Experiment(
            experiment_id="exp:allocation_test", control="control", variants={"variant": 0.5}, phase="shadow"
        )
        mgr.register(exp)
        choice = mgr.recommend("exp:allocation_test", {"tenant": "test", "workspace": "main"}, ["control", "variant"])
        assert any("Experiment allocation" in str(call) for call in mock_logger.debug.call_args_list)
        assert choice == "control"


def test_reward_recording_with_logging():
    """Test that reward recording includes proper logging."""
    enable_flag()
    mgr = ExperimentManager()
    with patch("core.rl.experiment.logger") as mock_logger:
        exp = Experiment(experiment_id="exp:reward_test", control="control", variants={"variant": 0.5}, phase="active")
        mgr.register(exp)
        mgr.record("exp:reward_test", "control", 0.85)
        debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Recording experiment reward" in call for call in debug_calls)
        assert any("Experiment reward recorded" in call for call in debug_calls)


def test_auto_activation_with_logging():
    """Test that auto-activation generates proper log messages."""
    enable_flag()
    mgr = ExperimentManager()
    with patch("core.rl.experiment.logger") as mock_logger:
        exp = Experiment(
            experiment_id="exp:auto_activate",
            control="control",
            variants={"variant": 0.5},
            phase="shadow",
            auto_activate_after=3,
        )
        mgr.register(exp)
        for _i in range(3):
            mgr.recommend("exp:auto_activate", {}, ["control", "variant"])
            mgr.record("exp:auto_activate", "control", 0.5)
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Experiment auto-activated" in call for call in info_calls)


def test_snapshot_dashboard_metadata():
    """Test that snapshot includes dashboard-ready metadata."""
    enable_flag()
    mgr = ExperimentManager()
    exp1 = Experiment(experiment_id="exp:active", control="c1", variants={"v1": 0.5}, phase="active")
    exp2 = Experiment(experiment_id="exp:shadow", control="c2", variants={"v2": 0.3}, phase="shadow")
    mgr.register(exp1)
    mgr.register(exp2)
    snapshot = mgr.snapshot()
    assert "total_experiments" in snapshot
    assert "active_experiments" in snapshot
    assert "shadow_experiments" in snapshot
    assert "experiments" in snapshot
    assert "timestamp" in snapshot
    assert snapshot["total_experiments"] == 2
    assert snapshot["active_experiments"] == 1
    assert snapshot["shadow_experiments"] == 1
    assert "exp:active" in snapshot["experiments"]
    assert "exp:shadow" in snapshot["experiments"]


def test_metrics_integration_availability():
    """Test metrics integration when metrics module is available."""
    enable_flag()
    with patch("core.rl.experiment.METRICS_AVAILABLE", True):
        with patch("core.rl.experiment.metrics") as mock_metrics_module:
            mock_allocation_metric = MagicMock()
            mock_phase_metric = MagicMock()
            mock_metrics_module.EXPERIMENT_VARIANT_ALLOCATIONS = mock_allocation_metric
            mock_phase_metric.labels.return_value = mock_phase_metric
            mock_metrics_module.EXPERIMENT_PHASE_STATUS = mock_phase_metric
            with patch("core.rl.experiment.current_tenant") as mock_current_tenant:
                mock_ctx = MagicMock()
                mock_ctx.tenant_id = "test_tenant"
                mock_ctx.workspace_id = "test_workspace"
                mock_current_tenant.return_value = mock_ctx
                mgr = ExperimentManager()
                exp = Experiment(
                    experiment_id="exp:metrics_test", control="control", variants={"variant": 0.5}, phase="shadow"
                )
                mgr.register(exp)
                choice = mgr.recommend("exp:metrics_test", {}, ["control", "variant"])
                assert choice == "control"


def test_flag_disabled_behavior():
    """Test that harness is disabled when flag is off."""
    os.environ.pop("ENABLE_EXPERIMENT_HARNESS", None)
    mgr = ExperimentManager()
    exp = Experiment(experiment_id="exp:disabled", control="control", variants={"variant": 0.5}, phase="active")
    mgr.register(exp)
    choice = mgr.recommend("exp:disabled", {}, ["option1", "option2"])
    assert choice == "option1"
    mgr.record("exp:disabled", "option1", 0.5)
    snapshot = mgr.snapshot()
    assert "total_experiments" in snapshot


def test_missing_experiment_handling():
    """Test graceful handling of missing experiments."""
    enable_flag()
    mgr = ExperimentManager()
    with patch("core.rl.experiment.logger") as mock_logger:
        choice = mgr.recommend("non_existent", {}, ["option1"])
        assert choice == "option1"
        mgr.record("non_existent", "option1", 0.5)
        debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
        assert any("Experiment not found" in call for call in debug_calls)
        assert any("Cannot record reward - experiment not found" in call for call in debug_calls)


if __name__ == "__main__":
    test_experiment_registration_logging()
    test_allocation_with_logging()
    test_reward_recording_with_logging()
    test_auto_activation_with_logging()
    test_snapshot_dashboard_metadata()
    test_metrics_integration_availability()
    test_flag_disabled_behavior()
    test_missing_experiment_handling()
    print("All enhanced experiment harness tests passed!")
