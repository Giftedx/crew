"""LangSmith-based self-evaluation gates for autonomous quality control.

This module implements shadow-mode evaluation gates that score pipeline outputs
using LangSmith's evaluation framework. Scores feed into Thompson Sampling routing
and trigger auto-rollback on regressions.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from platform.config.configuration import get_config
from platform.observability import metrics
from typing import Any

from ultimate_discord_intelligence_bot.tenancy import current_tenant


logger = logging.getLogger(__name__)


@dataclass
class EvalMetrics:
    """Evaluation metrics for a single run."""

    quality_score: float
    safety_score: float
    relevance_score: float
    coherence_score: float
    overall_score: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalResult:
    """Result of an evaluation run."""

    passed: bool
    metrics: EvalMetrics
    feedback: str
    should_rollback: bool
    regression_detected: bool


class LangSmithEvaluator:
    """Self-evaluation gate using LangSmith for quality/safety scoring.

    Integrates with LangSmith to score pipeline outputs (analysis, fallacy detection,
    perspective analysis) and detect regressions. Operates in shadow mode by default,
    only logging scores without blocking execution.

    Features:
    - Per-tenant/task baseline tracking
    - Auto-rollback on regression >threshold
    - Shadow mode for safe rollout
    - Metrics export for Thompson Sampling reward calculation
    """

    def __init__(self, shadow_mode: bool | None = None, regression_threshold: float | None = None) -> None:
        """Initialize evaluator with configuration.

        Args:
            shadow_mode: If True, only log scores without blocking (default from config)
            regression_threshold: Score drop % that triggers rollback (default from config)
        """
        config = get_config()
        self.enabled = config.enable_self_eval_gates
        self.shadow_mode = shadow_mode if shadow_mode is not None else config.self_eval_shadow_mode
        self.regression_threshold = (
            regression_threshold if regression_threshold is not None else config.self_eval_regression_threshold
        )
        self._langsmith_client: Any = None
        self._baselines: dict[str, EvalMetrics] = {}
        if self.enabled:
            self._initialize_langsmith()

    def _initialize_langsmith(self) -> None:
        """Initialize LangSmith client if available."""
        config = get_config()
        if not config.langsmith_api_key:
            logger.warning("LangSmith API key not set; evaluation gates disabled")
            self.enabled = False
            return
        try:
            from langsmith import Client

            self._langsmith_client = Client(api_key=config.langsmith_api_key)
            logger.info("LangSmith evaluator initialized in %s mode", "shadow" if self.shadow_mode else "active")
        except Exception as e:
            logger.warning("Failed to initialize LangSmith client: %s; evaluation gates disabled", e)
            self.enabled = False

    async def evaluate_output(
        self,
        task_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> EvalResult:
        """Evaluate a pipeline output and check for regressions.

        Args:
            task_name: Name of the task (e.g., "analysis", "fallacy_detection")
            input_data: Input to the task (e.g., transcript, URL)
            output_data: Output from the task (e.g., analysis result)
            context: Optional additional context

        Returns:
            EvalResult with scores, feedback, and rollback decision
        """
        if not self.enabled:
            return EvalResult(
                passed=True,
                metrics=EvalMetrics(
                    quality_score=1.0,
                    safety_score=1.0,
                    relevance_score=1.0,
                    coherence_score=1.0,
                    overall_score=1.0,
                    latency_ms=0.0,
                ),
                feedback="Evaluation disabled",
                should_rollback=False,
                regression_detected=False,
            )
        start = time.perf_counter()
        try:
            tenant_ctx = current_tenant()
            tenant_id = tenant_ctx.tenant_id if tenant_ctx else "default"
            task_key = f"{tenant_id}:{task_name}"
            metrics_result = await self._compute_metrics(task_name, input_data, output_data, context or {})
            latency_ms = (time.perf_counter() - start) * 1000
            metrics_result.latency_ms = latency_ms
            regression_detected, feedback = self._check_regression(task_key, metrics_result)
            if (
                task_key not in self._baselines
                or metrics_result.overall_score > self._baselines[task_key].overall_score
            ):
                self._baselines[task_key] = metrics_result
            should_rollback = regression_detected and (not self.shadow_mode)
            self._export_metrics(task_name, metrics_result, regression_detected)
            return EvalResult(
                passed=not should_rollback,
                metrics=metrics_result,
                feedback=feedback,
                should_rollback=should_rollback,
                regression_detected=regression_detected,
            )
        except Exception as e:
            logger.exception("Evaluation failed for task %s: %s", task_name, e)
            return EvalResult(
                passed=self.shadow_mode,
                metrics=EvalMetrics(
                    quality_score=0.0,
                    safety_score=0.0,
                    relevance_score=0.0,
                    coherence_score=0.0,
                    overall_score=0.0,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    metadata={"error": str(e)},
                ),
                feedback=f"Evaluation error: {e}",
                should_rollback=not self.shadow_mode,
                regression_detected=False,
            )

    async def _compute_metrics(
        self, task_name: str, input_data: dict[str, Any], output_data: dict[str, Any], context: dict[str, Any]
    ) -> EvalMetrics:
        """Compute evaluation metrics using LangSmith evaluators.

        This is a placeholder implementation. In production, you would:
        1. Call LangSmith's evaluation API with custom evaluators
        2. Use pre-defined eval datasets for regression testing
        3. Implement task-specific scoring (e.g., fallacy detection accuracy)
        """
        quality_score = self._score_quality(output_data)
        safety_score = self._score_safety(output_data)
        relevance_score = self._score_relevance(input_data, output_data)
        coherence_score = self._score_coherence(output_data)
        overall_score = 0.4 * quality_score + 0.3 * safety_score + 0.2 * relevance_score + 0.1 * coherence_score
        return EvalMetrics(
            quality_score=quality_score,
            safety_score=safety_score,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            overall_score=overall_score,
            latency_ms=0.0,
            metadata={"task": task_name, "evaluator": "langsmith", "version": "1.0"},
        )

    def _score_quality(self, output: dict[str, Any]) -> float:
        """Score output quality (0.0-1.0)."""
        if not output:
            return 0.0
        if "error" in output or "failed" in str(output).lower():
            return 0.3
        expected_keys = {"summary", "analysis", "content", "result"}
        present = sum(1 for k in expected_keys if k in output)
        return min(1.0, present / len(expected_keys) + 0.5)

    def _score_safety(self, output: dict[str, Any]) -> float:
        """Score safety (absence of harmful content) (0.0-1.0)."""
        content = str(output).lower()
        unsafe_markers = ["unsafe", "harmful", "inappropriate", "violation"]
        if any(marker in content for marker in unsafe_markers):
            return 0.2
        return 1.0

    def _score_relevance(self, input_data: dict[str, Any], output: dict[str, Any]) -> float:
        """Score relevance of output to input (0.0-1.0)."""
        input_text = str(input_data).lower()
        output_text = str(output).lower()
        if not input_text or not output_text:
            return 0.5
        input_tokens = set(input_text.split())
        output_tokens = set(output_text.split())
        overlap = len(input_tokens & output_tokens)
        return min(1.0, overlap / max(len(input_tokens), 1) * 2)

    def _score_coherence(self, output: dict[str, Any]) -> float:
        """Score coherence/consistency of output (0.0-1.0)."""
        if not output:
            return 0.0
        text_content = " ".join(str(v) for v in output.values() if isinstance(v, str))
        if len(text_content) < 50:
            return 0.5
        return 0.9

    def _check_regression(self, task_key: str, metrics: EvalMetrics) -> tuple[bool, str]:
        """Check if current metrics represent a regression from baseline.

        Returns:
            (regression_detected, feedback_message)
        """
        if task_key not in self._baselines:
            return (False, "First run; establishing baseline")
        baseline = self._baselines[task_key]
        score_drop = baseline.overall_score - metrics.overall_score
        if score_drop > self.regression_threshold:
            feedback = f"Regression detected: score dropped {score_drop:.2%} (baseline: {baseline.overall_score:.3f}, current: {metrics.overall_score:.3f})"
            return (True, feedback)
        feedback = f"Score: {metrics.overall_score:.3f} (baseline: {baseline.overall_score:.3f})"
        return (False, feedback)

    def _export_metrics(self, task_name: str, eval_metrics: EvalMetrics, regression_detected: bool) -> None:
        """Export evaluation metrics to observability backend."""
        try:
            labels = {"task": task_name, "evaluator": "langsmith", "regression": str(regression_detected)}
            metrics.get_metrics().histogram("eval_overall_score", eval_metrics.overall_score, labels=labels)
            metrics.get_metrics().histogram("eval_quality_score", eval_metrics.quality_score, labels=labels)
            metrics.get_metrics().histogram("eval_safety_score", eval_metrics.safety_score, labels=labels)
            metrics.get_metrics().histogram("eval_latency_ms", eval_metrics.latency_ms, labels=labels)
            if regression_detected:
                metrics.get_metrics().counter("eval_regressions_total", labels=labels)
        except Exception as e:
            logger.warning("Failed to export eval metrics: %s", e)

    def get_reward_signal(self, eval_result: EvalResult) -> float:
        """Convert evaluation result to reward signal for Thompson Sampling.

        Returns:
            Reward in [0.0, 1.0] range
        """
        if not eval_result.passed and (not self.shadow_mode):
            return 0.0
        quality_component = eval_result.metrics.overall_score
        latency_component = max(0.0, 1.0 - eval_result.metrics.latency_ms / 2000)
        return 0.7 * quality_component + 0.3 * latency_component


__all__ = ["EvalMetrics", "EvalResult", "LangSmithEvaluator"]
