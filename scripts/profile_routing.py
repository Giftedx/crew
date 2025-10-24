"""Profile LLM routing decision performance."""

from __future__ import annotations

import cProfile
import pstats
from pathlib import Path

from ultimate_discord_intelligence_bot.core.llm_router import LLMRouter


def profile_routing_decisions():
    """Profile routing decision logic."""
    # Mock clients for profiling
    mock_clients = {
        "gpt-4": None,  # Mock client
        "claude-3-sonnet": None,
        "gpt-3.5-turbo": None,
    }

    router = LLMRouter(mock_clients)

    # Simulate 100 routing decisions
    test_messages = [{"role": "user", "content": f"Test query {i}"} for i in range(100)]

    for messages in test_messages:
        router.select_model(messages=messages, context={"complexity": "medium", "budget": 1.0})

    return router


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    profile_routing_decisions()

    profiler.disable()

    Path("benchmarks/profiling").mkdir(exist_ok=True, parents=True)
    profiler.dump_stats("benchmarks/profiling/routing.prof")

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    with open("benchmarks/profiling/routing_analysis.txt", "w") as f:
        stats.stream = f
        stats.print_stats(30)


if __name__ == "__main__":
    main()
