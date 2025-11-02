"""
Pydantic models for Instagram Graph API responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InstagramUser(BaseModel):
    """Represents an Instagram user profile."""

    id: str = Field(..., description="Unique identifier for the user.")
    username: str = Field(..., description="User's Instagram username.")
    account_type: str = Field(..., description="Type of account (PERSONAL, BUSINESS, CREATOR).")
    media_count: int = Field(0, description="Number of media items posted by the user.")
    followers_count: int = Field(0, description="Number of followers.")
    follows_count: int = Field(0, description="Number of accounts the user follows.")
    name: str | None = Field(None, description="User's display name.")
    biography: str | None = Field(None, description="User's bio text.")
    website: str | None = Field(None, description="User's website URL.")
    profile_picture_url: str | None = Field(None, description="URL to the user's profile picture.")
    is_verified: bool = Field(False, description="Whether the user is verified.")
    is_private: bool = Field(False, description="Whether the user's account is private.")
    is_business: bool = Field(False, description="Whether the user has a business account.")
    is_creator: bool = Field(False, description="Whether the user has a creator account.")


class InstagramMedia(BaseModel):
    """Represents an Instagram media item (post, story, etc.)."""

    id: str = Field(..., description="Unique identifier for the media item.")
    media_type: str = Field(..., description="Type of media (IMAGE, VIDEO, CAROUSEL_ALBUM).")
    media_url: str = Field(..., description="URL to the media content.")
    permalink: str = Field(..., description="Permanent link to the media on Instagram.")
    caption: str | None = Field(None, description="Caption text for the media.")
    timestamp: datetime = Field(..., description="When the media was created.")
    like_count: int = Field(0, description="Number of likes.")
    comments_count: int = Field(0, description="Number of comments.")
    children: list["InstagramMedia"] | None = Field(None, description="Child media items for carousel posts.")
    thumbnail_url: str | None = Field(None, description="URL to the media thumbnail.")
    video_title: str | None = Field(None, description="Title for video content.")
    video_description: str | None = Field(None, description="Description for video content.")
    video_insights: dict[str, Any] | None = Field(None, description="Video-specific insights.")


class InstagramComment(BaseModel):
    """Represents a comment on an Instagram media item."""

    id: str = Field(..., description="Unique identifier for the comment.")
    text: str = Field(..., description="Comment text content.")
    timestamp: datetime = Field(..., description="When the comment was created.")
    like_count: int = Field(0, description="Number of likes on the comment.")
    hidden: bool = Field(False, description="Whether the comment is hidden.")
    user: InstagramUser | None = Field(None, description="User who made the comment.")
    parent_id: str | None = Field(None, description="ID of the parent comment if this is a reply.")


class InstagramStory(BaseModel):
    """Represents an Instagram story."""

    id: str = Field(..., description="Unique identifier for the story.")
    media_type: str = Field(..., description="Type of story media (IMAGE, VIDEO).")
    media_url: str = Field(..., description="URL to the story media content.")
    permalink: str = Field(..., description="Permanent link to the story.")
    timestamp: datetime = Field(..., description="When the story was created.")
    expires_at: datetime = Field(..., description="When the story expires.")
    impressions: int = Field(0, description="Number of story impressions.")
    reach: int = Field(0, description="Number of unique accounts reached.")
    replies: int = Field(0, description="Number of story replies.")
    taps_forward: int = Field(0, description="Number of forward taps.")
    taps_back: int = Field(0, description="Number of back taps.")
    exits: int = Field(0, description="Number of story exits.")


class InstagramInsight(BaseModel):
    """Represents an Instagram insight metric."""

    name: str = Field(..., description="Name of the insight metric.")
    period: str = Field(..., description="Time period for the insight (day, week, days_28).")
    values: list[dict[str, Any]] = Field(..., description="Insight values over time.")
    title: str = Field(..., description="Display title for the insight.")
    description: str = Field(..., description="Description of what the insight measures.")
    id: str = Field(..., description="Unique identifier for the insight.")


class InstagramHashtag(BaseModel):
    """Represents an Instagram hashtag."""

    name: str = Field(..., description="Hashtag name without the # symbol.")
    media_count: int = Field(0, description="Number of media items using this hashtag.")


class InstagramMention(BaseModel):
    """Represents an Instagram mention."""

    username: str = Field(..., description="Username of the mentioned account.")
    id: str | None = Field(None, description="ID of the mentioned account if available.")


class InstagramError(BaseModel):
    """Represents an error response from the Instagram API."""

    message: str = Field(..., description="Error message.")
    type: str = Field(..., description="Error type.")
    code: int = Field(..., description="Error code.")
    error_subcode: int | None = Field(None, description="Error subcode.")
    fbtrace_id: str | None = Field(None, description="Facebook trace ID for debugging.")


class InstagramPaging(BaseModel):
    """Represents pagination information from Instagram API responses."""

    cursors: dict[str, str] | None = Field(None, description="Pagination cursors.")
    next: str | None = Field(None, description="URL for the next page of results.")
    previous: str | None = Field(None, description="URL for the previous page of results.")


class InstagramResponse(BaseModel):
    """Base response model for Instagram API calls."""

    data: list[Any] | None = Field(None, description="Response data.")
    paging: InstagramPaging | None = Field(None, description="Pagination information.")
    error: InstagramError | None = Field(None, description="Error information if the request failed.")


class InstagramLongLivedToken(BaseModel):
    """Represents a long-lived access token from Instagram."""

    access_token: str = Field(..., description="The long-lived access token.")
    token_type: str = Field(..., description="Type of token (typically 'bearer').")
    expires_in: int = Field(..., description="Token expiration time in seconds.")


class InstagramWebhookSubscription(BaseModel):
    """Represents a webhook subscription for Instagram events."""

    object: str = Field(..., description="Object type (instagram).")
    callback_url: str = Field(..., description="URL to receive webhook notifications.")
    fields: list[str] = Field(..., description="Fields to monitor for changes.")
    verify_token: str = Field(..., description="Token used to verify webhook authenticity.")


class InstagramWebhookEvent(BaseModel):
    """Represents a webhook event from Instagram."""

    object: str = Field(..., description="Object type (instagram).")
    entry: list[dict[str, Any]] = Field(..., description="Array of entry objects containing the actual data.")
    id: str | None = Field(None, description="Unique identifier for the webhook event.")


class InstagramMediaInsight(BaseModel):
    """Represents insights for a specific Instagram media item."""

    media_id: str = Field(..., description="ID of the media item.")
    insights: list[InstagramInsight] = Field(..., description="List of insights for the media.")
    timestamp: datetime = Field(..., description="When the insights were generated.")


class InstagramAccountInsight(BaseModel):
    """Represents insights for an Instagram account."""

    account_id: str = Field(..., description="ID of the Instagram account.")
    insights: list[InstagramInsight] = Field(..., description="List of insights for the account.")
    timestamp: datetime = Field(..., description="When the insights were generated.")
    period: str = Field(..., description="Time period for the insights (day, week, days_28).")


# Update forward references
InstagramMedia.model_rebuild()
