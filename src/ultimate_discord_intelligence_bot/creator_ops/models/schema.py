"""
SQLAlchemy models for Creator Operations - SQLAlchemy 1.4 compatible.
"""

from __future__ import annotations

import json

from sqlalchemy import (  # type: ignore[import-untyped]
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base  # type: ignore[import-untyped]
from sqlalchemy.sql import func  # type: ignore[import-untyped]


BaseModel = declarative_base()


class Account(BaseModel):
    """Platform account for a creator."""

    __tablename__ = "creator_ops_accounts"

    id = Column(Integer, primary_key=True)
    tenant = Column(String(255), nullable=False)
    workspace = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # youtube, twitch, tiktok, instagram, x
    handle = Column(String(255), nullable=False)
    display_name = Column(String(255))
    platform_id = Column(String(255), nullable=False)  # Platform-specific ID
    oauth_scopes = Column(Text)  # JSON list of scopes
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "tenant",
            "workspace",
            "platform",
            "handle",
            name="uq_tenant_workspace_platform_handle",
        ),
        UniqueConstraint(
            "tenant",
            "workspace",
            "platform",
            "platform_id",
            name="uq_tenant_workspace_platform_id",
        ),
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

    id = Column(Integer, primary_key=True)
    tenant = Column(String(255), nullable=False)
    workspace = Column(String(255), nullable=False)
    account_id = Column(Integer, ForeignKey("creator_ops_accounts.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    media_type = Column(String(50), nullable=False)  # video, audio, post, story, clip
    platform_id = Column(String(255), nullable=False)
    url = Column(String(1000))
    title = Column(String(500))
    description = Column(Text)
    duration_seconds = Column(Integer)
    file_size_bytes = Column(Integer)
    thumbnail_url = Column(String(1000))
    published_at = Column(DateTime)
    media_metadata = Column(JSON)
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "tenant",
            "workspace",
            "platform",
            "platform_id",
            name="uq_media_platform_id",
        ),
    )


class Unit(BaseModel):
    """Content units (episodes, clips, segments, stories, posts)."""

    __tablename__ = "creator_ops_units"

    id = Column(Integer, primary_key=True)
    tenant = Column(String(255), nullable=False)
    workspace = Column(String(255), nullable=False)
    media_id = Column(Integer, ForeignKey("creator_ops_media.id"), nullable=False)
    unit_type = Column(String(50), nullable=False)  # episode, clip, segment, story, post
    title = Column(String(500))
    content = Column(Text)  # Transcript, post text, etc.
    start_time_seconds = Column(Integer)  # For clips/segments
    end_time_seconds = Column(Integer)  # For clips/segments
    speakers = Column(JSON)  # List of speaker names/IDs
    transcript_json = Column(JSON)  # Full transcript with timestamps
    nlp_analysis = Column(JSON)  # Topic, sentiment, entities, etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
