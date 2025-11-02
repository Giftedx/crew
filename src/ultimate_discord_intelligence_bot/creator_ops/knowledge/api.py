"""
Unified Knowledge API for cross-platform content querying.

This module provides high-level APIs for querying across platforms with
provenance tracking, deduplication, and canonicalization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.knowledge.retrieval import ContentRetriever
from ultimate_discord_intelligence_bot.creator_ops.knowledge.social_graph import SocialGraphMapper


if TYPE_CHECKING:
    from datetime import datetime
logger = logging.getLogger(__name__)


@dataclass
class Episode:
    """Episode information with cross-platform metadata."""

    id: str
    title: str
    creator: str
    platform: str
    published_at: datetime
    duration: float
    url: str
    thumbnail_url: str | None = None
    description: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    comment_count: int | None = None
    topics: list[str] | None = None
    claims: list[str] | None = None
    speakers: list[str] | None = None


@dataclass
class Clip:
    """Clip information with metadata."""

    id: str
    title: str
    episode_id: str
    start_time: float
    end_time: float
    duration: float
    url: str | None = None
    thumbnail_url: str | None = None
    transcript: str | None = None
    speakers: list[str] | None = None
    topics: list[str] | None = None
    sentiment: str | None = None
    engagement_score: float | None = None


@dataclass
class CommunityPulse:
    """Community engagement metrics for an episode."""

    episode_id: str
    total_comments: int
    total_reactions: int
    sentiment_distribution: dict[str, int]
    top_topics: list[str]
    engagement_timeline: list[dict[str, Any]]
    viral_moments: list[dict[str, Any]]
    audience_demographics: dict[str, Any] | None = None


@dataclass
class SearchResult:
    """Search result with relevance scoring."""

    content_id: str
    content_type: str
    platform: str
    title: str
    relevance_score: float
    url: str
    metadata: dict[str, Any]
    matched_terms: list[str]


class KnowledgeAPI:
    """
    Unified Knowledge API for cross-platform content querying.

    Features:
    - Cross-platform episode retrieval
    - Semantic content search
    - Related content discovery
    - Community engagement analysis
    - Provenance tracking and deduplication
    """

    def __init__(
        self,
        config: CreatorOpsConfig | None = None,
        retriever: ContentRetriever | None = None,
        social_graph: SocialGraphMapper | None = None,
    ) -> None:
        """Initialize Knowledge API."""
        self.config = config or CreatorOpsConfig()
        self.retriever = retriever or ContentRetriever(self.config)
        self.social_graph = social_graph or SocialGraphMapper(self.config)

    def get_episodes_by_creator(
        self,
        creator_handle: str,
        platform: str | None = None,
        date_range: tuple[datetime, datetime] | None = None,
        limit: int = 50,
    ) -> StepResult:
        """
        Get episodes by creator across platforms.

        Args:
            creator_handle: Creator's handle/username
            platform: Specific platform to search (optional)
            date_range: Date range tuple (start, end)
            limit: Maximum number of episodes to return

        Returns:
            StepResult with list of Episode objects
        """
        try:
            query_params = {"creator_handle": creator_handle, "limit": limit}
            if platform:
                query_params["platform"] = platform
            if date_range:
                query_params["date_range"] = date_range
            result = self.retriever.search_episodes(query_params)
            if not result.success:
                return result
            episodes = []
            for episode_data in result.data:
                episode = Episode(
                    id=episode_data["id"],
                    title=episode_data["title"],
                    creator=episode_data["creator"],
                    platform=episode_data["platform"],
                    published_at=episode_data["published_at"],
                    duration=episode_data["duration"],
                    url=episode_data["url"],
                    thumbnail_url=episode_data.get("thumbnail_url"),
                    description=episode_data.get("description"),
                    view_count=episode_data.get("view_count"),
                    like_count=episode_data.get("like_count"),
                    comment_count=episode_data.get("comment_count"),
                    topics=episode_data.get("topics"),
                    claims=episode_data.get("claims"),
                    speakers=episode_data.get("speakers"),
                )
                episodes.append(episode)
            return StepResult.ok(data=episodes)
        except Exception as e:
            logger.error(f"Failed to get episodes by creator: {e!s}")
            return StepResult.fail(f"Failed to get episodes by creator: {e!s}")

    def search_content(
        self,
        query: str,
        platforms: list[str] | None = None,
        content_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> StepResult:
        """
        Search content across platforms using semantic search.

        Args:
            query: Search query
            platforms: List of platforms to search
            content_types: List of content types (episode, clip, post)
            filters: Additional filters (date_range, creator, etc.)
            limit: Maximum number of results

        Returns:
            StepResult with list of SearchResult objects
        """
        try:
            search_params = {"query": query, "limit": limit}
            if platforms:
                search_params["platforms"] = platforms
            if content_types:
                search_params["content_types"] = content_types
            if filters:
                search_params["filters"] = filters
            result = self.retriever.semantic_search(search_params)
            if not result.success:
                return result
            search_results = []
            for result_data in result.data:
                search_result = SearchResult(
                    content_id=result_data["content_id"],
                    content_type=result_data["content_type"],
                    platform=result_data["platform"],
                    title=result_data["title"],
                    relevance_score=result_data["relevance_score"],
                    url=result_data["url"],
                    metadata=result_data["metadata"],
                    matched_terms=result_data.get("matched_terms", []),
                )
                search_results.append(search_result)
            return StepResult.ok(data=search_results)
        except Exception as e:
            logger.error(f"Failed to search content: {e!s}")
            return StepResult.fail(f"Failed to search content: {e!s}")

    def get_related_clips(self, clip_id: str, similarity_threshold: float = 0.7, limit: int = 10) -> StepResult:
        """
        Get clips similar to the given clip.

        Args:
            clip_id: ID of the reference clip
            similarity_threshold: Minimum similarity score
            limit: Maximum number of related clips

        Returns:
            StepResult with list of Clip objects
        """
        try:
            clip_result = self.retriever.get_clip(clip_id)
            if not clip_result.success:
                return clip_result
            reference_clip = clip_result.data
            similar_result = self.retriever.find_similar_clips(reference_clip, similarity_threshold, limit)
            if not similar_result.success:
                return similar_result
            clips = []
            for clip_data in similar_result.data:
                clip = Clip(
                    id=clip_data["id"],
                    title=clip_data["title"],
                    episode_id=clip_data["episode_id"],
                    start_time=clip_data["start_time"],
                    end_time=clip_data["end_time"],
                    duration=clip_data["duration"],
                    url=clip_data.get("url"),
                    thumbnail_url=clip_data.get("thumbnail_url"),
                    transcript=clip_data.get("transcript"),
                    speakers=clip_data.get("speakers"),
                    topics=clip_data.get("topics"),
                    sentiment=clip_data.get("sentiment"),
                    engagement_score=clip_data.get("engagement_score"),
                )
                clips.append(clip)
            return StepResult.ok(data=clips)
        except Exception as e:
            logger.error(f"Failed to get related clips: {e!s}")
            return StepResult.fail(f"Failed to get related clips: {e!s}")

    def get_community_pulse(self, episode_id: str, include_demographics: bool = False) -> StepResult:
        """
        Get community engagement metrics for an episode.

        Args:
            episode_id: ID of the episode
            include_demographics: Whether to include audience demographics

        Returns:
            StepResult with CommunityPulse object
        """
        try:
            interactions_result = self.retriever.get_episode_interactions(episode_id)
            if not interactions_result.success:
                return interactions_result
            interactions = interactions_result.data
            sentiment_distribution = self._analyze_sentiment_distribution(interactions)
            top_topics = self._extract_top_topics(interactions)
            engagement_timeline = self._build_engagement_timeline(interactions)
            viral_moments = self._identify_viral_moments(interactions)
            audience_demographics = None
            if include_demographics:
                demographics_result = self.retriever.get_audience_demographics(episode_id)
                if demographics_result.success:
                    audience_demographics = demographics_result.data
            community_pulse = CommunityPulse(
                episode_id=episode_id,
                total_comments=len(interactions.get("comments", [])),
                total_reactions=sum(interactions.get("reactions", {}).values()),
                sentiment_distribution=sentiment_distribution,
                top_topics=top_topics,
                engagement_timeline=engagement_timeline,
                viral_moments=viral_moments,
                audience_demographics=audience_demographics,
            )
            return StepResult.ok(data=community_pulse)
        except Exception as e:
            logger.error(f"Failed to get community pulse: {e!s}")
            return StepResult.fail(f"Failed to get community pulse: {e!s}")

    def get_creator_collaborations(self, creator_handle: str, limit: int = 20) -> StepResult:
        """
        Get collaboration recommendations for a creator.

        Args:
            creator_handle: Creator's handle/username
            limit: Maximum number of recommendations

        Returns:
            StepResult with collaboration recommendations
        """
        try:
            graph_result = self.social_graph.analyze_creator_network(creator_handle)
            if not graph_result.success:
                return graph_result
            network_data = graph_result.data
            recommendations_result = self.social_graph.get_collaboration_recommendations(creator_handle, limit)
            if not recommendations_result.success:
                return recommendations_result
            return StepResult.ok(
                data={
                    "creator": creator_handle,
                    "network_analysis": network_data,
                    "recommendations": recommendations_result.data,
                }
            )
        except Exception as e:
            logger.error(f"Failed to get creator collaborations: {e!s}")
            return StepResult.fail(f"Failed to get creator collaborations: {e!s}")

    def deduplicate_content(self, content_list: list[dict[str, Any]]) -> StepResult:
        """
        Deduplicate content across platforms.

        Args:
            content_list: List of content items to deduplicate

        Returns:
            StepResult with deduplicated content
        """
        try:
            canonical_groups = {}
            for content in content_list:
                canonical_id = self._create_canonical_id(content)
                if canonical_id not in canonical_groups:
                    canonical_groups[canonical_id] = []
                canonical_groups[canonical_id].append(content)
            deduplicated = []
            for group in canonical_groups.values():
                if len(group) == 1:
                    deduplicated.append(group[0])
                else:
                    best_content = self._select_best_representative(group)
                    deduplicated.append(best_content)
            return StepResult.ok(
                data={
                    "original_count": len(content_list),
                    "deduplicated_count": len(deduplicated),
                    "deduplication_ratio": len(deduplicated) / len(content_list),
                    "content": deduplicated,
                }
            )
        except Exception as e:
            logger.error(f"Failed to deduplicate content: {e!s}")
            return StepResult.fail(f"Failed to deduplicate content: {e!s}")

    def _analyze_sentiment_distribution(self, interactions: dict[str, Any]) -> dict[str, int]:
        """Analyze sentiment distribution from interactions."""
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for comment in interactions.get("comments", []):
            sentiment = comment.get("sentiment", "neutral")
            sentiment_counts[sentiment] += 1
        return sentiment_counts

    def _extract_top_topics(self, interactions: dict[str, Any]) -> list[str]:
        """Extract top topics from interactions."""
        topic_counts = {}
        for comment in interactions.get("comments", []):
            topics = comment.get("topics", [])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:10]]

    def _build_engagement_timeline(self, interactions: dict[str, Any]) -> list[dict[str, Any]]:
        """Build engagement timeline from interactions."""
        timeline = []
        time_windows = {}
        for comment in interactions.get("comments", []):
            timestamp = comment.get("timestamp")
            if timestamp:
                window = timestamp.replace(second=0, microsecond=0)
                window = window.replace(minute=window.minute // 5 * 5)
                if window not in time_windows:
                    time_windows[window] = {"comments": 0, "reactions": 0}
                time_windows[window]["comments"] += 1
        for window, metrics in sorted(time_windows.items()):
            timeline.append(
                {"timestamp": window.isoformat(), "comments": metrics["comments"], "reactions": metrics["reactions"]}
            )
        return timeline

    def _identify_viral_moments(self, interactions: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify viral moments from interactions."""
        viral_moments = []
        comments = interactions.get("comments", [])
        if len(comments) < 10:
            return viral_moments
        time_windows = {}
        for comment in comments:
            timestamp = comment.get("timestamp")
            if timestamp:
                window = timestamp.replace(second=0, microsecond=0)
                window = window.replace(minute=window.minute // 2 * 2)
                if window not in time_windows:
                    time_windows[window] = 0
                time_windows[window] += 1
        if time_windows:
            avg_activity = sum(time_windows.values()) / len(time_windows)
            threshold = avg_activity * 2
            for window, count in time_windows.items():
                if count > threshold:
                    viral_moments.append(
                        {
                            "timestamp": window.isoformat(),
                            "activity_level": count,
                            "threshold": threshold,
                            "type": "high_engagement",
                        }
                    )
        return viral_moments

    def _create_canonical_id(self, content: dict[str, Any]) -> str:
        """Create canonical identifier for content deduplication."""
        title = content.get("title", "").lower().strip()
        duration = content.get("duration", 0)
        import re

        normalized_title = re.sub("[^\\w\\s]", "", title)
        normalized_title = re.sub("\\s+", " ", normalized_title).strip()
        import hashlib

        content_string = f"{normalized_title}_{duration}"
        return hashlib.md5(content_string.encode(), usedforsecurity=False).hexdigest()

    def _select_best_representative(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        """Select best representative from a group of similar content."""
        best_item = None
        best_score = -1
        for item in group:
            score = 0
            view_count = item.get("view_count", 0)
            if view_count > 0:
                score += min(view_count / 1000000, 10)
            like_count = item.get("like_count", 0)
            if like_count > 0:
                score += min(like_count / 10000, 5)
            duration = item.get("duration", 0)
            if duration > 0:
                score += min(duration / 3600, 3)
            if item.get("thumbnail_url"):
                score += 1
            if score > best_score:
                best_score = score
                best_item = item
        return best_item or group[0]
