"""Enhanced creator profile schema for network intelligence system."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .schema import CreatorProfile, Platforms, VerificationEvent


@dataclass
class CollaborationEvent:
    """Record of a collaboration between creators."""

    collaborator_id: str
    collaboration_type: str  # "guest", "co-host", "interview", "debate", "collab_video"
    content_id: str
    platform: str
    date: datetime
    duration_minutes: float | None = None
    topic: str | None = None
    chemistry_score: float | None = None  # 0-1 rating of collaboration quality
    audience_reception: dict[str, Any] | None = None  # engagement metrics

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["date"] = self.date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CollaborationEvent:
        data["date"] = datetime.fromisoformat(data["date"])
        return cls(**data)


@dataclass
class SocialGraphMetrics:
    """Social graph analysis metrics for a creator."""

    centrality_score: float  # How central they are in the network
    influence_score: float  # How much they influence others
    reach_score: float  # How many people they can reach
    community_cluster: str | None = None  # Which community cluster they belong to
    bridge_score: float | None = None  # How much they bridge different communities
    authority_score: float | None = None  # How authoritative they are in their domain

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SocialGraphMetrics:
        return cls(**data)


@dataclass
class ContentCharacteristics:
    """Content characteristics and patterns for a creator."""

    content_frequency: dict[str, float] = field(default_factory=dict)  # platform -> posts/week
    typical_topics: list[str] = field(default_factory=list)
    typical_format: list[str] = field(default_factory=list)  # ["long-form", "clips", "stories", "threads"]
    audience_overlap: dict[str, float] = field(default_factory=dict)  # overlap with other creators
    content_quality_score: float | None = None  # 0-1 overall quality rating
    engagement_rate: dict[str, float] = field(default_factory=dict)  # platform -> avg engagement rate
    viral_potential: float | None = None  # 0-1 likelihood of content going viral

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentCharacteristics:
        return cls(**data)


@dataclass
class InteractionTracking:
    """Track interactions and mentions between creators."""

    mentions_count: dict[str, int] = field(default_factory=dict)  # who they mention
    mentioned_by_count: dict[str, int] = field(default_factory=dict)  # who mentions them
    collaboration_history: list[CollaborationEvent] = field(default_factory=list)
    last_interaction: dict[str, datetime] = field(default_factory=dict)  # last interaction with each creator
    interaction_sentiment: dict[str, float] = field(default_factory=dict)  # sentiment of interactions

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["collaboration_history"] = [c.to_dict() for c in self.collaboration_history]
        data["last_interaction"] = {k: v.isoformat() for k, v in self.last_interaction.items()}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InteractionTracking:
        data["collaboration_history"] = [CollaborationEvent.from_dict(c) for c in data["collaboration_history"]]
        data["last_interaction"] = {k: datetime.fromisoformat(v) for k, v in data["last_interaction"].items()}
        return cls(**data)


@dataclass
class EnhancedCreatorProfile(CreatorProfile):
    """Enhanced creator profile with comprehensive network tracking."""

    # Network relationships
    network_tier: int = 1  # 1=primary (H3/Hasan), 2=co-hosts/staff, 3=frequent guests, 4=extended
    relationship_type: list[str] = field(
        default_factory=list
    )  # ["co-host", "staff", "guest", "friend", "collaborator"]
    social_graph_position: SocialGraphMetrics | None = None

    # Multi-platform presence
    instagram_handle: str | None = None
    instagram_stories_enabled: bool = False
    tiktok_handle: str | None = None
    twitter_x_handle: str | None = None

    # Enhanced content characteristics
    content_characteristics: ContentCharacteristics = field(default_factory=ContentCharacteristics)

    # Interaction tracking
    interaction_tracking: InteractionTracking = field(default_factory=InteractionTracking)

    # Additional metadata
    discovery_date: datetime | None = None
    last_network_update: datetime | None = None
    network_confidence: float = 0.0  # 0-1 confidence in network mapping
    monitoring_priority: int = 1  # 1=highest, 5=lowest

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data["social_graph_position"] = self.social_graph_position.to_dict() if self.social_graph_position else None
        data["content_characteristics"] = self.content_characteristics.to_dict()
        data["interaction_tracking"] = self.interaction_tracking.to_dict()
        if self.discovery_date:
            data["discovery_date"] = self.discovery_date.isoformat()
        if self.last_network_update:
            data["last_network_update"] = self.last_network_update.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnhancedCreatorProfile:
        # Handle base CreatorProfile fields
        base_data = {
            k: v
            for k, v in data.items()
            if k
            not in [
                "social_graph_position",
                "content_characteristics",
                "interaction_tracking",
                "discovery_date",
                "last_network_update",
            ]
        }
        base_profile = CreatorProfile.from_dict(base_data)

        # Create enhanced profile
        profile = cls(
            name=base_profile.name,
            known_as=base_profile.known_as,
            type=base_profile.type,
            roles=base_profile.roles,
            shows=base_profile.shows,
            description=base_profile.description,
            content_tags=base_profile.content_tags,
            platforms=base_profile.platforms,
            frequent_collaborators=base_profile.frequent_collaborators,
            last_verified_at=base_profile.last_verified_at,
            verification_log=base_profile.verification_log,
            last_checked=base_profile.last_checked,
            network_tier=data.get("network_tier", 1),
            relationship_type=data.get("relationship_type", []),
            instagram_handle=data.get("instagram_handle"),
            instagram_stories_enabled=data.get("instagram_stories_enabled", False),
            tiktok_handle=data.get("tiktok_handle"),
            twitter_x_handle=data.get("twitter_x_handle"),
            discovery_date=datetime.fromisoformat(data["discovery_date"]) if data.get("discovery_date") else None,
            last_network_update=datetime.fromisoformat(data["last_network_update"])
            if data.get("last_network_update")
            else None,
            network_confidence=data.get("network_confidence", 0.0),
            monitoring_priority=data.get("monitoring_priority", 1),
        )

        # Set complex objects
        if data.get("social_graph_position"):
            profile.social_graph_position = SocialGraphMetrics.from_dict(data["social_graph_position"])
        if data.get("content_characteristics"):
            profile.content_characteristics = ContentCharacteristics.from_dict(data["content_characteristics"])
        if data.get("interaction_tracking"):
            profile.interaction_tracking = InteractionTracking.from_dict(data["interaction_tracking"])

        return profile


# Core Creator Definitions
PRIMARY_CREATORS = {
    "h3_podcast": {
        "name": "H3 Podcast",
        "known_as": "H3",
        "type": "show",
        "hosts": ["ethan_klein", "hila_klein"],
        "platforms": ["youtube", "tiktok", "instagram", "twitter"],
        "youtube_channels": ["@h3h3Productions", "@H3Podcast"],
        "staff": ["dan", "ab", "zach", "olivia", "ian", "lena", "sam"],
        "network_tier": 1,
        "relationship_type": ["primary_show"],
        "monitoring_priority": 1,
    },
    "ethan_klein": {
        "name": "Ethan Klein",
        "known_as": "Ethan",
        "type": "person",
        "platforms": ["youtube", "tiktok", "instagram", "twitter"],
        "shows": ["H3 Podcast", "H3TV"],
        "network_tier": 1,
        "relationship_type": ["primary_creator", "host"],
        "monitoring_priority": 1,
    },
    "hila_klein": {
        "name": "Hila Klein",
        "known_as": "Hila",
        "type": "person",
        "platforms": ["youtube", "instagram", "twitter"],
        "shows": ["H3 Podcast", "H3TV"],
        "network_tier": 1,
        "relationship_type": ["primary_creator", "host"],
        "monitoring_priority": 1,
    },
    "hasan_piker": {
        "name": "HasanAbi",
        "known_as": "Hasan",
        "type": "person",
        "platforms": ["twitch", "youtube", "twitter", "tiktok"],
        "twitch_channel": "hasanabi",
        "youtube_channel": "@HasanAbi",
        "network_tier": 1,
        "relationship_type": ["primary_creator", "streamer"],
        "monitoring_priority": 1,
    },
}

# H3 Staff and Collaborators
H3_NETWORK = {
    "dan": {
        "name": "Dan",
        "known_as": "Dan",
        "type": "person",
        "platforms": ["youtube", "twitter"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "producer"],
        "monitoring_priority": 2,
    },
    "ab": {
        "name": "AB",
        "known_as": "AB",
        "type": "person",
        "platforms": ["youtube", "twitter", "instagram"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "researcher"],
        "monitoring_priority": 2,
    },
    "zach": {
        "name": "Zach",
        "known_as": "Zach",
        "type": "person",
        "platforms": ["youtube", "twitter"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "sound_engineer"],
        "monitoring_priority": 2,
    },
    "olivia": {
        "name": "Olivia",
        "known_as": "Olivia",
        "type": "person",
        "platforms": ["youtube", "twitter", "instagram"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "researcher"],
        "monitoring_priority": 2,
    },
    "ian": {
        "name": "Ian",
        "known_as": "Ian",
        "type": "person",
        "platforms": ["youtube", "twitter"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "camera_operator"],
        "monitoring_priority": 2,
    },
    "lena": {
        "name": "Lena",
        "known_as": "Lena",
        "type": "person",
        "platforms": ["youtube", "twitter", "instagram"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "researcher"],
        "monitoring_priority": 2,
    },
    "sam": {
        "name": "Sam",
        "known_as": "Sam",
        "type": "person",
        "platforms": ["youtube", "twitter"],
        "shows": ["H3 Podcast"],
        "network_tier": 2,
        "relationship_type": ["staff", "researcher"],
        "monitoring_priority": 2,
    },
}

# Hasan's Network
HASAN_NETWORK = {
    "will_neff": {
        "name": "Will Neff",
        "known_as": "Will",
        "type": "person",
        "platforms": ["twitch", "youtube", "twitter"],
        "network_tier": 2,
        "relationship_type": ["friend", "collaborator"],
        "monitoring_priority": 2,
    },
    "qt_cinderella": {
        "name": "QT Cinderella",
        "known_as": "QT",
        "type": "person",
        "platforms": ["twitch", "youtube", "twitter", "instagram"],
        "network_tier": 2,
        "relationship_type": ["friend", "collaborator"],
        "monitoring_priority": 2,
    },
}

# Combine all networks
ALL_CREATOR_NETWORKS = {**PRIMARY_CREATORS, **H3_NETWORK, **HASAN_NETWORK}


def create_enhanced_profile_from_config(creator_id: str, config: dict[str, Any]) -> EnhancedCreatorProfile:
    """Create an enhanced creator profile from configuration data."""

    # Create base platforms
    platforms = Platforms()
    if "youtube_channels" in config:
        platforms.youtube = config["youtube_channels"][0] if config["youtube_channels"] else None
    if "twitch_channel" in config:
        platforms.twitch = config["twitch_channel"]

    # Create enhanced profile
    created_at = datetime.utcnow()

    profile = EnhancedCreatorProfile(
        name=config["name"],
        known_as=config.get("known_as"),
        type=config.get("type", "person"),
        roles=config.get("roles", []),
        shows=config.get("shows", []),
        platforms=platforms,
        network_tier=config.get("network_tier", 1),
        relationship_type=config.get("relationship_type", []),
        instagram_handle=config.get("instagram_handle"),
        instagram_stories_enabled=config.get("instagram_stories_enabled", False),
        tiktok_handle=config.get("tiktok_handle"),
        twitter_x_handle=config.get("twitter_x_handle"),
        discovery_date=created_at,
        monitoring_priority=config.get("monitoring_priority", 1),
    )

    profile.verification_log.append(
        VerificationEvent(
            timestamp=created_at,
            status="seeded",
            details=f"Profile initialized from creator registry entry '{creator_id}'.",
        )
    )

    return profile
