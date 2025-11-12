"""Dashboard Integration Service - Prometheus and Grafana integration

This service provides integration with Prometheus metrics and Grafana dashboards,
enabling comprehensive monitoring and visualization capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


logger = logging.getLogger(__name__)


class DashboardType(Enum):
    """Types of dashboards"""

    SYSTEM_OVERVIEW = "system_overview"
    AGENT_PERFORMANCE = "agent_performance"
    QUALITY_METRICS = "quality_metrics"
    BUSINESS_METRICS = "business_metrics"
    ALERT_DASHBOARD = "alert_dashboard"
    CUSTOM = "custom"


class WidgetType(Enum):
    """Types of dashboard widgets"""

    GRAPH = "graph"
    SINGLESTAT = "singlestat"
    TABLE = "table"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"


@dataclass
class MetricsQuery:
    """Prometheus metrics query"""

    query: str
    legend: str
    ref_id: str = "A"
    interval: str = "1m"
    range: str = "1h"
    step: str = "15s"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""

    widget_id: str
    title: str
    widget_type: WidgetType
    position: dict[str, int]
    queries: list[MetricsQuery]
    options: dict[str, Any] = field(default_factory=dict)
    thresholds: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GrafanaDashboard:
    """Grafana dashboard configuration"""

    dashboard_id: str
    title: str
    description: str
    dashboard_type: DashboardType
    widgets: list[DashboardWidget]
    tags: list[str] = field(default_factory=list)
    time_range: str = "1h"
    refresh_interval: str = "30s"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PrometheusMetrics:
    """Prometheus metrics configuration"""

    metric_name: str
    metric_type: str
    help_text: str
    labels: list[str] = field(default_factory=list)
    buckets: list[float] | None = None
    quantiles: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    """Configuration for dashboard integration"""

    enable_prometheus: bool = True
    enable_grafana: bool = True
    enable_auto_dashboards: bool = True
    prometheus_endpoint: str = "http://localhost:9090"
    metrics_path: str = "/metrics"
    scrape_interval: int = 15
    grafana_endpoint: str = "http://localhost:3000"
    grafana_api_key: str | None = None
    default_org_id: int = 1
    auto_refresh_interval: int = 30
    default_time_range: str = "1h"
    max_widgets_per_dashboard: int = 50
    max_concurrent_queries: int = 10
    query_timeout: int = 30
    cache_ttl: int = 60


class DashboardIntegrationService:
    """Dashboard integration service for Prometheus and Grafana"""

    def __init__(self, config: DashboardConfig | None = None):
        self.config = config or DashboardConfig()
        self._initialized = False
        self._prometheus_metrics: dict[str, PrometheusMetrics] = {}
        self._grafana_dashboards: dict[str, GrafanaDashboard] = {}
        self._dashboard_cache: dict[str, Any] = {}
        self._query_cache: dict[str, Any] = {}
        self._last_cache_update: dict[str, datetime] = {}
        self._initialize_dashboard_integration()

    def _initialize_dashboard_integration(self) -> None:
        """Initialize the dashboard integration service"""
        try:
            self._initialized = True
            logger.info("Dashboard Integration Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dashboard Integration Service: {e}")
            self._initialized = False

    async def register_prometheus_metric(
        self,
        metric_name: str,
        metric_type: str,
        help_text: str,
        labels: list[str] | None = None,
        buckets: list[float] | None = None,
        quantiles: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Register a metric with Prometheus"""
        try:
            if not self._initialized:
                return StepResult.fail("Dashboard Integration Service not initialized")
            prometheus_metric = PrometheusMetrics(
                metric_name=metric_name,
                metric_type=metric_type,
                help_text=help_text,
                labels=labels or [],
                buckets=buckets,
                quantiles=quantiles,
                metadata=metadata or {},
            )
            self._prometheus_metrics[metric_name] = prometheus_metric
            logger.info(f"Prometheus metric registered: {metric_name} ({metric_type})")
            return StepResult.ok(
                data={
                    "registered": True,
                    "metric_name": metric_name,
                    "metric_type": metric_type,
                    "labels": labels or [],
                    "help_text": help_text,
                }
            )
        except Exception as e:
            logger.error(f"Error registering Prometheus metric: {e}")
            return StepResult.fail(f"Prometheus metric registration failed: {e!s}")

    async def create_grafana_dashboard(
        self,
        dashboard_id: str,
        title: str,
        description: str,
        dashboard_type: DashboardType,
        widgets: list[DashboardWidget],
        tags: list[str] | None = None,
        time_range: str | None = None,
        refresh_interval: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Create a Grafana dashboard"""
        try:
            if not self._initialized:
                return StepResult.fail("Dashboard Integration Service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            dashboard = GrafanaDashboard(
                dashboard_id=dashboard_id,
                title=title,
                description=description,
                dashboard_type=dashboard_type,
                widgets=widgets,
                tags=tags or [],
                time_range=time_range or self.config.default_time_range,
                refresh_interval=refresh_interval or f"{self.config.auto_refresh_interval}s",
                metadata={
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    **(metadata or {}),
                },
            )
            self._grafana_dashboards[dashboard_id] = dashboard
            logger.info(f"Grafana dashboard created: {dashboard_id} - {title}")
            return StepResult.ok(
                data={
                    "created": True,
                    "dashboard_id": dashboard_id,
                    "title": title,
                    "dashboard_type": dashboard_type.value,
                    "widgets_count": len(widgets),
                    "tags": tags or [],
                }
            )
        except Exception as e:
            logger.error(f"Error creating Grafana dashboard: {e}")
            return StepResult.fail(f"Grafana dashboard creation failed: {e!s}")

    async def execute_metrics_query(
        self,
        query: str,
        range_time: str = "1h",
        step: str = "15s",
        timeout: int | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Execute a Prometheus metrics query"""
        try:
            if not self._initialized:
                return StepResult.fail("Dashboard Integration Service not initialized")
            cache_key = f"{query}:{range_time}:{step}"
            if cache_key in self._query_cache:
                cache_time = self._last_cache_update.get(cache_key)
                if cache_time and (datetime.now(timezone.utc) - cache_time).seconds < self.config.cache_ttl:
                    logger.debug(f"Returning cached query result: {query}")
                    return StepResult.ok(data=self._query_cache[cache_key])
            query_result = await self._execute_prometheus_query(query, range_time, step, timeout)
            self._query_cache[cache_key] = query_result
            self._last_cache_update[cache_key] = datetime.now(timezone.utc)
            return StepResult.ok(
                data={
                    "query": query,
                    "range": range_time,
                    "step": step,
                    "result": query_result,
                    "cached": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error executing metrics query: {e}")
            return StepResult.fail(f"Metrics query execution failed: {e!s}")

    async def get_dashboard_data(
        self,
        dashboard_id: str,
        time_range: str | None = None,
        refresh_cache: bool = False,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Get data for a dashboard"""
        try:
            if not self._initialized:
                return StepResult.fail("Dashboard Integration Service not initialized")
            if dashboard_id not in self._grafana_dashboards:
                return StepResult.fail(f"Dashboard {dashboard_id} not found")
            dashboard = self._grafana_dashboards[dashboard_id]
            time_range = time_range or dashboard.time_range
            cache_key = f"{dashboard_id}:{time_range}"
            if not refresh_cache and cache_key in self._dashboard_cache:
                cache_time = self._last_cache_update.get(cache_key)
                if cache_time and (datetime.now(timezone.utc) - cache_time).seconds < self.config.cache_ttl:
                    logger.debug(f"Returning cached dashboard data: {dashboard_id}")
                    return StepResult.ok(data=self._dashboard_cache[cache_key])
            dashboard_data = {
                "dashboard_id": dashboard_id,
                "title": dashboard.title,
                "description": dashboard.description,
                "dashboard_type": dashboard.dashboard_type.value,
                "time_range": time_range,
                "widgets": [],
                "metadata": dashboard.metadata,
            }
            for widget in dashboard.widgets:
                widget_data = await self._get_widget_data(widget, time_range)
                dashboard_data["widgets"].append(widget_data)
            self._dashboard_cache[cache_key] = dashboard_data
            self._last_cache_update[cache_key] = datetime.now(timezone.utc)
            return StepResult.ok(data=dashboard_data)
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return StepResult.fail(f"Dashboard data retrieval failed: {e!s}")

    async def export_dashboard_config(
        self,
        dashboard_id: str,
        format_type: str = "json",
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Export dashboard configuration"""
        try:
            if not self._initialized:
                return StepResult.fail("Dashboard Integration Service not initialized")
            if dashboard_id not in self._grafana_dashboards:
                return StepResult.fail(f"Dashboard {dashboard_id} not found")
            dashboard = self._grafana_dashboards[dashboard_id]
            if tenant_id and dashboard.metadata.get("tenant_id") != tenant_id:
                return StepResult.fail(f"Dashboard {dashboard_id} not accessible for tenant {tenant_id}")
            if workspace_id and dashboard.metadata.get("workspace_id") != workspace_id:
                return StepResult.fail(f"Dashboard {dashboard_id} not accessible for workspace {workspace_id}")
            if format_type == "json":
                exported_config = self._export_dashboard_json(dashboard)
            elif format_type == "grafana":
                exported_config = self._export_dashboard_grafana(dashboard)
            else:
                return StepResult.fail(f"Unsupported export format: {format_type}")
            return StepResult.ok(
                data={
                    "dashboard_id": dashboard_id,
                    "format": format_type,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "config": exported_config,
                }
            )
        except Exception as e:
            logger.error(f"Error exporting dashboard config: {e}")
            return StepResult.fail(f"Dashboard config export failed: {e!s}")

    async def _execute_prometheus_query(
        self, query: str, range_time: str, step: str, timeout: int | None
    ) -> dict[str, Any]:
        """Execute a Prometheus query (simulated)"""
        try:
            range_seconds = self._parse_time_range(range_time)
            data_points = []
            current_time = datetime.now(timezone.utc)
            for i in range(0, range_seconds, 15):
                timestamp = current_time - timedelta(seconds=i)
                value = 100 + i % 50
                data_points.append([int(timestamp.timestamp() * 1000), str(value)])
            return {
                "status": "success",
                "data": {"resultType": "matrix", "result": [{"metric": {"__name__": query}, "values": data_points}]},
            }
        except Exception as e:
            logger.error(f"Error executing Prometheus query: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_widget_data(self, widget: DashboardWidget, time_range: str) -> dict[str, Any]:
        """Get data for a specific widget"""
        try:
            widget_data = {
                "widget_id": widget.widget_id,
                "title": widget.title,
                "widget_type": widget.widget_type.value,
                "position": widget.position,
                "queries": [],
                "options": widget.options,
                "thresholds": widget.thresholds,
            }
            for query in widget.queries:
                query_result = await self._execute_prometheus_query(
                    query.query, query.range or time_range, query.step, None
                )
                widget_data["queries"].append(
                    {"ref_id": query.ref_id, "legend": query.legend, "query": query.query, "result": query_result}
                )
            return widget_data
        except Exception as e:
            logger.error(f"Error getting widget data: {e}")
            return {"widget_id": widget.widget_id, "error": str(e)}

    def _parse_time_range(self, time_range: str) -> int:
        """Parse time range string to seconds"""
        try:
            if time_range.endswith("s"):
                return int(time_range[:-1])
            elif time_range.endswith("m"):
                return int(time_range[:-1]) * 60
            elif time_range.endswith("h"):
                return int(time_range[:-1]) * 3600
            elif time_range.endswith("d"):
                return int(time_range[:-1]) * 86400
            else:
                return 3600
        except Exception:
            return 3600

    def _export_dashboard_json(self, dashboard: GrafanaDashboard) -> dict[str, Any]:
        """Export dashboard as JSON configuration"""
        try:
            return {
                "dashboard": {
                    "id": dashboard.dashboard_id,
                    "title": dashboard.title,
                    "description": dashboard.description,
                    "tags": dashboard.tags,
                    "time": {"from": f"now-{dashboard.time_range}", "to": "now"},
                    "refresh": dashboard.refresh_interval,
                    "panels": [
                        {
                            "id": widget.widget_id,
                            "title": widget.title,
                            "type": widget.widget_type.value,
                            "gridPos": widget.position,
                            "targets": [
                                {"expr": query.query, "legendFormat": query.legend, "refId": query.ref_id}
                                for query in widget.queries
                            ],
                            "options": widget.options,
                            "thresholds": widget.thresholds,
                        }
                        for widget in dashboard.widgets
                    ],
                },
                "meta": dashboard.metadata,
            }
        except Exception as e:
            logger.error(f"Error exporting dashboard JSON: {e}")
            return {"error": str(e)}

    def _export_dashboard_grafana(self, dashboard: GrafanaDashboard) -> dict[str, Any]:
        """Export dashboard as Grafana API format"""
        try:
            return {
                "dashboard": {
                    "title": dashboard.title,
                    "description": dashboard.description,
                    "tags": dashboard.tags,
                    "timezone": "utc",
                    "panels": [
                        {
                            "title": widget.title,
                            "type": widget.widget_type.value,
                            "gridPos": widget.position,
                            "targets": [
                                {"expr": query.query, "legendFormat": query.legend, "refId": query.ref_id}
                                for query in widget.queries
                            ],
                            "fieldConfig": {"defaults": widget.options, "thresholds": {"steps": widget.thresholds}},
                        }
                        for widget in dashboard.widgets
                    ],
                    "time": {"from": f"now-{dashboard.time_range}", "to": "now"},
                    "refresh": dashboard.refresh_interval,
                },
                "overwrite": True,
            }
        except Exception as e:
            logger.error(f"Error exporting dashboard Grafana format: {e}")
            return {"error": str(e)}

    def get_dashboard_integration_status(self) -> dict[str, Any]:
        """Get dashboard integration service status"""
        return {
            "initialized": self._initialized,
            "prometheus_metrics": len(self._prometheus_metrics),
            "grafana_dashboards": len(self._grafana_dashboards),
            "cached_queries": len(self._query_cache),
            "cached_dashboards": len(self._dashboard_cache),
            "config": {
                "enable_prometheus": self.config.enable_prometheus,
                "enable_grafana": self.config.enable_grafana,
                "enable_auto_dashboards": self.config.enable_auto_dashboards,
                "prometheus_endpoint": self.config.prometheus_endpoint,
                "grafana_endpoint": self.config.grafana_endpoint,
                "cache_ttl": self.config.cache_ttl,
            },
        }
