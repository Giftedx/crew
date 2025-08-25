import asyncio
from crewai_tools import BaseTool
from ..pipeline import ContentPipeline

class PipelineTool(BaseTool):
    """Tool wrapping the content pipeline."""

    name: str = "Content Pipeline Tool"
    description: str = "Download, transcribe, analyse and post a video to Discord."

    def _run(self, url: str) -> dict:
        pipeline = ContentPipeline()
        return asyncio.run(pipeline.process_video(url))

    # Expose run for CrewAI compatibility
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
