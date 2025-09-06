#!/usr/bin/env python3
"""
Progress tracking and dashboard for AI enhancement roadmap.
Provides real-time visibility into implementation progress, metrics, and health.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ProgressSummary:
    """Summary of roadmap implementation progress."""

    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    failed_tasks: int
    completion_percentage: float
    current_phase: str
    estimated_completion_date: str | None
    critical_blockers: list[str]


def calculate_velocity(completed_tasks: list, time_window_days: int = 30) -> float:
    """Calculate development velocity based on completed tasks within a time window.

    Args:
        completed_tasks: List of completed task dicts each optionally containing 'completed_at' ISO timestamp.
        time_window_days: Window size in days over which to measure velocity.

    Returns:
        Average tasks completed per day (float).
    """
    from datetime import datetime, timedelta

    if not completed_tasks:
        return 0.0

    cutoff_date = datetime.now(UTC) - timedelta(days=time_window_days)
    recent_tasks = [
        task
        for task in completed_tasks
        if task.get("completed_at") and datetime.fromisoformat(task["completed_at"]) > cutoff_date
    ]

    if not recent_tasks:
        return 0.0

    return len(recent_tasks) / time_window_days


def estimate_completion_date(remaining_tasks: int, velocity: float, buffer_factor: float = 1.2) -> datetime | None:
    """Estimate project completion date based on current velocity.

    If velocity is zero or negative, returns None.
    """
    from datetime import datetime, timedelta

    if velocity <= 0 or remaining_tasks <= 0:
        return None

    adjusted_velocity = velocity / buffer_factor
    days_to_complete = remaining_tasks / adjusted_velocity
    return datetime.now(UTC) + timedelta(days=days_to_complete)


class ProgressTracker:
    """Tracks and reports on roadmap implementation progress."""

    def __init__(self, progress_file: Path = Path("roadmap_progress.json")):
        self.progress_file = progress_file
        self.progress_data: dict[str, Any] = {}

    def load_progress(self) -> bool:
        """Load progress data from disk."""
        if not self.progress_file.exists():
            logger.warning("No progress file found - starting fresh")
            return False

        try:
            with open(self.progress_file) as f:
                self.progress_data = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Failed to load progress data: {e}")
            return False

    def calculate_progress_summary(self) -> ProgressSummary:
        """Calculate overall progress summary."""
        if not self.progress_data:
            return ProgressSummary(
                total_tasks=0,
                completed_tasks=0,
                in_progress_tasks=0,
                failed_tasks=0,
                completion_percentage=0.0,
                current_phase="Not Started",
                estimated_completion_date=None,
                critical_blockers=[],
            )

        tasks = self.progress_data.get("tasks", {})

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks.values() if t["status"] == "completed")
        in_progress_tasks = sum(1 for t in tasks.values() if t["status"] == "in_progress")
        failed_tasks = sum(1 for t in tasks.values() if t["status"] == "failed")

        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Find critical blockers (P0 failed tasks)
        critical_blockers = [
            f"{task_id}: {task_data['name']}"
            for task_id, task_data in tasks.items()
            if task_data["status"] == "failed" and task_data["priority"] == "P0"
        ]

        # Calculate velocity and estimated completion
        completed_tasks_list = [t for t in tasks.values() if t.get("status") == "completed"]
        velocity = calculate_velocity(completed_tasks_list)
        estimated_date = estimate_completion_date(
            remaining_tasks=len([t for t in tasks.values() if t.get("status") != "completed"]), velocity=velocity
        )

        return ProgressSummary(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            failed_tasks=failed_tasks,
            completion_percentage=completion_percentage,
            current_phase=self.progress_data.get("current_phase", "Unknown"),
            estimated_completion_date=estimated_date.isoformat() if estimated_date else None,  # Previously TODO
            critical_blockers=critical_blockers,
        )

    def display_dashboard(self):
        """Display progress dashboard in terminal."""
        summary = self.calculate_progress_summary()

        print("\n" + "=" * 80)
        print("🚀 ULTIMATE DISCORD INTELLIGENCE BOT - AI ENHANCEMENT ROADMAP")
        print("=" * 80)

        print("\n📊 PROGRESS OVERVIEW")
        print(f"   Current Phase: {summary.current_phase}")
        print(f"   Overall Progress: {summary.completion_percentage:.1f}%")
        print(f"   Tasks: {summary.completed_tasks}/{summary.total_tasks} completed")

        # Progress bar
        bar_width = 50
        filled = int(bar_width * summary.completion_percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"   [{bar}] {summary.completion_percentage:.1f}%")

        print("\n📈 TASK BREAKDOWN")
        print(f"   ✅ Completed: {summary.completed_tasks}")
        print(f"   🔄 In Progress: {summary.in_progress_tasks}")
        print(f"   ❌ Failed: {summary.failed_tasks}")
        print(
            f"   📝 Pending: {summary.total_tasks - summary.completed_tasks - summary.in_progress_tasks - summary.failed_tasks}"
        )

        if summary.critical_blockers:
            print("\n🚨 CRITICAL BLOCKERS")
            for blocker in summary.critical_blockers:
                print(f"   ⚠️  {blocker}")

        # Recent metrics
        if "metrics_history" in self.progress_data and self.progress_data["metrics_history"]:
            latest_metrics = self.progress_data["metrics_history"][-1]
            print("\n📊 LATEST METRICS")
            print(f"   Cost/Interaction: ${latest_metrics['cost_per_interaction']:.3f}")
            print(f"   Response Latency P95: {latest_metrics['response_latency_p95']:.1f}s")
            print(f"   Error Rate: {latest_metrics['error_rate']:.1%}")
            print(f"   Cache Hit Rate: {latest_metrics['cache_hit_rate']:.1%}")

        # Phase-specific details
        self._display_phase_details()

        print(f"\n🕒 Last Updated: {self.progress_data.get('last_updated', 'Unknown')}")
        print("=" * 80 + "\n")

    def _display_phase_details(self):
        """Display detailed progress for current phase."""
        if not self.progress_data.get("tasks"):
            return

        current_phase = self.progress_data.get("current_phase", "")
        phase_tasks = {
            task_id: task_data
            for task_id, task_data in self.progress_data["tasks"].items()
            if task_data["phase"] == current_phase
        }

        if not phase_tasks:
            return

        print(f"\n🔍 {current_phase.upper()} PHASE DETAILS")

        for task_id, task_data in sorted(phase_tasks.items(), key=lambda x: x[1]["week"]):
            status_icon = {"completed": "✅", "in_progress": "🔄", "failed": "❌", "pending": "⏳", "skipped": "⏭️"}.get(
                task_data["status"], "❓"
            )

            priority_color = {"P0": "🔴", "P1": "🟡", "P2": "🟢", "P3": "🔵"}.get(task_data["priority"], "⚪")

            print(f"   {status_icon} {priority_color} {task_id}: {task_data['name']}")

            if task_data["status"] == "failed" and task_data.get("error_message"):
                print(f"      ❗ Error: {task_data['error_message']}")

    def export_progress_report(self, output_file: Path = Path("progress_report.json")):
        """Export detailed progress report for external analysis."""
        summary = self.calculate_progress_summary()

        report = {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_tasks": summary.total_tasks,
                "completed_tasks": summary.completed_tasks,
                "in_progress_tasks": summary.in_progress_tasks,
                "failed_tasks": summary.failed_tasks,
                "completion_percentage": summary.completion_percentage,
                "current_phase": summary.current_phase,
                "critical_blockers": summary.critical_blockers,
            },
            "detailed_tasks": self.progress_data.get("tasks", {}),
            "metrics_history": self.progress_data.get("metrics_history", []),
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Progress report exported to {output_file}")

    def main(self):
        """Main execution for progress tracker."""
        if not self.load_progress():
            print("❌ No progress data found. Run roadmap_executor.py first.")
            return False

        self.display_dashboard()
        return True


def main():
    tracker = ProgressTracker()
    success = tracker.main()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
