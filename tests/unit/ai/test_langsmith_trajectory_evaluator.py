from __future__ import annotations

from types import SimpleNamespace

import pytest

from ai.rl.langsmith_trajectory_evaluator import LangSmithTrajectoryEvaluator
from eval.trajectory_evaluator import AgentTrajectory, TrajectoryStep
from ultimate_discord_intelligence_bot.step_result import StepResult


class _StubLangSmithAdapter:
    def evaluate(self, trajectory: AgentTrajectory) -> StepResult:
        result = StepResult.ok(
            score=True, reasoning="High confidence", accuracy_score=0.9, efficiency_score=0.8, error_handling_score=0.7
        )
        result.metadata["langsmith_evaluation_id"] = "eval-123"
        return result


class _StubOrchestrator:
    def __init__(self) -> None:
        self.calls: list[tuple[AgentTrajectory, dict[str, float]]] = []

    def submit_trajectory_feedback(
        self, trajectory: AgentTrajectory, evaluation_result: dict[str, float]
    ) -> StepResult:
        self.calls.append((trajectory, evaluation_result))
        return StepResult.ok(message="queued")


@pytest.fixture()
def sample_trajectory() -> AgentTrajectory:
    return AgentTrajectory(
        session_id="sess-1",
        user_input="hello",
        steps=[TrajectoryStep(timestamp=0.0, agent_role="assistant", action_type="response", content="All good")],
        final_output="done",
        total_duration=2.0,
        success=True,
        tenant="tenant-alpha",
        workspace="workspace-beta",
    )


def test_evaluate_and_submit_success(sample_trajectory: AgentTrajectory) -> None:
    orchestrator = _StubOrchestrator()
    evaluator = LangSmithTrajectoryEvaluator(
        orchestrator=orchestrator,
        settings=SimpleNamespace(enable_langsmith_eval=True, enable_unified_feedback=True),
        adapter=_StubLangSmithAdapter(),
    )
    result = evaluator.evaluate_and_submit(sample_trajectory)
    assert len(orchestrator.calls) == 1
    _, payload = orchestrator.calls[0]
    assert pytest.approx(payload["accuracy_score"]) == 0.9
    assert pytest.approx(payload["efficiency_score"]) == 0.8
    assert pytest.approx(payload["error_handling_score"]) == 0.7
    assert payload["evaluation_id"] == "eval-123"
    feedback_meta = result.metadata["langsmith_trajectory_evaluator"]
    assert feedback_meta["feedback_submitted"] is True


def test_evaluate_skip_when_disabled(sample_trajectory: AgentTrajectory) -> None:
    evaluator = LangSmithTrajectoryEvaluator(
        orchestrator=_StubOrchestrator(),
        settings=SimpleNamespace(enable_langsmith_eval=False, enable_unified_feedback=True),
        adapter=_StubLangSmithAdapter(),
    )
    result = evaluator.evaluate_and_submit(sample_trajectory)
    assert result.skipped is True


def test_submit_feedback_without_orchestrator(sample_trajectory: AgentTrajectory) -> None:
    evaluator = LangSmithTrajectoryEvaluator(
        orchestrator=None,
        settings=SimpleNamespace(enable_langsmith_eval=True, enable_unified_feedback=True),
        adapter=None,
    )
    evaluation = StepResult.ok(
        score=True, reasoning="Great", accuracy_score=0.95, efficiency_score=0.85, error_handling_score=0.9
    )
    result = evaluator.submit_feedback(sample_trajectory, evaluation)
    metadata = result.metadata["langsmith_trajectory_evaluator"]
    assert metadata["feedback_submitted"] is False
    assert metadata["reason"] == "orchestrator_unavailable"
