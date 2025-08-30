import asyncio
import logging
from functools import partial
from typing import TYPE_CHECKING, Any, Optional, TypedDict

from .settings import DISCORD_WEBHOOK
from .step_result import StepResult
from .tools.audio_transcription_tool import AudioTranscriptionTool
from .tools.discord_post_tool import DiscordPostTool
from .tools.drive_upload_tool import DriveUploadTool
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
    ):
        if downloader is None:
            from .tools.multi_platform_download_tool import (  # noqa: PLC0415 - lazy import avoids heavy optional deps at module import
                MultiPlatformDownloadTool,
            )

            self.downloader = MultiPlatformDownloadTool()
        else:
            self.downloader = downloader
        self.transcriber = transcriber or AudioTranscriptionTool()
        self.analyzer = analyzer or TextAnalysisTool()
        self.drive = drive or DriveUploadTool()
        self.discord = discord or DiscordPostTool(webhook_url or DISCORD_WEBHOOK)
        self.fallacy_detector = fallacy_detector or LogicalFallacyTool()
        self.perspective = perspective or PerspectiveSynthesizerTool()
        self.memory = memory or MemoryStorageTool()

    async def _run_with_retries(
        self,
        func: Any,
        *args: Any,
        step: str,
        attempts: int = 3,
        delay: float = 2.0,
        **kwargs: Any,
    ) -> StepResult:
        """Run a blocking function in the default executor with retries.

        Any dictionary responses are normalised into :class:`StepResult`.  Exceptions
        raised by ``func`` are caught and converted into failed results so that the
        pipeline can surface the failing step instead of aborting execution.
        """
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

    async def process_video(self, url: str, quality: str = "1080p") -> PipelineRunResult:  # noqa: PLR0915, PLR0911 - orchestrates sequential multi-step pipeline with explicit early exits for clearer error reporting
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

        logger.info("Starting download for %s", url)
        download_info = await self._run_with_retries(
            self.downloader.run, url, quality=quality, step="download"
        )
        if not download_info.success:
            logger.error("Download failed: %s", download_info.error)
            err = download_info.to_dict()
            err["step"] = "download"
            return err  # type: ignore[return-value]

        local_path = download_info.data["local_path"]
        logger.info("Uploading %s to Drive", local_path)
        drive_platform = download_info.data.get("platform", "unknown").lower()
        drive_info = await self._run_with_retries(
            self.drive.run, local_path, drive_platform, step="drive"
        )
        if not drive_info.success:
            logger.error("Drive upload failed: %s", drive_info.error)
            err = drive_info.to_dict()
            err["step"] = "drive"
            return err  # type: ignore[return-value]

        logger.info("Transcribing %s", local_path)
        transcription = await self._run_with_retries(
            self.transcriber.run, local_path, step="transcription"
        )
        if not transcription.success:
            logger.error("Transcription failed: %s", transcription.error)
            err = transcription.to_dict()
            err["step"] = "transcription"
            return err  # type: ignore[return-value]

        # persist raw transcript in its own collection
        await self._run_with_retries(
            self.memory.run,
            transcription.data.get("transcript", ""),
            {
                "video_id": download_info.data["video_id"],
                "title": download_info.data["title"],
                "platform": download_info.data.get("platform", "unknown"),
            },
            step="memory",
            collection="transcripts",
        )

        logger.info("Analyzing transcript")
        analysis = await self._run_with_retries(
            self.analyzer.run, transcription.data["transcript"], step="analysis"
        )
        if not analysis.success:
            logger.error("Analysis failed: %s", analysis.error)
            err = analysis.to_dict()
            err["step"] = "analysis"
            return err  # type: ignore[return-value]

        logger.info("Detecting logical fallacies")
        fallacy = await self._run_with_retries(
            self.fallacy_detector.run,
            transcription.data["transcript"],
            step="fallacy",
        )
        if not fallacy.success:
            logger.error("Fallacy detection failed: %s", fallacy.error)
            err = fallacy.to_dict()
            err["step"] = "fallacy"
            return err  # type: ignore[return-value]

        logger.info("Synthesizing perspectives")
        perspective = await self._run_with_retries(
            self.perspective.run,
            transcription.data["transcript"],
            str(analysis.data),
            step="perspective",
        )
        if not perspective.success:
            logger.error("Perspective synthesis failed: %s", perspective.error)
            err = perspective.to_dict()
            err["step"] = "perspective"
            return err  # type: ignore[return-value]

        logger.info("Storing results in vector memory")
        memory_payload = {
            "video_id": download_info.data["video_id"],
            "title": download_info.data["title"],
            "platform": download_info.data.get("platform", "unknown"),
            "sentiment": analysis.data.get("sentiment"),
            "keywords": analysis.data.get("keywords"),
            "summary": perspective.data.get("summary"),
        }
        memory = await self._run_with_retries(
            self.memory.run,
            perspective.data.get("summary", ""),
            memory_payload,
            step="memory",
            collection="analysis",
        )
        if not memory.success:
            logger.error("Memory storage failed: %s", memory.error)
            err = memory.to_dict()
            err["step"] = "memory"
            return err  # type: ignore[return-value]

        content_data = {
            **download_info.to_dict(),
            **analysis.to_dict(),
            **fallacy.data,
            **perspective.data,
        }

        logger.info("Posting to Discord")
        discord_result = await self._run_with_retries(
            self.discord.run, content_data, drive_info.data.get("links", {}), step="discord"
        )
        if not discord_result.success:
            logger.error("Discord post failed: %s", discord_result.error)
            err = discord_result.to_dict()
            err["step"] = "discord"
            return err  # type: ignore[return-value]

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
