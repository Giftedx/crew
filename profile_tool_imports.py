#!/usr/bin/env python3
"""Profile tool import time to measure consolidation improvements."""

import sys
import time
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def profile_tool_imports():
    """Profile the time it takes to import all tools."""
    print("Profiling tool import times...")

    # Measure individual tool imports
    tools_to_test = [
        "ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool",
        "ultimate_discord_intelligence_bot.tools.analysis.text_analysis_tool",
        "ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool",
        "ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool",
    ]

    import_times = {}

    for tool_module in tools_to_test:
        start_time = time.time()
        try:
            __import__(tool_module)
            end_time = time.time()
            import_times[tool_module] = end_time - start_time
            print(f"✓ {tool_module}: {import_times[tool_module]:.3f}s")
        except Exception as e:
            print(f"✗ {tool_module}: Failed - {e}")
            import_times[tool_module] = None

    # Measure total import time
    start_time = time.time()
    try:
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\nTotal tool import time: {total_time:.3f}s")

        # Calculate average
        valid_times = [t for t in import_times.values() if t is not None]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            print(f"Average individual import time: {avg_time:.3f}s")

    except Exception as e:
        print(f"Failed to import tools: {e}")

    return import_times


if __name__ == "__main__":
    profile_tool_imports()
