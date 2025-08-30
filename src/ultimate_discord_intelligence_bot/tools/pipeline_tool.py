import asyncio
import logging
import time
from typing import Any, TypedDict

from ..pipeline import ContentPipeline
from ._base import BaseTool

logger = logging.getLogger(__name__)


class _PipelineResult(TypedDict, total=False):
    status: str
    url: str
    quality: str
    processing_time: float
    timestamp: float
    data: Any
    error: str


class PipelineTool(BaseTool[_PipelineResult]):
    """Tool wrapping the content pipeline."""

    name: str = "Content Pipeline Tool"
    description: str = "Download, transcribe, analyse and post a video to Discord. Provide url and optional quality."

    def _run(self, url: str, quality: str = "1080p") -> _PipelineResult:
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
                return _PipelineResult(
                    status="error",
                    error="URL is required and must be a string",
                    url=url,
                    quality=quality,
                )

            if not quality or not isinstance(quality, str):
                quality = "1080p"  # Default fallback

            logger.info(f"Starting pipeline processing for URL: {url} with quality: {quality}")

            pipeline = ContentPipeline()
            result = asyncio.run(pipeline.process_video(url, quality=quality))

            # Normalise into structured result (pipeline returns TypedDict already)
            status_raw = result.get("status")
            status_val = status_raw if isinstance(status_raw, str) else "success"
            payload: Any = result.get("data", result)
            result_dict: _PipelineResult = {"status": status_val, "data": payload}

            processing_time = time.time() - start_time
            result_dict.update(
                {
                    "processing_time": processing_time,
                    "url": url,
                    "quality": quality,
                    "timestamp": time.time(),
                }
            )
            logger.info(
                f"Pipeline processing completed successfully in {processing_time:.2f}s"
            )
            return result_dict

        except Exception as e:  # pragma: no cover - error path
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

    def run(self, url: str, quality: str = "1080p") -> _PipelineResult:  # pragma: no cover - thin wrapper
        return self._run(url, quality)
