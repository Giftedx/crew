"""Compatibility shim for enhanced_monitoring in ultimate_discord_intelligence_bot.obs

This module re-exports the enhanced_monitoring API from platform.observability.enhanced_monitoring
to preserve the historical import path.
"""

from platform.observability.enhanced_monitoring import (
    Alert,
    AlertLevel,
    AlertRule,
    EnhancedMonitoringSystem,
    MonitoringStatus,
    QualityGate,
    SystemHealthMetrics,
    get_enhanced_monitoring,
    start_monitoring_system,
    stop_monitoring_system,
)


__all__ = [
    "Alert",
    "AlertLevel",
    "AlertRule",
    "EnhancedMonitoringSystem",
    "MonitoringStatus",
    "QualityGate",
    "SystemHealthMetrics",
    "get_enhanced_monitoring",
    "start_monitoring_system",
    "stop_monitoring_system",
]
