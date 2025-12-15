import asyncio
import sys
from contextlib import suppress
from typing import NoReturn


# Early bootstrap to avoid stdlib/platform name clash
try:
    from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy  # type: ignore
except Exception:
    # Fallback for legacy package name/location
    try:
        from ultimate_discord_intelligence_bot.core.bootstrap import ensure_platform_proxy  # type: ignore
    except Exception:
        ensure_platform_proxy = None  # type: ignore

if callable(ensure_platform_proxy):  # type: ignore
    with suppress(Exception):
        ensure_platform_proxy()  # type: ignore

from domains.orchestration.crew import get_crew
from ultimate_discord_intelligence_bot.enhanced_crew_integration import execute_crew_with_quality_monitoring


def create_app():
    """Create Flask application instance for testing purposes.

    This factory function initializes a Flask application (or a mock if Flask
    is not installed) configured for testing. It is primarily used by the
    test suite to verify web-related functionality.

    Returns:
        Flask | MockApp: A configured Flask application instance or a mock object
            if Flask is not available in the environment.
    """
    try:
        from flask import Flask

        app = Flask(__name__)
        app.config["TESTING"] = True
        return app
    except ImportError:

        class MockApp:
            def __init__(self):
                self.config = {"TESTING": True}

        return MockApp()


_MIN_ARGS = 2


async def run_async() -> None:
    """Asynchronously execute the enhanced CrewAI pipeline with monitoring.

    This function triggers the main execution flow of the intelligence bot
    using a hardcoded sample URL (Rick Roll) for demonstration/testing purposes.
    It utilizes the `execute_crew_with_quality_monitoring` function to ensure
    performance metrics and quality scores are tracked.

    The execution results, including quality scores, execution time, and any
    performance alerts, are printed to standard output.

    Returns:
        None: This function does not return a value but prints results to stdout.
    """
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    print("🚀 Starting Enhanced CrewAI Execution...")
    print(f"📝 Processing: {inputs['url']}")
    result = await execute_crew_with_quality_monitoring(inputs=inputs, quality_threshold=0.7, enable_alerts=True)
    print("\n✅ Execution completed!")
    print(f"⭐ Quality Score: {result.get('quality_score', 0.0):.2f}")
    print(f"⏱️  Execution Time: {result.get('execution_time', 0.0):.1f}s")
    print(f"🚨 Performance Alerts: {len(result.get('performance_alerts', []))}")
    if result.get("performance_alerts"):
        print("\n📋 Performance Alerts:")
        for alert in result.get("performance_alerts", []):
            print(f"  • {alert.get('type', 'unknown')}: {alert.get('message', 'No message')}")


def run() -> None:
    """Entry point for the synchronous execution wrapper.

    This function sets up the asyncio event loop and runs the `run_async` function.
    It is the primary entry point for the `run` command.

    Returns:
        None
    """
    asyncio.run(run_async())


def train() -> None:
    """Train the crew agents for a specified number of iterations.

    This function invokes the CrewAI training interface. It expects command-line
    arguments for the number of iterations and the output filename.

    Command-line Arguments (expected via sys.argv):
        sys.argv[1] (str): Number of iterations (converted to int).
        sys.argv[2] (str): Filename to save the training data/model.

    Raises:
        ValueError: If sys.argv[1] cannot be converted to an integer.
        IndexError: If insufficient command-line arguments are provided.

    Returns:
        None
    """
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    print("📚 Training mode: Using standard CrewAI training interface...")
    get_crew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)


def replay() -> None:
    """Replay a specific task execution from the crew history.

    This function allows for debugging or reviewing a specific task's execution
    by its ID.

    Command-line Arguments (expected via sys.argv):
        sys.argv[1] (str): The Task ID to replay.

    Raises:
        IndexError: If the Task ID is not provided in command-line arguments.

    Returns:
        None
    """
    get_crew().crew().replay(task_id=sys.argv[1])


def test() -> None:
    """Execute the crew in test mode with enhanced monitoring.

    This function runs the `execute_crew_with_quality_monitoring` function with
    a higher quality threshold (0.8) to verify system performance and correctness.
    It runs asynchronously via `asyncio.run`.

    Returns:
        None: Prints test results to standard output.
    """
    inputs = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    print("🧪 Test mode: Using enhanced CrewAI execution with monitoring...")

    async def test_async() -> None:
        result = await execute_crew_with_quality_monitoring(inputs=inputs, quality_threshold=0.8, enable_alerts=True)
        print("🧪 Test Results:")
        print(f"  Quality Score: {result.get('quality_score', 0.0):.2f}")
        print(f"  Execution Time: {result.get('execution_time', 0.0):.1f}s")
        print(f"  Alerts Generated: {len(result.get('performance_alerts', []))}")

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
