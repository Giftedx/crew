"""Twitch Helix API integration client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class TwitchClient:
    """Twitch Helix API client for creator operations."""

    def __init__(self, client_id: str, access_token: str | None = None):
        self.client_id = client_id
        self.access_token = access_token
        self.base_url = "https://api.twitch.tv/helix"
        self.headers = {
            "Client-ID": client_id,
            "Content-Type": "application/json",
        }

        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> StepResult:
        """Make authenticated request to Twitch API."""
        try:
            params = params or {}
            url = f"{self.base_url}/{endpoint}"

            async def _request():
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    return response.json()

            # For now, run sync - in production would be async
            import asyncio

            data = asyncio.run(_request())

            return StepResult.ok(data=data)

        except httpx.HTTPError as e:
            logger.error(f"Twitch API request failed: {e}")
            return StepResult.fail(f"Twitch API request failed: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in Twitch API request: {e}")
            return StepResult.fail(f"Unexpected error: {e!s}")

    def get_user_info(self, user_id: str | None = None, username: str | None = None) -> StepResult:
        """Get user information."""
        if not user_id and not username:
            return StepResult.bad_request("Either user_id or username must be provided")

        params = {}
        if user_id:
            params["id"] = user_id
        if username:
            params["login"] = username

        return self._make_request("users", params)

    def get_stream_info(self, user_id: str | None = None, user_login: str | None = None) -> StepResult:
        """Get stream information."""
        params = {}
        if user_id:
            params["user_id"] = user_id
        if user_login:
            params["user_login"] = user_login

        return self._make_request("streams", params)

    def get_videos(self, user_id: str, video_type: str = "archive", max_results: int = 20) -> StepResult:
        """Get videos from a user."""
        params = {
            "user_id": user_id,
            "type": video_type,
            "first": min(max_results, 100),  # Twitch API limit
        }

        return self._make_request("videos", params)

    def get_clips(
        self,
        broadcaster_id: str,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> StepResult:
        """Get clips from a broadcaster."""
        params = {
            "broadcaster_id": broadcaster_id,
            "first": 20,
        }

        if started_at:
            params["started_at"] = started_at
        if ended_at:
            params["ended_at"] = ended_at

        return self._make_request("clips", params)

    def get_game_info(self, game_id: str | None = None, game_name: str | None = None) -> StepResult:
        """Get game information."""
        params = {}
        if game_id:
            params["id"] = game_id
        if game_name:
            params["name"] = game_name

        return self._make_request("games", params)

    def search_categories(self, query: str, max_results: int = 20) -> StepResult:
        """Search for game categories."""
        params = {
            "query": query,
            "first": min(max_results, 100),
        }

        return self._make_request("search/categories", params)

    def get_top_games(self, max_results: int = 20) -> StepResult:
        """Get top games."""
        params = {
            "first": min(max_results, 100),
        }

        return self._make_request("games/top", params)

    def get_followed_channels(self, user_id: str, max_results: int = 20) -> StepResult:
        """Get followed channels (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for followed channels")

        params = {
            "user_id": user_id,
            "first": min(max_results, 100),
        }

        return self._make_request("channels/followed", params)

    def get_channel_followers(self, broadcaster_id: str, max_results: int = 20) -> StepResult:
        """Get channel followers (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for channel followers")

        params = {
            "broadcaster_id": broadcaster_id,
            "first": min(max_results, 100),
        }

        return self._make_request("channels/followers", params)

    def get_chat_settings(self, broadcaster_id: str, moderator_id: str | None = None) -> StepResult:
        """Get chat settings (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for chat settings")

        params = {
            "broadcaster_id": broadcaster_id,
        }

        if moderator_id:
            params["moderator_id"] = moderator_id

        return self._make_request("chat/settings", params)

    def get_moderators(self, broadcaster_id: str, max_results: int = 20) -> StepResult:
        """Get channel moderators (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for moderators")

        params = {
            "broadcaster_id": broadcaster_id,
            "first": min(max_results, 100),
        }

        return self._make_request("moderation/moderators", params)

    def get_bans(self, broadcaster_id: str, max_results: int = 20) -> StepResult:
        """Get channel bans (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for bans")

        params = {
            "broadcaster_id": broadcaster_id,
            "first": min(max_results, 100),
        }

        return self._make_request("moderation/banned", params)

    def get_stream_key(self, broadcaster_id: str) -> StepResult:
        """Get stream key (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for stream key")

        params = {
            "broadcaster_id": broadcaster_id,
        }

        return self._make_request("streams/key", params)

    def get_channel_analytics(self, broadcaster_id: str, started_at: str, ended_at: str) -> StepResult:
        """Get channel analytics (requires OAuth)."""
        if not self.access_token:
            return StepResult.unauthorized("OAuth access token required for analytics")

        params = {
            "broadcaster_id": broadcaster_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "type": "overview_v2",
        }

        return self._make_request("analytics/extensions", params)

    def extract_user_id_from_url(self, url: str) -> str | None:
        """Extract user ID from Twitch URL."""
        import re

        patterns = [
            r"twitch\.tv/([^/?]+)",
            r"twitch\.tv/user/([^/?]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_chat_emotes(self, broadcaster_id: str) -> StepResult:
        """Get chat emotes for a broadcaster."""
        params = {
            "broadcaster_id": broadcaster_id,
        }

        return self._make_request("chat/emotes", params)

    def get_global_emotes(self) -> StepResult:
        """Get global chat emotes."""
        return self._make_request("chat/emotes/global")

    def get_emote_sets(self, emote_set_ids: list[str]) -> StepResult:
        """Get emotes from specific sets."""
        params = {
            "emote_set_id": emote_set_ids,
        }

        return self._make_request("chat/emotes/set", params)

    def health_check(self) -> StepResult:
        """Perform health check on Twitch client."""
        try:
            # Test with a simple API call
            result = self.get_top_games(max_results=1)

            if result.success:
                return StepResult.ok(
                    data={
                        "service": "twitch",
                        "status": "healthy",
                        "client_id_configured": bool(self.client_id),
                        "access_token_configured": bool(self.access_token),
                    }
                )
            else:
                return StepResult.fail("Twitch API health check failed")

        except Exception as e:
            logger.error(f"Twitch client health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")
