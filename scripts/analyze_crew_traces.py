#!/usr/bin/env python3
"""
CrewAI Trace Analysis Script

This script analyzes local CrewAI execution traces and displays them
in a format similar to CrewAI Enterprise dashboard traces.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click


def load_latest_trace(traces_dir: str) -> dict[str, Any] | None:
    """Load the most recent trace file."""
    traces_path = Path(traces_dir)
    if not traces_path.exists():
        return None

    # Check for summary file first
    summary_path = traces_path / "latest_trace_summary.json"
    if summary_path.exists():
        try:
            with open(summary_path) as f:
                summary = json.load(f)

            trace_file = traces_path / summary["latest_trace_file"]
            if trace_file.exists():
                with open(trace_file) as f:
                    return json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    # Fallback: find most recent trace file
    trace_files = list(traces_path.glob("crew_trace_*.json"))
    if not trace_files:
        return None

    latest_file = max(trace_files, key=lambda f: f.stat().st_mtime)
    with open(latest_file) as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}m {seconds:.1f}s"


def display_trace_summary(trace_data: dict[str, Any]) -> None:
    """Display trace summary similar to CrewAI Enterprise."""
    print("\n" + "=" * 80)
    print("🚀 CREWAI EXECUTION TRACE ANALYSIS")
    print("=" * 80)

    execution_id = trace_data.get("execution_id", "unknown")
    start_time = trace_data.get("start_time", 0)
    current_time = trace_data.get("current_time", 0)
    total_duration = current_time - start_time if current_time > start_time else 0

    # Basic execution info
    print(f"📋 Execution ID: {execution_id}")
    print(f"⏱️  Total Duration: {format_duration(total_duration)}")
    print(f"🔢 Total Steps: {trace_data.get('total_steps', 0)}")

    # Extract summary statistics
    steps = trace_data.get("steps", [])
    if steps:
        agents_used = {step.get("agent_role", "unknown") for step in steps}
        tools_used = {step.get("tool", "unknown") for step in steps if step.get("tool") != "unknown"}

        print(f"🤖 Agents Involved: {len(agents_used)}")
        print(f"🔧 Tools Used: {len(tools_used)}")

        print("\n📊 EXECUTION OVERVIEW:")
        print(f"   Agents: {', '.join(sorted(agents_used))}")
        print(f"   Tools: {', '.join(sorted(tools_used))}")


def display_step_details(steps: list[dict[str, Any]], show_output: bool = False) -> None:
    """Display detailed step information."""
    print("\n🔍 STEP-BY-STEP EXECUTION TRACE:")
    print("-" * 80)

    for i, step in enumerate(steps, 1):
        step_num = step.get("step_number", i)
        timestamp = step.get("timestamp", "")
        agent_role = step.get("agent_role", "unknown")
        tool = step.get("tool", "unknown")
        step_type = step.get("step_type", "unknown")
        status = step.get("status", "unknown")
        duration = step.get("duration_from_start", 0)

        # Format timestamp
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%H:%M:%S")
            else:
                formatted_time = "unknown"
        except Exception:
            formatted_time = "unknown"

        # Status emoji
        status_emoji = {
            "completed": "✅",
            "running": "🏃",
            "pending": "⏳",
            "error": "❌",
            "unknown": "❓",
        }.get(status.lower(), "❓")

        print(f"Step {step_num:2d} | {formatted_time} | {format_duration(duration):>8s} | {status_emoji} {agent_role}")
        print(f"        | Tool: {tool}")

        if step_type != "unknown":
            print(f"        | Type: {step_type}")

        # Show output if requested and available
        if show_output:
            raw_output = step.get("raw_output", step.get("raw_output_snippet", ""))
            if raw_output:
                # Truncate and format output
                output_lines = str(raw_output).strip().split("\n")
                if len(output_lines) > 3:
                    output_preview = "\n".join(output_lines[:2]) + f"\n... ({len(output_lines) - 2} more lines)"
                else:
                    output_preview = raw_output[:200] + ("..." if len(raw_output) > 200 else "")

                print(f"        | Output: {output_preview}")

        print("-" * 80)


def analyze_performance(steps: list[dict[str, Any]]) -> None:
    """Analyze performance patterns."""
    print("\n📈 PERFORMANCE ANALYSIS:")
    print("-" * 40)

    if not steps:
        print("No steps available for analysis.")
        return

    # Calculate step durations
    step_durations = []
    for i, step in enumerate(steps):
        if i > 0:
            prev_duration = steps[i - 1].get("duration_from_start", 0)
            curr_duration = step.get("duration_from_start", 0)
            step_duration = curr_duration - prev_duration
            step_durations.append(
                (
                    step.get("agent_role", "unknown"),
                    step.get("tool", "unknown"),
                    step_duration,
                )
            )

    if step_durations:
        # Find slowest steps
        slowest_steps = sorted(step_durations, key=lambda x: x[2], reverse=True)[:5]
        print("🐌 Slowest Operations:")
        for agent, tool, duration in slowest_steps:
            print(f"   {format_duration(duration):>8s} - {agent} using {tool}")

        # Tool usage statistics
        tool_usage = {}
        for agent, tool, duration in step_durations:
            if tool not in tool_usage:
                tool_usage[tool] = []
            tool_usage[tool].append(duration)

        print("\n🔧 Tool Performance Summary:")
        for tool, durations in sorted(tool_usage.items()):
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            print(
                f"   {tool:.<30} {len(durations):>3} uses | avg: {format_duration(avg_duration):>8s} | max: {format_duration(max_duration):>8s}"
            )


@click.command()
@click.option(
    "--traces-dir",
    default="crew_data/Logs/traces",
    help="Directory containing trace files",
)
@click.option("--show-output", is_flag=True, help="Show step output details")
@click.option("--latest", is_flag=True, default=True, help="Analyze latest trace (default)")
@click.option("--trace-file", help="Specific trace file to analyze")
def main(traces_dir: str, show_output: bool, latest: bool, trace_file: str | None):
    """Analyze CrewAI execution traces."""

    if trace_file:
        # Analyze specific file
        if not os.path.exists(trace_file):
            click.echo(f"❌ Trace file not found: {trace_file}", err=True)
            sys.exit(1)

        with open(trace_file) as f:
            trace_data = json.load(f)
    else:
        # Load latest trace
        trace_data = load_latest_trace(traces_dir)
        if not trace_data:
            click.echo(f"❌ No trace files found in {traces_dir}", err=True)
            click.echo(
                "💡 Make sure CREWAI_SAVE_TRACES=true is set in your environment",
                err=True,
            )
            sys.exit(1)

    # Display analysis
    display_trace_summary(trace_data)

    steps = trace_data.get("steps", [])
    if steps:
        display_step_details(steps, show_output)
        analyze_performance(steps)

    print(f"\n✨ Analysis complete! Found {len(steps)} execution steps.")

    # Provide enterprise comparison info
    print("\n💡 TIP: For enterprise-level tracing like the URL you shared:")
    print("   1. Sign up for CrewAI Plus/Enterprise at https://app.crewai.com")
    print("   2. Set CREWAI_API_KEY and CREWAI_PROJECT_ID in your .env")
    print("   3. Your traces will be automatically uploaded and accessible via web dashboard")


if __name__ == "__main__":
    main()
