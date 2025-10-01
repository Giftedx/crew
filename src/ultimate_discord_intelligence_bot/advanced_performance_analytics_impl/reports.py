from __future__ import annotations

from typing import Any


def format_markdown_report(analysis: dict[str, Any]) -> str:
    report = f"""# Advanced Performance Analytics Report

**Generated**: {analysis.get("analysis_timestamp")}
**Analysis Period**: {analysis.get("lookback_hours")} hours

## 🏥 System Health

**Overall Score**: {analysis.get("system_health", {}).get("overall_score", 0):.2f}
**Status**: {analysis.get("system_health", {}).get("status", "unknown").title()}

### Key Indicators
"""

    key_indicators = analysis.get("system_health", {}).get("key_indicators", {})
    for indicator, value in key_indicators.items():
        report += f"- **{indicator.replace('_', ' ').title()}**: {value}\n"

    report += "\n## 📈 Performance Trends\n\n"
    trends = analysis.get("performance_trends", [])
    for trend in trends[:5]:
        direction_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(
            trend.get("trend_direction", "stable"), "➡️"
        )
        report += (
            f"- {direction_emoji} **{trend.get('metric_name')}**: {trend.get('trend_direction')} "
            f"({trend.get('change_rate', 0):.1f}% change)\n"
        )

    report += "\n## 🚨 Critical Recommendations\n\n"
    critical_recs = analysis.get("optimization_recommendations", {}).get("critical", [])
    for rec in critical_recs:
        report += f"### {rec.title}\n"
        report += f"**Category**: {rec.category.title()}\n"
        report += f"**Expected Impact**: {rec.expected_impact}\n"
        report += f"**Effort**: {rec.implementation_effort.title()}\n\n"

    report += "\n## 💡 Actionable Insights\n\n"
    insights = analysis.get("actionable_insights", [])
    for insight in insights:
        report += f"- {insight}\n"

    return report


def format_html_report(analysis: dict[str, Any]) -> str:
    health_score = analysis.get("system_health", {}).get("overall_score", 0)
    health_color = "green" if health_score > 0.8 else "orange" if health_score > 0.6 else "red"
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Performance Analytics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .health-score {{ color: {health_color}; font-size: 24px; font-weight: bold; }}
        .metric {{ background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .recommendation {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
        .insight {{ background: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; }}
    </style>
</head>
<body>
    <h1>🔬 Advanced Performance Analytics Report</h1>
    <p><strong>Generated:</strong> {analysis.get("analysis_timestamp")}</p>

    <h2>🏥 System Health</h2>
    <div class="health-score">Score: {health_score:.2f}</div>
    <p><strong>Status:</strong> {analysis.get("system_health", {}).get("status", "unknown").title()}</p>

    <h2>📊 Key Metrics</h2>
    <div class="metric">
        <strong>Performance Trends:</strong> {len(analysis.get("performance_trends", []))} analyzed<br>
        <strong>Anomalies Detected:</strong> {analysis.get("anomalies", {}).get("detected", 0)}<br>
        <strong>Optimization Recommendations:</strong> {
        analysis.get("optimization_recommendations", {}).get("total_recommendations", 0)
    }
    </div>

    <h2>🎯 Top Recommendations</h2>
    {
        "".join(
            f'<div class="recommendation"><strong>{rec.title}</strong><br>{rec.description}</div>'
            for rec in analysis.get("optimization_recommendations", {}).get("critical", [])[:3]
        )
    }

    <h2>💡 Key Insights</h2>
    {"".join(f'<div class="insight">{insight}</div>' for insight in analysis.get("actionable_insights", []))}
</body>
</html>
        """
