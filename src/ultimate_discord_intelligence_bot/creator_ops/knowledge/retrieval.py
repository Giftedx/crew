"""
Content retrieval and search functionality.

This module provides low-level content retrieval capabilities with
database queries, semantic search, and cross-platform aggregation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, desc  # type: ignore[import-untyped]

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.media.embeddings import (
    EmbeddingsGenerator,
)
from ultimate_discord_intelligence_bot.creator_ops.models.schema import (
    Account,
    Claim,
    Interaction,
    Media,
    Person,
    Topic,
    Unit,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


class ContentRetriever:
    """
    Content retrieval with database queries and semantic search.

    Features:
    - Database queries for episodes, clips, interactions
    - Semantic search using embeddings
    - Cross-platform content aggregation
    - Similarity-based content discovery
    """

    def __init__(
        self,
        config: CreatorOpsConfig | None = None,
        db_session: Session | None = None,
        embeddings_generator: EmbeddingsGenerator | None = None,
    ) -> None:
        """Initialize content retriever."""
        self.config = config or CreatorOpsConfig()
        self.db_session = db_session
        self.embeddings_generator = embeddings_generator or EmbeddingsGenerator(self.config)

    def search_episodes(
        self,
        query_params: dict[str, Any],
    ) -> StepResult:
        """
        Search for episodes based on query parameters.

        Args:
            query_params: Search parameters including creator, platform, date_range, etc.

        Returns:
            StepResult with list of episode data
        """
        try:
            if not self.db_session:
                return StepResult.fail("Database session not available")

            # Build query
            query = self.db_session.query(Media).join(Account)

            # Apply filters
            if "creator_handle" in query_params:
                query = query.filter(Account.handle == query_params["creator_handle"])

            if "platform" in query_params:
                query = query.filter(Account.platform == query_params["platform"])

            if "date_range" in query_params:
                start_date, end_date = query_params["date_range"]
                query = query.filter(and_(Media.created_at >= start_date, Media.created_at <= end_date))

            # Filter for video/audio content
            query = query.filter(Media.type.in_(["video", "audio"]))

            # Apply limit
            limit = query_params.get("limit", 50)
            query = query.limit(limit)

            # Order by creation date
            query = query.order_by(desc(Media.created_at))

            # Execute query
            results = query.all()

            # Convert to dict format
            episodes = []
            for media in results:
                episode_data = {
                    "id": str(media.id),
                    "title": media.title or "Untitled",
                    "creator": media.account.handle,
                    "platform": media.account.platform,
                    "published_at": media.created_at,
                    "duration": media.duration or 0,
                    "url": media.url or "",
                    "thumbnail_url": media.thumbnail_url,
                    "description": media.description,
                    "view_count": media.view_count,
                    "like_count": media.like_count,
                    "comment_count": media.comment_count,
                }

                # Add topics and claims if available
                topics = self._get_media_topics(media.id)
                claims = self._get_media_claims(media.id)
                speakers = self._get_media_speakers(media.id)

                episode_data["topics"] = topics
                episode_data["claims"] = claims
                episode_data["speakers"] = speakers

                episodes.append(episode_data)

            return StepResult.ok(data=episodes)

        except Exception as e:
            logger.error(f"Failed to search episodes: {e!s}")
            return StepResult.fail(f"Failed to search episodes: {e!s}")

    def semantic_search(
        self,
        search_params: dict[str, Any],
    ) -> StepResult:
        """
        Perform semantic search across content.

        Args:
            search_params: Search parameters including query, platforms, content_types, etc.

        Returns:
            StepResult with search results
        """
        try:
            query = search_params["query"]
            limit = search_params.get("limit", 20)

            # Use embeddings generator for semantic search
            search_result = self.embeddings_generator.search_similar_content(
                query=query,
                collection_name="creator_ops_transcripts",
                limit=limit,
                score_threshold=0.7,
            )

            if not search_result.success:
                return search_result

            # Convert to search result format
            results = []
            for result in search_result.data["results"]:
                # Extract metadata
                metadata = result.metadata

                # Determine content type
                content_type = "episode"  # Default
                if "clip" in metadata.get("content_type", "").lower():
                    content_type = "clip"
                elif "post" in metadata.get("content_type", "").lower():
                    content_type = "post"

                search_result_data = {
                    "content_id": metadata.get("segment_index", "unknown"),
                    "content_type": content_type,
                    "platform": metadata.get("platform", "unknown"),
                    "title": metadata.get("title", "Untitled"),
                    "relevance_score": result.score,
                    "url": metadata.get("url", ""),
                    "metadata": metadata,
                    "matched_terms": [query],  # Simplified for now
                }

                results.append(search_result_data)

            return StepResult.ok(data=results)

        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e!s}")
            return StepResult.fail(f"Failed to perform semantic search: {e!s}")

    def get_clip(self, clip_id: str) -> StepResult:
        """
        Get clip information by ID.

        Args:
            clip_id: Clip identifier

        Returns:
            StepResult with clip data
        """
        try:
            if not self.db_session:
                return StepResult.fail("Database session not available")

            # Query for clip (assuming clips are stored as Units)
            unit = self.db_session.query(Unit).filter(Unit.id == clip_id).first()

            if not unit:
                return StepResult.fail(f"Clip not found: {clip_id}")

            # Get associated media
            media = self.db_session.query(Media).filter(Media.id == unit.media_id).first()

            if not media:
                return StepResult.fail(f"Associated media not found for clip: {clip_id}")

            # Build clip data
            clip_data = {
                "id": str(unit.id),
                "title": unit.title or "Untitled Clip",
                "episode_id": str(unit.media_id),
                "start_time": unit.start_time or 0,
                "end_time": unit.end_time or 0,
                "duration": (unit.end_time or 0) - (unit.start_time or 0),
                "url": unit.url,
                "thumbnail_url": unit.thumbnail_url,
                "transcript": unit.transcript,
            }

            # Add speakers, topics, sentiment
            speakers = self._get_unit_speakers(unit.id)
            topics = self._get_unit_topics(unit.id)
            sentiment = self._get_unit_sentiment(unit.id)

            clip_data["speakers"] = speakers
            clip_data["topics"] = topics
            clip_data["sentiment"] = sentiment

            return StepResult.ok(data=clip_data)

        except Exception as e:
            logger.error(f"Failed to get clip: {e!s}")
            return StepResult.fail(f"Failed to get clip: {e!s}")

    def find_similar_clips(
        self,
        reference_clip: dict[str, Any],
        similarity_threshold: float = 0.7,
        limit: int = 10,
    ) -> StepResult:
        """
        Find clips similar to the reference clip.

        Args:
            reference_clip: Reference clip data
            similarity_threshold: Minimum similarity score
            limit: Maximum number of similar clips

        Returns:
            StepResult with similar clips
        """
        try:
            # Use transcript for similarity search
            transcript = reference_clip.get("transcript", "")
            if not transcript:
                return StepResult.fail("Reference clip has no transcript for similarity search")

            # Perform semantic search
            search_result = self.embeddings_generator.search_similar_content(
                query=transcript,
                collection_name="creator_ops_transcripts",
                limit=limit,
                score_threshold=similarity_threshold,
            )

            if not search_result.success:
                return search_result

            # Convert to clip format
            similar_clips = []
            for result in search_result.data["results"]:
                metadata = result.metadata

                clip_data = {
                    "id": metadata.get("segment_index", "unknown"),
                    "title": metadata.get("title", "Similar Clip"),
                    "episode_id": metadata.get("episode_id", "unknown"),
                    "start_time": metadata.get("start_time", 0),
                    "end_time": metadata.get("end_time", 0),
                    "duration": metadata.get("end_time", 0) - metadata.get("start_time", 0),
                    "url": metadata.get("url", ""),
                    "thumbnail_url": metadata.get("thumbnail_url"),
                    "transcript": result.text,
                    "speakers": metadata.get("speakers", []),
                    "topics": metadata.get("topics", []),
                    "sentiment": metadata.get("sentiment"),
                    "engagement_score": result.score,
                }

                similar_clips.append(clip_data)

            return StepResult.ok(data=similar_clips)

        except Exception as e:
            logger.error(f"Failed to find similar clips: {e!s}")
            return StepResult.fail(f"Failed to find similar clips: {e!s}")

    def get_episode_interactions(self, episode_id: str) -> StepResult:
        """
        Get interactions for an episode.

        Args:
            episode_id: Episode identifier

        Returns:
            StepResult with interaction data
        """
        try:
            if not self.db_session:
                return StepResult.fail("Database session not available")

            # Get interactions for the episode
            interactions = self.db_session.query(Interaction).filter(Interaction.media_id == episode_id).all()

            # Organize interactions by type
            interaction_data = {
                "comments": [],
                "reactions": {},
                "shares": [],
            }

            for interaction in interactions:
                if interaction.type == "comment":
                    comment_data = {
                        "id": str(interaction.id),
                        "text": interaction.content,
                        "author": interaction.author,
                        "timestamp": interaction.created_at,
                        "sentiment": interaction.sentiment,
                        "topics": interaction.topics or [],
                    }
                    interaction_data["comments"].append(comment_data)

                elif interaction.type == "reaction":
                    reaction_type = interaction.content
                    interaction_data["reactions"][reaction_type] = (
                        interaction_data["reactions"].get(reaction_type, 0) + 1
                    )

                elif interaction.type == "share":
                    share_data = {
                        "id": str(interaction.id),
                        "platform": interaction.platform,
                        "timestamp": interaction.created_at,
                    }
                    interaction_data["shares"].append(share_data)

            return StepResult.ok(data=interaction_data)

        except Exception as e:
            logger.error(f"Failed to get episode interactions: {e!s}")
            return StepResult.fail(f"Failed to get episode interactions: {e!s}")

    def get_audience_demographics(self, episode_id: str) -> StepResult:
        """
        Get audience demographics for an episode.

        Args:
            episode_id: Episode identifier

        Returns:
            StepResult with demographic data
        """
        try:
            if not self.db_session:
                return StepResult.fail("Database session not available")

            # Get interactions to analyze demographics
            interactions = self.db_session.query(Interaction).filter(Interaction.media_id == episode_id).all()

            # Simple demographic analysis based on available data
            demographics = {
                "total_interactions": len(interactions),
                "unique_authors": len({i.author for i in interactions if i.author}),
                "platform_distribution": {},
                "time_distribution": {},
            }

            # Analyze platform distribution
            for interaction in interactions:
                platform = interaction.platform or "unknown"
                demographics["platform_distribution"][platform] = (
                    demographics["platform_distribution"].get(platform, 0) + 1
                )

            # Analyze time distribution (hour of day)
            for interaction in interactions:
                hour = interaction.created_at.hour
                demographics["time_distribution"][str(hour)] = demographics["time_distribution"].get(str(hour), 0) + 1

            return StepResult.ok(data=demographics)

        except Exception as e:
            logger.error(f"Failed to get audience demographics: {e!s}")
            return StepResult.fail(f"Failed to get audience demographics: {e!s}")

    def _get_media_topics(self, media_id: int) -> list[str]:
        """Get topics for a media item."""
        try:
            if not self.db_session:
                return []

            topics = self.db_session.query(Topic).filter(Topic.media_id == media_id).all()
            return [topic.name for topic in topics]

        except Exception as e:
            logger.warning(f"Failed to get media topics: {e!s}")
            return []

    def _get_media_claims(self, media_id: int) -> list[str]:
        """Get claims for a media item."""
        try:
            if not self.db_session:
                return []

            claims = self.db_session.query(Claim).filter(Claim.media_id == media_id).all()
            return [claim.text for claim in claims]

        except Exception as e:
            logger.warning(f"Failed to get media claims: {e!s}")
            return []

    def _get_media_speakers(self, media_id: int) -> list[str]:
        """Get speakers for a media item."""
        try:
            if not self.db_session:
                return []

            # Get people associated with the media
            people = self.db_session.query(Person).filter(Person.media_id == media_id).all()
            return [person.name for person in people if person.role == "speaker"]

        except Exception as e:
            logger.warning(f"Failed to get media speakers: {e!s}")
            return []

    def _get_unit_speakers(self, unit_id: int) -> list[str]:
        """Get speakers for a unit (clip)."""
        try:
            if not self.db_session:
                return []

            # Get people associated with the unit
            people = self.db_session.query(Person).filter(Person.unit_id == unit_id).all()
            return [person.name for person in people if person.role == "speaker"]

        except Exception as e:
            logger.warning(f"Failed to get unit speakers: {e!s}")
            return []

    def _get_unit_topics(self, unit_id: int) -> list[str]:
        """Get topics for a unit (clip)."""
        try:
            if not self.db_session:
                return []

            topics = self.db_session.query(Topic).filter(Topic.unit_id == unit_id).all()
            return [topic.name for topic in topics]

        except Exception as e:
            logger.warning(f"Failed to get unit topics: {e!s}")
            return []

    def _get_unit_sentiment(self, unit_id: int) -> str | None:
        """Get sentiment for a unit (clip)."""
        try:
            if not self.db_session:
                return None

            # Get the unit to check for sentiment metadata
            unit = self.db_session.query(Unit).filter(Unit.id == unit_id).first()
            if unit and unit.metadata:
                return unit.metadata.get("sentiment")

            return None

        except Exception as e:
            logger.warning(f"Failed to get unit sentiment: {e!s}")
            return None
