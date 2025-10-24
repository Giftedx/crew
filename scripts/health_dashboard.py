#!/usr/bin/env python3
"""Tool Health Monitoring Dashboard.

This script provides a web-based dashboard for monitoring tool health
and performance metrics.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    from flask import Flask, jsonify, render_template, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not available - dashboard will run in console mode")


class HealthDashboard:
    """Web-based health monitoring dashboard."""

    def __init__(self):
        """Initialize the dashboard."""
        self.app = Flask(__name__) if FLASK_AVAILABLE else None
        self.health_data: dict[str, Any] = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes."""
        if not self.app:
            return

        @self.app.route("/")
        def index():
            """Main dashboard page."""
            return render_template(
                "health_dashboard.html", health_data=self.health_data, timestamp=datetime.now().isoformat()
            )

        @self.app.route("/api/health")
        def api_health():
            """Health data API endpoint."""
            return jsonify(self.health_data)

        @self.app.route("/api/health/refresh", methods=["POST"])
        def api_refresh():
            """Refresh health data."""
            self.refresh_health_data()
            return jsonify({"status": "success", "timestamp": datetime.now().isoformat()})

    def load_health_data(self) -> dict[str, Any]:
        """Load health data from report file."""
        report_path = Path("tool_health_report.json")

        if report_path.exists():
            try:
                with open(report_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load health report: {e}")

        return {
            "health_score": 0,
            "health_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": "No health data available",
        }

    def refresh_health_data(self):
        """Refresh health data by running health monitor."""
        import subprocess
        import sys

        try:
            # Run the health monitor
            result = subprocess.run(
                [sys.executable, "scripts/tool_health_monitor.py"], capture_output=True, text=True, cwd=Path.cwd()
            )

            if result.returncode == 0:
                self.health_data = self.load_health_data()
                print("✅ Health data refreshed successfully")
            else:
                print(f"❌ Health monitor failed: {result.stderr}")
                self.health_data = {
                    "health_score": 0,
                    "health_status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": result.stderr,
                }

        except Exception as e:
            print(f"❌ Failed to refresh health data: {e}")
            self.health_data = {
                "health_score": 0,
                "health_status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def generate_console_report(self):
        """Generate console-based health report."""
        print("🔍 Tool Health Dashboard - Console Mode")
        print("=" * 50)

        health_data = self.load_health_data()

        if "error" in health_data:
            print(f"❌ {health_data['error']}")
            return

        print(f"📊 Health Score: {health_data.get('health_score', 0)}/100")
        print(f"📊 Status: {health_data.get('health_status', 'unknown').upper()}")
        print(f"📊 Checks Passed: {health_data.get('passed_checks', 0)}/{health_data.get('total_checks', 0)}")

        if health_data.get("check_duration"):
            print(f"📊 Duration: {health_data['check_duration']:.4f}s")

        # Show errors
        errors = health_data.get("errors", [])
        if errors:
            print(f"\n❌ Errors ({len(errors)}):")
            for error in errors[:5]:
                print(f"  • {error}")
            if len(errors) > 5:
                print(f"  • ... and {len(errors) - 5} more errors")

        # Show warnings
        warnings = health_data.get("warnings", [])
        if warnings:
            print(f"\n⚠️  Warnings ({len(warnings)}):")
            for warning in warnings[:5]:
                print(f"  • {warning}")
            if len(warnings) > 5:
                print(f"  • ... and {len(warnings) - 5} more warnings")

        # Show healthy tools
        healthy_tools = health_data.get("healthy_tools", [])
        if healthy_tools:
            print(f"\n✅ Healthy Tools ({len(healthy_tools)}):")
            for tool in healthy_tools[:5]:
                print(f"  • {tool}")
            if len(healthy_tools) > 5:
                print(f"  • ... and {len(healthy_tools) - 5} more tools")

        # Show detailed metrics
        if "import_health" in health_data:
            import_health = health_data["import_health"]
            print("\n📦 Import Health:")
            print(f"  • Successful: {import_health.get('successful_imports', 0)}")
            print(f"  • Failed: {len(import_health.get('failed_imports', []))}")

        if "instantiation_health" in health_data:
            instantiation_health = health_data["instantiation_health"]
            print("\n🔧 Instantiation Health:")
            print(f"  • Successful: {instantiation_health.get('successful_instantiations', 0)}")
            print(f"  • Failed: {len(instantiation_health.get('failed_instantiations', []))}")

        if "memory_health" in health_data:
            memory_health = health_data["memory_health"]
            if memory_health.get("rss_mb"):
                print("\n💾 Memory Usage:")
                print(f"  • RSS: {memory_health.get('rss_mb', 0):.2f} MB")
                print(f"  • VMS: {memory_health.get('vms_mb', 0):.2f} MB")
                print(f"  • Status: {memory_health.get('status', 'unknown')}")

    def run_dashboard(self, port: int = 5000, host: str = "127.0.0.1"):
        """Run the health dashboard."""
        if not FLASK_AVAILABLE:
            print("❌ Flask not available - running in console mode")
            self.generate_console_report()
            return

        # Load initial health data
        self.health_data = self.load_health_data()

        print(f"🚀 Starting Health Dashboard on http://{host}:{port}")
        print("📊 Dashboard features:")
        print("  • Real-time health monitoring")
        print("  • Tool import/instantiation status")
        print("  • StepResult compliance checking")
        print("  • Memory usage monitoring")
        print("  • Agent-tool wiring validation")

        try:
            self.app.run(host=host, port=port, debug=False)
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")
        except Exception as e:
            print(f"❌ Dashboard failed: {e}")
            self.generate_console_report()


def main():
    """Main dashboard function."""
    import argparse

    parser = argparse.ArgumentParser(description="Tool Health Monitoring Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host")
    parser.add_argument("--console", action="store_true", help="Run in console mode")

    args = parser.parse_args()

    dashboard = HealthDashboard()

    if args.console or not FLASK_AVAILABLE:
        dashboard.generate_console_report()
    else:
        dashboard.run_dashboard(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
