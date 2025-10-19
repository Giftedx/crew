"""
Twitch Helix API models and DTOs.

This module defines typed data transfer objects for Twitch API responses,
ensuring type safety and proper validation of API data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TwitchUser:
    """Twitch user information."""

    id: str
    login: str
    display_name: str
    type: str | None = None
    broadcaster_type: str | None = None
    description: str | None = None
    profile_image_url: str | None = None
    offline_image_url: str | None = None
    view_count: int | None = None
    email: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchUser:
        """Create from Twitch API response data."""
        # Parse created_at
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            login=data["login"],
            display_name=data["display_name"],
            type=data.get("type"),
            broadcaster_type=data.get("broadcaster_type"),
            description=data.get("description"),
            profile_image_url=data.get("profile_image_url"),
            offline_image_url=data.get("offline_image_url"),
            view_count=int(data["view_count"]) if data.get("view_count") else None,
            email=data.get("email"),
            created_at=created_at,
        )


@dataclass
class TwitchStream:
    """Twitch stream information."""

    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str | None = None
    game_name: str | None = None
    type: str | None = None
    title: str | None = None
    viewer_count: int | None = None
    started_at: datetime | None = None
    language: str | None = None
    thumbnail_url: str | None = None
    tag_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_mature: bool | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchStream:
        """Create from Twitch API response data."""
        # Parse started_at
        started_at = None
        if data.get("started_at"):
            try:
                started_at = datetime.fromisoformat(data["started_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            user_id=data["user_id"],
            user_login=data["user_login"],
            user_name=data["user_name"],
            game_id=data.get("game_id"),
            game_name=data.get("game_name"),
            type=data.get("type"),
            title=data.get("title"),
            viewer_count=int(data["viewer_count"]) if data.get("viewer_count") else None,
            started_at=started_at,
            language=data.get("language"),
            thumbnail_url=data.get("thumbnail_url"),
            tag_ids=data.get("tag_ids", []),
            tags=data.get("tags", []),
            is_mature=data.get("is_mature"),
        )


@dataclass
class TwitchVideo:
    """Twitch video (VOD) information."""

    id: str
    user_id: str
    user_login: str
    user_name: str
    title: str
    stream_id: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    published_at: datetime | None = None
    url: str | None = None
    thumbnail_url: str | None = None
    viewable: str | None = None
    view_count: int | None = None
    language: str | None = None
    type: str | None = None
    duration: str | None = None
    muted_segments: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchVideo:
        """Create from Twitch API response data."""
        # Parse timestamps
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        published_at = None
        if data.get("published_at"):
            try:
                published_at = datetime.fromisoformat(data["published_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            stream_id=data.get("stream_id"),
            user_id=data["user_id"],
            user_login=data["user_login"],
            user_name=data["user_name"],
            title=data["title"],
            description=data.get("description"),
            created_at=created_at,
            published_at=published_at,
            url=data.get("url"),
            thumbnail_url=data.get("thumbnail_url"),
            viewable=data.get("viewable"),
            view_count=int(data["view_count"]) if data.get("view_count") else None,
            language=data.get("language"),
            type=data.get("type"),
            duration=data.get("duration"),
            muted_segments=data.get("muted_segments", []),
        )


@dataclass
class TwitchClip:
    """Twitch clip information."""

    id: str
    url: str
    embed_url: str
    broadcaster_id: str
    broadcaster_name: str
    creator_id: str
    creator_name: str
    video_id: str | None = None
    game_id: str | None = None
    language: str | None = None
    title: str | None = None
    view_count: int | None = None
    created_at: datetime | None = None
    thumbnail_url: str | None = None
    duration: float | None = None
    vod_offset: int | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchClip:
        """Create from Twitch API response data."""
        # Parse created_at
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            url=data["url"],
            embed_url=data["embed_url"],
            broadcaster_id=data["broadcaster_id"],
            broadcaster_name=data["broadcaster_name"],
            creator_id=data["creator_id"],
            creator_name=data["creator_name"],
            video_id=data.get("video_id"),
            game_id=data.get("game_id"),
            language=data.get("language"),
            title=data.get("title"),
            view_count=int(data["view_count"]) if data.get("view_count") else None,
            created_at=created_at,
            thumbnail_url=data.get("thumbnail_url"),
            duration=float(data["duration"]) if data.get("duration") else None,
            vod_offset=int(data["vod_offset"]) if data.get("vod_offset") else None,
        )


@dataclass
class TwitchChatMessage:
    """Twitch chat message information."""

    id: str
    user_id: str
    user_name: str
    user_login: str
    message: str
    timestamp: datetime | None = None
    color: str | None = None
    badges: list[str] = field(default_factory=list)
    emotes: list[dict[str, Any]] = field(default_factory=list)
    is_moderator: bool = False
    is_subscriber: bool = False
    is_vip: bool = False
    is_turbo: bool = False
    is_first_message: bool = False
    is_returning_chatter: bool = False

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchChatMessage:
        """Create from Twitch API response data."""
        # Parse timestamp
        timestamp = None
        if data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                pass

        # Parse badges
        badges = []
        if data.get("badges"):
            badges = [badge["id"] for badge in data["badges"]]

        # Parse emotes
        emotes = []
        if data.get("emotes"):
            emotes = data["emotes"]

        return cls(
            id=data["id"],
            user_id=data["user_id"],
            user_name=data["user_name"],
            user_login=data["user_login"],
            message=data["message"],
            timestamp=timestamp,
            color=data.get("color"),
            badges=badges,
            emotes=emotes,
            is_moderator=data.get("is_moderator", False),
            is_subscriber=data.get("is_subscriber", False),
            is_vip=data.get("is_vip", False),
            is_turbo=data.get("is_turbo", False),
            is_first_message=data.get("is_first_message", False),
            is_returning_chatter=data.get("is_returning_chatter", False),
        )


@dataclass
class TwitchStreamMarker:
    """Twitch stream marker information."""

    id: str
    created_at: datetime | None = None
    description: str | None = None
    position_seconds: int | None = None
    url: str | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchStreamMarker:
        """Create from Twitch API response data."""
        # Parse created_at
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            created_at=created_at,
            description=data.get("description"),
            position_seconds=int(data["position_seconds"]) if data.get("position_seconds") else None,
            url=data.get("url"),
        )


@dataclass
class TwitchEventSubEvent:
    """Twitch EventSub event information."""

    id: str
    type: str
    version: str
    status: str
    created_at: datetime | None = None
    condition: dict[str, Any] | None = None
    transport: dict[str, Any] | None = None
    cost: int | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> TwitchEventSubEvent:
        """Create from Twitch API response data."""
        # Parse created_at
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            type=data["type"],
            version=data["version"],
            status=data["status"],
            created_at=created_at,
            condition=data.get("condition"),
            transport=data.get("transport"),
            cost=data.get("cost"),
        )


@dataclass
class TwitchWebSocketMessage:
    """Twitch WebSocket message for EventSub."""

    metadata: dict[str, Any]
    payload: dict[str, Any]
    message_type: str | None = None
    message_id: str | None = None
    message_timestamp: datetime | None = None

    @classmethod
    def from_websocket_data(cls, data: dict[str, Any]) -> TwitchWebSocketMessage:
        """Create from WebSocket message data."""
        # Parse timestamp
        message_timestamp = None
        if data.get("metadata", {}).get("message_timestamp"):
            try:
                message_timestamp = datetime.fromisoformat(data["metadata"]["message_timestamp"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            metadata=data.get("metadata", {}),
            payload=data.get("payload", {}),
            message_type=data.get("metadata", {}).get("message_type"),
            message_id=data.get("metadata", {}).get("message_id"),
            message_timestamp=message_timestamp,
        )


@dataclass
class TwitchRateLimit:
    """Twitch API rate limit information."""

    limit: int
    remaining: int
    reset_time: datetime | None = None

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> TwitchRateLimit:
        """Create from HTTP response headers."""
        limit = int(headers.get("Ratelimit-Limit", 0))
        remaining = int(headers.get("Ratelimit-Remaining", 0))

        # Parse reset time
        reset_time = None
        if headers.get("Ratelimit-Reset"):
            try:
                reset_timestamp = int(headers["Ratelimit-Reset"])
                reset_time = datetime.fromtimestamp(reset_timestamp)
            except (ValueError, TypeError):
                pass

        return cls(
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
        )
