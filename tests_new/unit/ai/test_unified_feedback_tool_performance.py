"""Focused tests for tool performance extraction logic."""

from __future__ import annotations

import pytest

from src.ai.rl.unified_feedback_orchestrator import UnifiedFeedbackOrchestrator
from src.eval.trajectory_evaluator import AgentTrajectory, TrajectoryStep


@pytest.fixture()
def orchestrator() -> UnifiedFeedbackOrchestrator:
    return UnifiedFeedbackOrchestrator()


def _build_trajectory(*steps: TrajectoryStep) -> AgentTrajectory:
    return AgentTrajectory(
        session_id="traj-tool-test",
        user_input="mock",
        steps=list(steps),
        final_output="done",
        total_duration=float(len(steps)),
        success=True,
        tenant=None,
        workspace=None,
    )


def test_tool_performance_uses_step_success(orchestrator: UnifiedFeedbackOrchestrator) -> None:
    """Performance should average boolean success flags on steps."""

    steps = [
        TrajectoryStep(
            timestamp=0.0,
            agent_role="assistant",
            action_type="tool_call",
            content="call",
            tool_name="search",
            success=True,
        ),
        TrajectoryStep(
            timestamp=1.0,
            agent_role="assistant",
            action_type="tool_call",
            content="call",
            tool_name="search",
            success=False,
        ),
    ]

    trajectory = _build_trajectory(*steps)
    performance = orchestrator._extract_tool_performance(trajectory, {})

    assert "search" in performance
    assert performance["search"]["count"] == 2
    assert performance["search"]["reward"] == pytest.approx(0.5)
    assert performance["search"]["context"]["usage_count"] == 2


def test_tool_performance_handles_dict_result(orchestrator: UnifiedFeedbackOrchestrator) -> None:
    """Dict-based result payloads should act as success fallbacks."""

    step = TrajectoryStep(
        timestamp=0.0,
        agent_role="assistant",
        action_type="tool_call",
        content="call",
        tool_name="search",
        success=True,
    )
    step.success = None
    step.result = {"success": True}

    trajectory = _build_trajectory(step)
    performance = orchestrator._extract_tool_performance(trajectory, {})

    assert performance["search"]["reward"] == pytest.approx(1.0)
    assert performance["search"]["confidence"] == pytest.approx(0.8)
