"""Enhanced Metrics API with Web Dashboard Support.

This module provides an enhanced metrics API with web dashboard capabilities,
including HTML templates, real-time updates, and interactive charts.
"""

from __future__ import annotations

from datetime import datetime, timezone


try:
    from flask import Flask, jsonify, render_template_string, request  # type: ignore

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not available - enhanced metrics API will not be available")

from ultimate_discord_intelligence_bot.observability.dashboard_templates import get_base_template, get_simple_dashboard


class EnhancedMetricsAPI:
    """Enhanced metrics API with web dashboard support."""

    def __init__(self, app: Flask | None = None):
        """Initialize the enhanced metrics API."""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for enhanced metrics API")

        self.app = app or Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Setup enhanced API routes with dashboard support."""

        @self.app.route("/")
        def dashboard():
            """Main dashboard page."""
            return render_template_string(get_base_template())

        @self.app.route("/simple")
        def simple_dashboard():
            """Simple dashboard page."""
            return render_template_string(get_simple_dashboard())

        @self.app.route("/api/metrics/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "enhanced-metrics-api",
                    "version": "1.0.0",
                }
            )

        @self.app.route("/api/metrics/system")
        def get_system_metrics():
            """Get system-wide metrics."""
            try:
                from ultimate_discord_intelligence_bot.observability.metrics_collector import get_system_metrics

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
                            "health_score": self._calculate_health_score(),
                        },
                    }
                )
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/metrics/tools")
        def get_all_tool_metrics():
            """Get metrics for all tools."""
            try:
                from ultimate_discord_intelligence_bot.observability.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                metrics = collector.get_all_tool_metrics()

                # Add health status to each tool
                enhanced_metrics = {}
                for name, tool_metrics in metrics.items():
                    enhanced_metrics[name] = {
                        **tool_metrics.__dict__,
                        "health_status": self._get_tool_health_status(tool_metrics),
                        "performance_tier": self._get_performance_tier(tool_metrics),
                    }

                return jsonify({"status": "success", "data": {"tool_count": len(metrics), "tools": enhanced_metrics}})
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/metrics/tools/<tool_name>")
        def get_tool_metrics(tool_name: str):
            """Get metrics for a specific tool."""
            try:
                from ultimate_discord_intelligence_bot.observability.metrics_collector import get_tool_metrics

                metrics = get_tool_metrics(tool_name)

                if not metrics:
                    return jsonify({"status": "error", "error": f"Tool '{tool_name}' not found"}), 404

                return jsonify(
                    {
                        "status": "success",
                        "data": {
                            **metrics.__dict__,
                            "health_status": self._get_tool_health_status(metrics),
                            "performance_tier": self._get_performance_tier(metrics),
                            "recommendations": self._get_tool_recommendations(metrics),
                        },
                    }
                )
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/metrics/analytics")
        def get_analytics():
            """Get advanced analytics and insights."""
            try:
                from ultimate_discord_intelligence_bot.observability.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                all_metrics = collector.get_all_tool_metrics()

                analytics = {
                    "performance_insights": self._analyze_performance(all_metrics),
                    "trend_analysis": self._analyze_trends(all_metrics),
                    "bottleneck_analysis": self._analyze_bottlenecks(all_metrics),
                    "optimization_recommendations": self._get_optimization_recommendations(all_metrics),
                }

                return jsonify({"status": "success", "data": analytics})
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        @self.app.route("/api/metrics/export")
        def export_metrics():
            """Export metrics with enhanced formatting."""
            try:
                from ultimate_discord_intelligence_bot.observability.metrics_collector import get_metrics_collector

                collector = get_metrics_collector()
                export_file = f"enhanced_metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                if collector.export_metrics(export_file):
                    return jsonify(
                        {
                            "status": "success",
                            "message": f"Enhanced metrics exported to {export_file}",
                            "export_file": export_file,
                            "export_timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                else:
                    return jsonify({"status": "error", "error": "Failed to export metrics"}), 500

            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score."""
        try:
            from ultimate_discord_intelligence_bot.observability.metrics_collector import get_metrics_collector

            collector = get_metrics_collector()
            all_metrics = collector.get_all_tool_metrics()

            if not all_metrics:
                return 0.0

            # Calculate health score based on success rates and performance
            total_score = 0
            tool_count = 0

            for tool_metrics in all_metrics.values():
                if tool_metrics.total_calls > 0:
                    # Success rate weight: 70%
                    success_score = tool_metrics.success_rate * 0.7

                    # Performance weight: 30% (inverse of execution time)
                    # Normalize execution time (lower is better)
                    max_expected_time = 5.0  # 5 seconds max expected
                    performance_score = (
                        max(0, (max_expected_time - tool_metrics.average_execution_time) / max_expected_time) * 0.3
                    )

                    tool_score = success_score + performance_score
                    total_score += tool_score
                    tool_count += 1

            return float(total_score / tool_count * 100) if tool_count > 0 else 0.0

        except Exception:
            return 0.0

    def _get_tool_health_status(self, tool_metrics) -> str:
        """Get health status for a specific tool."""
        if tool_metrics.total_calls == 0:
            return "inactive"
        elif tool_metrics.success_rate >= 0.9:
            return "excellent"
        elif tool_metrics.success_rate >= 0.8:
            return "good"
        elif tool_metrics.success_rate >= 0.6:
            return "fair"
        else:
            return "poor"

    def _get_performance_tier(self, tool_metrics) -> str:
        """Get performance tier for a tool."""
        if tool_metrics.total_calls == 0:
            return "unused"
        elif tool_metrics.average_execution_time <= 0.5:
            return "fast"
        elif tool_metrics.average_execution_time <= 2.0:
            return "normal"
        elif tool_metrics.average_execution_time <= 5.0:
            return "slow"
        else:
            return "very_slow"

    def _get_tool_recommendations(self, tool_metrics) -> list[str]:
        """Get recommendations for a specific tool."""
        recommendations = []

        if tool_metrics.total_calls == 0:
            recommendations.append("Tool is unused - consider removing or investigating usage patterns")
        elif tool_metrics.success_rate < 0.8:
            recommendations.append("Low success rate - investigate error patterns and improve error handling")
        elif tool_metrics.average_execution_time > 5.0:
            recommendations.append("High execution time - consider optimization or caching")
        elif tool_metrics.failed_calls > tool_metrics.successful_calls:
            recommendations.append("More failures than successes - critical issue requiring immediate attention")
        else:
            recommendations.append("Tool is performing well")

        return recommendations

    def _analyze_performance(self, all_metrics) -> dict:
        """Analyze overall performance patterns."""
        if not all_metrics:
            return {"message": "No metrics available for analysis"}

        total_calls = sum(tool.total_calls for tool in all_metrics.values())
        avg_success_rate = sum(tool.success_rate for tool in all_metrics.values()) / len(all_metrics)
        avg_execution_time = sum(tool.average_execution_time for tool in all_metrics.values()) / len(all_metrics)

        return {
            "total_calls": total_calls,
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time,
            "performance_trend": "stable" if avg_success_rate > 0.8 else "declining",
        }

    def _analyze_trends(self, all_metrics) -> dict:
        """Analyze performance trends."""
        # This is a simplified trend analysis
        # In a real implementation, you'd analyze historical data
        return {
            "trend_period": "last_24_hours",
            "call_volume_trend": "stable",
            "performance_trend": "stable",
            "error_rate_trend": "stable",
        }

    def _analyze_bottlenecks(self, all_metrics) -> dict:
        """Analyze system bottlenecks."""
        bottlenecks = []

        for tool_metrics in all_metrics.values():
            if tool_metrics.average_execution_time > 3.0:
                bottlenecks.append(
                    {
                        "tool": tool_metrics.tool_name,
                        "issue": "high_execution_time",
                        "value": tool_metrics.average_execution_time,
                        "impact": "high" if tool_metrics.average_execution_time > 5.0 else "medium",
                    }
                )
            elif tool_metrics.success_rate < 0.7:
                bottlenecks.append(
                    {
                        "tool": tool_metrics.tool_name,
                        "issue": "low_success_rate",
                        "value": tool_metrics.success_rate,
                        "impact": "high" if tool_metrics.success_rate < 0.5 else "medium",
                    }
                )

        return {
            "bottlenecks": bottlenecks,
            "critical_issues": len([b for b in bottlenecks if b["impact"] == "high"]),
            "total_issues": len(bottlenecks),
        }

    def _get_optimization_recommendations(self, all_metrics) -> list[str]:
        """Get system-wide optimization recommendations."""
        recommendations = []

        # Analyze patterns and provide recommendations
        slow_tools = [tool for tool in all_metrics.values() if tool.average_execution_time > 3.0]
        error_prone_tools = [tool for tool in all_metrics.values() if tool.success_rate < 0.8]

        if slow_tools:
            recommendations.append(f"Consider optimizing {len(slow_tools)} slow tools for better performance")

        if error_prone_tools:
            recommendations.append(f"Investigate {len(error_prone_tools)} tools with low success rates")

        if not slow_tools and not error_prone_tools:
            recommendations.append("System is performing well - consider monitoring for capacity planning")

        return recommendations

    def run(self, host: str = "127.0.0.1", port: int = 5002, debug: bool = False):
        """Run the enhanced metrics API server."""
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required to run the enhanced metrics API")

        print(f"🚀 Starting Enhanced Metrics API on http://{host}:{port}")
        print("📊 Available endpoints:")
        print("  • GET  / - Main dashboard")
        print("  • GET  /simple - Simple dashboard")
        print("  • GET  /api/metrics/health - Health check")
        print("  • GET  /api/metrics/system - System metrics")
        print("  • GET  /api/metrics/tools - All tool metrics")
        print("  • GET  /api/metrics/tools/<name> - Specific tool metrics")
        print("  • GET  /api/metrics/analytics - Advanced analytics")
        print("  • GET  /api/metrics/export - Export metrics")

        self.app.run(host=host, port=port, debug=debug)


def create_enhanced_metrics_api() -> EnhancedMetricsAPI:
    """Create a new enhanced metrics API instance."""
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for enhanced metrics API")
    return EnhancedMetricsAPI()


def run_enhanced_metrics_api(host: str = "127.0.0.1", port: int = 5002, debug: bool = False):
    """Run the enhanced metrics API server."""
    api = create_enhanced_metrics_api()
    api.run(host=host, port=port, debug=debug)
