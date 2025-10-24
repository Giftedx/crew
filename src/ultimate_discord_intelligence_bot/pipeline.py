"""Unified pipeline for the Ultimate Discord Intelligence Bot.

This module provides the main pipeline interface that integrates all
components: vector memory, RL routing, MCP tools, prompt optimization,
and Discord publishing.
"""

from __future__ import annotations

import asyncio

from core.privacy import privacy_filter
from obs import metrics
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import (
    ContentPipeline,
)
from ultimate_discord_intelligence_bot.pipeline_components.types import (
    PipelineRunResult,
)
from ultimate_discord_intelligence_bot.services.request_budget import (
    track_request_budget,
)
from ultimate_discord_intelligence_bot.services.unified_pipeline import (
    PipelineConfig,
    UnifiedPipeline,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


__all__ = [
    "ContentPipeline",
    "PipelineConfig",
    "PipelineRunResult",
    "StepResult",
    "UnifiedPipeline",
    "metrics",
    "privacy_filter",
    "track_request_budget",
]


async def run_unified_pipeline_example():
    """Example of running the unified pipeline."""
    # Configure the pipeline
    config = PipelineConfig(
        enable_vector_memory=True,
        enable_rl_routing=True,
        enable_mcp_tools=True,
        enable_prompt_optimization=True,
        enable_discord_publishing=True,
        enable_observability=True,
    )

    # Initialize the unified pipeline
    pipeline = UnifiedPipeline(config)
    init_result = await pipeline.initialize()

    if not init_result.success:
        print(f"Pipeline initialization failed: {init_result.error}")
        return

    print("Unified pipeline initialized successfully")

    # Process some content
    content = "This is a test content for the unified pipeline"
    result = await pipeline.process_content(
        content=content,
        content_type="analysis",
        tenant="test_tenant",
        workspace="test_workspace",
    )

    if result.success:
        print(f"Content processed successfully: {result.data}")
    else:
        print(f"Content processing failed: {result.error}")

    # Get pipeline statistics
    stats_result = await pipeline.get_pipeline_stats()
    if stats_result.success:
        print(f"Pipeline stats: {stats_result.data}")

    # Perform health check
    health_result = await pipeline.health_check()
    if health_result.success:
        print(f"Pipeline health: {health_result.data}")

    # Shutdown the pipeline
    shutdown_result = await pipeline.shutdown()
    if shutdown_result.success:
        print("Pipeline shutdown completed")


if __name__ == "__main__":  # pragma: no cover - manual execution path
    import argparse

    parser = argparse.ArgumentParser(description="Run content pipeline")
    parser.add_argument("url", help="Video URL")
    parser.add_argument(
        "--quality",
        default="1080p",
        help="Maximum download resolution (e.g. 720p)",
    )
    parser.add_argument(
        "--unified",
        action="store_true",
        help="Use unified pipeline instead of legacy pipeline",
    )
    args = parser.parse_args()

    if args.unified:
        # Run unified pipeline example
        asyncio.run(run_unified_pipeline_example())
    else:
        # Run legacy pipeline
        pipeline = ContentPipeline()
        asyncio.run(pipeline.process_video(args.url, quality=args.quality))
