"""Observability Package - Unified metrics, monitoring, and alerting

This package provides comprehensive observability capabilities including
unified metrics collection, intelligent alerting, and dashboard integration.

See ADR-0005 for analytics consolidation architecture.
"""

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
    # Consolidated analytics (ADR-0005)
    "AnalyticsService",
    "get_analytics_service",
    "SystemHealth",
    "PerformanceMetrics",
    # Unified metrics
    "UnifiedMetricsCollector",
    "UnifiedMetricsConfig",
    "MetricType",
    "MetricCategory",
    "SystemMetric",
    "AgentMetric",
    "UnifiedPerformanceMetric",
    "QualityMetric",
    # Intelligent alerting
    "IntelligentAlertingService",
    "AlertingConfig",
    "AlertLevel",
    "AlertType",
    "AlertRule",
    "AlertCondition",
    "AlertAction",
    # Dashboard integration
    "DashboardIntegrationService",
    "DashboardConfig",
    "GrafanaDashboard",
    "PrometheusMetrics",
    "DashboardWidget",
    "MetricsQuery",
    "DashboardType",
    "WidgetType",
]
