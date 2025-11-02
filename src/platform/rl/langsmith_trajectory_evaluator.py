"""LangSmith trajectory evaluation with unified feedback emission.

This module bridges the LangSmith Evaluate adapter with the unified feedback
orchestrator. It allows agent trajectories to be scored via LangSmith and the
resulting metrics to be propagated into the reinforcement learning feedback
loops through the ``UnifiedFeedbackOrchestrator``.
"""

from __future__ import annotations

import logging
from platform.config.configuration import SecureConfig, get_config
from platform.core.step_result import StepResult
from platform.observability import metrics
from typing import TYPE_CHECKING, Any

from core.orchestration.application import UnifiedFeedbackOrchestrator, get_orchestrator
from eval.langsmith_adapter import LangSmithEvaluationAdapter


if TYPE_CHECKING:
    from eval.trajectory_evaluator import AgentTrajectory
logger = logging.getLogger(__name__)


class LangSmithTrajectoryEvaluator:
    """Evaluate agent trajectories with LangSmith and emit unified feedback."""

    def __init__(
        self,
        orchestrator: UnifiedFeedbackOrchestrator | None = None,
        *,
        settings: SecureConfig | None = None,
        adapter: LangSmithEvaluationAdapter | None = None,
    ) -> None:
        self._settings = settings or get_config()
        self._langsmith_enabled = bool(getattr(self._settings, "enable_langsmith_eval", False))
        self._feedback_enabled = bool(getattr(self._settings, "enable_unified_feedback", True))
        self._orchestrator = orchestrator
        self._adapter = adapter
        if self._adapter is None and self._langsmith_enabled:
            try:
                self._adapter = LangSmithEvaluationAdapter(self._settings)
            except Exception as exc:
                logger.warning("Failed to initialize LangSmith adapter: %s", exc)
                self._adapter = None

    def evaluate(self, trajectory: AgentTrajectory) -> StepResult:
        """Run LangSmith-based evaluation for the trajectory."""
        if not self._langsmith_enabled:
            return StepResult.skip(reason="langsmith_eval_disabled")
        if self._adapter is None:
            return StepResult.skip(reason="langsmith_adapter_unavailable")
        result = self._adapter.evaluate(trajectory)
        metrics.TRAJECTORY_EVALUATIONS.labels(
            **metrics.label_ctx({"success": str(result.success and (not result.skipped)).lower()})
        ).inc()
        return result

    def evaluate_and_submit(self, trajectory: AgentTrajectory) -> StepResult:
        """Evaluate a trajectory and forward the scores to the orchestrator."""
        result = self.evaluate(trajectory)
        return self.submit_feedback(trajectory, result)

    def submit_feedback(self, trajectory: AgentTrajectory, evaluation: StepResult) -> StepResult:
        """Push evaluation metrics into the unified feedback orchestrator."""
        metadata = evaluation.metadata.setdefault("langsmith_trajectory_evaluator", {})
        if evaluation.skipped:
            metadata.update({"feedback_submitted": False, "reason": "evaluation_skipped"})
            return evaluation
        if not evaluation.success:
            metadata.update({"feedback_submitted": False, "reason": "evaluation_failed"})
            if evaluation.error:
                metadata["error"] = evaluation.error
            return evaluation
        if not self._feedback_enabled:
            metadata.update({"feedback_submitted": False, "reason": "feedback_disabled"})
            return evaluation
        payload = self._build_feedback_payload(evaluation)
        if not payload:
            metadata.update({"feedback_submitted": False, "reason": "insufficient_metrics"})
            return evaluation
        orchestrator = self._ensure_orchestrator()
        if orchestrator is None:
            metadata.update({"feedback_submitted": False, "reason": "orchestrator_unavailable"})
            return evaluation
        try:
            feedback_result = orchestrator.submit_trajectory_feedback(trajectory, payload)
        except Exception as exc:
            logger.warning("Unified feedback submission failed: %s", exc)
            metadata.update({"feedback_submitted": False, "reason": "orchestrator_exception", "error": str(exc)})
            return evaluation
        metadata.update(
            {
                "feedback_submitted": feedback_result.success and (not feedback_result.skipped),
                "orchestrator_status": feedback_result.custom_status
                or ("skipped" if feedback_result.skipped else "success" if feedback_result.success else "error"),
                "feedback_payload": payload,
            }
        )
        if feedback_result.error:
            metadata["orchestrator_error"] = feedback_result.error
        metadata["orchestrator_result"] = feedback_result.to_dict()
        return evaluation

    def _ensure_orchestrator(self) -> UnifiedFeedbackOrchestrator | None:
        if self._orchestrator is not None:
            return self._orchestrator
        orchestrator = get_orchestrator(auto_create=False)
        if orchestrator is not None:
            self._orchestrator = orchestrator
        return self._orchestrator

    @staticmethod
    def _build_feedback_payload(evaluation: StepResult) -> dict[str, Any] | None:
        data = evaluation.data
        if not data:
            return None
        accuracy = LangSmithTrajectoryEvaluator._coerce_float(data.get("accuracy_score"), default=0.0)
        efficiency = LangSmithTrajectoryEvaluator._coerce_float(data.get("efficiency_score"), default=accuracy)
        error_handling = LangSmithTrajectoryEvaluator._coerce_float(data.get("error_handling_score"), default=accuracy)
        if accuracy == 0.0 and efficiency == 0.0 and (error_handling == 0.0):
            return None
        overall = LangSmithTrajectoryEvaluator._coerce_float(
            data.get("overall_score"), default=0.5 * accuracy + 0.3 * efficiency + 0.2 * error_handling
        )
        overall = max(0.0, min(1.0, overall))
        confidence = LangSmithTrajectoryEvaluator._coerce_float(data.get("confidence"), default=accuracy)
        confidence = max(0.0, min(1.0, confidence))
        reasoning = str(data.get("reasoning", ""))
        evaluation_id = evaluation.metadata.get("langsmith_evaluation_id") or data.get("evaluation_id")
        payload: dict[str, Any] = {
            "score": bool(data.get("score", True)),
            "overall_score": overall,
            "accuracy_score": accuracy,
            "efficiency_score": efficiency,
            "error_handling_score": error_handling,
            "confidence": confidence,
            "reasoning": reasoning,
        }
        if evaluation_id:
            payload["evaluation_id"] = evaluation_id
        return payload

    @staticmethod
    def _coerce_float(value: Any, *, default: float = 0.0) -> float:
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)


__all__ = ["LangSmithTrajectoryEvaluator"]
