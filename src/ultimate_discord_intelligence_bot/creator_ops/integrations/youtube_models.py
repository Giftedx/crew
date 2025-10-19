"""
YouTube Data API v3 models and DTOs.

This module defines typed data transfer objects for YouTube API responses,
ensuring type safety and proper validation of API data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


@dataclass
class YouTubeThumbnail:
    """YouTube thumbnail information."""

    url: str
    width: int
    height: int


@dataclass
class YouTubeThumbnails:
    """Collection of YouTube thumbnails."""

    default: YouTubeThumbnail | None = None
    medium: YouTubeThumbnail | None = None
    high: YouTubeThumbnail | None = None
    standard: YouTubeThumbnail | None = None
    maxres: YouTubeThumbnail | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeThumbnails:
        """Create from YouTube API response data."""
        thumbnails = {}
        for size, thumb_data in data.items():
            thumbnails[size] = YouTubeThumbnail(
                url=thumb_data["url"],
                width=thumb_data.get("width", 0),
                height=thumb_data.get("height", 0),
            )
        return cls(**thumbnails)


@dataclass
class YouTubeChannel:
    """YouTube channel information."""

    id: str
    title: str
    description: str | None = None
    custom_url: str | None = None
    published_at: datetime | None = None
    thumbnails: YouTubeThumbnails | None = None
    country: str | None = None
    view_count: int | None = None
    subscriber_count: int | None = None
    video_count: int | None = None
    privacy_status: str | None = None
    is_linked: bool | None = None
    long_uploads_status: str | None = None
    made_for_kids: bool | None = None
    self_declared_made_for_kids: bool | None = None
    branding_settings: dict[str, Any] | None = None
    content_details: dict[str, Any] | None = None
    statistics: dict[str, Any] | None = None
    topic_details: dict[str, Any] | None = None
    status: dict[str, Any] | None = None
    snippet: dict[str, Any] | None = None
    localizations: dict[str, Any] | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeChannel:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        status = data.get("status", {})
        branding_settings = data.get("brandingSettings", {})
        content_details = data.get("contentDetails", {})
        topic_details = data.get("topicDetails", {})
        localizations = data.get("localizations", {})

        # Parse published_at
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        # Parse thumbnails
        thumbnails = None
        if snippet.get("thumbnails"):
            thumbnails = YouTubeThumbnails.from_api_data(snippet["thumbnails"])

        return cls(
            id=data["id"],
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            custom_url=snippet.get("customUrl"),
            published_at=published_at,
            thumbnails=thumbnails,
            country=snippet.get("country"),
            view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
            subscriber_count=int(statistics.get("subscriberCount", 0)) if statistics.get("subscriberCount") else None,
            video_count=int(statistics.get("videoCount", 0)) if statistics.get("videoCount") else None,
            privacy_status=status.get("privacyStatus"),
            is_linked=status.get("isLinked"),
            long_uploads_status=status.get("longUploadsStatus"),
            made_for_kids=status.get("madeForKids"),
            self_declared_made_for_kids=status.get("selfDeclaredMadeForKids"),
            branding_settings=branding_settings,
            content_details=content_details,
            statistics=statistics,
            topic_details=topic_details,
            status=status,
            snippet=snippet,
            localizations=localizations,
        )


@dataclass
class YouTubeVideo:
    """YouTube video information."""

    id: str
    title: str
    description: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    published_at: datetime | None = None
    thumbnails: YouTubeThumbnails | None = None
    duration: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    dislike_count: int | None = None
    comment_count: int | None = None
    tags: list[str] = field(default_factory=list)
    category_id: str | None = None
    default_language: str | None = None
    default_audio_language: str | None = None
    privacy_status: str | None = None
    upload_status: str | None = None
    license: str | None = None
    embeddable: bool | None = None
    public_stats_viewable: bool | None = None
    made_for_kids: bool | None = None
    self_declared_made_for_kids: bool | None = None
    live_broadcast_content: str | None = None
    recording_details: dict[str, Any] | None = None
    file_details: dict[str, Any] | None = None
    processing_details: dict[str, Any] | None = None
    suggestions: dict[str, Any] | None = None
    localizations: dict[str, Any] | None = None
    snippet: dict[str, Any] | None = None
    statistics: dict[str, Any] | None = None
    status: dict[str, Any] | None = None
    content_details: dict[str, Any] | None = None
    player: dict[str, Any] | None = None
    topic_details: dict[str, Any] | None = None
    live_streaming_details: dict[str, Any] | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeVideo:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})
        statistics = data.get("statistics", {})
        status = data.get("status", {})
        content_details = data.get("contentDetails", {})
        player = data.get("player", {})
        recording_details = data.get("recordingDetails", {})
        file_details = data.get("fileDetails", {})
        processing_details = data.get("processingDetails", {})
        suggestions = data.get("suggestions", {})
        localizations = data.get("localizations", {})
        topic_details = data.get("topicDetails", {})
        live_streaming_details = data.get("liveStreamingDetails", {})

        # Parse published_at
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        # Parse thumbnails
        thumbnails = None
        if snippet.get("thumbnails"):
            thumbnails = YouTubeThumbnails.from_api_data(snippet["thumbnails"])

        # Parse duration
        duration_seconds = None
        if content_details.get("duration"):
            duration_seconds = cls._parse_duration(content_details["duration"])

        # Parse tags
        tags = snippet.get("tags", [])

        return cls(
            id=data["id"],
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            channel_id=snippet.get("channelId"),
            channel_title=snippet.get("channelTitle"),
            published_at=published_at,
            thumbnails=thumbnails,
            duration=content_details.get("duration"),
            duration_seconds=duration_seconds,
            view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
            like_count=int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else None,
            dislike_count=int(statistics.get("dislikeCount", 0)) if statistics.get("dislikeCount") else None,
            comment_count=int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else None,
            tags=tags,
            category_id=snippet.get("categoryId"),
            default_language=snippet.get("defaultLanguage"),
            default_audio_language=snippet.get("defaultAudioLanguage"),
            privacy_status=status.get("privacyStatus"),
            upload_status=status.get("uploadStatus"),
            license=status.get("license"),
            embeddable=status.get("embeddable"),
            public_stats_viewable=status.get("publicStatsViewable"),
            made_for_kids=status.get("madeForKids"),
            self_declared_made_for_kids=status.get("selfDeclaredMadeForKids"),
            live_broadcast_content=snippet.get("liveBroadcastContent"),
            recording_details=recording_details,
            file_details=file_details,
            processing_details=processing_details,
            suggestions=suggestions,
            localizations=localizations,
            snippet=snippet,
            statistics=statistics,
            status=status,
            content_details=content_details,
            player=player,
            topic_details=topic_details,
            live_streaming_details=live_streaming_details,
        )

    @staticmethod
    def _parse_duration(duration: str) -> int:
        """Parse ISO 8601 duration to seconds."""
        import re

        # Match PT1H2M3S format
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds


@dataclass
class YouTubeComment:
    """YouTube comment information."""

    id: str
    text_display: str
    text_original: str | None = None
    author_display_name: str | None = None
    author_profile_image_url: str | None = None
    author_channel_url: str | None = None
    author_channel_id: str | None = None
    like_count: int | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    parent_id: str | None = None
    can_rate: bool | None = None
    viewer_rating: str | None = None
    moderation_status: str | None = None
    snippet: dict[str, Any] | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeComment:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})
        top_level_comment = snippet.get("topLevelComment", {})
        comment_snippet = top_level_comment.get("snippet", {})

        # Parse timestamps
        published_at = None
        if comment_snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(comment_snippet["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        updated_at = None
        if comment_snippet.get("updatedAt"):
            try:
                updated_at = datetime.fromisoformat(comment_snippet["updatedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return cls(
            id=data["id"],
            text_display=comment_snippet.get("textDisplay", ""),
            text_original=comment_snippet.get("textOriginal"),
            author_display_name=comment_snippet.get("authorDisplayName"),
            author_profile_image_url=comment_snippet.get("authorProfileImageUrl"),
            author_channel_url=comment_snippet.get("authorChannelUrl"),
            author_channel_id=comment_snippet.get("authorChannelId", {}).get("value"),
            like_count=int(comment_snippet.get("likeCount", 0)) if comment_snippet.get("likeCount") else None,
            published_at=published_at,
            updated_at=updated_at,
            parent_id=snippet.get("parentId"),
            can_rate=comment_snippet.get("canRate"),
            viewer_rating=comment_snippet.get("viewerRating"),
            moderation_status=snippet.get("moderationStatus"),
            snippet=snippet,
        )


@dataclass
class YouTubeLiveChatMessage:
    """YouTube live chat message information."""

    id: str
    snippet: dict[str, Any]
    author_details: dict[str, Any] | None = None
    display_message: str | None = None
    text_message_details: dict[str, Any] | None = None
    super_chat_details: dict[str, Any] | None = None
    super_sticker_details: dict[str, Any] | None = None
    membership_gifting_details: dict[str, Any] | None = None
    new_sponsor_details: dict[str, Any] | None = None
    poll_details: dict[str, Any] | None = None
    user_banned_details: dict[str, Any] | None = None
    message_type: str | None = None
    published_at: datetime | None = None
    has_display_content: bool | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeLiveChatMessage:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})
        author_details = data.get("authorDetails", {})
        text_message_details = snippet.get("textMessageDetails", {})
        super_chat_details = snippet.get("superChatDetails", {})
        super_sticker_details = snippet.get("superStickerDetails", {})
        membership_gifting_details = snippet.get("membershipGiftingDetails", {})
        new_sponsor_details = snippet.get("newSponsorDetails", {})
        poll_details = snippet.get("pollDetails", {})
        user_banned_details = snippet.get("userBannedDetails", {})

        # Parse published_at
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        # Extract display message
        display_message = text_message_details.get("messageText") if text_message_details else None

        return cls(
            id=data["id"],
            snippet=snippet,
            author_details=author_details,
            display_message=display_message,
            text_message_details=text_message_details,
            super_chat_details=super_chat_details,
            super_sticker_details=super_sticker_details,
            membership_gifting_details=membership_gifting_details,
            new_sponsor_details=new_sponsor_details,
            poll_details=poll_details,
            user_banned_details=user_banned_details,
            message_type=snippet.get("type"),
            published_at=published_at,
            has_display_content=snippet.get("hasDisplayContent"),
        )


@dataclass
class YouTubeCaption:
    """YouTube caption information."""

    id: str
    snippet: dict[str, Any]
    track_kind: str | None = None
    language: str | None = None
    name: str | None = None
    is_auto_synced: bool | None = None
    is_cc: bool | None = None
    is_draft: bool | None = None
    is_easy_reader: bool | None = None
    is_large: bool | None = None
    audio_track_type: str | None = None
    status: str | None = None
    failure_reason: str | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeCaption:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})

        return cls(
            id=data["id"],
            snippet=snippet,
            track_kind=snippet.get("trackKind"),
            language=snippet.get("language"),
            name=snippet.get("name"),
            is_auto_synced=snippet.get("isAutoSynced"),
            is_cc=snippet.get("isCC"),
            is_draft=snippet.get("isDraft"),
            is_easy_reader=snippet.get("isEasyReader"),
            is_large=snippet.get("isLarge"),
            audio_track_type=snippet.get("audioTrackType"),
            status=snippet.get("status"),
            failure_reason=snippet.get("failureReason"),
        )


@dataclass
class YouTubeSearchResult:
    """YouTube search result information."""

    kind: str
    etag: str
    id: dict[str, Any]
    snippet: dict[str, Any]
    video_id: str | None = None
    channel_id: str | None = None
    playlist_id: str | None = None
    title: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    thumbnails: YouTubeThumbnails | None = None
    channel_title: str | None = None
    live_broadcast_content: str | None = None

    @classmethod
    def from_api_data(cls, data: dict[str, Any]) -> YouTubeSearchResult:
        """Create from YouTube API response data."""
        snippet = data.get("snippet", {})
        result_id = data.get("id", {})

        # Parse published_at
        published_at = None
        if snippet.get("publishedAt"):
            try:
                published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            except ValueError:
                pass

        # Parse thumbnails
        thumbnails = None
        if snippet.get("thumbnails"):
            thumbnails = YouTubeThumbnails.from_api_data(snippet["thumbnails"])

        return cls(
            kind=data.get("kind", ""),
            etag=data.get("etag", ""),
            id=result_id,
            snippet=snippet,
            video_id=result_id.get("videoId"),
            channel_id=result_id.get("channelId"),
            playlist_id=result_id.get("playlistId"),
            title=snippet.get("title"),
            description=snippet.get("description"),
            published_at=published_at,
            thumbnails=thumbnails,
            channel_title=snippet.get("channelTitle"),
            live_broadcast_content=snippet.get("liveBroadcastContent"),
        )


@dataclass
class YouTubeQuotaUsage:
    """YouTube API quota usage tracking."""

    total_quota: int = 10000  # Daily quota limit
    used_quota: int = 0
    remaining_quota: int = 10000
    reset_time: datetime | None = None

    def consume_quota(self, units: int) -> StepResult:
        """Consume quota units."""
        if self.used_quota + units > self.total_quota:
            return StepResult.fail(f"Quota exceeded. Requested: {units}, Available: {self.remaining_quota}")

        self.used_quota += units
        self.remaining_quota = self.total_quota - self.used_quota
        return StepResult.ok(data={"used_quota": self.used_quota, "remaining_quota": self.remaining_quota})

    def reset_quota(self) -> None:
        """Reset quota usage."""
        self.used_quota = 0
        self.remaining_quota = self.total_quota
        self.reset_time = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_quota": self.total_quota,
            "used_quota": self.used_quota,
            "remaining_quota": self.remaining_quota,
            "reset_time": self.reset_time.isoformat() if self.reset_time else None,
        }
