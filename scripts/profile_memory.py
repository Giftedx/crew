"""Profile vector store and embedding operations."""

from __future__ import annotations

import asyncio
import cProfile
import pstats
from pathlib import Path

from memory.vector_store import EnhancedVectorStore


async def profile_vector_operations():
    """Profile vector store operations."""
    store = EnhancedVectorStore()

    # Test data
    test_content = {
        "text": "Sample content for embedding and storage",
        "metadata": {"source": "test", "type": "benchmark"},
    }
    test_embedding = [0.1] * 768  # Typical embedding dimension

    # Profile store operations
    await store.store_vectors(
        vectors=[test_embedding] * 100, payloads=[test_content] * 100, tenant="benchmark", workspace="profiling"
    )

    # Profile search operations
    await store.search_similar(query_vector=test_embedding, limit=50, tenant="benchmark", workspace="profiling")

    # Profile batch operations
    await store.batch_upsert(
        vectors=[test_embedding] * 500, payloads=[test_content] * 500, tenant="benchmark", workspace="profiling"
    )

    return store


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    asyncio.run(profile_vector_operations())

    profiler.disable()

    Path("profiling").mkdir(exist_ok=True)
    profiler.dump_stats("profiling/memory.prof")

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")

    with open("profiling/memory_analysis.txt", "w") as f:
        stats.stream = f
        stats.print_stats(30)


if __name__ == "__main__":
    main()
