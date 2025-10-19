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
    AlertRule,
    ContentType,
    EngagementMetrics,
    InfluencerProfile,
    MonitoringConfig,
    MonitoringResult,
    PlatformType,
    SentimentType,
    SocialContent,
    SocialMonitor,
    TrendAnalysis,
)

__all__ = [
    # Social monitoring
    "SocialContent",
    "PlatformType",
    "ContentType",
    "SentimentType",
    "EngagementMetrics",
    "SocialMonitor",
    "MonitoringConfig",
    "AlertRule",
    "MonitoringResult",
    "TrendAnalysis",
    "InfluencerProfile",
    # Content discovery
    "DiscoveryStrategy",
    "ContentRankingMethod",
    "AggregationMode",
    "DiscoveryQuery",
    "ContentCluster",
    "DiscoveryResult",
    "ContentDiscovery",
    # Cross-platform analytics
    "AnalyticsMetric",
    "TimeGranularity",
    "VisualizationType",
    "AnalyticsDimension",
    "AnalyticsQuery",
    "AnalyticsDataPoint",
    "AnalyticsResult",
    "CrossPlatformInsight",
    "CrossPlatformAnalytics",
    # Platform integration
    "IntegrationStatus",
    "AuthType",
    "SyncMode",
    "PlatformConfig",
    "IntegrationMetrics",
    "SyncResult",
    "PlatformIntegration",
]
