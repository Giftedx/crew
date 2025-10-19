"""
Content recommendation tool for AI-driven content discovery and curation.

This tool provides comprehensive content recommendation including:
- AI-driven content discovery and curation
- Personalized content recommendations
- Topic clustering and categorization
- Content similarity scoring
- Trending content identification
"""

import logging
import time
from collections import defaultdict
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


class UserProfile(TypedDict, total=False):
    """User profile for personalized recommendations."""

    user_id: str
    interests: list[str]
    demographics: dict[str, Any]
    behavior_history: list[dict[str, Any]]
    engagement_patterns: dict[str, Any]
    platform_preferences: dict[str, float]
    content_preferences: dict[str, float]


class RecommendationContext(TypedDict, total=False):
    """Context for content recommendations."""

    user_profile: UserProfile | None
    current_trends: list[str]
    platform: str
    content_type: str
    time_context: dict[str, Any]
    social_context: dict[str, Any]


class ContentRecommendation(TypedDict, total=False):
    """Individual content recommendation result."""

    content_id: str
    title: str
    description: str
    platform: str
    content_type: str
    relevance_score: float
    engagement_prediction: float
    trending_score: float
    personalization_score: float
    overall_score: float
    recommendation_reasons: list[str]
    metadata: dict[str, Any]


class ContentCluster(TypedDict, total=False):
    """Content cluster for categorization."""

    cluster_id: str
    cluster_name: str
    content_items: list[dict[str, Any]]
    cluster_characteristics: dict[str, Any]
    size: int
    cohesion_score: float
    representative_content: dict[str, Any]


class SimilarityScore(TypedDict, total=False):
    """Content similarity scoring result."""

    content_id_1: str
    content_id_2: str
    similarity_score: float
    similarity_factors: dict[str, float]
    shared_characteristics: list[str]
    differences: list[str]


class TrendingContent(TypedDict, total=False):
    """Trending content identification result."""

    content_id: str
    trending_score: float
    trend_category: str
    growth_rate: float
    engagement_velocity: float
    viral_potential: float
    trend_duration: float
    peak_prediction: dict[str, Any]


class ContentRecommendationResult(TypedDict, total=False):
    """Complete content recommendation result."""

    personalized_recommendations: list[ContentRecommendation]
    trending_recommendations: list[ContentRecommendation]
    similar_content: list[ContentRecommendation]
    content_clusters: list[ContentCluster]
    similarity_scores: list[SimilarityScore]
    trending_content: list[TrendingContent]
    discovery_insights: dict[str, Any]
    recommendation_quality: dict[str, Any]
    processing_time: float
    metadata: dict[str, Any]


class ContentRecommendationTool(BaseTool[StepResult]):
    """Advanced content recommendation with AI-driven discovery and personalization."""

    name: str = "Content Recommendation Tool"
    description: str = (
        "Provides AI-driven content discovery, personalized recommendations, "
        "topic clustering, similarity scoring, and trending content identification."
    )

    def __init__(
        self,
        enable_personalization: bool = True,
        enable_trending_discovery: bool = True,
        enable_similarity_analysis: bool = True,
        enable_clustering: bool = True,
        max_recommendations: int = 20,
        similarity_threshold: float = 0.7,
        personalization_weight: float = 0.4,
        trending_weight: float = 0.3,
        quality_weight: float = 0.3,
    ):
        super().__init__()
        self._enable_personalization = enable_personalization
        self._enable_trending_discovery = enable_trending_discovery
        self._enable_similarity_analysis = enable_similarity_analysis
        self._enable_clustering = enable_clustering
        self._max_recommendations = max_recommendations
        self._similarity_threshold = similarity_threshold
        self._personalization_weight = personalization_weight
        self._trending_weight = trending_weight
        self._quality_weight = quality_weight
        self._metrics = get_metrics()

    def _run(
        self,
        content_pool: list[dict[str, Any]],
        user_profile: UserProfile | None = None,
        recommendation_context: RecommendationContext | None = None,
        discovery_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        recommendation_mode: str = "comprehensive",
    ) -> StepResult:
        """
        Perform comprehensive content recommendation analysis.

        Args:
            content_pool: Pool of content to analyze and recommend from
            user_profile: User profile for personalization
            recommendation_context: Context for recommendations
            discovery_config: Configuration for discovery algorithms
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            recommendation_mode: Recommendation mode (basic, comprehensive, detailed)

        Returns:
            StepResult with comprehensive content recommendation results
        """
        start_time = time.monotonic()

        try:
            # Input validation
            if not content_pool:
                return StepResult.fail("Content pool cannot be empty")

            if tenant and workspace:
                self.note(f"Starting content recommendation for {len(content_pool)} content items")

            # Perform content recommendation analysis
            personalized_recommendations = (
                self._generate_personalized_recommendations(content_pool, user_profile)
                if self._enable_personalization
                else []
            )
            trending_recommendations = (
                self._discover_trending_content(content_pool) if self._enable_trending_discovery else []
            )
            similar_content = (
                self._find_similar_content(content_pool, recommendation_context)
                if self._enable_similarity_analysis
                else []
            )
            content_clusters = self._cluster_similar_content(content_pool) if self._enable_clustering else []
            similarity_scores = (
                self._calculate_similarity_scores(content_pool) if self._enable_similarity_analysis else []
            )
            trending_content = self._identify_trending_content(content_pool)
            discovery_insights = self._analyze_discovery_insights(
                personalized_recommendations, trending_recommendations, content_clusters
            )
            recommendation_quality = self._assess_recommendation_quality(personalized_recommendations, user_profile)

            processing_time = time.monotonic() - start_time

            result: ContentRecommendationResult = {
                "personalized_recommendations": personalized_recommendations,
                "trending_recommendations": trending_recommendations,
                "similar_content": similar_content,
                "content_clusters": content_clusters,
                "similarity_scores": similarity_scores,
                "trending_content": trending_content,
                "discovery_insights": discovery_insights,
                "recommendation_quality": recommendation_quality,
                "processing_time": processing_time,
                "metadata": {
                    "recommendation_mode": recommendation_mode,
                    "content_pool_size": len(content_pool),
                    "max_recommendations": self._max_recommendations,
                    "tenant": tenant,
                    "workspace": workspace,
                    "timestamp": time.time(),
                },
            }

            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "success"}).inc()
            self._metrics.histogram("tool_run_seconds", processing_time, labels={"tool": self.name})

            return StepResult.ok(data=result)

        except Exception as e:
            processing_time = time.monotonic() - start_time
            self._metrics.counter("tool_runs_total", labels={"tool": self.name, "outcome": "error"}).inc()
            logging.exception("Content recommendation failed")
            return StepResult.fail(f"Content recommendation failed: {str(e)}")

    def _generate_personalized_recommendations(
        self,
        content_pool: list[dict[str, Any]],
        user_profile: UserProfile | None,
    ) -> list[ContentRecommendation]:
        """Generate personalized content recommendations."""
        recommendations = []

        if not user_profile:
            # Fallback to general recommendations
            return self._generate_general_recommendations(content_pool)

        for content in content_pool:
            # Calculate personalization score
            personalization_score = self._calculate_personalization_score(content, user_profile)

            # Calculate overall recommendation score
            overall_score = self._calculate_overall_recommendation_score(content, user_profile)

            # Generate recommendation reasons
            recommendation_reasons = self._generate_recommendation_reasons(content, user_profile)

            # Create recommendation
            recommendation: ContentRecommendation = {
                "content_id": content.get("content_id", "unknown"),
                "title": content.get("title", "Untitled"),
                "description": content.get("description", ""),
                "platform": content.get("platform", "unknown"),
                "content_type": content.get("content_type", "unknown"),
                "relevance_score": self._calculate_relevance_score(content, user_profile),
                "engagement_prediction": self._predict_engagement(content, user_profile),
                "trending_score": self._calculate_trending_score(content),
                "personalization_score": personalization_score,
                "overall_score": overall_score,
                "recommendation_reasons": recommendation_reasons,
                "metadata": content.get("metadata", {}),
            }

            recommendations.append(recommendation)

        # Sort by overall score and limit results
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        return recommendations[: self._max_recommendations]

    def _discover_trending_content(self, content_pool: list[dict[str, Any]]) -> list[ContentRecommendation]:
        """Discover trending content from the pool."""
        trending_recommendations = []

        for content in content_pool:
            # Calculate trending metrics
            trending_score = self._calculate_trending_score(content)
            growth_rate = self._calculate_growth_rate(content)

            # Only include content with significant trending indicators
            if trending_score > 0.6 or growth_rate > 0.5:
                recommendation: ContentRecommendation = {
                    "content_id": content.get("content_id", "unknown"),
                    "title": content.get("title", "Untitled"),
                    "description": content.get("description", ""),
                    "platform": content.get("platform", "unknown"),
                    "content_type": content.get("content_type", "unknown"),
                    "relevance_score": trending_score,
                    "engagement_prediction": self._predict_engagement(content),
                    "trending_score": trending_score,
                    "personalization_score": 0.5,  # Neutral for trending content
                    "overall_score": trending_score,
                    "recommendation_reasons": [
                        f"Trending with {trending_score:.2f} score",
                        f"Growth rate: {growth_rate:.2f}",
                    ],
                    "metadata": content.get("metadata", {}),
                }

                trending_recommendations.append(recommendation)

        # Sort by trending score
        trending_recommendations.sort(key=lambda x: x["trending_score"], reverse=True)
        return trending_recommendations[: self._max_recommendations // 2]

    def _find_similar_content(
        self,
        content_pool: list[dict[str, Any]],
        recommendation_context: RecommendationContext | None,
    ) -> list[ContentRecommendation]:
        """Find content similar to context or user preferences."""
        similar_recommendations: list[ContentRecommendation] = []

        if not recommendation_context:
            return similar_recommendations

        # Get reference content or user preferences
        user_profile = recommendation_context.get("user_profile")
        if not user_profile:
            return similar_recommendations

        reference_content = user_profile.get("behavior_history", [])
        if not reference_content:
            return similar_recommendations

        # Find most recent or relevant content as reference
        reference_item = reference_content[-1] if reference_content else None
        if not reference_item:
            return similar_recommendations

        for content in content_pool:
            # Calculate similarity score
            similarity_score = self._calculate_content_similarity(content, reference_item)

            if similarity_score >= self._similarity_threshold:
                recommendation: ContentRecommendation = {
                    "content_id": content.get("content_id", "unknown"),
                    "title": content.get("title", "Untitled"),
                    "description": content.get("description", ""),
                    "platform": content.get("platform", "unknown"),
                    "content_type": content.get("content_type", "unknown"),
                    "relevance_score": similarity_score,
                    "engagement_prediction": self._predict_engagement(content),
                    "trending_score": self._calculate_trending_score(content),
                    "personalization_score": similarity_score,
                    "overall_score": similarity_score,
                    "recommendation_reasons": [f"Similar to your interests (similarity: {similarity_score:.2f})"],
                    "metadata": content.get("metadata", {}),
                }

                similar_recommendations.append(recommendation)

        # Sort by similarity score
        similar_recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        return similar_recommendations[: self._max_recommendations // 3]

    def _cluster_similar_content(self, content_pool: list[dict[str, Any]]) -> list[ContentCluster]:
        """Cluster similar content for categorization."""
        clusters: list[ContentCluster] = []

        if len(content_pool) < 5:  # Need minimum content for clustering
            return clusters

        # Group content by topic/category
        topic_groups = self._group_content_by_topic(content_pool)

        for topic, content_items in topic_groups.items():
            if len(content_items) >= 3:  # Minimum cluster size
                cluster_characteristics = self._analyze_cluster_characteristics(content_items)
                cohesion_score = self._calculate_cluster_cohesion(content_items)
                representative_content = self._find_representative_content(content_items)

                cluster: ContentCluster = {
                    "cluster_id": f"cluster_{topic}",
                    "cluster_name": topic.replace("_", " ").title(),
                    "content_items": content_items,
                    "cluster_characteristics": cluster_characteristics,
                    "size": len(content_items),
                    "cohesion_score": cohesion_score,
                    "representative_content": representative_content,
                }

                clusters.append(cluster)

        return clusters

    def _calculate_similarity_scores(self, content_pool: list[dict[str, Any]]) -> list[SimilarityScore]:
        """Calculate similarity scores between content items."""
        similarity_scores = []

        # Compare each content item with others
        for i, content1 in enumerate(content_pool):
            for j, content2 in enumerate(content_pool[i + 1 :], i + 1):
                similarity_score = self._calculate_content_similarity(content1, content2)

                if similarity_score > 0.3:  # Only include significant similarities
                    similarity_factors = self._analyze_similarity_factors(content1, content2)
                    shared_characteristics = self._find_shared_characteristics(content1, content2)
                    differences = self._find_content_differences(content1, content2)

                    similarity: SimilarityScore = {
                        "content_id_1": content1.get("content_id", f"content_{i}"),
                        "content_id_2": content2.get("content_id", f"content_{j}"),
                        "similarity_score": similarity_score,
                        "similarity_factors": similarity_factors,
                        "shared_characteristics": shared_characteristics,
                        "differences": differences,
                    }

                    similarity_scores.append(similarity)

        return similarity_scores

    def _identify_trending_content(self, content_pool: list[dict[str, Any]]) -> list[TrendingContent]:
        """Identify trending content with detailed metrics."""
        trending_content = []

        for content in content_pool:
            trending_score = self._calculate_trending_score(content)
            growth_rate = self._calculate_growth_rate(content)
            engagement_velocity = self._calculate_engagement_velocity(content)
            viral_potential = self._assess_viral_potential(content)
            trend_duration = self._estimate_trend_duration(content)
            peak_prediction = self._predict_trend_peak(content)

            # Only include content with significant trending indicators
            if trending_score > 0.5 or growth_rate > 0.3:
                trend_category = self._categorize_trend_type(content)

                trending: TrendingContent = {
                    "content_id": content.get("content_id", "unknown"),
                    "trending_score": trending_score,
                    "trend_category": trend_category,
                    "growth_rate": growth_rate,
                    "engagement_velocity": engagement_velocity,
                    "viral_potential": viral_potential,
                    "trend_duration": trend_duration,
                    "peak_prediction": peak_prediction,
                }

                trending_content.append(trending)

        # Sort by trending score
        trending_content.sort(key=lambda x: x["trending_score"], reverse=True)
        return trending_content[:10]  # Top 10 trending items

    def _calculate_personalization_score(self, content: dict[str, Any], user_profile: UserProfile) -> float:
        """Calculate personalization score for content."""
        score = 0.0

        # Interest matching
        user_interests = user_profile.get("interests", [])
        content_keywords = content.get("keywords", [])

        if user_interests and content_keywords:
            interest_matches = len(set(user_interests) & set(content_keywords))
            interest_score = interest_matches / len(user_interests)
            score += interest_score * 0.4

        # Platform preference
        platform = content.get("platform", "unknown")
        platform_preferences = user_profile.get("platform_preferences", {})
        platform_score = platform_preferences.get(platform, 0.5)
        score += platform_score * 0.3

        # Content type preference
        content_type = content.get("content_type", "unknown")
        content_preferences = user_profile.get("content_preferences", {})
        content_type_score = content_preferences.get(content_type, 0.5)
        score += content_type_score * 0.3

        return min(1.0, score)

    def _calculate_overall_recommendation_score(
        self, content: dict[str, Any], user_profile: UserProfile | None
    ) -> float:
        """Calculate overall recommendation score."""
        personalization_score = self._calculate_personalization_score(content, user_profile) if user_profile else 0.5
        trending_score = self._calculate_trending_score(content)
        quality_score = self._assess_content_quality(content)

        overall_score = (
            personalization_score * self._personalization_weight
            + trending_score * self._trending_weight
            + quality_score * self._quality_weight
        )

        return min(1.0, overall_score)

    def _generate_recommendation_reasons(self, content: dict[str, Any], user_profile: UserProfile | None) -> list[str]:
        """Generate reasons for recommending content."""
        reasons = []

        if user_profile:
            # Interest-based reasons
            user_interests = user_profile.get("interests", [])
            content_keywords = content.get("keywords", [])

            if user_interests and content_keywords:
                matching_interests = set(user_interests) & set(content_keywords)
                if matching_interests:
                    reasons.append(f"Matches your interests: {', '.join(list(matching_interests)[:3])}")

            # Platform preference reasons
            platform = content.get("platform", "unknown")
            platform_preferences = user_profile.get("platform_preferences", {})
            if platform_preferences.get(platform, 0) > 0.7:
                reasons.append(f"You're active on {platform}")

        # Trending reasons
        trending_score = self._calculate_trending_score(content)
        if trending_score > 0.7:
            reasons.append("Currently trending")
        elif trending_score > 0.5:
            reasons.append("Gaining popularity")

        # Quality reasons
        quality_score = self._assess_content_quality(content)
        if quality_score > 0.8:
            reasons.append("High quality content")

        # Content type reasons
        content_type = content.get("content_type", "unknown")
        if content_type in ["video", "image"]:
            reasons.append("Visual content")
        elif content_type == "text":
            reasons.append("Informative text content")

        return reasons[:3]  # Limit to top 3 reasons

    def _calculate_relevance_score(self, content: dict[str, Any], user_profile: UserProfile | None) -> float:
        """Calculate relevance score for content."""
        if not user_profile:
            return 0.5  # Neutral relevance without user profile

        return self._calculate_personalization_score(content, user_profile)

    def _predict_engagement(self, content: dict[str, Any], user_profile: UserProfile | None = None) -> float:
        """Predict engagement for content."""
        base_engagement = 0.5

        # Content quality factors
        content_metadata = content.get("metadata", {})

        if content_metadata.get("content_quality") == "high":
            base_engagement += 0.2

        if content_metadata.get("trending_topic"):
            base_engagement += 0.15

        if content_metadata.get("emotional_impact") == "high":
            base_engagement += 0.1

        # Platform factors
        platform = content.get("platform", "unknown")
        platform_engagement = {
            "youtube": 0.8,
            "tiktok": 0.9,
            "instagram": 0.8,
            "twitter": 0.6,
            "linkedin": 0.5,
        }

        platform_factor = platform_engagement.get(platform, 0.5)
        base_engagement = (base_engagement + platform_factor) / 2

        return min(1.0, base_engagement)

    def _calculate_trending_score(self, content: dict[str, Any]) -> float:
        """Calculate trending score for content."""
        trending_score = 0.0

        # Engagement velocity
        engagement_metrics = content.get("engagement_metrics", {})
        if engagement_metrics:
            views = engagement_metrics.get("views", 0)
            likes = engagement_metrics.get("likes", 0)
            shares = engagement_metrics.get("shares", 0)

            # Calculate engagement rate
            if views > 0:
                engagement_rate = (likes + shares) / views
                trending_score += min(0.5, engagement_rate * 2)

        # Recency factor
        timestamp = content.get("timestamp", 0)
        if timestamp:
            current_time = time.time()
            age_hours = (current_time - timestamp) / 3600

            # Recent content gets higher trending score
            if age_hours < 24:
                trending_score += 0.3
            elif age_hours < 72:
                trending_score += 0.2
            elif age_hours < 168:  # 1 week
                trending_score += 0.1

        # Trending topic indicator
        if content.get("trending_topic"):
            trending_score += 0.2

        return min(1.0, trending_score)

    def _calculate_growth_rate(self, content: dict[str, Any]) -> float:
        """Calculate growth rate for content."""
        engagement_metrics = content.get("engagement_metrics", {})
        if not engagement_metrics:
            return 0.0

        # Simple growth rate calculation based on engagement metrics
        views = engagement_metrics.get("views", 0)
        likes = engagement_metrics.get("likes", 0)
        shares = engagement_metrics.get("shares", 0)

        total_engagement = views + likes + shares

        # Estimate growth rate based on engagement level
        if total_engagement > 10000:
            return 0.8  # High growth
        elif total_engagement > 1000:
            return 0.6  # Medium growth
        elif total_engagement > 100:
            return 0.4  # Low growth
        else:
            return 0.2  # Minimal growth

    def _calculate_engagement_velocity(self, content: dict[str, Any]) -> float:
        """Calculate engagement velocity for content."""
        engagement_metrics = content.get("engagement_metrics", {})
        if not engagement_metrics:
            return 0.0

        # Calculate velocity based on engagement per hour
        timestamp = content.get("timestamp", 0)
        if not timestamp:
            return 0.0

        current_time = time.time()
        age_hours = max(1, (current_time - timestamp) / 3600)

        total_engagement = sum(
            [
                engagement_metrics.get("views", 0),
                engagement_metrics.get("likes", 0),
                engagement_metrics.get("shares", 0),
                engagement_metrics.get("comments", 0),
            ]
        )

        velocity = total_engagement / age_hours

        # Normalize velocity (0-1 scale)
        if velocity > 1000:
            return 1.0
        elif velocity > 100:
            return 0.8
        elif velocity > 10:
            return 0.6
        elif velocity > 1:
            return 0.4
        else:
            return 0.2

    def _assess_viral_potential(self, content: dict[str, Any]) -> float:
        """Assess viral potential of content."""
        viral_potential = 0.0

        # Content characteristics
        content_metadata = content.get("metadata", {})

        if content_metadata.get("emotional_impact") == "high":
            viral_potential += 0.3

        if content_metadata.get("entertainment_value") == "high":
            viral_potential += 0.2

        if content_metadata.get("controversy_level", 0) > 0.5:
            viral_potential += 0.2

        if content.get("trending_topic"):
            viral_potential += 0.2

        # Platform viral potential
        platform = content.get("platform", "unknown")
        platform_viral = {
            "tiktok": 0.9,
            "youtube": 0.8,
            "instagram": 0.7,
            "twitter": 0.6,
            "linkedin": 0.3,
        }

        viral_potential += platform_viral.get(platform, 0.5) * 0.1

        return min(1.0, viral_potential)

    def _estimate_trend_duration(self, content: dict[str, Any]) -> float:
        """Estimate trend duration in hours."""
        content_type = content.get("content_type", "unknown")

        # Base duration by content type
        base_durations = {
            "video": 48.0,  # 2 days
            "image": 24.0,  # 1 day
            "text": 12.0,  # 12 hours
            "audio": 36.0,  # 1.5 days
        }

        base_duration = base_durations.get(content_type, 24.0)

        # Adjust based on viral potential
        viral_potential = self._assess_viral_potential(content)
        duration_multiplier = 1.0 + viral_potential

        return base_duration * duration_multiplier

    def _predict_trend_peak(self, content: dict[str, Any]) -> dict[str, Any]:
        """Predict trend peak characteristics."""
        current_time = time.time()
        timestamp = content.get("timestamp", current_time)
        age_hours = (current_time - timestamp) / 3600

        # Predict peak time based on content age and type
        content_type = content.get("content_type", "unknown")

        if content_type == "video":
            peak_time = age_hours + 6  # Peak 6 hours after posting
        elif content_type == "image":
            peak_time = age_hours + 3  # Peak 3 hours after posting
        else:
            peak_time = age_hours + 2  # Peak 2 hours after posting

        # Predict peak engagement
        current_engagement = sum(
            [
                content.get("engagement_metrics", {}).get("views", 0),
                content.get("engagement_metrics", {}).get("likes", 0),
                content.get("engagement_metrics", {}).get("shares", 0),
            ]
        )

        viral_potential = self._assess_viral_potential(content)
        peak_engagement = current_engagement * (1.5 + viral_potential)

        return {
            "peak_time_hours": peak_time,
            "peak_engagement": peak_engagement,
            "peak_duration_hours": 6.0,
        }

    def _categorize_trend_type(self, content: dict[str, Any]) -> str:
        """Categorize the type of trend."""
        content_metadata = content.get("metadata", {})

        if content_metadata.get("controversy_level", 0) > 0.7:
            return "controversial"
        elif content_metadata.get("emotional_impact") == "high":
            return "emotional"
        elif content_metadata.get("entertainment_value") == "high":
            return "entertainment"
        elif content_metadata.get("educational_value"):
            return "educational"
        elif content.get("trending_topic"):
            return "news"
        else:
            return "general"

    def _assess_content_quality(self, content: dict[str, Any]) -> float:
        """Assess content quality score."""
        quality_score = 0.5  # Base quality

        content_metadata = content.get("metadata", {})

        # Production quality indicators
        if content_metadata.get("video_quality") == "high":
            quality_score += 0.2
        elif content_metadata.get("video_quality") == "low":
            quality_score -= 0.1

        if content_metadata.get("audio_quality") == "high":
            quality_score += 0.1

        # Content characteristics
        if content_metadata.get("professional_quality"):
            quality_score += 0.1

        if content_metadata.get("originality_score", 0) > 0.7:
            quality_score += 0.1

        # Engagement quality (high engagement with good ratio indicates quality)
        engagement_metrics = content.get("engagement_metrics", {})
        if engagement_metrics:
            views = engagement_metrics.get("views", 0)
            likes = engagement_metrics.get("likes", 0)

            if views > 0:
                like_ratio = likes / views
                if like_ratio > 0.1:  # 10% like ratio
                    quality_score += 0.1

        return min(1.0, max(0.0, quality_score))

    def _calculate_content_similarity(self, content1: dict[str, Any], content2: dict[str, Any]) -> float:
        """Calculate similarity between two content items."""
        similarity_score = 0.0

        # Topic/keyword similarity
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))

        if keywords1 and keywords2:
            keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            similarity_score += keyword_similarity * 0.4

        # Content type similarity
        type1 = content1.get("content_type", "unknown")
        type2 = content2.get("content_type", "unknown")

        if type1 == type2:
            similarity_score += 0.2

        # Platform similarity
        platform1 = content1.get("platform", "unknown")
        platform2 = content2.get("platform", "unknown")

        if platform1 == platform2:
            similarity_score += 0.1

        # Metadata similarity
        metadata1 = content1.get("metadata", {})
        metadata2 = content2.get("metadata", {})

        # Sentiment similarity
        sentiment1 = metadata1.get("sentiment", "neutral")
        sentiment2 = metadata2.get("sentiment", "neutral")

        if sentiment1 == sentiment2:
            similarity_score += 0.1

        # Quality similarity
        quality1 = self._assess_content_quality(content1)
        quality2 = self._assess_content_quality(content2)
        quality_diff = abs(quality1 - quality2)
        quality_similarity = 1.0 - quality_diff
        similarity_score += quality_similarity * 0.2

        return min(1.0, similarity_score)

    def _group_content_by_topic(self, content_pool: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group content by topic/category."""
        topic_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for content in content_pool:
            # Determine topic from keywords or metadata
            keywords = content.get("keywords", [])
            topic = content.get("topic", "general")

            if keywords:
                # Use first keyword as primary topic
                primary_topic = keywords[0].lower().replace(" ", "_")
            else:
                primary_topic = topic.lower().replace(" ", "_")

            topic_groups[primary_topic].append(content)

        return dict(topic_groups)

    def _analyze_cluster_characteristics(self, content_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze characteristics of a content cluster."""
        characteristics = {
            "common_keywords": [],
            "content_types": [],
            "platforms": [],
            "avg_quality": 0.0,
            "avg_engagement": 0.0,
            "sentiment_distribution": {},
        }

        if not content_items:
            return characteristics

        # Collect all keywords
        all_keywords = []
        for content in content_items:
            all_keywords.extend(content.get("keywords", []))

        # Find most common keywords
        keyword_counts: dict[str, int] = defaultdict(int)
        for keyword in all_keywords:
            keyword_counts[keyword] += 1

        common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        characteristics["common_keywords"] = [kw[0] for kw in common_keywords]

        # Content types
        content_types = [content.get("content_type", "unknown") for content in content_items]
        characteristics["content_types"] = list(set(content_types))

        # Platforms
        platforms = [content.get("platform", "unknown") for content in content_items]
        characteristics["platforms"] = list(set(platforms))

        # Average quality
        quality_scores = [self._assess_content_quality(content) for content in content_items]
        characteristics["avg_quality"] = sum(quality_scores) / len(quality_scores)

        # Average engagement
        engagement_scores = []
        for content in content_items:
            engagement_metrics = content.get("engagement_metrics", {})
            total_engagement = sum(
                [
                    engagement_metrics.get("views", 0),
                    engagement_metrics.get("likes", 0),
                    engagement_metrics.get("shares", 0),
                ]
            )
            engagement_scores.append(total_engagement)

        if engagement_scores:
            characteristics["avg_engagement"] = sum(engagement_scores) / len(engagement_scores)

        # Sentiment distribution
        sentiments = []
        for content in content_items:
            sentiment = content.get("metadata", {}).get("sentiment", "neutral")
            sentiments.append(sentiment)

        sentiment_counts: dict[str, int] = defaultdict(int)
        for sentiment in sentiments:
            sentiment_counts[sentiment] += 1

        characteristics["sentiment_distribution"] = dict(sentiment_counts)

        return characteristics

    def _calculate_cluster_cohesion(self, content_items: list[dict[str, Any]]) -> float:
        """Calculate cohesion score for a content cluster."""
        if len(content_items) < 2:
            return 1.0

        # Calculate pairwise similarities
        similarities = []
        for i, content1 in enumerate(content_items):
            for content2 in content_items[i + 1 :]:
                similarity = self._calculate_content_similarity(content1, content2)
                similarities.append(similarity)

        if similarities:
            return sum(similarities) / len(similarities)

        return 0.0

    def _find_representative_content(self, content_items: list[dict[str, Any]]) -> dict[str, Any]:
        """Find representative content for a cluster."""
        if not content_items:
            return {}

        # Find content with highest quality and engagement
        best_content = None
        best_score = 0.0

        for content in content_items:
            quality_score = self._assess_content_quality(content)
            engagement_score = self._calculate_trending_score(content)
            combined_score = (quality_score + engagement_score) / 2

            if combined_score > best_score:
                best_score = combined_score
                best_content = content

        return best_content or content_items[0]

    def _analyze_similarity_factors(self, content1: dict[str, Any], content2: dict[str, Any]) -> dict[str, float]:
        """Analyze factors contributing to content similarity."""
        factors = {}

        # Keyword similarity
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))

        if keywords1 and keywords2:
            keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            factors["keyword_similarity"] = keyword_similarity
        else:
            factors["keyword_similarity"] = 0.0

        # Content type similarity
        type1 = content1.get("content_type", "unknown")
        type2 = content2.get("content_type", "unknown")
        factors["content_type_similarity"] = 1.0 if type1 == type2 else 0.0

        # Platform similarity
        platform1 = content1.get("platform", "unknown")
        platform2 = content2.get("platform", "unknown")
        factors["platform_similarity"] = 1.0 if platform1 == platform2 else 0.0

        # Quality similarity
        quality1 = self._assess_content_quality(content1)
        quality2 = self._assess_content_quality(content2)
        factors["quality_similarity"] = 1.0 - abs(quality1 - quality2)

        return factors

    def _find_shared_characteristics(self, content1: dict[str, Any], content2: dict[str, Any]) -> list[str]:
        """Find shared characteristics between content items."""
        shared = []

        # Shared keywords
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))
        shared_keywords = keywords1 & keywords2
        if shared_keywords:
            shared.extend([f"keyword: {kw}" for kw in list(shared_keywords)[:3]])

        # Shared content type
        type1 = content1.get("content_type", "unknown")
        type2 = content2.get("content_type", "unknown")
        if type1 == type2:
            shared.append(f"content_type: {type1}")

        # Shared platform
        platform1 = content1.get("platform", "unknown")
        platform2 = content2.get("platform", "unknown")
        if platform1 == platform2:
            shared.append(f"platform: {platform1}")

        # Shared sentiment
        sentiment1 = content1.get("metadata", {}).get("sentiment", "neutral")
        sentiment2 = content2.get("metadata", {}).get("sentiment", "neutral")
        if sentiment1 == sentiment2:
            shared.append(f"sentiment: {sentiment1}")

        return shared

    def _find_content_differences(self, content1: dict[str, Any], content2: dict[str, Any]) -> list[str]:
        """Find differences between content items."""
        differences = []

        # Different keywords
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))
        unique_keywords1 = keywords1 - keywords2
        unique_keywords2 = keywords2 - keywords1

        if unique_keywords1:
            differences.append(f"content1_unique_keywords: {list(unique_keywords1)[:2]}")
        if unique_keywords2:
            differences.append(f"content2_unique_keywords: {list(unique_keywords2)[:2]}")

        # Different content types
        type1 = content1.get("content_type", "unknown")
        type2 = content2.get("content_type", "unknown")
        if type1 != type2:
            differences.append(f"content_type: {type1} vs {type2}")

        # Different platforms
        platform1 = content1.get("platform", "unknown")
        platform2 = content2.get("platform", "unknown")
        if platform1 != platform2:
            differences.append(f"platform: {platform1} vs {platform2}")

        return differences

    def _generate_general_recommendations(self, content_pool: list[dict[str, Any]]) -> list[ContentRecommendation]:
        """Generate general recommendations without user profile."""
        recommendations = []

        for content in content_pool:
            trending_score = self._calculate_trending_score(content)
            quality_score = self._assess_content_quality(content)
            engagement_prediction = self._predict_engagement(content)

            overall_score = (trending_score + quality_score + engagement_prediction) / 3

            recommendation: ContentRecommendation = {
                "content_id": content.get("content_id", "unknown"),
                "title": content.get("title", "Untitled"),
                "description": content.get("description", ""),
                "platform": content.get("platform", "unknown"),
                "content_type": content.get("content_type", "unknown"),
                "relevance_score": overall_score,
                "engagement_prediction": engagement_prediction,
                "trending_score": trending_score,
                "personalization_score": 0.5,  # Neutral without user profile
                "overall_score": overall_score,
                "recommendation_reasons": ["Popular content", "High quality"],
                "metadata": content.get("metadata", {}),
            }

            recommendations.append(recommendation)

        # Sort by overall score
        recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
        return recommendations[: self._max_recommendations]

    def _analyze_discovery_insights(
        self,
        personalized_recommendations: list[ContentRecommendation],
        trending_recommendations: list[ContentRecommendation],
        content_clusters: list[ContentCluster],
    ) -> dict[str, Any]:
        """Analyze insights from content discovery."""
        insights: dict[str, Any] = {
            "recommendation_summary": {},
            "trending_insights": {},
            "cluster_insights": {},
            "discovery_patterns": [],
        }

        # Recommendation summary
        if personalized_recommendations:
            avg_personalization = sum(r["personalization_score"] for r in personalized_recommendations) / len(
                personalized_recommendations
            )
            insights["recommendation_summary"] = {
                "total_recommendations": len(personalized_recommendations),
                "avg_personalization_score": avg_personalization,
                "high_quality_count": len([r for r in personalized_recommendations if r["overall_score"] > 0.8]),
            }

        # Trending insights
        if trending_recommendations:
            avg_trending = sum(r["trending_score"] for r in trending_recommendations) / len(trending_recommendations)
            insights["trending_insights"] = {
                "trending_count": len(trending_recommendations),
                "avg_trending_score": avg_trending,
                "viral_potential_count": len([r for r in trending_recommendations if r["trending_score"] > 0.8]),
            }

        # Cluster insights
        if content_clusters:
            insights["cluster_insights"] = {
                "total_clusters": len(content_clusters),
                "avg_cluster_size": sum(c["size"] for c in content_clusters) / len(content_clusters),
                "high_cohesion_clusters": len([c for c in content_clusters if c["cohesion_score"] > 0.7]),
            }

        # Discovery patterns
        discovery_patterns = insights["discovery_patterns"]
        if personalized_recommendations and trending_recommendations:
            discovery_patterns.append("Mix of personalized and trending content recommended")

        if content_clusters:
            discovery_patterns.append("Content successfully clustered by topic")

        return insights

    def _assess_recommendation_quality(
        self,
        personalized_recommendations: list[ContentRecommendation],
        user_profile: UserProfile | None,
    ) -> dict[str, Any]:
        """Assess quality of recommendations."""
        quality = {
            "diversity_score": 0.0,
            "relevance_score": 0.0,
            "coverage_score": 0.0,
            "overall_quality": 0.0,
        }

        if not personalized_recommendations:
            return quality

        # Diversity score (platform and content type diversity)
        platforms = set(r["platform"] for r in personalized_recommendations)
        content_types = set(r["content_type"] for r in personalized_recommendations)

        platform_diversity = len(platforms) / max(1, len(personalized_recommendations))
        type_diversity = len(content_types) / max(1, len(personalized_recommendations))
        quality["diversity_score"] = (platform_diversity + type_diversity) / 2

        # Relevance score
        if user_profile:
            avg_relevance = sum(r["relevance_score"] for r in personalized_recommendations) / len(
                personalized_recommendations
            )
            quality["relevance_score"] = avg_relevance
        else:
            quality["relevance_score"] = 0.5  # Neutral without user profile

        # Coverage score (how well recommendations cover user interests)
        if user_profile:
            user_interests = set(user_profile.get("interests", []))
            covered_interests = set()

            for rec in personalized_recommendations:
                rec_keywords = set(rec.get("metadata", {}).get("keywords", []))
                covered_interests.update(user_interests & rec_keywords)

            if user_interests:
                quality["coverage_score"] = len(covered_interests) / len(user_interests)
            else:
                quality["coverage_score"] = 0.0
        else:
            quality["coverage_score"] = 0.5  # Neutral without user profile

        # Overall quality
        quality["overall_quality"] = (
            quality["diversity_score"] * 0.3 + quality["relevance_score"] * 0.4 + quality["coverage_score"] * 0.3
        )

        return quality

    def run(
        self,
        content_pool: list[dict[str, Any]],
        user_profile: UserProfile | None = None,
        recommendation_context: RecommendationContext | None = None,
        discovery_config: dict[str, Any] | None = None,
        tenant: str = "default",
        workspace: str = "default",
        recommendation_mode: str = "comprehensive",
    ) -> StepResult:
        """Public interface for content recommendation."""
        return self._run(
            content_pool, user_profile, recommendation_context, discovery_config, tenant, workspace, recommendation_mode
        )
