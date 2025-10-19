"""Observability Tools - CrewAI tools for metrics, alerting, and dashboards

This module provides CrewAI-compatible tools for agents to interact with
the observability system for metrics collection, alerting, and dashboard management.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from crewai.tools import BaseTool
from pydantic import Field

from ultimate_discord_intelligence_bot.observability import (
    AlertingConfig,
    AlertLevel,
    AlertType,
    DashboardConfig,
    DashboardIntegrationService,
    DashboardType,
    IntelligentAlertingService,
    MetricCategory,
    MetricType,
    UnifiedMetricsCollector,
    UnifiedMetricsConfig,
    WidgetType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class UnifiedMetricsTool(BaseTool):
    """Tool for collecting and managing unified metrics"""

    name: str = "unified_metrics_tool"
    description: str = (
        "Collect system, agent, performance, and quality metrics. "
        "Provides comprehensive metrics collection and analysis capabilities."
    )

    # Configuration
    metrics_config: Optional[UnifiedMetricsConfig] = Field(
        default=None, description="Metrics collector configuration"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize metrics collector
        self._metrics_collector = UnifiedMetricsCollector(self.metrics_config)

    def _run(
        self,
        operation: str,
        agent_id: str,
        agent_type: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> str:
        """Execute metrics operations"""
        try:
            if operation == "collect_system_metric":
                return self._collect_system_metric(agent_id, agent_type, data, **kwargs)
            elif operation == "collect_agent_metric":
                return self._collect_agent_metric(agent_id, agent_type, data, **kwargs)
            elif operation == "collect_performance_metric":
                return self._collect_performance_metric(
                    agent_id, agent_type, data, **kwargs
                )
            elif operation == "collect_quality_metric":
                return self._collect_quality_metric(
                    agent_id, agent_type, data, **kwargs
                )
            elif operation == "get_metrics_summary":
                return self._get_metrics_summary(agent_id, agent_type, data, **kwargs)
            elif operation == "export_metrics":
                return self._export_metrics(agent_id, agent_type, data, **kwargs)
            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_string()

        except Exception as e:
            logger.error(f"Error in unified metrics tool: {e}")
            return StepResult.fail(f"Metrics operation failed: {str(e)}").to_string()

    def _collect_system_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Collect a system-level metric"""
        try:
            # Extract parameters
            name = data.get("name", "")
            value = float(data.get("value", 0))
            metric_type = MetricType(data.get("metric_type", "gauge"))
            category = MetricCategory(data.get("category", "system"))
            labels = data.get("labels", {})
            description = data.get("description", "")
            metadata = data.get("metadata", {})

            # Collect system metric
            import asyncio

            result = asyncio.run(
                self._metrics_collector.collect_system_metric(
                    name=name,
                    value=value,
                    metric_type=metric_type,
                    category=category,
                    labels=labels,
                    description=description,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error collecting system metric: {e}")
            return StepResult.fail(
                f"System metric collection failed: {str(e)}"
            ).to_string()

    def _collect_agent_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Collect an agent-specific metric"""
        try:
            # Extract parameters
            metric_name = data.get("metric_name", "")
            value = float(data.get("value", 0))
            metric_type = MetricType(data.get("metric_type", "gauge"))
            category = MetricCategory(data.get("category", "agent"))
            labels = data.get("labels", {})
            description = data.get("description", "")
            metadata = data.get("metadata", {})

            # Collect agent metric
            import asyncio

            result = asyncio.run(
                self._metrics_collector.collect_agent_metric(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    metric_name=metric_name,
                    value=value,
                    metric_type=metric_type,
                    category=category,
                    labels=labels,
                    description=description,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error collecting agent metric: {e}")
            return StepResult.fail(
                f"Agent metric collection failed: {str(e)}"
            ).to_string()

    def _collect_performance_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Collect a performance metric"""
        try:
            # Extract parameters
            component = data.get("component", "")
            operation = data.get("operation", "")
            duration_ms = float(data.get("duration_ms", 0))
            success = bool(data.get("success", True))
            error_message = data.get("error_message")
            metadata = data.get("metadata", {})

            # Collect performance metric
            import asyncio

            result = asyncio.run(
                self._metrics_collector.collect_performance_metric(
                    component=component,
                    operation=operation,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error collecting performance metric: {e}")
            return StepResult.fail(
                f"Performance metric collection failed: {str(e)}"
            ).to_string()

    def _collect_quality_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Collect a quality metric"""
        try:
            # Extract parameters
            component = data.get("component", "")
            quality_type = data.get("quality_type", "")
            score = float(data.get("score", 0))
            threshold = float(data.get("threshold", 0))
            passed = bool(data.get("passed", True))
            metadata = data.get("metadata", {})

            # Collect quality metric
            import asyncio

            result = asyncio.run(
                self._metrics_collector.collect_quality_metric(
                    component=component,
                    quality_type=quality_type,
                    score=score,
                    threshold=threshold,
                    passed=passed,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error collecting quality metric: {e}")
            return StepResult.fail(
                f"Quality metric collection failed: {str(e)}"
            ).to_string()

    def _get_metrics_summary(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get metrics summary"""
        try:
            # Extract parameters
            category = (
                MetricCategory(data.get("category")) if data.get("category") else None
            )
            component = data.get("component")
            agent_type_filter = data.get("agent_type")
            hours = int(data.get("hours", 24))

            # Get metrics summary
            import asyncio

            result = asyncio.run(
                self._metrics_collector.get_metrics_summary(
                    category=category,
                    component=component,
                    agent_type=agent_type_filter,
                    hours=hours,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return StepResult.fail(
                f"Metrics summary retrieval failed: {str(e)}"
            ).to_string()

    def _export_metrics(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Export metrics"""
        try:
            # Extract parameters
            format_type = data.get("format_type", "prometheus")
            category = (
                MetricCategory(data.get("category")) if data.get("category") else None
            )
            hours = int(data.get("hours", 1))

            # Export metrics
            import asyncio

            result = asyncio.run(
                self._metrics_collector.export_metrics(
                    format_type=format_type, category=category, hours=hours
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return StepResult.fail(f"Metrics export failed: {str(e)}").to_string()


class IntelligentAlertingTool(BaseTool):
    """Tool for intelligent alerting and monitoring"""

    name: str = "intelligent_alerting_tool"
    description: str = (
        "Create alert rules, evaluate metrics, and manage alerts. "
        "Provides intelligent alerting with adaptive thresholds and anomaly detection."
    )

    # Configuration
    alerting_config: Optional[AlertingConfig] = Field(
        default=None, description="Alerting service configuration"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize alerting service
        self._alerting_service = IntelligentAlertingService(self.alerting_config)

    def _run(
        self,
        operation: str,
        agent_id: str,
        agent_type: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> str:
        """Execute alerting operations"""
        try:
            if operation == "create_alert_rule":
                return self._create_alert_rule(agent_id, agent_type, data, **kwargs)
            elif operation == "evaluate_metric":
                return self._evaluate_metric(agent_id, agent_type, data, **kwargs)
            elif operation == "resolve_alert":
                return self._resolve_alert(agent_id, agent_type, data, **kwargs)
            elif operation == "get_active_alerts":
                return self._get_active_alerts(agent_id, agent_type, data, **kwargs)
            elif operation == "get_alert_statistics":
                return self._get_alert_statistics(agent_id, agent_type, data, **kwargs)
            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_string()

        except Exception as e:
            logger.error(f"Error in intelligent alerting tool: {e}")
            return StepResult.fail(f"Alerting operation failed: {str(e)}").to_string()

    def _create_alert_rule(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Create an alert rule"""
        try:
            # Extract parameters
            rule_id = data.get("rule_id", "")
            name = data.get("name", "")
            description = data.get("description", "")
            alert_type = AlertType(data.get("alert_type", "threshold"))
            alert_level = AlertLevel(data.get("alert_level", "warning"))

            # Parse conditions
            conditions_data = data.get("conditions", [])
            conditions = []
            for cond_data in conditions_data:
                from ultimate_discord_intelligence_bot.observability.intelligent_alerts import (
                    AlertCondition,
                )

                condition = AlertCondition(
                    metric_name=cond_data.get("metric_name", ""),
                    operator=cond_data.get("operator", ">"),
                    threshold_value=float(cond_data.get("threshold_value", 0)),
                    time_window=int(cond_data.get("time_window", 300)),
                    evaluation_periods=int(cond_data.get("evaluation_periods", 1)),
                )
                conditions.append(condition)

            enabled = bool(data.get("enabled", True))
            cooldown_period = data.get("cooldown_period")
            max_alerts_per_hour = data.get("max_alerts_per_hour")
            notification_channels = data.get("notification_channels", [])
            tags = data.get("tags", [])
            metadata = data.get("metadata", {})

            # Create alert rule
            import asyncio

            result = asyncio.run(
                self._alerting_service.create_alert_rule(
                    rule_id=rule_id,
                    name=name,
                    description=description,
                    alert_type=alert_type,
                    alert_level=alert_level,
                    conditions=conditions,
                    enabled=enabled,
                    cooldown_period=cooldown_period,
                    max_alerts_per_hour=max_alerts_per_hour,
                    notification_channels=notification_channels,
                    tags=tags,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            return StepResult.fail(f"Alert rule creation failed: {str(e)}").to_string()

    def _evaluate_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Evaluate a metric for alerts"""
        try:
            # Extract parameters
            metric_name = data.get("metric_name", "")
            value = float(data.get("value", 0))
            timestamp = data.get("timestamp")
            labels = data.get("labels", {})
            metadata = data.get("metadata", {})

            # Parse timestamp if provided
            from datetime import datetime

            if timestamp:
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.fromtimestamp(timestamp)

            # Evaluate metric
            import asyncio

            result = asyncio.run(
                self._alerting_service.evaluate_metric_for_alerts(
                    metric_name=metric_name,
                    value=value,
                    timestamp=timestamp,
                    labels=labels,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error evaluating metric: {e}")
            return StepResult.fail(f"Metric evaluation failed: {str(e)}").to_string()

    def _resolve_alert(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Resolve an alert"""
        try:
            # Extract parameters
            alert_id = data.get("alert_id", "")
            resolution_reason = data.get("resolution_reason", "")
            resolved_by = data.get("resolved_by", agent_id)
            metadata = data.get("metadata", {})

            # Resolve alert
            import asyncio

            result = asyncio.run(
                self._alerting_service.resolve_alert(
                    alert_id=alert_id,
                    resolution_reason=resolution_reason,
                    resolved_by=resolved_by,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return StepResult.fail(f"Alert resolution failed: {str(e)}").to_string()

    def _get_active_alerts(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get active alerts"""
        try:
            # Extract parameters
            alert_level = (
                AlertLevel(data.get("alert_level")) if data.get("alert_level") else None
            )
            alert_type = (
                AlertType(data.get("alert_type")) if data.get("alert_type") else None
            )

            # Get active alerts
            import asyncio

            result = asyncio.run(
                self._alerting_service.get_active_alerts(
                    alert_level=alert_level, alert_type=alert_type
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return StepResult.fail(
                f"Active alerts retrieval failed: {str(e)}"
            ).to_string()

    def _get_alert_statistics(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get alert statistics"""
        try:
            # Extract parameters
            hours = int(data.get("hours", 24))

            # Get alert statistics
            import asyncio

            result = asyncio.run(
                self._alerting_service.get_alert_statistics(hours=hours)
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return StepResult.fail(
                f"Alert statistics retrieval failed: {str(e)}"
            ).to_string()


class DashboardIntegrationTool(BaseTool):
    """Tool for dashboard integration and management"""

    name: str = "dashboard_integration_tool"
    description: str = (
        "Create dashboards, execute metrics queries, and manage visualization. "
        "Provides integration with Prometheus and Grafana for comprehensive monitoring."
    )

    # Configuration
    dashboard_config: Optional[DashboardConfig] = Field(
        default=None, description="Dashboard integration configuration"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize dashboard integration service
        self._dashboard_service = DashboardIntegrationService(self.dashboard_config)

    def _run(
        self,
        operation: str,
        agent_id: str,
        agent_type: str,
        data: Dict[str, Any],
        **kwargs,
    ) -> str:
        """Execute dashboard operations"""
        try:
            if operation == "register_prometheus_metric":
                return self._register_prometheus_metric(
                    agent_id, agent_type, data, **kwargs
                )
            elif operation == "create_dashboard":
                return self._create_dashboard(agent_id, agent_type, data, **kwargs)
            elif operation == "execute_query":
                return self._execute_query(agent_id, agent_type, data, **kwargs)
            elif operation == "get_dashboard_data":
                return self._get_dashboard_data(agent_id, agent_type, data, **kwargs)
            elif operation == "export_dashboard_config":
                return self._export_dashboard_config(
                    agent_id, agent_type, data, **kwargs
                )
            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_string()

        except Exception as e:
            logger.error(f"Error in dashboard integration tool: {e}")
            return StepResult.fail(f"Dashboard operation failed: {str(e)}").to_string()

    def _register_prometheus_metric(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Register a Prometheus metric"""
        try:
            # Extract parameters
            metric_name = data.get("metric_name", "")
            metric_type = data.get("metric_type", "gauge")
            help_text = data.get("help_text", "")
            labels = data.get("labels", [])
            buckets = data.get("buckets")
            quantiles = data.get("quantiles")
            metadata = data.get("metadata", {})

            # Register metric
            import asyncio

            result = asyncio.run(
                self._dashboard_service.register_prometheus_metric(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    help_text=help_text,
                    labels=labels,
                    buckets=buckets,
                    quantiles=quantiles,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error registering Prometheus metric: {e}")
            return StepResult.fail(
                f"Prometheus metric registration failed: {str(e)}"
            ).to_string()

    def _create_dashboard(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Create a Grafana dashboard"""
        try:
            # Extract parameters
            dashboard_id = data.get("dashboard_id", "")
            title = data.get("title", "")
            description = data.get("description", "")
            dashboard_type = DashboardType(data.get("dashboard_type", "custom"))

            # Parse widgets
            widgets_data = data.get("widgets", [])
            widgets = []
            for widget_data in widgets_data:
                from ultimate_discord_intelligence_bot.observability.dashboard_integration import (
                    DashboardWidget,
                    MetricsQuery,
                )

                # Parse queries
                queries_data = widget_data.get("queries", [])
                queries = []
                for query_data in queries_data:
                    query = MetricsQuery(
                        query=query_data.get("query", ""),
                        legend=query_data.get("legend", ""),
                        ref_id=query_data.get("ref_id", "A"),
                        interval=query_data.get("interval", "1m"),
                        range=query_data.get("range", "1h"),
                        step=query_data.get("step", "15s"),
                    )
                    queries.append(query)

                widget = DashboardWidget(
                    widget_id=widget_data.get("widget_id", ""),
                    title=widget_data.get("title", ""),
                    widget_type=WidgetType(widget_data.get("widget_type", "graph")),
                    position=widget_data.get(
                        "position", {"x": 0, "y": 0, "width": 12, "height": 8}
                    ),
                    queries=queries,
                    options=widget_data.get("options", {}),
                    thresholds=widget_data.get("thresholds", []),
                )
                widgets.append(widget)

            tags = data.get("tags", [])
            time_range = data.get("time_range")
            refresh_interval = data.get("refresh_interval")
            metadata = data.get("metadata", {})

            # Create dashboard
            import asyncio

            result = asyncio.run(
                self._dashboard_service.create_grafana_dashboard(
                    dashboard_id=dashboard_id,
                    title=title,
                    description=description,
                    dashboard_type=dashboard_type,
                    widgets=widgets,
                    tags=tags,
                    time_range=time_range,
                    refresh_interval=refresh_interval,
                    metadata=metadata,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return StepResult.fail(f"Dashboard creation failed: {str(e)}").to_string()

    def _execute_query(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Execute a metrics query"""
        try:
            # Extract parameters
            query = data.get("query", "")
            range_time = data.get("range", "1h")
            step = data.get("step", "15s")
            timeout = data.get("timeout")

            # Execute query
            import asyncio

            result = asyncio.run(
                self._dashboard_service.execute_metrics_query(
                    query=query, range_time=range_time, step=step, timeout=timeout
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return StepResult.fail(f"Query execution failed: {str(e)}").to_string()

    def _get_dashboard_data(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Get dashboard data"""
        try:
            # Extract parameters
            dashboard_id = data.get("dashboard_id", "")
            time_range = data.get("time_range")
            refresh_cache = bool(data.get("refresh_cache", False))

            # Get dashboard data
            import asyncio

            result = asyncio.run(
                self._dashboard_service.get_dashboard_data(
                    dashboard_id=dashboard_id,
                    time_range=time_range,
                    refresh_cache=refresh_cache,
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return StepResult.fail(
                f"Dashboard data retrieval failed: {str(e)}"
            ).to_string()

    def _export_dashboard_config(
        self, agent_id: str, agent_type: str, data: Dict[str, Any], **kwargs
    ) -> str:
        """Export dashboard configuration"""
        try:
            # Extract parameters
            dashboard_id = data.get("dashboard_id", "")
            format_type = data.get("format_type", "json")

            # Export dashboard config
            import asyncio

            result = asyncio.run(
                self._dashboard_service.export_dashboard_config(
                    dashboard_id=dashboard_id, format_type=format_type
                )
            )

            return result.to_string()

        except Exception as e:
            logger.error(f"Error exporting dashboard config: {e}")
            return StepResult.fail(
                f"Dashboard config export failed: {str(e)}"
            ).to_string()
