"""
Twitch Helix API client with EventSub WebSocket support.

This client provides comprehensive access to Twitch's Helix API with proper
error handling, rate limiting, OAuth support, and EventSub WebSocket integration.
"""

from __future__ import annotations
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar
import websockets
from core import http_utils
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_models import (
    TwitchChatMessage,
    TwitchClip,
    TwitchEventSubEvent,
    TwitchRateLimit,
    TwitchStream,
    TwitchStreamMarker,
    TwitchUser,
    TwitchVideo,
    TwitchWebSocketMessage,
)
from platform.core.step_result import StepResult

if TYPE_CHECKING:
    from collections.abc import Callable
    from ultimate_discord_intelligence_bot.creator_ops.auth.oauth_manager import TwitchOAuthManager
logger = logging.getLogger(__name__)


class TwitchClient:
    """
    Twitch Helix API client with comprehensive features.

    Features:
    - Helix API integration
    - EventSub WebSocket support
    - Rate limiting and backoff
    - OAuth token management
    - Stream markers creation
    - VOD and clips fetching
    - Chat message retrieval
    - Fixture mode for testing
    """

    BASE_URL = "https://api.twitch.tv/helix"
    EVENTSUB_WS_URL = "wss://eventsub.wss.twitch.tv/ws"
    RATE_LIMITS: ClassVar[dict[str, int]] = {"default": 800, "moderator": 1200, "broadcaster": 1200}

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        oauth_manager: TwitchOAuthManager | None = None,
        config: CreatorOpsConfig | None = None,
        fixture_mode: bool = False,
    ) -> None:
        """Initialize Twitch client."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_manager = oauth_manager
        self.config = config or CreatorOpsConfig()
        self.fixture_mode = fixture_mode
        self.last_request_time = 0.0
        self.min_request_interval = 0.075
        self.rate_limit = TwitchRateLimit(limit=800, remaining=800)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Accept": "application/vnd.twitchtv.v5+json", "Client-ID": self.client_id or ""}
        if self.oauth_manager:
            token_result = self.oauth_manager.get_valid_token()
            if token_result.success:
                headers["Authorization"] = f"Bearer {token_result.data['access_token']}"
        return headers

    def _rate_limit(self) -> None:
        """Apply rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _update_rate_limit(self, response: http_utils.requests.Response) -> None:
        """Update rate limit from response headers."""
        self.rate_limit = TwitchRateLimit.from_headers(response.headers)

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> StepResult:
        """Make authenticated request to Twitch API."""
        if self.fixture_mode:
            return self._get_fixture_response(endpoint, params or {})
        self._rate_limit()
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_headers()
        try:
            response = http_utils.retrying_get(url, params=params or None, headers=headers, timeout_seconds=30)
            response.raise_for_status()
            self._update_rate_limit(response)
            data = response.json()
            return StepResult.ok(data=data)
        except http_utils.requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Ratelimit-Reset", 60))
                logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            elif e.response.status_code == 401:
                return StepResult.unauthorized("Twitch API authentication failed")
            elif e.response.status_code == 403:
                return StepResult.fail("Forbidden - check OAuth scopes")
            else:
                return StepResult.fail(f"HTTP error {e.response.status_code}: {e!s}")
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f"Request failed: {e!s}")
        except Exception as e:
            return StepResult.fail(f"Unexpected error: {e!s}")

    def _get_fixture_response(self, endpoint: str, params: dict[str, Any]) -> StepResult:
        """Get fixture response for testing."""
        try:
            fixture_file = f"fixtures/creator_ops/twitch_{endpoint.replace('/', '_')}.json"
            with open(fixture_file) as f:
                fixture_data = json.load(f)
            return StepResult.ok(data=fixture_data)
        except FileNotFoundError:
            return StepResult.fail(f"Fixture file not found: {fixture_file}")
        except Exception as e:
            return StepResult.fail(f"Fixture error: {e!s}")

    def get_user(self, user_id: str | None = None, login: str | None = None) -> StepResult:
        """Get user information."""
        params = {}
        if user_id:
            params["id"] = user_id
        if login:
            params["login"] = login
        if not params:
            return StepResult.fail("Either user_id or login must be provided")
        result = self._make_request("users", params)
        if not result.success:
            return result
        data = result.data
        if not data.get("data"):
            return StepResult.fail("User not found")
        user = TwitchUser.from_api_data(data["data"][0])
        return StepResult.ok(data=user)

    def get_streams(
        self,
        user_id: str | None = None,
        user_login: str | None = None,
        game_id: str | None = None,
        type: str | None = None,
        language: str | None = None,
        first: int = 20,
    ) -> StepResult:
        """Get live streams."""
        params = {"first": min(first, 100)}
        if user_id:
            params["user_id"] = user_id
        if user_login:
            params["user_login"] = user_login
        if game_id:
            params["game_id"] = game_id
        if type:
            params["type"] = type
        if language:
            params["language"] = language
        result = self._make_request("streams", params)
        if not result.success:
            return result
        data = result.data
        streams = [TwitchStream.from_api_data(item) for item in data.get("data", [])]
        return StepResult.ok(data={"streams": streams, "pagination": data.get("pagination")})

    def get_videos(
        self,
        user_id: str | None = None,
        game_id: str | None = None,
        id: str | None = None,
        language: str | None = None,
        period: str = "all",
        sort: str = "time",
        type: str = "all",
        first: int = 20,
    ) -> StepResult:
        """Get videos (VODs)."""
        params = {"first": min(first, 100), "period": period, "sort": sort, "type": type}
        if user_id:
            params["user_id"] = user_id
        if game_id:
            params["game_id"] = game_id
        if id:
            params["id"] = id
        if language:
            params["language"] = language
        result = self._make_request("videos", params)
        if not result.success:
            return result
        data = result.data
        videos = [TwitchVideo.from_api_data(item) for item in data.get("data", [])]
        return StepResult.ok(data={"videos": videos, "pagination": data.get("pagination")})

    def get_clips(
        self,
        broadcaster_id: str | None = None,
        game_id: str | None = None,
        id: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        first: int = 20,
    ) -> StepResult:
        """Get clips."""
        params = {"first": min(first, 100)}
        if broadcaster_id:
            params["broadcaster_id"] = broadcaster_id
        if game_id:
            params["game_id"] = game_id
        if id:
            params["id"] = id
        if started_at:
            params["started_at"] = started_at.isoformat() + "Z"
        if ended_at:
            params["ended_at"] = ended_at.isoformat() + "Z"
        result = self._make_request("clips", params)
        if not result.success:
            return result
        data = result.data
        clips = [TwitchClip.from_api_data(item) for item in data.get("data", [])]
        return StepResult.ok(data={"clips": clips, "pagination": data.get("pagination")})

    def create_stream_marker(self, user_id: str, description: str | None = None) -> StepResult:
        """Create a stream marker."""
        if self.fixture_mode:
            mock_marker = {
                "id": "test_marker_id",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "description": description or "Test marker",
                "position_seconds": 300,
                "url": "https://www.twitch.tv/videos/test_video?t=5m",
            }
            return StepResult.ok(data=TwitchStreamMarker.from_api_data(mock_marker))
        self._rate_limit()
        url = f"{self.BASE_URL}/streams/markers"
        headers = self._get_headers()
        data = {"user_id": user_id}
        if description:
            data["description"] = description
        try:
            response = http_utils.retrying_post(url, json_payload=data, headers=headers, timeout_seconds=30)
            response.raise_for_status()
            self._update_rate_limit(response)
            response_data = response.json()
            if not response_data.get("data"):
                return StepResult.fail("Failed to create stream marker")
            marker = TwitchStreamMarker.from_api_data(response_data["data"][0])
            return StepResult.ok(data=marker)
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f"Failed to create stream marker: {e!s}")

    def get_chat_messages(self, broadcaster_id: str, moderator_id: str, first: int = 100) -> StepResult:
        """Get chat messages (requires moderator access)."""
        params = {"broadcaster_id": broadcaster_id, "moderator_id": moderator_id, "first": min(first, 1000)}
        result = self._make_request("chat/messages", params)
        if not result.success:
            return result
        data = result.data
        messages = [TwitchChatMessage.from_api_data(item) for item in data.get("data", [])]
        return StepResult.ok(data={"messages": messages, "pagination": data.get("pagination")})

    def get_eventsub_subscriptions(self) -> StepResult:
        """Get EventSub subscriptions."""
        result = self._make_request("eventsub/subscriptions")
        if not result.success:
            return result
        data = result.data
        subscriptions = [TwitchEventSubEvent.from_api_data(item) for item in data.get("data", [])]
        return StepResult.ok(
            data={"subscriptions": subscriptions, "total": data.get("total"), "pagination": data.get("pagination")}
        )

    def create_eventsub_subscription(
        self, type: str, version: str, condition: dict[str, Any], transport: dict[str, Any]
    ) -> StepResult:
        """Create EventSub subscription."""
        if self.fixture_mode:
            mock_subscription = {
                "id": "test_subscription_id",
                "type": type,
                "version": version,
                "status": "enabled",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "condition": condition,
                "transport": transport,
                "cost": 0,
            }
            return StepResult.ok(data=TwitchEventSubEvent.from_api_data(mock_subscription))
        self._rate_limit()
        url = f"{self.BASE_URL}/eventsub/subscriptions"
        headers = self._get_headers()
        data = {"type": type, "version": version, "condition": condition, "transport": transport}
        try:
            response = http_utils.retrying_post(url, json_payload=data, headers=headers, timeout_seconds=30)
            response.raise_for_status()
            self._update_rate_limit(response)
            response_data = response.json()
            if not response_data.get("data"):
                return StepResult.fail("Failed to create EventSub subscription")
            subscription = TwitchEventSubEvent.from_api_data(response_data["data"][0])
            return StepResult.ok(data=subscription)
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f"Failed to create EventSub subscription: {e!s}")

    def delete_eventsub_subscription(self, subscription_id: str) -> StepResult:
        """Delete EventSub subscription."""
        if self.fixture_mode:
            return StepResult.ok(data={"deleted": True})
        self._rate_limit()
        url = f"{self.BASE_URL}/eventsub/subscriptions"
        headers = self._get_headers()
        params = {"id": subscription_id}
        try:
            response = http_utils.retrying_delete(url, params=params, headers=headers, timeout_seconds=30)
            response.raise_for_status()
            self._update_rate_limit(response)
            return StepResult.ok(data={"deleted": True})
        except http_utils.requests.exceptions.RequestException as e:
            return StepResult.fail(f"Failed to delete EventSub subscription: {e!s}")

    async def connect_eventsub_websocket(
        self, callback: Callable[[TwitchWebSocketMessage], None], max_duration_minutes: int = 60
    ) -> StepResult:
        """Connect to EventSub WebSocket and listen for events."""
        if self.fixture_mode:
            await asyncio.sleep(1)
            mock_message = TwitchWebSocketMessage(
                metadata={
                    "message_id": "test_message_id",
                    "message_type": "notification",
                    "message_timestamp": datetime.utcnow().isoformat() + "Z",
                },
                payload={
                    "subscription": {"id": "test_subscription_id", "type": "stream.online", "version": "1"},
                    "event": {
                        "id": "test_stream_id",
                        "broadcaster_user_id": "test_user_id",
                        "broadcaster_user_login": "testuser",
                        "broadcaster_user_name": "TestUser",
                        "type": "live",
                        "started_at": datetime.utcnow().isoformat() + "Z",
                    },
                },
            )
            await callback(mock_message)
            return StepResult.ok(data={"status": "connected", "duration_minutes": 1})
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=max_duration_minutes)
        try:
            async with websockets.connect(self.EVENTSUB_WS_URL) as websocket:
                logger.info("Connected to Twitch EventSub WebSocket")
                keepalive_message = {"type": "ping"}
                await websocket.send(json.dumps(keepalive_message))
                while datetime.utcnow() < end_time:
                    try:
                        message_data = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message_data)
                        message = TwitchWebSocketMessage.from_websocket_data(data)
                        await callback(message)
                        if message.message_type == "session_keepalive":
                            await websocket.send(json.dumps(keepalive_message))
                    except TimeoutError:
                        await websocket.send(json.dumps(keepalive_message))
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                return StepResult.ok(data={"status": "completed", "duration_minutes": max_duration_minutes})
        except Exception as e:
            return StepResult.fail(f"WebSocket connection failed: {e!s}")

    def get_rate_limit_info(self) -> dict[str, Any]:
        """Get current rate limit information."""
        return {
            "limit": self.rate_limit.limit,
            "remaining": self.rate_limit.remaining,
            "reset_time": self.rate_limit.reset_time.isoformat() if self.rate_limit.reset_time else None,
        }

    def close(self) -> None:
        """Close the client and cleanup resources."""
        return None
