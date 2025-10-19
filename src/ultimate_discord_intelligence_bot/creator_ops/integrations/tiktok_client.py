"""
TikTok API client for Research API and Content Posting API.

This module provides a client for interacting with TikTok's APIs including
user information, video lists, comments, and content posting capabilities.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_models import (
    TikTokComment,
    TikTokCommentList,
    TikTokInsights,
    TikTokPublishStatus,
    TikTokUploadResponse,
    TikTokUser,
    TikTokVideo,
    TikTokVideoList,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class TikTokClient:
    """
    TikTok API client with Research API and Content Posting API support.

    Features:
    - User information retrieval
    - Video list and details
    - Comments and insights
    - Content posting and publishing
    - 5xx retry logic with exponential backoff
    - Regional eligibility checks
    - OAuth token management
    """

    def __init__(self, config: CreatorOpsConfig | None = None) -> None:
        """Initialize TikTok client."""
        self.config = config or CreatorOpsConfig()
        self.base_url = "https://open-api.tiktok.com"
        self.research_api_url = f"{self.base_url}/research"
        self.content_api_url = f"{self.base_url}/content"

        # API credentials
        self.client_key = self.config.tiktok_client_key
        self.client_secret = self.config.tiktok_client_secret
        self.access_token = self.config.tiktok_access_token

        # Rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = None

        # Regional eligibility
        self.supported_regions = ["US", "GB", "CA", "AU", "DE", "FR", "IT", "ES", "NL", "SE"]

        logger.info("TikTokClient initialized")

    def _get_headers(self, include_auth: bool = True) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "CreatorOps/1.0",
        }

        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def _check_rate_limit(self, response: httpx.Response) -> None:
        """Check and update rate limit information."""
        if "X-RateLimit-Remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])

        if "X-RateLimit-Reset" in response.headers:
            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])

    def _check_regional_eligibility(self, region: str | None = None) -> bool:
        """Check if the region is supported by TikTok APIs."""
        if not region:
            region = self.config.default_region or "US"

        return region.upper() in self.supported_regions

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: None,
    )
    def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic for 5xx errors."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers or self._get_headers(),
                )

                # Check rate limits
                self._check_rate_limit(response)

                # Retry on 5xx errors
                if 500 <= response.status_code < 600:
                    logger.warning(f"TikTok API 5xx error: {response.status_code}, retrying...")
                    response.raise_for_status()

                return response

        except httpx.HTTPStatusError as e:
            if 500 <= e.response.status_code < 600:
                logger.warning(f"TikTok API 5xx error: {e.response.status_code}, retrying...")
                raise
            else:
                logger.error(f"TikTok API error: {e.response.status_code} - {e.response.text}")
                raise
        except Exception as e:
            logger.error(f"TikTok API request failed: {str(e)}")
            raise

    def get_user_info(self, open_id: str | None = None) -> StepResult:
        """
        Get user information.

        Args:
            open_id: User's Open ID (optional, uses token owner if not provided)

        Returns:
            StepResult with TikTokUser data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.research_api_url}/user/info/"
            params = {}

            if open_id:
                params["open_id"] = open_id

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            user_data = data.get("data", {}).get("user", {})
            user = TikTokUser(**user_data)

            return StepResult.ok(data=user)

        except Exception as e:
            logger.error(f"Failed to get TikTok user info: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok user info: {str(e)}")

    def get_video_list(
        self,
        open_id: str | None = None,
        cursor: str | None = None,
        max_count: int = 20,
    ) -> StepResult:
        """
        Get user's video list.

        Args:
            open_id: User's Open ID (optional, uses token owner if not provided)
            cursor: Pagination cursor
            max_count: Maximum number of videos to return (max 20)

        Returns:
            StepResult with TikTokVideoList data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.research_api_url}/video/list/"
            params = {
                "max_count": min(max_count, 20),
            }

            if open_id:
                params["open_id"] = open_id

            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            video_data = data.get("data", {})
            videos = [TikTokVideo(**video) for video in video_data.get("videos", [])]

            video_list = TikTokVideoList(
                videos=videos,
                cursor=video_data.get("cursor"),
                has_more=video_data.get("has_more", False),
            )

            return StepResult.ok(data=video_list)

        except Exception as e:
            logger.error(f"Failed to get TikTok video list: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok video list: {str(e)}")

    def get_video_details(self, video_id: str) -> StepResult:
        """
        Get video details.

        Args:
            video_id: Video ID

        Returns:
            StepResult with TikTokVideo data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.research_api_url}/video/query/"
            params = {
                "video_id": video_id,
            }

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            video_data = data.get("data", {}).get("videos", [])
            if not video_data:
                return StepResult.fail("Video not found")

            video = TikTokVideo(**video_data[0])

            return StepResult.ok(data=video)

        except Exception as e:
            logger.error(f"Failed to get TikTok video details: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok video details: {str(e)}")

    def get_video_comments(
        self,
        video_id: str,
        cursor: str | None = None,
        max_count: int = 20,
    ) -> StepResult:
        """
        Get video comments.

        Args:
            video_id: Video ID
            cursor: Pagination cursor
            max_count: Maximum number of comments to return (max 20)

        Returns:
            StepResult with TikTokCommentList data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.research_api_url}/video/comment/list/"
            params = {
                "video_id": video_id,
                "max_count": min(max_count, 20),
            }

            if cursor:
                params["cursor"] = cursor

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            comment_data = data.get("data", {})
            comments = [TikTokComment(**comment) for comment in comment_data.get("comments", [])]

            comment_list = TikTokCommentList(
                comments=comments,
                cursor=comment_data.get("cursor"),
                has_more=comment_data.get("has_more", False),
            )

            return StepResult.ok(data=comment_list)

        except Exception as e:
            logger.error(f"Failed to get TikTok video comments: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok video comments: {str(e)}")

    def get_video_insights(
        self,
        video_id: str,
        date_range: dict[str, str] | None = None,
    ) -> StepResult:
        """
        Get video insights.

        Args:
            video_id: Video ID
            date_range: Date range for insights (start_date, end_date)

        Returns:
            StepResult with TikTokInsights data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.research_api_url}/video/insights/"
            params = {
                "video_id": video_id,
            }

            if date_range:
                params.update(date_range)

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            insights_data = data.get("data", {})
            insights = TikTokInsights(
                video_id=video_id,
                view_count=insights_data.get("view_count", 0),
                like_count=insights_data.get("like_count", 0),
                comment_count=insights_data.get("comment_count", 0),
                share_count=insights_data.get("share_count", 0),
                profile_views=insights_data.get("profile_views", 0),
                video_views_by_region=insights_data.get("video_views_by_region", {}),
                video_views_by_age_group=insights_data.get("video_views_by_age_group", {}),
                video_views_by_gender=insights_data.get("video_views_by_gender", {}),
                date_range=date_range or {"start_date": "", "end_date": ""},
            )

            return StepResult.ok(data=insights)

        except Exception as e:
            logger.error(f"Failed to get TikTok video insights: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok video insights: {str(e)}")

    def upload_video(
        self,
        video_file_path: str,
        title: str,
        description: str | None = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        hashtags: list[str] | None = None,
    ) -> StepResult:
        """
        Upload video to TikTok.

        Args:
            video_file_path: Path to video file
            title: Video title
            description: Video description
            privacy_level: Privacy level (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIEND, PRIVATE)
            hashtags: List of hashtags

        Returns:
            StepResult with TikTokUploadResponse data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            # Step 1: Initialize upload
            url = f"{self.content_api_url}/post/publish/video/init/"
            json_data = {
                "post_info": {
                    "title": title,
                    "description": description or "",
                    "privacy_level": privacy_level,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                    "video_cover_timestamp_ms": 1000,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": 0,  # Will be updated after file upload
                    "chunk_size": 0,  # Will be updated after file upload
                },
            }

            if hashtags:
                json_data["post_info"]["hashtags"] = hashtags

            response = self._make_request("POST", url, json_data=json_data)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            upload_data = data.get("data", {})
            publish_id = upload_data.get("publish_id")
            upload_url = upload_data.get("upload_url")

            if not publish_id or not upload_url:
                return StepResult.fail("Failed to initialize TikTok video upload")

            # Step 2: Upload video file
            with open(video_file_path, "rb") as video_file:
                upload_response = httpx.put(upload_url, content=video_file.read())
                upload_response.raise_for_status()

            upload_response_data = TikTokUploadResponse(
                publish_id=publish_id,
                upload_url=upload_url,
                status="UPLOADED",
            )

            return StepResult.ok(data=upload_response_data)

        except Exception as e:
            logger.error(f"Failed to upload TikTok video: {str(e)}")
            return StepResult.fail(f"Failed to upload TikTok video: {str(e)}")

    def publish_video(self, publish_id: str) -> StepResult:
        """
        Publish uploaded video.

        Args:
            publish_id: Publish ID from upload response

        Returns:
            StepResult with TikTokPublishStatus data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.content_api_url}/post/publish/"
            json_data = {
                "publish_id": publish_id,
            }

            response = self._make_request("POST", url, json_data=json_data)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            publish_data = data.get("data", {})
            status = TikTokPublishStatus(
                publish_id=publish_id,
                status=publish_data.get("status", "UNKNOWN"),
                video_id=publish_data.get("video_id"),
                error_message=publish_data.get("error_message"),
                created_time=publish_data.get("created_time"),
            )

            return StepResult.ok(data=status)

        except Exception as e:
            logger.error(f"Failed to publish TikTok video: {str(e)}")
            return StepResult.fail(f"Failed to publish TikTok video: {str(e)}")

    def get_publish_status(self, publish_id: str) -> StepResult:
        """
        Get video publish status.

        Args:
            publish_id: Publish ID

        Returns:
            StepResult with TikTokPublishStatus data
        """
        try:
            if not self.access_token:
                return StepResult.fail("TikTok access token not configured")

            # Check regional eligibility
            if not self._check_regional_eligibility():
                return StepResult.fail("Region not supported by TikTok APIs")

            url = f"{self.content_api_url}/post/publish/status/fetch/"
            params = {
                "publish_id": publish_id,
            }

            response = self._make_request("GET", url, params=params)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                return StepResult.fail(f"TikTok API error: {data['error']['message']}")

            status_data = data.get("data", {})
            status = TikTokPublishStatus(
                publish_id=publish_id,
                status=status_data.get("status", "UNKNOWN"),
                video_id=status_data.get("video_id"),
                error_message=status_data.get("error_message"),
                created_time=status_data.get("created_time"),
            )

            return StepResult.ok(data=status)

        except Exception as e:
            logger.error(f"Failed to get TikTok publish status: {str(e)}")
            return StepResult.fail(f"Failed to get TikTok publish status: {str(e)}")

    def get_rate_limit_info(self) -> dict[str, Any]:
        """Get current rate limit information."""
        return {
            "remaining": self.rate_limit_remaining,
            "reset": self.rate_limit_reset,
            "supported_regions": self.supported_regions,
        }

    def _get_fixture_response(self, endpoint: str) -> dict[str, Any]:
        """Get fixture response for testing."""
        try:
            from pathlib import Path

            fixture_file = (
                Path(__file__).parent.parent.parent.parent / "fixtures" / "creator_ops" / f"tiktok_{endpoint}.json"
            )

            if fixture_file.exists():
                with open(fixture_file) as f:
                    return json.load(f)
            else:
                logger.warning(f"Fixture file not found: {fixture_file}")
                return {}

        except Exception as e:
            logger.warning(f"Failed to load fixture response: {str(e)}")
            return {}
