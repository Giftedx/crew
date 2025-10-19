"""
Platform API Wrappers with Circuit Breaker Protection

This module provides circuit breaker-protected wrappers for all platform APIs,
ensuring resilient operation and graceful degradation when services are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from .circuit_breaker_canonical import (
    get_platform_circuit_breaker,
)

logger = logging.getLogger(__name__)


class PlatformAPIWrapper:
    """Base wrapper for platform APIs with circuit breaker protection."""

    def __init__(self, platform: str, api_client: Any):
        """Initialize platform API wrapper.

        Args:
            platform: Platform name (youtube, twitch, tiktok, instagram, x)
            api_client: The underlying API client
        """
        self.platform = platform
        self.api_client = api_client
        self.circuit_breaker = get_platform_circuit_breaker(platform)

    async def call_with_circuit_breaker(self, method_name: str, *args, **kwargs) -> StepResult:
        """Call API method with circuit breaker protection.

        Args:
            method_name: Name of the API method to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            StepResult with the API response or error
        """
        try:
            method = getattr(self.api_client, method_name)
            result = await self.circuit_breaker.call(method, *args, **kwargs)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Platform API call failed: {self.platform}.{method_name}: {e}")
            return StepResult.fail(f"API call failed: {str(e)}")

    def get_health_status(self) -> dict[str, Any]:
        """Get circuit breaker health status."""
        return self.circuit_breaker.get_health_status()


class YouTubeAPIWrapper(PlatformAPIWrapper):
    """YouTube API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        super().__init__("youtube", api_client)

    async def get_video_info(self, video_id: str) -> StepResult:
        """Get video information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_video_info", video_id)

    async def get_channel_info(self, channel_id: str) -> StepResult:
        """Get channel information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_channel_info", channel_id)

    async def search_videos(self, query: str, max_results: int = 10) -> StepResult:
        """Search videos with circuit breaker protection."""
        return await self.call_with_circuit_breaker("search_videos", query, max_results)


class TwitchAPIWrapper(PlatformAPIWrapper):
    """Twitch API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        super().__init__("twitch", api_client)

    async def get_stream_info(self, user_id: str) -> StepResult:
        """Get stream information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_stream_info", user_id)

    async def get_user_info(self, username: str) -> StepResult:
        """Get user information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_user_info", username)

    async def get_clips(self, broadcaster_id: str, started_at: str, ended_at: str) -> StepResult:
        """Get clips with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_clips", broadcaster_id, started_at, ended_at)


class TikTokAPIWrapper(PlatformAPIWrapper):
    """TikTok API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        super().__init__("tiktok", api_client)

    async def get_video_info(self, video_id: str) -> StepResult:
        """Get video information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_video_info", video_id)

    async def get_user_info(self, username: str) -> StepResult:
        """Get user information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_user_info", username)

    async def search_videos(self, query: str, max_results: int = 10) -> StepResult:
        """Search videos with circuit breaker protection."""
        return await self.call_with_circuit_breaker("search_videos", query, max_results)


class InstagramAPIWrapper(PlatformAPIWrapper):
    """Instagram API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        super().__init__("instagram", api_client)

    async def get_media_info(self, media_id: str) -> StepResult:
        """Get media information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_media_info", media_id)

    async def get_user_info(self, user_id: str) -> StepResult:
        """Get user information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_user_info", user_id)

    async def get_stories(self, user_id: str) -> StepResult:
        """Get stories with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_stories", user_id)


class XAPIWrapper(PlatformAPIWrapper):
    """X (Twitter) API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        super().__init__("x", api_client)

    async def get_tweet_info(self, tweet_id: str) -> StepResult:
        """Get tweet information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_tweet_info", tweet_id)

    async def get_user_info(self, username: str) -> StepResult:
        """Get user information with circuit breaker protection."""
        return await self.call_with_circuit_breaker("get_user_info", username)

    async def search_tweets(self, query: str, max_results: int = 10) -> StepResult:
        """Search tweets with circuit breaker protection."""
        return await self.call_with_circuit_breaker("search_tweets", query, max_results)


class OpenRouterAPIWrapper:
    """OpenRouter API wrapper with circuit breaker protection."""

    def __init__(self, api_client: Any):
        self.api_client = api_client
        self.circuit_breaker = get_platform_circuit_breaker("openrouter")

    async def complete(self, prompt: str, **kwargs) -> StepResult:
        """Complete text with circuit breaker protection."""
        try:
            result = await self.circuit_breaker.call(self.api_client.complete, prompt, **kwargs)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            return StepResult.fail(f"API call failed: {str(e)}")

    async def chat_complete(self, messages: list[dict], **kwargs) -> StepResult:
        """Chat completion with circuit breaker protection."""
        try:
            result = await self.circuit_breaker.call(self.api_client.chat_complete, messages, **kwargs)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"OpenRouter chat completion failed: {e}")
            return StepResult.fail(f"Chat completion failed: {str(e)}")

    def get_health_status(self) -> dict[str, Any]:
        """Get circuit breaker health status."""
        return self.circuit_breaker.get_health_status()


class QdrantAPIWrapper:
    """Qdrant API wrapper with circuit breaker protection."""

    def __init__(self, qdrant_client: Any):
        self.qdrant_client = qdrant_client
        self.circuit_breaker = get_platform_circuit_breaker("qdrant")

    async def upsert(self, collection_name: str, points: list, **kwargs) -> StepResult:
        """Upsert points with circuit breaker protection."""
        try:
            result = await self.circuit_breaker.call(self.qdrant_client.upsert, collection_name, points, **kwargs)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Qdrant upsert failed: {e}")
            return StepResult.fail(f"Upsert failed: {str(e)}")

    async def search(self, collection_name: str, query_vector: list, limit: int = 10, **kwargs) -> StepResult:
        """Search vectors with circuit breaker protection."""
        try:
            result = await self.circuit_breaker.call(
                self.qdrant_client.search, collection_name, query_vector, limit, **kwargs
            )
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return StepResult.fail(f"Search failed: {str(e)}")

    async def delete(self, collection_name: str, points: list, **kwargs) -> StepResult:
        """Delete points with circuit breaker protection."""
        try:
            result = await self.circuit_breaker.call(self.qdrant_client.delete, collection_name, points, **kwargs)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Qdrant delete failed: {e}")
            return StepResult.fail(f"Delete failed: {str(e)}")

    def get_health_status(self) -> dict[str, Any]:
        """Get circuit breaker health status."""
        return self.circuit_breaker.get_health_status()


# Factory functions for creating wrapped API clients
def create_youtube_wrapper(api_client: Any) -> YouTubeAPIWrapper:
    """Create YouTube API wrapper."""
    return YouTubeAPIWrapper(api_client)


def create_twitch_wrapper(api_client: Any) -> TwitchAPIWrapper:
    """Create Twitch API wrapper."""
    return TwitchAPIWrapper(api_client)


def create_tiktok_wrapper(api_client: Any) -> TikTokAPIWrapper:
    """Create TikTok API wrapper."""
    return TikTokAPIWrapper(api_client)


def create_instagram_wrapper(api_client: Any) -> InstagramAPIWrapper:
    """Create Instagram API wrapper."""
    return InstagramAPIWrapper(api_client)


def create_x_wrapper(api_client: Any) -> XAPIWrapper:
    """Create X API wrapper."""
    return XAPIWrapper(api_client)


def create_openrouter_wrapper(api_client: Any) -> OpenRouterAPIWrapper:
    """Create OpenRouter API wrapper."""
    return OpenRouterAPIWrapper(api_client)


def create_qdrant_wrapper(qdrant_client: Any) -> QdrantAPIWrapper:
    """Create Qdrant API wrapper."""
    return QdrantAPIWrapper(qdrant_client)


# Global registry for tracking all wrapped APIs
_wrapped_apis: dict[str, Any] = {}


def register_wrapped_api(name: str, wrapper: Any):
    """Register a wrapped API for monitoring."""
    _wrapped_apis[name] = wrapper


def get_all_api_health_status() -> dict[str, Any]:
    """Get health status for all registered wrapped APIs."""
    health_status = {}
    for name, wrapper in _wrapped_apis.items():
        if hasattr(wrapper, "get_health_status"):
            health_status[name] = wrapper.get_health_status()
    return health_status


__all__ = [
    "PlatformAPIWrapper",
    "YouTubeAPIWrapper",
    "TwitchAPIWrapper",
    "TikTokAPIWrapper",
    "InstagramAPIWrapper",
    "XAPIWrapper",
    "OpenRouterAPIWrapper",
    "QdrantAPIWrapper",
    "create_youtube_wrapper",
    "create_twitch_wrapper",
    "create_tiktok_wrapper",
    "create_instagram_wrapper",
    "create_x_wrapper",
    "create_openrouter_wrapper",
    "create_qdrant_wrapper",
    "register_wrapped_api",
    "get_all_api_health_status",
]
