"""Core dependency wiring and retry helpers for the content pipeline."""

from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import random
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast

from core.settings import get_settings

from obs import metrics
from security.rate_limit import TokenBucket
from ultimate_discord_intelligence_bot.tenancy import current_tenant, with_tenant
from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry

from ..cache import TranscriptCache
from ..settings import DISCORD_WEBHOOK
from ..step_result import StepResult
from ..tools.audio_transcription_tool import AudioTranscriptionTool
from ..tools.discord_post_tool import DiscordPostTool
from ..tools.graph_memory_tool import GraphMemoryTool
from ..tools.hipporag_continual_memory_tool import HippoRagContinualMemoryTool


try:  # pragma: no cover - optional dependency fallback
    from ..tools.drive_upload_tool import DriveUploadTool
except Exception:  # pragma: no cover - degrade gracefully
    from ..tools.drive_upload_tool_bypass import (
        DriveUploadTool,  # type: ignore[assignment]
    )

from ..services.prompt_engine import PromptEngine
from ..tools.logical_fallacy_tool import LogicalFallacyTool
from ..tools.memory_storage_tool import MemoryStorageTool
from ..tools.perspective_synthesizer_tool import PerspectiveSynthesizerTool
from ..tools.text_analysis_tool import TextAnalysisTool
from .log_pattern_middleware import LogPatternMiddleware
from .middleware import PipelineStepMiddleware, TracingStepMiddleware
from .tracing import TRACING_AVAILABLE


if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Iterable

    from ..tools.multi_platform_download_tool import MultiPlatformDownloadTool


class PipelineBase:
    """Provides dependency wiring, rate limiting, and retry helpers."""

    downloader: MultiPlatformDownloadTool
    transcriber: AudioTranscriptionTool
    analyzer: TextAnalysisTool
    drive: DriveUploadTool | None
    discord: DiscordPostTool | None
    fallacy_detector: LogicalFallacyTool
    perspective: PerspectiveSynthesizerTool
    memory: MemoryStorageTool
    graph_memory: GraphMemoryTool | None
    hipporag_memory: HippoRagContinualMemoryTool | None
    transcript_cache: TranscriptCache

    def __init__(
        self,
        webhook_url: str | None = None,
        downloader: MultiPlatformDownloadTool | None = None,
        transcriber: AudioTranscriptionTool | None = None,
        analyzer: TextAnalysisTool | None = None,
        drive: DriveUploadTool | None = None,
        discord: DiscordPostTool | None = None,
        fallacy_detector: LogicalFallacyTool | None = None,
        perspective: PerspectiveSynthesizerTool | None = None,
        memory: MemoryStorageTool | None = None,
        graph_memory: GraphMemoryTool | None = None,
        hipporag_memory: HippoRagContinualMemoryTool | None = None,
        transcript_cache: TranscriptCache | None = None,
        pipeline_rate_limit: float = 120.0,
        tool_rate_limit: float = 120.0,
        step_middlewares: Iterable[PipelineStepMiddleware] | None = None,
    ) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self._orchestrator = self.__class__.__name__
        self._pipeline_pkg = import_module("ultimate_discord_intelligence_bot.pipeline")
        self._step_middlewares: list[PipelineStepMiddleware] = list(step_middlewares or [])
        self._step_observability: dict[str, dict[str, Any]] = {}
        if TRACING_AVAILABLE and not any(isinstance(m, TracingStepMiddleware) for m in self._step_middlewares):
            self._step_middlewares.append(TracingStepMiddleware())
        if not any(isinstance(m, LogPatternMiddleware) for m in self._step_middlewares):
            self._step_middlewares.append(LogPatternMiddleware())

        if downloader is None:
            from ..tools.multi_platform_download_tool import (
                MultiPlatformDownloadTool,
            )

            self.downloader = MultiPlatformDownloadTool()
        else:
            self.downloader = downloader

        self.transcriber = transcriber or AudioTranscriptionTool()

        if analyzer is None:
            try:
                self.analyzer = TextAnalysisTool()
            except RuntimeError as exc:  # pragma: no cover - degraded dependency path
                self.logger.warning(
                    "TextAnalysisTool unavailable (%s) - using degraded stub analyzer",
                    exc,
                )

                class _DegradedAnalyzer:
                    name = "DegradedTextAnalysisTool"

                    def run(self, text: str) -> StepResult:
                        return StepResult.skip(
                            reason="text_analysis_unavailable",
                            details={
                                "tokens": len(text.split()),
                                "note": "NLTK missing",
                            },
                        )

                    def _run(self, text: str) -> StepResult:
                        return self.run(text)

                self.analyzer = cast("TextAnalysisTool", _DegradedAnalyzer())
        else:
            self.analyzer = analyzer

        try:
            drive_tool = drive or DriveUploadTool()
            if getattr(drive_tool, "service", None) is None:
                self.logger.warning("Drive upload disabled via configuration")
                self.drive = None
            else:
                self.drive = drive_tool
        except Exception as exc:  # pragma: no cover - optional dependency path
            self.logger.warning("Drive upload unavailable: %s", exc)
            self.drive = None

        discord_webhook = webhook_url or DISCORD_WEBHOOK
        # If a Discord tool is explicitly provided, always use it (even without webhook)
        if discord is not None:
            self.discord = discord
        elif discord_webhook and discord_webhook.strip():
            self.discord = DiscordPostTool(discord_webhook)
        else:
            if discord_webhook:
                self.logger.warning("Discord webhook provided but empty - Discord posting disabled")
            else:
                self.logger.warning("Discord webhook not configured - Discord posting disabled")
            self.discord = None

        self.fallacy_detector = fallacy_detector or LogicalFallacyTool()
        self.perspective = perspective or PerspectiveSynthesizerTool()
        self.memory = memory or MemoryStorageTool()
        self.prompt_engine = PromptEngine()

        settings = get_settings()
        truthy = {"1", "true", "yes", "on"}
        env_graph = os.getenv("ENABLE_GRAPH_MEMORY")
        graph_enabled = bool(getattr(settings, "enable_graph_memory", False))
        if env_graph is not None:
            graph_enabled = env_graph.lower() in truthy

        if graph_memory is not None:
            self.graph_memory = graph_memory
            graph_enabled = graph_enabled or graph_memory is not None
        elif graph_enabled:
            try:
                self.graph_memory = GraphMemoryTool()
            except Exception as exc:  # pragma: no cover - optional dependency path
                self.logger.warning("Graph memory unavailable: %s", exc)
                self.graph_memory = None
                graph_enabled = False
        else:
            self.graph_memory = None

        self._graph_memory_enabled = graph_enabled and self.graph_memory is not None

        # HippoRAG continual memory setup (accept canonical and legacy flags)
        env_hipporag = os.getenv("ENABLE_HIPPORAG_MEMORY")
        if env_hipporag is None:
            env_hipporag = os.getenv("ENABLE_HIPPORAG_CONTINUAL_MEMORY")
        hipporag_enabled = bool(
            getattr(settings, "enable_hipporag_memory", False)
            or getattr(settings, "enable_hipporag_continual_memory", False)
        )
        if env_hipporag is not None:
            hipporag_enabled = env_hipporag.lower() in truthy

        if hipporag_memory is not None:
            self.hipporag_memory = hipporag_memory
            hipporag_enabled = hipporag_enabled or hipporag_memory is not None
        elif hipporag_enabled:
            try:
                self.hipporag_memory = HippoRagContinualMemoryTool()
            except Exception as exc:  # pragma: no cover - optional dependency path
                self.logger.warning("HippoRAG continual memory unavailable: %s", exc)
                self.hipporag_memory = None
                hipporag_enabled = False
        else:
            self.hipporag_memory = None

        self._hipporag_memory_enabled = hipporag_enabled and self.hipporag_memory is not None

        env_transcript_compression = os.getenv("ENABLE_TRANSCRIPT_COMPRESSION")
        transcript_compression_enabled = bool(getattr(settings, "enable_transcript_compression", False))
        if env_transcript_compression is not None:
            transcript_compression_enabled = env_transcript_compression.lower() in truthy

        self._transcript_compression_enabled = transcript_compression_enabled
        try:
            min_tokens_cfg = getattr(settings, "transcript_compression_min_tokens", 0)
            self._transcript_compression_min_tokens = max(0, int(min_tokens_cfg or 0))
        except Exception:
            self._transcript_compression_min_tokens = 0

        try:
            ratio_cfg = getattr(settings, "transcript_compression_target_ratio", 0.0)
            self._transcript_compression_target_ratio = float(ratio_cfg or 0.0)
        except Exception:
            self._transcript_compression_target_ratio = 0.0

        max_tokens_cfg = getattr(settings, "transcript_compression_max_tokens", None)
        if isinstance(max_tokens_cfg, str) and not max_tokens_cfg.strip():
            max_tokens_cfg = None
        try:
            if max_tokens_cfg in (None, "0", 0):
                self._transcript_compression_max_tokens = None
            else:
                self._transcript_compression_max_tokens = int(max_tokens_cfg)
        except Exception:
            self._transcript_compression_max_tokens = None

        # Disable transcript cache by default to avoid nondeterministic test interference
        # and ensure transcriber runs are executed each time unless explicitly enabled.
        try:
            enable_cache_env = os.getenv("ENABLE_TRANSCRIPT_CACHE", "0").lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        except Exception:
            enable_cache_env = False
        self.transcript_cache = transcript_cache or TranscriptCache(enabled=enable_cache_env)

        self.pipeline_bucket = TokenBucket(
            rate=pipeline_rate_limit / 60.0,
            capacity=max(int(pipeline_rate_limit), 1),
        )
        # Backwards-compatibility alias for tests referencing `pipeline_limiter`
        self.pipeline_limiter = self.pipeline_bucket  # type: ignore[assign-attr]
        self.tool_bucket = TokenBucket(
            rate=tool_rate_limit / 60.0,
            capacity=max(int(tool_rate_limit), 3),
        )

    @property
    def step_middlewares(self) -> tuple[PipelineStepMiddleware, ...]:
        return tuple(self._step_middlewares)

    def add_step_middleware(self, middleware: PipelineStepMiddleware) -> None:
        self._step_middlewares.append(middleware)

    # ---------------------------------------------------------------------
    # Guardrails and helper utilities
    # ---------------------------------------------------------------------

    def _apply_pii_filtering(self, text: str, step: str) -> str:
        try:
            privacy = self._pipeline_pkg.privacy_filter
            ctx = current_tenant()
            context = {"tenant": ctx.tenant_id, "workspace": ctx.workspace_id} if ctx else {}
            filtered_text, report = privacy.filter_text(text, context)
            if report.found:
                self.logger.info(
                    "PII detected in %s: %s patterns found",
                    step,
                    sum(report.redacted_by_type.values()),
                )
            return filtered_text
        except Exception as exc:  # pragma: no cover - resilience path
            self.logger.warning("PII filtering failed in %s: %s", step, exc)
            return text

    def _check_rate_limit(self, operation_type: str) -> bool:
        ctx = current_tenant()
        tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"
        bucket = self.pipeline_bucket if operation_type == "pipeline" else self.tool_bucket
        if operation_type not in {"pipeline", "tool"}:
            return True
        return bucket.allow(tenant_key)

    def _maybe_compress_transcript(self, transcript: str) -> tuple[str, dict[str, Any] | None]:
        if not transcript:
            return transcript, None

        if not getattr(self, "_transcript_compression_enabled", False):
            return transcript, None

        engine = getattr(self, "prompt_engine", None)
        if engine is None:
            return transcript, None

        try:
            original_tokens = engine.count_tokens(transcript)
        except Exception:
            original_tokens = len(transcript.split())

        threshold = max(0, getattr(self, "_transcript_compression_min_tokens", 0))
        meta: dict[str, Any] = {
            "enabled": True,
            "original_tokens": original_tokens,
            "threshold": threshold,
        }

        if threshold > 0 and original_tokens < threshold:
            meta.update(
                {
                    "applied": False,
                    "final_tokens": original_tokens,
                    "reason": "below_threshold",
                }
            )
            return transcript, meta

        ratio = max(
            0.0,
            float(getattr(self, "_transcript_compression_target_ratio", 0.0) or 0.0),
        )
        max_tokens = getattr(self, "_transcript_compression_max_tokens", None)

        try:
            compressed, details = engine.optimise_with_metadata(
                transcript,
                target_token_reduction=ratio,
                max_tokens=max_tokens,
                llmlingua_ratio=ratio if ratio > 0 else None,
                force_enable=True,
            )
        except Exception as exc:  # pragma: no cover - rare failure path
            self.logger.warning("Transcript compression failed: %s", exc)
            meta.update(
                {
                    "applied": False,
                    "final_tokens": original_tokens,
                    "reason": "compression_error",
                }
            )
            return transcript, meta

        final_tokens: int
        raw_final = details.get("final_tokens") if isinstance(details, dict) else None
        if isinstance(raw_final, (int, float)):
            final_tokens = int(raw_final)
        else:
            try:
                final_tokens = engine.count_tokens(compressed)
            except Exception:
                final_tokens = original_tokens

        compressed_changed = compressed != transcript
        applied = bool(details.get("enabled")) and compressed_changed

        meta.update(
            {
                "applied": applied,
                "compressed": compressed_changed,
                "final_tokens": final_tokens,
                "details": details,
            }
        )

        return compressed, meta

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
        import inspect

        if check_tool_rate_limit and not self._check_rate_limit("tool"):
            ctx = current_tenant()
            tenant_key = f"{ctx.tenant_id}:{ctx.workspace_id}" if ctx else "default:default"
            self.logger.warning("Tool rate limit exceeded for tenant %s on step %s", tenant_key, step)
            return StepResult.fail(
                f"Tool rate limit exceeded for tenant {tenant_key}",
                rate_limit_exceeded=True,
            )

        loop = asyncio.get_running_loop()
        tenant_ctx = current_tenant()
        result = StepResult.fail("unknown")

        for attempt in range(attempts):
            try:
                if inspect.iscoroutinefunction(func):

                    async def call_async() -> Any:
                        if tenant_ctx is not None:
                            with with_tenant(tenant_ctx):
                                return await func(*args, **kwargs)
                        return await func(*args, **kwargs)

                    raw = await call_async()
                else:

                    def call_sync() -> Any:
                        if tenant_ctx is not None:
                            with with_tenant(tenant_ctx):
                                return func(*args, **kwargs)
                        return func(*args, **kwargs)

                    raw = await loop.run_in_executor(None, call_sync)
                # If callable produced an awaitable (e.g., MagicMock side_effect), await it under tenant
                if inspect.isawaitable(raw):
                    if tenant_ctx is not None:
                        with with_tenant(tenant_ctx):
                            raw = await raw  # type: ignore[assignment]
                    else:
                        raw = await raw  # type: ignore[assignment]
                result = StepResult.from_dict(raw)
            except Exception as exc:  # pragma: no cover - rare path
                self.logger.exception("%s attempt %s raised: %s", step, attempt + 1, exc)
                result = StepResult.fail(str(exc))

            if result.success:
                return result

            classification = self._classify_failure(result)
            self.logger.warning(
                "%s attempt %s failed (%s): %s",
                step,
                attempt + 1,
                classification,
                result.error,
            )
            if classification == "permanent" or attempt >= attempts - 1:
                break

            backoff = delay * (2**attempt)
            jitter = random.uniform(0.5, 1.5)
            sleep_for = max(0.0, min(backoff * jitter, 60.0))
            try:  # pragma: no cover - optional metric
                metrics.PIPELINE_RETRIES.labels(
                    **metrics.label_ctx(),
                    step=step,
                    reason=classification,
                ).inc()
            except Exception:
                pass
            await asyncio.sleep(sleep_for)

        return result

    @staticmethod
    def _classify_failure(result: StepResult) -> str:
        status_code: int | None
        try:
            status_code = int(result.get("status_code", result.data.get("status_code")))  # type: ignore[arg-type]
        except Exception:
            status_code = None

        if status_code == 429:
            return "rate_limit"
        if status_code is not None and 400 <= status_code < 500:
            return "permanent"

        err = (result.error or "").lower()
        transient_markers = [
            "timeout",
            "temporarily",
            "temporary",
            "connection reset",
            "dns",
            "unavailable",
        ]
        if any(marker in err for marker in transient_markers):
            return "transient"

        return "transient"

    def _transcriber_model_name(self) -> str:
        candidate = getattr(self.transcriber, "model_name", None)
        if isinstance(candidate, str) and candidate:
            return candidate
        fallback = getattr(self.transcriber, "_model_name", None)
        if isinstance(fallback, str) and fallback:
            return fallback
        return "default"

    async def _transcription_step(
        self,
        local_path: str,
        video_id: str | None,
        model_name: str | None,
    ) -> StepResult:
        cache = getattr(self, "transcript_cache", None)
        cached_payload: dict[str, Any] | None = None
        if isinstance(cache, TranscriptCache):
            cached_payload = cache.load(video_id, model_name)
        if cached_payload is not None:
            return StepResult.ok(
                transcript=cached_payload["transcript"],
                segments=cached_payload.get("segments", []),
                cache_hit=True,
                cached_at=cached_payload.get("cached_at"),
                video_id=cached_payload.get("video_id", video_id),
                model=model_name,
            )

        import inspect

        raw_result = self.transcriber.run(local_path)
        # If the transcriber returns an awaitable (async implementation or patched side_effect), await it
        if inspect.isawaitable(raw_result):
            raw_result = await raw_result
        result = StepResult.from_dict(raw_result)
        if isinstance(cache, TranscriptCache) and result.success:
            transcript = result.data.get("transcript")
            if isinstance(transcript, str) and transcript:
                segments = result.data.get("segments")
                serialized_segments: list[dict[str, Any]] | None
                if isinstance(segments, list):
                    serialized_segments = [seg for seg in segments if isinstance(seg, dict)]
                else:
                    serialized_segments = None
                cache.store(video_id, model_name, transcript, serialized_segments)
        result.data.setdefault("cache_hit", False)

        if model_name is not None and "model" not in result.data:
            result.data["model"] = model_name
        if video_id is not None and "video_id" not in result.data:
            result.data["video_id"] = video_id

        return result

    def _resolve_budget_limits(self) -> tuple[float | None, dict[str, float]]:
        ctx = current_tenant()
        total_limit: float | None = None
        per_task_limits: dict[str, float] = {}

        try:
            registry: TenantRegistry | None = None
            for candidate in (
                getattr(self, "analyzer", None),
                getattr(self, "perspective", None),
            ):
                router = getattr(candidate, "router", None)
                if router is not None:
                    maybe_registry = getattr(router, "tenant_registry", None)
                    if isinstance(maybe_registry, TenantRegistry):
                        registry = maybe_registry
                        break

            if registry is None:
                tenants_dir = pathlib.Path("tenants")
                if tenants_dir.exists():  # pragma: no branch - simple check
                    try:  # pragma: no cover - best effort
                        registry = TenantRegistry(tenants_dir)
                    except Exception:
                        registry = None

            if ctx and registry:
                try:
                    total_limit = registry.get_request_total_limit(ctx)
                except Exception:
                    total_limit = None
                try:
                    per_task_limits = registry.get_per_task_cost_limits(ctx)
                except Exception:
                    per_task_limits = {}
        except Exception:  # pragma: no cover - budgeting optional
            total_limit = None
            per_task_limits = {}

        return total_limit, per_task_limits
