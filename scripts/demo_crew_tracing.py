#!/usr/bin/env python3
"""
CrewAI Tracing Demo Script

This script demonstrates the enhanced tracing capabilities by running a simple CrewAI task
and then analyzing the generated trace.
"""

import os
import sys
import time
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from crewai import Task

    from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you have CrewAI installed: pip install 'crewai[tools]'")
    sys.exit(1)


def run_demo_task():
    """Run a simple demo task to generate trace data."""
    print("🚀 Starting CrewAI Tracing Demo...")

    # Create crew instance
    crew_instance = UltimateDiscordIntelligenceBotCrew()

    # Create a simple demo task
    demo_task = Task(
        description="Perform a system status check and generate a brief health report",
        expected_output="System status report with key metrics and recommendations",
        agent=crew_instance.system_operations_manager,
    )

    # Create crew with the demo task
    crew = crew_instance.crew()
    crew.tasks = [demo_task]

    print("📋 Demo Task: System Health Check")
    print("🤖 Agent: System Operations Manager")

    try:
        # Execute the task
        print("\n⏳ Executing task...")
        start_time = time.time()

        result = crew.kickoff()

        end_time = time.time()
        duration = end_time - start_time

        print(f"\n✅ Task completed in {duration:.2f} seconds")
        print(f"📊 Result: {str(result)[:200]}...")

        # Get execution summary
        if hasattr(crew_instance, "get_execution_summary"):
            summary = crew_instance.get_execution_summary()
            print("\n📈 Execution Summary:")
            print(f"   Steps: {summary.get('total_steps', 0)}")
            print(f"   Duration: {summary.get('execution_duration', 0):.2f}s")
            print(f"   Agents: {', '.join(summary.get('agents_involved', []))}")
            print(f"   Tools: {', '.join(summary.get('tools_used', []))}")

        return True

    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        return False


def analyze_trace():
    """Analyze the generated trace."""
    print("\n🔍 Analyzing generated trace...")

    # Run the trace analysis script
    traces_dir = os.getenv("CREWAI_TRACES_DIR", "crew_data/Logs/traces")
    analysis_script = Path(__file__).parent / "analyze_crew_traces.py"

    if not analysis_script.exists():
        print(f"❌ Analysis script not found: {analysis_script}")
        return False

    try:
        import subprocess

        result = subprocess.run(
            ["python", str(analysis_script), "--traces-dir", traces_dir], capture_output=True, text=True
        )

        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Analysis failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error running analysis: {e}")
        return False

    return True


def main():
    """Main demo function."""
    print("=" * 80)
    print("🎯 CrewAI Enhanced Tracing Demo")
    print("=" * 80)

    # Check environment setup
    print("\n🔧 Checking configuration...")

    required_vars = ["CREWAI_SAVE_TRACES", "ENABLE_CREW_STEP_VERBOSE"]
    for var in required_vars:
        value = os.getenv(var, "not set")
        print(f"   {var}: {value}")

    traces_dir = os.getenv("CREWAI_TRACES_DIR", "crew_data/Logs/traces")
    print(f"   Traces will be saved to: {traces_dir}")

    # Ensure traces directory exists
    Path(traces_dir).mkdir(parents=True, exist_ok=True)

    # Run the demo task
    if run_demo_task():
        print("\n" + "=" * 50)
        time.sleep(1)  # Brief pause for trace file writing

        # Analyze the trace
        if analyze_trace():
            print("\n✨ Demo completed successfully!")
            print(f"💡 Check {traces_dir}/ for saved trace files")
            print("🎯 Try running: ./scripts/analyze_crew_traces.py --show-output")
        else:
            print("\n⚠️  Demo completed but trace analysis failed")
    else:
        print("\n❌ Demo failed during task execution")


if __name__ == "__main__":
    main()
