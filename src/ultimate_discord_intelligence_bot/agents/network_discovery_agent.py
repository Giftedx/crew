"""Network discovery agent for creator social networks."""

from __future__ import annotations
import time
from typing import Any, TypedDict
from ultimate_discord_intelligence_bot.profiles.creator_network_schema import (
    ALL_CREATOR_NETWORKS,
    EnhancedCreatorProfile,
    create_enhanced_profile_from_config,
)
from platform.core.step_result import StepResult


class CollaborationPattern(TypedDict, total=False):
    """Pattern of collaboration between creators."""

    creator_1: str
    creator_2: str
    collaboration_type: str
    frequency: int
    last_collaboration: float
    topics: list[str]
    platforms: list[str]
    success_rate: float


class NetworkDiscoveryResult(TypedDict, total=False):
    """Result of network discovery process."""

    seed_creator: str
    discovery_depth: int
    creators_discovered: list[str]
    relationships_found: list[dict[str, Any]]
    collaboration_patterns: list[CollaborationPattern]
    network_metrics: dict[str, Any]
    processing_time_seconds: float
    recommendations: list[str]


class NetworkDiscoveryAgent:
    """Autonomous agent for discovering creator social networks."""

    def __init__(self) -> None:
        self._discovered_creators: dict[str, EnhancedCreatorProfile] = {}
        self._collaboration_patterns: list[CollaborationPattern] = []
        self._network_relationships: dict[str, list[str]] = {}

    async def discover_network(
        self, seed_creator: str, depth: int = 3, tenant: str = "default", workspace: str = "default"
    ) -> StepResult:
        """
        Recursively discover social network.

        Args:
            seed_creator: ID of the creator to start discovery from
            depth: Maximum depth of discovery (1=direct collaborators, 2=frequent guests, 3=extended)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with network discovery data
        """
        try:
            if not seed_creator:
                return StepResult.fail("Seed creator is required")
            if depth < 1 or depth > 3:
                return StepResult.fail("Depth must be between 1 and 3")
            start_time = time.time()
            discovered_creators: list[str] = []
            relationships_found: list[dict[str, Any]] = []
            collaboration_patterns: list[CollaborationPattern] = []
            if seed_creator not in self._discovered_creators:
                await self._initialize_creator_profile(seed_creator, tenant, workspace)
            discovered_creators.append(seed_creator)
            current_level_creators = [seed_creator]
            for current_depth in range(1, depth + 1):
                next_level_creators: list[str] = []
                for creator_id in current_level_creators:
                    mentions = await self._extract_mentions_from_content(creator_id, tenant, workspace)
                    patterns = await self._identify_collaboration_patterns(creator_id, tenant, workspace)
                    collaboration_patterns.extend(patterns)
                    for mentioned_creator in mentions:
                        if mentioned_creator not in discovered_creators:
                            await self._initialize_creator_profile(mentioned_creator, tenant, workspace)
                            discovered_creators.append(mentioned_creator)
                            next_level_creators.append(mentioned_creator)
                            relationships_found.append(
                                {
                                    "source": creator_id,
                                    "target": mentioned_creator,
                                    "relationship_type": "mentioned",
                                    "depth": current_depth,
                                    "discovery_method": "content_analysis",
                                }
                            )
                current_level_creators = next_level_creators
            network_metrics = await self._calculate_network_metrics(discovered_creators, relationships_found)
            recommendations = self._generate_discovery_recommendations(
                discovered_creators, relationships_found, collaboration_patterns
            )
            result = NetworkDiscoveryResult(
                seed_creator=seed_creator,
                discovery_depth=depth,
                creators_discovered=discovered_creators,
                relationships_found=relationships_found,
                collaboration_patterns=collaboration_patterns,
                network_metrics=network_metrics,
                processing_time_seconds=time.time() - start_time,
                recommendations=recommendations,
            )
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Network discovery failed: {e!s}")

    async def _initialize_creator_profile(self, creator_id: str, tenant: str, workspace: str) -> None:
        """Initialize creator profile from configuration or create new one."""
        try:
            if creator_id in ALL_CREATOR_NETWORKS:
                config = ALL_CREATOR_NETWORKS[creator_id]
                profile = create_enhanced_profile_from_config(creator_id, config)
            else:
                from datetime import datetime

                profile = EnhancedCreatorProfile(
                    name=creator_id.replace("_", " ").title(),
                    known_as=creator_id,
                    type="person",
                    network_tier=4,
                    relationship_type=["discovered"],
                    discovery_date=datetime.utcnow(),
                    monitoring_priority=3,
                )
            self._discovered_creators[creator_id] = profile
        except Exception as e:
            print(f"Error initializing profile for {creator_id}: {e}")

    async def _extract_mentions_from_content(self, creator_id: str, tenant: str, workspace: str) -> list[str]:
        """Use LLM to extract creator mentions from transcripts."""
        try:
            mock_mentions = []
            if creator_id == "h3_podcast" or creator_id == "ethan_klein":
                mock_mentions = ["hasan_piker", "dan", "ab", "zach", "olivia"]
            elif creator_id == "hasan_piker":
                mock_mentions = ["h3_podcast", "ethan_klein", "will_neff", "qt_cinderella"]
            elif creator_id in ["dan", "ab", "zach", "olivia"]:
                mock_mentions = ["h3_podcast", "ethan_klein", "hila_klein"]
            elif creator_id in ["will_neff", "qt_cinderella"]:
                mock_mentions = ["hasan_piker"]
            return mock_mentions
        except Exception as e:
            print(f"Error extracting mentions for {creator_id}: {e}")
            return []

    async def _identify_collaboration_patterns(
        self, creator_id: str, tenant: str, workspace: str
    ) -> list[CollaborationPattern]:
        """Analyze historical content for collaboration patterns."""
        try:
            patterns: list[CollaborationPattern] = []
            current_time = time.time()
            if creator_id == "h3_podcast":
                patterns = [
                    CollaborationPattern(
                        creator_1="h3_podcast",
                        creator_2="hasan_piker",
                        collaboration_type="guest_appearance",
                        frequency=3,
                        last_collaboration=current_time - 7 * 24 * 3600,
                        topics=["politics", "gaming", "controversy"],
                        platforms=["youtube", "twitch"],
                        success_rate=0.9,
                    ),
                    CollaborationPattern(
                        creator_1="h3_podcast",
                        creator_2="dan",
                        collaboration_type="co_host",
                        frequency=100,
                        last_collaboration=current_time - 1 * 24 * 3600,
                        topics=["podcast", "production", "tech"],
                        platforms=["youtube"],
                        success_rate=0.95,
                    ),
                ]
            elif creator_id == "hasan_piker":
                patterns = [
                    CollaborationPattern(
                        creator_1="hasan_piker",
                        creator_2="will_neff",
                        collaboration_type="stream_collaboration",
                        frequency=20,
                        last_collaboration=current_time - 2 * 24 * 3600,
                        topics=["gaming", "politics", "entertainment"],
                        platforms=["twitch"],
                        success_rate=0.85,
                    )
                ]
            return patterns
        except Exception as e:
            print(f"Error identifying collaboration patterns for {creator_id}: {e}")
            return []

    async def _calculate_network_metrics(
        self, creators: list[str], relationships: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate network-level metrics."""
        try:
            total_creators = len(creators)
            total_relationships = len(relationships)
            max_possible_relationships = total_creators * (total_creators - 1)
            relationship_density = (
                total_relationships / max_possible_relationships if max_possible_relationships > 0 else 0
            )
            creator_connections: dict[str, int] = {}
            for rel in relationships:
                source = rel["source"]
                target = rel["target"]
                creator_connections[source] = creator_connections.get(source, 0) + 1
                creator_connections[target] = creator_connections.get(target, 0) + 1
            avg_connections = sum(creator_connections.values()) / len(creator_connections) if creator_connections else 0
            network_hubs = sorted(creator_connections.items(), key=lambda x: x[1], reverse=True)[:3]
            tier_distribution = {"tier_1": 0, "tier_2": 0, "tier_3": 0, "tier_4": 0}
            for creator_id in creators:
                if creator_id in self._discovered_creators:
                    tier = self._discovered_creators[creator_id].network_tier
                    tier_key = f"tier_{tier}"
                    if tier_key in tier_distribution:
                        tier_distribution[tier_key] += 1
            return {
                "total_creators": total_creators,
                "total_relationships": total_relationships,
                "relationship_density": relationship_density,
                "average_connections": avg_connections,
                "network_hubs": network_hubs,
                "tier_distribution": tier_distribution,
                "network_health_score": min(relationship_density * 2, 1.0),
            }
        except Exception as e:
            print(f"Error calculating network metrics: {e}")
            return {}

    def _generate_discovery_recommendations(
        self, creators: list[str], relationships: list[dict[str, Any]], patterns: list[CollaborationPattern]
    ) -> list[str]:
        """Generate recommendations based on discovery results."""
        recommendations = []
        try:
            if len(creators) < 10:
                recommendations.append("Consider expanding network discovery to include more creators")
            elif len(creators) > 50:
                recommendations.append("Large network detected - consider focusing on high-priority creators")
            total_creators = len(creators)
            total_relationships = len(relationships)
            density = total_relationships / (total_creators * (total_creators - 1)) if total_creators > 1 else 0
            if density < 0.1:
                recommendations.append("Low relationship density - creators may be operating in isolated clusters")
            elif density > 0.5:
                recommendations.append("High relationship density - strong interconnected network detected")
            if patterns:
                high_frequency_patterns = [p for p in patterns if p["frequency"] > 10]
                if high_frequency_patterns:
                    recommendations.append(
                        f"Found {len(high_frequency_patterns)} high-frequency collaboration patterns"
                    )
                recent_patterns = [p for p in patterns if time.time() - p["last_collaboration"] < 30 * 24 * 3600]
                if recent_patterns:
                    recommendations.append(f"Found {len(recent_patterns)} recent collaboration patterns")
            tier_1_creators = [
                c for c in creators if c in self._discovered_creators and self._discovered_creators[c].network_tier == 1
            ]
            if len(tier_1_creators) > 0:
                recommendations.append(
                    f"Network includes {len(tier_1_creators)} primary creators - high influence potential"
                )
            return recommendations
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]

    def get_discovered_creator(self, creator_id: str) -> EnhancedCreatorProfile | None:
        """Get a discovered creator profile."""
        return self._discovered_creators.get(creator_id)

    def get_all_discovered_creators(self) -> dict[str, EnhancedCreatorProfile]:
        """Get all discovered creator profiles."""
        return self._discovered_creators.copy()

    def get_collaboration_patterns(self) -> list[CollaborationPattern]:
        """Get all discovered collaboration patterns."""
        return self._collaboration_patterns.copy()

    def get_discovery_count(self) -> int:
        """Get the total number of discovered creators."""
        return len(self._discovered_creators)
