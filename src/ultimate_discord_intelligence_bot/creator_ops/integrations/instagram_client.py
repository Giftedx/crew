"""
Instagram Graph API client for Business and Creator accounts.
"""

import logging
from datetime import datetime
from typing import Any

import httpx  # type: ignore[import-not-found]
from tenacity import (  # type: ignore[import-not-found]
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from ultimate_discord_intelligence_bot.creator_ops.auth.oauth_manager import (
    OAuthManager,
)
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_models import (
    InstagramAccountInsight,
    InstagramComment,
    InstagramError,
    InstagramHashtag,
    InstagramInsight,
    InstagramLongLivedToken,
    InstagramMedia,
    InstagramMediaInsight,
    InstagramStory,
    InstagramUser,
    InstagramWebhookEvent,
    InstagramWebhookSubscription,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class InstagramClient:
    """
    Client for interacting with the Instagram Graph API.
    Handles OAuth 2.0, API requests with retry logic, pagination, and webhook management.
    """

    BASE_URL = "https://graph.facebook.com/v18.0"
    STORIES_API_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, config: CreatorOpsConfig, oauth_manager: OAuthManager):
        self.config = config
        self.oauth_manager = oauth_manager
        self.client = httpx.AsyncClient(timeout=self.config.INSTAGRAM_API_TIMEOUT)
        self.app_id = self.config.INSTAGRAM_APP_ID
        self.app_secret = self.config.INSTAGRAM_APP_SECRET
        self.redirect_uri = self.config.INSTAGRAM_REDIRECT_URI
        self.scope = "instagram_basic,instagram_manage_insights,instagram_manage_comments,instagram_manage_messages"

        logger.info("InstagramClient initialized.")

    async def _get_access_token(self, creator_id: str) -> StepResult[str]:
        """Retrieves an access token for the given creator."""
        token_result = await self.oauth_manager.get_access_token(
            platform="instagram", creator_id=creator_id, scopes=self.scope.split(",")
        )
        if not token_result.success:
            return StepResult.fail(f"Failed to get Instagram access token: {token_result.error}")
        return StepResult.success(token_result.data)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        retry_error_callback=lambda retry_state: StepResult.fail(
            f"Instagram API request failed after multiple retries: {retry_state.outcome.exception()}"
        ),
        reraise=True,
    )
    async def _make_api_request(
        self,
        method: str,
        url: str,
        creator_id: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        base_url: str = BASE_URL,
    ) -> StepResult[dict[str, Any]]:
        """Helper to make authenticated API requests to Instagram."""
        access_token_result = await self._get_access_token(creator_id)
        if not access_token_result.success:
            return access_token_result.as_failure()

        token = access_token_result.data
        full_url = f"{base_url}{url}"

        _headers = (
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                **headers,
            }
            if headers
            else {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        try:
            logger.debug(f"Making Instagram API request: {method} {full_url} with params {params}")
            response = await self.client.request(method, full_url, json=json, params=params, headers=_headers)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                instagram_error = InstagramError(**data["error"])
                logger.error(f"Instagram API error: {instagram_error.message} (Code: {instagram_error.code})")
                return StepResult.fail(f"Instagram API error: {instagram_error.message}")

            return StepResult.success(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"Instagram API HTTP error for {full_url}: {e.response.status_code} - {e.response.text}")
            if 500 <= e.response.status_code < 600:
                raise
            return StepResult.fail(f"Instagram API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Instagram API request error for {full_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Instagram API request to {full_url}: {e}")
            return StepResult.fail(f"Unexpected error: {e}")

    async def get_user_info(self, creator_id: str, fields: list[str] | None = None) -> StepResult[InstagramUser]:
        """
        Fetches information about an Instagram user.
        Requires 'instagram_basic' scope.
        """
        url = f"/{creator_id}"
        params = {"fields": ",".join(fields)} if fields else None
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        user_data = result.data
        if not user_data:
            return StepResult.fail("User data not found in Instagram API response.")

        try:
            return StepResult.success(InstagramUser(**user_data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse Instagram user data: {e}")

    async def get_user_media(
        self,
        creator_id: str,
        limit: int = 25,
        after: str | None = None,
        fields: list[str] | None = None,
    ) -> StepResult[tuple[list[InstagramMedia], str | None]]:
        """
        Fetches media for an Instagram user.
        Requires 'instagram_basic' scope. Supports pagination.
        """
        url = f"/{creator_id}/media"
        params = {
            "limit": limit,
            "after": after,
            "fields": ",".join(fields) if fields else None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data = result.data.get("data", [])
        paging = result.data.get("paging", {})
        next_cursor = paging.get("cursors", {}).get("after") if paging else None

        media_items = []
        for media_data in data:
            try:
                media_items.append(InstagramMedia(**media_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram media data: {e} - {media_data}")

        return StepResult.success((media_items, next_cursor))

    async def get_media_comments(
        self,
        creator_id: str,
        media_id: str,
        limit: int = 25,
        after: str | None = None,
    ) -> StepResult[tuple[list[InstagramComment], str | None]]:
        """
        Fetches comments for a specific Instagram media item.
        Requires 'instagram_manage_comments' scope.
        """
        url = f"/{media_id}/comments"
        params = {
            "limit": limit,
            "after": after,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data = result.data.get("data", [])
        paging = result.data.get("paging", {})
        next_cursor = paging.get("cursors", {}).get("after") if paging else None

        comments = []
        for comment_data in data:
            try:
                comments.append(InstagramComment(**comment_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram comment data: {e} - {comment_data}")

        return StepResult.success((comments, next_cursor))

    async def get_user_stories(
        self,
        creator_id: str,
        fields: list[str] | None = None,
    ) -> StepResult[list[InstagramStory]]:
        """
        Fetches stories for an Instagram user.
        Requires 'instagram_basic' scope.
        """
        url = f"/{creator_id}/stories"
        params = {"fields": ",".join(fields)} if fields else None

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data = result.data.get("data", [])
        stories = []
        for story_data in data:
            try:
                stories.append(InstagramStory(**story_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram story data: {e} - {story_data}")

        return StepResult.success(stories)

    async def get_media_insights(
        self,
        creator_id: str,
        media_id: str,
        metrics: list[str],
    ) -> StepResult[InstagramMediaInsight]:
        """
        Fetches insights for a specific Instagram media item.
        Requires 'instagram_manage_insights' scope.
        """
        url = f"/{media_id}/insights"
        params = {"metric": ",".join(metrics)}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        insights_data = result.data.get("data", [])
        insights = []
        for insight_data in insights_data:
            try:
                insights.append(InstagramInsight(**insight_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram insight data: {e} - {insight_data}")

        return StepResult.success(
            InstagramMediaInsight(media_id=media_id, insights=insights, timestamp=datetime.utcnow())
        )

    async def get_account_insights(
        self,
        creator_id: str,
        metrics: list[str],
        period: str = "day",
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> StepResult[InstagramAccountInsight]:
        """
        Fetches insights for an Instagram account.
        Requires 'instagram_manage_insights' scope.
        """
        url = f"/{creator_id}/insights"
        params = {
            "metric": ",".join(metrics),
            "period": period,
        }

        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        insights_data = result.data.get("data", [])
        insights = []
        for insight_data in insights_data:
            try:
                insights.append(InstagramInsight(**insight_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram insight data: {e} - {insight_data}")

        return StepResult.success(
            InstagramAccountInsight(
                account_id=creator_id,
                insights=insights,
                timestamp=datetime.utcnow(),
                period=period,
            )
        )

    async def search_hashtags(
        self,
        creator_id: str,
        query: str,
        limit: int = 25,
    ) -> StepResult[list[InstagramHashtag]]:
        """
        Searches for Instagram hashtags.
        Requires 'instagram_basic' scope.
        """
        url = "/ig_hashtag_search"
        params = {
            "q": query,
            "limit": limit,
        }

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data = result.data.get("data", [])
        hashtags = []
        for hashtag_data in data:
            try:
                hashtags.append(InstagramHashtag(**hashtag_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram hashtag data: {e} - {hashtag_data}")

        return StepResult.success(hashtags)

    async def get_hashtag_media(
        self,
        creator_id: str,
        hashtag_id: str,
        limit: int = 25,
        after: str | None = None,
    ) -> StepResult[tuple[list[InstagramMedia], str | None]]:
        """
        Fetches media for a specific hashtag.
        Requires 'instagram_basic' scope.
        """
        url = f"/{hashtag_id}/recent_media"
        params = {
            "limit": limit,
            "after": after,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data = result.data.get("data", [])
        paging = result.data.get("paging", {})
        next_cursor = paging.get("cursors", {}).get("after") if paging else None

        media_items = []
        for media_data in data:
            try:
                media_items.append(InstagramMedia(**media_data))
            except Exception as e:
                logger.warning(f"Failed to parse Instagram media data: {e} - {media_data}")

        return StepResult.success((media_items, next_cursor))

    async def create_webhook_subscription(
        self,
        creator_id: str,
        callback_url: str,
        fields: list[str],
        verify_token: str,
    ) -> StepResult[InstagramWebhookSubscription]:
        """
        Creates a webhook subscription for Instagram events.
        Requires appropriate permissions.
        """
        url = f"/{self.app_id}/subscriptions"
        payload = {
            "object": "instagram",
            "callback_url": callback_url,
            "fields": ",".join(fields),
            "verify_token": verify_token,
        }

        result = await self._make_api_request("POST", url, creator_id, json=payload)
        if not result.success:
            return result.as_failure()

        try:
            return StepResult.success(InstagramWebhookSubscription(**result.data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse webhook subscription response: {e}")

    async def get_long_lived_token(
        self,
        creator_id: str,
        short_lived_token: str,
    ) -> StepResult[InstagramLongLivedToken]:
        """
        Exchanges a short-lived token for a long-lived token.
        """
        url = "/access_token"
        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.app_secret,
            "access_token": short_lived_token,
        }

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        try:
            return StepResult.success(InstagramLongLivedToken(**result.data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse long-lived token response: {e}")

    async def refresh_long_lived_token(
        self,
        creator_id: str,
        long_lived_token: str,
    ) -> StepResult[InstagramLongLivedToken]:
        """
        Refreshes a long-lived token.
        """
        url = "/refresh_access_token"
        params = {
            "grant_type": "ig_refresh_token",
            "access_token": long_lived_token,
        }

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        try:
            return StepResult.success(InstagramLongLivedToken(**result.data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse refreshed token response: {e}")

    async def verify_webhook(
        self,
        mode: str,
        token: str,
        challenge: str,
    ) -> StepResult[str]:
        """
        Verifies a webhook subscription.
        """
        if mode == "subscribe" and token == self.config.INSTAGRAM_WEBHOOK_VERIFY_TOKEN:
            return StepResult.success(challenge)
        return StepResult.fail("Webhook verification failed")

    async def process_webhook_event(
        self,
        event_data: dict[str, Any],
    ) -> StepResult[InstagramWebhookEvent]:
        """
        Processes a webhook event from Instagram.
        """
        try:
            webhook_event = InstagramWebhookEvent(**event_data)
            return StepResult.success(webhook_event)
        except Exception as e:
            return StepResult.fail(f"Failed to parse webhook event: {e}")

    async def get_rate_limit_info(self, creator_id: str) -> StepResult[dict[str, Any]]:
        """
        Gets rate limit information for the Instagram API.
        """
        # Instagram Graph API doesn't provide explicit rate limit headers
        # This is a placeholder for future implementation
        return StepResult.success(
            {
                "platform": "instagram",
                "rate_limit_type": "app_based",
                "note": "Instagram Graph API uses app-based rate limiting",
            }
        )

    async def close(self):
        """Closes the HTTP client session."""
        if self.client:
            await self.client.aclose()
            logger.info("InstagramClient HTTPX session closed.")
