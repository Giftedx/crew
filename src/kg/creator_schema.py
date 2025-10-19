"""Creator-focused knowledge graph schema extensions.

This module defines the extended schema for creator intelligence, including
14 creator node types and 16 edge types for comprehensive content modeling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CreatorNodeType:
    """Definition of a creator node type."""

    name: str
    description: str
    required_attrs: list[str]
    optional_attrs: list[str]
    examples: list[str]


@dataclass
class CreatorEdgeType:
    """Definition of a creator edge type."""

    name: str
    description: str
    source_types: list[str]
    target_types: list[str]
    weight_range: tuple[float, float]
    examples: list[str]


# Creator Node Types (14 total)
CREATOR_NODE_TYPES = [
    CreatorNodeType(
        name="creator",
        description="Content creator (YouTuber, streamer, podcaster)",
        required_attrs=["platform", "channel_id", "subscriber_count"],
        optional_attrs=["bio", "location", "language", "category", "monetization_status"],
        examples=["H3 Podcast", "Ethan Klein", "Hasan Piker"],
    ),
    CreatorNodeType(
        name="episode",
        description="Individual content episode (video, stream, podcast)",
        required_attrs=["title", "duration", "upload_date", "platform"],
        optional_attrs=["description", "view_count", "like_count", "comment_count", "tags", "url"],
        examples=["H3 Podcast #123", "Hasan's Stream - 2024-01-15"],
    ),
    CreatorNodeType(
        name="guest",
        description="Guest appearing on creator content",
        required_attrs=["name", "role"],
        optional_attrs=["bio", "social_links", "expertise", "appearance_count"],
        examples=["Joe Rogan", "Alex Jones", "Bella Poarch"],
    ),
    CreatorNodeType(
        name="topic",
        description="Subject matter discussed in content",
        required_attrs=["name", "category"],
        optional_attrs=["description", "trending_score", "sentiment", "complexity", "mentions"],
        examples=["Politics", "Gaming", "Conspiracy Theories", "Social Media Drama"],
    ),
    CreatorNodeType(
        name="claim",
        description="Factual claim or statement made in content",
        required_attrs=["text", "speaker", "timestamp", "confidence"],
        optional_attrs=["verification_status", "source_urls", "controversy_score"],
        examples=["The election was stolen", "Climate change is real", "This product works"],
    ),
    CreatorNodeType(
        name="quote",
        description="Notable quote or soundbite from content",
        required_attrs=["text", "speaker", "timestamp", "context"],
        optional_attrs=["viral_potential", "sentiment", "reaction_count"],
        examples=["I'm not a conspiracy theorist", "That's crazy", "Let's go Brandon"],
    ),
    CreatorNodeType(
        name="highlight",
        description="Notable moment or clip from content",
        required_attrs=["start_time", "end_time", "description", "episode_id"],
        optional_attrs=["view_count", "share_count", "reaction_type", "viral_score", "confidence"],
        examples=["Ethan's rant about Twitter", "Hasan's reaction to news", "Funny moment"],
    ),
    CreatorNodeType(
        name="sponsor",
        description="Sponsor or advertiser mentioned in content",
        required_attrs=["name", "product", "mention_type"],
        optional_attrs=["website", "industry", "disclosure_status", "promo_code"],
        examples=["Raid Shadow Legends", "NordVPN", "Honey", "Audible"],
    ),
    CreatorNodeType(
        name="event",
        description="Real-world event referenced in content",
        required_attrs=["name", "date", "type"],
        optional_attrs=["location", "impact", "relevance_score", "source_urls"],
        examples=["2020 Election", "COVID-19 Pandemic", "Twitter Acquisition"],
    ),
    CreatorNodeType(
        name="person",
        description="Person mentioned or discussed in content",
        required_attrs=["name", "role"],
        optional_attrs=["bio", "political_affiliation", "controversy_level", "social_links"],
        examples=["Donald Trump", "Elon Musk", "Joe Biden", "Andrew Tate"],
    ),
    CreatorNodeType(
        name="organization",
        description="Organization, company, or institution mentioned",
        required_attrs=["name", "type"],
        optional_attrs=["industry", "size", "reputation", "website"],
        examples=["Twitter", "Tesla", "White House", "FBI"],
    ),
    CreatorNodeType(
        name="product",
        description="Product, service, or technology mentioned",
        required_attrs=["name", "category"],
        optional_attrs=["brand", "price", "rating", "availability"],
        examples=["iPhone", "ChatGPT", "Tesla Model 3", "OnlyFans"],
    ),
    CreatorNodeType(
        name="location",
        description="Geographic location mentioned in content",
        required_attrs=["name", "type"],
        optional_attrs=["country", "coordinates", "population", "significance"],
        examples=["Los Angeles", "Ukraine", "Mar-a-Lago", "Silicon Valley"],
    ),
    CreatorNodeType(
        name="narrative",
        description="Ongoing story or narrative thread across content",
        required_attrs=["title", "start_date", "status"],
        optional_attrs=["description", "participants", "resolution", "impact_score"],
        examples=["Twitter Drama", "Election Fraud Claims", "COVID Response"],
    ),
]

# Creator Edge Types (16 total)
CREATOR_EDGE_TYPES = [
    CreatorEdgeType(
        name="hosts",
        description="Creator hosts an episode",
        source_types=["creator"],
        target_types=["episode"],
        weight_range=(1.0, 1.0),
        examples=["H3 Podcast hosts H3 Podcast #123"],
    ),
    CreatorEdgeType(
        name="features",
        description="Guest features in an episode",
        source_types=["guest"],
        target_types=["episode"],
        weight_range=(0.8, 1.0),
        examples=["Joe Rogan features in H3 Podcast #123"],
    ),
    CreatorEdgeType(
        name="discusses",
        description="Content discusses a topic",
        source_types=["episode"],
        target_types=["topic"],
        weight_range=(0.1, 1.0),
        examples=["H3 Podcast #123 discusses Politics"],
    ),
    CreatorEdgeType(
        name="makes_claim",
        description="Speaker makes a factual claim",
        source_types=["creator", "guest"],
        target_types=["claim"],
        weight_range=(0.5, 1.0),
        examples=["Ethan makes claim about election fraud"],
    ),
    CreatorEdgeType(
        name="quotes",
        description="Speaker says a notable quote",
        source_types=["creator", "guest"],
        target_types=["quote"],
        weight_range=(0.7, 1.0),
        examples=["Hasan quotes 'That's crazy'"],
    ),
    CreatorEdgeType(
        name="contains_highlight",
        description="Episode contains a highlight moment",
        source_types=["episode"],
        target_types=["highlight"],
        weight_range=(0.8, 1.0),
        examples=["H3 Podcast #123 contains highlight 'Ethan's rant'"],
    ),
    CreatorEdgeType(
        name="promotes",
        description="Content promotes a sponsor",
        source_types=["episode"],
        target_types=["sponsor"],
        weight_range=(0.6, 1.0),
        examples=["H3 Podcast #123 promotes NordVPN"],
    ),
    CreatorEdgeType(
        name="references",
        description="Content references an event",
        source_types=["episode"],
        target_types=["event"],
        weight_range=(0.3, 1.0),
        examples=["H3 Podcast #123 references 2020 Election"],
    ),
    CreatorEdgeType(
        name="mentions",
        description="Content mentions a person",
        source_types=["episode"],
        target_types=["person"],
        weight_range=(0.2, 1.0),
        examples=["H3 Podcast #123 mentions Donald Trump"],
    ),
    CreatorEdgeType(
        name="belongs_to",
        description="Entity belongs to an organization",
        source_types=["person", "product"],
        target_types=["organization"],
        weight_range=(0.5, 1.0),
        examples=["Elon Musk belongs to Tesla"],
    ),
    CreatorEdgeType(
        name="manufactures",
        description="Organization manufactures a product",
        source_types=["organization"],
        target_types=["product"],
        weight_range=(0.8, 1.0),
        examples=["Apple manufactures iPhone"],
    ),
    CreatorEdgeType(
        name="located_in",
        description="Entity is located in a place",
        source_types=["person", "organization", "event"],
        target_types=["location"],
        weight_range=(0.6, 1.0),
        examples=["Tesla located in Silicon Valley"],
    ),
    CreatorEdgeType(
        name="contradicts",
        description="Claim contradicts another claim",
        source_types=["claim"],
        target_types=["claim"],
        weight_range=(0.7, 1.0),
        examples=["Claim A contradicts Claim B"],
    ),
    CreatorEdgeType(
        name="supports",
        description="Claim supports another claim",
        source_types=["claim"],
        target_types=["claim"],
        weight_range=(0.6, 1.0),
        examples=["Claim A supports Claim B"],
    ),
    CreatorEdgeType(
        name="part_of_narrative",
        description="Content is part of a larger narrative",
        source_types=["episode", "claim", "quote"],
        target_types=["narrative"],
        weight_range=(0.3, 1.0),
        examples=["H3 Podcast #123 part of Twitter Drama narrative"],
    ),
    CreatorEdgeType(
        name="collaborates_with",
        description="Creators collaborate on content",
        source_types=["creator"],
        target_types=["creator"],
        weight_range=(0.4, 1.0),
        examples=["H3 Podcast collaborates with Hasan"],
    ),
]


# Schema validation functions
def validate_node_type(node_type: str) -> bool:
    """Validate that a node type is in the creator schema."""
    return any(nt.name == node_type for nt in CREATOR_NODE_TYPES)


def validate_edge_type(edge_type: str) -> bool:
    """Validate that an edge type is in the creator schema."""
    return any(et.name == edge_type for et in CREATOR_EDGE_TYPES)


def get_node_type_definition(node_type: str) -> CreatorNodeType | None:
    """Get the definition for a node type."""
    for nt in CREATOR_NODE_TYPES:
        if nt.name == node_type:
            return nt
    return None


def get_edge_type_definition(edge_type: str) -> CreatorEdgeType | None:
    """Get the definition for an edge type."""
    for et in CREATOR_EDGE_TYPES:
        if et.name == edge_type:
            return et
    return None


def validate_node_attrs(node_type: str, attrs: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate node attributes against schema."""
    definition = get_node_type_definition(node_type)
    if not definition:
        return False, [f"Unknown node type: {node_type}"]

    errors = []

    # Check required attributes
    for required_attr in definition.required_attrs:
        if required_attr not in attrs:
            errors.append(f"Missing required attribute: {required_attr}")

    # Check for unknown attributes
    all_attrs = set(definition.required_attrs + definition.optional_attrs)
    for attr in attrs:
        if attr not in all_attrs:
            errors.append(f"Unknown attribute: {attr}")

    return len(errors) == 0, errors


def validate_edge_compatibility(edge_type: str, src_type: str, dst_type: str) -> bool:
    """Validate that an edge type is compatible with source and target node types."""
    definition = get_edge_type_definition(edge_type)
    if not definition:
        return False

    return src_type in definition.source_types and dst_type in definition.target_types


# Migration utilities
def get_schema_migration_sql() -> list[str]:
    """Get SQL statements for schema migration."""
    return [
        # Add indexes for better performance
        "CREATE INDEX IF NOT EXISTS idx_kg_nodes_tenant_type ON kg_nodes(tenant, type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_nodes_tenant_name ON kg_nodes(tenant, name)",
        "CREATE INDEX IF NOT EXISTS idx_kg_edges_src_type ON kg_edges(src_id, type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_edges_dst_type ON kg_edges(dst_id, type)",
        "CREATE INDEX IF NOT EXISTS idx_kg_edges_type ON kg_edges(type)",
        # Add constraints for data integrity
        "CREATE INDEX IF NOT EXISTS idx_kg_provenance_node_id ON kg_provenance(node_id)",
    ]


def get_schema_validation_queries() -> list[str]:
    """Get queries for validating schema integrity."""
    return [
        # Check for orphaned edges
        """
        SELECT COUNT(*) as orphaned_edges
        FROM kg_edges e
        LEFT JOIN kg_nodes n1 ON e.src_id = n1.id
        LEFT JOIN kg_nodes n2 ON e.dst_id = n2.id
        WHERE n1.id IS NULL OR n2.id IS NULL
        """,
        # Check for nodes with invalid types
        f"""
        SELECT COUNT(*) as invalid_node_types
        FROM kg_nodes n
        WHERE n.type NOT IN ({", ".join(f"'{nt.name}'" for nt in CREATOR_NODE_TYPES)})
        """,
        # Check for edges with invalid types
        f"""
        SELECT COUNT(*) as invalid_edge_types
        FROM kg_edges e
        WHERE e.type NOT IN ({", ".join(f"'{et.name}'" for et in CREATOR_EDGE_TYPES)})
        """,
    ]
