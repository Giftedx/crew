"""Pipeline mixins providing metrics and execution helpers."""

from __future__ import annotations

import contextlib
import time
from collections.abc import Callable, Iterable
from typing import Any

from obs import metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from .middleware import PipelineStepMiddleware, StepContext
from .types import PipelineRunResult


class PipelineMetricsMixin:
    """Shared instrumentation helpers for pipeline implementations."""

    _orchestrator: str

    def _step_outcome(self, result: StepResult | Exception | None) -> str:
        """Normalise step outcomes into metric-friendly status labels."""

        if result is None:
            return "skipped"
        if isinstance(result, Exception):
            return "error"
        if result.custom_status == "skipped":
            return "skipped"
        if result.custom_status == "uncertain":
            return "success"
        return "success" if result.success else "error"

    def _record_step_metrics(self, step: str, outcome: str, duration: float | None) -> None:
        labels = metrics.label_ctx()
        try:
            if outcome == "success":
                metrics.PIPELINE_STEPS_COMPLETED.labels(**labels, step=step).inc()
            elif outcome == "skipped":
                metrics.PIPELINE_STEPS_SKIPPED.labels(**labels, step=step).inc()
            else:
                metrics.PIPELINE_STEPS_FAILED.labels(**labels, step=step).inc()
            if duration is not None:
                metrics.PIPELINE_STEP_DURATION.labels(
                    **labels,
                    step=step,
                    orchestrator=self._orchestrator,
                    status=outcome,
                ).observe(duration)
        except Exception:  # pragma: no cover - metrics optional
            logger = getattr(self, "logger", None)
            if logger is not None:
                logger.debug("metrics emit failed (step %s, outcome %s)", step, outcome)

    def _record_step_skip(self, step: str) -> None:
        self._record_step_metrics(step, "skipped", None)

    @contextlib.contextmanager
    def _pipeline_inflight(self) -> Any:
        labels = metrics.label_ctx()
        try:
            metrics.PIPELINE_INFLIGHT.labels(
                **labels,
                orchestrator=self._orchestrator,
            ).inc()
        except Exception:  # pragma: no cover - metrics optional
            logger = getattr(self, "logger", None)
            if logger is not None:
                logger.debug("metrics emit failed (inflight inc)")
        try:
            yield
        finally:
            try:
                metrics.PIPELINE_INFLIGHT.labels(
                    **labels,
                    orchestrator=self._orchestrator,
                ).dec()
            except Exception:  # pragma: no cover - metrics optional
                logger = getattr(self, "logger", None)
                if logger is not None:
                    logger.debug("metrics emit failed (inflight dec)")

    def _record_pipeline_duration(self, status: str, duration: float) -> None:
        labels = metrics.label_ctx()
        try:
            metrics.PIPELINE_DURATION.labels(**labels, status=status).observe(duration)
            metrics.PIPELINE_TOTAL_DURATION.labels(
                **labels,
                orchestrator=self._orchestrator,
                status=status,
            ).observe(duration)
        except Exception:  # pragma: no cover - metrics optional
            logger = getattr(self, "logger", None)
            if logger is not None:
                logger.debug("metrics emit failed (pipeline duration - %s)", status)

    def _finalize_pipeline(
        self,
        start_time: float,
        status: str,
        payload: PipelineRunResult,
        *,
        duration: float | None = None,
    ) -> PipelineRunResult:
        if duration is None:
            duration = max(time.monotonic() - start_time, 0.0)
        self._record_pipeline_duration(status, duration)
        payload.setdefault("status", status)
        return payload


class PipelineExecutionMixin(PipelineMetricsMixin):
    """Provides `_execute_step`, building upon retry helpers from the base class."""

    async def _execute_step(
        self,
        step: str,
        func: Callable[..., Any],
        *args: Any,
        retries: int | None = None,
        retry_delay: float = 2.0,
        check_tool_rate_limit: bool = True,
        **kwargs: Any,
    ) -> StepResult:
        start = time.monotonic()
        result: StepResult | None = None
        error: Exception | None = None
        attempts = retries if retries is not None else 3
        middlewares: Iterable[PipelineStepMiddleware] = getattr(self, "step_middlewares", ())
        context = StepContext(step=step, args=args, kwargs=kwargs, pipeline=self)
        try:
            await self._dispatch_before_step(context, middlewares)
            result = await self._run_with_retries(  # type: ignore[attr-defined]
                func,
                *args,
                step=step,
                attempts=attempts,
                delay=retry_delay,
                check_tool_rate_limit=check_tool_rate_limit,
                **kwargs,
            )
            context.result = result
            await self._dispatch_after_step(context, middlewares)
            return result
        except Exception as exc:  # pragma: no cover - unexpected path
            error = exc
            context.exception = exc
            await self._dispatch_on_error(context, middlewares)
            logger = getattr(self, "logger", None)
            if logger is not None:
                logger.exception("%s step raised unhandled exception", step)
            return StepResult.fail(str(exc))
        finally:
            outcome = self._step_outcome(result if error is None else error)
            duration = time.monotonic() - start
            self._record_step_metrics(step, outcome, duration)

    async def _dispatch_before_step(
        self,
        context: StepContext,
        middlewares: Iterable[PipelineStepMiddleware],
    ) -> None:
        await self._run_middlewares(middlewares, "before_step", context)

    async def _dispatch_after_step(
        self,
        context: StepContext,
        middlewares: Iterable[PipelineStepMiddleware],
    ) -> None:
        await self._run_middlewares(middlewares, "after_step", context)

    async def _dispatch_on_error(
        self,
        context: StepContext,
        middlewares: Iterable[PipelineStepMiddleware],
    ) -> None:
        await self._run_middlewares(middlewares, "on_error", context)

    async def _run_middlewares(
        self,
        middlewares: Iterable[PipelineStepMiddleware],
        hook_name: str,
        context: StepContext,
    ) -> None:
        for middleware in middlewares:
            hook = getattr(middleware, hook_name, None)
            if hook is None:
                continue
            try:
                await hook(context)
            except Exception as exc:  # pragma: no cover - middleware failures should not break pipeline
                logger = getattr(self, "logger", None)
                if logger is not None:
                    logger.warning(
                        "Middleware %s.%s failed: %s",
                        middleware.__class__.__name__,
                        hook_name,
                        exc,
                    )
