"""Compatibility wrapper for the modular content pipeline."""

from __future__ import annotations

import asyncio

from core.privacy import privacy_filter
from obs import metrics
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import (
    ContentPipeline,
)
from ultimate_discord_intelligence_bot.pipeline_components.types import PipelineRunResult
from ultimate_discord_intelligence_bot.services.request_budget import track_request_budget
from ultimate_discord_intelligence_bot.step_result import StepResult

__all__ = [
    "ContentPipeline",
    "PipelineRunResult",
    "StepResult",
    "track_request_budget",
    "privacy_filter",
    "metrics",
]


if __name__ == "__main__":  # pragma: no cover - manual execution path
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
