from __future__ import annotations

import time
from datetime import datetime
from typing import Any, TypedDict

from ultimate_discord_intelligence_bot.profiles.creator_network_schema import (
    ALL_CREATOR_NETWORKS,
    EnhancedCreatorProfile,
    create_enhanced_profile_from_config,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


class CollaborationEvent(TypedDict, total=False):
    """Record of a collaboration between creators."""

    collaboration_id: str
    creator_1: str
    creator_2: str
    collaboration_type: str  # "guest", "co-host", "interview", "debate", "collab_video"
    platform: str
    content_id: str
    date: float
    duration_minutes: int
    topics: list[str]
    sentiment: float | None
    chemistry_score: float | None
    audience_reception: dict[str, Any] | None
    engagement_metrics: dict[str, Any] | None


class GuestIntelligenceResult(TypedDict, total=False):
    """Result of guest intelligence analysis."""

    timestamp: float
    analysis_type: str
    discovered_guests: list[EnhancedCreatorProfile]
    collaboration_events: list[CollaborationEvent]
    network_expansion_recommendations: list[str]
    monitoring_recommendations: list[str]
    relationship_insights: dict[str, Any]
    processing_time_seconds: float
    errors: list[str]


class GuestIntelligenceAgent:
    """Agent for automatic guest and collaborator profile building and monitoring recommendations."""

    def __init__(self) -> None:
        self._guest_profiles: dict[str, EnhancedCreatorProfile] = {}
        self._collaboration_history: list[CollaborationEvent] = []
        self._monitoring_recommendations: dict[str, list[str]] = {}
        self._relationship_insights: dict[str, Any] = {}

    async def analyze_guest_network(
        self, primary_creator: str, depth: int = 2, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """
        Analyze guest network and collaboration patterns for a primary creator.

        Args:
            primary_creator: ID of the primary creator to analyze
            depth: Depth of network analysis (1=direct guests, 2=guest's guests)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with guest intelligence data
        """
        try:
            if not primary_creator:
                return StepResult.fail("Primary creator is required")

            start_time = time.time()

            # Discover guests and collaborators
            discovered_guests = await self._discover_guests_and_collaborators(primary_creator, depth, tenant, workspace)

            # Analyze collaboration events
            collaboration_events = await self._analyze_collaboration_events(
                primary_creator, discovered_guests, tenant, workspace
            )

            # Generate network expansion recommendations
            network_recommendations = await self._generate_network_expansion_recommendations(
                primary_creator, discovered_guests, collaboration_events, tenant, workspace
            )

            # Generate monitoring recommendations
            monitoring_recommendations = await self._generate_monitoring_recommendations(
                primary_creator, discovered_guests, collaboration_events, tenant, workspace
            )

            # Analyze relationship insights
            relationship_insights = await self._analyze_relationship_insights(
                primary_creator, discovered_guests, collaboration_events, tenant, workspace
            )

            result = GuestIntelligenceResult(
                timestamp=time.time(),
                analysis_type="guest_network_analysis",
                discovered_guests=discovered_guests,
                collaboration_events=collaboration_events,
                network_expansion_recommendations=network_recommendations,
                monitoring_recommendations=monitoring_recommendations,
                relationship_insights=relationship_insights,
                processing_time_seconds=time.time() - start_time,
                errors=[],
            )

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"Guest intelligence analysis failed: {str(e)}")

    async def _discover_guests_and_collaborators(
        self, primary_creator: str, depth: int, tenant: str, workspace: str
    ) -> list[EnhancedCreatorProfile]:
        """Discover guests and collaborators for a primary creator."""
        try:
            discovered_guests: list[EnhancedCreatorProfile] = []
            current_level_creators = [primary_creator]
            processed_creators = {primary_creator}

            for current_depth in range(1, depth + 1):
                next_level_creators: list[str] = []

                for creator_id in current_level_creators:
                    # Extract mentions and collaborations from content
                    mentions = await self._extract_creator_mentions(creator_id, tenant, workspace)
                    collaborations = await self._extract_collaborations(creator_id, tenant, workspace)

                    # Combine and deduplicate
                    all_related = list(set(mentions + collaborations))

                    for related_creator in all_related:
                        if related_creator not in processed_creators:
                            # Create or get profile for the guest
                            guest_profile = await self._create_guest_profile(
                                related_creator, primary_creator, current_depth, tenant, workspace
                            )
                            discovered_guests.append(guest_profile)
                            next_level_creators.append(related_creator)
                            processed_creators.add(related_creator)

                current_level_creators = next_level_creators

            return discovered_guests

        except Exception as e:
            print(f"Error discovering guests: {e}")
            return []

    async def _extract_creator_mentions(self, creator_id: str, tenant: str, workspace: str) -> list[str]:
        """Extract creator mentions from content analysis."""
        try:
            # Mock implementation - in real system, would use content analysis
            mock_mentions = {
                "h3_podcast": ["hasan_piker", "dan", "ab", "zach", "olivia", "will_neff"],
                "ethan_klein": ["hasan_piker", "dan", "ab", "hila_klein"],
                "hasan_piker": ["ethan_klein", "will_neff", "qt_cinderella", "destiny"],
                "will_neff": ["hasan_piker", "qt_cinderella", "pokimane"],
                "qt_cinderella": ["hasan_piker", "will_neff", "pokimane"],
            }

            return mock_mentions.get(creator_id, [])

        except Exception:
            return []

    async def _extract_collaborations(self, creator_id: str, tenant: str, workspace: str) -> list[str]:
        """Extract collaboration partners from content analysis."""
        try:
            # Mock implementation - in real system, would analyze collaboration history
            mock_collaborations = {
                "h3_podcast": ["hasan_piker", "dan", "ab", "zach", "olivia"],
                "ethan_klein": ["hasan_piker", "dan", "ab", "hila_klein"],
                "hasan_piker": ["ethan_klein", "will_neff", "qt_cinderella"],
                "will_neff": ["hasan_piker", "qt_cinderella"],
                "qt_cinderella": ["hasan_piker", "will_neff"],
            }

            return mock_collaborations.get(creator_id, [])

        except Exception:
            return []

    async def _create_guest_profile(
        self, guest_id: str, primary_creator: str, depth: int, tenant: str, workspace: str
    ) -> EnhancedCreatorProfile:
        """Create or enhance guest profile."""
        try:
            # Check if profile exists in predefined networks
            if guest_id in ALL_CREATOR_NETWORKS:
                config = ALL_CREATOR_NETWORKS[guest_id]
                profile = create_enhanced_profile_from_config(guest_id, config)
            else:
                # Create new profile for discovered guest
                from datetime import datetime

                profile = EnhancedCreatorProfile(
                    id=guest_id,
                    name=guest_id.replace("_", " ").title(),
                    known_as=guest_id,
                    type="person",
                    platforms=["unknown"],  # Will be discovered through analysis
                    network_tier=depth + 1,  # Based on discovery depth
                    relationship_type=["guest", "collaborator"],
                    discovery_date=datetime.utcnow(),
                    network_confidence=0.7,  # Medium confidence for discovered guests
                    monitoring_priority=3,  # Medium priority
                )

            # Store in cache
            self._guest_profiles[guest_id] = profile

            return profile

        except Exception as e:
            print(f"Error creating guest profile for {guest_id}: {e}")
            # Return basic profile on error
            return EnhancedCreatorProfile(
                id=guest_id,
                name=guest_id,
                known_as=guest_id,
                type="person",
                platforms=["unknown"],
                network_tier=depth + 1,
                relationship_type=["guest"],
            )

    async def _analyze_collaboration_events(
        self, primary_creator: str, discovered_guests: list[EnhancedCreatorProfile], tenant: str, workspace: str
    ) -> list[CollaborationEvent]:
        """Analyze historical collaboration events."""
        try:
            collaboration_events: list[CollaborationEvent] = []
            current_time = time.time()

            for guest in discovered_guests:
                guest_id = guest.id

                # Mock collaboration events - in real system, would analyze historical data
                if primary_creator == "h3_podcast" and guest_id == "hasan_piker":
                    event = CollaborationEvent(
                        collaboration_id="collab_1",
                        creator_1=primary_creator,
                        creator_2=guest_id,
                        collaboration_type="interview",
                        platform="youtube",
                        content_id="h3_hasan_interview_1",
                        date=current_time - (30 * 24 * 3600),  # 30 days ago
                        duration_minutes=120,
                        topics=["politics", "gaming", "controversy"],
                        sentiment=0.7,
                        chemistry_score=0.85,
                        audience_reception={"positive": 0.8, "negative": 0.1, "neutral": 0.1},
                        engagement_metrics={
                            "views": 500000,
                            "likes": 25000,
                            "comments": 1500,
                            "shares": 800,
                        },
                    )
                    collaboration_events.append(event)

                elif primary_creator == "hasan_piker" and guest_id == "will_neff":
                    event = CollaborationEvent(
                        collaboration_id="collab_2",
                        creator_1=primary_creator,
                        creator_2=guest_id,
                        collaboration_type="co-host",
                        platform="twitch",
                        content_id="hasan_will_stream_1",
                        date=current_time - (7 * 24 * 3600),  # 7 days ago
                        duration_minutes=180,
                        topics=["gaming", "streaming", "entertainment"],
                        sentiment=0.8,
                        chemistry_score=0.9,
                        audience_reception={"positive": 0.85, "negative": 0.05, "neutral": 0.1},
                        engagement_metrics={
                            "views": 150000,
                            "likes": 8000,
                            "comments": 400,
                            "shares": 200,
                        },
                    )
                    collaboration_events.append(event)

            # Store in history
            self._collaboration_history.extend(collaboration_events)

            return collaboration_events

        except Exception as e:
            print(f"Error analyzing collaboration events: {e}")
            return []

    async def _generate_network_expansion_recommendations(
        self,
        primary_creator: str,
        discovered_guests: list[EnhancedCreatorProfile],
        collaboration_events: list[CollaborationEvent],
        tenant: str,
        workspace: str,
    ) -> list[str]:
        """Generate recommendations for network expansion."""
        try:
            recommendations = []

            # Analyze collaboration success
            successful_collaborations = [
                event
                for event in collaboration_events
                if event.get("chemistry_score", 0) > 0.7 and event.get("sentiment", 0) > 0.5
            ]

            if len(successful_collaborations) > 0:
                recommendations.append("Focus on repeat collaborations with high-chemistry guests")

            # Analyze guest diversity
            guest_types = set()
            for guest in discovered_guests:
                guest_types.update(guest.relationship_type)

            if len(guest_types) < 3:
                recommendations.append("Expand guest diversity by inviting different types of creators")

            # Analyze platform coverage
            platforms_used = set()
            for event in collaboration_events:
                platforms_used.add(event["platform"])

            if len(platforms_used) < 3:
                recommendations.append("Explore collaborations on additional platforms for broader reach")

            # Analyze topic diversity
            all_topics = set()
            for event in collaboration_events:
                all_topics.update(event.get("topics", []))

            if len(all_topics) < 5:
                recommendations.append("Invite guests with expertise in different topic areas")

            # Analyze network gaps
            if len(discovered_guests) < 10:
                recommendations.append("Expand network by discovering more potential collaborators")

            return recommendations

        except Exception as e:
            print(f"Error generating network recommendations: {e}")
            return []

    async def _generate_monitoring_recommendations(
        self,
        primary_creator: str,
        discovered_guests: list[EnhancedCreatorProfile],
        collaboration_events: list[CollaborationEvent],
        tenant: str,
        workspace: str,
    ) -> list[str]:
        """Generate monitoring recommendations for guests."""
        try:
            recommendations = []

            # High-priority guests (frequent collaborators)
            frequent_collaborators = {}
            for event in collaboration_events:
                collaborator = event["creator_2"] if event["creator_1"] == primary_creator else event["creator_1"]
                frequent_collaborators[collaborator] = frequent_collaborators.get(collaborator, 0) + 1

            high_priority_guests = [guest for guest, count in frequent_collaborators.items() if count >= 2]

            if high_priority_guests:
                recommendations.append(f"Monitor high-priority guests: {', '.join(high_priority_guests)}")

            # Platform-specific monitoring
            platform_activity = {}
            for guest in discovered_guests:
                for platform in guest.platforms:
                    if platform != "unknown":
                        platform_activity[platform] = platform_activity.get(platform, 0) + 1

            for platform, count in platform_activity.items():
                if count >= 3:
                    recommendations.append(f"Set up {platform} monitoring for guest network")

            # Content type monitoring
            recommendations.append("Monitor for new content types from frequent collaborators")
            recommendations.append("Set up alerts for guest appearances on other shows")

            # Trend monitoring
            recommendations.append("Monitor trending topics among guest network")
            recommendations.append("Track viral content from high-chemistry collaborators")

            return recommendations

        except Exception as e:
            print(f"Error generating monitoring recommendations: {e}")
            return []

    async def _analyze_relationship_insights(
        self,
        primary_creator: str,
        discovered_guests: list[EnhancedCreatorProfile],
        collaboration_events: list[CollaborationEvent],
        tenant: str,
        workspace: str,
    ) -> dict[str, Any]:
        """Analyze relationship insights and patterns."""
        try:
            insights = {
                "total_guests_discovered": len(discovered_guests),
                "total_collaborations": len(collaboration_events),
                "average_chemistry_score": 0.0,
                "most_successful_collaboration_type": "unknown",
                "platform_distribution": {},
                "topic_distribution": {},
                "relationship_strength_ranking": [],
                "collaboration_frequency": {},
            }

            if collaboration_events:
                # Calculate average chemistry score
                chemistry_scores = [
                    event.get("chemistry_score", 0)
                    for event in collaboration_events
                    if event.get("chemistry_score") is not None
                ]
                if chemistry_scores:
                    insights["average_chemistry_score"] = sum(chemistry_scores) / len(chemistry_scores)

                # Find most successful collaboration type
                type_success = {}
                for event in collaboration_events:
                    collab_type = event["collaboration_type"]
                    success_score = event.get("chemistry_score", 0) * event.get("sentiment", 0)
                    if collab_type not in type_success:
                        type_success[collab_type] = []
                    type_success[collab_type].append(success_score)

                if type_success:
                    avg_type_success = {
                        collab_type: sum(scores) / len(scores) for collab_type, scores in type_success.items()
                    }
                    insights["most_successful_collaboration_type"] = max(avg_type_success, key=avg_type_success.get)

                # Platform distribution
                for event in collaboration_events:
                    platform = event["platform"]
                    insights["platform_distribution"][platform] = insights["platform_distribution"].get(platform, 0) + 1

                # Topic distribution
                for event in collaboration_events:
                    for topic in event.get("topics", []):
                        insights["topic_distribution"][topic] = insights["topic_distribution"].get(topic, 0) + 1

                # Collaboration frequency
                for event in collaboration_events:
                    collaborator = event["creator_2"] if event["creator_1"] == primary_creator else event["creator_1"]
                    insights["collaboration_frequency"][collaborator] = (
                        insights["collaboration_frequency"].get(collaborator, 0) + 1
                    )

                # Relationship strength ranking
                relationship_scores = {}
                for event in collaboration_events:
                    collaborator = event["creator_2"] if event["creator_1"] == primary_creator else event["creator_1"]
                    if collaborator not in relationship_scores:
                        relationship_scores[collaborator] = []
                    relationship_scores[collaborator].append(
                        event.get("chemistry_score", 0) * event.get("sentiment", 0)
                    )

                insights["relationship_strength_ranking"] = sorted(
                    relationship_scores.keys(),
                    key=lambda x: sum(relationship_scores[x]) / len(relationship_scores[x]),
                    reverse=True,
                )

            # Store insights
            self._relationship_insights[primary_creator] = insights

            return insights

        except Exception as e:
            print(f"Error analyzing relationship insights: {e}")
            return {}

    def get_guest_profile(self, guest_id: str) -> EnhancedCreatorProfile | None:
        """Get cached guest profile."""
        return self._guest_profiles.get(guest_id)

    def get_collaboration_history(self, creator_id: str | None = None) -> list[CollaborationEvent]:
        """Get collaboration history, optionally filtered by creator."""
        if creator_id:
            return [
                event
                for event in self._collaboration_history
                if event["creator_1"] == creator_id or event["creator_2"] == creator_id
            ]
        return self._collaboration_history.copy()

    def get_monitoring_recommendations(self, creator_id: str) -> list[str]:
        """Get monitoring recommendations for a creator."""
        return self._monitoring_recommendations.get(creator_id, [])

    def get_relationship_insights(self, creator_id: str) -> dict[str, Any]:
        """Get relationship insights for a creator."""
        return self._relationship_insights.get(creator_id, {})

    async def update_guest_profile(
        self, guest_id: str, updates: dict[str, Any], tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """Update guest profile with new information."""
        try:
            if guest_id not in self._guest_profiles:
                return StepResult.fail(f"Guest profile {guest_id} not found")

            profile = self._guest_profiles[guest_id]

            # Update profile fields
            for key, value in updates.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)

            # Update last network update time
            profile.last_network_update = datetime.utcnow()

            self._guest_profiles[guest_id] = profile

            return StepResult.ok(data={"updated_profile": profile.to_dict()})

        except Exception as e:
            return StepResult.fail(f"Failed to update guest profile: {str(e)}")

    async def add_collaboration_event(
        self, event: CollaborationEvent, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """Add a new collaboration event to the history."""
        try:
            self._collaboration_history.append(event)

            # Update relationship insights
            primary_creator = event["creator_1"]
            if primary_creator in self._relationship_insights:
                # Recalculate insights
                await self._analyze_relationship_insights(
                    primary_creator,
                    list(self._guest_profiles.values()),
                    self._collaboration_history,
                    tenant,
                    workspace,
                )

            return StepResult.ok(data={"event_added": event["collaboration_id"]})

        except Exception as e:
            return StepResult.fail(f"Failed to add collaboration event: {str(e)}")

    def get_agent_stats(self) -> dict[str, Any]:
        """Get agent statistics."""
        return {
            "total_guest_profiles": len(self._guest_profiles),
            "total_collaboration_events": len(self._collaboration_history),
            "monitoring_recommendations_count": sum(len(recs) for recs in self._monitoring_recommendations.values()),
            "relationship_insights_count": len(self._relationship_insights),
        }
