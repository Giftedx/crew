import asyncio
import logging
import time
from typing import Any

from crewai.tools import BaseTool

from ..pipeline import ContentPipeline

logger = logging.getLogger(__name__)


class PipelineTool(BaseTool):
    """Tool wrapping the content pipeline."""

    name: str = "Content Pipeline Tool"
    description: str = "Download, transcribe, analyse and post a video to Discord. Provide url and optional quality."

    def _run(self, url: str, quality: str = "1080p") -> dict[str, Any]:
        """
        Process video with comprehensive error handling.

        Args:
            url: Video URL to process (required)
            quality: Video quality preference (default: 1080p)

        Returns:
            Dict containing processing results and metadata
        """
        start_time = time.time()

        try:
            # Validate inputs
            if not url or not isinstance(url, str):
                return {
                    "status": "error",
                    "error": "URL is required and must be a string",
                    "url": url,
                    "quality": quality,
                }

            if not quality or not isinstance(quality, str):
                quality = "1080p"  # Default fallback

            logger.info(f"Starting pipeline processing for URL: {url} with quality: {quality}")

            pipeline = ContentPipeline()
            result = asyncio.run(pipeline.process_video(url, quality=quality))

            # Ensure consistent return format
            if not isinstance(result, dict):
                result = {"status": "success", "data": result}

            # Add metadata
            result.update(
                {
                    "processing_time": time.time() - start_time,
                    "url": url,
                    "quality": quality,
                    "timestamp": time.time(),
                }
            )

            logger.info(
                f"Pipeline processing completed successfully in {result['processing_time']:.2f}s"
            )
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Pipeline processing failed for URL {url}: {error_msg}")

            return {
                "status": "error",
                "error": error_msg,
                "url": url,
                "quality": quality,
                "processing_time": time.time() - start_time,
                "timestamp": time.time(),
            }

    def run(self, *args, **kwargs) -> dict[str, Any]:
        """Public wrapper with type safety."""
        return self._run(*args, **kwargs)
