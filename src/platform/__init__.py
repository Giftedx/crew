"""
Platform integration and social media monitoring system for the Ultimate Discord Intelligence Bot.

Provides comprehensive social media monitoring, content discovery, cross-platform analytics,
and platform integration capabilities for multi-platform content analysis and engagement.
"""

from .content_discovery import (
    AggregationMode,
    ContentCluster,
    ContentDiscovery,
    ContentRankingMethod,
    DiscoveryQuery,
    DiscoveryResult,
    DiscoveryStrategy,
)
from .cross_platform_analytics import (
    AnalyticsDataPoint,
    AnalyticsDimension,
    AnalyticsMetric,
    AnalyticsQuery,
    AnalyticsResult,
    CrossPlatformAnalytics,
    CrossPlatformInsight,
    TimeGranularity,
    VisualizationType,
)
from .platform_integration import (
    AuthType,
    IntegrationMetrics,
    IntegrationStatus,
    PlatformConfig,
    PlatformIntegration,
    SyncMode,
    SyncResult,
)
from .social_monitor import (
    ContentType,
    MonitoringRule,
    PlatformType,
    SentimentType,
    SocialContent,
    SocialMonitor,
    TrendData,
)


__all__ = [
    "AggregationMode",
    "AnalyticsDataPoint",
    "AnalyticsDimension",
    # Cross-platform analytics
    "AnalyticsMetric",
    "AnalyticsQuery",
    "AnalyticsResult",
    "AuthType",
    "ContentCluster",
    "ContentDiscovery",
    "ContentRankingMethod",
    "ContentType",
    "CrossPlatformAnalytics",
    "CrossPlatformInsight",
    "DiscoveryQuery",
    "DiscoveryResult",
    # Content discovery
    "DiscoveryStrategy",
    "IntegrationMetrics",
    # Platform integration
    "IntegrationStatus",
    "MonitoringRule",
    "PlatformConfig",
    "PlatformIntegration",
    "PlatformType",
    "SentimentType",
    # Social monitoring
    "SocialContent",
    "SocialMonitor",
    "SyncMode",
    "SyncResult",
    "TimeGranularity",
    "TrendData",
    "VisualizationType",
]
