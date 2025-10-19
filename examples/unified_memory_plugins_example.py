"""Example: Using UnifiedMemoryService with memory plugins.

Demonstrates plugin-based memory routing for specialty backends:
- Mem0: Long-term episodic memory
- HippoRAG: Continual learning with consolidation
- Graph: Knowledge graph operations
"""

import asyncio

from ultimate_discord_intelligence_bot.memory import get_unified_memory
from ultimate_discord_intelligence_bot.memory.plugins import (
    GraphPlugin,
    HippoRAGPlugin,
    Mem0Plugin,
)


async def example_mem0_plugin():
    """Example: Mem0 plugin for user preferences."""
    print("\n=== Mem0 Plugin Example ===")

    # Get unified memory service
    memory = get_unified_memory()

    # Register Mem0 plugin
    mem0 = Mem0Plugin()
    memory.register_plugin("mem0", mem0)

    # Store user preference using Mem0
    result = await memory.upsert(
        tenant="demo",
        workspace="main",
        records=[
            {
                "content": "User prefers concise summaries with bullet points.",
                "metadata": {"type": "preference", "category": "output_format"},
            },
            {
                "content": "User is interested in AI safety and alignment research.",
                "metadata": {"type": "interest", "category": "topics"},
            },
        ],
        creator="user123",
        plugin="mem0",  # Route to Mem0 plugin
    )

    print(f"Storage result: {result.success}")
    if result.success:
        print(f"  Stored: {result.data.get('stored')} records")
        print(f"  Backend: {result.data.get('backend')}")

    # Query Mem0 for relevant preferences
    query_result = await memory.query(
        tenant="demo",
        workspace="main",
        vector=[],  # Not used by plugins
        top_k=5,
        creator="user123",
        plugin="mem0",
        query_text="What does the user prefer for summaries?",
    )

    print(f"\nQuery result: {query_result.success}")
    if query_result.success:
        print(f"  Found: {query_result.data.get('count')} memories")
        for i, memory_item in enumerate(query_result.data.get("results", [])[:2], 1):
            print(f"  [{i}] {memory_item.get('content', '')[:80]}")
            print(f"      Score: {memory_item.get('score', 0.0):.3f}")


async def example_hipporag_plugin():
    """Example: HippoRAG plugin for continual learning."""
    print("\n=== HippoRAG Plugin Example ===")

    memory = get_unified_memory()

    # Register HippoRAG plugin
    hipporag = HippoRAGPlugin()
    memory.register_plugin("hipporag", hipporag)

    # Store knowledge with continual learning
    result = await memory.upsert(
        tenant="demo",
        workspace="research",
        records=[
            {
                "content": "Transformer architectures use self-attention mechanisms to process sequences in parallel. "
                "They have revolutionized natural language processing by enabling efficient training on large corpora.",
                "metadata": {
                    "source": "research_paper",
                    "topic": "transformers",
                    "tags": ["nlp", "attention", "architecture"],
                },
            }
        ],
        creator="researcher",
        plugin="hipporag",  # Route to HippoRAG plugin
    )

    print(f"Storage result: {result.success}")
    if result.success:
        print(f"  Stored: {result.data.get('stored')} records")
        print(f"  Backend: {result.data.get('backend')}")
        print(f"  Capabilities: {', '.join(result.data.get('capabilities', []))}")

    # Query HippoRAG with reasoning
    query_result = await memory.query(
        tenant="demo",
        workspace="research",
        vector=[],
        top_k=3,
        creator="researcher",
        plugin="hipporag",
        query_text="How do transformers process sequential data?",
    )

    print(f"\nQuery result: {query_result.success}")
    if query_result.success:
        print(f"  Found: {query_result.data.get('count')} memories")
        for i, item in enumerate(query_result.data.get("results", [])[:1], 1):
            print(f"  [{i}] {item.get('content', '')[:80]}")
            print(f"      Score: {item.get('score', 0.0):.3f}")
            reasoning = item.get("reasoning", "")
            if reasoning:
                print(f"      Reasoning: {reasoning[:100]}...")


async def example_graph_plugin():
    """Example: Graph plugin for knowledge relationships."""
    print("\n=== Graph Plugin Example ===")

    memory = get_unified_memory()

    # Register Graph plugin
    graph = GraphPlugin()
    memory.register_plugin("graph", graph)

    # Store knowledge as graph
    result = await memory.upsert(
        tenant="demo",
        workspace="knowledge",
        records=[
            {
                "content": "Python is a high-level programming language. "
                "It supports object-oriented programming. "
                "Python is widely used for data science and machine learning. "
                "Popular frameworks include TensorFlow and PyTorch.",
                "metadata": {
                    "source": "documentation",
                    "tags": ["python", "programming", "ml"],
                },
            }
        ],
        creator="curator",
        plugin="graph",  # Route to Graph plugin
    )

    print(f"Storage result: {result.success}")
    if result.success:
        print(f"  Stored: {result.data.get('stored')} graphs")
        print(f"  Graph IDs: {result.data.get('graph_ids', [])}")

    # Query graphs by keyword
    query_result = await memory.query(
        tenant="demo",
        workspace="knowledge",
        vector=[],
        top_k=3,
        creator="curator",
        plugin="graph",
        query_text="Python machine learning frameworks",
    )

    print(f"\nQuery result: {query_result.success}")
    if query_result.success:
        print(f"  Found: {query_result.data.get('count')} graphs")
        for i, graph_item in enumerate(query_result.data.get("results", [])[:1], 1):
            print(f"  [{i}] Graph ID: {graph_item.get('graph_id', 'N/A')}")
            print(f"      Score: {graph_item.get('score', 0.0):.3f}")
            print(f"      Keywords: {', '.join(graph_item.get('keywords', [])[:5])}")
            print(
                f"      Nodes: {graph_item.get('node_count', 0)}, Edges: {graph_item.get('edge_count', 0)}"
            )


async def example_plugin_comparison():
    """Example: Compare different memory backends for the same content."""
    print("\n=== Plugin Comparison Example ===")

    memory = get_unified_memory()

    # Register all plugins
    memory.register_plugin("mem0", Mem0Plugin())
    memory.register_plugin("hipporag", HippoRAGPlugin())
    memory.register_plugin("graph", GraphPlugin())

    content = (
        "Deep learning models require large amounts of training data. "
        "Transfer learning can reduce data requirements by leveraging pre-trained models. "
        "Fine-tuning is a common approach for adapting models to new tasks."
    )

    # Store same content in all three backends
    print("Storing content in all backends...")

    # Mem0: User learning pattern
    mem0_result = await memory.upsert(
        tenant="demo",
        workspace="comparison",
        records=[{"content": content, "metadata": {"type": "learning_pattern"}}],
        plugin="mem0",
    )
    print(
        f"  Mem0: {mem0_result.success} (backend: {mem0_result.data.get('backend', 'N/A')})"
    )

    # HippoRAG: Continual knowledge
    hippo_result = await memory.upsert(
        tenant="demo",
        workspace="comparison",
        records=[{"content": content, "metadata": {"type": "knowledge"}}],
        plugin="hipporag",
    )
    print(
        f"  HippoRAG: {hippo_result.success} (backend: {hippo_result.data.get('backend', 'N/A')})"
    )

    # Graph: Knowledge relationships
    graph_result = await memory.upsert(
        tenant="demo",
        workspace="comparison",
        records=[{"content": content, "metadata": {"type": "relationships"}}],
        plugin="graph",
    )
    print(
        f"  Graph: {graph_result.success} (backend: {graph_result.data.get('backend', 'N/A')})"
    )

    # Query same question across all backends
    query = "How to train models with limited data?"

    print(f"\nQuerying all backends: '{query}'")

    # Mem0 retrieval
    mem0_query = await memory.query(
        tenant="demo",
        workspace="comparison",
        vector=[],
        plugin="mem0",
        query_text=query,
    )
    print(
        f"  Mem0: Found {mem0_query.data.get('count', 0) if mem0_query.success else 0} results"
    )

    # HippoRAG retrieval
    hippo_query = await memory.query(
        tenant="demo",
        workspace="comparison",
        vector=[],
        plugin="hipporag",
        query_text=query,
    )
    print(
        f"  HippoRAG: Found {hippo_query.data.get('count', 0) if hippo_query.success else 0} results"
    )

    # Graph retrieval
    graph_query = await memory.query(
        tenant="demo",
        workspace="comparison",
        vector=[],
        plugin="graph",
        query_text=query,
    )
    print(
        f"  Graph: Found {graph_query.data.get('count', 0) if graph_query.success else 0} results"
    )


async def main():
    """Run all examples."""
    print("=" * 60)
    print("UnifiedMemoryService Plugin Examples")
    print("=" * 60)

    try:
        await example_mem0_plugin()
    except Exception as exc:
        print(f"Mem0 example failed (expected if Mem0 not configured): {exc}")

    try:
        await example_hipporag_plugin()
    except Exception as exc:
        print(f"HippoRAG example failed (expected if package not installed): {exc}")

    try:
        await example_graph_plugin()
    except Exception as exc:
        print(f"Graph example failed: {exc}")

    try:
        await example_plugin_comparison()
    except Exception as exc:
        print(f"Comparison example failed: {exc}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
