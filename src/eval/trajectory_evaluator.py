"""Enhanced trajectory evaluation for CrewAI agents.

This module implements trajectory evaluation patterns inspired by AgentEvals
but built on the existing StepResult contract and infrastructure.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from obs import metrics, tracing
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import current_tenant


if TYPE_CHECKING:
    from core.learning_engine import LearningEngine
    from core.router import Router


# Optional AgentEvals integration (Context7 recommendation)
_AGENTEVALS_AVAILABLE = False
_agentevals_create_judge = None  # lazy handle to factory


# Local minimal adapter function placeholder (tests monkeypatch this symbol)
def _lc_evaluate_trajectory(
    outputs,
):  # pragma: no cover - default simple passthrough heuristic
    return {
        "score": True,
        "reasoning": "local chain evaluator placeholder",
        "accuracy_score": 0.5,
        "efficiency_score": 0.5,
        "error_handling_score": 0.5,
    }


# Mark as default stub so tests can distinguish and monkeypatch reliably
_DEFAULT_LC_EVAL = _lc_evaluate_trajectory


try:  # pragma: no cover - optional dependency path
    # Only attempt import when explicitly enabled to avoid hard dependency
    if os.getenv("ENABLE_AGENT_EVALS", "0") == "1":
        from agentevals.trajectory.llm import (  # type: ignore
            create_trajectory_llm_as_judge as _create_judge,
        )

        _AGENTEVALS_AVAILABLE = True
        _agentevals_create_judge = _create_judge
except Exception:
    _AGENTEVALS_AVAILABLE = False
    _agentevals_create_judge = None

# Trajectory accuracy evaluation prompt for LLM-as-judge
TRAJECTORY_ACCURACY_PROMPT = """You are an expert AI system evaluator. Analyze the following agent trajectory and determine if it accurately accomplishes the user's request.

Agent Trajectory:
{trajectory}

Evaluation Criteria:
1. Task Understanding: Did the agent correctly understand the user's request?
2. Tool Selection: Were appropriate tools chosen for the task?
3. Execution Order: Was the sequence of actions logical and efficient?
4. Error Handling: How well did the agent handle any errors or unexpected situations?
5. Result Quality: Was the final output accurate and complete?

Return your evaluation as JSON:
{{
    "score": true/false,
    "reasoning": "detailed explanation of your assessment",
    "accuracy_score": 0.0-1.0,
    "efficiency_score": 0.0-1.0,
    "error_handling_score": 0.0-1.0
}}"""


@dataclass
class TrajectoryStep:
    """Represents a single step in an agent trajectory."""

    timestamp: float
    agent_role: str
    action_type: str  # "tool_call", "reasoning", "response"
    content: str
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    success: bool = True
    error: str | None = None


@dataclass
class AgentTrajectory:
    """Represents a complete agent execution trajectory."""

    session_id: str
    user_input: str
    steps: list[TrajectoryStep]
    final_output: str
    total_duration: float
    success: bool
    tenant: str | None = None
    workspace: str | None = None


class TrajectoryEvaluator:
    """Enhanced trajectory evaluator for CrewAI agents."""

    def __init__(
        self,
        router: Router | None = None,
        learning_engine: LearningEngine | None = None,
    ):
        self.router = router
        self.learning_engine = learning_engine
        self.enabled = os.getenv("ENABLE_TRAJECTORY_EVALUATION", "0") == "1"

        if self.learning_engine and "trajectory_evaluation" not in self.learning_engine.registry:
            self.learning_engine.register_domain("trajectory_evaluation")

    @tracing.trace_call("trajectory_evaluator.extract_from_crew_execution")
    def extract_trajectory_from_crew_execution(self, crew_execution_log: dict[str, Any]) -> AgentTrajectory:
        """Extract trajectory from CrewAI execution log."""
        steps = []
        start_time = crew_execution_log.get("start_time", time.time())

        # Extract steps from crew execution
        for step_data in crew_execution_log.get("steps", []):
            step = TrajectoryStep(
                timestamp=step_data.get("timestamp", time.time()),
                agent_role=step_data.get("agent_role", "unknown"),
                action_type=step_data.get("action_type", "unknown"),
                content=step_data.get("content", ""),
                tool_name=step_data.get("tool_name"),
                tool_args=step_data.get("tool_args"),
                success=step_data.get("success", True),
                error=step_data.get("error"),
            )
            steps.append(step)

        # Get tenant context
        ctx = current_tenant()

        return AgentTrajectory(
            session_id=crew_execution_log.get("session_id", "unknown"),
            user_input=crew_execution_log.get("user_input", ""),
            steps=steps,
            final_output=crew_execution_log.get("final_output", ""),
            total_duration=crew_execution_log.get("total_duration", time.time() - start_time),
            success=crew_execution_log.get("success", True),
            tenant=getattr(ctx, "tenant_id", None) if ctx else None,
            workspace=getattr(ctx, "workspace", None) if ctx else None,
        )

    @tracing.trace_call("trajectory_evaluator.evaluate_accuracy")
    def evaluate_trajectory_accuracy(self, trajectory: AgentTrajectory) -> StepResult:
        """Evaluate trajectory accuracy using LLM-as-judge."""
        if not self.enabled:
            return StepResult.skip(reason="Trajectory evaluation disabled")

        try:
            # Optional: AgentEvals adapter path (if enabled). Prefer the lightweight
            # monkeypatched evaluator used in tests when present, regardless of
            # import-time availability of the full AgentEvals package.
            if os.getenv("ENABLE_AGENT_EVALS", "0") == "1":
                try:
                    outputs = self._to_agentevals_messages(trajectory)
                    # Detect injected evaluator from either local module or src-qualified alias
                    injected_func = None
                    try:
                        import src.eval.trajectory_evaluator as _mod_src  # type: ignore

                        if (
                            hasattr(_mod_src, "_lc_evaluate_trajectory")
                            and _mod_src._lc_evaluate_trajectory is not _DEFAULT_LC_EVAL
                        ):
                            injected_func = _mod_src._lc_evaluate_trajectory
                    except Exception:
                        pass
                    if (
                        injected_func is None
                        and ("_lc_evaluate_trajectory" in globals())
                        and _lc_evaluate_trajectory is not _DEFAULT_LC_EVAL
                    ):
                        injected_func = _lc_evaluate_trajectory

                    if injected_func is not None:
                        try:
                            return StepResult.ok(
                                evaluator="AgentEvals",
                                **injected_func(outputs),  # type: ignore[arg-type]
                            )
                        except Exception:
                            # Injection failed -> fall through to heuristic; do not attempt real AgentEvals
                            raise
                    # No injection; attempt real AgentEvals if available
                    if _AGENTEVALS_AVAILABLE and _agentevals_create_judge:
                        judge_model = os.getenv("AGENTEVALS_MODEL", "openai:o3-mini")
                        evaluator = _agentevals_create_judge(model=judge_model)
                        ae_res = evaluator(outputs=outputs)  # reference optional
                        if isinstance(ae_res, dict):
                            score_bool = bool(ae_res.get("score", True))
                            return StepResult.ok(
                                score=score_bool,
                                reasoning=str(ae_res.get("reasoning", "")),
                                accuracy_score=float(ae_res.get("accuracy_score", 0.0)),
                                efficiency_score=float(ae_res.get("efficiency_score", 0.0)),
                                error_handling_score=float(ae_res.get("error_handling_score", 0.0)),
                                trajectory_id=trajectory.session_id,
                                evaluator="AgentEvals",
                            )
                        return StepResult.ok(
                            score=True,
                            reasoning="AgentEvals evaluator returned non-dict result; see raw",
                            trajectory_id=trajectory.session_id,
                            evaluator="AgentEvals",
                            raw=str(ae_res),
                        )
                except Exception:
                    # Fall through to local evaluator while recording metric
                    metrics.DEGRADATION_EVENTS.labels(
                        **metrics.label_ctx(),
                        component="trajectory_eval",
                        event_type="agent_evals_fallback",
                        severity="warn",
                    ).inc()
            # Format trajectory for evaluation
            formatted_trajectory = self._format_trajectory_for_evaluation(trajectory)

            # Use router to select appropriate model for evaluation
            evaluation_prompt = TRAJECTORY_ACCURACY_PROMPT.format(trajectory=formatted_trajectory)

            if self.router:
                # Get model for evaluation task
                _model = self.router.route(
                    task="trajectory_evaluation",
                    candidates=["gpt-4o-mini", "gpt-3.5-turbo", "claude-3-haiku"],
                    context={
                        "prompt": evaluation_prompt,
                        "expected_output_tokens": 200,
                        "estimated_cost_usd": 0.01,
                    },
                )

                # This would integrate with the LLM service
                # For now, we'll simulate the evaluation
                evaluation_result = self._simulate_llm_evaluation(trajectory)
            else:
                evaluation_result = self._simulate_llm_evaluation(trajectory)

            # Record results for learning
            if self.learning_engine:
                reward = evaluation_result["accuracy_score"]
                self.learning_engine.record(
                    "trajectory_evaluation",
                    context={"trajectory_length": len(trajectory.steps)},
                    action="evaluate",
                    reward=reward,
                )

            # Update metrics
            metrics.TRAJECTORY_EVALUATIONS.labels(
                **metrics.label_ctx(), success=str(evaluation_result["score"]).lower()
            ).inc()

            return StepResult.ok(
                score=evaluation_result["score"],
                reasoning=evaluation_result["reasoning"],
                accuracy_score=evaluation_result["accuracy_score"],
                efficiency_score=evaluation_result["efficiency_score"],
                error_handling_score=evaluation_result["error_handling_score"],
                trajectory_id=trajectory.session_id,
                evaluator="LLMHeuristic",
            )

        except Exception as e:
            return StepResult.fail(f"Trajectory evaluation failed: {e}")

    def evaluate_trajectory_match(
        self,
        trajectory: AgentTrajectory,
        reference_trajectory: AgentTrajectory,
        match_mode: str = "strict",
    ) -> StepResult:
        """Evaluate trajectory against a reference trajectory."""
        if not self.enabled:
            return StepResult.skip(reason="Trajectory evaluation disabled")

        try:
            if match_mode == "strict":
                return self._strict_trajectory_match(trajectory, reference_trajectory)
            elif match_mode == "superset":
                return self._superset_trajectory_match(trajectory, reference_trajectory)
            elif match_mode == "unordered":
                return self._unordered_trajectory_match(trajectory, reference_trajectory)
            else:
                return StepResult.fail(f"Unknown match mode: {match_mode}")

        except Exception as e:
            return StepResult.fail(f"Trajectory match evaluation failed: {e}")

    def _format_trajectory_for_evaluation(self, trajectory: AgentTrajectory) -> str:
        """Format trajectory for LLM evaluation."""
        formatted = [
            f"User Input: {trajectory.user_input}",
            f"Duration: {trajectory.total_duration:.2f}s",
            f"Success: {trajectory.success}",
            "",
            "Steps:",
        ]

        for i, step in enumerate(trajectory.steps, 1):
            formatted.append(f"{i}. [{step.agent_role}] {step.action_type}")
            if step.tool_name:
                formatted.append(f"   Tool: {step.tool_name}")
                if step.tool_args:
                    formatted.append(f"   Args: {json.dumps(step.tool_args, indent=2)}")
            formatted.append(f"   Content: {step.content[:200]}...")
            if step.error:
                formatted.append(f"   Error: {step.error}")
            formatted.append("")

        formatted.append(f"Final Output: {trajectory.final_output}")

        return "\n".join(formatted)

    def _simulate_llm_evaluation(self, trajectory: AgentTrajectory) -> dict[str, Any]:
        """Simulate LLM evaluation (replace with actual LLM call)."""
        # Basic heuristic evaluation for demonstration
        accuracy_score = 0.8 if trajectory.success else 0.3
        efficiency_score = max(0.1, 1.0 - (len(trajectory.steps) / 20))  # Fewer steps = more efficient
        error_handling_score = 0.9 if not any(step.error for step in trajectory.steps) else 0.6

        overall_score = (accuracy_score + efficiency_score + error_handling_score) / 3 > 0.7

        return {
            "score": overall_score,
            "reasoning": f"Trajectory {'succeeded' if trajectory.success else 'failed'} with {len(trajectory.steps)} steps",
            "accuracy_score": accuracy_score,
            "efficiency_score": efficiency_score,
            "error_handling_score": error_handling_score,
        }

    def _to_agentevals_messages(self, trajectory: AgentTrajectory) -> list[dict[str, Any]]:
        """Convert internal trajectory to agentevals messages schema.

        Best-effort mapping:
        - Start with user message.
        - For tool calls: assistant message with tool_calls + a tool result message using step content.
        - For reasoning/response: assistant content message.
        - Append final assistant message with final_output if present.
        """
        messages: list[dict[str, Any]] = []
        if trajectory.user_input:
            messages.append({"role": "user", "content": str(trajectory.user_input)})
        for s in trajectory.steps:
            if s.tool_name:
                # Assistant indicating a tool call
                call = {
                    "function": {
                        "name": str(s.tool_name),
                        "arguments": json.dumps(s.tool_args or {}),
                    }
                }
                messages.append({"role": "assistant", "content": "", "tool_calls": [call]})
                # Tool response message (best-effort)
                messages.append({"role": "tool", "content": str(s.content or "")})
            else:
                # Assistant message with content (reasoning/response)
                if s.content:
                    messages.append({"role": "assistant", "content": str(s.content)})
        if trajectory.final_output:
            messages.append({"role": "assistant", "content": str(trajectory.final_output)})
        return messages

    def _strict_trajectory_match(self, trajectory: AgentTrajectory, reference: AgentTrajectory) -> StepResult:
        """Strict trajectory matching - exact tool sequence."""
        traj_tools = [step.tool_name for step in trajectory.steps if step.tool_name]
        ref_tools = [step.tool_name for step in reference.steps if step.tool_name]

        match = traj_tools == ref_tools

        return StepResult.ok(
            match=match,
            score=1.0 if match else 0.0,
            trajectory_tools=traj_tools,
            reference_tools=ref_tools,
            match_type="strict",
        )

    def _superset_trajectory_match(self, trajectory: AgentTrajectory, reference: AgentTrajectory) -> StepResult:
        """Superset trajectory matching - trajectory contains all reference tools."""
        traj_tools = {step.tool_name for step in trajectory.steps if step.tool_name}
        ref_tools = {step.tool_name for step in reference.steps if step.tool_name}

        match = ref_tools.issubset(traj_tools)
        coverage = len(ref_tools.intersection(traj_tools)) / len(ref_tools) if ref_tools else 1.0

        return StepResult.ok(
            match=match,
            score=coverage,
            coverage=coverage,
            missing_tools=list(ref_tools - traj_tools),
            extra_tools=list(traj_tools - ref_tools),
            match_type="superset",
        )

    def _unordered_trajectory_match(self, trajectory: AgentTrajectory, reference: AgentTrajectory) -> StepResult:
        """Unordered trajectory matching - same tools, any order."""
        traj_tools = {step.tool_name for step in trajectory.steps if step.tool_name}
        ref_tools = {step.tool_name for step in reference.steps if step.tool_name}

        match = traj_tools == ref_tools

        return StepResult.ok(
            match=match,
            score=1.0 if match else 0.0,
            trajectory_tools=sorted(traj_tools),
            reference_tools=sorted(ref_tools),
            match_type="unordered",
        )


class EnhancedCrewEvaluator:
    """Enhanced evaluator for CrewAI execution with trajectory analysis."""

    def __init__(
        self,
        router: Router | None = None,
        learning_engine: LearningEngine | None = None,
    ):
        self.trajectory_evaluator = TrajectoryEvaluator(router, learning_engine)
        self.enabled = os.getenv("ENABLE_ENHANCED_CREW_EVALUATION", "0") == "1"

    @tracing.trace_call("enhanced_crew_evaluator.evaluate_crew_execution")
    def evaluate_crew_execution(self, crew_execution_log: dict[str, Any]) -> StepResult:
        """Comprehensive evaluation of crew execution."""
        if not self.enabled:
            return StepResult.skip(reason="Enhanced crew evaluation disabled")

        try:
            # Extract trajectory
            trajectory = self.trajectory_evaluator.extract_trajectory_from_crew_execution(crew_execution_log)

            # Evaluate trajectory accuracy
            accuracy_result = self.trajectory_evaluator.evaluate_trajectory_accuracy(trajectory)

            if not accuracy_result.success:
                return accuracy_result

            # Additional crew-specific metrics
            crew_metrics = self._calculate_crew_metrics(trajectory)

            # Combine results
            combined_result = {
                "trajectory_evaluation": accuracy_result.data,
                "crew_metrics": crew_metrics,
                "session_id": trajectory.session_id,
                "evaluation_timestamp": time.time(),
            }

            return StepResult.ok(**combined_result)

        except Exception as e:
            return StepResult.fail(f"Enhanced crew evaluation failed: {e}")

    def _calculate_crew_metrics(self, trajectory: AgentTrajectory) -> dict[str, Any]:
        """Calculate crew-specific performance metrics."""
        return {
            "total_steps": len(trajectory.steps),
            "unique_agents": len({step.agent_role for step in trajectory.steps}),
            "tool_usage_count": len([step for step in trajectory.steps if step.tool_name]),
            "error_rate": len([step for step in trajectory.steps if step.error]) / len(trajectory.steps)
            if trajectory.steps
            else 0,
            "average_step_duration": trajectory.total_duration / len(trajectory.steps) if trajectory.steps else 0,
            "success_rate": 1.0 if trajectory.success else 0.0,
        }


__all__ = [
    "AgentTrajectory",
    "EnhancedCrewEvaluator",
    "TrajectoryEvaluator",
    "TrajectoryStep",
]
