"""
TikTok API response models and DTOs.

This module defines Pydantic models for TikTok Research API and Content Posting API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TikTokUser(BaseModel):
    """TikTok user information."""

    open_id: str = Field(..., description="User's Open ID")
    union_id: str | None = Field(None, description="User's Union ID")
    avatar_url: str | None = Field(None, description="User's avatar URL")
    display_name: str = Field(..., description="User's display name")
    follower_count: int = Field(default=0, description="Number of followers")
    following_count: int = Field(default=0, description="Number of following")
    likes_count: int = Field(default=0, description="Number of likes received")
    video_count: int = Field(default=0, description="Number of videos posted")
    is_verified: bool = Field(default=False, description="Whether user is verified")


class TikTokVideo(BaseModel):
    """TikTok video information."""

    id: str = Field(..., description="Video ID")
    title: str | None = Field(None, description="Video title")
    description: str | None = Field(None, description="Video description")
    duration: int = Field(..., description="Video duration in seconds")
    cover_image_url: str | None = Field(None, description="Cover image URL")
    embed_url: str | None = Field(None, description="Embed URL")
    share_url: str | None = Field(None, description="Share URL")
    view_count: int = Field(default=0, description="Number of views")
    like_count: int = Field(default=0, description="Number of likes")
    comment_count: int = Field(default=0, description="Number of comments")
    share_count: int = Field(default=0, description="Number of shares")
    created_time: datetime = Field(..., description="Creation timestamp")
    updated_time: datetime | None = Field(None, description="Last update timestamp")
    privacy_level: str = Field(default="PUBLIC_TO_EVERYONE", description="Privacy level")
    status: str = Field(default="PUBLISHED", description="Video status")
    video_url: str | None = Field(None, description="Direct video URL")
    hashtags: list[str] = Field(default_factory=list, description="Hashtags")
    mentions: list[str] = Field(default_factory=list, description="User mentions")


class TikTokVideoList(BaseModel):
    """TikTok video list response."""

    videos: list[TikTokVideo] = Field(..., description="List of videos")
    cursor: str | None = Field(None, description="Pagination cursor")
    has_more: bool = Field(default=False, description="Whether there are more videos")


class TikTokComment(BaseModel):
    """TikTok comment information."""

    id: str = Field(..., description="Comment ID")
    text: str = Field(..., description="Comment text")
    like_count: int = Field(default=0, description="Number of likes")
    reply_count: int = Field(default=0, description="Number of replies")
    created_time: datetime = Field(..., description="Creation timestamp")
    user: TikTokUser | None = Field(None, description="Comment author")
    parent_comment_id: str | None = Field(None, description="Parent comment ID if reply")


class TikTokCommentList(BaseModel):
    """TikTok comment list response."""

    comments: list[TikTokComment] = Field(..., description="List of comments")
    cursor: str | None = Field(None, description="Pagination cursor")
    has_more: bool = Field(default=False, description="Whether there are more comments")


class TikTokInsights(BaseModel):
    """TikTok video insights."""

    video_id: str = Field(..., description="Video ID")
    view_count: int = Field(default=0, description="Total views")
    like_count: int = Field(default=0, description="Total likes")
    comment_count: int = Field(default=0, description="Total comments")
    share_count: int = Field(default=0, description="Total shares")
    profile_views: int = Field(default=0, description="Profile views from video")
    video_views_by_region: dict[str, int] = Field(default_factory=dict, description="Views by region")
    video_views_by_age_group: dict[str, int] = Field(default_factory=dict, description="Views by age group")
    video_views_by_gender: dict[str, int] = Field(default_factory=dict, description="Views by gender")
    date_range: dict[str, str] = Field(..., description="Date range for insights")


class TikTokError(BaseModel):
    """TikTok API error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    log_id: str | None = Field(None, description="Log ID for debugging")


class TikTokResponse(BaseModel):
    """Generic TikTok API response."""

    data: Any = Field(..., description="Response data")
    error: TikTokError | None = Field(None, description="Error information")
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional response data")


class TikTokUploadResponse(BaseModel):
    """TikTok video upload response."""

    publish_id: str = Field(..., description="Publish ID for tracking upload")
    upload_url: str | None = Field(None, description="Upload URL for video file")
    status: str = Field(..., description="Upload status")


class TikTokPublishStatus(BaseModel):
    """TikTok video publish status."""

    publish_id: str = Field(..., description="Publish ID")
    status: str = Field(..., description="Publish status")
    video_id: str | None = Field(None, description="Video ID if published")
    error_message: str | None = Field(None, description="Error message if failed")
    created_time: datetime | None = Field(None, description="Creation timestamp")
