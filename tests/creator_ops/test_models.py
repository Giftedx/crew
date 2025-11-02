"""
Tests for Creator Operations data models.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ultimate_discord_intelligence_bot.creator_ops.models import (
    Account,
    BaseModel,
    Claim,
    Interaction,
    Media,
    Topic,
    Unit,
)


@pytest.fixture
def test_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


class TestAccount:
    """Test Account model."""

    def test_create_account(self, test_session):
        """Test creating an account."""
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@h3podcast",
            display_name="H3 Podcast",
            platform_id="UCGmFY9KzQwQdL6yJGHd4VvQ",
        )
        test_session.add(account)
        test_session.commit()

        assert account.id is not None
        assert account.tenant == "test_tenant"
        assert account.platform == "youtube"
        assert account.handle == "@h3podcast"

    def test_oauth_scopes_serialization(self, test_session):
        """Test OAuth scopes serialization."""
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id",
        )

        # Test setting scopes
        scopes = ["youtube.readonly", "youtube.force-ssl"]
        account.set_oauth_scopes(scopes)
        assert account.oauth_scopes == json.dumps(scopes)

        # Test getting scopes
        retrieved_scopes = account.get_oauth_scopes()
        assert retrieved_scopes == scopes

        # Test empty scopes
        account.set_oauth_scopes([])
        assert account.get_oauth_scopes() == []

    def test_unique_constraints(self, test_session):
        """Test unique constraints."""
        # Create first account
        account1 = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id_1",
        )
        test_session.add(account1)
        test_session.commit()

        # Try to create duplicate account (should fail)
        account2 = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id_2",
        )
        test_session.add(account2)

        with pytest.raises(Exception):  # IntegrityError or similar
            test_session.commit()


class TestMedia:
    """Test Media model."""

    def test_create_media(self, test_session):
        """Test creating media."""
        # Create account first
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id",
        )
        test_session.add(account)
        test_session.commit()

        # Create media
        media = Media(
            tenant="test_tenant",
            workspace="test_workspace",
            account_id=account.id,
            platform="youtube",
            media_type="video",
            platform_id="video_id_123",
            title="Test Video",
            duration_seconds=3600,
            published_at=datetime.now(),
        )
        test_session.add(media)
        test_session.commit()

        assert media.id is not None
        assert media.title == "Test Video"
        assert media.duration_seconds == 3600
        assert media.account_id == account.id

    def test_media_relationship(self, test_session):
        """Test media-account relationship."""
        # Create account
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id",
        )
        test_session.add(account)
        test_session.commit()

        # Create media
        media = Media(
            tenant="test_tenant",
            workspace="test_workspace",
            account_id=account.id,
            platform="youtube",
            media_type="video",
            platform_id="video_id_123",
        )
        test_session.add(media)
        test_session.commit()

        # Test relationship
        assert media.account.id == account.id
        assert media in account.media


class TestUnit:
    """Test Unit model."""

    def test_create_unit(self, test_session):
        """Test creating a unit."""
        # Create account and media
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id",
        )
        test_session.add(account)
        test_session.commit()

        media = Media(
            tenant="test_tenant",
            workspace="test_workspace",
            account_id=account.id,
            platform="youtube",
            media_type="video",
            platform_id="video_id_123",
        )
        test_session.add(media)
        test_session.commit()

        # Create unit
        unit = Unit(
            tenant="test_tenant",
            workspace="test_workspace",
            media_id=media.id,
            unit_type="episode",
            title="Test Episode",
            content="This is a test transcript",
            speakers=["Ethan", "Hila"],
            start_time_seconds=0.0,
            end_time_seconds=3600.0,
        )
        test_session.add(unit)
        test_session.commit()

        assert unit.id is not None
        assert unit.unit_type == "episode"
        assert unit.speakers == ["Ethan", "Hila"]
        assert unit.start_time_seconds == 0.0


class TestInteraction:
    """Test Interaction model."""

    def test_create_interaction(self, test_session):
        """Test creating an interaction."""
        # Create account and media
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@test",
            platform_id="test_id",
        )
        test_session.add(account)
        test_session.commit()

        media = Media(
            tenant="test_tenant",
            workspace="test_workspace",
            account_id=account.id,
            platform="youtube",
            media_type="video",
            platform_id="video_id_123",
        )
        test_session.add(media)
        test_session.commit()

        # Create interaction
        interaction = Interaction(
            tenant="test_tenant",
            workspace="test_workspace",
            media_id=media.id,
            interaction_type="comment",
            platform="youtube",
            platform_id="comment_123",
            user_id="user_123",
            username="test_user",
            content="Great video!",
            timestamp=datetime.now(),
        )
        test_session.add(interaction)
        test_session.commit()

        assert interaction.id is not None
        assert interaction.interaction_type == "comment"
        assert interaction.content == "Great video!"


class TestDatabaseFunctions:
    """Test database utility functions."""

    def test_create_database_engine_success(self):
        """Test successful engine creation."""
        result = create_database_engine("sqlite:///:memory:")
        assert result.success
        assert "engine" in result.data

    def test_create_database_engine_failure(self):
        """Test engine creation failure."""
        result = create_database_engine("invalid://url")
        assert not result.success
        assert "Failed to create database engine" in result.error

    def test_create_tables_success(self, test_engine):
        """Test successful table creation."""
        result = create_tables(test_engine)
        assert result.success
        assert "Tables created successfully" in result.data["message"]

    def test_create_tables_failure(self):
        """Test table creation failure."""
        # Create engine that will fail
        engine = create_engine("sqlite:///nonexistent/path.db")
        result = create_tables(engine)
        assert not result.success
        assert "Failed to create tables" in result.error


class TestModelRelationships:
    """Test model relationships and constraints."""

    def test_full_content_pipeline(self, test_session):
        """Test creating a full content pipeline."""
        # Create account
        account = Account(
            tenant="test_tenant",
            workspace="test_workspace",
            platform="youtube",
            handle="@h3podcast",
            platform_id="h3_channel_id",
        )
        test_session.add(account)
        test_session.commit()

        # Create media
        media = Media(
            tenant="test_tenant",
            workspace="test_workspace",
            account_id=account.id,
            platform="youtube",
            media_type="video",
            platform_id="video_123",
            title="H3 Podcast #123",
            duration_seconds=7200,
            published_at=datetime.now(),
        )
        test_session.add(media)
        test_session.commit()

        # Create unit
        unit = Unit(
            tenant="test_tenant",
            workspace="test_workspace",
            media_id=media.id,
            unit_type="episode",
            title="H3 Podcast #123",
            content="Full transcript here...",
            speakers=["Ethan", "Hila", "Dan"],
        )
        test_session.add(unit)
        test_session.commit()

        # Create topics
        topic = Topic(
            tenant="test_tenant",
            workspace="test_workspace",
            unit_id=unit.id,
            topic_type="main_topic",
            text="AI and Technology",
            confidence=0.95,
        )
        test_session.add(topic)
        test_session.commit()

        # Create claim
        claim = Claim(
            tenant="test_tenant",
            workspace="test_workspace",
            unit_id=unit.id,
            claim_text="AI will replace all jobs in 5 years",
            stance="supporting",
            confidence=0.8,
            uncertainty=0.3,
        )
        test_session.add(claim)
        test_session.commit()

        # Create interaction
        interaction = Interaction(
            tenant="test_tenant",
            workspace="test_workspace",
            media_id=media.id,
            unit_id=unit.id,
            interaction_type="comment",
            platform="youtube",
            platform_id="comment_456",
            content="Interesting take on AI!",
        )
        test_session.add(interaction)
        test_session.commit()

        # Verify relationships
        assert len(account.media) == 1
        assert len(media.units) == 1
        assert len(unit.topics) == 1
        assert len(unit.claims) == 1
        assert len(media.interactions) == 1

        # Verify data integrity
        assert media.account.handle == "@h3podcast"
        assert unit.media.title == "H3 Podcast #123"
        assert topic.unit.content.startswith("Full transcript")
        assert claim.unit.title == "H3 Podcast #123"
