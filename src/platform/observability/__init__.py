"""Observability Package - Unified metrics, monitoring, and alerting

This package provides comprehensive observability capabilities including
unified metrics collection, intelligent alerting, and dashboard integration.

See ADR-0005 for analytics consolidation architecture.
"""

from .agent_metrics import AgentMetricsCollector
from .analytics_service import (
    AnalyticsService,
    PerformanceMetrics,
    SystemHealth,
    get_analytics_service,
)
from .dashboard_integration import (
    DashboardConfig,
    DashboardIntegrationService,
    DashboardType,
    DashboardWidget,
    GrafanaDashboard,
    MetricsQuery,
    PrometheusMetrics,
    WidgetType,
)
from .intelligent_alerts import (
    AlertAction,
    AlertCondition,
    AlertingConfig,
    AlertLevel,
    AlertRule,
    AlertType,
    IntelligentAlertingService,
)
from .unified_metrics import (
    AgentMetric,
    MetricCategory,
    MetricType,
    QualityMetric,
    SystemMetric,
    UnifiedMetricsCollector,
    UnifiedMetricsConfig,
)
from .unified_metrics import (
    PerformanceMetric as UnifiedPerformanceMetric,
)


__all__ = [
    "AgentMetric",
    "AgentMetricsCollector",
    "AlertAction",
    "AlertCondition",
    "AlertLevel",
    "AlertRule",
    "AlertType",
    "AlertingConfig",
    # Consolidated analytics (ADR-0005)
    "AnalyticsService",
    "DashboardConfig",
    # Dashboard integration
    "DashboardIntegrationService",
    "DashboardType",
    "DashboardWidget",
    "GrafanaDashboard",
    # Intelligent alerting
    "IntelligentAlertingService",
    "MetricCategory",
    "MetricType",
    "MetricsQuery",
    "PerformanceMetrics",
    "PrometheusMetrics",
    "QualityMetric",
    "SystemHealth",
    "SystemMetric",
    # Unified metrics
    "UnifiedMetricsCollector",
    "UnifiedMetricsConfig",
    "UnifiedPerformanceMetric",
    "WidgetType",
    "get_analytics_service",
]
