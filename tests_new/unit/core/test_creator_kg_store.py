"""Tests for the creator KG store and schema."""

import pytest

from src.kg.creator_kg_store import CreatorKGStore
from src.kg.creator_schema import (
    CREATOR_EDGE_TYPES,
    CREATOR_NODE_TYPES,
    validate_edge_compatibility,
    validate_edge_type,
    validate_node_attrs,
    validate_node_type,
)


class TestCreatorSchema:
    """Test creator schema validation."""

    def test_validate_node_type(self) -> None:
        """Test node type validation."""
        assert validate_node_type("creator")
        assert validate_node_type("episode")
        assert validate_node_type("topic")
        assert not validate_node_type("invalid_type")

    def test_validate_edge_type(self) -> None:
        """Test edge type validation."""
        assert validate_edge_type("hosts")
        assert validate_edge_type("discusses")
        assert validate_edge_type("makes_claim")
        assert not validate_edge_type("invalid_edge")

    def test_validate_node_attrs(self) -> None:
        """Test node attribute validation."""
        # Valid creator attributes
        attrs = {
            "platform": "YouTube",
            "channel_id": "test123",
            "subscriber_count": 1000000,
            "bio": "Test creator",
        }
        is_valid, errors = validate_node_attrs("creator", attrs)
        assert is_valid
        assert len(errors) == 0

        # Missing required attribute
        attrs = {"platform": "YouTube"}
        is_valid, errors = validate_node_attrs("creator", attrs)
        assert not is_valid
        assert "Missing required attribute: channel_id" in errors

        # Unknown attribute
        attrs = {
            "platform": "YouTube",
            "channel_id": "test123",
            "subscriber_count": 1000000,
            "unknown_attr": "value",
        }
        is_valid, errors = validate_node_attrs("creator", attrs)
        assert not is_valid
        assert "Unknown attribute: unknown_attr" in errors

    def test_validate_edge_compatibility(self) -> None:
        """Test edge compatibility validation."""
        assert validate_edge_compatibility("hosts", "creator", "episode")
        assert validate_edge_compatibility("discusses", "episode", "topic")
        assert validate_edge_compatibility("makes_claim", "creator", "claim")
        assert not validate_edge_compatibility("hosts", "episode", "creator")
        assert not validate_edge_compatibility("invalid_edge", "creator", "episode")


class TestCreatorKGStore:
    """Test CreatorKGStore implementation."""

    @pytest.fixture
    def store(self) -> CreatorKGStore:
        """Create a temporary KG store for testing."""
        return CreatorKGStore(":memory:")

    def test_add_creator_node(self, store: CreatorKGStore) -> None:
        """Test adding creator nodes with validation."""
        # Valid creator node
        node_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )
        assert node_id > 0

        # Invalid node type
        with pytest.raises(ValueError, match="Invalid node type"):
            store.add_creator_node(
                tenant="test",
                node_type="invalid_type",
                name="Test",
                attrs={},
            )

        # Invalid attributes
        with pytest.raises(ValueError, match="Invalid node attributes"):
            store.add_creator_node(
                tenant="test",
                node_type="creator",
                name="Test",
                attrs={"platform": "YouTube"},  # Missing required attributes
            )

    def test_add_creator_edge(self, store: CreatorKGStore) -> None:
        """Test adding creator edges with validation."""
        # Create nodes first
        creator_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )

        episode_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Test Episode",
            attrs={
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        # Valid edge
        edge_id = store.add_creator_edge(creator_id, episode_id, "hosts")
        assert edge_id > 0

        # Invalid edge type
        with pytest.raises(ValueError, match="Invalid edge type"):
            store.add_creator_edge(creator_id, episode_id, "invalid_edge")

        # Incompatible edge
        with pytest.raises(ValueError, match="not compatible"):
            store.add_creator_edge(episode_id, creator_id, "hosts")

    def test_get_creator_nodes(self, store: CreatorKGStore) -> None:
        """Test getting creator nodes with filtering."""
        # Add test nodes
        store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )

        store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Test Episode",
            attrs={
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        # Get all nodes
        all_nodes = store.get_creator_nodes("test")
        assert len(all_nodes) == 2

        # Get nodes by type
        creator_nodes = store.get_creator_nodes("test", node_type="creator")
        assert len(creator_nodes) == 1
        assert creator_nodes[0].name == "Test Creator"

        episode_nodes = store.get_creator_nodes("test", node_type="episode")
        assert len(episode_nodes) == 1
        assert episode_nodes[0].name == "Test Episode"

    def test_get_episode_timeline(self, store: CreatorKGStore) -> None:
        """Test getting episode timeline for a creator."""
        # Create creator
        creator_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )

        # Create episodes
        episode1_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Episode 1",
            attrs={
                "title": "Episode 1",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        episode2_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Episode 2",
            attrs={
                "title": "Episode 2",
                "duration": 3600,
                "upload_date": "2024-01-02",
                "platform": "YouTube",
            },
        )

        # Create edges
        store.add_creator_edge(creator_id, episode1_id, "hosts")
        store.add_creator_edge(creator_id, episode2_id, "hosts")

        # Get timeline
        timeline = store.get_episode_timeline("test", creator_id)
        assert len(timeline) == 2
        # Should be ordered by upload_date DESC
        assert timeline[0].name == "Episode 2"
        assert timeline[1].name == "Episode 1"

    def test_get_episode_highlights(self, store: CreatorKGStore) -> None:
        """Test getting highlights for an episode."""
        # Create episode
        episode_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Test Episode",
            attrs={
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        # Create highlights
        highlight1_id = store.add_creator_node(
            tenant="test",
            node_type="highlight",
            name="Highlight 1",
            attrs={
                "start_time": 300,
                "end_time": 600,
                "description": "Funny moment",
                "episode_id": episode_id,
            },
        )

        highlight2_id = store.add_creator_node(
            tenant="test",
            node_type="highlight",
            name="Highlight 2",
            attrs={
                "start_time": 1200,
                "end_time": 1500,
                "description": "Another moment",
                "episode_id": episode_id,
            },
        )

        # Create edges
        store.add_creator_edge(episode_id, highlight1_id, "contains_highlight")
        store.add_creator_edge(episode_id, highlight2_id, "contains_highlight")

        # Get highlights
        highlights = store.get_episode_highlights("test", episode_id)
        assert len(highlights) == 2
        # Should be ordered by start_time ASC
        assert highlights[0].name == "Highlight 1"
        assert highlights[1].name == "Highlight 2"

    def test_get_creator_collaborations(self, store: CreatorKGStore) -> None:
        """Test getting creator collaborations."""
        # Create creators
        creator1_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Creator 1",
            attrs={
                "platform": "YouTube",
                "channel_id": "test1",
                "subscriber_count": 1000000,
            },
        )

        creator2_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Creator 2",
            attrs={
                "platform": "YouTube",
                "channel_id": "test2",
                "subscriber_count": 2000000,
            },
        )

        # Create collaboration edge
        store.add_creator_edge(creator1_id, creator2_id, "collaborates_with")

        # Get collaborations
        collaborations = store.get_creator_collaborations("test", creator1_id)
        assert len(collaborations) == 1
        assert collaborations[0][0].name == "Creator 1"
        assert collaborations[0][1].name == "Creator 2"

    def test_get_topic_mentions(self, store: CreatorKGStore) -> None:
        """Test getting episodes that mention a topic."""
        # Create topic
        topic_id = store.add_creator_node(
            tenant="test",
            node_type="topic",
            name="Politics",
            attrs={
                "name": "Politics",
                "category": "Current Events",
                "trending_score": 0.8,
            },
        )

        # Create episodes
        episode1_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Episode 1",
            attrs={
                "title": "Episode 1",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        episode2_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Episode 2",
            attrs={
                "title": "Episode 2",
                "duration": 3600,
                "upload_date": "2024-01-02",
                "platform": "YouTube",
            },
        )

        # Create edges
        store.add_creator_edge(episode1_id, topic_id, "discusses")
        store.add_creator_edge(episode2_id, topic_id, "discusses")

        # Get topic mentions
        mentions = store.get_topic_mentions("test", topic_id)
        assert len(mentions) == 2
        # Should be ordered by upload_date DESC
        assert mentions[0][0].name == "Episode 2"
        assert mentions[1][0].name == "Episode 1"

    def test_get_claim_verification_graph(self, store: CreatorKGStore) -> None:
        """Test getting claim verification graph."""
        # Create claims
        claim1_id = store.add_creator_node(
            tenant="test",
            node_type="claim",
            name="Claim 1",
            attrs={
                "text": "The sky is blue",
                "speaker": "Test Speaker",
                "timestamp": 1800,
                "confidence": 0.9,
            },
        )

        claim2_id = store.add_creator_node(
            tenant="test",
            node_type="claim",
            name="Claim 2",
            attrs={
                "text": "The sky is not blue",
                "speaker": "Test Speaker",
                "timestamp": 1900,
                "confidence": 0.1,
            },
        )

        claim3_id = store.add_creator_node(
            tenant="test",
            node_type="claim",
            name="Claim 3",
            attrs={
                "text": "The sky is definitely blue",
                "speaker": "Test Speaker",
                "timestamp": 2000,
                "confidence": 0.95,
            },
        )

        # Create edges
        store.add_creator_edge(claim1_id, claim3_id, "supports")
        store.add_creator_edge(claim1_id, claim2_id, "contradicts")

        # Get verification graph
        graph = store.get_claim_verification_graph("test", claim1_id)
        assert len(graph["original_claim"]) == 1
        assert len(graph["supporting_claims"]) == 1
        assert len(graph["contradicting_claims"]) == 1
        assert graph["original_claim"][0].name == "Claim 1"
        assert graph["supporting_claims"][0].name == "Claim 3"
        assert graph["contradicting_claims"][0].name == "Claim 2"

    def test_validate_schema_integrity(self, store: CreatorKGStore) -> None:
        """Test schema integrity validation."""
        # Add some test data
        creator_id = store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )

        episode_id = store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Test Episode",
            attrs={
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        store.add_creator_edge(creator_id, episode_id, "hosts")

        # Validate integrity
        integrity = store.validate_schema_integrity()
        assert "orphaned_edges" in integrity
        assert "invalid_node_types" in integrity
        assert "invalid_edge_types" in integrity

    def test_get_schema_stats(self, store: CreatorKGStore) -> None:
        """Test getting schema statistics."""
        # Add some test data
        store.add_creator_node(
            tenant="test",
            node_type="creator",
            name="Test Creator",
            attrs={
                "platform": "YouTube",
                "channel_id": "test123",
                "subscriber_count": 1000000,
            },
        )

        store.add_creator_node(
            tenant="test",
            node_type="episode",
            name="Test Episode",
            attrs={
                "title": "Test Episode",
                "duration": 3600,
                "upload_date": "2024-01-01",
                "platform": "YouTube",
            },
        )

        # Get stats
        stats = store.get_schema_stats()
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "node_type_counts" in stats
        assert "edge_type_counts" in stats
        assert "schema_version" in stats
        assert stats["total_nodes"] == 2
        assert stats["node_type_counts"]["creator"] == 1
        assert stats["node_type_counts"]["episode"] == 1


class TestCreatorSchemaDefinitions:
    """Test creator schema definitions."""

    def test_node_types_count(self) -> None:
        """Test that we have exactly 14 node types."""
        assert len(CREATOR_NODE_TYPES) == 14

    def test_edge_types_count(self) -> None:
        """Test that we have exactly 16 edge types."""
        assert len(CREATOR_EDGE_TYPES) == 16

    def test_node_types_have_required_attrs(self) -> None:
        """Test that all node types have required attributes."""
        for node_type in CREATOR_NODE_TYPES:
            assert len(node_type.required_attrs) > 0
            assert len(node_type.examples) > 0

    def test_edge_types_have_compatible_types(self) -> None:
        """Test that all edge types have compatible source and target types."""
        for edge_type in CREATOR_EDGE_TYPES:
            assert len(edge_type.source_types) > 0
            assert len(edge_type.target_types) > 0
            assert edge_type.weight_range[0] <= edge_type.weight_range[1]
