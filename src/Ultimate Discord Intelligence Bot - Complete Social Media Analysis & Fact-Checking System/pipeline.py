import asyncio
import logging
from typing import Optional

from .settings import DISCORD_WEBHOOK
from .tools.youtube_download_tool import YouTubeDownloadTool
from .tools.audio_transcription_tool import AudioTranscriptionTool
from .tools.text_analysis_tool import TextAnalysisTool
from .tools.discord_post_tool import DiscordPostTool
from .tools.drive_upload_tool import DriveUploadTool
from .step_result import StepResult

logger = logging.getLogger(__name__)


class ContentPipeline:
    """End-to-end pipeline for downloading, processing and posting content."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        youtube_downloader: Optional[YouTubeDownloadTool] = None,
        transcriber: Optional[AudioTranscriptionTool] = None,
        analyzer: Optional[TextAnalysisTool] = None,
        drive: Optional[DriveUploadTool] = None,
        discord: Optional[DiscordPostTool] = None,
    ):
        self.youtube_downloader = youtube_downloader or YouTubeDownloadTool()
        self.transcriber = transcriber or AudioTranscriptionTool()
        self.analyzer = analyzer or TextAnalysisTool()
        self.drive = drive or DriveUploadTool()
        self.discord = discord or DiscordPostTool(webhook_url or DISCORD_WEBHOOK)

    async def _run_with_retries(
        self, func, *args, step: str, attempts: int = 3, delay: float = 2.0
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
                raw = await loop.run_in_executor(None, func, *args)
                result = StepResult.from_dict(raw)
            except Exception as exc:  # pragma: no cover - rare
                logger.exception("%s attempt %s raised: %s", step, attempt + 1, exc)
                result = StepResult.fail(str(exc))
            if result.success:
                return result
            logger.warning("%s attempt %s failed: %s", step, attempt + 1, result.error)
            await asyncio.sleep(delay)
        return result

    async def process_video(self, url: str) -> dict:
        """Run the full content pipeline for a single video.

        Parameters
        ----------
        url: str
            The YouTube URL to process.

        Returns
        -------
        dict
            ``{"status": "success", ...}`` with step results on success or
            ``{"status": "error", "step": <stage>, ...}`` on failure.
        """

        logger.info("Starting download for %s", url)
        download_info = await self._run_with_retries(
            self.youtube_downloader.run, url, step="download"
        )
        if not download_info.success:
            logger.error("Download failed: %s", download_info.error)
            err = download_info.to_dict()
            err["step"] = "download"
            return err

        local_path = download_info.data["local_path"]
        logger.info("Uploading %s to Drive", local_path)
        drive_info = await self._run_with_retries(
            self.drive.run, local_path, "youtube", step="drive"
        )
        if not drive_info.success:
            logger.error("Drive upload failed: %s", drive_info.error)
            err = drive_info.to_dict()
            err["step"] = "drive"
            return err

        logger.info("Transcribing %s", local_path)
        transcription = await self._run_with_retries(
            self.transcriber.run, local_path, step="transcription"
        )
        if not transcription.success:
            logger.error("Transcription failed: %s", transcription.error)
            err = transcription.to_dict()
            err["step"] = "transcription"
            return err

        logger.info("Analyzing transcript")
        analysis = await self._run_with_retries(
            self.analyzer.run, transcription.data["transcript"], step="analysis"
        )
        if not analysis.success:
            logger.error("Analysis failed: %s", analysis.error)
            err = analysis.to_dict()
            err["step"] = "analysis"
            return err

        content_data = {
            **download_info.to_dict(),
            **analysis.to_dict(),
            "platform": "YouTube",
        }

        logger.info("Posting to Discord")
        discord_result = await self._run_with_retries(
            self.discord.run, content_data, drive_info.data.get("links", {}), step="discord"
        )
        if not discord_result.success:
            logger.error("Discord post failed: %s", discord_result.error)
            err = discord_result.to_dict()
            err["step"] = "discord"
            return err

        return {
            "status": "success",
            "download": download_info.to_dict(),
            "drive": drive_info.to_dict(),
            "transcription": transcription.to_dict(),
            "analysis": analysis.to_dict(),
            "discord": discord_result.to_dict(),
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run content pipeline")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()

    pipeline = ContentPipeline()
    asyncio.run(pipeline.process_video(args.url))
