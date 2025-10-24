#!/usr/bin/env python3
"""Metrics Dashboard for Tool Monitoring.

This script provides a comprehensive dashboard for viewing tool metrics,
performance data, and system observability information.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from ultimate_discord_intelligence_bot.observability.metrics_collector import (
        generate_metrics_report,
        get_metrics_collector,
        get_system_metrics,
    )

    METRICS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Metrics not available: {e}")
    METRICS_AVAILABLE = False


class MetricsDashboard:
    """Comprehensive metrics dashboard for tool monitoring."""

    def __init__(self):
        """Initialize the metrics dashboard."""
        self.collector = get_metrics_collector() if METRICS_AVAILABLE else None

    def display_system_overview(self):
        """Display system overview metrics."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return

        print("🔍 System Overview")
        print("=" * 50)

        try:
            system_metrics = get_system_metrics()

            print(f"📊 Total Tool Calls: {system_metrics.total_tool_calls:,}")
            print(f"📊 Total Execution Time: {system_metrics.total_execution_time:.2f}s")
            print(f"📊 Active Tools: {system_metrics.active_tools}")
            print(f"📊 System Uptime: {system_metrics.system_uptime:.2f}s")
            print(f"📊 Memory Usage: {system_metrics.memory_usage_mb:.2f} MB")
            print(f"📊 CPU Usage: {system_metrics.cpu_usage_percent:.1f}%")

            if system_metrics.last_updated:
                print(f"📊 Last Updated: {system_metrics.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"❌ Failed to get system metrics: {e}")

    def display_tool_metrics(self, limit: int = 10):
        """Display tool metrics."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return

        print(f"\n🔧 Tool Metrics (Top {limit})")
        print("=" * 50)

        try:
            collector = get_metrics_collector()
            all_metrics = collector.get_all_tool_metrics()

            if not all_metrics:
                print("📭 No tool metrics available")
                return

            # Sort by total calls
            sorted_tools = sorted(all_metrics.values(), key=lambda x: x.total_calls, reverse=True)[:limit]

            print(f"{'Tool Name':<30} {'Calls':<8} {'Success%':<10} {'Avg Time':<10} {'Last Called':<15}")
            print("-" * 85)

            for tool in sorted_tools:
                last_called = tool.last_called.strftime("%H:%M:%S") if tool.last_called else "Never"
                print(
                    f"{tool.tool_name:<30} {tool.total_calls:<8} {tool.success_rate * 100:<9.1f}% {tool.average_execution_time:<9.4f}s {last_called:<15}"
                )

        except Exception as e:
            print(f"❌ Failed to get tool metrics: {e}")

    def display_performance_analysis(self):
        """Display performance analysis."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return

        print("\n⚡ Performance Analysis")
        print("=" * 50)

        try:
            collector = get_metrics_collector()

            # Slowest tools
            print("🐌 Slowest Tools:")
            slowest = collector.get_slowest_tools(5)
            for i, tool in enumerate(slowest, 1):
                print(f"  {i}. {tool.tool_name}: {tool.average_execution_time:.4f}s avg ({tool.total_calls} calls)")

            # Error-prone tools
            print("\n❌ Most Error-Prone Tools:")
            error_prone = collector.get_most_error_prone_tools(5)
            for i, tool in enumerate(error_prone, 1):
                error_rate = tool.failed_calls / tool.total_calls if tool.total_calls > 0 else 0
                print(
                    f"  {i}. {tool.tool_name}: {error_rate * 100:.1f}% error rate ({tool.failed_calls}/{tool.total_calls})"
                )

            # Top performers
            print("\n🏆 Top Performers:")
            top_tools = collector.get_top_tools(5)
            for i, tool in enumerate(top_tools, 1):
                print(f"  {i}. {tool.tool_name}: {tool.total_calls} calls, {tool.success_rate * 100:.1f}% success")

        except Exception as e:
            print(f"❌ Failed to get performance analysis: {e}")

    def display_health_status(self):
        """Display health status."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return

        print("\n🏥 Health Status")
        print("=" * 50)

        try:
            collector = get_metrics_collector()
            all_metrics = collector.get_all_tool_metrics()

            if not all_metrics:
                print("📭 No tools to analyze")
                return

            # Calculate health metrics
            total_tools = len(all_metrics)
            active_tools = len([m for m in all_metrics.values() if m.total_calls > 0])
            healthy_tools = len([m for m in all_metrics.values() if m.success_rate >= 0.8])
            problematic_tools = len([m for m in all_metrics.values() if m.success_rate < 0.5 and m.total_calls > 0])

            print(f"📊 Total Tools: {total_tools}")
            print(f"📊 Active Tools: {active_tools}")
            print(f"📊 Healthy Tools (≥80% success): {healthy_tools}")
            print(f"📊 Problematic Tools (<50% success): {problematic_tools}")

            # Health score
            if active_tools > 0:
                health_score = (healthy_tools / active_tools) * 100
                print(f"📊 Health Score: {health_score:.1f}%")

                if health_score >= 90:
                    print("✅ System Health: Excellent")
                elif health_score >= 70:
                    print("⚠️  System Health: Good")
                elif health_score >= 50:
                    print("🔶 System Health: Fair")
                else:
                    print("❌ System Health: Poor")

        except Exception as e:
            print(f"❌ Failed to get health status: {e}")

    def display_detailed_report(self):
        """Display detailed metrics report."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return

        print("\n📋 Detailed Metrics Report")
        print("=" * 50)

        try:
            report = generate_metrics_report()

            print(f"📅 Report Generated: {report['timestamp']}")
            print(f"📊 Tool Count: {report['tool_count']}")
            print(f"📊 Active Tools: {report['active_tools']}")
            print(f"📊 Total Tool Calls: {report['total_tool_calls']:,}")
            print(f"📊 Average Execution Time: {report['average_execution_time']:.4f}s")

            # Top tools
            if report["top_tools"]:
                print("\n🏆 Top Tools:")
                for tool in report["top_tools"]:
                    print(
                        f"  • {tool['tool_name']}: {tool['total_calls']} calls, {tool['success_rate'] * 100:.1f}% success"
                    )

            # Slowest tools
            if report["slowest_tools"]:
                print("\n🐌 Slowest Tools:")
                for tool in report["slowest_tools"]:
                    print(f"  • {tool['tool_name']}: {tool['average_execution_time']:.4f}s avg")

            # Error-prone tools
            if report["error_prone_tools"]:
                print("\n❌ Error-Prone Tools:")
                for tool in report["error_prone_tools"]:
                    error_rate = tool["failed_calls"] / tool["total_calls"] if tool["total_calls"] > 0 else 0
                    print(f"  • {tool['tool_name']}: {error_rate * 100:.1f}% error rate")

        except Exception as e:
            print(f"❌ Failed to generate detailed report: {e}")

    def export_metrics(self, export_file: str = None):
        """Export metrics to file."""
        if not METRICS_AVAILABLE:
            print("❌ Metrics not available")
            return False

        if not export_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = f"metrics_dashboard_export_{timestamp}.json"

        try:
            collector = get_metrics_collector()
            success = collector.export_metrics(export_file)

            if success:
                print(f"✅ Metrics exported to {export_file}")
                return True
            else:
                print(f"❌ Failed to export metrics to {export_file}")
                return False

        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False

    def run_dashboard(self):
        """Run the complete metrics dashboard."""
        print("🚀 Tool Metrics Dashboard")
        print("=" * 50)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not METRICS_AVAILABLE:
            print("\n❌ Metrics collection not available")
            print("💡 Make sure the metrics collector is properly installed and configured")
            return

        try:
            # Display all dashboard sections
            self.display_system_overview()
            self.display_tool_metrics(limit=10)
            self.display_performance_analysis()
            self.display_health_status()
            self.display_detailed_report()

            # Export metrics
            print("\n💾 Exporting metrics...")
            self.export_metrics()

            print("\n✅ Dashboard complete")

        except Exception as e:
            print(f"❌ Dashboard failed: {e}")


def main():
    """Main dashboard function."""
    import argparse

    parser = argparse.ArgumentParser(description="Tool Metrics Dashboard")
    parser.add_argument("--export", help="Export file path")
    parser.add_argument("--limit", type=int, default=10, help="Number of tools to display")

    args = parser.parse_args()

    dashboard = MetricsDashboard()

    if args.export:
        dashboard.export_metrics(args.export)
    else:
        dashboard.run_dashboard()


if __name__ == "__main__":
    main()
