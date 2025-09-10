"""Pipeline tool for orchestrating multi-step operations per Copilot instructions."""

import asyncio
import logging
import time
from typing import Any, TypedDict

from core.settings import get_settings
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

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


class PipelineTool(BaseTool):
    """Tool wrapping the content pipeline."""

    name: str = "Content Pipeline Tool"
    description: str = "Download, transcribe, analyse and post a video to Discord. Provide url and optional quality."

    def __init__(self, pipeline: Any | None = None):
        # Retain attribute for potential future dependency injection, though current code
        # constructs its own ContentPipeline instance per run.
        self.pipeline = pipeline
        self._metrics = get_metrics()

    async def _run(self, url: str, quality: str = "1080p") -> StepResult:
        """Process video with comprehensive error handling."""
        start_time = time.time()

        try:
            # Validate inputs
            if not url or not isinstance(url, str):
                duration = time.time() - start_time
                self._metrics.histogram("tool_run_seconds", duration, labels={"tool": "pipeline"})
                self._metrics.counter("tool_runs_total", labels={"tool": "pipeline", "outcome": "error"}).inc()
                return StepResult.fail(error="URL is required and must be a string", url=url, quality=quality)

            if not quality or not isinstance(quality, str) or not quality.strip():
                settings = get_settings()
                default_quality = getattr(settings, "download_quality_default", "720p")
                quality = quality or quality.strip() or default_quality  # central default

            logger.info(f"Starting pipeline processing for URL: {url} with quality: {quality}")

            pipeline = ContentPipeline()
            result = await pipeline.process_video(url, quality=quality)

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
            logger.info(f"Pipeline processing completed successfully in {processing_time:.2f}s")
            self._metrics.counter("tool_runs_total", labels={"tool": "pipeline", "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": "pipeline"})
            return StepResult.ok(
                url=url,
                quality=quality,
                processing_time=processing_time,
                timestamp=result_dict.get("timestamp"),
                data=result_dict.get("data"),
            )

        except Exception as e:  # pragma: no cover - error path
            error_msg = str(e)
            processing_time = time.time() - start_time
            logger.error(f"Pipeline processing failed for URL {url}: {error_msg}")
            self._metrics.counter("tool_runs_total", labels={"tool": "pipeline", "outcome": "error"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": "pipeline"})
            return StepResult.fail(
                error=error_msg,
                url=url,
                quality=quality,
                processing_time=processing_time,
                timestamp=time.time(),
            )

    def run(self, url: str, quality: str = "1080p") -> StepResult:  # pragma: no cover - thin wrapper
        """Run pipeline with proper async handling."""
        try:
            # Check if we're already in an event loop (e.g., Discord bot)
            loop = asyncio.get_running_loop()
            # If we're in a running loop, we need to create a task
            # This should be called with await from the Discord command
            if loop and loop.is_running():
                # We're in an async context, caller should use _run_async instead
                raise RuntimeError(
                    "Pipeline tool is being called from an async context. "
                    "Use 'await pipeline_tool._run_async(url)' instead of 'pipeline_tool.run(url)'"
                )
        except RuntimeError:
            # No event loop running, we can use asyncio.run()
            pass

        # Use asyncio.run() when no event loop is running
        return asyncio.run(self._run_async(url, quality))

    async def _run_async(self, url: str, quality: str = "1080p") -> StepResult:
        """Async version for use within async contexts."""
        return await self._run(url, quality)

    def execute_pipeline_steps(self, steps: list[str], input_data: dict[str, Any]) -> StepResult:
        """Execute pipeline steps following StepResult pattern per instruction #3."""
        if not steps:
            return StepResult.ok(skipped=True, reason="No pipeline steps provided")

        try:
            current_data = input_data
            results: list[dict[str, object]] = []

            for step_name in steps:
                # Execute each step
                step_result = self._execute_step(step_name, current_data)

                # Check if step failed
                if not step_result.success:
                    return StepResult.fail(
                        error=f"Pipeline failed at step: {step_name}",
                        data={
                            "failed_step": step_name,
                            "completed_steps": results,
                            "error": step_result.error,
                        },
                    )

                # Use output as input for next step
                current_data = step_result.data
                results.append({"step": step_name, "success": True, "data": current_data})

            return StepResult.ok(data={"pipeline_results": results, "final_output": current_data})

        except Exception as e:
            # Recoverable error - don't raise per instruction #3
            return StepResult.fail(error=f"Pipeline execution error: {str(e)}")

    def _execute_step(self, step_name: str, input_data: dict[str, Any]) -> StepResult:
        """Execute a single pipeline step."""
        # This would call the actual pipeline step
        # For now, simulate step execution

        if step_name == "validate":
            if not input_data:
                return StepResult.fail(error="Validation failed: empty input")
            return StepResult.ok(data=input_data)

        elif step_name == "transform":
            transformed = {**input_data, "transformed": True}
            return StepResult.ok(data=transformed)

        elif step_name == "enrich":
            enriched = {**input_data, "enriched": True, "metadata": {}}
            return StepResult.ok(data=enriched)

        else:
            return StepResult.ok(skipped=True, reason=f"Unknown step: {step_name}")
