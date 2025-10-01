"""High-level orchestration for the content pipeline."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from core.secure_config import get_config
from obs import metrics
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import current_tenant

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ultimate_discord_intelligence_bot.services.request_budget import RequestCostTracker

from .base import PipelineBase
from .mixins import PipelineExecutionMixin
from .tracing import tracing_module
from .types import PipelineRunResult


@dataclass
class _DriveArtifacts:
    result: StepResult
    outcome: str


@dataclass
class _PipelineContext:
    span: Any
    start_time: float
    tracker: RequestCostTracker | None


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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_video(self, url: str, quality: str = "1080p") -> PipelineRunResult:
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
            yield _PipelineContext(span=span, start_time=start_time, tracker=tracker)

    async def _run_pipeline(self, ctx: _PipelineContext, url: str, quality: str) -> PipelineRunResult:
        download_info, failure = await self._download_phase(ctx, url, quality)
        if failure is not None:
            return failure
        assert download_info is not None  # for type checkers

        transcription_bundle, failure = await self._transcription_phase(ctx, download_info)
        if failure is not None:
            return failure
        assert transcription_bundle is not None

        analysis_bundle, failure = await self._analysis_phase(ctx, download_info, transcription_bundle)
        if failure is not None:
            return failure
        assert analysis_bundle is not None

        return await self._finalize_phase(ctx, download_info, transcription_bundle, analysis_bundle)

    async def _download_phase(
        self,
        ctx: _PipelineContext,
        url: str,
        quality: str,
    ) -> tuple[StepResult | None, PipelineRunResult | None]:
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
        return download_info, None

    async def _transcription_phase(
        self,
        ctx: _PipelineContext,
        download_info: StepResult,
    ) -> tuple[_TranscriptionArtifacts | None, PipelineRunResult | None]:
        local_path = download_info.data["local_path"]
        video_id = download_info.data.get("video_id")
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
                return None, self._fail(ctx.span, ctx.start_time, "transcription", transcription.to_dict())

        drive_artifacts = await self._await_drive_result(drive_task, drive_info, ctx.span, ctx.start_time)
        if isinstance(drive_artifacts, dict):
            return None, drive_artifacts
        drive_artifacts = cast(_DriveArtifacts, drive_artifacts)

        filtered_transcript = self._apply_pii_filtering(
            transcription.data.get("transcript", ""),
            "transcript",
        )
        # Defer transcript storage scheduling until analysis phase begins so that
        # analysis memory writes occur deterministically before transcript storage
        # in tests expecting specific call ordering.
        transcript_task: asyncio.Task[StepResult] | None = None

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
        # Schedule transcript storage after analysis memory task is created to guarantee ordering
        transcript_task = transcription_bundle.transcript_task
        compression_meta: dict[str, Any] | None = None

        analysis = await self._run_analysis(filtered_transcript)
        if isinstance(analysis, Exception) or not analysis.success:
            # Ensure transcript storage is attempted even if analysis fails
            if transcript_task is None:
                transcript_task = self._schedule_transcript_storage(filtered_transcript, download_info)
            if transcript_task is not None and not transcript_task.done():
                await self._await_transcript_best_effort(transcript_task)
            error_msg = str(analysis) if isinstance(analysis, Exception) else analysis.error or "analysis failed"
            error_payload = {"status": "error", "error": error_msg, "step": "analysis"}
            return None, self._fail(ctx.span, ctx.start_time, "analysis", error_payload)

        compressed_transcript, compression_meta = self._maybe_compress_transcript(filtered_transcript)
        if compression_meta:
            analysis.data.setdefault("transcript_compression", compression_meta)

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
            return None, self._fail(
                ctx.span,
                ctx.start_time,
                "fallacy",
                {"status": "error", "error": fallacy.error, "step": "fallacy"},
            )

        try:
            perspective = await perspective_task
        except Exception as exc:  # pragma: no cover - defensive path
            return None, self._fail(
                ctx.span,
                ctx.start_time,
                "perspective",
                {"status": "error", "error": str(exc), "step": "perspective"},
            )

        if not perspective.success:
            perspective_payload = perspective.to_dict()
            perspective_payload["step"] = "perspective"
            return None, self._fail(ctx.span, ctx.start_time, "perspective", perspective_payload)

        if compression_meta:
            fallacy.data.setdefault("transcript_compression", compression_meta)
            perspective.data.setdefault("transcript_compression", compression_meta)

        summary = self._apply_pii_filtering(perspective.data.get("summary", ""), "summary")
        perspective.data["summary"] = summary

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
        memory_step = cast(StepResult, memory_result)
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
                graph_step = cast(StepResult, graph_result)
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
                hipporag_step = cast(StepResult, hipporag_result)
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
            self.logger.info("Drive upload skipped: %s", drive_info.data.get("message", "quota or disabled"))
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
                from ingest.providers.youtube import fetch_transcript  # noqa: PLC0415

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
        try:
            await asyncio.wait_for(task, timeout=2)
        except Exception:  # pragma: no cover - best effort logging already handled elsewhere
            pass

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
    ) -> tuple[StepResult | Exception, StepResult | Exception | None, StepResult | Exception | None]:
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
                transcript_result = cast(StepResult, transcript_result)
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
