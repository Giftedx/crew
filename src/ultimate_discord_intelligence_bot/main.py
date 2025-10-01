import asyncio
import sys

from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
from ultimate_discord_intelligence_bot.enhanced_crew_integration import (
    execute_crew_with_quality_monitoring,
)

_MIN_ARGS = 2  # program name + command

# This file simply wires CLI commands to the crew. Avoid adding heavy logic.


async def run_async() -> None:
    """Kick off the crew with enhanced monitoring and a sample URL."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

    print("🚀 Starting Enhanced CrewAI Execution...")
    print(f"📝 Processing: {inputs['url']}")

    result = await execute_crew_with_quality_monitoring(inputs=inputs, quality_threshold=0.7, enable_alerts=True)

    # Display enhanced results
    print("\n✅ Execution completed!")
    print(f"⭐ Quality Score: {result.get('quality_score', 0.0):.2f}")
    print(f"⏱️  Execution Time: {result.get('execution_time', 0.0):.1f}s")
    print(f"🚨 Performance Alerts: {len(result.get('performance_alerts', []))}")

    if result.get("performance_alerts"):
        print("\n📋 Performance Alerts:")
        for alert in result.get("performance_alerts", []):
            print(f"  • {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")

    return result


def run() -> None:
    """Kick off the crew with enhanced monitoring."""
    asyncio.run(run_async())


def train() -> None:
    """Train the crew for a given number of iterations with enhanced monitoring."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

    # For training, we still use the original approach as CrewAI's train method
    # requires the direct crew instance. Enhanced monitoring is primarily for execution.
    print("📚 Training mode: Using standard CrewAI training interface...")
    UltimateDiscordIntelligenceBotCrew().crew().train(
        n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
    )


def replay() -> None:
    """Replay the crew execution from a specific task."""
    UltimateDiscordIntelligenceBotCrew().crew().replay(task_id=sys.argv[1])


def test() -> None:
    """Test the crew execution with enhanced monitoring."""
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

    # For testing, we use enhanced monitoring with test parameters
    print("🧪 Test mode: Using enhanced CrewAI execution with monitoring...")

    async def test_async():
        result = await execute_crew_with_quality_monitoring(
            inputs=inputs,
            quality_threshold=0.8,  # Higher threshold for testing
            enable_alerts=True,
        )

        print("🧪 Test Results:")
        print(f"  Quality Score: {result.get('quality_score', 0.0):.2f}")
        print(f"  Execution Time: {result.get('execution_time', 0.0):.1f}s")
        print(f"  Alerts Generated: {len(result.get('performance_alerts', []))}")

        return result

    asyncio.run(test_async())


if __name__ == "__main__":
    if len(sys.argv) < _MIN_ARGS:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
