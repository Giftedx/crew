"""High-level orchestration for the content pipeline."""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import ExitStack, contextmanager, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from core.secure_config import get_config

from obs import metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import current_tenant


if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterator

    from ultimate_discord_intelligence_bot.services.request_budget import (
        RequestCostTracker,
    )

    from .types import PipelineRunResult

from obs.logfire_spans import span as logfire_span

from .base import PipelineBase
from .mixins import PipelineExecutionMixin
from .tracing import tracing_module


@dataclass
class _DriveArtifacts:
    result: StepResult
    outcome: str


@dataclass
class _PipelineContext:
    span: Any
    start_time: float
    tracker: RequestCostTracker | None
    langfuse_service: Any | None = None
    langfuse_trace: Any | None = None
    langfuse_pipeline_span: Any | None = None
    langfuse_spans: dict[str, Any] = field(default_factory=dict)
    langfuse_trace_finalized: bool = False
    langfuse_trace_output: dict[str, Any] | None = None
    langfuse_trace_error: str | None = None


@dataclass
class _TranscriptionArtifacts:
    transcription: StepResult
    drive: _DriveArtifacts
    filtered_transcript: str
    transcript_task: asyncio.Task[StepResult] | None


@dataclass
class _AnalysisArtifacts:
    analysis: StepResult
    fallacy: StepResult
    perspective: StepResult
    summary: str
    memory_payload: dict[str, Any]
    analysis_memory_task: asyncio.Task[StepResult]
    discord_task: asyncio.Task[StepResult] | None
    discord_placeholder: StepResult
    graph_task: asyncio.Task[StepResult] | None
    graph_placeholder: StepResult
    hipporag_task: asyncio.Task[StepResult] | None
    hipporag_placeholder: StepResult
    compression: dict[str, Any] | None


class ContentPipeline(PipelineExecutionMixin, PipelineBase):
    """Full content pipeline orchestrator composed from modular helpers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._active_pipeline_ctx: _PipelineContext | None = None

    # ------------------------------------------------------------------
    # Langfuse helpers
    # ------------------------------------------------------------------

    def _langfuse_prepare_payload(self, value: Any) -> Any:
        if isinstance(value, StepResult):
            return self._langfuse_prepare_payload(value.to_dict())
        if isinstance(value, dict):
            return {str(k): self._langfuse_prepare_payload(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._langfuse_prepare_payload(v) for v in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _langfuse_start_span(
        self,
        ctx: _PipelineContext,
        name: str,
        input_data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        service = getattr(ctx, "langfuse_service", None)
        trace = getattr(ctx, "langfuse_trace", None)
        if not service or not trace:
            return
        result = service.create_span(
            trace,
            name,
            self._langfuse_prepare_payload(input_data),
            metadata=self._langfuse_prepare_payload(metadata or {}),
        )
        if result.success:
            span = result.data.get("span")
            if span is not None:
                ctx.langfuse_spans[name] = span

    def _langfuse_finish_span(
        self,
        ctx: _PipelineContext,
        name: str,
        output_data: dict[str, Any] | None = None,
        *,
        error: str | None = None,
    ) -> None:
        service = getattr(ctx, "langfuse_service", None)
        if not service:
            return
        span = ctx.langfuse_spans.pop(name, None)
        if not span:
            return
        payload = self._langfuse_prepare_payload(output_data or {})
        service.update_span(span, payload, error=error)

    def _langfuse_error_message(self, payload: Any) -> str | None:
        if isinstance(payload, dict):
            for key in ("error", "message", "detail", "status_message"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
        return None

    def _langfuse_finalize_trace(
        self,
        ctx: _PipelineContext | None,
        status: str,
        payload: dict[str, Any],
        duration: float,
    ) -> None:
        if ctx is None or not ctx.langfuse_service or not ctx.langfuse_trace:
            return

        service = ctx.langfuse_service
        sanitized = self._langfuse_prepare_payload(payload)
        ctx.langfuse_trace_output = sanitized

        error_message = ctx.langfuse_trace_error
        if status != "success":
            error_message = error_message or self._langfuse_error_message(payload)

        metadata = {"duration_seconds": duration, "status": status}
        if ctx.langfuse_pipeline_span:
            service.update_span(
                ctx.langfuse_pipeline_span,
                sanitized,
                error=error_message,
            )
            ctx.langfuse_pipeline_span = None

        service.finalize_trace(
            ctx.langfuse_trace,
            sanitized,
            error=error_message,
            metadata=metadata,
        )
        ctx.langfuse_trace_finalized = True
        ctx.langfuse_trace_error = error_message

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _finalize_pipeline(
        self,
        start_time: float,
        status: str,
        payload: dict[str, Any],
        *,
        duration: float | None = None,
    ) -> dict[str, Any]:
        ctx = self._active_pipeline_ctx
        resolved_duration = duration if duration is not None else max(time.monotonic() - start_time, 0.0)
        if ctx and not ctx.langfuse_trace_finalized:
            self._langfuse_finalize_trace(ctx, status, payload, resolved_duration)
        return super()._finalize_pipeline(start_time, status, payload, duration=resolved_duration)

    async def process_video(self, url: str, quality: str = "1080p") -> PipelineRunResult:
        observability = getattr(self, "_step_observability", None)
        if isinstance(observability, dict):
            observability.clear()

        rate_limit_error = self._rate_limit_failure()
        if rate_limit_error is not None:
            return rate_limit_error

        pipeline_start = time.monotonic()
        total_limit, per_task_limits = self._resolve_budget_limits()
        with self._pipeline_context(url, quality, pipeline_start, total_limit, per_task_limits) as ctx:
            return await self._run_pipeline(ctx, url, quality)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _pipeline_context(
        self,
        url: str,
        quality: str,
        start_time: float,
        total_limit: float | None,
        per_task_limits: dict[str, float],
    ) -> Iterator[_PipelineContext]:
        with ExitStack() as stack:
            tracker = stack.enter_context(
                self._pipeline_pkg.track_request_budget(  # type: ignore[attr-defined]
                    total_limit=total_limit,
                    per_task_limits=per_task_limits,
                )
            )
            stack.enter_context(self._pipeline_inflight())
            span = stack.enter_context(tracing_module.start_span("pipeline.process_video"))
            span.set_attribute("url", url)
            span.set_attribute("quality", quality)
            self.logger.info("Starting concurrent pipeline for %s (quality: %s)", url, quality)
            self._increment_pipeline_requests()
            langfuse_service = getattr(self, "langfuse_service", None)
            langfuse_trace = None
            langfuse_pipeline_span = None
            if langfuse_service and getattr(langfuse_service, "enabled", False):
                tenant_ctx = current_tenant()
                tenant_id = getattr(tenant_ctx, "tenant_id", None) if tenant_ctx else None
                workspace_id = getattr(tenant_ctx, "workspace_id", None) if tenant_ctx else None
                user_id = tenant_id or workspace_id or "global"
                trace_result = langfuse_service.create_trace(
                    name="pipeline.process_video",
                    user_id=user_id,
                    metadata={"orchestrator": self._orchestrator, "workspace": workspace_id},
                    input_data={"url": url, "quality": quality},
                    tags=[self._orchestrator],
                )
                if trace_result.success:
                    langfuse_trace = trace_result.data.get("trace")
                    span_result = langfuse_service.create_span(
                        langfuse_trace,
                        "pipeline_execution",
                        {"url": url, "quality": quality},
                        metadata={"phase": "pipeline_start"},
                    )
                    if span_result.success:
                        langfuse_pipeline_span = span_result.data.get("span")

            ctx = _PipelineContext(
                span=span,
                start_time=start_time,
                tracker=tracker,
                langfuse_service=langfuse_service,
                langfuse_trace=langfuse_trace,
                langfuse_pipeline_span=langfuse_pipeline_span,
            )
            self._active_pipeline_ctx = ctx
            try:
                yield ctx
            except Exception as exc:
                ctx.langfuse_trace_error = str(exc)
                if langfuse_service and langfuse_pipeline_span:
                    langfuse_service.update_span(
                        langfuse_pipeline_span,
                        {"status": "exception", "exception": str(exc)},
                        error=str(exc),
                    )
                    ctx.langfuse_pipeline_span = None
                if langfuse_service and langfuse_trace and not ctx.langfuse_trace_finalized:
                    langfuse_service.finalize_trace(
                        langfuse_trace,
                        {"status": "exception"},
                        error=str(exc),
                    )
                    ctx.langfuse_trace_finalized = True
                raise
            finally:
                self._active_pipeline_ctx = None
                if langfuse_service and ctx.langfuse_pipeline_span and not ctx.langfuse_trace_finalized:
                    langfuse_service.update_span(
                        ctx.langfuse_pipeline_span,
                        ctx.langfuse_trace_output or {"status": "unknown"},
                        error=ctx.langfuse_trace_error,
                    )
                    ctx.langfuse_pipeline_span = None
                if langfuse_service and langfuse_trace and not ctx.langfuse_trace_finalized:
                    langfuse_service.finalize_trace(
                        langfuse_trace,
                        ctx.langfuse_trace_output or {"status": "unknown"},
                        error=ctx.langfuse_trace_error,
                    )
                    ctx.langfuse_trace_finalized = True

    async def _run_pipeline(self, ctx: _PipelineContext, url: str, quality: str) -> PipelineRunResult:
        with logfire_span("pipeline.download_phase", url=url, quality=quality):
            download_info, failure = await self._download_phase(ctx, url, quality)
        if failure is not None:
            return failure
        assert download_info is not None  # for type checkers

        # Week 4 Phase 2 Week 2: Checkpoint 1 - Post-download early exit
        (
            should_exit,
            exit_reason,
            exit_confidence,
        ) = await self._check_early_exit_condition(
            ctx,
            "post_download",
            {
                "duration": download_info.data.get("duration", 0),
                "view_count": download_info.data.get("view_count", 0),
                "age_days": download_info.data.get("age_days", 0),
                "title_spam_score": self._calculate_spam_score(download_info.data.get("title", "")),
            },
        )
        if should_exit:
            return await self._early_exit_processing(ctx, download_info, None, exit_reason, exit_confidence)

        with logfire_span("pipeline.transcription_phase"):
            transcription_bundle, failure = await self._transcription_phase(ctx, download_info)
        if failure is not None:
            return failure
        assert transcription_bundle is not None

        # Week 4 Phase 2: Content type routing phase
        routing_result = await self._content_routing_phase(ctx, download_info, transcription_bundle)

        # Week 4 Phase 2 Week 2: Checkpoint 2 - Post-transcription early exit
        (
            should_exit,
            exit_reason,
            exit_confidence,
        ) = await self._check_early_exit_condition(
            ctx,
            "post_transcription",
            {
                "transcript_length": len(transcription_bundle.filtered_transcript),
                "transcription_confidence": transcription_bundle.transcription.data.get("confidence", 1.0),
                "word_error_rate": self._calculate_wer(transcription_bundle.filtered_transcript),
                "repetition_ratio": self._calculate_repetition_ratio(transcription_bundle.filtered_transcript),
                "unique_word_ratio": self._calculate_vocabulary_diversity(transcription_bundle.filtered_transcript),
            },
            routing_result,
        )
        if should_exit:
            return await self._early_exit_processing(
                ctx, download_info, transcription_bundle, exit_reason, exit_confidence
            )

        # Week 4 Phase 1: Quality filtering phase (now uses routing thresholds)
        quality_result, should_skip_analysis = await self._quality_filtering_phase(
            ctx, transcription_bundle.filtered_transcript, routing_result
        )

        # Week 4 Phase 2 Week 2: Checkpoint 3 - Post-quality-filtering early exit
        if quality_result.success:
            qr_data = quality_result.data
            if "result" in qr_data and isinstance(qr_data["result"], dict):
                qr_data = qr_data["result"]

            (
                should_exit,
                exit_reason,
                exit_confidence,
            ) = await self._check_early_exit_condition(
                ctx,
                "post_quality_filtering",
                {
                    "overall_quality": qr_data.get("overall_score", 0.0),
                    "assessment_confidence": qr_data.get("confidence", 0.0),
                    "coherence_score": qr_data.get("quality_metrics", {}).get("coherence", 0.0),
                    "completeness_score": qr_data.get("quality_metrics", {}).get("completeness", 0.0),
                    "informativeness_score": qr_data.get("quality_metrics", {}).get("informativeness", 0.0),
                },
                routing_result,
            )
            if should_exit:
                return await self._early_exit_processing(
                    ctx,
                    download_info,
                    transcription_bundle,
                    exit_reason,
                    exit_confidence,
                    quality_result,
                )

        if should_skip_analysis:
            return await self._lightweight_processing_phase(ctx, download_info, transcription_bundle, quality_result)

        with logfire_span("pipeline.analysis_phase"):
            analysis_bundle, failure = await self._analysis_phase(ctx, download_info, transcription_bundle)
        if failure is not None:
            return failure
        assert analysis_bundle is not None

        return await self._finalize_phase(ctx, download_info, transcription_bundle, analysis_bundle)

    async def _content_routing_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
        transcription_bundle: _TranscriptionArtifacts,
    ) -> StepResult:
        """Route content based on type classification (Week 4 Phase 2)."""
        import os

        self._langfuse_start_span(
            ctx,
            "content_routing",
            {
                "title": download_info.data.get("title"),
                "video_id": download_info.data.get("video_id"),
            },
            metadata={"phase": "content_routing"},
        )

        routing_enabled = os.getenv("ENABLE_CONTENT_ROUTING", "1") == "1"
        result: StepResult
        error_message: str | None = None

        try:
            if not routing_enabled:
                self.logger.debug("Content routing disabled, using default thresholds")
                result = StepResult.ok(result={"routing_enabled": False, "content_type": "general"})
            else:
                from ultimate_discord_intelligence_bot.tools import ContentTypeRoutingTool

                routing_input = {
                    "transcript": transcription_bundle.filtered_transcript,
                    "title": download_info.data.get("title", ""),
                    "description": download_info.data.get("description", ""),
                    "metadata": download_info.data.get("metadata", {}),
                }

                routing_tool = ContentTypeRoutingTool()
                routing_result = routing_tool.run(routing_input)

                if not routing_result.success:
                    error_message = routing_result.error or "routing_failed"
                    self.logger.warning(
                        "Content routing failed, using default thresholds: %s",
                        routing_result.error,
                    )
                    result = StepResult.ok(result={"routing_enabled": False, "content_type": "general"})
                else:
                    result = routing_result
        except Exception as exc:
            error_message = str(exc)
            self.logger.warning(
                "Content routing failed with exception, using default thresholds: %s",
                error_message,
            )
            result = StepResult.ok(
                result={
                    "routing_enabled": False,
                    "content_type": "general",
                    "error": error_message,
                }
            )

        routing_payload: dict[str, Any] = {"routing_enabled": routing_enabled}
        data = result.data
        if "result" in data and isinstance(data["result"], dict):
            data = data["result"]
        if isinstance(data, dict):
            classification = data.get("classification", {})
            routing_payload.update(
                {
                    "success": result.success,
                    "content_type": classification.get("primary_type", "general"),
                    "confidence": classification.get("confidence"),
                    "pipeline": data.get("routing", {}).get("pipeline")
                    if isinstance(data.get("routing"), dict)
                    else None,
                }
            )

        self._langfuse_finish_span(ctx, "content_routing", routing_payload, error=error_message)

        if result.success:
            content_type = routing_payload.get("content_type", "general")
            confidence = routing_payload.get("confidence", 0.0) or 0.0
            pipeline = routing_payload.get("pipeline", "standard_pipeline") or "standard_pipeline"
            self.logger.info(
                "Content routed as '%s' (confidence: %.2f, pipeline: %s)",
                content_type,
                confidence,
                pipeline,
            )
            ctx.span.set_attribute("content_type", content_type)
            ctx.span.set_attribute("routing_confidence", confidence)
            ctx.span.set_attribute("routing_pipeline", pipeline)

            try:
                if hasattr(metrics, "CONTENT_TYPE_ROUTED"):
                    metrics.CONTENT_TYPE_ROUTED.labels(**metrics.label_ctx(), content_type=content_type).inc()
            except Exception:
                pass

        return result

    def _load_content_type_thresholds(self, routing_result: StepResult | None) -> dict[str, float]:
        """Load content-type specific quality thresholds from config."""
        import os
        from pathlib import Path

        import yaml

        # Default thresholds (fallback if config loading fails)
        default_thresholds = {
            "quality_threshold": float(os.getenv("QUALITY_MIN_OVERALL", "0.65")),
            "coherence_threshold": float(os.getenv("QUALITY_MIN_COHERENCE", "0.60")),
            "completeness_threshold": float(os.getenv("QUALITY_MIN_COMPLETENESS", "0.60")),
            "informativeness_threshold": float(os.getenv("QUALITY_MIN_INFORMATIVENESS", "0.65")),
        }

        # If no routing result, use defaults
        if routing_result is None or not routing_result.success:
            return default_thresholds

        # Extract content type from routing result
        routing_data = routing_result.data
        if "result" in routing_data and isinstance(routing_data["result"], dict):
            routing_data = routing_data["result"]

        content_type = routing_data.get("classification", {}).get("primary_type", "general")

        # Try to load content type config
        try:
            config_path = Path("config/content_types.yaml")
            if not config_path.exists():
                self.logger.debug("Content types config not found, using defaults")
                return default_thresholds

            with config_path.open("r") as f:
                config = yaml.safe_load(f)

            # Check if routing is enabled in config
            if not config.get("enabled", True):
                self.logger.debug("Content routing disabled in config")
                return default_thresholds

            # Get content type specific thresholds
            content_types = config.get("content_types", {})
            if content_type not in content_types:
                self.logger.warning(f"Content type '{content_type}' not in config, using defaults")
                return default_thresholds

            type_config = content_types[content_type]
            thresholds = {
                "quality_threshold": type_config.get("quality_threshold", default_thresholds["quality_threshold"]),
                "coherence_threshold": type_config.get(
                    "coherence_threshold", default_thresholds["coherence_threshold"]
                ),
                "completeness_threshold": type_config.get(
                    "completeness_threshold",
                    default_thresholds["completeness_threshold"],
                ),
                "informativeness_threshold": type_config.get(
                    "informativeness_threshold",
                    default_thresholds["informativeness_threshold"],
                ),
            }

            self.logger.info(
                f"Loaded thresholds for content type '{content_type}': quality={thresholds['quality_threshold']:.2f}"
            )
            return thresholds

        except Exception as e:
            self.logger.warning(f"Failed to load content type config: {e}, using defaults")
            return default_thresholds

    async def _quality_filtering_phase(
        self,
        ctx: _PipelineContext,
        transcript: str,
        routing_result: StepResult | None = None,
    ) -> tuple[StepResult, bool]:
        """Assess transcript quality and determine processing path (now with content-type aware thresholds)."""
        # Check if quality filtering is enabled
        import os

        self._langfuse_start_span(
            ctx,
            "quality_filtering",
            {"transcript_length": len(transcript)},
            metadata={"phase": "quality_filtering"},
        )

        quality_enabled = os.getenv("ENABLE_QUALITY_FILTERING", "1") == "1"
        if not quality_enabled:
            result = StepResult.ok(
                result={
                    "should_process": True,
                    "bypass_reason": "quality_filtering_disabled",
                }
            )
            skip_analysis = False
        else:
            content_type_thresholds = self._load_content_type_thresholds(routing_result)
            try:
                from ultimate_discord_intelligence_bot.tools import (
                    ContentQualityAssessmentTool,
                )

                quality_tool = ContentQualityAssessmentTool()
                quality_input = {
                    "transcript": transcript,
                    "thresholds": content_type_thresholds,
                }
                result = quality_tool.run(quality_input)

                if not result.success:
                    self.logger.warning(
                        "Quality assessment failed, proceeding with full analysis: %s",
                        result.error,
                    )
                    metrics.get_metrics().counter("quality_filtering_errors_total").inc()
                    skip_analysis = False
                else:
                    qr_data = result.data
                    if "result" in qr_data and isinstance(qr_data["result"], dict):
                        qr_data = qr_data["result"]

                    should_process = qr_data.get("should_process", True)
                    bypass_reason = qr_data.get("bypass_reason", "")
                    quality_score = qr_data.get("overall_score", 0.0)

                    if not should_process:
                        self.logger.info(
                            "Quality filtering bypass: %s (score: %.2f)",
                            bypass_reason,
                            quality_score,
                        )
                        ctx.span.set_attribute("quality_bypass", True)
                        ctx.span.set_attribute("bypass_reason", bypass_reason)
                        ctx.span.set_attribute("quality_score", quality_score)
                        try:  # pragma: no cover - metrics optional
                            if hasattr(metrics, "PIPELINE_STEPS_SKIPPED"):
                                metrics.PIPELINE_STEPS_SKIPPED.labels(
                                    **metrics.label_ctx(), step="quality_filtering"
                                ).inc()
                        except Exception:
                            pass
                    else:
                        ctx.span.set_attribute("quality_bypass", False)
                        ctx.span.set_attribute("quality_score", quality_score)
                        try:  # pragma: no cover - metrics optional
                            if hasattr(metrics, "PIPELINE_STEPS_COMPLETED"):
                                metrics.PIPELINE_STEPS_COMPLETED.labels(
                                    **metrics.label_ctx(), step="quality_filtering"
                                ).inc()
                        except Exception:
                            pass

                    skip_analysis = not should_process
            except Exception as exc:
                self.logger.warning(
                    "Quality filtering failed with exception, proceeding with full analysis: %s",
                    str(exc),
                )
                metrics.get_metrics().counter("quality_filtering_exceptions_total").inc()
                result = StepResult.fail(error=str(exc))
                skip_analysis = False

        qr_output: dict[str, Any] = {"quality_filtering_enabled": quality_enabled}
        if result.success:
            data = result.data
            if "result" in data and isinstance(data["result"], dict):
                data = data["result"]
            if isinstance(data, dict):
                qr_output.update(
                    {
                        "should_process": data.get("should_process", True),
                        "overall_score": data.get("overall_score"),
                        "bypass_reason": data.get("bypass_reason"),
                    }
                )

        error_message = result.error if not result.success else None
        self._langfuse_finish_span(ctx, "quality_filtering", qr_output, error=error_message)

        return result, skip_analysis

    def _load_early_exit_config(self) -> dict[str, Any]:
        """Load early exit configuration from config/early_exit.yaml."""
        import yaml

        # Default config (used if file doesn't exist or loading fails)
        default_config = {
            "enabled": True,
            "global": {
                "min_exit_confidence": 0.80,
                "continue_on_error": True,
            },
            "checkpoints": {},
        }

        try:
            config_path = Path("config/early_exit.yaml")
            if not config_path.exists():
                self.logger.debug("Early exit config not found, using defaults")
                return default_config

            with config_path.open() as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                self.logger.warning("Invalid early exit config format, using defaults")
                return default_config

            return config

        except Exception as e:
            self.logger.warning(f"Failed to load early exit config: {e}, using defaults")
            return default_config

    async def _check_early_exit_condition(
        self,
        ctx: _PipelineContext,
        checkpoint_name: str,
        checkpoint_data: dict[str, Any],
        routing_result: StepResult | None = None,
    ) -> tuple[bool, str, float]:
        """
        Check if content should exit early at this checkpoint.

        Args:
            ctx: Pipeline context
            checkpoint_name: Name of checkpoint (post_download, post_transcription, etc.)
            checkpoint_data: Data to evaluate against checkpoint conditions
            routing_result: Optional routing result for content-type specific overrides

        Returns:
            Tuple of (should_exit, exit_reason, confidence)
        """
        import os

        # Check if early exit is enabled globally
        early_exit_enabled = os.getenv("ENABLE_EARLY_EXIT", "1") == "1"
        if not early_exit_enabled:
            return False, "", 0.0

        truthy = {"1", "true", "yes", "on"}
        quality_filtering_enabled = os.getenv("ENABLE_QUALITY_FILTERING", "0").lower() in truthy

        try:
            # Load config
            config = self._load_early_exit_config()
            if not config.get("enabled", True):
                return False, "", 0.0

            # Get content type for overrides
            content_type = "general"
            if routing_result and routing_result.success:
                routing_data = routing_result.data
                if "result" in routing_data and isinstance(routing_data["result"], dict):
                    routing_data = routing_data["result"]
                content_type = routing_data.get("classification", {}).get("primary_type", "general")

            # Check for content-type specific overrides
            overrides = config.get("content_type_overrides", {}).get(content_type, {})
            checkpoint_config = overrides.get("checkpoints", {}).get(checkpoint_name)

            # If no override, use default checkpoint config
            if checkpoint_config is None:
                checkpoint_config = config.get("checkpoints", {}).get(checkpoint_name, {})

            # If checkpoint disabled or not found, don't exit
            if not checkpoint_config or not checkpoint_config.get("enabled", True):
                return False, "", 0.0

            # Get exit conditions for this checkpoint
            exit_conditions = checkpoint_config.get("exit_conditions", [])
            global_config = config.get("global", {})
            min_confidence = global_config.get("min_exit_confidence", 0.80)

            # Evaluate each condition
            for condition in exit_conditions:
                if not condition.get("enabled", True):
                    continue

                condition_name = condition.get("name", "unknown")
                condition_expr = condition.get("condition", "")
                condition_confidence = condition.get("confidence", 0.0)
                condition_reason = condition.get("reason", "Early exit condition met")

                # Only process if confidence meets minimum
                if condition_confidence < min_confidence:
                    continue

                # Evaluate condition
                try:
                    # Create evaluation context with checkpoint data
                    eval_context = checkpoint_data.copy()

                    # Simple condition evaluation (supports basic comparisons)
                    if self._evaluate_condition(condition_expr, eval_context):
                        if (
                            checkpoint_name == "post_transcription"
                            and condition_name == "very_short_transcript"
                            and quality_filtering_enabled
                        ):
                            self.logger.debug(
                                "Early exit condition '%s' suppressed to allow quality filtering", condition_name
                            )
                            continue
                        self.logger.info(
                            f"Early exit triggered at {checkpoint_name}: {condition_name} "
                            f"(confidence: {condition_confidence:.2f})"
                        )

                        # Set tracing attributes
                        ctx.span.set_attribute("early_exit", True)
                        ctx.span.set_attribute("exit_checkpoint", checkpoint_name)
                        ctx.span.set_attribute("exit_condition", condition_name)
                        ctx.span.set_attribute("exit_confidence", condition_confidence)

                        # Emit metrics (best-effort)
                        try:
                            if hasattr(metrics, "PIPELINE_EARLY_EXITS"):
                                metrics.PIPELINE_EARLY_EXITS.labels(
                                    **metrics.label_ctx(), checkpoint=checkpoint_name
                                ).inc()
                        except Exception:
                            pass

                        return True, condition_reason, condition_confidence

                except Exception as e:
                    self.logger.warning(f"Failed to evaluate condition '{condition_name}' at {checkpoint_name}: {e}")
                    # Continue to next condition on evaluation error
                    if not global_config.get("continue_on_error", True):
                        raise

            # No exit conditions met
            return False, "", 0.0

        except Exception as e:
            self.logger.warning(f"Early exit check failed at {checkpoint_name}: {e}")
            # On error, don't exit (safe fallback)
            return False, "", 0.0

    def _evaluate_condition(self, condition_expr: str, context: dict[str, Any]) -> bool:
        """
        Safely evaluate a condition expression against context data.

        Supports simple comparison operations:
        - duration < 30
        - quality_score > 0.80
        - duration < 120 and transcript_length < 500
        """
        try:
            # Build a safe evaluation namespace
            safe_namespace = {
                # Operators
                "__builtins__": {},
                # Context values
                **context,
            }

            # Evaluate the condition (restricted eval for safety)
            result = eval(condition_expr, {"__builtins__": {}}, safe_namespace)
            return bool(result)

        except Exception as e:
            self.logger.warning(f"Condition evaluation failed: {condition_expr} - {e}")
            return False

    async def _early_exit_processing(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
        transcription_bundle: _TranscriptionArtifacts | None,
        exit_reason: str,
        exit_confidence: float,
        quality_result: StepResult | None = None,
    ) -> PipelineRunResult:
        """
        Process content that exited early at a checkpoint.

        Creates a minimal summary and optionally stores in memory based on
        checkpoint configuration.
        """
        start_time = time.monotonic()

        # Build minimal summary
        title = download_info.data.get("title", "Unknown")
        source_url = download_info.data.get("source_url", "")
        duration = download_info.data.get("duration", 0)

        basic_summary = f"Content exited early: {exit_reason}"
        if transcription_bundle:
            transcript_preview = transcription_bundle.filtered_transcript[:200]
            if len(transcription_bundle.filtered_transcript) > 200:
                transcript_preview += "..."
        else:
            transcript_preview = "No transcript available"

        # Get quality score if available
        quality_score = 0.0
        if quality_result and quality_result.success:
            qr_data = quality_result.data
            if "result" in qr_data and isinstance(qr_data["result"], dict):
                qr_data = qr_data["result"]
            quality_score = qr_data.get("overall_score", 0.0)

        # Create lightweight memory payload
        memory_payload = {
            "source_url": source_url,
            "title": title,
            "summary": basic_summary,
            "exit_reason": exit_reason,
            "exit_confidence": exit_confidence,
            "quality_score": quality_score,
            "processing_type": "early_exit",
            "duration": duration,
            "transcript_preview": transcript_preview,
            "processed_at": time.time(),
        }

        # Store in memory (lightweight)
        memory_task = asyncio.create_task(self._store_lightweight_memory(memory_payload), name="early_exit_memory")

        # Wait for memory storage (with timeout)
        memory_result = None
        try:
            memory_result = await asyncio.wait_for(memory_task, timeout=5.0)
        except TimeoutError:
            self.logger.warning("Early exit memory storage timed out")
            memory_result = StepResult.fail(error="Memory storage timeout")
        except Exception as e:
            self.logger.warning(f"Early exit memory storage failed: {e}")
            memory_result = StepResult.fail(error=str(e))

        # Record metrics
        processing_duration = time.monotonic() - start_time
        try:
            if hasattr(metrics, "PIPELINE_PROCESSING_TIME"):
                metrics.PIPELINE_PROCESSING_TIME.labels(**metrics.label_ctx(), processing_type="early_exit").observe(
                    processing_duration
                )
        except Exception:
            pass

        # Set span attributes
        ctx.span.set_attribute("processing_type", "early_exit")
        ctx.span.set_attribute("exit_reason", exit_reason)
        ctx.span.set_attribute("exit_confidence", exit_confidence)
        ctx.span.set_attribute("processing_duration_seconds", processing_duration)

        self.logger.info(
            f"Early exit processing complete: {exit_reason} (confidence: {exit_confidence:.2f}, "
            f"duration: {processing_duration:.2f}s)"
        )

        return self._finalize_pipeline(
            ctx.start_time,
            "success",
            {
                "status": "success",
                "processing_type": "early_exit",
                "exit_reason": exit_reason,
                "exit_confidence": exit_confidence,
                "quality_score": quality_score,
                "summary": basic_summary,
                "title": title,
                "memory_stored": memory_result.success if memory_result else False,
                "processing_duration": processing_duration,
                "time_saved_estimate": "75-90%",
            },
        )

    async def _lightweight_processing_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
        transcription_bundle: _TranscriptionArtifacts,
        quality_result: StepResult,
    ) -> PipelineRunResult:
        """Lightweight processing for low-quality content."""
        start_time = time.monotonic()

        span_input = {
            "video_id": download_info.data.get("video_id"),
            "transcript_length": len(transcription_bundle.filtered_transcript),
            "quality_result_success": quality_result.success,
        }
        self._langfuse_start_span(
            ctx,
            "lightweight_processing",
            span_input,
            metadata={"phase": "lightweight_processing"},
        )

        span_output: dict[str, Any] = {}
        try:
            # Basic summary from quality assessment
            qr_data = quality_result.data
            if "result" in qr_data and isinstance(qr_data["result"], dict):
                qr_data = qr_data["result"]

            basic_summary = qr_data.get("recommendation_details", "Basic content processed")
            quality_score = qr_data.get("overall_score", 0.0)
            bypass_reason = qr_data.get("bypass_reason", "")
            raw_metrics = {}
            qm = qr_data.get("quality_metrics")
            if isinstance(qm, dict):  # Capture raw quality metrics for observability & analytics
                raw_metrics = {
                    k: v
                    for k, v in qm.items()
                    if k
                    in {
                        "word_count",
                        "sentence_count",
                        "avg_sentence_length",
                        "coherence_score",
                        "topic_clarity_score",
                        "language_quality_score",
                        "overall_quality_score",
                    }
                }

            # Enhanced lightweight analysis
            title = download_info.data.get("title", "")
            source_url = download_info.data.get("source_url", "")
            duration = download_info.data.get("duration", 0)

            # Create lightweight memory payload
            memory_payload = {
                "source_url": source_url,
                "title": title,
                "summary": basic_summary,
                "quality_score": quality_score,
                "processing_type": "lightweight",
                "bypass_reason": bypass_reason,
                "duration": duration,
                "quality_metrics": raw_metrics,
                "transcript_preview": transcription_bundle.filtered_transcript[:200] + "..."
                if len(transcription_bundle.filtered_transcript) > 200
                else transcription_bundle.filtered_transcript,
                "processed_at": time.time(),
            }

            # Optional: Store in memory with lightweight flag
            memory_task = asyncio.create_task(self._store_lightweight_memory(memory_payload), name="lightweight_memory")

            # Wait for memory storage (with timeout)
            memory_result = None
            try:
                memory_result = await asyncio.wait_for(memory_task, timeout=10.0)
            except TimeoutError:
                self.logger.warning("Lightweight memory storage timed out")
                memory_task.cancel()
            except Exception as e:
                self.logger.warning(f"Lightweight memory storage failed: {e}")

            # Record metrics
            processing_duration = time.monotonic() - start_time
            try:  # pragma: no cover - metrics optional
                if hasattr(metrics, "PIPELINE_STEP_DURATION"):
                    metrics.PIPELINE_STEP_DURATION.labels(**metrics.label_ctx(), step="lightweight_processing").observe(
                        processing_duration
                    )
            except Exception:
                pass

            # Set span attributes for observability
            ctx.span.set_attribute("processing_type", "lightweight")
            ctx.span.set_attribute("quality_score", quality_score)
            ctx.span.set_attribute("bypass_reason", bypass_reason)
            ctx.span.set_attribute("processing_duration_seconds", processing_duration)

            span_output.update(
                {
                    "status": "success",
                    "quality_score": quality_score,
                    "bypass_reason": bypass_reason,
                    "memory_stored": bool(memory_result and memory_result.success),
                    "processing_duration": processing_duration,
                }
            )

            result = self._finalize_pipeline(
                ctx.start_time,
                "success",
                {
                    "status": "success",
                    "processing_type": "lightweight",
                    "quality_score": quality_score,
                    "summary": basic_summary,
                    "title": title,
                    "bypass_reason": bypass_reason,
                    "memory_stored": memory_result.success if memory_result else False,
                    "processing_duration": processing_duration,
                    "time_saved_estimate": "60-75%",
                    "quality_metrics": raw_metrics,
                },
            )
            self._langfuse_finish_span(ctx, "lightweight_processing", span_output)
            return result
        except Exception as exc:
            error_msg = str(exc)
            span_output.setdefault("status", "error")
            span_output["error"] = error_msg
            self._langfuse_finish_span(ctx, "lightweight_processing", span_output, error=error_msg)
            raise

    async def _store_lightweight_memory(self, payload: dict[str, Any]) -> StepResult:
        """Store lightweight content summary in memory."""
        try:
            from ultimate_discord_intelligence_bot.tools import MemoryStorageTool

            memory_tool = MemoryStorageTool()
            return memory_tool.run(payload)
        except Exception as e:
            self.logger.warning(f"Lightweight memory storage failed: {e}")
            return StepResult.fail(error=str(e))

    async def _download_phase(
        self,
        ctx: _PipelineContext,
        url: str,
        quality: str,
    ) -> tuple[StepResult | None, PipelineRunResult | None]:
        self._langfuse_start_span(
            ctx,
            "download",
            {"url": url, "quality": quality},
            metadata={"phase": "download"},
        )
        download_info = await self._run_download(url, quality)
        if not download_info.success:
            return None, self._fail(ctx.span, ctx.start_time, "download", download_info.to_dict())

        local_path = download_info.data["local_path"]
        download_info.data.setdefault("source_url", url)
        if not download_info.data.get("platform"):
            extractor = download_info.data.get("extractor") or download_info.data.get("tool")
            if extractor:
                download_info.data["platform"] = str(extractor).lower()
        ctx.span.set_attribute("local_path", local_path)
        span_output = {
            "status": "success",
            "platform": download_info.data.get("platform"),
            "video_id": download_info.data.get("video_id"),
            "duration": download_info.data.get("duration"),
        }
        self._langfuse_finish_span(ctx, "download", span_output)
        return download_info, None

    async def _transcription_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
    ) -> tuple[_TranscriptionArtifacts | None, PipelineRunResult | None]:
        local_path = download_info.data["local_path"]
        video_id = download_info.data.get("video_id")
        self._langfuse_start_span(
            ctx,
            "transcription",
            {
                "video_id": video_id,
                "local_path": local_path,
            },
            metadata={"phase": "transcription"},
        )
        transcription_task = asyncio.create_task(self._run_transcription(local_path, video_id), name="transcription")
        drive_task, drive_info = self._start_drive_upload(download_info, local_path)

        transcription = await transcription_task
        if not transcription.success:
            fallback = await self._attempt_transcription_fallback(download_info, transcription)
            if fallback is not None:
                self.logger.warning(
                    "Transcription unavailable (%s); using %s-derived fallback",
                    transcription.error or "unknown error",
                    fallback.data.get("transcript_source", "metadata"),
                )
                transcription = fallback
            else:
                if drive_task and not drive_task.done():
                    drive_task.cancel()
                error_message = transcription.error or "transcription_failed"
                self._langfuse_finish_span(ctx, "transcription", transcription.to_dict(), error=error_message)
                return None, self._fail(ctx.span, ctx.start_time, "transcription", transcription.to_dict())

        drive_artifacts = await self._await_drive_result(drive_task, drive_info, ctx.span, ctx.start_time)
        if isinstance(drive_artifacts, dict):
            error_message = self._langfuse_error_message(drive_artifacts)
            self._langfuse_finish_span(ctx, "transcription", drive_artifacts, error=error_message)
            return None, drive_artifacts
        drive_artifacts = cast("_DriveArtifacts", drive_artifacts)

        filtered_transcript = self._apply_pii_filtering(
            transcription.data.get("transcript", ""),
            "transcript",
        )
        # Defer transcript storage scheduling until analysis phase begins so that
        # analysis memory writes occur deterministically before transcript storage
        # in tests expecting specific call ordering.
        transcript_task: asyncio.Task[StepResult] | None = None

        span_output = {
            "status": "success",
            "transcription_confidence": transcription.data.get("confidence"),
            "drive_outcome": drive_artifacts.outcome,
            "transcript_length": len(filtered_transcript),
        }
        self._langfuse_finish_span(ctx, "transcription", span_output)

        return (
            _TranscriptionArtifacts(
                transcription=transcription,
                drive=drive_artifacts,
                filtered_transcript=filtered_transcript,
                transcript_task=transcript_task,
            ),
            None,
        )

    async def _analysis_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
        transcription_bundle: _TranscriptionArtifacts,
    ) -> tuple[_AnalysisArtifacts | None, PipelineRunResult | None]:
        filtered_transcript = transcription_bundle.filtered_transcript
        transcript_task = transcription_bundle.transcript_task
        compression_meta: dict[str, Any] | None = None

        analysis_span_output: dict[str, Any] = {
            "video_id": download_info.data.get("video_id"),
            "platform": download_info.data.get("platform"),
            "transcript_length": len(filtered_transcript),
        }
        self._langfuse_start_span(
            ctx,
            "analysis",
            analysis_span_output,
            metadata={"phase": "analysis"},
        )

        try:
            analysis = await self._run_analysis(filtered_transcript)
        except Exception as exc:  # pragma: no cover - defensive
            if transcript_task is None:
                transcript_task = self._schedule_transcript_storage(filtered_transcript, download_info)
            if transcript_task is not None and not transcript_task.done():
                await self._await_transcript_best_effort(transcript_task)
            error_msg = str(exc)
            analysis_span_output.update({"status": "analysis_exception", "error": error_msg})
            self._langfuse_finish_span(ctx, "analysis", analysis_span_output, error=error_msg)
            error_payload = {"status": "error", "error": error_msg, "step": "analysis"}
            return None, self._fail(ctx.span, ctx.start_time, "analysis", error_payload)

        if isinstance(analysis, Exception) or not analysis.success:
            if transcript_task is None:
                transcript_task = self._schedule_transcript_storage(filtered_transcript, download_info)
            if transcript_task is not None and not transcript_task.done():
                await self._await_transcript_best_effort(transcript_task)
            error_msg = str(analysis) if isinstance(analysis, Exception) else analysis.error or "analysis failed"
            analysis_span_output.update({"status": "analysis_failed", "error": error_msg})
            self._langfuse_finish_span(ctx, "analysis", analysis_span_output, error=error_msg)
            error_payload = {"status": "error", "error": error_msg, "step": "analysis"}
            return None, self._fail(ctx.span, ctx.start_time, "analysis", error_payload)

        analysis_span_output.update(
            {
                "analysis_keys": list(analysis.data.keys())[:10],
                "analysis_success": True,
            }
        )

        compressed_transcript, compression_meta = self._maybe_compress_transcript(filtered_transcript)
        if compression_meta:
            analysis.data.setdefault("transcript_compression", compression_meta)
            analysis_span_output["compression"] = compression_meta

        fallacy_task = asyncio.create_task(self._run_fallacy(compressed_transcript), name="fallacy")
        perspective_task = asyncio.create_task(
            self._run_perspective(compressed_transcript, analysis.data),
            name="perspective",
        )

        fallacy = await fallacy_task
        if not fallacy.success:
            if not perspective_task.done():
                perspective_task.cancel()
                with suppress(Exception):
                    await perspective_task
            fallacy_error = fallacy.error or "fallacy failed"
            analysis_span_output.update({"status": "fallacy_failed", "fallacy_error": fallacy_error})
            self._langfuse_finish_span(ctx, "analysis", analysis_span_output, error=fallacy_error)
            return None, self._fail(
                ctx.span,
                ctx.start_time,
                "fallacy",
                {"status": "error", "error": fallacy_error, "step": "fallacy"},
            )

        try:
            perspective = await perspective_task
        except Exception as exc:  # pragma: no cover - defensive
            error_msg = str(exc)
            analysis_span_output.update({"status": "perspective_exception", "perspective_error": error_msg})
            self._langfuse_finish_span(ctx, "analysis", analysis_span_output, error=error_msg)
            return None, self._fail(
                ctx.span,
                ctx.start_time,
                "perspective",
                {"status": "error", "error": error_msg, "step": "perspective"},
            )

        if not perspective.success:
            perspective_payload = perspective.to_dict()
            perspective_payload["step"] = "perspective"
            perspective_error = perspective.error or "perspective failed"
            analysis_span_output.update({"status": "perspective_failed", "perspective_error": perspective_error})
            self._langfuse_finish_span(ctx, "analysis", analysis_span_output, error=perspective_error)
            return None, self._fail(ctx.span, ctx.start_time, "perspective", perspective_payload)

        if compression_meta:
            fallacy.data.setdefault("transcript_compression", compression_meta)
            perspective.data.setdefault("transcript_compression", compression_meta)

        summary = self._apply_pii_filtering(perspective.data.get("summary", ""), "summary")
        perspective.data["summary"] = summary
        analysis_span_output.update(
            {
                "status": "success",
                "summary_length": len(summary),
                "sentiment": analysis.data.get("sentiment"),
            }
        )

        memory_payload = {
            "video_id": download_info.data["video_id"],
            "title": download_info.data["title"],
            "platform": download_info.data.get("platform", "unknown"),
            "sentiment": analysis.data.get("sentiment"),
            "keywords": analysis.data.get("keywords"),
            "summary": summary,
        }
        if compression_meta:
            memory_payload["transcript_compression"] = compression_meta

        analysis_memory_task = asyncio.create_task(
            self._run_analysis_memory(summary, memory_payload),
            name="analysis_memory",
        )

        if transcript_task is None:
            transcript_task = self._schedule_transcript_storage(filtered_transcript, download_info)

        graph_task: asyncio.Task[StepResult] | None = None
        graph_placeholder = StepResult.skip(data={"state": "skipped", "reason": "graph_memory_disabled"})
        hipporag_task: asyncio.Task[StepResult] | None = None
        hipporag_placeholder = StepResult.skip(data={"state": "skipped", "reason": "hipporag_memory_disabled"})

        if getattr(self, "graph_memory", None) is not None and getattr(self, "_graph_memory_enabled", False):
            tags: set[str] = set()
            platform = memory_payload.get("platform")
            if isinstance(platform, str) and platform:
                tags.add(f"platform:{platform.lower()}")
            sentiment = analysis.data.get("sentiment")
            if isinstance(sentiment, str) and sentiment:
                tags.add(f"sentiment:{sentiment}")
            keywords = memory_payload.get("keywords")
            if isinstance(keywords, list):
                for kw in keywords[:5]:
                    if isinstance(kw, str) and kw:
                        tags.add(f"keyword:{kw.lower()}")
            graph_task = asyncio.create_task(
                self._execute_step(
                    "graph_memory",
                    self.graph_memory.run,  # type: ignore[union-attr]
                    text=summary,
                    metadata=memory_payload,
                    index="analysis",
                    tags=sorted(tags),
                ),
                name="graph_memory",
            )
            graph_placeholder = StepResult.skip(data={"state": "pending"})
        else:
            self._record_step_skip("graph_memory")

        # HippoRAG continual memory integration
        if getattr(self, "hipporag_memory", None) is not None and getattr(self, "_hipporag_memory_enabled", False):
            # Create consolidated tags for continual memory
            hippo_tags = []
            platform = memory_payload.get("platform")
            if isinstance(platform, str) and platform:
                hippo_tags.append(f"platform:{platform.lower()}")
            sentiment = analysis.data.get("sentiment")
            if isinstance(sentiment, str) and sentiment:
                hippo_tags.append(f"sentiment:{sentiment}")
            keywords = memory_payload.get("keywords")
            if isinstance(keywords, list):
                for kw in keywords[:3]:  # Fewer tags for HippoRAG to avoid noise
                    if isinstance(kw, str) and kw:
                        hippo_tags.append(f"keyword:{kw.lower()}")

            hipporag_task = asyncio.create_task(
                self._execute_step(
                    "hipporag_memory",
                    self.hipporag_memory.run,  # type: ignore[union-attr]
                    text=summary,
                    metadata=memory_payload,
                    index="continual_memory",
                    tags=hippo_tags,
                    consolidate=True,
                ),
                name="hipporag_memory",
            )
            hipporag_placeholder = StepResult.skip(data={"state": "pending"})
        else:
            self._record_step_skip("hipporag_memory")

        discord_task, discord_placeholder = self._schedule_discord_post(
            transcription_bundle.drive,
            download_info,
            analysis,
            fallacy,
            perspective,
        )

        analysis_span_output.update(
            {
                "memory_payload_keys": list(memory_payload.keys())[:10],
                "graph_memory_enabled": graph_task is not None,
                "hipporag_memory_enabled": hipporag_task is not None,
            }
        )
        self._langfuse_finish_span(ctx, "analysis", analysis_span_output)

        return (
            _AnalysisArtifacts(
                analysis=analysis,
                fallacy=fallacy,
                perspective=perspective,
                summary=summary,
                memory_payload=memory_payload,
                analysis_memory_task=analysis_memory_task,
                discord_task=discord_task,
                discord_placeholder=discord_placeholder,
                graph_task=graph_task,
                graph_placeholder=graph_placeholder,
                hipporag_task=hipporag_task,
                hipporag_placeholder=hipporag_placeholder,
                compression=compression_meta,
            ),
            None,
        )

    async def _finalize_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
        transcription_bundle: _TranscriptionArtifacts,
        analysis_bundle: _AnalysisArtifacts,
    ) -> PipelineRunResult:
        memory_result, graph_result, hipporag_result = await self._await_storage_tasks(
            analysis_bundle.analysis_memory_task,
            transcription_bundle.transcript_task,
            analysis_bundle.graph_task,
            analysis_bundle.hipporag_task,
        )
        if isinstance(memory_result, Exception):
            if analysis_bundle.discord_task:
                analysis_bundle.discord_task.cancel()
            return self._fail(
                ctx.span,
                ctx.start_time,
                "memory",
                {"status": "error", "step": "memory", "error": str(memory_result)},
            )
        memory_step = cast("StepResult", memory_result)
        if not memory_step.success:
            if analysis_bundle.discord_task:
                analysis_bundle.discord_task.cancel()
            memory_payload = memory_step.to_dict()
            memory_payload["step"] = "memory"
            return self._fail(ctx.span, ctx.start_time, "memory", memory_payload)

        graph_step = analysis_bundle.graph_placeholder
        if graph_result is not None:
            if isinstance(graph_result, Exception):
                self.logger.warning("Graph memory task raised exception: %s", graph_result)
                graph_step = StepResult.fail(str(graph_result))
            else:
                graph_step = cast("StepResult", graph_result)
        if graph_step is not None and not graph_step.success and graph_step.custom_status != "skipped":
            self.logger.warning("Graph memory storage failed: %s", graph_step.error)
        elif graph_step is not None and graph_step.success:
            graph_id = graph_step.data.get("graph_id")
            if graph_id:
                analysis_bundle.memory_payload.setdefault("graph_id", graph_id)

        # Handle HippoRAG continual memory results
        hipporag_step = analysis_bundle.hipporag_placeholder
        if hipporag_result is not None:
            if isinstance(hipporag_result, Exception):
                self.logger.warning("HippoRAG memory task raised exception: %s", hipporag_result)
                hipporag_step = StepResult.fail(str(hipporag_result))
            else:
                hipporag_step = cast("StepResult", hipporag_result)
        if hipporag_step is not None and not hipporag_step.success and hipporag_step.custom_status != "skipped":
            self.logger.warning("HippoRAG memory storage failed: %s", hipporag_step.error)
        elif hipporag_step is not None and hipporag_step.success:
            memory_id = hipporag_step.data.get("memory_id")
            if memory_id:
                analysis_bundle.memory_payload.setdefault("hipporag_memory_id", memory_id)

        discord_result = analysis_bundle.discord_placeholder
        if analysis_bundle.discord_task:
            discord_result = await analysis_bundle.discord_task
            if not discord_result.success:
                payload = discord_result.to_dict()
                payload["step"] = "discord"
                return self._fail(ctx.span, ctx.start_time, "discord", payload)

        duration = time.monotonic() - ctx.start_time
        ctx.span.set_attribute("pipeline_duration_seconds", duration)
        self.logger.info("✅ Concurrent pipeline completed in %.2f seconds", duration)

        return self._finalize_pipeline(
            ctx.start_time,
            "success",
            {
                "status": "success",
                "download": download_info.to_dict(),
                "drive": transcription_bundle.drive.result.to_dict(),
                "transcription": transcription_bundle.transcription.to_dict(),
                "analysis": analysis_bundle.analysis.to_dict(),
                "fallacy": analysis_bundle.fallacy.to_dict(),
                "perspective": analysis_bundle.perspective.to_dict(),
                "memory": memory_step.to_dict(),
                "graph_memory": graph_step.to_dict() if graph_step is not None else {},
                "hipporag_memory": hipporag_step.to_dict() if hipporag_step is not None else {},
                "discord": discord_result.to_dict(),
                "transcript_compression": analysis_bundle.compression,
            },
            duration=duration,
        )

    def _rate_limit_failure(self) -> PipelineRunResult | None:
        if self._check_rate_limit("pipeline"):
            return None
        ctx = current_tenant()
        tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"
        self.logger.warning("Pipeline rate limit exceeded for tenant %s", tenant_key)
        self._record_step_metrics("rate_limit", "error", None)
        return {
            "status": "error",
            "step": "rate_limit",
            "error": f"Pipeline rate limit exceeded for tenant {tenant_key}",
            "rate_limit_exceeded": True,
            "status_code": 429,
        }

    def _start_drive_upload(
        self,
        download_info: StepResult,
        local_path: str,
    ) -> tuple[asyncio.Task[StepResult] | None, StepResult | None]:
        if not self.drive:
            self.logger.info("Drive upload skipped (disabled)")
            skip_result = StepResult.skip(
                data={
                    "state": "skipped",
                    "message": "Google Drive disabled",
                    "reason": "disabled",
                },
            )
            self._record_step_skip("drive")
            return None, skip_result

        drive_platform = download_info.data.get("platform", "unknown").lower()
        task = asyncio.create_task(
            self._execute_step("drive", self.drive.run, local_path, drive_platform),
            name="drive",
        )
        return task, None

    async def _await_drive_result(
        self,
        drive_task: asyncio.Task[StepResult] | None,
        existing_info: StepResult | None,
        span,
        pipeline_start: float,
    ) -> PipelineRunResult | _DriveArtifacts:
        if drive_task is None:
            assert existing_info is not None
            return _DriveArtifacts(result=existing_info, outcome="skipped")

        drive_info = await drive_task
        outcome = self._step_outcome(drive_info)
        if not drive_info.success and outcome != "skipped":
            payload = drive_info.to_dict()
            payload["step"] = "drive"
            return self._fail(span, pipeline_start, "drive", payload)

        if outcome == "skipped":
            self.logger.info(
                "Drive upload skipped: %s",
                drive_info.data.get("message", "quota or disabled"),
            )
        else:
            self.logger.info("Drive upload completed successfully")
        return _DriveArtifacts(result=drive_info, outcome=outcome)

    async def _attempt_transcription_fallback(
        self,
        download_info: StepResult,
        transcription: StepResult,
    ) -> StepResult | None:
        error_text = (transcription.error or "").lower()
        degrade_markers = (
            "whisper package is not installed",
            "no module named 'whisper'",
            'no module named "whisper"',
            "failed to load whisper",
        )
        if not any(marker in error_text for marker in degrade_markers):
            return None

        source_url = download_info.data.get("source_url")
        provider_text, provider_source = await self._fetch_provider_transcript(download_info, source_url)

        transcript_text = provider_text
        transcript_source = provider_source
        if not transcript_text:
            metadata = self._load_download_metadata(download_info)
            transcript_text = self._compose_metadata_transcript(download_info, metadata, source_url)
            transcript_source = "metadata"

        if not transcript_text:
            return None

        segments = self._build_segments_from_text(transcript_text)
        data = dict(transcription.data)
        data.update(
            {
                "transcript": transcript_text,
                "segments": segments,
                "cache_hit": False,
                "model": "metadata-fallback",
                "video_id": download_info.data.get("video_id"),
                "transcript_source": transcript_source,
                "fallback_reason": transcription.error,
                "tool": "transcription-fallback",
            },
        )
        return StepResult(success=True, data=data, custom_status="degraded")

    async def _fetch_provider_transcript(
        self,
        download_info: StepResult,
        source_url: str | None,
    ) -> tuple[str | None, str]:
        if not source_url:
            return None, ""

        platform = str(download_info.data.get("platform", "")).lower()
        try:
            if "youtube" in platform or "youtu" in source_url:
                from ingest.providers.youtube import fetch_transcript

                text = await asyncio.to_thread(fetch_transcript, source_url)
                if text:
                    return text.strip(), "provider"
        except Exception as exc:  # pragma: no cover - network variability
            self.logger.debug("Provider transcript fallback failed: %s", exc)
        return None, ""

    def _compose_metadata_transcript(
        self,
        download_info: StepResult,
        metadata: dict[str, Any],
        source_url: str | None,
    ) -> str | None:
        lines: list[str] = []
        title = download_info.data.get("title") or metadata.get("title")
        if title:
            lines.append(f"Title: {title}")

        presenter = (
            download_info.data.get("uploader")
            or download_info.data.get("channel")
            or metadata.get("uploader")
            or metadata.get("channel")
        )
        if presenter:
            lines.append(f"Presenter: {presenter}")

        description = metadata.get("description") or download_info.data.get("description")
        if isinstance(description, str) and description.strip():
            lines.append(description.strip())

        summary = metadata.get("summary")
        if isinstance(summary, str) and summary.strip():
            lines.append(summary.strip())

        if not lines and source_url:
            lines.append(f"Transcript unavailable automatically. Review manually: {source_url}")

        transcript_text = "\n".join(line for line in lines if line)
        return transcript_text.strip() or None

    def _load_download_metadata(self, download_info: StepResult) -> dict[str, Any]:
        local_path = download_info.data.get("local_path")
        if not local_path:
            return {}

        try:
            path = Path(local_path)
            info_path = path.with_suffix("")
            info_path = info_path.with_suffix(".info.json")
        except Exception:
            return {}

        if not info_path.exists():
            return {}

        try:
            with info_path.open("r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.debug("Failed to load metadata from %s: %s", info_path, exc)
            return {}

    def _build_segments_from_text(self, transcript_text: str) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        for idx, line in enumerate(transcript_text.splitlines()):
            stripped = line.strip()
            if not stripped:
                continue
            segments.append(
                {
                    "id": idx,
                    "start": float(idx),
                    "end": float(idx + 1),
                    "text": stripped,
                }
            )
        return segments

    def _schedule_transcript_storage(
        self,
        transcript: str,
        download_info: StepResult,
    ) -> asyncio.Task[StepResult] | None:
        disable_transcript = bool(get_config().get_setting("disable_transcript_memory", False))
        if disable_transcript:
            self._record_step_skip("transcript_memory")
            return None

        return asyncio.create_task(
            self._execute_step(
                "transcript_memory",
                self.memory.run,
                transcript,
                {
                    "video_id": download_info.data["video_id"],
                    "title": download_info.data["title"],
                    "platform": download_info.data.get("platform", "unknown"),
                },
                collection="transcripts",
            ),
            name="transcript_storage",
        )

    async def _await_transcript_best_effort(self, task: asyncio.Task[StepResult]) -> None:
        with suppress(Exception):  # pragma: no cover - best effort logging already handled elsewhere
            await asyncio.wait_for(task, timeout=2)

    def _schedule_discord_post(
        self,
        drive_artifacts: _DriveArtifacts,
        download_info: StepResult,
        analysis: StepResult,
        fallacy: StepResult,
        perspective: StepResult,
    ) -> tuple[asyncio.Task[StepResult] | None, StepResult]:
        content_data = {
            **download_info.to_dict(),
            **analysis.to_dict(),
            **fallacy.data,
            **perspective.data,
        }

        if not self.discord:
            self.logger.info("Discord posting skipped - no webhook configured")
            skip = StepResult.skip(data={"state": "skipped", "reason": "no webhook configured"})
            self._record_step_skip("discord")
            return None, skip

        if drive_artifacts.outcome == "skipped":
            drive_links = {
                "status": "skipped",
                "reason": drive_artifacts.result.data.get("reason", "quota"),
                "message": drive_artifacts.result.data.get("message", "Drive upload skipped"),
            }
        else:
            drive_links = drive_artifacts.result.data.get("links", {}) if drive_artifacts.result.success else {}

        return (
            asyncio.create_task(
                self._execute_step("discord", self.discord.run, content_data, drive_links),
                name="discord",
            ),
            StepResult.skip(data={"state": "pending"}),
        )

    async def _await_storage_tasks(
        self,
        analysis_memory_task: asyncio.Task[StepResult],
        transcript_task: asyncio.Task[StepResult] | None,
        graph_task: asyncio.Task[StepResult] | None,
        hipporag_task: asyncio.Task[StepResult] | None,
    ) -> tuple[
        StepResult | Exception,
        StepResult | Exception | None,
        StepResult | Exception | None,
    ]:
        awaitables: list[asyncio.Task[StepResult]] = [analysis_memory_task]
        if transcript_task is not None:
            awaitables.append(transcript_task)
        if graph_task is not None:
            awaitables.append(graph_task)
        if hipporag_task is not None:
            awaitables.append(hipporag_task)

        results = await asyncio.gather(*awaitables, return_exceptions=True)

        idx = 0
        memory_result = results[idx]
        idx += 1

        transcript_result: StepResult | Exception | None = None
        if transcript_task is not None:
            transcript_result = results[idx]
            idx += 1

        graph_result: StepResult | Exception | None = None
        if graph_task is not None:
            graph_result = results[idx]
            idx += 1

        hipporag_result: StepResult | Exception | None = None
        if hipporag_task is not None:
            hipporag_result = results[idx]

        if transcript_result is not None:
            if isinstance(transcript_result, Exception):
                self.logger.warning("Transcript storage task raised exception: %s", transcript_result)
            else:
                transcript_result = cast("StepResult", transcript_result)
                if not transcript_result.success:
                    self.logger.warning("Transcript storage failed: %s", transcript_result.error)

        return memory_result, graph_result, hipporag_result

    def _increment_pipeline_requests(self) -> None:
        try:  # pragma: no cover - metrics optional
            metrics.PIPELINE_REQUESTS.labels(**metrics.label_ctx()).inc()
        except Exception:
            self.logger.debug("metrics emit failed (pipeline start)")

    def _fail(
        self,
        span,
        pipeline_start: float,
        step: str,
        payload: dict[str, Any],
    ) -> PipelineRunResult:
        span.set_attribute("error", True)
        span.set_attribute("error_step", step)
        payload.setdefault("step", step)
        payload.setdefault("status", "error")
        return self._finalize_pipeline(pipeline_start, "error", payload)

    async def _run_download(self, url: str, quality: str) -> StepResult:
        return await self._execute_step("download", self.downloader.run, url, quality=quality)

    async def _run_transcription(self, local_path: str, video_id: str | None) -> StepResult:
        model_name = self._transcriber_model_name()
        return await self._execute_step(
            "transcription",
            self._transcription_step,
            local_path,
            video_id,
            model_name,
        )

    async def _run_analysis(self, transcript: str) -> StepResult:
        return await self._execute_step("analysis", self.analyzer.run, transcript)

    async def _run_fallacy(self, transcript: str) -> StepResult:
        return await self._execute_step("fallacy", self.fallacy_detector.run, transcript)

    async def _run_perspective(self, transcript: str, analysis_data: dict[str, Any]) -> StepResult:
        return await self._execute_step("perspective", self.perspective.run, transcript, str(analysis_data))

    async def _run_analysis_memory(self, summary: str, payload: dict[str, Any]) -> StepResult:
        return await self._execute_step(
            "analysis_memory",
            self.memory.run,
            summary,
            payload,
            collection="analysis",
        )

    def _calculate_spam_score(self, title: str) -> float:
        """Calculate spam score for a title.

        Args:
            title: The title to analyze

        Returns:
            Spam score between 0.0 (not spam) and 1.0 (definitely spam)
        """
        if not title:
            return 0.0

        title_lower = title.lower()

        # Spam indicators
        spam_indicators = [
            "buy now",
            "click here",
            "limited time",
            "discount",
            "sale",
            "free",
            "win",
            "prize",
            "cash",
            "money",
            "earn",
            "profit",
            "guaranteed",
            "no risk",
            "act now",
            "hurry",
            "expires",
            "subscribe",
            "follow",
            "like",
            "share",
            "comment",
            "link in bio",
            "swipe up",
            "tap here",
            "download now",
        ]

        # Calculate spam score based on indicators
        spam_count = sum(1 for indicator in spam_indicators if indicator in title_lower)

        # Additional heuristics
        score = 0.0

        # Multiple exclamation marks
        if title.count("!") > 2:
            score += 0.2

        # All caps
        if len(title) > 10 and title.isupper():
            score += 0.3

        # Excessive punctuation
        if title.count("!") + title.count("?") > 3:
            score += 0.2

        # Repeated words
        words = title_lower.split()
        if len(words) > 3:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            max_repetition = max(word_counts.values())
            if max_repetition > 2:
                score += 0.2

        # Spam indicator matches
        score += min(0.5, spam_count * 0.1)

        return min(1.0, score)

    def _calculate_wer(self, transcript: str) -> float:
        """Calculate Word Error Rate for a transcript.

        Args:
            transcript: The transcript to analyze

        Returns:
            WER score between 0.0 (perfect) and 1.0 (all errors)
        """
        if not transcript:
            return 1.0

        # Simple WER estimation based on transcript characteristics
        words = transcript.split()
        if not words:
            return 1.0

        # Estimate errors based on common transcription issues
        error_indicators = 0

        # Check for common transcription errors
        for word in words:
            # Repeated characters (e.g., "helllooo")
            if len(word) > 3 and any(word.count(char) > 2 for char in set(word)):
                error_indicators += 1

            # Very short words that might be fragments
            if len(word) == 1 and word.isalpha():
                error_indicators += 1

            # Numbers that might be misheard
            if word.isdigit() and len(word) > 2:
                error_indicators += 1

        # Calculate WER as ratio of potential errors to total words
        wer = min(1.0, error_indicators / len(words))

        return wer

    def _calculate_repetition_ratio(self, transcript: str) -> float:
        """Calculate repetition ratio for a transcript.

        Args:
            transcript: The transcript to analyze

        Returns:
            Repetition ratio between 0.0 (no repetition) and 1.0 (all repetition)
        """
        if not transcript:
            return 0.0

        words = transcript.lower().split()
        if len(words) < 3:
            return 0.0

        # Count word repetitions
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Calculate repetition ratio
        total_words = len(words)
        len(word_counts)
        repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)

        if total_words == 0:
            return 0.0

        repetition_ratio = repeated_words / total_words
        return min(1.0, repetition_ratio)

    def _calculate_vocabulary_diversity(self, transcript: str) -> float:
        """Calculate vocabulary diversity for a transcript.

        Args:
            transcript: The transcript to analyze

        Returns:
            Vocabulary diversity ratio between 0.0 (no diversity) and 1.0 (high diversity)
        """
        if not transcript:
            return 0.0

        words = transcript.lower().split()
        if not words:
            return 0.0

        # Calculate unique word ratio
        unique_words = len(set(words))
        total_words = len(words)

        if total_words == 0:
            return 0.0

        # Basic diversity ratio
        diversity_ratio = unique_words / total_words

        # Adjust for vocabulary richness (longer words indicate more sophisticated vocabulary)
        avg_word_length = sum(len(word) for word in words) / total_words
        length_bonus = min(0.2, (avg_word_length - 4) * 0.05)  # Bonus for longer words

        # Adjust for word complexity (words with more syllables)
        complex_words = sum(1 for word in words if len(word) > 6)
        complexity_bonus = min(0.1, complex_words / total_words)

        final_diversity = min(1.0, diversity_ratio + length_bonus + complexity_bonus)
        return final_diversity
