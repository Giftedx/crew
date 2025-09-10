import asyncio
import logging
import pathlib
import time
from functools import partial
from typing import TYPE_CHECKING, Any, Optional, TypedDict, cast

from core.privacy import privacy_filter
from obs import metrics
from security.rate_limit import TokenBucket
from ultimate_discord_intelligence_bot.services.request_budget import track_request_budget
from ultimate_discord_intelligence_bot.tenancy import current_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

_tracing_mod: Any
try:
    from obs import tracing as _obs_tracing

    _TRACING_AVAILABLE = True
    _tracing_mod = _obs_tracing
except ImportError:
    _TRACING_AVAILABLE = False

    # Create a no-op tracing context for when obs is not available
    class _NoOpSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, key, value):
            pass

    class _NoOpTracing:
        def start_span(self, name):
            return _NoOpSpan()

    _tracing_mod = _NoOpTracing()

from .settings import DISCORD_WEBHOOK
from .step_result import StepResult
from .tools.audio_transcription_tool import AudioTranscriptionTool
from .tools.discord_post_tool import DiscordPostTool

try:
    from .tools.drive_upload_tool import DriveUploadTool
except Exception:
    # Use bypass version if main tool fails
    from .tools.drive_upload_tool_bypass import DriveUploadTool  # type: ignore[assignment]
from .tools.logical_fallacy_tool import LogicalFallacyTool
from .tools.memory_storage_tool import MemoryStorageTool
from .tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from .tools.text_analysis_tool import TextAnalysisTool

if TYPE_CHECKING:  # pragma: no cover - for typing only
    from .tools.multi_platform_download_tool import MultiPlatformDownloadTool

logger = logging.getLogger(__name__)


class PipelineRunResult(TypedDict, total=False):
    status: str
    download: dict[str, Any]
    drive: dict[str, Any]
    transcription: dict[str, Any]
    analysis: dict[str, Any]
    fallacy: dict[str, Any]
    perspective: dict[str, Any]
    memory: dict[str, Any]
    discord: dict[str, Any]
    step: str
    error: str
    rate_limit_exceeded: bool
    status_code: int


class ContentPipeline:
    """End-to-end pipeline for downloading, processing and posting content."""

    def __init__(  # noqa: PLR0913 - many optional dependency injection points improve testability
        self,
        webhook_url: str | None = None,
        downloader: Optional["MultiPlatformDownloadTool"] = None,
        transcriber: AudioTranscriptionTool | None = None,
        analyzer: TextAnalysisTool | None = None,
        drive: DriveUploadTool | None = None,
        discord: DiscordPostTool | None = None,
        fallacy_detector: LogicalFallacyTool | None = None,
        perspective: PerspectiveSynthesizerTool | None = None,
        memory: MemoryStorageTool | None = None,
        pipeline_rate_limit: float = 2.0,  # pipelines per minute per tenant
        tool_rate_limit: float = 10.0,  # tool operations per minute per tenant
    ):
        if downloader is None:
            from .tools.multi_platform_download_tool import (  # noqa: PLC0415 - lazy import avoids heavy optional deps at module import
                MultiPlatformDownloadTool,
            )

            self.downloader = MultiPlatformDownloadTool()
        else:
            self.downloader = downloader
        self.transcriber = transcriber or AudioTranscriptionTool()
        if analyzer is not None:
            self.analyzer = analyzer
        else:
            try:
                self.analyzer = TextAnalysisTool()
            except RuntimeError as e:  # NLTK unavailable fallback
                logger.warning("TextAnalysisTool unavailable (%s) - using degraded stub analyzer", e)

                class _DegradedAnalyzer:
                    name = "DegradedTextAnalysisTool"

                    def run(self, text: str):  # mimic interface subset
                        return StepResult.ok(
                            skipped=True,
                            reason="text_analysis_unavailable",
                            status="success",
                            data={"tokens": len(text.split()), "note": "NLTK missing"},
                        )

                    def _run(self, text: str):  # for consistency if called directly
                        return self.run(text)

                self.analyzer = cast(TextAnalysisTool, _DegradedAnalyzer())
        # Initialize Drive tool with error handling
        try:
            drive_tool = drive or DriveUploadTool()
            # Check if the drive tool is actually functional (has a service)
            if getattr(drive_tool, "service", None) is None:
                logger.warning("Drive upload disabled via configuration")
                self.drive = None
            else:
                self.drive = drive_tool
        except Exception as e:
            logger.warning("Drive upload unavailable: %s", e)
            self.drive = None
        # Initialize Discord tool only if webhook URL is provided
        discord_webhook = webhook_url or DISCORD_WEBHOOK
        if discord_webhook and discord_webhook.strip():
            self.discord: DiscordPostTool | None = discord or DiscordPostTool(discord_webhook)
        else:
            logger.warning("Discord webhook not configured - Discord posting disabled")
            self.discord = None
        self.fallacy_detector = fallacy_detector or LogicalFallacyTool()
        self.perspective = perspective or PerspectiveSynthesizerTool()
        self.memory = memory or MemoryStorageTool()

        # Rate limiting for tenant-isolated operations
        self.pipeline_bucket = TokenBucket(
            rate=pipeline_rate_limit / 60.0,  # convert per-minute to per-second
            capacity=max(int(pipeline_rate_limit), 1),
        )
        self.tool_bucket = TokenBucket(
            rate=tool_rate_limit / 60.0,  # convert per-minute to per-second
            capacity=max(int(tool_rate_limit), 3),
        )

    def _apply_pii_filtering(self, text: str, step: str) -> str:
        """Apply PII filtering to content before processing or storage.

        Returns filtered text with PII redacted according to current policy.
        """
        try:
            ctx = current_tenant()
            context = {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id} if ctx else {}
            filtered_text, report = privacy_filter.filter_text(text, context)

            if report.found:
                logger.info("PII detected in %s: %s patterns found", step, sum(report.redacted_by_type.values()))

            return filtered_text
        except Exception as exc:
            # Don't fail pipeline on PII filtering errors - log and continue
            logger.warning("PII filtering failed in %s: %s", step, exc)
            return text

    def _check_rate_limit(self, operation_type: str) -> bool:
        """Check rate limits for tenant-scoped operations.

        Returns True if operation is allowed, False if rate limit exceeded.
        """
        ctx = current_tenant()
        tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"

        if operation_type == "pipeline":
            bucket = self.pipeline_bucket
        elif operation_type == "tool":
            bucket = self.tool_bucket
        else:
            # Unknown operation type - don't rate limit
            return True

        return bucket.allow(tenant_key)

    async def _run_with_retries(
        self,
        func: Any,
        *args: Any,
        step: str,
        attempts: int = 3,
        delay: float = 2.0,
        check_tool_rate_limit: bool = True,
        **kwargs: Any,
    ) -> StepResult:
        """Run a blocking function in the default executor with retries.

        Any dictionary responses are normalised into :class:`StepResult`.  Exceptions
        raised by ``func`` are caught and converted into failed results so that the
        pipeline can surface the failing step instead of aborting execution.
        """
        # Check tool rate limit for expensive operations
        if check_tool_rate_limit and not self._check_rate_limit("tool"):
            ctx = current_tenant()
            tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"
            logger.warning("Tool rate limit exceeded for tenant %s on step %s", tenant_key, step)
            return StepResult.fail(f"Tool rate limit exceeded for tenant {tenant_key}", rate_limit_exceeded=True)
        loop = asyncio.get_running_loop()
        result = StepResult.fail("unknown")
        for attempt in range(attempts):
            try:
                call = partial(func, *args, **kwargs)
                raw = await loop.run_in_executor(None, call)
                result = StepResult.from_dict(raw)
            except Exception as exc:  # pragma: no cover - rare
                logger.exception("%s attempt %s raised: %s", step, attempt + 1, exc)
                result = StepResult.fail(str(exc))
            if result.success:
                return result
            logger.warning("%s attempt %s failed: %s", step, attempt + 1, result.error)
            await asyncio.sleep(delay)
        return result

    async def process_video(self, url: str, quality: str = "1080p") -> PipelineRunResult:  # noqa: PLR0915, PLR0911, PLR0912 - orchestrates concurrent multi-step pipeline with explicit early exits for clearer error reporting
        """Run the full content pipeline for a single video.

        Parameters
        ----------
        url: str
            The video URL to process. Supported platforms include YouTube,
            Twitch, Kick, Twitter, Instagram, TikTok and Reddit.
        quality: str, optional
            Preferred maximum resolution for the download (e.g. ``720p``).
            Defaults to ``1080p``.

        Returns
        -------
        dict
            ``{"status": "success", ...}`` with step results on success or
            ``{"status": "error", "step": <stage>, ...}`` on failure.
        """

        # Check pipeline rate limit before starting
        if not self._check_rate_limit("pipeline"):
            ctx = current_tenant()
            tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"
            logger.warning("Pipeline rate limit exceeded for tenant %s", tenant_key)
            # Emit metrics for failed rate-limited attempt
            try:  # pragma: no cover - metrics may be no-op
                metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="rate_limit").inc()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("metrics emit failed (rate_limit): %s", exc)
            return {
                "status": "error",
                "step": "rate_limit",
                "error": f"Pipeline rate limit exceeded for tenant {tenant_key}",
                "rate_limit_exceeded": True,
                "status_code": 429,
            }

        pipeline_start_time = time.time()

        # Resolve cumulative budgeting limits (may be None / empty if not configured). We intentionally
        # derive these outside the tracing span so budget resolution failures can't impact tracing.
        ctx = current_tenant()
        total_limit: float | None = None
        per_task_limits: dict[str, float] = {}
        try:
            # Lazy registry discovery – some tools embed a router with a registry.
            reg: TenantRegistry | None = None
            for cand in (getattr(self, "analyzer", None), getattr(self, "perspective", None)):
                router = getattr(cand, "router", None)
                if router is not None:
                    maybe_reg = getattr(router, "tenant_registry", None)
                    if isinstance(maybe_reg, TenantRegistry):
                        reg = maybe_reg
                        break
            if reg is None:
                tenants_dir = pathlib.Path("tenants")
                if tenants_dir.exists():  # pragma: no branch - simple check
                    try:  # pragma: no cover - best effort
                        reg = TenantRegistry(tenants_dir)
                    except Exception:  # pragma: no cover - ignore
                        reg = None
            if ctx and reg:
                try:
                    total_limit = reg.get_request_total_limit(ctx)
                except Exception:  # pragma: no cover
                    total_limit = None
                try:
                    per_task_limits = reg.get_per_task_cost_limits(ctx)
                except Exception:  # pragma: no cover
                    per_task_limits = {}
        except Exception:  # pragma: no cover - budgeting optional
            total_limit = None
            per_task_limits = {}

        with (
            track_request_budget(total_limit=total_limit, per_task_limits=per_task_limits),
            _tracing_mod.start_span("pipeline.process_video") as span,
        ):
            span.set_attribute("url", url)
            span.set_attribute("quality", quality)

            logger.info("Starting concurrent pipeline for %s (quality: %s)", url, quality)
            # Count pipeline request
            try:  # pragma: no cover - metrics optional
                metrics.PIPELINE_REQUESTS.labels(**metrics.label_ctx()).inc()
            except Exception as exc:  # pragma: no cover
                logger.debug("metrics emit failed (pipeline start): %s", exc)
            download_info = await self._run_with_retries(self.downloader.run, url, quality=quality, step="download")
            if not download_info.success:
                logger.error("Download failed: %s", download_info.error)
                try:  # pragma: no cover
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="download").inc()
                except Exception as exc:  # pragma: no cover
                    logger.debug("metrics emit failed (download fail): %s", exc)
                span.set_attribute("error", True)
                span.set_attribute("error_step", "download")
                err = download_info.to_dict()
                err["step"] = "download"
                return err  # type: ignore[return-value]

            local_path = download_info.data["local_path"]
            span.set_attribute("local_path", local_path)

            # Phase 2: Drive upload and transcription can run concurrently
            logger.info("Starting concurrent drive upload and transcription")
            drive_task = None
            transcription_task = asyncio.create_task(
                self._run_with_retries(self.transcriber.run, local_path, step="transcription"), name="transcription"
            )

            if self.drive:
                logger.info("Uploading %s to Drive concurrently", local_path)
                drive_platform = download_info.data.get("platform", "unknown").lower()
                drive_task = asyncio.create_task(
                    self._run_with_retries(self.drive.run, local_path, drive_platform, step="drive"), name="drive"
                )

            # Wait for transcription (critical path)
            transcription = await transcription_task
            if not transcription.success:
                logger.error("Transcription failed: %s", transcription.error)
                try:  # pragma: no cover
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="transcription").inc()
                except Exception as exc:  # pragma: no cover
                    logger.debug("metrics emit failed (transcription fail): %s", exc)
                span.set_attribute("error", True)
                span.set_attribute("error_step", "transcription")
                # Cancel drive upload if still running
                if drive_task and not drive_task.done():
                    drive_task.cancel()
                err = transcription.to_dict()
                err["step"] = "transcription"
                return err  # type: ignore[return-value]

            # Wait for drive upload if it was started
            if drive_task:
                drive_info = await drive_task
                if not drive_info.success:
                    logger.error("Drive upload failed: %s", drive_info.error)
                    try:  # pragma: no cover
                        metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="drive").inc()
                    except Exception as exc:  # pragma: no cover
                        logger.debug("metrics emit failed (drive fail): %s", exc)
                    span.set_attribute("error", True)
                    span.set_attribute("error_step", "drive")
                    err = drive_info.to_dict()
                    err["step"] = "drive"
                    return err  # type: ignore[return-value]
                logger.info("Drive upload completed successfully")
            else:
                logger.info("Drive upload skipped (disabled)")
                drive_info = StepResult.ok(data={"status": "skipped", "message": "Google Drive disabled"})

            # Apply PII filtering to transcript before storage
            raw_transcript = transcription.data.get("transcript", "")
            filtered_transcript = self._apply_pii_filtering(raw_transcript, "transcript")

            # Phase 3: Run analysis first, store transcript concurrently; only run fallacy detection if analysis succeeds
            logger.info("Starting analysis and transcript storage (fallacy deferred until analysis success)")

            # Transcript storage (can run concurrently with analysis)
            transcript_storage_task = asyncio.create_task(
                self._run_with_retries(
                    self.memory.run,
                    filtered_transcript,
                    {
                        "video_id": download_info.data["video_id"],
                        "title": download_info.data["title"],
                        "platform": download_info.data.get("platform", "unknown"),
                    },
                    step="transcript_memory",
                    collection="transcripts",
                ),
                name="transcript_storage",
            )

            analysis = await self._run_with_retries(self.analyzer.run, filtered_transcript, step="analysis")

            # Handle analysis errors (ensure transcript storage given limited time to complete)
            if not analysis.success:
                logger.error("Analysis failed: %s", analysis.error)
                span.set_attribute("error", True)
                span.set_attribute("error_step", "analysis")
                try:
                    if not transcript_storage_task.done():
                        await asyncio.wait_for(transcript_storage_task, timeout=2)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.debug("Transcript storage still pending after analysis failure: %s", exc)
                try:  # pragma: no cover
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="analysis").inc()
                except Exception as exc:  # pragma: no cover
                    logger.debug("metrics emit failed (analysis fail): %s", exc)
                err = analysis.to_dict()
                err["step"] = "analysis"
                return err  # type: ignore[return-value]

            # Run fallacy detection only after successful analysis
            fallacy = await self._run_with_retries(
                self.fallacy_detector.run,
                filtered_transcript,
                step="fallacy",
            )
            if not fallacy.success:
                logger.error("Fallacy detection failed: %s", fallacy.error)
                # Cancel transcript storage (not critical but free resources) if still running
                if not transcript_storage_task.done():
                    transcript_storage_task.cancel()
                try:  # pragma: no cover
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="fallacy").inc()
                except Exception as exc:  # pragma: no cover
                    logger.debug("metrics emit failed (fallacy fail): %s", exc)
                err = fallacy.to_dict()
                err["step"] = "fallacy"
                return err  # type: ignore[return-value]

            # At this point, analysis and fallacy are successful StepResult instances

            # Phase 4: Perspective synthesis (depends on analysis results)
            logger.info("Synthesizing perspectives")
            perspective = await self._run_with_retries(
                self.perspective.run,
                filtered_transcript,
                str(analysis.data),
                step="perspective",
            )
            if not perspective.success:
                logger.error("Perspective synthesis failed: %s", perspective.error)
                transcript_storage_task.cancel()
                try:  # pragma: no cover
                    metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="perspective").inc()
                except Exception as exc:  # pragma: no cover
                    logger.debug("metrics emit failed (perspective fail): %s", exc)
                err = perspective.to_dict()
                err["step"] = "perspective"
                return err  # type: ignore[return-value]

            # Phase 5: Final storage and Discord posting can run concurrently
            logger.info("Starting concurrent memory storage and Discord posting")

            # Prepare content data for Discord
            content_data = {
                **download_info.to_dict(),
                **analysis.to_dict(),
                **fallacy.data,
                **perspective.data,
            }

            # Apply PII filtering to summary before storage
            raw_summary = perspective.data.get("summary", "")
            filtered_summary = self._apply_pii_filtering(raw_summary, "summary")

            memory_payload = {
                "video_id": download_info.data["video_id"],
                "title": download_info.data["title"],
                "platform": download_info.data.get("platform", "unknown"),
                "sentiment": analysis.data.get("sentiment"),
                "keywords": analysis.data.get("keywords"),
                "summary": filtered_summary,
            }

            # Create tasks for final phase
            analysis_memory_task = asyncio.create_task(
                self._run_with_retries(
                    self.memory.run,
                    filtered_summary,
                    memory_payload,
                    step="analysis_memory",
                    collection="analysis",
                ),
                name="analysis_memory",
            )

            discord_task = None
            if self.discord:
                logger.info("Preparing Discord post concurrently")
                drive_links = drive_info.data.get("links", {}) if drive_info.success else {}
                discord_task = asyncio.create_task(
                    self._run_with_retries(self.discord.run, content_data, drive_links, step="discord"), name="discord"
                )

            # Wait for all storage tasks (transcript + analysis memory)
            storage_results = await asyncio.gather(
                transcript_storage_task, analysis_memory_task, return_exceptions=True
            )

            transcript_memory_result, memory = storage_results

            # Handle transcript storage errors (non-critical, log but continue)
            if isinstance(transcript_memory_result, Exception):
                logger.warning("Transcript storage task raised exception: %s", transcript_memory_result)
            else:
                transcript_memory_result = cast(StepResult, transcript_memory_result)
                if not transcript_memory_result.success:
                    logger.warning("Transcript storage failed: %s", transcript_memory_result.error)

            # Handle analysis memory storage errors (critical)
            if isinstance(memory, Exception):
                logger.error("Analysis memory storage task raised exception: %s", memory)
                span.set_attribute("error", True)
                span.set_attribute("error_step", "memory")
                if discord_task:
                    discord_task.cancel()
                return {"status": "error", "step": "memory", "error": str(memory)}
            else:
                memory = cast(StepResult, memory)
                if not memory.success:
                    logger.error("Analysis memory storage failed: %s", memory.error)
                    if discord_task:
                        discord_task.cancel()
                    err = memory.to_dict()
                    err["step"] = "memory"
                    return err  # type: ignore[return-value]

            # Wait for Discord posting if it was started
            if discord_task:
                discord_result = await discord_task
                if not discord_result.success:
                    logger.error("Discord post failed: %s", discord_result.error)
                    try:  # pragma: no cover
                        metrics.PIPELINE_STEPS_FAILED.labels(**metrics.label_ctx(), step="discord").inc()
                    except Exception as exc:  # pragma: no cover
                        logger.debug("metrics emit failed (discord fail): %s", exc)
                    err = discord_result.to_dict()
                    err["step"] = "discord"
                    return err  # type: ignore[return-value]
            else:
                logger.info("Discord posting skipped - no webhook configured")
                discord_result = StepResult.ok(data={"status": "skipped", "reason": "no webhook configured"})

        pipeline_duration = time.time() - pipeline_start_time
        logger.info("✅ Concurrent pipeline completed in %.2f seconds", pipeline_duration)
        span.set_attribute("pipeline_duration_seconds", pipeline_duration)
        try:  # pragma: no cover
            metrics.PIPELINE_DURATION.labels(**metrics.label_ctx(), status="success").observe(pipeline_duration)
        except Exception as exc:  # pragma: no cover
            logger.debug("metrics emit failed (duration): %s", exc)

        return {
            "status": "success",
            "download": download_info.to_dict(),
            "drive": drive_info.to_dict(),
            "transcription": transcription.to_dict(),
            "analysis": analysis.to_dict(),
            "fallacy": fallacy.to_dict(),
            "perspective": perspective.to_dict(),
            "memory": memory.to_dict(),
            "discord": discord_result.to_dict(),
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run content pipeline")
    parser.add_argument("url", help="Video URL")
    parser.add_argument(
        "--quality",
        default="1080p",
        help="Maximum download resolution (e.g. 720p)",
    )
    args = parser.parse_args()

    pipeline = ContentPipeline()
    asyncio.run(pipeline.process_video(args.url, quality=args.quality))
# ruff: noqa: E402
