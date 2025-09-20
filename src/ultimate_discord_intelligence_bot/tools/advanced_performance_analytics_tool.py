"""
Advanced Performance Analytics Tool

This tool provides crew agents with access to the Advanced Performance Analytics System,
enabling automated performance monitoring, alert generation, and optimization execution
as part of the standard crew workflow.

Key Features:
- Execute comprehensive performance analytics
- Generate and send performance alerts
- Run predictive performance analysis
- Execute automated optimizations
- Send executive performance summaries
- Integration with Discord notification system
"""

from __future__ import annotations

import logging
from typing import Any

from core.time import default_utc_now

from ..advanced_performance_analytics_discord_integration import AdvancedPerformanceAnalyticsDiscordIntegration
from ..advanced_performance_analytics_integration import (
    get_performance_dashboard,
    run_full_performance_analysis,
)
from ..obs.metrics import get_metrics
from ..step_result import StepResult
from ._base import BaseTool

logger = logging.getLogger(__name__)


class AdvancedPerformanceAnalyticsTool(BaseTool[dict]):
    """Tool for running advanced performance analytics within crew workflows."""

    name: str = "Advanced Performance Analytics Tool"
    description: str = """Execute comprehensive performance analytics, generate alerts, run optimizations, and send reports.

    Capabilities:
    - Run comprehensive performance analysis with health scoring and recommendations
    - Generate and send performance alerts based on configurable rules
    - Execute predictive performance analysis with forecasting
    - Run automated performance optimizations
    - Send executive performance summaries to leadership channels
    - Monitor real-time performance dashboard data

    Use this tool for automated performance management as part of crew workflows."""

    def __init__(self):
        """Initialize the analytics tool."""
        self.discord_integration = AdvancedPerformanceAnalyticsDiscordIntegration()
        self._metrics = get_metrics()

    def _run(
        self,
        action: str,
        lookback_hours: int = 24,
        include_optimization: bool = False,
        send_notifications: bool = True,
        **kwargs: Any,
    ) -> StepResult:
        """Execute performance analytics actions.

        Args:
            action: Action to perform ('analyze', 'alerts', 'optimize', 'predict', 'executive_summary', 'dashboard')
            lookback_hours: Hours of historical data to analyze
            include_optimization: Whether to include optimization execution
            send_notifications: Whether to send Discord notifications
            **kwargs: Additional action-specific parameters

        Returns:
            StepResult with action results
        """
        try:
            logger.info(f"Executing performance analytics action: {action}")

            if action == "analyze":
                return self._run_comprehensive_analysis(lookback_hours, include_optimization, send_notifications)
            elif action == "alerts":
                return self._run_alert_monitoring(lookback_hours, send_notifications)
            elif action == "optimize":
                return self._run_optimization_execution(lookback_hours)
            elif action == "predict":
                return self._run_predictive_analysis(lookback_hours, send_notifications)
            elif action == "executive_summary":
                return self._send_executive_summary(lookback_hours)
            elif action == "dashboard":
                return self._get_dashboard_data()
            else:
                res = StepResult.fail(
                    error=f"Unknown action: {action}",
                    details="Supported actions: analyze, alerts, optimize, predict, executive_summary, dashboard",
                )
                try:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                    ).inc()
                except Exception:
                    pass
                return res

        except Exception as e:
            logger.error(f"Error executing performance analytics action '{action}': {e}")
            res = StepResult.fail(
                error=f"Performance analytics execution failed: {str(e)}",
                action=action,
                lookback_hours=lookback_hours,
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _run_comprehensive_analysis(
        self, lookback_hours: int, include_optimization: bool, send_notifications: bool
    ) -> StepResult:
        """Run comprehensive performance analysis.

        Args:
            lookback_hours: Hours of data to analyze
            include_optimization: Whether to include optimization execution
            send_notifications: Whether to send notifications

        Returns:
            StepResult with analysis results
        """
        try:
            import asyncio

            # Run the analysis
            analysis_results = asyncio.run(
                run_full_performance_analysis(lookback_hours=lookback_hours, include_optimization=include_optimization)
            )

            if "error" in analysis_results:
                return StepResult.fail(
                    error=analysis_results["error"], action="comprehensive_analysis", lookback_hours=lookback_hours
                )

            # Extract key metrics for crew reporting
            executive_summary = analysis_results.get("executive_summary", {})
            component_results = analysis_results.get("component_results", {})

            # Send notifications if requested
            notification_results = {}
            if send_notifications:
                # Generate and send alerts
                alerts = asyncio.run(
                    self.discord_integration.alert_engine.evaluate_analytics_for_alerts(lookback_hours)
                )
                if alerts:
                    notification_result = asyncio.run(self.discord_integration.send_batch_notifications(alerts))
                    notification_results = {
                        "alerts_generated": len(alerts),
                        "notification_status": notification_result.get("status", "unknown"),
                    }

            res = StepResult.ok(
                data={
                    "analysis_type": "comprehensive",
                    "lookback_hours": lookback_hours,
                    "optimization_included": include_optimization,
                    "overall_performance_score": executive_summary.get("overall_performance_score", 0),
                    "system_status": executive_summary.get("system_status", "unknown"),
                    "key_insights_count": executive_summary.get("key_insights_count", 0),
                    "recommendations_count": executive_summary.get("priority_recommendations_count", 0),
                    "component_health": {
                        "analytics": component_results.get("analytics", {}).get("health_score", 0),
                        "predictive": component_results.get("predictive", {}).get("reliability_score", 0),
                        "optimization": component_results.get("optimization", {}).get("success_rate", 0),
                    },
                    "notifications": notification_results,
                    "analysis_metadata": analysis_results.get("analysis_metadata", {}),
                    "full_results": analysis_results,  # Include full results for detailed access
                },
                message=f"Comprehensive performance analysis completed for {lookback_hours}h period",
                timestamp=default_utc_now(),
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                ).inc()
            except Exception:
                pass
            return res

        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            res = StepResult.fail(error=str(e), action="comprehensive_analysis")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _run_alert_monitoring(self, lookback_hours: int, send_notifications: bool) -> StepResult:
        """Run performance alert monitoring and notification.

        Args:
            lookback_hours: Hours of data to analyze for alerts
            send_notifications: Whether to send Discord notifications

        Returns:
            StepResult with alert monitoring results
        """
        try:
            import asyncio

            # Generate alerts
            alerts = asyncio.run(self.discord_integration.alert_engine.evaluate_analytics_for_alerts(lookback_hours))

            if not alerts:
                res = StepResult.ok(
                    data={
                        "alerts_generated": 0,
                        "lookback_hours": lookback_hours,
                        "status": "no_alerts",
                        "message": "No performance alerts generated - system operating within normal parameters",
                    },
                    message="Performance monitoring completed - no alerts",
                )
                try:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                    ).inc()
                except Exception:
                    pass
                return res

            # Group alerts by severity
            alert_summary = {"critical": 0, "warning": 0, "info": 0}
            for alert in alerts:
                alert_summary[alert.severity.value] += 1

            notification_results = {}
            if send_notifications:
                notification_result = asyncio.run(self.discord_integration.send_batch_notifications(alerts))
                notification_results = {
                    "notification_status": notification_result.get("status", "unknown"),
                    "successful_notifications": notification_result.get("successful", 0),
                    "failed_notifications": notification_result.get("failed", 0),
                }

            res = StepResult.ok(
                data={
                    "alerts_generated": len(alerts),
                    "lookback_hours": lookback_hours,
                    "alert_breakdown": alert_summary,
                    "notifications": notification_results,
                    "alert_details": [
                        {
                            "id": alert.alert_id,
                            "severity": alert.severity.value,
                            "category": alert.category.value,
                            "title": alert.title,
                            "metrics_violated": len(alert.metrics),
                        }
                        for alert in alerts
                    ],
                },
                message=f"Generated {len(alerts)} performance alerts ({alert_summary})",
                timestamp=default_utc_now(),
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                ).inc()
            except Exception:
                pass
            return res

        except Exception as e:
            logger.error(f"Error in alert monitoring: {e}")
            res = StepResult.fail(error=str(e), action="alert_monitoring")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _run_optimization_execution(self, lookback_hours: int) -> StepResult:
        """Run automated performance optimization.

        Args:
            lookback_hours: Hours of data to analyze for optimization

        Returns:
            StepResult with optimization results
        """
        try:
            import asyncio

            # Run analysis with optimization
            optimization_results = asyncio.run(
                run_full_performance_analysis(lookback_hours=lookback_hours, include_optimization=True)
            )

            if "error" in optimization_results:
                return StepResult.fail(
                    error=optimization_results["error"], action="optimization_execution", lookback_hours=lookback_hours
                )

            # Extract optimization-specific results
            detailed_results = optimization_results.get("detailed_results", {})
            optimization_data = detailed_results.get("optimization_results_full", {})

            if not optimization_data:
                res = StepResult.ok(
                    data={
                        "optimization_executed": False,
                        "message": "No optimization opportunities identified or optimization engine not available",
                        "lookback_hours": lookback_hours,
                    },
                    message="Performance optimization scan completed - no actions needed",
                )
                try:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                    ).inc()
                except Exception:
                    pass
                return res

            res = StepResult.ok(
                data={
                    "optimization_executed": True,
                    "lookback_hours": lookback_hours,
                    "actions_executed": optimization_data.get("actions_executed", 0),
                    "successful_optimizations": optimization_data.get("successful_optimizations", 0),
                    "performance_improvements": optimization_data.get("performance_improvements", {}),
                    "optimization_strategy": optimization_data.get("strategy_used", "unknown"),
                    "validation_results": optimization_data.get("validation_results", {}),
                    "full_optimization_data": optimization_data,
                },
                message=f"Executed {optimization_data.get('successful_optimizations', 0)} performance optimizations",
                timestamp=default_utc_now(),
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                ).inc()
            except Exception:
                pass
            return res

        except Exception as e:
            logger.error(f"Error in optimization execution: {e}")
            res = StepResult.fail(error=str(e), action="optimization_execution")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _run_predictive_analysis(self, lookback_hours: int, send_notifications: bool) -> StepResult:
        """Run predictive performance analysis.

        Args:
            lookback_hours: Hours of historical data for prediction modeling
            send_notifications: Whether to send predictive alerts

        Returns:
            StepResult with predictive analysis results
        """
        try:
            import asyncio

            # Get analytics system and run predictive analysis
            analytics_system = self.discord_integration.alert_engine.analytics_system
            predictive_results = asyncio.run(
                analytics_system.predictive_engine.generate_comprehensive_predictions(lookback_hours)
            )

            if "error" in predictive_results:
                return StepResult.fail(
                    error=predictive_results["error"], action="predictive_analysis", lookback_hours=lookback_hours
                )

            # Extract predictive insights
            predictions = predictive_results.get("predictions", [])
            early_warnings = predictive_results.get("early_warnings", {})
            capacity_forecast = predictive_results.get("capacity_forecast", {})

            # Send predictive alerts if requested and warnings exist
            notification_results = {}
            if send_notifications and early_warnings.get("total_warnings", 0) > 0:
                # Generate alerts for predictive warnings
                alerts = asyncio.run(
                    self.discord_integration.alert_engine.evaluate_analytics_for_alerts(lookback_hours)
                )
                predictive_alerts = [alert for alert in alerts if "predictive" in alert.category.value]

                if predictive_alerts:
                    notification_result = asyncio.run(
                        self.discord_integration.send_batch_notifications(predictive_alerts)
                    )
                    notification_results = {
                        "predictive_alerts_sent": len(predictive_alerts),
                        "notification_status": notification_result.get("status", "unknown"),
                    }

            res = StepResult.ok(
                data={
                    "prediction_type": "comprehensive",
                    "lookback_hours": lookback_hours,
                    "predictions_generated": len(predictions),
                    "reliability_score": predictive_results.get("reliability_score", 0),
                    "early_warnings": {
                        "total": early_warnings.get("total_warnings", 0),
                        "critical": early_warnings.get("critical", 0),
                        "warning": early_warnings.get("warning", 0),
                        "info": early_warnings.get("info", 0),
                    },
                    "capacity_forecast": {
                        "forecast_horizon": capacity_forecast.get("forecast_horizon", 0),
                        "predicted_capacity_issues": capacity_forecast.get("predicted_issues", []),
                        "optimization_recommendations": capacity_forecast.get("recommendations", []),
                    },
                    "notifications": notification_results,
                    "full_predictive_data": predictive_results,
                },
                message=f"Predictive analysis completed with {len(predictions)} forecasts and {early_warnings.get('total_warnings', 0)} warnings",
                timestamp=default_utc_now(),
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                ).inc()
            except Exception:
                pass
            return res

        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            res = StepResult.fail(error=str(e), action="predictive_analysis")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _send_executive_summary(self, lookback_hours: int) -> StepResult:
        """Send executive performance summary to Discord.

        Args:
            lookback_hours: Hours of data to summarize

        Returns:
            StepResult with executive summary delivery status
        """
        try:
            import asyncio

            # Send executive summary
            summary_result = asyncio.run(self.discord_integration.send_executive_summary(lookback_hours))

            if summary_result.get("status") == "success":
                res = StepResult.ok(
                    data={
                        "summary_delivered": True,
                        "summary_period_hours": lookback_hours,
                        "alerts_summarized": summary_result.get("total_alerts_summarized", 0),
                        "message_length": summary_result.get("message_length", 0),
                        "delivery_status": "success",
                    },
                    message=f"Executive performance summary delivered for {lookback_hours}h period",
                    timestamp=default_utc_now(),
                )
                try:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                    ).inc()
                except Exception:
                    pass
                return res
            else:
                res = StepResult.fail(
                    error=summary_result.get("error", "Unknown error"),
                    action="executive_summary",
                    summary_period_hours=lookback_hours,
                )
                try:
                    self._metrics.counter(
                        "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                    ).inc()
                except Exception:
                    pass
                return res

        except Exception as e:
            logger.error(f"Error sending executive summary: {e}")
            res = StepResult.fail(error=str(e), action="executive_summary")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res

    def _get_dashboard_data(self) -> StepResult:
        """Get real-time performance dashboard data.

        Returns:
            StepResult with dashboard data
        """
        try:
            import asyncio

            # Get dashboard data
            dashboard_data = asyncio.run(get_performance_dashboard())

            if "error" in dashboard_data:
                return StepResult.fail(error=dashboard_data["error"], action="dashboard_data")

            # Extract key dashboard metrics
            system_health = dashboard_data.get("system_health", {})
            advanced_analytics = dashboard_data.get("advanced_analytics", {})

            res = StepResult.ok(
                data={
                    "dashboard_status": dashboard_data.get("dashboard_status", "unknown"),
                    "timestamp": dashboard_data.get("timestamp", default_utc_now().isoformat()),
                    "system_health": {
                        "overall_status": system_health.get("overall_status", "unknown"),
                        "performance_score": system_health.get("performance_score", 0),
                        "active_components": system_health.get("active_components", []),
                    },
                    "analytics_status": {
                        "analytics_engine_active": advanced_analytics.get("analytics_engine_active", False),
                        "predictive_capabilities": advanced_analytics.get("predictive_capabilities", "disabled"),
                        "optimization_engine_active": advanced_analytics.get("optimization_engine_active", False),
                    },
                    "full_dashboard_data": dashboard_data,
                },
                message="Performance dashboard data retrieved successfully",
                timestamp=default_utc_now(),
            )
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "success"}
                ).inc()
            except Exception:
                pass
            return res

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            res = StepResult.fail(error=str(e), action="dashboard_data")
            try:
                self._metrics.counter(
                    "tool_runs_total", labels={"tool": "advanced_performance_analytics", "outcome": "error"}
                ).inc()
            except Exception:
                pass
            return res
