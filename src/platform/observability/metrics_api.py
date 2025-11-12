"""Metrics API Endpoint for Tool Monitoring.

This module provides REST API endpoints for accessing tool metrics
and system observability data.
"""

from __future__ import annotations

from datetime import datetime, timezone


try:
    from flask import Flask, jsonify, request

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not available - metrics API will not be available")


class MetricsAPI:
    """REST API for tool metrics and observability data."""

    def __init__(self, app: Flask | None = None):
        """Initialize the metrics API."""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for metrics API")
        self.app = app or Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Setup API routes."""

        @self.app.route("/api/metrics/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "metrics-api"}
            )

        @self.app.route("/api/metrics/system")
        def get_system_metrics():
            """Get system-wide metrics."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_system_metrics

                metrics = get_system_metrics()
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "total_tool_calls": metrics.total_tool_calls,
                            "total_execution_time": metrics.total_execution_time,
                            "active_tools": metrics.active_tools,
                            "system_uptime": metrics.system_uptime,
                            "memory_usage_mb": metrics.memory_usage_mb,
                            "cpu_usage_percent": metrics.cpu_usage_percent,
                            "last_updated": metrics.last_updated.isoformat() if metrics.last_updated else None,
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/tools")
        def get_all_tool_metrics():
            """Get metrics for all tools."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_all_tool_metrics

                metrics = get_all_tool_metrics()
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "tool_count": len(metrics),
                            "tools": {
                                name: {
                                    "tool_name": m.tool_name,
                                    "total_calls": m.total_calls,
                                    "successful_calls": m.successful_calls,
                                    "failed_calls": m.failed_calls,
                                    "success_rate": m.success_rate,
                                    "average_execution_time": m.average_execution_time,
                                    "min_execution_time": m.min_execution_time,
                                    "max_execution_time": m.max_execution_time,
                                    "last_called": m.last_called.isoformat() if m.last_called else None,
                                    "first_called": m.first_called.isoformat() if m.first_called else None,
                                }
                                for name, m in metrics.items()
                            },
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/tools/<tool_name>")
        def get_tool_metrics(tool_name: str):
            """Get metrics for a specific tool."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_tool_metrics

                metrics = get_tool_metrics(tool_name)
                if not metrics:
                    return (jsonify({"status": "error", "error": f"Tool '{tool_name}' not found"}), 404)
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "tool_name": metrics.tool_name,
                            "total_calls": metrics.total_calls,
                            "successful_calls": metrics.successful_calls,
                            "failed_calls": metrics.failed_calls,
                            "success_rate": metrics.success_rate,
                            "average_execution_time": metrics.average_execution_time,
                            "min_execution_time": metrics.min_execution_time,
                            "max_execution_time": metrics.max_execution_time,
                            "total_execution_time": metrics.total_execution_time,
                            "last_called": metrics.last_called.isoformat() if metrics.last_called else None,
                            "first_called": metrics.first_called.isoformat() if metrics.first_called else None,
                            "error_count": metrics.error_count,
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/top-tools")
        def get_top_tools():
            """Get top tools by usage."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                limit = request.args.get("limit", 10, type=int)
                top_tools = collector.get_top_tools(limit)
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "limit": limit,
                            "tools": [
                                {
                                    "tool_name": tool.tool_name,
                                    "total_calls": tool.total_calls,
                                    "success_rate": tool.success_rate,
                                    "average_execution_time": tool.average_execution_time,
                                }
                                for tool in top_tools
                            ],
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/slowest-tools")
        def get_slowest_tools():
            """Get slowest tools by execution time."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                limit = request.args.get("limit", 10, type=int)
                slowest_tools = collector.get_slowest_tools(limit)
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "limit": limit,
                            "tools": [
                                {
                                    "tool_name": tool.tool_name,
                                    "average_execution_time": tool.average_execution_time,
                                    "total_calls": tool.total_calls,
                                    "max_execution_time": tool.max_execution_time,
                                }
                                for tool in slowest_tools
                            ],
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/error-prone-tools")
        def get_error_prone_tools():
            """Get tools with highest error rates."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                limit = request.args.get("limit", 10, type=int)
                error_prone_tools = collector.get_most_error_prone_tools(limit)
                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            "limit": limit,
                            "tools": [
                                {
                                    "tool_name": tool.tool_name,
                                    "error_rate": tool.failed_calls / tool.total_calls if tool.total_calls > 0 else 0,
                                    "failed_calls": tool.failed_calls,
                                    "total_calls": tool.total_calls,
                                    "success_rate": tool.success_rate,
                                }
                                for tool in error_prone_tools
                            ],
                        },
                    }
                )
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/report")
        def get_metrics_report():
            """Get comprehensive metrics report."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import generate_metrics_report

                report = generate_metrics_report()
                return jsonify({"status": "success", "data": report})
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/export")
        def export_metrics():
            """Export metrics to file."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                export_file = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if collector.export_metrics(export_file):
                    return jsonify(
                        {
                            "status": "success",
                            "message": f"Metrics exported to {export_file}",
                            "export_file": export_file,
                        }
                    )
                else:
                    return (jsonify({"status": "error", "error": "Failed to export metrics"}), 500)
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

        @self.app.route("/api/metrics/reset", methods=["POST"])
        def reset_metrics():
            """Reset all metrics."""
            try:
                from ultimate_discord_intelligence_bot.obs.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                collector.reset_metrics()
                return jsonify({"status": "success", "message": "All metrics have been reset"})
            except Exception as e:
                return (jsonify({"status": "error", "error": str(e)}), 500)

    def run(self, host: str = "127.0.0.1", port: int = 5001, debug: bool = False):
        """Run the metrics API server."""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required to run the metrics API")
        print(f"🚀 Starting Metrics API on http://{host}:{port}")
        print("📊 Available endpoints:")
        print("  • GET  /api/metrics/health - Health check")
        print("  • GET  /api/metrics/system - System metrics")
        print("  • GET  /api/metrics/tools - All tool metrics")
        print("  • GET  /api/metrics/tools/<name> - Specific tool metrics")
        print("  • GET  /api/metrics/top-tools - Top tools by usage")
        print("  • GET  /api/metrics/slowest-tools - Slowest tools")
        print("  • GET  /api/metrics/error-prone-tools - Error-prone tools")
        print("  • GET  /api/metrics/report - Comprehensive report")
        print("  • GET  /api/metrics/export - Export metrics")
        print("  • POST /api/metrics/reset - Reset metrics")
        self.app.run(host=host, port=port, debug=debug)


def create_metrics_api() -> MetricsAPI:
    """Create a new metrics API instance."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for metrics API")
    return MetricsAPI()


def run_metrics_api(host: str = "127.0.0.1", port: int = 5001, debug: bool = False):
    """Run the metrics API server."""
    api = create_metrics_api()
    api.run(host=host, port=port, debug=debug)
