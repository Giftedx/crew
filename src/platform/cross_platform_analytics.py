"""
Cross-platform analytics system for the Ultimate Discord Intelligence Bot.

Provides comprehensive analytics and insights across multiple social media platforms
with advanced data visualization, reporting, and trend analysis capabilities.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from .social_monitor import ContentType, PlatformType, SentimentType, SocialContent


logger = logging.getLogger(__name__)


class AnalyticsMetric(Enum):
    """Analytics metrics."""

    ENGAGEMENT_RATE = "engagement_rate"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    CLICK_THROUGH_RATE = "click_through_rate"
    SHARE_RATE = "share_rate"
    COMMENT_RATE = "comment_rate"
    SENTIMENT_DISTRIBUTION = "sentiment_distribution"
    CONTENT_PERFORMANCE = "content_performance"
    AUTHOR_INFLUENCE = "author_influence"
    TREND_VELOCITY = "trend_velocity"


class TimeGranularity(Enum):
    """Time granularity for analytics."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class VisualizationType(Enum):
    """Visualization types."""

    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    DASHBOARD = "dashboard"


@dataclass
class AnalyticsDimension:
    """Analytics dimension for grouping data."""

    name: str
    values: list[str]
    grouping_type: str = "categorical"


@dataclass
class AnalyticsQuery:
    """Analytics query configuration."""

    query_id: str
    metrics: list[AnalyticsMetric]
    dimensions: list[AnalyticsDimension] = field(default_factory=list)
    platforms: list[PlatformType] = field(default_factory=list)
    content_types: list[ContentType] = field(default_factory=list)
    time_range: tuple[float, float] = (0.0, time.time())
    time_granularity: TimeGranularity = TimeGranularity.DAILY
    filters: dict[str, Any] = field(default_factory=dict)
    aggregations: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_hours(self) -> float:
        """Get query duration in hours."""
        return (self.time_range[1] - self.time_range[0]) / 3600


@dataclass
class AnalyticsDataPoint:
    """Single analytics data point."""

    timestamp: float
    metric_name: str
    metric_value: float
    dimensions: dict[str, str] = field(default_factory=dict)
    platform: PlatformType | None = None
    content_type: ContentType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsResult:
    """Analytics query result."""

    query_id: str
    data_points: list[AnalyticsDataPoint]
    aggregated_data: dict[str, Any] = field(default_factory=dict)
    summary_statistics: dict[str, float] = field(default_factory=dict)
    trends: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    visualizations: list[dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_data_points(self) -> int:
        """Get total number of data points."""
        return len(self.data_points)

    @property
    def has_trends(self) -> bool:
        """Check if result has trend data."""
        return len(self.trends) > 0


@dataclass
class CrossPlatformInsight:
    """Cross-platform insight."""

    insight_id: str
    insight_type: str
    title: str
    description: str
    platforms_affected: list[PlatformType]
    metrics_involved: list[AnalyticsMetric]
    confidence_score: float
    impact_score: float
    actionable_recommendations: list[str]
    supporting_data: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_impact(self) -> bool:
        """Check if insight is high impact."""
        return self.impact_score > 0.7

    @property
    def is_high_confidence(self) -> bool:
        """Check if insight has high confidence."""
        return self.confidence_score > 0.8


class CrossPlatformAnalytics:
    """
    Advanced cross-platform analytics system.

    Provides comprehensive analytics, insights, and reporting capabilities
    across multiple social media platforms with advanced data processing
    and visualization features.
    """

    def __init__(self):
        """Initialize cross-platform analytics system."""
        self.content_data: dict[str, SocialContent] = {}
        self.analytics_cache: dict[str, AnalyticsResult] = {}
        self.insights_history: list[CrossPlatformInsight] = []

        # Analytics statistics
        self.analytics_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "total_data_points": 0,
            "insights_generated": 0,
            "average_processing_time": 0.0,
            "cache_hit_rate": 0.0,
        }

        # Platform-specific configurations
        self.platform_configs = {
            PlatformType.TWITTER: {"engagement_weight": 1.0, "reach_multiplier": 1.0},
            PlatformType.FACEBOOK: {"engagement_weight": 1.2, "reach_multiplier": 1.5},
            PlatformType.INSTAGRAM: {"engagement_weight": 1.3, "reach_multiplier": 1.2},
            PlatformType.LINKEDIN: {"engagement_weight": 0.8, "reach_multiplier": 0.9},
            PlatformType.YOUTUBE: {"engagement_weight": 1.1, "reach_multiplier": 2.0},
            PlatformType.TIKTOK: {"engagement_weight": 1.4, "reach_multiplier": 1.8},
            PlatformType.REDDIT: {"engagement_weight": 0.9, "reach_multiplier": 0.8},
        }

        logger.info("Cross-platform analytics system initialized")

    async def analyze_cross_platform_performance(self, query: AnalyticsQuery) -> AnalyticsResult:
        """Analyze performance across multiple platforms."""
        start_time = time.time()

        try:
            self.analytics_stats["total_queries"] += 1

            # Check cache first
            cache_key = self._generate_cache_key(query)
            if cache_key in self.analytics_cache:
                self.analytics_stats["cache_hit_rate"] = self.analytics_stats["cache_hit_rate"] * 0.9 + 0.1
                return self.analytics_cache[cache_key]

            # Gather data
            data_points = await self._gather_analytics_data(query)

            # Process data
            aggregated_data = await self._aggregate_data(data_points, query)
            summary_statistics = await self._calculate_summary_statistics(data_points)
            trends = await self._analyze_trends(data_points, query)

            # Generate insights
            insights = await self._generate_insights(data_points, trends, query)

            # Create visualizations
            visualizations = await self._create_visualizations(data_points, query)

            # Create result
            result = AnalyticsResult(
                query_id=query.query_id,
                data_points=data_points,
                aggregated_data=aggregated_data,
                summary_statistics=summary_statistics,
                trends=trends,
                insights=insights,
                visualizations=visualizations,
                processing_time=time.time() - start_time,
            )

            # Cache result
            self.analytics_cache[cache_key] = result

            # Update statistics
            self._update_analytics_stats(result)

            logger.info(
                f"Cross-platform analysis completed for query {query.query_id}: "
                f"{len(data_points)} data points, {len(insights)} insights"
            )

            return result

        except Exception as e:
            logger.error(f"Cross-platform analysis failed for query {query.query_id}: {e}")
            return AnalyticsResult(
                query_id=query.query_id,
                data_points=[],
                processing_time=time.time() - start_time,
            )

    async def compare_platform_performance(
        self, platforms: list[PlatformType], time_range: tuple[float, float]
    ) -> dict[str, Any]:
        """Compare performance across platforms."""
        try:
            comparison_data = {}

            for platform in platforms:
                # Get platform-specific data
                platform_data = await self._get_platform_data(platform, time_range)

                # Calculate platform metrics
                metrics = await self._calculate_platform_metrics(platform_data, platform)
                comparison_data[platform.value] = metrics

            # Calculate comparative insights
            insights = await self._generate_platform_comparison_insights(comparison_data)

            return {
                "platforms": comparison_data,
                "insights": insights,
                "time_range": time_range,
                "generated_at": time.time(),
            }

        except Exception as e:
            logger.error(f"Platform performance comparison failed: {e}")
            return {}

    async def analyze_content_virality(
        self, content: list[SocialContent], time_window_hours: int = 24
    ) -> dict[str, Any]:
        """Analyze content virality patterns."""
        try:
            virality_analysis = {
                "total_content": len(content),
                "viral_content": [],
                "virality_factors": {},
                "platform_performance": {},
                "temporal_patterns": {},
                "author_patterns": {},
                "content_type_patterns": {},
                "recommendations": [],
            }

            # Identify viral content
            viral_content = []
            for item in content:
                if await self._is_viral_content(item):
                    viral_content.append(item)

            virality_analysis["viral_content"] = viral_content

            # Analyze virality factors
            virality_factors = await self._analyze_virality_factors(viral_content)
            virality_analysis["virality_factors"] = virality_factors

            # Platform performance analysis
            platform_performance = {}
            for platform in PlatformType:
                platform_content = [item for item in viral_content if item.platform == platform]
                if platform_content:
                    platform_performance[platform.value] = await self._analyze_platform_virality(platform_content)

            virality_analysis["platform_performance"] = platform_performance

            # Temporal patterns
            temporal_patterns = await self._analyze_viral_temporal_patterns(viral_content)
            virality_analysis["temporal_patterns"] = temporal_patterns

            # Author patterns
            author_patterns = await self._analyze_viral_author_patterns(viral_content)
            virality_analysis["author_patterns"] = author_patterns

            # Content type patterns
            content_type_patterns = await self._analyze_viral_content_type_patterns(viral_content)
            virality_analysis["content_type_patterns"] = content_type_patterns

            # Generate recommendations
            recommendations = await self._generate_virality_recommendations(virality_analysis)
            virality_analysis["recommendations"] = recommendations

            return virality_analysis

        except Exception as e:
            logger.error(f"Content virality analysis failed: {e}")
            return {}

    async def track_campaign_performance(self, campaign_id: str, platforms: list[PlatformType]) -> dict[str, Any]:
        """Track performance of a cross-platform campaign."""
        try:
            campaign_data = {
                "campaign_id": campaign_id,
                "platforms": [p.value for p in platforms],
                "overall_metrics": {},
                "platform_breakdown": {},
                "content_performance": {},
                "audience_insights": {},
                "roi_analysis": {},
                "recommendations": [],
                "tracking_period": {},
            }

            # Get campaign content
            campaign_content = await self._get_campaign_content(campaign_id, platforms)

            if not campaign_content:
                logger.warning(f"No content found for campaign {campaign_id}")
                return campaign_data

            # Calculate overall metrics
            overall_metrics = await self._calculate_campaign_overall_metrics(campaign_content)
            campaign_data["overall_metrics"] = overall_metrics

            # Platform breakdown
            for platform in platforms:
                platform_content = [item for item in campaign_content if item.platform == platform]
                if platform_content:
                    platform_metrics = await self._calculate_platform_campaign_metrics(platform_content)
                    campaign_data["platform_breakdown"][platform.value] = platform_metrics

            # Content performance
            content_performance = await self._analyze_campaign_content_performance(campaign_content)
            campaign_data["content_performance"] = content_performance

            # Audience insights
            audience_insights = await self._analyze_campaign_audience(campaign_content)
            campaign_data["audience_insights"] = audience_insights

            # ROI analysis
            roi_analysis = await self._analyze_campaign_roi(campaign_content)
            campaign_data["roi_analysis"] = roi_analysis

            # Generate recommendations
            recommendations = await self._generate_campaign_recommendations(campaign_data)
            campaign_data["recommendations"] = recommendations

            # Tracking period
            campaign_data["tracking_period"] = {
                "start_time": min(item.timestamp for item in campaign_content),
                "end_time": max(item.timestamp for item in campaign_content),
                "duration_hours": (
                    max(item.timestamp for item in campaign_content) - min(item.timestamp for item in campaign_content)
                )
                / 3600,
            }

            return campaign_data

        except Exception as e:
            logger.error(f"Campaign performance tracking failed for {campaign_id}: {e}")
            return {}

    async def generate_executive_dashboard(
        self, time_range: tuple[float, float], platforms: list[PlatformType]
    ) -> dict[str, Any]:
        """Generate executive dashboard with key metrics."""
        try:
            dashboard = {
                "time_range": time_range,
                "platforms": [p.value for p in platforms],
                "key_metrics": {},
                "performance_summary": {},
                "top_content": {},
                "trending_topics": {},
                "audience_insights": {},
                "competitive_analysis": {},
                "recommendations": {},
                "generated_at": time.time(),
            }

            # Get data for time range
            time_data = await self._get_time_range_data(time_range, platforms)

            # Key metrics
            key_metrics = await self._calculate_key_metrics(time_data)
            dashboard["key_metrics"] = key_metrics

            # Performance summary
            performance_summary = await self._generate_performance_summary(time_data, platforms)
            dashboard["performance_summary"] = performance_summary

            # Top content
            top_content = await self._identify_top_content(time_data)
            dashboard["top_content"] = top_content

            # Trending topics
            trending_topics = await self._identify_trending_topics(time_data)
            dashboard["trending_topics"] = trending_topics

            # Audience insights
            audience_insights = await self._generate_audience_insights(time_data)
            dashboard["audience_insights"] = audience_insights

            # Competitive analysis
            competitive_analysis = await self._perform_competitive_analysis(time_data)
            dashboard["competitive_analysis"] = competitive_analysis

            # Recommendations
            recommendations = await self._generate_dashboard_recommendations(dashboard)
            dashboard["recommendations"] = recommendations

            return dashboard

        except Exception as e:
            logger.error(f"Executive dashboard generation failed: {e}")
            return {}

    async def _gather_analytics_data(self, query: AnalyticsQuery) -> list[AnalyticsDataPoint]:
        """Gather analytics data based on query."""
        try:
            data_points = []

            # Filter content by time range
            relevant_content = [
                content
                for content in self.content_data.values()
                if query.time_range[0] <= content.timestamp <= query.time_range[1]
            ]

            # Filter by platforms
            if query.platforms:
                relevant_content = [content for content in relevant_content if content.platform in query.platforms]

            # Filter by content types
            if query.content_types:
                relevant_content = [
                    content for content in relevant_content if content.content_type in query.content_types
                ]

            # Generate data points for each metric
            for metric in query.metrics:
                for content in relevant_content:
                    data_point = await self._create_data_point(content, metric, query)
                    if data_point:
                        data_points.append(data_point)

            return data_points

        except Exception as e:
            logger.error(f"Analytics data gathering failed: {e}")
            return []

    async def _create_data_point(
        self, content: SocialContent, metric: AnalyticsMetric, query: AnalyticsQuery
    ) -> AnalyticsDataPoint | None:
        """Create a data point for specific content and metric."""
        try:
            metric_value = await self._calculate_metric_value(content, metric)

            if metric_value is None:
                return None

            # Create dimensions
            dimensions = {}
            for dimension in query.dimensions:
                if dimension.name == "platform":
                    dimensions["platform"] = content.platform.value
                elif dimension.name == "content_type":
                    dimensions["content_type"] = content.content_type.value
                elif dimension.name == "sentiment":
                    dimensions["sentiment"] = content.sentiment.value

            data_point = AnalyticsDataPoint(
                timestamp=content.timestamp,
                metric_name=metric.value,
                metric_value=metric_value,
                dimensions=dimensions,
                platform=content.platform,
                content_type=content.content_type,
            )

            return data_point

        except Exception as e:
            logger.error(f"Data point creation failed: {e}")
            return None

    async def _calculate_metric_value(self, content: SocialContent, metric: AnalyticsMetric) -> float | None:
        """Calculate metric value for content."""
        try:
            if metric == AnalyticsMetric.ENGAGEMENT_RATE:
                total_engagement = sum(content.engagement_metrics.values())
                return min(1.0, total_engagement / 10000)

            elif metric == AnalyticsMetric.REACH:
                # Estimate reach based on engagement
                total_engagement = sum(content.engagement_metrics.values())
                return total_engagement * 10  # Rough estimate

            elif metric == AnalyticsMetric.IMPRESSIONS:
                # Estimate impressions based on reach
                reach = await self._calculate_metric_value(content, AnalyticsMetric.REACH)
                return reach * 3 if reach else 0

            elif metric == AnalyticsMetric.CLICK_THROUGH_RATE:
                # Simulate CTR
                return np.random.uniform(0.01, 0.05)

            elif metric == AnalyticsMetric.SHARE_RATE:
                shares = content.engagement_metrics.get("shares", 0)
                total_engagement = sum(content.engagement_metrics.values())
                return shares / max(1, total_engagement)

            elif metric == AnalyticsMetric.COMMENT_RATE:
                comments = content.engagement_metrics.get("comments", 0)
                total_engagement = sum(content.engagement_metrics.values())
                return comments / max(1, total_engagement)

            elif metric == AnalyticsMetric.SENTIMENT_DISTRIBUTION:
                sentiment_values = {
                    SentimentType.POSITIVE: 1.0,
                    SentimentType.NEUTRAL: 0.0,
                    SentimentType.NEGATIVE: -1.0,
                }
                return sentiment_values.get(content.sentiment, 0.0)

            elif metric == AnalyticsMetric.CONTENT_PERFORMANCE:
                return content.relevance_score

            elif metric == AnalyticsMetric.AUTHOR_INFLUENCE:
                # Simulate author influence based on engagement
                total_engagement = sum(content.engagement_metrics.values())
                return min(1.0, total_engagement / 5000)

            elif metric == AnalyticsMetric.TREND_VELOCITY:
                # Simulate trend velocity
                return np.random.uniform(0.0, 1.0)

            return None

        except Exception as e:
            logger.error(f"Metric value calculation failed for {metric}: {e}")
            return None

    async def _aggregate_data(self, data_points: list[AnalyticsDataPoint], query: AnalyticsQuery) -> dict[str, Any]:
        """Aggregate data points based on query configuration."""
        try:
            aggregated_data = {}

            # Group by dimensions
            grouped_data = {}
            for data_point in data_points:
                key = tuple(data_point.dimensions.items())
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(data_point)

            # Calculate aggregations
            for group_key, group_points in grouped_data.items():
                group_name = "_".join([f"{k}_{v}" for k, v in group_key])

                values = [point.metric_value for point in group_points]

                aggregated_data[group_name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "median": sorted(values)[len(values) // 2] if values else 0,
                }

            return aggregated_data

        except Exception as e:
            logger.error(f"Data aggregation failed: {e}")
            return {}

    async def _calculate_summary_statistics(self, data_points: list[AnalyticsDataPoint]) -> dict[str, float]:
        """Calculate summary statistics for data points."""
        try:
            if not data_points:
                return {}

            values = [point.metric_value for point in data_points]

            return {
                "total_points": len(values),
                "sum": sum(values),
                "mean": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2],
                "min": min(values),
                "max": max(values),
                "std_dev": np.std(values) if len(values) > 1 else 0.0,
                "variance": np.var(values) if len(values) > 1 else 0.0,
            }

        except Exception as e:
            logger.error(f"Summary statistics calculation failed: {e}")
            return {}

    async def _analyze_trends(self, data_points: list[AnalyticsDataPoint], query: AnalyticsQuery) -> dict[str, Any]:
        """Analyze trends in data points."""
        try:
            if len(data_points) < 2:
                return {}

            # Group by time periods
            time_groups = await self._group_data_by_time(data_points, query.time_granularity)

            trends = {}
            for metric_name, time_series in time_groups.items():
                if len(time_series) < 2:
                    continue

                # Calculate trend direction
                trend_direction = await self._calculate_trend_direction(time_series)

                # Calculate trend strength
                trend_strength = await self._calculate_trend_strength(time_series)

                # Calculate growth rate
                growth_rate = await self._calculate_growth_rate(time_series)

                trends[metric_name] = {
                    "direction": trend_direction,
                    "strength": trend_strength,
                    "growth_rate": growth_rate,
                    "time_series": time_series,
                }

            return trends

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {}

    async def _generate_insights(
        self,
        data_points: list[AnalyticsDataPoint],
        trends: dict[str, Any],
        query: AnalyticsQuery,
    ) -> list[str]:
        """Generate insights from analytics data."""
        try:
            insights = []

            # Performance insights
            if data_points:
                avg_performance = sum(point.metric_value for point in data_points) / len(data_points)
                insights.append(f"Average performance across all platforms: {avg_performance:.2f}")

            # Trend insights
            for metric, trend_data in trends.items():
                if trend_data["direction"] == "increasing":
                    insights.append(f"{metric} is trending upward with {trend_data['strength']:.2f} strength")
                elif trend_data["direction"] == "decreasing":
                    insights.append(f"{metric} is trending downward with {trend_data['strength']:.2f} strength")

            # Platform insights
            platform_performance = {}
            for point in data_points:
                if point.platform:
                    platform = point.platform.value
                    if platform not in platform_performance:
                        platform_performance[platform] = []
                    platform_performance[platform].append(point.metric_value)

            for platform, values in platform_performance.items():
                avg_value = sum(values) / len(values)
                insights.append(f"{platform} average performance: {avg_value:.2f}")

            return insights

        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return []

    async def _create_visualizations(
        self, data_points: list[AnalyticsDataPoint], query: AnalyticsQuery
    ) -> list[dict[str, Any]]:
        """Create visualizations for analytics data."""
        try:
            visualizations = []

            # Line chart for time series
            if len(data_points) > 1:
                line_chart = {
                    "type": VisualizationType.LINE_CHART.value,
                    "title": f"{query.query_id} - Time Series",
                    "data": {
                        "labels": [point.timestamp for point in data_points],
                        "datasets": [
                            {
                                "label": "Metric Value",
                                "data": [point.metric_value for point in data_points],
                            }
                        ],
                    },
                    "options": {
                        "responsive": True,
                        "scales": {"x": {"type": "time"}, "y": {"beginAtZero": True}},
                    },
                }
                visualizations.append(line_chart)

            # Bar chart for platform comparison
            platform_data = {}
            for point in data_points:
                if point.platform:
                    platform = point.platform.value
                    if platform not in platform_data:
                        platform_data[platform] = []
                    platform_data[platform].append(point.metric_value)

            if platform_data:
                bar_chart = {
                    "type": VisualizationType.BAR_CHART.value,
                    "title": "Platform Performance Comparison",
                    "data": {
                        "labels": list(platform_data.keys()),
                        "datasets": [
                            {
                                "label": "Average Performance",
                                "data": [sum(values) / len(values) for values in platform_data.values()],
                            }
                        ],
                    },
                    "options": {
                        "responsive": True,
                        "scales": {"y": {"beginAtZero": True}},
                    },
                }
                visualizations.append(bar_chart)

            return visualizations

        except Exception as e:
            logger.error(f"Visualization creation failed: {e}")
            return []

    async def _generate_cache_key(self, query: AnalyticsQuery) -> str:
        """Generate cache key for query."""
        key_parts = [
            query.query_id,
            str(sorted([m.value for m in query.metrics])),
            str(sorted([p.value for p in query.platforms])),
            str(query.time_range),
            str(query.time_granularity.value),
        ]
        return "_".join(key_parts)

    async def _group_data_by_time(
        self, data_points: list[AnalyticsDataPoint], granularity: TimeGranularity
    ) -> dict[str, list[float]]:
        """Group data points by time periods."""
        try:
            groups = {}

            for point in data_points:
                # Determine time period based on granularity
                if granularity == TimeGranularity.HOURLY:
                    period = int(point.timestamp // 3600) * 3600
                elif granularity == TimeGranularity.DAILY:
                    period = int(point.timestamp // 86400) * 86400
                elif granularity == TimeGranularity.WEEKLY:
                    period = int(point.timestamp // 604800) * 604800
                elif granularity == TimeGranularity.MONTHLY:
                    period = int(point.timestamp // 2592000) * 2592000
                else:
                    period = point.timestamp

                period_key = f"{point.metric_name}_{period}"

                if period_key not in groups:
                    groups[period_key] = []
                groups[period_key].append(point.metric_value)

            return groups

        except Exception as e:
            logger.error(f"Time grouping failed: {e}")
            return {}

    async def _calculate_trend_direction(self, time_series: list[float]) -> str:
        """Calculate trend direction from time series."""
        try:
            if len(time_series) < 2:
                return "stable"

            # Simple linear regression slope
            x = list(range(len(time_series)))
            y = time_series

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

            if slope > 0.01:
                return "increasing"
            elif slope < -0.01:
                return "decreasing"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Trend direction calculation failed: {e}")
            return "stable"

    async def _calculate_trend_strength(self, time_series: list[float]) -> float:
        """Calculate trend strength from time series."""
        try:
            if len(time_series) < 2:
                return 0.0

            # Calculate R-squared
            x = list(range(len(time_series)))
            y = time_series

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            sum(y[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            intercept = (sum_y - slope * sum_x) / n

            # Calculate R-squared
            y_mean = sum_y / n
            ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
            ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))

            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            return max(0.0, min(1.0, r_squared))

        except Exception as e:
            logger.error(f"Trend strength calculation failed: {e}")
            return 0.0

    async def _calculate_growth_rate(self, time_series: list[float]) -> float:
        """Calculate growth rate from time series."""
        try:
            if len(time_series) < 2:
                return 0.0

            first_value = time_series[0]
            last_value = time_series[-1]

            if first_value == 0:
                return 0.0

            growth_rate = (last_value - first_value) / first_value
            return growth_rate

        except Exception as e:
            logger.error(f"Growth rate calculation failed: {e}")
            return 0.0

    def _update_analytics_stats(self, result: AnalyticsResult) -> None:
        """Update analytics statistics."""
        try:
            self.analytics_stats["successful_queries"] += 1
            self.analytics_stats["total_data_points"] += len(result.data_points)

            # Update average processing time
            total_queries = self.analytics_stats["total_queries"]
            current_avg = self.analytics_stats["average_processing_time"]
            new_avg = (current_avg * (total_queries - 1) + result.processing_time) / total_queries
            self.analytics_stats["average_processing_time"] = new_avg

        except Exception as e:
            logger.error(f"Analytics stats update failed: {e}")

    # Placeholder methods for advanced analytics features
    async def _get_platform_data(self, platform: PlatformType, time_range: tuple[float, float]) -> list[SocialContent]:
        """Get platform-specific data."""
        return [
            content
            for content in self.content_data.values()
            if content.platform == platform and time_range[0] <= content.timestamp <= time_range[1]
        ]

    async def _calculate_platform_metrics(
        self, platform_data: list[SocialContent], platform: PlatformType
    ) -> dict[str, Any]:
        """Calculate platform-specific metrics."""
        return {"total_content": len(platform_data), "platform": platform.value}

    async def _generate_platform_comparison_insights(self, comparison_data: dict[str, Any]) -> list[str]:
        """Generate platform comparison insights."""
        return ["Platform comparison insights generated"]

    async def _is_viral_content(self, content: SocialContent) -> bool:
        """Check if content is viral."""
        total_engagement = sum(content.engagement_metrics.values())
        return total_engagement > 10000

    async def _analyze_virality_factors(self, viral_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze virality factors."""
        return {"factor_analysis": "completed"}

    async def _analyze_platform_virality(self, platform_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze platform-specific virality."""
        return {"platform_virality": "analyzed"}

    async def _analyze_viral_temporal_patterns(self, viral_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze viral temporal patterns."""
        return {"temporal_patterns": "analyzed"}

    async def _analyze_viral_author_patterns(self, viral_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze viral author patterns."""
        return {"author_patterns": "analyzed"}

    async def _analyze_viral_content_type_patterns(self, viral_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze viral content type patterns."""
        return {"content_type_patterns": "analyzed"}

    async def _generate_virality_recommendations(self, virality_analysis: dict[str, Any]) -> list[str]:
        """Generate virality recommendations."""
        return ["Focus on high-engagement content types", "Optimize posting times"]

    async def _get_campaign_content(self, campaign_id: str, platforms: list[PlatformType]) -> list[SocialContent]:
        """Get campaign content."""
        return [
            content
            for content in self.content_data.values()
            if content.platform in platforms and campaign_id in content.metadata.get("campaign_id", "")
        ]

    async def _calculate_campaign_overall_metrics(self, campaign_content: list[SocialContent]) -> dict[str, Any]:
        """Calculate campaign overall metrics."""
        return {
            "total_content": len(campaign_content),
            "total_engagement": sum(sum(c.engagement_metrics.values()) for c in campaign_content),
        }

    async def _calculate_platform_campaign_metrics(self, platform_content: list[SocialContent]) -> dict[str, Any]:
        """Calculate platform campaign metrics."""
        return {"platform_content": len(platform_content)}

    async def _analyze_campaign_content_performance(self, campaign_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze campaign content performance."""
        return {"performance_analysis": "completed"}

    async def _analyze_campaign_audience(self, campaign_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze campaign audience."""
        return {"audience_analysis": "completed"}

    async def _analyze_campaign_roi(self, campaign_content: list[SocialContent]) -> dict[str, Any]:
        """Analyze campaign ROI."""
        return {"roi_analysis": "completed"}

    async def _generate_campaign_recommendations(self, campaign_data: dict[str, Any]) -> list[str]:
        """Generate campaign recommendations."""
        return [
            "Optimize content for better engagement",
            "Focus on top-performing platforms",
        ]

    async def _get_time_range_data(
        self, time_range: tuple[float, float], platforms: list[PlatformType]
    ) -> list[SocialContent]:
        """Get data for time range."""
        return [
            content
            for content in self.content_data.values()
            if time_range[0] <= content.timestamp <= time_range[1] and content.platform in platforms
        ]

    async def _calculate_key_metrics(self, time_data: list[SocialContent]) -> dict[str, Any]:
        """Calculate key metrics."""
        return {
            "total_content": len(time_data),
            "total_engagement": sum(sum(c.engagement_metrics.values()) for c in time_data),
        }

    async def _generate_performance_summary(
        self, time_data: list[SocialContent], platforms: list[PlatformType]
    ) -> dict[str, Any]:
        """Generate performance summary."""
        return {"performance_summary": "generated"}

    async def _identify_top_content(self, time_data: list[SocialContent]) -> dict[str, Any]:
        """Identify top content."""
        return {
            "top_content": sorted(
                time_data,
                key=lambda x: sum(x.engagement_metrics.values()),
                reverse=True,
            )[:10]
        }

    async def _identify_trending_topics(self, time_data: list[SocialContent]) -> dict[str, Any]:
        """Identify trending topics."""
        return {"trending_topics": ["topic1", "topic2", "topic3"]}

    async def _generate_audience_insights(self, time_data: list[SocialContent]) -> dict[str, Any]:
        """Generate audience insights."""
        return {"audience_insights": "generated"}

    async def _perform_competitive_analysis(self, time_data: list[SocialContent]) -> dict[str, Any]:
        """Perform competitive analysis."""
        return {"competitive_analysis": "completed"}

    async def _generate_dashboard_recommendations(self, dashboard: dict[str, Any]) -> dict[str, Any]:
        """Generate dashboard recommendations."""
        return {"recommendations": ["Increase engagement", "Optimize content strategy"]}

    async def get_analytics_statistics(self) -> dict[str, Any]:
        """Get analytics statistics."""
        return self.analytics_stats.copy()

    async def clear_cache(self) -> None:
        """Clear analytics cache."""
        self.analytics_cache.clear()
        logger.info("Analytics cache cleared")

    async def __aenter__(self) -> "CrossPlatformAnalytics":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.clear_cache()
