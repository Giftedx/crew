import pytest

from eval.trajectory_evaluator import AgentTrajectory, TrajectoryEvaluator, TrajectoryStep
from ultimate_discord_intelligence_bot.obs import metrics


class _FakeAgentEvals:
    def __init__(self, payload):
        self.payload = payload

    def __call__(self, data):
        return {
            "score": True,
            "reasoning": "ok",
            "accuracy_score": 0.88,
            "efficiency_score": 0.77,
            "error_handling_score": 0.66,
        }


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for k in ["ENABLE_TRAJECTORY_EVALUATION", "ENABLE_AGENT_EVALS"]:
        monkeypatch.delenv(k, raising=False)
    yield


def test_agent_evals_adapter_happy_path(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_EVALUATION", "1")
    monkeypatch.setenv("ENABLE_AGENT_EVALS", "1")
    metrics.reset()
    monkeypatch.setenv("ENABLE_AGENT_EVALS", "1")
    monkeypatch.setitem(globals(), "__name__", "tests.test_agent_evals_adapter_context")
    monkeypatch.setattr("src.eval.trajectory_evaluator._lc_evaluate_trajectory", _FakeAgentEvals({}), raising=False)
    monkeypatch.setattr("src.eval.trajectory_evaluator._AGENTEVALS_AVAILABLE", True, raising=False)
    ev = TrajectoryEvaluator(router=None, learning_engine=None)
    traj = AgentTrajectory(
        session_id="s1",
        user_input="do it",
        steps=[TrajectoryStep(timestamp=0.0, agent_role="a1", action_type="tool_call", content="", tool_name="t1")],
        final_output="done",
        total_duration=1.0,
        success=True,
    )
    res = ev.evaluate_trajectory_accuracy(traj)
    assert res.success is True
    assert res["evaluator"] == "AgentEvals"
    assert isinstance(res["accuracy_score"], float)


def test_agent_evals_fallback_on_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_EVALUATION", "1")
    monkeypatch.setenv("ENABLE_AGENT_EVALS", "1")
    metrics.reset()

    def _boom(_):
        raise RuntimeError("boom")

    monkeypatch.setattr("src.eval.trajectory_evaluator._lc_evaluate_trajectory", _boom, raising=False)
    monkeypatch.setattr("src.eval.trajectory_evaluator._AGENTEVALS_AVAILABLE", True, raising=False)
    ev = TrajectoryEvaluator(router=None, learning_engine=None)
    traj = AgentTrajectory(
        session_id="s2", user_input="do it", steps=[], final_output="ok", total_duration=0.1, success=True
    )
    res = ev.evaluate_trajectory_accuracy(traj)
    assert res.success is True
    assert res["evaluator"] == "LLMHeuristic"
