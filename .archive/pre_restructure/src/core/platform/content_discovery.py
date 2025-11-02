"""
Content discovery and aggregation system for the Ultimate Discord Intelligence Bot.

Provides intelligent content discovery, aggregation, and recommendation capabilities
across multiple social media platforms with advanced filtering and ranking.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

from .social_monitor import ContentType, PlatformType, SentimentType, SocialContent


logger = logging.getLogger(__name__)


class DiscoveryStrategy(Enum):
    """Content discovery strategies."""

    KEYWORD_BASED = "keyword_based"
    TREND_FOLLOWING = "trend_following"
    INFLUENCER_TRACKING = "influencer_tracking"
    SENTIMENT_DRIVEN = "sentiment_driven"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"
    HYBRID = "hybrid"


class ContentRankingMethod(Enum):
    """Content ranking methods."""

    RELEVANCE = "relevance"
    ENGAGEMENT = "engagement"
    RECENCY = "recency"
    AUTHORITY = "authority"
    DIVERSITY = "diversity"
    QUALITY = "quality"


class AggregationMode(Enum):
    """Content aggregation modes."""

    REAL_TIME = "real_time"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"


@dataclass
class DiscoveryQuery:
    """Content discovery query."""

    query_id: str
    keywords: list[str]
    platforms: list[PlatformType]
    content_types: list[ContentType] = field(default_factory=list)
    sentiment_filter: SentimentType | None = None
    min_engagement: int = 0
    max_age_hours: int = 24
    languages: list[str] = field(default_factory=lambda: ["en"])
    geographic_regions: list[str] = field(default_factory=list)
    author_filters: list[str] = field(default_factory=list)
    hashtag_filters: list[str] = field(default_factory=list)
    discovery_strategy: DiscoveryStrategy = DiscoveryStrategy.HYBRID
    ranking_method: ContentRankingMethod = ContentRankingMethod.RELEVANCE
    max_results: int = 100
    diversity_threshold: float = 0.7
    quality_threshold: float = 0.6
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complex(self) -> bool:
        """Check if query is complex."""
        return (
            len(self.keywords) > 5
            or len(self.platforms) > 3
            or len(self.content_types) > 2
            or self.sentiment_filter is not None
            or len(self.geographic_regions) > 2
            or len(self.author_filters) > 3
            or len(self.hashtag_filters) > 5
        )


@dataclass
class ContentCluster:
    """Cluster of related content."""

    cluster_id: str
    content_items: list[SocialContent]
    cluster_theme: str
    similarity_score: float
    engagement_summary: dict[str, int]
    sentiment_summary: dict[SentimentType, int]
    top_keywords: list[str]
    representative_content: SocialContent
    cluster_size: int
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_significant(self) -> bool:
        """Check if cluster is significant."""
        total_engagement = sum(self.engagement_summary.values())
        return self.cluster_size >= 3 and total_engagement > 500

    @property
    def dominant_sentiment(self) -> SentimentType:
        """Get dominant sentiment in cluster."""
        if not self.sentiment_summary:
            return SentimentType.NEUTRAL

        return max(self.sentiment_summary.items(), key=lambda x: x[1])[0]


@dataclass
class DiscoveryResult:
    """Result of content discovery operation."""

    query_id: str
    content_items: list[SocialContent]
    clusters: list[ContentCluster]
    total_matches: int
    filtered_matches: int
    discovery_time: float
    ranking_time: float
    clustering_time: float
    quality_scores: dict[str, float]
    diversity_scores: dict[str, float]
    recommendations: list[SocialContent]
    trending_keywords: list[str]
    influential_authors: list[str]
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate discovery success rate."""
        if self.total_matches == 0:
            return 0.0
        return self.filtered_matches / self.total_matches

    @property
    def average_quality(self) -> float:
        """Calculate average content quality."""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores.values()) / len(self.quality_scores)


class ContentDiscovery:
    """
    Advanced content discovery and aggregation system.

    Provides intelligent content discovery, clustering, ranking, and recommendation
    capabilities across multiple social media platforms.
    """

    def __init__(self):
        """Initialize content discovery system."""
        self.active_queries: dict[str, DiscoveryQuery] = {}
        self.content_index: dict[str, SocialContent] = {}
        self.cluster_cache: dict[str, list[ContentCluster]] = {}

        # Discovery statistics
        self.discovery_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "total_content_discovered": 0,
            "clusters_created": 0,
            "average_discovery_time": 0.0,
            "average_quality_score": 0.0,
        }

        # Ranking weights
        self.ranking_weights = {
            ContentRankingMethod.RELEVANCE: {
                "relevance": 0.4,
                "engagement": 0.3,
                "recency": 0.2,
                "authority": 0.1,
            },
            ContentRankingMethod.ENGAGEMENT: {
                "engagement": 0.5,
                "relevance": 0.2,
                "recency": 0.2,
                "authority": 0.1,
            },
            ContentRankingMethod.RECENCY: {
                "recency": 0.5,
                "relevance": 0.2,
                "engagement": 0.2,
                "authority": 0.1,
            },
            ContentRankingMethod.AUTHORITY: {
                "authority": 0.4,
                "relevance": 0.3,
                "engagement": 0.2,
                "recency": 0.1,
            },
            ContentRankingMethod.DIVERSITY: {
                "diversity": 0.4,
                "relevance": 0.3,
                "engagement": 0.2,
                "recency": 0.1,
            },
            ContentRankingMethod.QUALITY: {
                "quality": 0.5,
                "relevance": 0.2,
                "engagement": 0.2,
                "authority": 0.1,
            },
        }

        logger.info("Content discovery system initialized")

    async def discover_content(self, query: DiscoveryQuery) -> DiscoveryResult:
        """Discover content based on query."""
        time.time()

        try:
            self.discovery_stats["total_queries"] += 1

            # Store active query
            self.active_queries[query.query_id] = query

            # Discover content
            discovery_start = time.time()
            raw_content = await self._discover_raw_content(query)
            discovery_time = time.time() - discovery_start

            # Filter content
            filtered_content = await self._filter_content(raw_content, query)

            # Rank content
            ranking_start = time.time()
            ranked_content = await self._rank_content(filtered_content, query)
            ranking_time = time.time() - ranking_start

            # Cluster content
            clustering_start = time.time()
            clusters = await self._cluster_content(ranked_content, query)
            clustering_time = time.time() - clustering_start

            # Calculate quality and diversity scores
            quality_scores = await self._calculate_quality_scores(ranked_content)
            diversity_scores = await self._calculate_diversity_scores(ranked_content)

            # Generate recommendations
            recommendations = await self._generate_recommendations(ranked_content, query)

            # Extract trending keywords and influential authors
            trending_keywords = await self._extract_trending_keywords(ranked_content)
            influential_authors = await self._extract_influential_authors(ranked_content)

            # Create result
            result = DiscoveryResult(
                query_id=query.query_id,
                content_items=ranked_content,
                clusters=clusters,
                total_matches=len(raw_content),
                filtered_matches=len(filtered_content),
                discovery_time=discovery_time,
                ranking_time=ranking_time,
                clustering_time=clustering_time,
                quality_scores=quality_scores,
                diversity_scores=diversity_scores,
                recommendations=recommendations,
                trending_keywords=trending_keywords,
                influential_authors=influential_authors,
            )

            # Update statistics
            self._update_discovery_stats(result)

            logger.info(
                f"Content discovery completed for query {query.query_id}: "
                f"{len(ranked_content)} items, {len(clusters)} clusters"
            )

            return result

        except Exception as e:
            logger.error(f"Content discovery failed for query {query.query_id}: {e}")
            return DiscoveryResult(
                query_id=query.query_id,
                content_items=[],
                clusters=[],
                total_matches=0,
                filtered_matches=0,
                discovery_time=0.0,
                ranking_time=0.0,
                clustering_time=0.0,
                quality_scores={},
                diversity_scores={},
                recommendations=[],
                trending_keywords=[],
                influential_authors=[],
            )

    async def get_content_recommendations(self, user_profile: dict[str, Any], limit: int = 20) -> list[SocialContent]:
        """Get personalized content recommendations."""
        try:
            # This would use user profile data to generate recommendations
            # For now, return high-quality content from the index

            recommendations = []

            for content in self.content_index.values():
                if content.relevance_score > 0.7 and content.is_highly_engaged:
                    recommendations.append(content)

            # Sort by relevance and engagement
            recommendations.sort(
                key=lambda x: (x.relevance_score, sum(x.engagement_metrics.values())),
                reverse=True,
            )

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Content recommendations failed: {e}")
            return []

    async def track_content_performance(self, content_id: str, duration_hours: int = 24) -> dict[str, Any]:
        """Track performance of specific content over time."""
        try:
            if content_id not in self.content_index:
                logger.warning(f"Content {content_id} not found in index")
                return {}

            content = self.content_index[content_id]

            # Simulate performance tracking
            performance_data = {
                "content_id": content_id,
                "initial_engagement": sum(content.engagement_metrics.values()),
                "engagement_growth": [],
                "sentiment_evolution": [],
                "reach_metrics": [],
                "interaction_rates": [],
                "peak_performance_time": None,
                "total_performance_score": 0.0,
            }

            # Simulate hourly performance updates
            for hour in range(duration_hours):
                # Simulate engagement growth
                growth_factor = np.random.uniform(0.8, 1.5)
                current_engagement = int(sum(content.engagement_metrics.values()) * (growth_factor**hour))
                performance_data["engagement_growth"].append(current_engagement)

                # Simulate sentiment evolution
                sentiment_variation = np.random.uniform(-0.2, 0.2)
                current_sentiment = max(-1.0, min(1.0, content.sentiment_score + sentiment_variation))
                performance_data["sentiment_evolution"].append(current_sentiment)

                # Simulate reach metrics
                reach = int(current_engagement * np.random.uniform(2, 10))
                performance_data["reach_metrics"].append(reach)

                # Simulate interaction rates
                interaction_rate = np.random.uniform(0.02, 0.08)
                performance_data["interaction_rates"].append(interaction_rate)

            # Find peak performance time
            max_engagement = max(performance_data["engagement_growth"])
            peak_index = performance_data["engagement_growth"].index(max_engagement)
            performance_data["peak_performance_time"] = peak_index

            # Calculate total performance score
            avg_engagement = sum(performance_data["engagement_growth"]) / len(performance_data["engagement_growth"])
            avg_sentiment = sum(performance_data["sentiment_evolution"]) / len(performance_data["sentiment_evolution"])
            avg_reach = sum(performance_data["reach_metrics"]) / len(performance_data["reach_metrics"])

            performance_score = (
                (avg_engagement / 1000) * 0.4 + (avg_sentiment + 1) / 2 * 0.3 + (avg_reach / 10000) * 0.3
            )
            performance_data["total_performance_score"] = min(1.0, performance_score)

            return performance_data

        except Exception as e:
            logger.error(f"Content performance tracking failed for {content_id}: {e}")
            return {}

    async def analyze_content_trends(self, time_window_hours: int = 24) -> dict[str, Any]:
        """Analyze content trends over a time window."""
        try:
            current_time = time.time()
            time_threshold = current_time - (time_window_hours * 3600)

            # Get recent content
            recent_content = [content for content in self.content_index.values() if content.timestamp > time_threshold]

            if not recent_content:
                return {}

            # Analyze trends
            trend_analysis = {
                "time_window_hours": time_window_hours,
                "total_content": len(recent_content),
                "platform_distribution": {},
                "content_type_distribution": {},
                "sentiment_distribution": {},
                "engagement_trends": {},
                "keyword_frequency": {},
                "hashtag_trends": {},
                "author_activity": {},
                "temporal_patterns": {},
            }

            # Platform distribution
            for platform in PlatformType:
                count = len([c for c in recent_content if c.platform == platform])
                if count > 0:
                    trend_analysis["platform_distribution"][platform.value] = count

            # Content type distribution
            for content_type in ContentType:
                count = len([c for c in recent_content if c.content_type == content_type])
                if count > 0:
                    trend_analysis["content_type_distribution"][content_type.value] = count

            # Sentiment distribution
            for sentiment in SentimentType:
                count = len([c for c in recent_content if c.sentiment == sentiment])
                if count > 0:
                    trend_analysis["sentiment_distribution"][sentiment.value] = count

            # Engagement trends
            engagement_buckets = {"low": 0, "medium": 0, "high": 0}
            for content in recent_content:
                total_engagement = sum(content.engagement_metrics.values())
                if total_engagement < 100:
                    engagement_buckets["low"] += 1
                elif total_engagement < 1000:
                    engagement_buckets["medium"] += 1
                else:
                    engagement_buckets["high"] += 1

            trend_analysis["engagement_trends"] = engagement_buckets

            # Keyword frequency
            keyword_counts = {}
            for content in recent_content:
                words = content.text_content.lower().split()
                for word in words:
                    if len(word) > 3:  # Ignore short words
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Get top keywords
            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            trend_analysis["keyword_frequency"] = dict(top_keywords)

            # Hashtag trends
            hashtag_counts = {}
            for content in recent_content:
                for hashtag in content.hashtags:
                    hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1

            # Get top hashtags
            top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:15]
            trend_analysis["hashtag_trends"] = dict(top_hashtags)

            # Author activity
            author_counts = {}
            for content in recent_content:
                author_counts[content.author_id] = author_counts.get(content.author_id, 0) + 1

            # Get most active authors
            top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            trend_analysis["author_activity"] = dict(top_authors)

            # Temporal patterns (hourly distribution)
            hourly_distribution = {}
            for content in recent_content:
                hour = int((current_time - content.timestamp) / 3600)
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1

            trend_analysis["temporal_patterns"] = hourly_distribution

            return trend_analysis

        except Exception as e:
            logger.error(f"Content trend analysis failed: {e}")
            return {}

    async def _discover_raw_content(self, query: DiscoveryQuery) -> list[SocialContent]:
        """Discover raw content based on query."""
        try:
            # This would integrate with platform APIs
            # For now, simulate content discovery

            raw_content = []

            for keyword in query.keywords:
                for platform in query.platforms:
                    # Simulate finding content
                    for i in range(np.random.randint(5, 20)):
                        content = SocialContent(
                            content_id=f"discovered_{int(time.time())}_{hash(keyword)}_{i}",
                            platform=platform,
                            content_type=np.random.choice(list(ContentType)),
                            author_id=f"author_{hash(keyword)}_{i}",
                            author_name=f"User_{hash(keyword + str(i)) % 1000}",
                            text_content=f"Sample content about {keyword} with additional context",
                            hashtags=[keyword, f"#{keyword}"],
                            engagement_metrics={
                                "likes": np.random.randint(0, 5000),
                                "shares": np.random.randint(0, 500),
                                "comments": np.random.randint(0, 200),
                            },
                            timestamp=time.time() - np.random.uniform(0, query.max_age_hours * 3600),
                            language=query.languages[0] if query.languages else "en",
                        )

                        # Calculate relevance score
                        content.relevance_score = await self._calculate_content_relevance(content, query)

                        # Add to index
                        self.content_index[content.content_id] = content
                        raw_content.append(content)

            return raw_content

        except Exception as e:
            logger.error(f"Raw content discovery failed: {e}")
            return []

    async def _filter_content(self, content: list[SocialContent], query: DiscoveryQuery) -> list[SocialContent]:
        """Filter content based on query criteria."""
        try:
            filtered_content = []

            for item in content:
                # Age filter
                if item.timestamp < time.time() - (query.max_age_hours * 3600):
                    continue

                # Language filter
                if item.language not in query.languages:
                    continue

                # Engagement filter
                total_engagement = sum(item.engagement_metrics.values())
                if total_engagement < query.min_engagement:
                    continue

                # Content type filter
                if query.content_types and item.content_type not in query.content_types:
                    continue

                # Sentiment filter
                if query.sentiment_filter and item.sentiment != query.sentiment_filter:
                    continue

                # Author filter
                if query.author_filters and item.author_id not in query.author_filters:
                    continue

                # Hashtag filter
                if query.hashtag_filters and not any(tag in item.hashtags for tag in query.hashtag_filters):
                    continue

                # Quality threshold
                if item.relevance_score < query.quality_threshold:
                    continue

                filtered_content.append(item)

            return filtered_content

        except Exception as e:
            logger.error(f"Content filtering failed: {e}")
            return content

    async def _rank_content(self, content: list[SocialContent], query: DiscoveryQuery) -> list[SocialContent]:
        """Rank content based on query ranking method."""
        try:
            ranking_method = query.ranking_method
            weights = self.ranking_weights.get(ranking_method, self.ranking_weights[ContentRankingMethod.RELEVANCE])

            for item in content:
                # Calculate ranking score
                relevance_score = item.relevance_score
                engagement_score = await self._calculate_engagement_score(item)
                recency_score = await self._calculate_recency_score(item)
                authority_score = await self._calculate_authority_score(item)
                diversity_score = await self._calculate_diversity_score(item, content)
                quality_score = await self._calculate_quality_score(item)

                # Apply weights
                ranking_score = (
                    relevance_score * weights.get("relevance", 0.4)
                    + engagement_score * weights.get("engagement", 0.3)
                    + recency_score * weights.get("recency", 0.2)
                    + authority_score * weights.get("authority", 0.1)
                    + diversity_score * weights.get("diversity", 0.0)
                    + quality_score * weights.get("quality", 0.0)
                )

                # Store ranking score in metadata
                item.metadata["ranking_score"] = ranking_score

            # Sort by ranking score
            ranked_content = sorted(content, key=lambda x: x.metadata.get("ranking_score", 0), reverse=True)

            return ranked_content[: query.max_results]

        except Exception as e:
            logger.error(f"Content ranking failed: {e}")
            return content

    async def _cluster_content(self, content: list[SocialContent], query: DiscoveryQuery) -> list[ContentCluster]:
        """Cluster related content."""
        try:
            if len(content) < 3:
                return []

            clusters = []
            used_content = set()

            for i, content_item in enumerate(content):
                if content_item.content_id in used_content:
                    continue

                # Find similar content
                cluster_items = [content_item]
                used_content.add(content_item.content_id)

                for _j, other_item in enumerate(content[i + 1 :], i + 1):
                    if other_item.content_id in used_content:
                        continue

                    similarity = await self._calculate_content_similarity(content_item, other_item)
                    if similarity > 0.7:  # Similarity threshold
                        cluster_items.append(other_item)
                        used_content.add(other_item.content_id)

                # Create cluster if significant
                if len(cluster_items) >= 2:
                    cluster = await self._create_content_cluster(cluster_items, query)
                    if cluster:
                        clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"Content clustering failed: {e}")
            return []

    async def _create_content_cluster(
        self, content_items: list[SocialContent], query: DiscoveryQuery
    ) -> ContentCluster | None:
        """Create a content cluster from items."""
        try:
            if len(content_items) < 2:
                return None

            cluster_id = f"cluster_{int(time.time())}_{hash(str(content_items[0].content_id))}"

            # Calculate similarity score
            similarity_scores = []
            for i in range(len(content_items)):
                for j in range(i + 1, len(content_items)):
                    similarity = await self._calculate_content_similarity(content_items[i], content_items[j])
                    similarity_scores.append(similarity)

            avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0

            # Determine cluster theme
            theme = await self._determine_cluster_theme(content_items)

            # Calculate engagement summary
            engagement_summary = {}
            for item in content_items:
                for metric, value in item.engagement_metrics.items():
                    engagement_summary[metric] = engagement_summary.get(metric, 0) + value

            # Calculate sentiment summary
            sentiment_summary = dict.fromkeys(SentimentType, 0)
            for item in content_items:
                sentiment_summary[item.sentiment] += 1

            # Extract top keywords
            keyword_counts = {}
            for item in content_items:
                words = item.text_content.lower().split()
                for word in words:
                    if len(word) > 3:
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1

            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_keywords = [word for word, count in top_keywords]

            # Find representative content (highest engagement)
            representative_content = max(content_items, key=lambda x: sum(x.engagement_metrics.values()))

            cluster = ContentCluster(
                cluster_id=cluster_id,
                content_items=content_items,
                cluster_theme=theme,
                similarity_score=avg_similarity,
                engagement_summary=engagement_summary,
                sentiment_summary=sentiment_summary,
                top_keywords=top_keywords,
                representative_content=representative_content,
                cluster_size=len(content_items),
            )

            return cluster

        except Exception as e:
            logger.error(f"Cluster creation failed: {e}")
            return None

    async def _calculate_content_relevance(self, content: SocialContent, query: DiscoveryQuery) -> float:
        """Calculate content relevance to query."""
        try:
            score = 0.0

            # Keyword match
            text_lower = content.text_content.lower()
            keyword_matches = sum(1 for keyword in query.keywords if keyword.lower() in text_lower)
            score += keyword_matches * 0.3

            # Hashtag match
            hashtag_matches = sum(1 for keyword in query.keywords if keyword in content.hashtags)
            score += hashtag_matches * 0.4

            # Platform relevance
            if content.platform in query.platforms:
                score += 0.2

            # Content type relevance
            if not query.content_types or content.content_type in query.content_types:
                score += 0.1

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Relevance calculation failed: {e}")
            return 0.0

    async def _calculate_engagement_score(self, content: SocialContent) -> float:
        """Calculate engagement score."""
        try:
            total_engagement = sum(content.engagement_metrics.values())
            return min(1.0, total_engagement / 10000)  # Normalize to 0-1

        except Exception as e:
            logger.error(f"Engagement score calculation failed: {e}")
            return 0.0

    async def _calculate_recency_score(self, content: SocialContent) -> float:
        """Calculate recency score."""
        try:
            age_hours = (time.time() - content.timestamp) / 3600
            return max(0.0, 1.0 - (age_hours / 24))  # Decay over 24 hours

        except Exception as e:
            logger.error(f"Recency score calculation failed: {e}")
            return 0.0

    async def _calculate_authority_score(self, content: SocialContent) -> float:
        """Calculate author authority score."""
        try:
            # This would use author metrics from platform APIs
            # For now, use engagement as proxy for authority
            total_engagement = sum(content.engagement_metrics.values())
            return min(1.0, total_engagement / 5000)

        except Exception as e:
            logger.error(f"Authority score calculation failed: {e}")
            return 0.0

    async def _calculate_diversity_score(self, content: SocialContent, all_content: list[SocialContent]) -> float:
        """Calculate diversity score."""
        try:
            # Calculate how different this content is from others
            similarities = []
            for other in all_content:
                if other.content_id != content.content_id:
                    similarity = await self._calculate_content_similarity(content, other)
                    similarities.append(similarity)

            if not similarities:
                return 1.0

            avg_similarity = sum(similarities) / len(similarities)
            return 1.0 - avg_similarity  # Higher diversity = lower similarity

        except Exception as e:
            logger.error(f"Diversity score calculation failed: {e}")
            return 0.0

    async def _calculate_quality_score(self, content: SocialContent) -> float:
        """Calculate content quality score."""
        try:
            score = 0.0

            # Text quality (length, readability)
            text_length = len(content.text_content)
            if 50 <= text_length <= 1000:
                score += 0.3

            # Engagement rate
            if content.is_highly_engaged:
                score += 0.4

            # Hashtag usage
            if 1 <= len(content.hashtags) <= 5:
                score += 0.2

            # Media presence
            if content.media_urls:
                score += 0.1

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return 0.0

    async def _calculate_content_similarity(self, content1: SocialContent, content2: SocialContent) -> float:
        """Calculate similarity between two content items."""
        try:
            # Simple similarity based on text overlap
            words1 = set(content1.text_content.lower().split())
            words2 = set(content2.text_content.lower().split())

            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            return len(intersection) / len(union)

        except Exception as e:
            logger.error(f"Content similarity calculation failed: {e}")
            return 0.0

    async def _determine_cluster_theme(self, content_items: list[SocialContent]) -> str:
        """Determine the theme of a content cluster."""
        try:
            # Extract common keywords
            all_words = []
            for item in content_items:
                words = item.text_content.lower().split()
                all_words.extend([word for word in words if len(word) > 3])

            word_counts = {}
            for word in all_words:
                word_counts[word] = word_counts.get(word, 0) + 1

            # Get most common words
            common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            theme = " ".join([word for word, count in common_words])

            return theme or "General Content"

        except Exception as e:
            logger.error(f"Cluster theme determination failed: {e}")
            return "General Content"

    async def _calculate_quality_scores(self, content: list[SocialContent]) -> dict[str, float]:
        """Calculate quality scores for content."""
        try:
            quality_scores = {}
            for item in content:
                score = await self._calculate_quality_score(item)
                quality_scores[item.content_id] = score

            return quality_scores

        except Exception as e:
            logger.error(f"Quality scores calculation failed: {e}")
            return {}

    async def _calculate_diversity_scores(self, content: list[SocialContent]) -> dict[str, float]:
        """Calculate diversity scores for content."""
        try:
            diversity_scores = {}
            for item in content:
                score = await self._calculate_diversity_score(item, content)
                diversity_scores[item.content_id] = score

            return diversity_scores

        except Exception as e:
            logger.error(f"Diversity scores calculation failed: {e}")
            return {}

    async def _generate_recommendations(
        self, content: list[SocialContent], query: DiscoveryQuery
    ) -> list[SocialContent]:
        """Generate content recommendations."""
        try:
            # Return top content as recommendations
            return content[: min(10, len(content))]

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return []

    async def _extract_trending_keywords(self, content: list[SocialContent]) -> list[str]:
        """Extract trending keywords from content."""
        try:
            keyword_counts = {}
            for item in content:
                words = item.text_content.lower().split()
                for word in words:
                    if len(word) > 3:
                        keyword_counts[word] = keyword_counts.get(word, 0) + 1

            trending_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            return [word for word, count in trending_keywords]

        except Exception as e:
            logger.error(f"Trending keywords extraction failed: {e}")
            return []

    async def _extract_influential_authors(self, content: list[SocialContent]) -> list[str]:
        """Extract influential authors from content."""
        try:
            author_engagement = {}
            for item in content:
                total_engagement = sum(item.engagement_metrics.values())
                author_engagement[item.author_id] = author_engagement.get(item.author_id, 0) + total_engagement

            influential_authors = sorted(author_engagement.items(), key=lambda x: x[1], reverse=True)[:10]
            return [author for author, engagement in influential_authors]

        except Exception as e:
            logger.error(f"Influential authors extraction failed: {e}")
            return []

    def _update_discovery_stats(self, result: DiscoveryResult) -> None:
        """Update discovery statistics."""
        try:
            self.discovery_stats["successful_queries"] += 1
            self.discovery_stats["total_content_discovered"] += len(result.content_items)
            self.discovery_stats["clusters_created"] += len(result.clusters)

            # Update average discovery time
            total_queries = self.discovery_stats["total_queries"]
            current_avg = self.discovery_stats["average_discovery_time"]
            new_avg = (current_avg * (total_queries - 1) + result.discovery_time) / total_queries
            self.discovery_stats["average_discovery_time"] = new_avg

            # Update average quality score
            if result.quality_scores:
                avg_quality = sum(result.quality_scores.values()) / len(result.quality_scores)
                total_queries = self.discovery_stats["total_queries"]
                current_avg_quality = self.discovery_stats["average_quality_score"]
                new_avg_quality = (current_avg_quality * (total_queries - 1) + avg_quality) / total_queries
                self.discovery_stats["average_quality_score"] = new_avg_quality

        except Exception as e:
            logger.error(f"Discovery stats update failed: {e}")

    async def get_discovery_statistics(self) -> dict[str, Any]:
        """Get discovery statistics."""
        return self.discovery_stats.copy()

    async def clear_cache(self) -> None:
        """Clear discovery cache."""
        self.content_index.clear()
        self.cluster_cache.clear()
        logger.info("Content discovery cache cleared")

    async def __aenter__(self) -> "ContentDiscovery":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.clear_cache()
