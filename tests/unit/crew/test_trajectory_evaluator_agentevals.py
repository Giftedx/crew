from __future__ import annotations

import os

from eval.trajectory_evaluator import (
    AgentTrajectory,
    TrajectoryEvaluator,
    TrajectoryStep,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


def test_agentevals_flag_skip(monkeypatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_EVALUATION", "1")
    monkeypatch.delenv("ENABLE_AGENT_EVALS", raising=False)
    ev = TrajectoryEvaluator()
    traj = AgentTrajectory(
        session_id="s1",
        user_input="hello",
        steps=[TrajectoryStep(0.0, "agent", "response", "hi")],
        final_output="done",
        total_duration=0.1,
        success=True,
    )
    res = ev.evaluate_trajectory_accuracy(traj)
    assert isinstance(res, StepResult)
    assert res.success is True
    assert res.get("evaluator") == "LLMHeuristic"


def test_agentevals_messages_adapter(monkeypatch):
    monkeypatch.setenv("ENABLE_TRAJECTORY_EVALUATION", "1")
    monkeypatch.setenv("ENABLE_AGENT_EVALS", "1")
    # Force unavailable import path so we exercise fallback and adapter doesn't crash
    monkeypatch.setitem(os.environ, "AGENTEVALS_MODEL", "openai:o3-mini")
    ev = TrajectoryEvaluator()
    traj = AgentTrajectory(
        session_id="s2",
        user_input="weather in SF?",
        steps=[
            TrajectoryStep(
                0.0,
                "agent",
                "tool_call",
                "",
                tool_name="get_weather",
                tool_args={"city": "SF"},
            ),
            TrajectoryStep(0.1, "agent", "response", "It's 80 degrees and sunny."),
        ],
        final_output="The weather in SF is 80 degrees and sunny.",
        total_duration=0.2,
        success=True,
    )
    # Adapter should produce a list of dicts; call private helper via name mangling
    msgs = ev._to_agentevals_messages(traj)  # type: ignore[attr-defined]
    assert isinstance(msgs, list)
    assert msgs[0]["role"] == "user"
    assert any(m.get("tool_calls") for m in msgs if isinstance(m, dict))
