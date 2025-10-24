"""
Advanced social media monitoring for the Ultimate Discord Intelligence Bot.

Provides comprehensive social media monitoring capabilities including trend detection,
content discovery, cross-platform analytics, and real-time sentiment tracking.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """Supported social media platforms."""

    TWITTER = "twitter"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    TWITCH = "twitch"


class ContentType(Enum):
    """Types of content that can be monitored."""

    POST = "post"
    COMMENT = "comment"
    VIDEO = "video"
    IMAGE = "image"
    STORY = "story"
    LIVE_STREAM = "live_stream"
    POLL = "poll"
    LINK = "link"


class SentimentType(Enum):
    """Sentiment classification types."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class TrendDirection(Enum):
    """Trend direction indicators."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class SocialContent:
    """Social media content item."""

    content_id: str
    platform: PlatformType
    content_type: ContentType
    author_id: str
    author_name: str
    text_content: str
    media_urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    engagement_metrics: dict[str, int] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    location: str | None = None
    language: str = "en"
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0
    relevance_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_highly_engaged(self) -> bool:
        """Check if content has high engagement."""
        total_engagement = sum(self.engagement_metrics.values())
        return total_engagement > 1000

    def is_recent(self, hours: int = 24) -> bool:
        """Check if content is recent."""
        return time.time() - self.timestamp < hours * 3600

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if not self.engagement_metrics:
            return 0.0

        total_engagement = sum(self.engagement_metrics.values())
        # Assume author has 1000 followers as baseline
        follower_count = self.metadata.get("author_followers", 1000)
        return float(min(1.0, total_engagement / max(1, follower_count)))


@dataclass
class TrendData:
    """Trend analysis data."""

    keyword: str
    platform: PlatformType
    current_volume: int
    previous_volume: int
    growth_rate: float
    sentiment_distribution: dict[SentimentType, int]
    top_content: list[SocialContent]
    trending_hashtags: list[str]
    influential_authors: list[str]
    geographic_distribution: dict[str, int]
    timestamp: float = field(default_factory=time.time)
    confidence_score: float = 0.0
    trend_direction: TrendDirection = TrendDirection.STABLE

    @property
    def is_trending(self) -> bool:
        """Check if keyword is trending."""
        return self.growth_rate > 0.5 and self.confidence_score > 0.7

    @property
    def sentiment_bias(self) -> SentimentType:
        """Get overall sentiment bias."""
        if not self.sentiment_distribution:
            return SentimentType.NEUTRAL

        total = sum(self.sentiment_distribution.values())
        if total == 0:
            return SentimentType.NEUTRAL

        positive_ratio = self.sentiment_distribution.get(SentimentType.POSITIVE, 0) / total
        negative_ratio = self.sentiment_distribution.get(SentimentType.NEGATIVE, 0) / total

        if positive_ratio > 0.6:
            return SentimentType.POSITIVE
        elif negative_ratio > 0.6:
            return SentimentType.NEGATIVE
        elif abs(positive_ratio - negative_ratio) < 0.2:
            return SentimentType.MIXED
        else:
            return SentimentType.NEUTRAL


@dataclass
class MonitoringRule:
    """Social media monitoring rule."""

    rule_id: str
    name: str
    keywords: list[str]
    platforms: list[PlatformType]
    content_types: list[ContentType] = field(default_factory=list)
    sentiment_filter: SentimentType | None = None
    min_engagement: int = 0
    min_sentiment_score: float = -1.0
    max_sentiment_score: float = 1.0
    languages: list[str] = field(default_factory=lambda: ["en"])
    geographic_regions: list[str] = field(default_factory=list)
    author_filters: list[str] = field(default_factory=list)
    hashtag_filters: list[str] = field(default_factory=list)
    is_active: bool = True
    priority: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complex(self) -> bool:
        """Check if rule is complex."""
        return (
            len(self.keywords) > 5
            or len(self.platforms) > 3
            or len(self.content_types) > 2
            or self.sentiment_filter is not None
            or len(self.geographic_regions) > 2
        )

    def matches_content(self, content: SocialContent) -> bool:
        """Check if content matches this rule."""
        # Platform check
        if content.platform not in self.platforms:
            return False

        # Content type check
        if self.content_types and content.content_type not in self.content_types:
            return False

        # Language check
        if content.language not in self.languages:
            return False

        # Geographic check
        if self.geographic_regions and content.location and content.location not in self.geographic_regions:
            return False

        # Keyword check
        text_lower = content.text_content.lower()
        if not any(keyword.lower() in text_lower for keyword in self.keywords):
            return False

        # Hashtag check
        if self.hashtag_filters and not any(hashtag in content.hashtags for hashtag in self.hashtag_filters):
            return False

        # Engagement check
        total_engagement = sum(content.engagement_metrics.values())
        if total_engagement < self.min_engagement:
            return False

        # Sentiment check
        if self.sentiment_filter and content.sentiment != self.sentiment_filter:
            return False

        return not (
            content.sentiment_score < self.min_sentiment_score or content.sentiment_score > self.max_sentiment_score
        )


class SocialMonitor:
    """
    Advanced social media monitoring system.

    Provides comprehensive monitoring capabilities including trend detection,
    content discovery, sentiment analysis, and cross-platform analytics.
    """

    def __init__(self):
        """Initialize social monitor."""
        self.monitoring_rules: dict[str, MonitoringRule] = {}
        self.active_monitors: dict[str, asyncio.Task[None]] = {}
        self.content_cache: dict[str, SocialContent] = {}
        self.trend_data: dict[str, TrendData] = {}

        # Monitoring statistics
        self.monitoring_stats = {
            "total_content_processed": 0,
            "active_rules": 0,
            "trends_detected": 0,
            "high_engagement_content": 0,
            "sentiment_analysis_count": 0,
            "average_processing_time": 0.0,
        }

        # Platform-specific configurations
        self.platform_configs = {
            PlatformType.TWITTER: {"rate_limit": 300, "api_version": "v2"},
            PlatformType.REDDIT: {"rate_limit": 60, "api_version": "v1"},
            PlatformType.YOUTUBE: {"rate_limit": 10000, "api_version": "v3"},
            PlatformType.TIKTOK: {"rate_limit": 500, "api_version": "v1"},
            PlatformType.INSTAGRAM: {"rate_limit": 200, "api_version": "v1"},
            PlatformType.FACEBOOK: {"rate_limit": 200, "api_version": "v18"},
            PlatformType.LINKEDIN: {"rate_limit": 100, "api_version": "v2"},
            PlatformType.DISCORD: {"rate_limit": 50, "api_version": "v10"},
            PlatformType.TELEGRAM: {"rate_limit": 30, "api_version": "v1"},
            PlatformType.TWITCH: {"rate_limit": 800, "api_version": "v1"},
        }

        logger.info("Social monitor initialized")

    async def add_monitoring_rule(self, rule: MonitoringRule) -> bool:
        """Add a monitoring rule."""
        try:
            if rule.rule_id in self.monitoring_rules:
                logger.warning(f"Rule {rule.rule_id} already exists")
                return False

            self.monitoring_rules[rule.rule_id] = rule
            self.monitoring_stats["active_rules"] = len([r for r in self.monitoring_rules.values() if r.is_active])

            # Start monitoring if rule is active
            if rule.is_active:
                await self._start_monitoring(rule)

            logger.info(f"Added monitoring rule: {rule.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add monitoring rule {rule.rule_id}: {e}")
            return False

    async def remove_monitoring_rule(self, rule_id: str) -> bool:
        """Remove a monitoring rule."""
        try:
            if rule_id not in self.monitoring_rules:
                logger.warning(f"Rule {rule_id} not found")
                return False

            # Stop monitoring if active
            if rule_id in self.active_monitors:
                self.active_monitors[rule_id].cancel()
                del self.active_monitors[rule_id]

            del self.monitoring_rules[rule_id]
            self.monitoring_stats["active_rules"] = len([r for r in self.monitoring_rules.values() if r.is_active])

            logger.info(f"Removed monitoring rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove monitoring rule {rule_id}: {e}")
            return False

    async def update_monitoring_rule(self, rule_id: str, updates: dict[str, Any]) -> bool:
        """Update a monitoring rule."""
        try:
            if rule_id not in self.monitoring_rules:
                logger.warning(f"Rule {rule_id} not found")
                return False

            rule = self.monitoring_rules[rule_id]

            # Update rule fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

            rule.updated_at = time.time()

            # Restart monitoring if active
            if rule.is_active and rule_id in self.active_monitors:
                self.active_monitors[rule_id].cancel()
                del self.active_monitors[rule_id]
                await self._start_monitoring(rule)

            logger.info(f"Updated monitoring rule: {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update monitoring rule {rule_id}: {e}")
            return False

    async def get_matching_content(self, rule_id: str, limit: int = 100) -> list[SocialContent]:
        """Get content matching a specific rule."""
        try:
            if rule_id not in self.monitoring_rules:
                logger.warning(f"Rule {rule_id} not found")
                return []

            rule = self.monitoring_rules[rule_id]
            matching_content = []

            for content in self.content_cache.values():
                if rule.matches_content(content):
                    matching_content.append(content)

            # Sort by relevance and recency
            matching_content.sort(key=lambda x: (x.relevance_score, x.timestamp), reverse=True)

            return matching_content[:limit]

        except Exception as e:
            logger.error(f"Failed to get matching content for rule {rule_id}: {e}")
            return []

    async def analyze_trends(self, keywords: list[str], platforms: list[PlatformType]) -> list[TrendData]:
        """Analyze trends for specific keywords and platforms."""
        try:
            trends = []

            for keyword in keywords:
                for platform in platforms:
                    trend = await self._analyze_keyword_trend(keyword, platform)
                    if trend:
                        trends.append(trend)

            # Sort by growth rate and confidence
            trends.sort(key=lambda x: (x.growth_rate, x.confidence_score), reverse=True)

            logger.info(f"Analyzed trends for {len(keywords)} keywords across {len(platforms)} platforms")
            return trends

        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return []

    async def get_trending_topics(self, platform: PlatformType, limit: int = 10) -> list[str]:
        """Get trending topics for a specific platform."""
        try:
            # This would integrate with platform APIs to get trending topics
            # For now, return mock trending topics
            trending_topics = [
                "AI technology",
                "climate change",
                "space exploration",
                "cryptocurrency",
                "sustainable energy",
                "virtual reality",
                "quantum computing",
                "renewable resources",
                "autonomous vehicles",
                "biotechnology",
            ]

            return trending_topics[:limit]

        except Exception as e:
            logger.error(f"Failed to get trending topics for {platform.value}: {e}")
            return []

    async def get_sentiment_analysis(self, content: SocialContent) -> tuple[SentimentType, float]:
        """Perform sentiment analysis on content."""
        try:
            # This would integrate with a sentiment analysis service
            # For now, use a simple heuristic based on keywords

            positive_keywords = [
                "good",
                "great",
                "excellent",
                "amazing",
                "love",
                "best",
                "awesome",
                "fantastic",
            ]
            negative_keywords = [
                "bad",
                "terrible",
                "awful",
                "hate",
                "worst",
                "horrible",
                "disgusting",
                "angry",
            ]

            text_lower = content.text_content.lower()

            positive_count = sum(1 for word in positive_keywords if word in text_lower)
            negative_count = sum(1 for word in negative_keywords if word in text_lower)

            if positive_count > negative_count:
                sentiment = SentimentType.POSITIVE
                score = min(1.0, 0.5 + positive_count * 0.1)
            elif negative_count > positive_count:
                sentiment = SentimentType.NEGATIVE
                score = max(-1.0, -0.5 - negative_count * 0.1)
            else:
                sentiment = SentimentType.NEUTRAL
                score = 0.0

            self.monitoring_stats["sentiment_analysis_count"] += 1

            return sentiment, score

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return SentimentType.NEUTRAL, 0.0

    async def get_cross_platform_analytics(self, keywords: list[str]) -> dict[str, Any]:
        """Get cross-platform analytics for keywords."""
        try:
            analytics: dict[str, Any] = {
                "keywords": keywords,
                "platform_distribution": {},
                "sentiment_summary": {},
                "engagement_summary": {},
                "top_content": [],
                "influential_authors": [],
                "geographic_distribution": {},
                "temporal_analysis": {},
            }

            for keyword in keywords:
                platform_data = {}
                sentiment_data = {}
                engagement_data = {}

                for platform in PlatformType:
                    # Get content for this keyword and platform
                    platform_content = [
                        content
                        for content in self.content_cache.values()
                        if keyword.lower() in content.text_content.lower() and content.platform == platform
                    ]

                    if platform_content:
                        platform_data[platform.value] = len(platform_content)

                        # Sentiment analysis
                        sentiment_counts = dict.fromkeys(SentimentType, 0)
                        total_sentiment_score = 0.0

                        for content in platform_content:
                            sentiment_counts[content.sentiment] += 1
                            total_sentiment_score += content.sentiment_score

                        sentiment_data[platform.value] = {
                            "distribution": {k.value: v for k, v in sentiment_counts.items()},
                            "average_score": total_sentiment_score / len(platform_content) if platform_content else 0.0,
                        }

                        # Engagement analysis
                        total_engagement = sum(sum(c.engagement_metrics.values()) for c in platform_content)
                        avg_engagement = total_engagement / len(platform_content) if platform_content else 0

                        engagement_data[platform.value] = {
                            "total_engagement": total_engagement,
                            "average_engagement": avg_engagement,
                            "high_engagement_count": len([c for c in platform_content if c.is_highly_engaged]),
                        }

                analytics["platform_distribution"][keyword] = platform_data
                analytics["sentiment_summary"][keyword] = sentiment_data
                analytics["engagement_summary"][keyword] = engagement_data

            return analytics

        except Exception as e:
            logger.error(f"Cross-platform analytics failed: {e}")
            return {}

    async def _start_monitoring(self, rule: MonitoringRule) -> None:
        """Start monitoring for a rule."""
        try:

            async def monitor_task() -> None:
                while True:
                    try:
                        # Simulate content discovery
                        await self._discover_content(rule)
                        await asyncio.sleep(60)  # Check every minute
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Monitoring error for rule {rule.rule_id}: {e}")
                        await asyncio.sleep(300)  # Wait 5 minutes on error

            task = asyncio.create_task(monitor_task())
            self.active_monitors[rule.rule_id] = task

        except Exception as e:
            logger.error(f"Failed to start monitoring for rule {rule.rule_id}: {e}")

    async def _discover_content(self, rule: MonitoringRule) -> None:
        """Discover content matching the rule."""
        try:
            # This would integrate with platform APIs to discover content
            # For now, simulate content discovery

            for keyword in rule.keywords:
                for platform in rule.platforms:
                    # Simulate finding content
                    content = SocialContent(
                        content_id=f"mock_{int(time.time())}_{hash(keyword)}",
                        platform=platform,
                        content_type=ContentType.POST,
                        author_id=f"author_{hash(keyword)}",
                        author_name=f"User_{hash(keyword) % 1000}",
                        text_content=f"Mock content about {keyword}",
                        hashtags=[keyword],
                        engagement_metrics={
                            "likes": np.random.randint(0, 1000),
                            "shares": np.random.randint(0, 100),
                            "comments": np.random.randint(0, 50),
                        },
                        timestamp=time.time() - np.random.uniform(0, 3600),  # Within last hour
                    )

                    # Perform sentiment analysis
                    sentiment, score = await self.get_sentiment_analysis(content)
                    content.sentiment = sentiment
                    content.sentiment_score = score

                    # Calculate relevance score
                    content.relevance_score = await self._calculate_relevance_score(content, rule)

                    # Cache content
                    self.content_cache[content.content_id] = content
                    self.monitoring_stats["total_content_processed"] += 1

        except Exception as e:
            logger.error(f"Content discovery failed for rule {rule.rule_id}: {e}")

    async def _calculate_relevance_score(self, content: SocialContent, rule: MonitoringRule) -> float:
        """Calculate relevance score for content."""
        try:
            score = 0.0

            # Keyword match bonus
            text_lower = content.text_content.lower()
            keyword_matches = sum(1 for keyword in rule.keywords if keyword.lower() in text_lower)
            score += keyword_matches * 0.3

            # Engagement bonus
            total_engagement = sum(content.engagement_metrics.values())
            if total_engagement > 100:
                score += 0.2
            if total_engagement > 1000:
                score += 0.3

            # Recency bonus
            if content.is_recent(1):  # Within last hour
                score += 0.2

            # Sentiment alignment bonus
            if rule.sentiment_filter and content.sentiment == rule.sentiment_filter:
                score += 0.2

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Relevance score calculation failed: {e}")
            return 0.0

    async def _analyze_keyword_trend(self, keyword: str, platform: PlatformType) -> TrendData | None:
        """Analyze trend for a specific keyword and platform."""
        try:
            # Get content for this keyword and platform
            keyword_content = [
                content
                for content in self.content_cache.values()
                if keyword.lower() in content.text_content.lower() and content.platform == platform
            ]

            if not keyword_content:
                return None

            # Calculate current and previous volume
            current_time = time.time()
            current_content = [c for c in keyword_content if c.timestamp > current_time - 3600]  # Last hour
            previous_content = [c for c in keyword_content if 3600 < current_time - c.timestamp < 7200]  # Hour before

            current_volume = len(current_content)
            previous_volume = len(previous_content)

            # Calculate growth rate
            if previous_volume > 0:
                growth_rate = (current_volume - previous_volume) / previous_volume
            else:
                growth_rate = 1.0 if current_volume > 0 else 0.0

            # Analyze sentiment distribution
            sentiment_distribution = dict.fromkeys(SentimentType, 0)
            for content in current_content:
                sentiment_distribution[content.sentiment] += 1

            # Get top content
            top_content = sorted(current_content, key=lambda x: x.relevance_score, reverse=True)[:5]

            # Extract trending hashtags
            trending_hashtags = []
            hashtag_counts: dict[str, int] = {}
            for content in current_content:
                for hashtag in content.hashtags:
                    hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1

            trending_hashtags = [
                tag for tag, count in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Get influential authors
            author_counts: dict[str, int] = {}
            for content in current_content:
                author_counts[content.author_id] = author_counts.get(content.author_id, 0) + 1

            influential_authors = [
                author for author, count in sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ]

            # Determine trend direction
            if growth_rate > 0.5:
                trend_direction = TrendDirection.RISING
            elif growth_rate < -0.3:
                trend_direction = TrendDirection.FALLING
            elif abs(growth_rate) < 0.1:
                trend_direction = TrendDirection.STABLE
            else:
                trend_direction = TrendDirection.VOLATILE

            # Calculate confidence score
            confidence_score = min(1.0, (current_volume / 100) + (abs(growth_rate) * 0.5))

            trend = TrendData(
                keyword=keyword,
                platform=platform,
                current_volume=current_volume,
                previous_volume=previous_volume,
                growth_rate=growth_rate,
                sentiment_distribution=sentiment_distribution,
                top_content=top_content,
                trending_hashtags=trending_hashtags,
                influential_authors=influential_authors,
                geographic_distribution={},  # Would be populated with real data
                confidence_score=confidence_score,
                trend_direction=trend_direction,
            )

            # Cache trend data
            trend_key = f"{keyword}_{platform.value}"
            self.trend_data[trend_key] = trend

            return trend

        except Exception as e:
            logger.error(f"Trend analysis failed for {keyword} on {platform.value}: {e}")
            return None

    async def get_monitoring_statistics(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        return self.monitoring_stats.copy()

    async def clear_cache(self) -> None:
        """Clear content cache."""
        self.content_cache.clear()
        self.trend_data.clear()
        logger.info("Social monitor cache cleared")

    async def __aenter__(self) -> "SocialMonitor":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        # Cancel all active monitoring tasks
        for task in self.active_monitors.values():
            task.cancel()

        await asyncio.gather(*self.active_monitors.values(), return_exceptions=True)
        await self.clear_cache()
