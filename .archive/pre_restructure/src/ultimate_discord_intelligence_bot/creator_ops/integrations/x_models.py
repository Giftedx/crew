"""
Pydantic models for X (Twitter) API v2 responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class XUser(BaseModel):
    """Represents an X (Twitter) user profile."""

    id: str = Field(..., description="Unique identifier for the user.")
    username: str = Field(..., description="User's X username (without @).")
    name: str = Field(..., description="User's display name.")
    description: str | None = Field(None, description="User's bio description.")
    profile_image_url: str | None = Field(None, description="URL to the user's profile image.")
    public_metrics: dict[str, int] | None = Field(None, description="Public metrics for the user.")
    verified: bool = Field(False, description="Whether the user is verified.")
    protected: bool = Field(False, description="Whether the user's account is protected.")
    created_at: datetime | None = Field(None, description="When the user account was created.")
    location: str | None = Field(None, description="User's location.")
    url: str | None = Field(None, description="User's website URL.")
    pinned_tweet_id: str | None = Field(None, description="ID of the user's pinned tweet.")
    entities: dict[str, Any] | None = Field(None, description="Entities in the user's profile.")


class XTweet(BaseModel):
    """Represents an X (Twitter) tweet."""

    id: str = Field(..., description="Unique identifier for the tweet.")
    text: str = Field(..., description="Content of the tweet.")
    author_id: str = Field(..., description="ID of the user who posted the tweet.")
    created_at: datetime = Field(..., description="When the tweet was created.")
    public_metrics: dict[str, int] | None = Field(None, description="Public metrics for the tweet.")
    context_annotations: list[dict[str, Any]] | None = Field(None, description="Context annotations for the tweet.")
    entities: dict[str, Any] | None = Field(None, description="Entities in the tweet.")
    in_reply_to_user_id: str | None = Field(None, description="ID of the user this tweet is replying to.")
    referenced_tweets: list[dict[str, str]] | None = Field(None, description="Tweets referenced in this tweet.")
    lang: str | None = Field(None, description="Language of the tweet.")
    possibly_sensitive: bool = Field(False, description="Whether the tweet might contain sensitive content.")
    reply_settings: str | None = Field(None, description="Who can reply to this tweet.")
    source: str | None = Field(None, description="Source of the tweet (e.g., 'Twitter for iPhone').")
    conversation_id: str | None = Field(None, description="ID of the conversation this tweet belongs to.")


class XMedia(BaseModel):
    """Represents media attached to an X (Twitter) tweet."""

    media_key: str = Field(..., description="Unique identifier for the media.")
    type: str = Field(..., description="Type of media (photo, video, animated_gif).")
    url: str | None = Field(None, description="URL to the media content.")
    preview_image_url: str | None = Field(None, description="URL to the media preview image.")
    alt_text: str | None = Field(None, description="Alt text for the media.")
    duration_ms: int | None = Field(None, description="Duration of the media in milliseconds.")
    height: int | None = Field(None, description="Height of the media in pixels.")
    width: int | None = Field(None, description="Width of the media in pixels.")
    public_metrics: dict[str, int] | None = Field(None, description="Public metrics for the media.")
    variants: list[dict[str, Any]] | None = Field(None, description="Variants of the media (for video).")


class XPoll(BaseModel):
    """Represents a poll attached to an X (Twitter) tweet."""

    id: str = Field(..., description="Unique identifier for the poll.")
    options: list[dict[str, Any]] = Field(..., description="Options for the poll.")
    duration_minutes: int = Field(..., description="Duration of the poll in minutes.")
    end_datetime: datetime | None = Field(None, description="When the poll ends.")
    voting_status: str | None = Field(None, description="Status of the poll (open, closed).")


class XPlace(BaseModel):
    """Represents a place attached to an X (Twitter) tweet."""

    id: str = Field(..., description="Unique identifier for the place.")
    name: str = Field(..., description="Name of the place.")
    country_code: str = Field(..., description="Country code for the place.")
    place_type: str = Field(..., description="Type of place (city, country, etc.).")
    full_name: str = Field(..., description="Full name of the place.")
    country: str = Field(..., description="Country name.")
    contained_within: list[str] | None = Field(None, description="Places that contain this place.")
    geo: dict[str, Any] | None = Field(None, description="Geographic information for the place.")


class XMention(BaseModel):
    """Represents a mention in an X (Twitter) tweet."""

    start: int = Field(..., description="Start position of the mention in the tweet text.")
    end: int = Field(..., description="End position of the mention in the tweet text.")
    username: str = Field(..., description="Username of the mentioned account.")
    id: str = Field(..., description="ID of the mentioned account.")


class XHashtag(BaseModel):
    """Represents a hashtag in an X (Twitter) tweet."""

    start: int = Field(..., description="Start position of the hashtag in the tweet text.")
    end: int = Field(..., description="End position of the hashtag in the tweet text.")
    tag: str = Field(..., description="Hashtag text (without #).")


class XURL(BaseModel):
    """Represents a URL in an X (Twitter) tweet."""

    start: int = Field(..., description="Start position of the URL in the tweet text.")
    end: int = Field(..., description="End position of the URL in the tweet text.")
    url: str = Field(..., description="The URL.")
    expanded_url: str | None = Field(None, description="Expanded version of the URL.")
    display_url: str | None = Field(None, description="Display version of the URL.")
    title: str | None = Field(None, description="Title of the linked page.")
    description: str | None = Field(None, description="Description of the linked page.")
    images: list[dict[str, str]] | None = Field(None, description="Images from the linked page.")


class XCashtag(BaseModel):
    """Represents a cashtag in an X (Twitter) tweet."""

    start: int = Field(..., description="Start position of the cashtag in the tweet text.")
    end: int = Field(..., description="End position of the cashtag in the tweet text.")
    tag: str = Field(..., description="Cashtag text (without $).")


class XAnnotation(BaseModel):
    """Represents a context annotation in an X (Twitter) tweet."""

    start: int = Field(..., description="Start position of the annotation in the tweet text.")
    end: int = Field(..., description="End position of the annotation in the tweet text.")
    probability: float = Field(..., description="Probability of the annotation being correct.")
    type: str = Field(..., description="Type of annotation.")
    normalized_text: str = Field(..., description="Normalized text of the annotation.")


class XError(BaseModel):
    """Represents an error response from the X API."""

    message: str = Field(..., description="Error message.")
    type: str = Field(..., description="Error type.")
    code: int = Field(..., description="Error code.")
    title: str | None = Field(None, description="Error title.")
    detail: str | None = Field(None, description="Error detail.")
    parameter: str | None = Field(None, description="Parameter that caused the error.")
    resource_type: str | None = Field(None, description="Type of resource that caused the error.")
    resource_id: str | None = Field(None, description="ID of the resource that caused the error.")
    value: str | None = Field(None, description="Value that caused the error.")


class XMeta(BaseModel):
    """Represents metadata for X API responses."""

    result_count: int | None = Field(None, description="Number of results returned.")
    next_token: str | None = Field(None, description="Token for the next page of results.")
    previous_token: str | None = Field(None, description="Token for the previous page of results.")
    newest_id: str | None = Field(None, description="ID of the newest result.")
    oldest_id: str | None = Field(None, description="ID of the oldest result.")
    sent: str | None = Field(None, description="When the request was sent.")


class XResponse(BaseModel):
    """Base response model for X API calls."""

    data: list[Any] | None = Field(None, description="Response data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XTweetResponse(BaseModel):
    """Response model for X tweet API calls."""

    data: list[XTweet] | None = Field(None, description="Tweet data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XUserResponse(BaseModel):
    """Response model for X user API calls."""

    data: list[XUser] | None = Field(None, description="User data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XSearchResponse(BaseModel):
    """Response model for X search API calls."""

    data: list[XTweet] | None = Field(None, description="Search results.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XTimelineResponse(BaseModel):
    """Response model for X timeline API calls."""

    data: list[XTweet] | None = Field(None, description="Timeline data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XMentionResponse(BaseModel):
    """Response model for X mention API calls."""

    data: list[XTweet] | None = Field(None, description="Mention data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XMediaResponse(BaseModel):
    """Response model for X media API calls."""

    data: list[XMedia] | None = Field(None, description="Media data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XPollResponse(BaseModel):
    """Response model for X poll API calls."""

    data: list[XPoll] | None = Field(None, description="Poll data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XPlaceResponse(BaseModel):
    """Response model for X place API calls."""

    data: list[XPlace] | None = Field(None, description="Place data.")
    meta: XMeta | None = Field(None, description="Response metadata.")
    errors: list[XError] | None = Field(None, description="Errors in the response.")
    includes: dict[str, list[Any]] | None = Field(None, description="Additional data included in the response.")


class XWebhookEvent(BaseModel):
    """Represents a webhook event from X."""

    for_user_id: str = Field(..., description="ID of the user the event is for.")
    tweet_create_events: list[XTweet] | None = Field(None, description="Tweet creation events.")
    tweet_delete_events: list[dict[str, str]] | None = Field(None, description="Tweet deletion events.")
    direct_message_events: list[dict[str, Any]] | None = Field(None, description="Direct message events.")
    follow_events: list[dict[str, str]] | None = Field(None, description="Follow events.")
    favorite_events: list[dict[str, str]] | None = Field(None, description="Favorite events.")
    block_events: list[dict[str, str]] | None = Field(None, description="Block events.")
    mute_events: list[dict[str, str]] | None = Field(None, description="Mute events.")
    user_event: dict[str, Any] | None = Field(None, description="User event.")


class XWebhookSubscription(BaseModel):
    """Represents a webhook subscription for X events."""

    id: str = Field(..., description="Unique identifier for the subscription.")
    url: str = Field(..., description="URL to receive webhook notifications.")
    valid: bool = Field(..., description="Whether the subscription is valid.")
    created_timestamp: datetime = Field(..., description="When the subscription was created.")


class XRateLimit(BaseModel):
    """Represents rate limit information for X API."""

    limit: int = Field(..., description="Rate limit for the endpoint.")
    remaining: int = Field(..., description="Remaining requests in the current window.")
    reset: datetime = Field(..., description="When the rate limit resets.")
    retry_after: int | None = Field(None, description="Seconds to wait before retrying.")


class XCostGuard(BaseModel):
    """Represents cost guard information for X API."""

    tier: str = Field(..., description="API tier (free, basic, pro, enterprise).")
    monthly_tweet_cap: int = Field(..., description="Monthly tweet cap for the tier.")
    tweets_used: int = Field(..., description="Number of tweets used this month.")
    tweets_remaining: int = Field(..., description="Number of tweets remaining this month.")
    reset_date: datetime = Field(..., description="When the monthly cap resets.")
    cost_per_tweet: float = Field(..., description="Cost per tweet in USD.")
    estimated_monthly_cost: float = Field(..., description="Estimated monthly cost in USD.")
