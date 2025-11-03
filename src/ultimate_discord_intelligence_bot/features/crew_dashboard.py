"""Crew comparison dashboard for visualizing performance metrics.

This module provides a dashboard for comparing crew implementations,
generating charts, and exporting results to documentation.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.features.crew_analytics import CrewAnalytics
logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Metrics for dashboard visualization."""

    crew_type: str
    success_rate: float
    avg_execution_time: float
    avg_memory_usage: float
    avg_cpu_usage: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    performance_score: float
    last_execution: float | None = None


@dataclass
class ComparisonChart:
    """Chart data for crew comparison."""

    chart_type: str
    title: str
    data: dict[str, Any]
    labels: list[str]
    values: list[float]
    colors: list[str] = field(default_factory=lambda: ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"])


@dataclass
class DashboardData:
    """Complete dashboard data structure."""

    timestamp: str
    metrics: list[DashboardMetrics]
    charts: list[ComparisonChart]
    summary: dict[str, Any]
    recommendations: list[str]


class CrewDashboard:
    """Dashboard for crew performance comparison and visualization."""

    def __init__(self, analytics: CrewAnalytics):
        """Initialize crew dashboard.

        Args:
            analytics: Crew analytics instance for data collection
        """
        self.analytics = analytics

    def get_dashboard_data(self) -> StepResult:
        """Get comprehensive dashboard data.

        Returns:
            StepResult: Result containing dashboard data
        """
        try:
            analytics_result = self.analytics.get_dashboard_data()
            if not analytics_result.success:
                return StepResult.fail("Failed to get analytics data")
            analytics_data = analytics_result.data
            metrics = []
            for crew_type, crew_data in analytics_data["crews"].items():
                metrics.append(
                    DashboardMetrics(
                        crew_type=crew_type,
                        success_rate=crew_data["success_rate"],
                        avg_execution_time=crew_data["average_execution_time"],
                        avg_memory_usage=crew_data["average_memory_usage"],
                        avg_cpu_usage=crew_data.get("average_cpu_usage", 0.0),
                        total_executions=crew_data.get("total_executions", 0),
                        successful_executions=int(crew_data["success_rate"] * crew_data.get("total_executions", 0)),
                        failed_executions=int((1 - crew_data["success_rate"]) * crew_data.get("total_executions", 0)),
                        performance_score=crew_data["performance_score"],
                        last_execution=crew_data.get("last_execution"),
                    )
                )
            charts = self._generate_charts(metrics)
            summary = self._generate_summary(metrics)
            recommendations = self._generate_recommendations(metrics)
            dashboard_data = DashboardData(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                metrics=metrics,
                charts=charts,
                summary=summary,
                recommendations=recommendations,
            )
            return StepResult.ok(
                data={
                    "dashboard_data": dashboard_data,
                    "metrics_count": len(metrics),
                    "charts_count": len(charts),
                    "recommendations_count": len(recommendations),
                }
            )
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return StepResult.fail(f"Dashboard data retrieval failed: {e}")

    def _generate_charts(self, metrics: list[DashboardMetrics]) -> list[ComparisonChart]:
        """Generate comparison charts.

        Args:
            metrics: List of crew metrics

        Returns:
            List of comparison charts
        """
        charts: list[ComparisonChart] = []
        if not metrics:
            return charts
        success_chart = ComparisonChart(
            chart_type="bar",
            title="Success Rate Comparison",
            data={
                "type": "bar",
                "data": {
                    "labels": [m.crew_type for m in metrics],
                    "datasets": [
                        {
                            "label": "Success Rate (%)",
                            "data": [m.success_rate * 100 for m in metrics],
                            "backgroundColor": ["#2ecc71" if m.success_rate > 0.8 else "#e74c3c" for m in metrics],
                            "borderColor": ["#27ae60" if m.success_rate > 0.8 else "#c0392b" for m in metrics],
                            "borderWidth": 1,
                        }
                    ],
                },
                "options": {"scales": {"y": {"beginAtZero": True, "max": 100}}},
            },
            labels=[m.crew_type for m in metrics],
            values=[m.success_rate * 100 for m in metrics],
        )
        charts.append(success_chart)
        time_chart = ComparisonChart(
            chart_type="bar",
            title="Average Execution Time",
            data={
                "type": "bar",
                "data": {
                    "labels": [m.crew_type for m in metrics],
                    "datasets": [
                        {
                            "label": "Execution Time (seconds)",
                            "data": [m.avg_execution_time for m in metrics],
                            "backgroundColor": ["#3498db" for _ in metrics],
                            "borderColor": ["#2980b9" for _ in metrics],
                            "borderWidth": 1,
                        }
                    ],
                },
                "options": {"scales": {"y": {"beginAtZero": True}}},
            },
            labels=[m.crew_type for m in metrics],
            values=[m.avg_execution_time for m in metrics],
        )
        charts.append(time_chart)
        memory_chart = ComparisonChart(
            chart_type="bar",
            title="Average Memory Usage",
            data={
                "type": "bar",
                "data": {
                    "labels": [m.crew_type for m in metrics],
                    "datasets": [
                        {
                            "label": "Memory Usage (MB)",
                            "data": [m.avg_memory_usage for m in metrics],
                            "backgroundColor": ["#f39c12" for _ in metrics],
                            "borderColor": ["#e67e22" for _ in metrics],
                            "borderWidth": 1,
                        }
                    ],
                },
                "options": {"scales": {"y": {"beginAtZero": True}}},
            },
            labels=[m.crew_type for m in metrics],
            values=[m.avg_memory_usage for m in metrics],
        )
        charts.append(memory_chart)
        performance_chart = ComparisonChart(
            chart_type="radar",
            title="Performance Score Comparison",
            data={
                "type": "radar",
                "data": {
                    "labels": ["Success Rate", "Speed", "Memory Efficiency", "Reliability"],
                    "datasets": [
                        {
                            "label": m.crew_type,
                            "data": [
                                m.success_rate * 100,
                                max(0, 100 - m.avg_execution_time / 10),
                                max(0, 100 - m.avg_memory_usage / 10),
                                m.performance_score * 100,
                            ],
                            "backgroundColor": f"rgba({i * 50}, {100 + i * 30}, {200 - i * 40}, 0.2)",
                            "borderColor": f"rgba({i * 50}, {100 + i * 30}, {200 - i * 40}, 1)",
                            "borderWidth": 2,
                        }
                        for i, m in enumerate(metrics)
                    ],
                },
                "options": {"scales": {"r": {"beginAtZero": True, "max": 100}}},
            },
            labels=[m.crew_type for m in metrics],
            values=[m.performance_score for m in metrics],
        )
        charts.append(performance_chart)
        return charts

    def _generate_summary(self, metrics: list[DashboardMetrics]) -> dict[str, Any]:
        """Generate summary statistics.

        Args:
            metrics: List of crew metrics

        Returns:
            Summary statistics
        """
        if not metrics:
            return {}
        best_success = max(metrics, key=lambda m: m.success_rate)
        fastest = min(metrics, key=lambda m: m.avg_execution_time)
        most_efficient = min(metrics, key=lambda m: m.avg_memory_usage)
        best_performance = max(metrics, key=lambda m: m.performance_score)
        total_executions = sum(m.total_executions for m in metrics)
        total_successful = sum(m.successful_executions for m in metrics)
        overall_success_rate = total_successful / total_executions if total_executions > 0 else 0
        return {
            "total_crews": len(metrics),
            "total_executions": total_executions,
            "total_successful": total_successful,
            "overall_success_rate": overall_success_rate,
            "best_success_rate": {"crew": best_success.crew_type, "rate": best_success.success_rate},
            "fastest_execution": {"crew": fastest.crew_type, "time": fastest.avg_execution_time},
            "most_memory_efficient": {"crew": most_efficient.crew_type, "usage": most_efficient.avg_memory_usage},
            "best_overall_performance": {
                "crew": best_performance.crew_type,
                "score": best_performance.performance_score,
            },
        }

    def _generate_recommendations(self, metrics: list[DashboardMetrics]) -> list[str]:
        """Generate recommendations based on metrics.

        Args:
            metrics: List of crew metrics

        Returns:
            List of recommendations
        """
        recommendations = []
        if not metrics:
            return ["No metrics available for recommendations"]
        best_performer = max(metrics, key=lambda m: m.performance_score)
        recommendations.append(
            f"🏆 Recommended for production: {best_performer.crew_type} (performance score: {best_performer.performance_score:.2f})"
        )
        for metric in metrics:
            if metric.success_rate < 0.8:
                recommendations.append(
                    f"⚠️ {metric.crew_type}: Low success rate ({metric.success_rate:.1%}) - investigate stability issues"
                )
            if metric.avg_execution_time > 60.0:
                recommendations.append(
                    f"⚠️ {metric.crew_type}: Slow execution ({metric.avg_execution_time:.1f}s) - consider optimization"
                )
            if metric.avg_memory_usage > 500.0:
                recommendations.append(
                    f"⚠️ {metric.crew_type}: High memory usage ({metric.avg_memory_usage:.1f}MB) - consider memory optimization"
                )
        if len(metrics) > 1:
            fastest = min(metrics, key=lambda m: m.avg_execution_time)
            most_efficient = min(metrics, key=lambda m: m.avg_memory_usage)
            if fastest.crew_type != best_performer.crew_type:
                recommendations.append(
                    f"⚡ For speed-critical workloads: {fastest.crew_type} (avg: {fastest.avg_execution_time:.1f}s)"
                )
            if most_efficient.crew_type != best_performer.crew_type:
                recommendations.append(
                    f"💾 For memory-constrained environments: {most_efficient.crew_type} (avg: {most_efficient.avg_memory_usage:.1f}MB)"
                )
        return recommendations

    def export_to_markdown(
        self, dashboard_data: DashboardData, filename: str = "crew_comparison_report.md"
    ) -> StepResult:
        """Export dashboard data to markdown report.

        Args:
            dashboard_data: Dashboard data to export
            filename: Output filename

        Returns:
            StepResult: Result of export operation
        """
        try:
            with open(filename, "w") as f:
                f.write("# Crew Performance Comparison Report\n\n")
                f.write(f"**Generated:** {dashboard_data.timestamp}\n\n")
                f.write("## Summary\n\n")
                summary = dashboard_data.summary
                f.write(f"- **Total Crews Tested:** {summary.get('total_crews', 0)}\n")
                f.write(f"- **Total Executions:** {summary.get('total_executions', 0)}\n")
                f.write(f"- **Overall Success Rate:** {summary.get('overall_success_rate', 0):.1%}\n")
                f.write(f"- **Best Performer:** {summary.get('best_overall_performance', {}).get('crew', 'N/A')}\n\n")
                f.write("## Performance Metrics\n\n")
                f.write("| Crew Type | Success Rate | Avg Time (s) | Avg Memory (MB) | Performance Score |\n")
                f.write("|-----------|--------------|--------------|-----------------|-------------------|\n")
                for metric in dashboard_data.metrics:
                    f.write(
                        f"| {metric.crew_type} | {metric.success_rate:.1%} | {metric.avg_execution_time:.2f} | {metric.avg_memory_usage:.1f} | {metric.performance_score:.2f} |\n"
                    )
                f.write("\n")
                f.write("## Recommendations\n\n")
                for i, recommendation in enumerate(dashboard_data.recommendations, 1):
                    f.write(f"{i}. {recommendation}\n")
                f.write("\n")
                f.write("## Performance Charts\n\n")
                f.write("The following charts provide visual comparisons of crew performance:\n\n")
                for chart in dashboard_data.charts:
                    f.write(f"### {chart.title}\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(chart.data, indent=2))
                    f.write("\n```\n\n")
                f.write("---\n")
                f.write("*Report generated by Crew Dashboard*\n")
            return StepResult.ok(data={"filename": filename, "size": len(dashboard_data.metrics)})
        except Exception as e:
            logger.error(f"Failed to export markdown report: {e}")
            return StepResult.fail(f"Markdown export failed: {e}")

    def export_to_json(self, dashboard_data: DashboardData, filename: str = "crew_comparison_data.json") -> StepResult:
        """Export dashboard data to JSON file.

        Args:
            dashboard_data: Dashboard data to export
            filename: Output filename

        Returns:
            StepResult: Result of export operation
        """
        try:
            export_data = {
                "timestamp": dashboard_data.timestamp,
                "metrics": [
                    {
                        "crew_type": m.crew_type,
                        "success_rate": m.success_rate,
                        "avg_execution_time": m.avg_execution_time,
                        "avg_memory_usage": m.avg_memory_usage,
                        "avg_cpu_usage": m.avg_cpu_usage,
                        "total_executions": m.total_executions,
                        "successful_executions": m.successful_executions,
                        "failed_executions": m.failed_executions,
                        "performance_score": m.performance_score,
                        "last_execution": m.last_execution,
                    }
                    for m in dashboard_data.metrics
                ],
                "charts": [
                    {
                        "chart_type": c.chart_type,
                        "title": c.title,
                        "data": c.data,
                        "labels": c.labels,
                        "values": c.values,
                        "colors": c.colors,
                    }
                    for c in dashboard_data.charts
                ],
                "summary": dashboard_data.summary,
                "recommendations": dashboard_data.recommendations,
            }
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            return StepResult.ok(data={"filename": filename, "metrics_count": len(dashboard_data.metrics)})
        except Exception as e:
            logger.error(f"Failed to export JSON data: {e}")
            return StepResult.fail(f"JSON export failed: {e}")

    def generate_html_dashboard(
        self, dashboard_data: DashboardData, filename: str = "crew_dashboard.html"
    ) -> StepResult:
        """Generate HTML dashboard.

        Args:
            dashboard_data: Dashboard data to visualize
            filename: Output filename

        Returns:
            StepResult: Result of HTML generation
        """
        try:
            html_content = f'\n<!DOCTYPE html>\n<html>\n<head>\n    <title>Crew Performance Dashboard</title>\n    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n    <style>\n        body {{ font-family: Arial, sans-serif; margin: 20px; }}\n        .header {{ text-align: center; margin-bottom: 30px; }}\n        .metrics-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}\n        .metrics-table th, .metrics-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}\n        .metrics-table th {{ background-color: #f2f2f2; }}\n        .chart-container {{ margin: 20px 0; }}\n        .recommendations {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}\n    </style>\n</head>\n<body>\n    <div class="header">\n        <h1>Crew Performance Dashboard</h1>\n        <p>Generated: {dashboard_data.timestamp}</p>\n    </div>\n\n    <h2>Performance Metrics</h2>\n    <table class="metrics-table">\n        <tr>\n            <th>Crew Type</th>\n            <th>Success Rate</th>\n            <th>Avg Time (s)</th>\n            <th>Avg Memory (MB)</th>\n            <th>Performance Score</th>\n        </tr>\n'
            for metric in dashboard_data.metrics:
                html_content += f"\n        <tr>\n            <td>{metric.crew_type}</td>\n            <td>{metric.success_rate:.1%}</td>\n            <td>{metric.avg_execution_time:.2f}</td>\n            <td>{metric.avg_memory_usage:.1f}</td>\n            <td>{metric.performance_score:.2f}</td>\n        </tr>\n"
            html_content += "\n    </table>\n\n    <h2>Performance Charts</h2>\n"
            for i, chart in enumerate(dashboard_data.charts):
                html_content += f'\n    <div class="chart-container">\n        <h3>{chart.title}</h3>\n        <canvas id="chart{i}" width="400" height="200"></canvas>\n    </div>\n'
            html_content += '\n    <h2>Recommendations</h2>\n    <div class="recommendations">\n        <ul>\n'
            for recommendation in dashboard_data.recommendations:
                html_content += f"            <li>{recommendation}</li>\n"
            html_content += "\n        </ul>\n    </div>\n\n    <script>\n"
            for i, chart in enumerate(dashboard_data.charts):
                html_content += f"\n        // Chart {i}: {chart.title}\n        const ctx{i} = document.getElementById('chart{i}').getContext('2d');\n        new Chart(ctx{i}, {json.dumps(chart.data)});\n"
            html_content += "\n    </script>\n</body>\n</html>\n"
            with open(filename, "w") as f:
                f.write(html_content)
            return StepResult.ok(data={"filename": filename, "charts_count": len(dashboard_data.charts)})
        except Exception as e:
            logger.error(f"Failed to generate HTML dashboard: {e}")
            return StepResult.fail(f"HTML dashboard generation failed: {e}")
