"""LangSmith Evaluate API adapter for agent trajectory scoring.

This module provides an optional bridge into the LangSmith Evaluate API so that
trajectory accuracy scoring can be delegated to LangSmith when the integration
is enabled. The adapter intentionally mirrors the StepResult contract used
throughout the codebase and can gracefully fall back when LangSmith is not
available or misconfigured.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from platform.config.settings import SecureConfig, get_settings
from platform.core.step_result import ErrorCategory, ErrorContext, StepResult
from platform.observability import metrics
from typing import TYPE_CHECKING, Any


logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from eval.trajectory_evaluator import AgentTrajectory
EvaluationCallable = Callable[..., Any]


class LangSmithEvaluationAdapter:
    """Adapter responsible for delegating trajectory scoring to LangSmith."""

    DEFAULT_EVALUATION_NAME = "trajectory-accuracy"

    def __init__(self, settings: SecureConfig | None = None, evaluate_fn: EvaluationCallable | None = None) -> None:
        self._settings = settings or get_settings()
        self.enabled = bool(getattr(self._settings, "enable_langsmith_eval", False))
        self.api_key = getattr(self._settings, "langsmith_api_key", None)
        self.project_name = getattr(self._settings, "langsmith_project", "discord-intel-evals")
        self.dataset_name = getattr(self._settings, "langsmith_evaluation_dataset", None)
        self.evaluation_name = getattr(self._settings, "langsmith_evaluation_name", self.DEFAULT_EVALUATION_NAME)
        self._evaluate_fn: EvaluationCallable | None = evaluate_fn
        self._import_error: Exception | None = None
        if not self.enabled:
            return
        if not self.api_key:
            logger.debug("LangSmith evaluation enabled but API key is missing")
        if self._evaluate_fn is None:
            try:
                from langsmith import evaluate as _evaluate

                self._evaluate_fn = _evaluate
            except Exception as exc:
                self._import_error = exc
                logger.debug("LangSmith evaluate import failed: %s", exc)
        if self.api_key and "LANGSMITH_API_KEY" not in os.environ:
            os.environ["LANGSMITH_API_KEY"] = str(self.api_key)
        if self.project_name and "LANGSMITH_PROJECT" not in os.environ:
            os.environ.setdefault("LANGSMITH_PROJECT", str(self.project_name))

    def evaluate(self, trajectory: AgentTrajectory) -> StepResult:
        """Run LangSmith-based evaluation for the provided trajectory."""
        context = self._build_context(trajectory)
        if not self.enabled:
            return StepResult.skip(reason="LangSmith evaluation disabled")
        if not self.api_key:
            return StepResult.skip(reason="LangSmith API key not configured")
        if self._evaluate_fn is None:
            return self._handle_unavailable_adapter(context)
        payload = {
            "trajectory": self._serialize_trajectory(trajectory),
            "metadata": {
                "session_id": trajectory.session_id,
                "tenant": trajectory.tenant,
                "workspace": trajectory.workspace,
            },
        }
        try:
            response = self._evaluate_fn(
                evaluation=self.evaluation_name,
                data=payload,
                project_name=self.project_name,
                dataset_name=self.dataset_name,
            )
        except Exception as exc:
            self._record_degradation("runtime_error", context, error=str(exc))
            return StepResult.with_context(
                success=False,
                error=f"LangSmith evaluation failed: {exc}",
                error_category=ErrorCategory.DEPENDENCY_FAILURE,
                context=context,
            )
        metrics_data = self._extract_metrics(response)
        if not metrics_data:
            self._record_degradation("empty_metrics", context)
            return StepResult.with_context(
                success=False,
                error="LangSmith evaluation returned no metrics",
                error_category=ErrorCategory.PROCESSING,
                context=context,
            )
        score = bool(
            metrics_data.get("score")
            or metrics_data.get("passed")
            or metrics_data.get("success")
            or metrics_data.get("accuracy_score")
        )
        accuracy = self._coerce_float(metrics_data.get("accuracy_score") or metrics_data.get("accuracy") or 0.0)
        efficiency = self._coerce_float(
            metrics_data.get("efficiency_score") or metrics_data.get("efficiency") or accuracy
        )
        error_handling = self._coerce_float(
            metrics_data.get("error_handling_score") or metrics_data.get("error_handling") or accuracy
        )
        reasoning = (
            str(metrics_data.get("reasoning"))
            if metrics_data.get("reasoning") is not None
            else str(metrics_data.get("explanation"))
            if metrics_data.get("explanation") is not None
            else str(metrics_data.get("comment"))
            if metrics_data.get("comment") is not None
            else "LangSmith evaluation completed"
        )
        evaluation_id = (
            metrics_data.get("evaluation_id") or metrics_data.get("eval_run_id") or metrics_data.get("run_id")
        )
        result = StepResult.with_context(
            success=True,
            context=context,
            score=score,
            reasoning=reasoning,
            accuracy_score=accuracy,
            efficiency_score=efficiency,
            error_handling_score=error_handling,
            evaluation_id=evaluation_id,
            raw_metrics=self._sanitize(metrics_data),
        )
        result.metadata["evaluator"] = "LangSmith"
        result.metadata["langsmith_project"] = self.project_name
        if self.dataset_name:
            result.metadata["langsmith_dataset"] = self.dataset_name
        if evaluation_id:
            result.metadata["langsmith_evaluation_id"] = evaluation_id
        return result

    def _handle_unavailable_adapter(self, context: ErrorContext) -> StepResult:
        """Create a StepResult when LangSmith cannot be reached/imported."""
        error_message = "LangSmith evaluate integration unavailable"
        if self._import_error:
            error_message = f"LangSmith evaluate integration unavailable: {self._import_error}"
        self._record_degradation("import_error", context, error=error_message)
        return StepResult.with_context(
            success=False, error=error_message, error_category=ErrorCategory.DEPENDENCY_FAILURE, context=context
        )

    def _serialize_trajectory(self, trajectory: AgentTrajectory) -> dict[str, Any]:
        """Serialize AgentTrajectory into a LangSmith-friendly structure."""
        steps: list[dict[str, Any]] = []
        for step in trajectory.steps:
            steps.append(
                {
                    "timestamp": step.timestamp,
                    "agent_role": step.agent_role,
                    "action_type": step.action_type,
                    "content": step.content,
                    "tool_name": step.tool_name,
                    "tool_args": step.tool_args,
                    "success": step.success,
                    "error": step.error,
                }
            )
        return {
            "session_id": trajectory.session_id,
            "user_input": trajectory.user_input,
            "steps": steps,
            "final_output": trajectory.final_output,
            "total_duration": trajectory.total_duration,
            "success": trajectory.success,
            "tenant": trajectory.tenant,
            "workspace": trajectory.workspace,
        }

    def _extract_metrics(self, response: Any) -> dict[str, Any]:
        """Normalize LangSmith response into a metrics dictionary."""
        if response is None:
            return {}
        if isinstance(response, dict):
            if isinstance(response.get("metrics"), dict):
                merged = {**response["metrics"]}
                if "id" in response:
                    merged.setdefault("evaluation_id", response.get("id"))
                if isinstance(response.get("metadata"), dict):
                    merged.setdefault("metadata", response["metadata"])
                return merged
            return response
        metrics_dict = getattr(response, "metrics", None)
        if isinstance(metrics_dict, dict):
            merged = {**metrics_dict}
            evaluation_id = getattr(response, "id", None) or getattr(response, "evaluation_id", None)
            if evaluation_id:
                merged.setdefault("evaluation_id", evaluation_id)
            for attr in ("comment", "reasoning", "explanation"):
                if getattr(response, attr, None) and attr not in merged:
                    merged[attr] = getattr(response, attr)
            metadata_val = getattr(response, "metadata", None)
            if isinstance(metadata_val, dict):
                merged.setdefault("metadata", metadata_val)
            return merged
        return {}

    def _build_context(self, trajectory: AgentTrajectory) -> ErrorContext:
        tenant = trajectory.tenant or "global"
        workspace = trajectory.workspace or "global"
        return ErrorContext(
            operation="trajectory_evaluation",
            component="langsmith",
            tenant=tenant,
            workspace=workspace,
            session_id=trajectory.session_id,
        )

    def _record_degradation(self, event_type: str, context: ErrorContext, error: str | None = None) -> None:
        try:
            metrics.DEGRADATION_EVENTS.labels(
                tenant=context.tenant,
                workspace=context.workspace,
                component="langsmith_eval",
                event_type=event_type,
                severity="warn",
            ).inc()
        except Exception:
            logger.debug("Failed to record LangSmith degradation event", exc_info=True)
        if error:
            logger.debug("LangSmith degradation (%s): %s", event_type, error)

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, dict):
            return {str(k): self._sanitize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._sanitize(v) for v in value]
        return str(value)

    def _coerce_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


__all__ = ["LangSmithEvaluationAdapter"]
