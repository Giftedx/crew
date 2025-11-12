"""Observability package.

Provides metrics, tracing, alerting, and SLO monitoring.
"""

from enum import Enum

from .metrics import get_metrics


# Enums for observability
class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""

    THRESHOLD = "threshold"
    ANOMALY = "anomaly"
    TREND = "trend"


class DashboardType(str, Enum):
    """Types of dashboards."""

    METRICS = "metrics"
    LOGS = "logs"
    TRACES = "traces"


class MetricCategory(str, Enum):
    """Metric categories."""

    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"


class MetricType(str, Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class WidgetType(str, Enum):
    """Dashboard widget types."""

    CHART = "chart"
    TABLE = "table"
    GAUGE = "gauge"


# Placeholder classes for backward compatibility
class AlertingConfig:
    """Placeholder for alerting configuration."""

    def __init__(self, **kwargs):
        self.config = kwargs


class DashboardConfig:
    """Placeholder for dashboard configuration."""

    def __init__(self, **kwargs):
        self.config = kwargs


class DashboardIntegrationService:
    """Placeholder for dashboard integration."""


class IntelligentAlertingService:
    """Placeholder for intelligent alerting."""


class UnifiedMetricsCollector:
    """Placeholder for metrics collector."""


class UnifiedMetricsConfig:
    """Placeholder for metrics config."""

    def __init__(self, **kwargs):
        self.config = kwargs


class IncidentManager:
    """Placeholder for incident management."""


class SLOMonitor:
    """Placeholder for SLO monitoring."""


incident = IncidentManager()
slo = SLOMonitor()

__all__ = [
    "AlertLevel",
    "AlertType",
    "AlertingConfig",
    "DashboardConfig",
    "DashboardIntegrationService",
    "DashboardType",
    "IntelligentAlertingService",
    "MetricCategory",
    "MetricType",
    "UnifiedMetricsCollector",
    "UnifiedMetricsConfig",
    "WidgetType",
    "get_metrics",
    "incident",
    "slo",
]
