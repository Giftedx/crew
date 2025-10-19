"""Profile ContentPipeline orchestrator performance."""

from __future__ import annotations

import asyncio
import cProfile
import pstats
from pathlib import Path

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline


async def profile_pipeline():
    """Profile full pipeline execution."""
    pipeline = ContentPipeline()
    # Use test URL from benchmarks
    url = "https://www.youtube.com/watch?v=test"
    result = await pipeline.process_video(url, quality="720p")
    return result


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    asyncio.run(profile_pipeline())

    profiler.disable()

    # Save profile data
    Path("profiling").mkdir(exist_ok=True)
    profiler.dump_stats("profiling/orchestrator.prof")

    # Generate analysis
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    # Top 30 functions by cumulative time
    with open("profiling/orchestrator_analysis.txt", "w") as f:
        stats.stream = f
        stats.print_stats(30)
        f.write("\n\n=== Top 20 by Total Time ===\n")
        stats.sort_stats("tottime")
        stats.print_stats(20)
        f.write("\n\n=== Most Called Functions ===\n")
        stats.sort_stats("ncalls")
        stats.print_stats(20)


if __name__ == "__main__":
    main()
