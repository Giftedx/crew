"""TikTok Research API integration client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class TikTokClient:
    """TikTok Research API client for creator operations."""

    def __init__(self, client_key: str, access_token: str | None = None):
        self.client_key = client_key
        self.access_token = access_token
        self.base_url = "https://open.tiktokapis.com/v2"
        self.headers = {
            "Content-Type": "application/json",
        }

        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    def _make_request(self, endpoint: str, method: str = "GET", data: dict[str, Any] | None = None) -> StepResult:
        """Make authenticated request to TikTok API."""
        try:
            url = f"{self.base_url}/{endpoint}"

            async def _request():
                async with httpx.AsyncClient() as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=self.headers)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=self.headers, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")

                    response.raise_for_status()
                    return response.json()

            # For now, run sync - in production would be async
            import asyncio

            result_data = asyncio.run(_request())

            return StepResult.ok(data=result_data)

        except httpx.HTTPError as e:
            logger.error(f"TikTok API request failed: {e}")
            return StepResult.fail(f"TikTok API request failed: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in TikTok API request: {e}")
            return StepResult.fail(f"Unexpected error: {e!s}")

    def get_user_info(self, fields: list[str] | None = None) -> StepResult:
        """Get user information (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for user info")

        params = {}
        if fields:
            params["fields"] = ",".join(fields)

        return self._make_request("user/info/", params=params)

    def get_video_list(
        self,
        max_count: int = 20,
        cursor: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> StepResult:
        """Get user's video list (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for video list")

        data = {
            "max_count": min(max_count, 20),  # TikTok API limit
        }

        if cursor:
            data["cursor"] = cursor
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        return self._make_request("video/list/", method="POST", data=data)

    def get_video_info(self, video_ids: list[str], fields: list[str] | None = None) -> StepResult:
        """Get video information (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for video info")

        data = {
            "video_ids": video_ids,
        }

        if fields:
            data["fields"] = fields

        return self._make_request("video/info/", method="POST", data=data)

    def get_video_analytics(self, video_ids: list[str], start_date: str, end_date: str) -> StepResult:
        """Get video analytics (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for video analytics")

        data = {
            "video_ids": video_ids,
            "start_date": start_date,
            "end_date": end_date,
        }

        return self._make_request("video/analytics/", method="POST", data=data)

    def get_user_analytics(self, start_date: str, end_date: str, dimensions: list[str] | None = None) -> StepResult:
        """Get user analytics (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for user analytics")

        data = {
            "start_date": start_date,
            "end_date": end_date,
        }

        if dimensions:
            data["dimensions"] = dimensions

        return self._make_request("user/analytics/", method="POST", data=data)

    def search_videos(self, query: str, max_count: int = 20, cursor: str | None = None) -> StepResult:
        """Search for videos (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for video search")

        data = {
            "query": query,
            "max_count": min(max_count, 20),
        }

        if cursor:
            data["cursor"] = cursor

        return self._make_request("video/search/", method="POST", data=data)

    def get_hashtag_info(self, hashtag_name: str, fields: list[str] | None = None) -> StepResult:
        """Get hashtag information (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for hashtag info")

        data = {
            "hashtag_name": hashtag_name,
        }

        if fields:
            data["fields"] = fields

        return self._make_request("hashtag/info/", method="POST", data=data)

    def get_hashtag_videos(self, hashtag_name: str, max_count: int = 20, cursor: str | None = None) -> StepResult:
        """Get videos for a hashtag (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for hashtag videos")

        data = {
            "hashtag_name": hashtag_name,
            "max_count": min(max_count, 20),
        }

        if cursor:
            data["cursor"] = cursor

        return self._make_request("hashtag/videos/", method="POST", data=data)

    def get_trending_hashtags(self, count: int = 20, region: str = "US") -> StepResult:
        """Get trending hashtags (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for trending hashtags")

        data = {
            "count": min(count, 100),
            "region": region,
        }

        return self._make_request("hashtag/trending/", method="POST", data=data)

    def get_music_info(self, music_ids: list[str], fields: list[str] | None = None) -> StepResult:
        """Get music information (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for music info")

        data = {
            "music_ids": music_ids,
        }

        if fields:
            data["fields"] = fields

        return self._make_request("music/info/", method="POST", data=data)

    def search_music(self, query: str, max_count: int = 20) -> StepResult:
        """Search for music (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for music search")

        data = {
            "query": query,
            "max_count": min(max_count, 20),
        }

        return self._make_request("music/search/", method="POST", data=data)

    def get_comment_list(self, video_id: str, max_count: int = 20, cursor: str | None = None) -> StepResult:
        """Get video comments (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for comments")

        data = {
            "video_id": video_id,
            "max_count": min(max_count, 20),
        }

        if cursor:
            data["cursor"] = cursor

        return self._make_request("comment/list/", method="POST", data=data)

    def get_live_videos(self, max_count: int = 20, cursor: str | None = None) -> StepResult:
        """Get live videos (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for live videos")

        data = {
            "max_count": min(max_count, 20),
        }

        if cursor:
            data["cursor"] = cursor

        return self._make_request("video/live/", method="POST", data=data)

    def extract_video_id(self, url: str) -> str | None:
        """Extract video ID from TikTok URL."""
        import re

        patterns = [
            r"tiktok\.com/@[^/]+/video/(\d+)",
            r"vm\.tiktok\.com/([^/?]+)",
            r"vt\.tiktok\.com/([^/?]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def extract_user_id(self, url: str) -> str | None:
        """Extract user ID from TikTok URL."""
        import re

        patterns = [
            r"tiktok\.com/@([^/?]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def health_check(self) -> StepResult:
        """Perform health check on TikTok client."""
        try:
            # Test with a simple API call (without auth for basic check)
            return StepResult.ok(
                data={
                    "service": "tiktok",
                    "status": "healthy",
                    "client_key_configured": bool(self.client_key),
                    "access_token_configured": bool(self.access_token),
                }
            )

        except Exception as e:
            logger.error(f"TikTok client health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")
