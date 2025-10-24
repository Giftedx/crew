"""Bias evaluation dashboard with visualization and reporting.

This module provides comprehensive bias reporting including real-time bias detection,
historical bias trend tracking, comparative bias analysis, bias mitigation recommendations,
and transparency reports for users.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.analysis.bias_metrics import BiasAnalyzer, BiasMetrics
from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class BiasTrend:
    """Historical bias trend data."""

    timestamp: float
    bias_score: float
    political_leaning: float
    partisan_intensity: float
    viewpoint_diversity: float
    source: str
    content_type: str


@dataclass
class ComparativeAnalysis:
    """Comparative bias analysis across sources/topics."""

    source_a: str
    source_b: str
    bias_difference: float
    similarity_score: float
    key_differences: list[str]
    recommendations: list[str]


@dataclass
class BiasMitigation:
    """Bias mitigation recommendations."""

    content_id: str
    original_bias_score: float
    mitigation_strategies: list[str]
    expected_improvement: float
    implementation_effort: str  # "low", "medium", "high"


class BiasDashboard:
    """Dashboard for bias evaluation and reporting.

    Provides comprehensive bias analysis including real-time detection,
    historical tracking, comparative analysis, and mitigation recommendations.
    """

    def __init__(self) -> None:
        """Initialize the bias dashboard."""
        self.logger = logging.getLogger(__name__)
        self.analyzer = BiasAnalyzer()
        self.bias_history: list[BiasTrend] = []
        self.comparative_analyses: list[ComparativeAnalysis] = []
        self.mitigation_recommendations: list[BiasMitigation] = []

    def analyze_content_bias(self, content: str, source: str = "unknown", content_type: str = "text") -> StepResult:
        """Analyze bias in content and track trends.

        Args:
            content: The content to analyze
            source: Source identifier
            content_type: Type of content (text, video, audio, etc.)

        Returns:
            StepResult with bias analysis and trend data
        """
        try:
            # Analyze bias metrics
            analysis_result = self.analyzer.analyze_bias(content)
            if not analysis_result.success:
                return analysis_result

            metrics = analysis_result.data["bias_metrics"]

            # Create trend data point
            trend = BiasTrend(
                timestamp=time.time(),
                bias_score=metrics.overall_bias_score,
                political_leaning=metrics.political_leaning,
                partisan_intensity=metrics.partisan_intensity,
                viewpoint_diversity=metrics.viewpoint_diversity,
                source=source,
                content_type=content_type,
            )

            # Store in history
            self.bias_history.append(trend)

            # Generate mitigation recommendations if bias is high
            if metrics.overall_bias_score > 0.6:
                mitigation = self._generate_mitigation_recommendations(content, metrics, source)
                self.mitigation_recommendations.append(mitigation)

            return StepResult.ok(
                data={
                    "bias_analysis": analysis_result.data,
                    "trend_data": trend,
                    "historical_context": self._get_historical_context(source),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Content bias analysis failed: {e}")
            return StepResult.fail(f"Content bias analysis failed: {e}")

    def _get_historical_context(self, source: str) -> dict[str, Any]:
        """Get historical context for a source."""
        source_history = [trend for trend in self.bias_history if trend.source == source]

        if not source_history:
            return {"message": "No historical data available"}

        # Calculate trends
        recent_trends = source_history[-10:] if len(source_history) >= 10 else source_history
        avg_bias = sum(trend.bias_score for trend in recent_trends) / len(recent_trends)
        avg_leaning = sum(trend.political_leaning for trend in recent_trends) / len(recent_trends)

        return {
            "total_analyses": len(source_history),
            "average_bias_score": avg_bias,
            "average_political_leaning": avg_leaning,
            "trend_direction": self._calculate_trend_direction(recent_trends),
            "recent_analyses": len(recent_trends),
        }

    def _calculate_trend_direction(self, trends: list[BiasTrend]) -> str:
        """Calculate the direction of bias trends."""
        if len(trends) < 2:
            return "insufficient_data"

        recent_scores = [trend.bias_score for trend in trends[-5:]]
        if len(recent_scores) < 2:
            return "insufficient_data"

        # Simple trend calculation
        first_half = recent_scores[: len(recent_scores) // 2]
        second_half = recent_scores[len(recent_scores) // 2 :]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg + 0.1:
            return "increasing"
        elif second_avg < first_avg - 0.1:
            return "decreasing"
        else:
            return "stable"

    def _generate_mitigation_recommendations(self, content: str, metrics: BiasMetrics, source: str) -> BiasMitigation:
        """Generate bias mitigation recommendations."""
        strategies = []

        if metrics.partisan_intensity > 0.7:
            strategies.append("Reduce partisan language and emotional appeals")

        if metrics.viewpoint_diversity < 0.3:
            strategies.append("Include more diverse perspectives and viewpoints")

        if metrics.evidence_balance < 0.4:
            strategies.append("Present more balanced evidence from multiple sides")

        if metrics.framing_neutrality < 0.5:
            strategies.append("Use more neutral language and avoid loaded terms")

        if metrics.source_diversity < 0.3:
            strategies.append("Include sources from a wider range of perspectives")

        # Calculate expected improvement
        expected_improvement = min(0.3, metrics.overall_bias_score * 0.5)

        # Determine implementation effort
        if len(strategies) <= 2:
            effort = "low"
        elif len(strategies) <= 4:
            effort = "medium"
        else:
            effort = "high"

        return BiasMitigation(
            content_id=f"{source}_{int(time.time())}",
            original_bias_score=metrics.overall_bias_score,
            mitigation_strategies=strategies,
            expected_improvement=expected_improvement,
            implementation_effort=effort,
        )

    def compare_sources(self, source_a: str, source_b: str) -> StepResult:
        """Compare bias between two sources.

        Args:
            source_a: First source identifier
            source_b: Second source identifier

        Returns:
            StepResult with comparative analysis
        """
        try:
            # Get historical data for both sources
            history_a = [trend for trend in self.bias_history if trend.source == source_a]
            history_b = [trend for trend in self.bias_history if trend.source == source_b]

            if not history_a or not history_b:
                return StepResult.fail("Insufficient historical data for comparison")

            # Calculate average metrics
            avg_bias_a = sum(trend.bias_score for trend in history_a) / len(history_a)
            avg_bias_b = sum(trend.bias_score for trend in history_b) / len(history_b)

            avg_leaning_a = sum(trend.political_leaning for trend in history_a) / len(history_a)
            avg_leaning_b = sum(trend.political_leaning for trend in history_b) / len(history_b)

            # Calculate differences
            bias_difference = abs(avg_bias_a - avg_bias_b)
            leaning_difference = abs(avg_leaning_a - avg_leaning_b)

            # Calculate similarity score
            similarity_score = 1.0 - (bias_difference + leaning_difference) / 2.0

            # Identify key differences
            key_differences = []
            if bias_difference > 0.3:
                key_differences.append(
                    f"Significant bias difference: {source_a} ({avg_bias_a:.2f}) vs {source_b} ({avg_bias_b:.2f})"
                )

            if leaning_difference > 0.5:
                key_differences.append(
                    f"Different political leanings: {source_a} ({avg_leaning_a:.2f}) vs {source_b} ({avg_leaning_b:.2f})"
                )

            # Generate recommendations
            recommendations = []
            if bias_difference > 0.4:
                recommendations.append("Consider balancing content between sources")

            if leaning_difference > 0.6:
                recommendations.append("Include more diverse political perspectives")

            if similarity_score < 0.3:
                recommendations.append("Sources show very different bias patterns")

            # Create comparative analysis
            analysis = ComparativeAnalysis(
                source_a=source_a,
                source_b=source_b,
                bias_difference=bias_difference,
                similarity_score=similarity_score,
                key_differences=key_differences,
                recommendations=recommendations,
            )

            # Store for future reference
            self.comparative_analyses.append(analysis)

            return StepResult.ok(
                data={
                    "comparative_analysis": analysis,
                    "source_a_metrics": {
                        "average_bias": avg_bias_a,
                        "average_leaning": avg_leaning_a,
                        "analysis_count": len(history_a),
                    },
                    "source_b_metrics": {
                        "average_bias": avg_bias_b,
                        "average_leaning": avg_leaning_b,
                        "analysis_count": len(history_b),
                    },
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Source comparison failed: {e}")
            return StepResult.fail(f"Source comparison failed: {e}")

    def get_bias_trends(self, source: str | None = None, days: int = 30) -> StepResult:
        """Get bias trends for analysis.

        Args:
            source: Optional source filter
            days: Number of days to look back

        Returns:
            StepResult with trend data
        """
        try:
            cutoff_time = time.time() - (days * 24 * 60 * 60)

            # Filter trends
            if source:
                trends = [
                    trend for trend in self.bias_history if trend.source == source and trend.timestamp >= cutoff_time
                ]
            else:
                trends = [trend for trend in self.bias_history if trend.timestamp >= cutoff_time]

            if not trends:
                return StepResult.ok(data={"trends": [], "message": "No trend data available"})

            # Calculate trend statistics
            bias_scores = [trend.bias_score for trend in trends]
            leanings = [trend.political_leaning for trend in trends]

            trend_stats = {
                "total_analyses": len(trends),
                "average_bias": sum(bias_scores) / len(bias_scores),
                "max_bias": max(bias_scores),
                "min_bias": min(bias_scores),
                "average_leaning": sum(leanings) / len(leanings),
                "trend_direction": self._calculate_trend_direction(trends),
                "sources_analyzed": len(set(trend.source for trend in trends)),
            }

            return StepResult.ok(
                data={
                    "trends": [trend.__dict__ for trend in trends],
                    "statistics": trend_stats,
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return StepResult.fail(f"Trend analysis failed: {e}")

    def get_mitigation_recommendations(self, source: str | None = None) -> StepResult:
        """Get bias mitigation recommendations.

        Args:
            source: Optional source filter

        Returns:
            StepResult with mitigation recommendations
        """
        try:
            if source:
                recommendations = [rec for rec in self.mitigation_recommendations if source in rec.content_id]
            else:
                recommendations = self.mitigation_recommendations

            if not recommendations:
                return StepResult.ok(data={"recommendations": [], "message": "No mitigation recommendations available"})

            # Sort by expected improvement
            recommendations.sort(key=lambda x: x.expected_improvement, reverse=True)

            return StepResult.ok(
                data={
                    "recommendations": [rec.__dict__ for rec in recommendations],
                    "total_recommendations": len(recommendations),
                    "analysis_complete": True,
                }
            )

        except Exception as e:
            self.logger.error(f"Mitigation recommendations failed: {e}")
            return StepResult.fail(f"Mitigation recommendations failed: {e}")

    def generate_transparency_report(self, format: str = "json") -> StepResult:
        """Generate transparency report for users.

        Args:
            format: Report format (json, markdown, html)

        Returns:
            StepResult with transparency report
        """
        try:
            # Calculate overall statistics
            total_analyses = len(self.bias_history)
            if total_analyses == 0:
                return StepResult.ok(data={"report": "No data available for transparency report"})

            avg_bias = sum(trend.bias_score for trend in self.bias_history) / total_analyses
            sources_analyzed = len(set(trend.source for trend in self.bias_history))

            # Calculate bias distribution
            low_bias = len([t for t in self.bias_history if t.bias_score < 0.3])
            moderate_bias = len([t for t in self.bias_history if 0.3 <= t.bias_score < 0.6])
            high_bias = len([t for t in self.bias_history if t.bias_score >= 0.6])

            report_data = {
                "report_metadata": {
                    "generated_at": time.time(),
                    "total_analyses": total_analyses,
                    "sources_analyzed": sources_analyzed,
                    "report_period": "all_time",
                },
                "bias_statistics": {
                    "average_bias_score": avg_bias,
                    "bias_distribution": {
                        "low_bias": low_bias,
                        "moderate_bias": moderate_bias,
                        "high_bias": high_bias,
                    },
                    "bias_percentages": {
                        "low_bias_pct": (low_bias / total_analyses) * 100,
                        "moderate_bias_pct": (moderate_bias / total_analyses) * 100,
                        "high_bias_pct": (high_bias / total_analyses) * 100,
                    },
                },
                "mitigation_efforts": {
                    "total_recommendations": len(self.mitigation_recommendations),
                    "comparative_analyses": len(self.comparative_analyses),
                },
                "transparency_commitments": [
                    "All bias analyses are performed using transparent algorithms",
                    "Historical bias data is preserved for audit purposes",
                    "Mitigation recommendations are based on objective metrics",
                    "Comparative analyses help identify bias patterns",
                ],
            }

            if format == "json":
                return StepResult.ok(data={"transparency_report": report_data})
            elif format == "markdown":
                markdown_report = self._generate_markdown_report(report_data)
                return StepResult.ok(data={"transparency_report": markdown_report})
            elif format == "html":
                html_report = self._generate_html_report(report_data)
                return StepResult.ok(data={"transparency_report": html_report})
            else:
                return StepResult.fail(f"Unsupported format: {format}")

        except Exception as e:
            self.logger.error(f"Transparency report generation failed: {e}")
            return StepResult.fail(f"Transparency report generation failed: {e}")

    def _generate_markdown_report(self, report_data: dict[str, Any]) -> str:
        """Generate markdown transparency report."""
        md = f"""# Bias Analysis Transparency Report

## Report Metadata
- Generated: {time.ctime(report_data["report_metadata"]["generated_at"])}
- Total Analyses: {report_data["report_metadata"]["total_analyses"]}
- Sources Analyzed: {report_data["report_metadata"]["sources_analyzed"]}

## Bias Statistics
- Average Bias Score: {report_data["bias_statistics"]["average_bias_score"]:.3f}

### Bias Distribution
- Low Bias (< 0.3): {report_data["bias_statistics"]["bias_distribution"]["low_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["low_bias_pct"]:.1f}%)
- Moderate Bias (0.3-0.6): {report_data["bias_statistics"]["bias_distribution"]["moderate_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["moderate_bias_pct"]:.1f}%)
- High Bias (≥ 0.6): {report_data["bias_statistics"]["bias_distribution"]["high_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["high_bias_pct"]:.1f}%)

## Mitigation Efforts
- Total Recommendations: {report_data["mitigation_efforts"]["total_recommendations"]}
- Comparative Analyses: {report_data["mitigation_efforts"]["comparative_analyses"]}

## Transparency Commitments
"""
        for commitment in report_data["transparency_commitments"]:
            md += f"- {commitment}\n"

        return md

    def _generate_html_report(self, report_data: dict[str, Any]) -> str:
        """Generate HTML transparency report."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Bias Analysis Transparency Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e8f4f8; border-radius: 3px; }}
        .commitment {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Bias Analysis Transparency Report</h1>
        <p>Generated: {time.ctime(report_data["report_metadata"]["generated_at"])}</p>
    </div>
    
    <div class="section">
        <h2>Report Metadata</h2>
        <div class="metric">Total Analyses: {report_data["report_metadata"]["total_analyses"]}</div>
        <div class="metric">Sources Analyzed: {report_data["report_metadata"]["sources_analyzed"]}</div>
    </div>
    
    <div class="section">
        <h2>Bias Statistics</h2>
        <div class="metric">Average Bias Score: {report_data["bias_statistics"]["average_bias_score"]:.3f}</div>
        <h3>Bias Distribution</h3>
        <div class="metric">Low Bias: {report_data["bias_statistics"]["bias_distribution"]["low_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["low_bias_pct"]:.1f}%)</div>
        <div class="metric">Moderate Bias: {report_data["bias_statistics"]["bias_distribution"]["moderate_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["moderate_bias_pct"]:.1f}%)</div>
        <div class="metric">High Bias: {report_data["bias_statistics"]["bias_distribution"]["high_bias"]} ({report_data["bias_statistics"]["bias_percentages"]["high_bias_pct"]:.1f}%)</div>
    </div>
    
    <div class="section">
        <h2>Mitigation Efforts</h2>
        <div class="metric">Total Recommendations: {report_data["mitigation_efforts"]["total_recommendations"]}</div>
        <div class="metric">Comparative Analyses: {report_data["mitigation_efforts"]["comparative_analyses"]}</div>
    </div>
    
    <div class="section">
        <h2>Transparency Commitments</h2>
"""
        for commitment in report_data["transparency_commitments"]:
            html += f"        <div class='commitment'>• {commitment}</div>\n"

        html += """    </div>
</body>
</html>"""

        return html
