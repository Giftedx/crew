"""Comprehensive examples of orchestration strategies.

Demonstrates dynamic strategy selection, registry usage, and
integration with unified memory plugins.

Phase 5: Orchestration Strategy Extraction
"""

import asyncio
import logging

from ultimate_discord_intelligence_bot.orchestration import (
    OrchestrationFacade,
    OrchestrationStrategy,
    get_orchestrator,
)
from ultimate_discord_intelligence_bot.orchestration.strategies import (
    FallbackStrategy,
    HierarchicalStrategy,
    MonitoringStrategy,
    get_strategy_registry,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_fallback_strategy() -> None:
    """Example 1: FallbackStrategy for degraded mode.

    Use case: System degradation, service outages, reduced capacity
    Features: Basic pipeline → analysis → fact-check → report
    """
    print("\n" + "=" * 80)
    print("Example 1: FallbackStrategy - Degraded Mode Intelligence")
    print("=" * 80)

    # Option A: Direct strategy instantiation
    strategy = FallbackStrategy()
    result = await strategy.execute_workflow(
        url="https://www.youtube.com/watch?v=example",
        depth="standard",
        tenant="demo",
        workspace="fallback-test",
    )

    print(f"\nDirect instantiation result: {result.status}")
    if result.data:
        print(f"Pipeline output: {result.data.get('pipeline_result', {}).get('status')}")
        print(f"Analysis: {result.data.get('analysis_result', {}).get('status')}")

    # Option B: Via facade with enum
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.FALLBACK)
    result = await facade.execute_workflow(
        url="https://www.youtube.com/watch?v=example",
        depth="standard",
        tenant="demo",
        workspace="fallback-test",
    )

    print(f"\nFacade result: {result.status}")

    # Option C: Via get_orchestrator helper
    orchestrator = get_orchestrator(strategy=OrchestrationStrategy.FALLBACK)
    result = await orchestrator.execute_workflow(
        url="https://www.youtube.com/watch?v=example",
        depth="standard",
        tenant="demo",
        workspace="fallback-test",
    )

    print(f"Helper result: {result.status}")


async def example_hierarchical_strategy() -> None:
    """Example 2: HierarchicalStrategy for complex coordination.

    Use case: Multi-agent coordination, parallel task execution
    Features: Executive supervisor, workflow managers, specialist agents
    """
    print("\n" + "=" * 80)
    print("Example 2: HierarchicalStrategy - Multi-Tier Agent Coordination")
    print("=" * 80)

    # Direct strategy usage with session context
    strategy = HierarchicalStrategy()

    # Create orchestration session with tasks
    result = await strategy.execute_workflow(
        url="https://arxiv.org/abs/2401.12345",
        depth="deep",
        tenant="research",
        workspace="papers",
        tasks=[
            {"name": "extract_paper_metadata", "priority": "high"},
            {"name": "analyze_methodology", "priority": "high"},
            {"name": "identify_citations", "priority": "medium"},
            {"name": "generate_summary", "priority": "low"},
        ],
    )

    print(f"\nHierarchical workflow result: {result.status}")
    if result.data:
        session = result.data.get("session", {})
        print(f"Session ID: {session.get('session_id')}")
        print(f"Tasks executed: {len(session.get('completed_tasks', []))}")
        print(f"Load balancing: {session.get('load_balancing_enabled', False)}")


async def example_monitoring_strategy() -> None:
    """Example 3: MonitoringStrategy for platform observation.

    Use case: Real-time platform monitoring, intelligent scheduling
    Platforms: YouTube, Twitch, TikTok, Instagram, Twitter, Reddit, Discord
    """
    print("\n" + "=" * 80)
    print("Example 3: MonitoringStrategy - Real-Time Platform Monitoring")
    print("=" * 80)

    # Monitor YouTube channel
    strategy = MonitoringStrategy()
    result = await strategy.execute_workflow(
        url="https://www.youtube.com/@example-channel",
        depth="standard",
        tenant="media",
        workspace="monitoring",
        platform="youtube",  # Optional: auto-detected from URL
        check_interval=300,  # 5 minutes
    )

    print(f"\nMonitoring result: {result.status}")
    if result.data:
        monitoring = result.data.get("monitoring", {})
        print(f"Platform: {monitoring.get('platform')}")
        print(f"Check interval: {monitoring.get('check_interval')}s")
        print(f"Active monitors: {monitoring.get('active_monitors', 0)}")

    # Monitor Reddit subreddit
    result = await strategy.execute_workflow(
        url="https://reddit.com/r/example",
        depth="standard",
        tenant="media",
        workspace="monitoring",
        platform="reddit",
    )

    print(f"\nReddit monitoring result: {result.status}")


async def example_dynamic_strategy_switching() -> None:
    """Example 4: Dynamic strategy switching based on conditions.

    Demonstrates runtime strategy selection without code changes.
    """
    print("\n" + "=" * 80)
    print("Example 4: Dynamic Strategy Switching")
    print("=" * 80)

    # Simulate condition-based strategy selection
    async def process_url(url: str, system_health: float) -> StepResult:
        """Process URL with strategy based on system health."""
        if system_health < 0.5:
            # System degraded - use fallback
            strategy_type = OrchestrationStrategy.FALLBACK
            print(f"\nSystem health {system_health:.1%} - using FALLBACK strategy")
        elif "arxiv.org" in url:
            # Research paper - use hierarchical for complex analysis
            strategy_type = OrchestrationStrategy.HIERARCHICAL
            print("\nResearch paper detected - using HIERARCHICAL strategy")
        elif any(platform in url for platform in ["youtube.com", "reddit.com"]):
            # Platform URL - use monitoring
            strategy_type = OrchestrationStrategy.MONITORING
            print("\nPlatform URL detected - using MONITORING strategy")
        else:
            # Default to autonomous
            strategy_type = OrchestrationStrategy.AUTONOMOUS
            print("\nStandard content - using AUTONOMOUS strategy")

        orchestrator = get_orchestrator(strategy=strategy_type)
        return await orchestrator.execute_workflow(
            url=url,
            depth="standard",
            tenant="adaptive",
            workspace="dynamic",
        )

    # Test different scenarios
    scenarios = [
        ("https://www.youtube.com/watch?v=example", 1.0),  # Monitoring
        ("https://arxiv.org/abs/2401.12345", 1.0),  # Hierarchical
        ("https://example.com/article", 0.3),  # Fallback (degraded)
    ]

    for url, health in scenarios:
        result = await process_url(url, health)
        print(f"Result: {result.status}")


async def example_registry_inspection() -> None:
    """Example 5: Registry inspection and custom strategy registration.

    Demonstrates how to inspect available strategies and register custom ones.
    """
    print("\n" + "=" * 80)
    print("Example 5: Registry Inspection & Custom Registration")
    print("=" * 80)

    registry = get_strategy_registry()

    # List all registered strategies
    print("\nRegistered strategies:")
    for name, strategy_class in registry.list_strategies().items():
        print(f"  - {name}: {strategy_class.__name__}")
        if hasattr(strategy_class, "description"):
            print(f"    {strategy_class.description}")

    # Get specific strategy
    fallback_class = registry.get("fallback")
    if fallback_class:
        print(f"\nRetrieved 'fallback' strategy: {fallback_class.__name__}")

    # Custom strategy registration example (commented - demonstration only)
    """
    class CustomStrategy:
        name = "custom"
        description = "Custom workflow logic"

        async def execute_workflow(self, url, depth, tenant, workspace, **kwargs):
            # Custom implementation
            return StepResult.ok({"custom": "result"})

    registry.register(CustomStrategy)
    print(f"\nRegistered custom strategy: {CustomStrategy.name}")
    """


async def example_memory_integration() -> None:
    """Example 6: Orchestration strategy with memory plugins.

    Demonstrates how Phase 5 orchestration strategies integrate with
    Phase 4 memory plugins for end-to-end workflows.
    """
    print("\n" + "=" * 80)
    print("Example 6: Strategy + Memory Plugin Integration")
    print("=" * 80)

    # Fallback strategy with Mem0 memory
    print("\nFallback strategy + Mem0 memory plugin:")
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.FALLBACK)
    result = await facade.execute_workflow(
        url="https://example.com/content",
        depth="standard",
        tenant="integrated",
        workspace="mem0-test",
        memory_plugin="mem0",  # Use Mem0 for episodic memory
    )
    print(f"Result: {result.status}")

    # Hierarchical strategy with HippoRAG memory
    print("\nHierarchical strategy + HippoRAG memory plugin:")
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.HIERARCHICAL)
    result = await facade.execute_workflow(
        url="https://arxiv.org/abs/2401.12345",
        depth="deep",
        tenant="integrated",
        workspace="hipporag-test",
        memory_plugin="hipporag",  # Use HippoRAG for continual learning
    )
    print(f"Result: {result.status}")

    # Monitoring strategy with Graph memory
    print("\nMonitoring strategy + Graph memory plugin:")
    facade = OrchestrationFacade(strategy=OrchestrationStrategy.MONITORING)
    result = await facade.execute_workflow(
        url="https://www.youtube.com/@channel",
        depth="standard",
        tenant="integrated",
        workspace="graph-test",
        memory_plugin="graph",  # Use Graph for relationship tracking
    )
    print(f"Result: {result.status}")


async def main() -> None:
    """Run all orchestration strategy examples."""
    print("=" * 80)
    print("ORCHESTRATION STRATEGIES - Comprehensive Examples")
    print("Phase 5: Strategy Extraction with Dynamic Registry")
    print("=" * 80)

    examples = [
        ("Fallback Strategy", example_fallback_strategy),
        ("Hierarchical Strategy", example_hierarchical_strategy),
        ("Monitoring Strategy", example_monitoring_strategy),
        ("Dynamic Switching", example_dynamic_strategy_switching),
        ("Registry Inspection", example_registry_inspection),
        ("Memory Integration", example_memory_integration),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as exc:
            logger.error(f"{name} failed: {exc}", exc_info=True)
            print(f"\n❌ {name} encountered error: {exc}")
        else:
            print(f"\n✅ {name} completed successfully")

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
