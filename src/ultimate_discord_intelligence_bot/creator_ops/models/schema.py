"""
SQLAlchemy models for Creator Operations cross-platform schema.

This module defines the database schema for storing content, accounts,
interactions, and analysis results across multiple platforms.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ultimate_discord_intelligence_bot.step_result import StepResult

BaseModel = declarative_base()


class Account(BaseModel):
    """Platform account for a creator."""

    __tablename__ = "creator_ops_accounts"

    id = relationship(Integer, primary_key=True)
    tenant = relationship(String(255), nullable=False)
    workspace = relationship(String(255), nullable=False)
    platform = relationship(String(50), nullable=False)  # youtube, twitch, tiktok, instagram, x
    handle = relationship(String(255), nullable=False)
    display_name = relationship(String(255))
    platform_id = relationship(String(255), nullable=False)  # Platform-specific ID
    oauth_scopes = relationship(Text)  # JSON list of scopes
    access_token_encrypted = relationship(Text)
    refresh_token_encrypted = relationship(Text)
    token_expires_at = relationship(DateTime)
    is_active = relationship(Boolean, default=True)
    created_at = relationship(DateTime, default=func.now())
    updated_at = relationship(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    media = relationship("Media", back_populates="account")

    __table_args__ = (
        UniqueConstraint("tenant", "workspace", "platform", "handle", name="uq_tenant_workspace_platform_handle"),
        UniqueConstraint("tenant", "workspace", "platform", "platform_id", name="uq_tenant_workspace_platform_id"),
    )

    def get_oauth_scopes(self) -> list[str]:
        """Get OAuth scopes as a list."""
        if not self.oauth_scopes:
            return []
        try:
            return json.loads(self.oauth_scopes)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_oauth_scopes(self, scopes: list[str]) -> None:
        """Set OAuth scopes from a list."""
        self.oauth_scopes = json.dumps(scopes)


class Media(BaseModel):
    """Media content from platforms (videos, posts, stories)."""

    __tablename__ = "creator_ops_media"

    id = relationship(Integer, primary_key=True)
    tenant = relationship(String(255), nullable=False)
    workspace = relationship(String(255), nullable=False)
    account_id = relationship(Integer, ForeignKey("creator_ops_accounts.id"), nullable=False)
    platform = relationship(String(50), nullable=False)
    media_type = relationship(String(50), nullable=False)  # video, audio, post, story, clip
    platform_id = relationship(String(255), nullable=False)
    url = relationship(String(1000))
    title = relationship(String(500))
    description = relationship(Text)
    duration_seconds = relationship(Integer)
    file_size_bytes = relationship(Integer)
    thumbnail_url = relationship(String(1000))
    published_at = relationship(DateTime)
    media_metadata = relationship(JSON)
    is_processed = relationship(Boolean, default=False)
    processing_status = relationship(
        String(50), default="pending"
    )  # pending, processing, completed, failed
    created_at = relationship(DateTime, default=func.now())
    updated_at = relationship(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    account = relationship("Account", back_populates="media")
    units = relationship("Unit", back_populates="media")
    interactions = relationship("Interaction", back_populates="media")

    __table_args__ = (UniqueConstraint("tenant", "workspace", "platform", "platform_id", name="uq_media_platform_id"),)


class Unit(BaseModel):
    """Content units (episodes, clips, segments, stories, posts)."""

    __tablename__ = "creator_ops_units"

    id = relationship(Integer, primary_key=True)
    tenant = relationship(String(255), nullable=False)
    workspace = relationship(String(255), nullable=False)
    media_id = relationship(Integer, ForeignKey("creator_ops_media.id"), nullable=False)
    unit_type = relationship(String(50), nullable=False)  # episode, clip, segment, story, post
    title = relationship(String(500))
    content = relationship(Text)  # Transcript, post text, etc.
    start_time_seconds = relationship(Integer)  # For clips/segments
    end_time_seconds = relationship(Integer)  # For clips/segments
    speakers = relationship(JSON)  # List of speaker names/IDs
    transcript_json = relationship(JSON)  # Full transcript with timestamps
    nlp_analysis = relationship(JSON)  # Topic, sentiment, entities, etc.
    created_at = relationship(DateTime, default=func.now())
    updated_at = relationship(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    media = relationship("Media", back_populates="units")
    interactions = relationship("Interaction", back_populates="unit")
    topics = relationship("Topic", back_populates="unit")
    claims = relationship(list[Claim]] = relationship("Claim", back_populates="unit")
    embeddings = relationship(list[Embedding]] = relationship("Embedding", back_populates="unit")

    __table_args__ = (
        UniqueConstraint(
            "tenant", "workspace", "media_id", "unit_type", "start_time_seconds", name="uq_unit_media_type_time"
        ),
    )


class Interaction(BaseModel):
    """User interactions (comments, chat messages, reactions)."""

    __tablename__ = "creator_ops_interactions"

    id = relationship(int] = mapped_column(Integer, primary_key=True)
    tenant = relationship(str] = mapped_column(String(255), nullable=False)
    workspace = relationship(str] = mapped_column(String(255), nullable=False)
    media_id = relationship(int | None] = mapped_column(ForeignKey("creator_ops_media.id"))
    unit_id = relationship(int | None] = mapped_column(ForeignKey("creator_ops_units.id"))
    interaction_type = relationship(str] = mapped_column(String(50), nullable=False)  # comment, chat, reaction, like, share
    platform = relationship(str] = mapped_column(String(50), nullable=False)
    platform_id = relationship(str] = mapped_column(String(255), nullable=False)
    user_id = relationship(str | None] = mapped_column(String(255))
    username = relationship(str | None] = mapped_column(String(255))
    content = relationship(str | None] = mapped_column(Text)
    interaction_metadata = relationship(dict[str, Any] | None] = mapped_column(JSON)
    timestamp = relationship(datetime | None] = mapped_column(DateTime)
    created_at = relationship(datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    media = relationship(Media | None] = relationship("Media", back_populates="interactions")
    unit = relationship(Unit | None] = relationship("Unit", back_populates="interactions")

    __table_args__ = (
        UniqueConstraint("tenant", "workspace", "platform", "platform_id", name="uq_interaction_platform_id"),
    )


class Person(BaseModel):
    """People mentioned or appearing in content."""

    __tablename__ = "creator_ops_people"

    id = relationship(int] = mapped_column(Integer, primary_key=True)
    tenant = relationship(str] = mapped_column(String(255), nullable=False)
    workspace = relationship(str] = mapped_column(String(255), nullable=False)
    name = relationship(str] = mapped_column(String(255), nullable=False)
    display_name = relationship(str | None] = mapped_column(String(255))
    person_type = relationship(str] = mapped_column(String(50), nullable=False)  # speaker, guest, staff, collaborator
    platform_handles = relationship(dict[str, str] | None] = mapped_column(JSON)  # {platform: handle}
    bio = relationship(str | None] = mapped_column(Text)
    profile_image_url = relationship(str | None] = mapped_column(String(1000))
    interaction_metadata = relationship(dict[str, Any] | None] = mapped_column(JSON)
    created_at = relationship(datetime] = mapped_column(DateTime, default=func.now())
    updated_at = relationship(datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("tenant", "workspace", "name", "person_type", name="uq_person_name_type"),)


class Topic(BaseModel):
    """Extracted topics and keyphrases from content."""

    __tablename__ = "creator_ops_topics"

    id = relationship(int] = mapped_column(Integer, primary_key=True)
    tenant = relationship(str] = mapped_column(String(255), nullable=False)
    workspace = relationship(str] = mapped_column(String(255), nullable=False)
    unit_id = relationship(int] = mapped_column(ForeignKey("creator_ops_units.id"), nullable=False)
    topic_type = relationship(str] = mapped_column(String(50), nullable=False)  # main_topic, keyphrase, entity
    text = relationship(str] = mapped_column(String(500), nullable=False)
    confidence = relationship(float | None] = mapped_column(Integer)  # 0.0 to 1.0
    start_time_seconds = relationship(float | None] = mapped_column(Integer)
    end_time_seconds = relationship(float | None] = mapped_column(Integer)
    interaction_metadata = relationship(dict[str, Any] | None] = mapped_column(JSON)
    created_at = relationship(datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    unit = relationship(Unit] = relationship("Unit", back_populates="topics")

    __table_args__ = (
        UniqueConstraint("tenant", "workspace", "unit_id", "topic_type", "text", name="uq_topic_unit_type_text"),
    )


class Claim(BaseModel):
    """Fact-checkable claims extracted from content."""

    __tablename__ = "creator_ops_claims"

    id = relationship(int] = mapped_column(Integer, primary_key=True)
    tenant = relationship(str] = mapped_column(String(255), nullable=False)
    workspace = relationship(str] = mapped_column(String(255), nullable=False)
    unit_id = relationship(int] = mapped_column(ForeignKey("creator_ops_units.id"), nullable=False)
    claim_text = relationship(str] = mapped_column(Text, nullable=False)
    stance = relationship(str | None] = mapped_column(String(50))  # supporting, refuting, neutral
    confidence = relationship(float | None] = mapped_column(Integer)  # 0.0 to 1.0
    uncertainty = relationship(float | None] = mapped_column(Integer)  # 0.0 to 1.0
    sources = relationship(list[str] | None] = mapped_column(JSON)  # List of source URLs
    fact_check_status = relationship(str] = mapped_column(
        String(50), default="pending"
    )  # pending, verified, disputed, unknown
    start_time_seconds = relationship(float | None] = mapped_column(Integer)
    end_time_seconds = relationship(float | None] = mapped_column(Integer)
    interaction_metadata = relationship(dict[str, Any] | None] = mapped_column(JSON)
    created_at = relationship(datetime] = mapped_column(DateTime, default=func.now())
    updated_at = relationship(datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    unit = relationship(Unit] = relationship("Unit", back_populates="claims")

    __table_args__ = (UniqueConstraint("tenant", "workspace", "unit_id", "claim_text", name="uq_claim_unit_text"),)


class Embedding(BaseModel):
    """Vector embeddings for semantic search."""

    __tablename__ = "creator_ops_embeddings"

    id = relationship(int] = mapped_column(Integer, primary_key=True)
    tenant = relationship(str] = mapped_column(String(255), nullable=False)
    workspace = relationship(str] = mapped_column(String(255), nullable=False)
    unit_id = relationship(int] = mapped_column(ForeignKey("creator_ops_units.id"), nullable=False)
    vector_id = relationship(str] = mapped_column(String(255), nullable=False)  # Qdrant vector ID
    platform = relationship(str] = mapped_column(String(50), nullable=False)
    model_version = relationship(str] = mapped_column(String(100), nullable=False)
    embedding_type = relationship(str] = mapped_column(String(50), nullable=False)  # transcript, summary, title
    content_hash = relationship(str] = mapped_column(String(64), nullable=False)  # SHA-256 of content
    created_at = relationship(datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    unit = relationship(Unit] = relationship("Unit", back_populates="embeddings")

    __table_args__ = (
        UniqueConstraint("tenant", "workspace", "unit_id", "embedding_type", name="uq_embedding_unit_type"),
        UniqueConstraint("tenant", "workspace", "vector_id", name="uq_embedding_vector_id"),
    )


def create_database_engine(database_url: str) -> StepResult:
    """Create SQLAlchemy engine for Creator Operations database."""
    try:
        engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        return StepResult.ok(data={"engine": engine})
    except Exception as e:
        return StepResult.fail(f"Failed to create database engine: {str(e)}")


def create_tables(engine) -> StepResult:
    """Create all Creator Operations tables."""
    try:
        BaseModel.metadata.create_all(engine)
        return StepResult.ok(data={"message": "Tables created successfully"})
    except Exception as e:
        return StepResult.fail(f"Failed to create tables: {str(e)}")
