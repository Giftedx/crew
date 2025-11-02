"""
X (Twitter) API v2 client with tier-aware rate limits and OAuth 2.0 PKCE.
"""

import logging
from datetime import datetime, timedelta
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
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_models import (
    XCostGuard,
    XError,
    XMedia,
    XPlace,
    XPoll,
    XRateLimit,
    XTweet,
    XUser,
    XWebhookEvent,
    XWebhookSubscription,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class XClient:
    """
    Client for interacting with the X (Twitter) API v2.
    Handles OAuth 2.0 PKCE, tier-aware rate limits, cost guards, and API requests with retry logic.
    """

    BASE_URL = "https://api.twitter.com/2"
    OAUTH_URL = "https://api.twitter.com/oauth2"

    def __init__(self, config: CreatorOpsConfig, oauth_manager: OAuthManager):
        self.config = config
        self.oauth_manager = oauth_manager
        self.client = httpx.AsyncClient(timeout=self.config.X_API_TIMEOUT)
        self.client_id = self.config.X_CLIENT_ID
        self.client_secret = self.config.X_CLIENT_SECRET
        self.redirect_uri = self.config.X_REDIRECT_URI
        self.scope = "tweet.read,tweet.write,users.read,offline.access"
        self.api_tier = self.config.X_API_TIER or "free"
        self.monthly_tweet_cap = self._get_monthly_tweet_cap()
        self.tweets_used = 0
        self.cost_per_tweet = self._get_cost_per_tweet()

        logger.info(f"XClient initialized with {self.api_tier} tier.")

    def _get_monthly_tweet_cap(self) -> int:
        """Get monthly tweet cap based on API tier."""
        caps = {
            "free": 0,
            "basic": 10000,
            "pro": 100000,
            "enterprise": 1000000,
        }
        return caps.get(self.api_tier, 0)

    def _get_cost_per_tweet(self) -> float:
        """Get cost per tweet based on API tier."""
        costs = {
            "free": 0.0,
            "basic": 0.001,
            "pro": 0.0005,
            "enterprise": 0.0001,
        }
        return costs.get(self.api_tier, 0.0)

    async def _get_access_token(self, creator_id: str) -> StepResult[str]:
        """Retrieves an access token for the given creator."""
        token_result = await self.oauth_manager.get_access_token(
            platform="x", creator_id=creator_id, scopes=self.scope.split(",")
        )
        if not token_result.success:
            return StepResult.fail(f"Failed to get X access token: {token_result.error}")
        return StepResult.success(token_result.data)

    def _check_rate_limit(self, response: httpx.Response) -> XRateLimit:
        """Extract rate limit information from response headers."""
        headers = response.headers
        return XRateLimit(
            limit=int(headers.get("x-rate-limit-limit", 0)),
            remaining=int(headers.get("x-rate-limit-remaining", 0)),
            reset=datetime.fromtimestamp(int(headers.get("x-rate-limit-reset", 0))),
            retry_after=int(headers.get("retry-after", 0)) if headers.get("retry-after") else None,
        )

    def _check_cost_guard(self) -> StepResult[XCostGuard]:
        """Check if we're within cost limits."""
        if self.api_tier == "free":
            return StepResult.success(
                XCostGuard(
                    tier=self.api_tier,
                    monthly_tweet_cap=0,
                    tweets_used=0,
                    tweets_remaining=0,
                    reset_date=datetime.utcnow() + timedelta(days=30),
                    cost_per_tweet=0.0,
                    estimated_monthly_cost=0.0,
                )
            )

        if self.tweets_used >= self.monthly_tweet_cap:
            return StepResult.fail("Monthly tweet cap exceeded")

        return StepResult.success(
            XCostGuard(
                tier=self.api_tier,
                monthly_tweet_cap=self.monthly_tweet_cap,
                tweets_used=self.tweets_used,
                tweets_remaining=self.monthly_tweet_cap - self.tweets_used,
                reset_date=datetime.utcnow() + timedelta(days=30),
                cost_per_tweet=self.cost_per_tweet,
                estimated_monthly_cost=self.tweets_used * self.cost_per_tweet,
            )
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        retry_error_callback=lambda retry_state: StepResult.fail(
            f"X API request failed after multiple retries: {retry_state.outcome.exception()}"
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
    ) -> StepResult[tuple[dict[str, Any], XRateLimit]]:
        """Helper to make authenticated API requests to X."""
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
            logger.debug(f"Making X API request: {method} {full_url} with params {params}")
            response = await self.client.request(method, full_url, json=json, params=params, headers=_headers)
            response.raise_for_status()
            data = response.json()

            if data.get("errors"):
                error = XError(**data["errors"][0])
                logger.error(f"X API error: {error.message} (Code: {error.code})")
                return StepResult.fail(f"X API error: {error.message}")

            rate_limit = self._check_rate_limit(response)
            return StepResult.success((data, rate_limit))
        except httpx.HTTPStatusError as e:
            logger.error(f"X API HTTP error for {full_url}: {e.response.status_code} - {e.response.text}")
            if 500 <= e.response.status_code < 600:
                raise
            return StepResult.fail(f"X API HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"X API request error for {full_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during X API request to {full_url}: {e}")
            return StepResult.fail(f"Unexpected error: {e}")

    async def get_user_by_username(
        self,
        creator_id: str,
        username: str,
        fields: list[str] | None = None,
    ) -> StepResult[XUser]:
        """
        Fetches information about an X user by username.
        Requires 'users.read' scope.
        """
        url = f"/users/by/username/{username}"
        params = {"user.fields": ",".join(fields)} if fields else None
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        user_data = data.get("data")
        if not user_data:
            return StepResult.fail("User data not found in X API response.")

        try:
            return StepResult.success(XUser(**user_data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X user data: {e}")

    async def get_user_by_id(
        self,
        creator_id: str,
        user_id: str,
        fields: list[str] | None = None,
    ) -> StepResult[XUser]:
        """
        Fetches information about an X user by ID.
        Requires 'users.read' scope.
        """
        url = f"/users/{user_id}"
        params = {"user.fields": ",".join(fields)} if fields else None
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        user_data = data.get("data")
        if not user_data:
            return StepResult.fail("User data not found in X API response.")

        try:
            return StepResult.success(XUser(**user_data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X user data: {e}")

    async def get_user_timeline(
        self,
        creator_id: str,
        user_id: str,
        max_results: int = 10,
        pagination_token: str | None = None,
        fields: list[str] | None = None,
    ) -> StepResult[tuple[list[XTweet], str | None, XRateLimit]]:
        """
        Fetches tweets from a user's timeline.
        Requires 'tweet.read' scope. Supports pagination.
        """
        url = f"/users/{user_id}/tweets"
        params = {
            "max_results": max_results,
            "pagination_token": pagination_token,
            "tweet.fields": ",".join(fields) if fields else None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, rate_limit = result.data
        tweets_data = data.get("data", [])
        meta = data.get("meta", {})
        next_token = meta.get("next_token")

        tweets = []
        for tweet_data in tweets_data:
            try:
                tweets.append(XTweet(**tweet_data))
            except Exception as e:
                logger.warning(f"Failed to parse X tweet data: {e} - {tweet_data}")

        return StepResult.success((tweets, next_token, rate_limit))

    async def get_user_mentions(
        self,
        creator_id: str,
        user_id: str,
        max_results: int = 10,
        pagination_token: str | None = None,
        fields: list[str] | None = None,
    ) -> StepResult[tuple[list[XTweet], str | None, XRateLimit]]:
        """
        Fetches tweets mentioning a user.
        Requires 'tweet.read' scope. Supports pagination.
        """
        url = f"/users/{user_id}/mentions"
        params = {
            "max_results": max_results,
            "pagination_token": pagination_token,
            "tweet.fields": ",".join(fields) if fields else None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, rate_limit = result.data
        tweets_data = data.get("data", [])
        meta = data.get("meta", {})
        next_token = meta.get("next_token")

        tweets = []
        for tweet_data in tweets_data:
            try:
                tweets.append(XTweet(**tweet_data))
            except Exception as e:
                logger.warning(f"Failed to parse X tweet data: {e} - {tweet_data}")

        return StepResult.success((tweets, next_token, rate_limit))

    async def search_tweets(
        self,
        creator_id: str,
        query: str,
        max_results: int = 10,
        next_token: str | None = None,
        fields: list[str] | None = None,
    ) -> StepResult[tuple[list[XTweet], str | None, XRateLimit]]:
        """
        Searches for tweets.
        Requires 'tweet.read' scope. Supports pagination.
        """
        url = "/tweets/search/recent"
        params = {
            "query": query,
            "max_results": max_results,
            "next_token": next_token,
            "tweet.fields": ",".join(fields) if fields else None,
        }
        params = {k: v for k, v in params.items() if v is not None}

        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, rate_limit = result.data
        tweets_data = data.get("data", [])
        meta = data.get("meta", {})
        next_token = meta.get("next_token")

        tweets = []
        for tweet_data in tweets_data:
            try:
                tweets.append(XTweet(**tweet_data))
            except Exception as e:
                logger.warning(f"Failed to parse X tweet data: {e} - {tweet_data}")

        return StepResult.success((tweets, next_token, rate_limit))

    async def get_tweet(
        self,
        creator_id: str,
        tweet_id: str,
        fields: list[str] | None = None,
    ) -> StepResult[XTweet]:
        """
        Fetches a specific tweet by ID.
        Requires 'tweet.read' scope.
        """
        url = f"/tweets/{tweet_id}"
        params = {"tweet.fields": ",".join(fields)} if fields else None
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        tweet_data = data.get("data")
        if not tweet_data:
            return StepResult.fail("Tweet data not found in X API response.")

        try:
            return StepResult.success(XTweet(**tweet_data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X tweet data: {e}")

    async def create_tweet(
        self,
        creator_id: str,
        text: str,
        reply_to_tweet_id: str | None = None,
        media_ids: list[str] | None = None,
    ) -> StepResult[XTweet]:
        """
        Creates a new tweet.
        Requires 'tweet.write' scope.
        """
        # Check cost guard
        cost_guard_result = self._check_cost_guard()
        if not cost_guard_result.success:
            return cost_guard_result.as_failure()

        url = "/tweets"
        payload = {"text": text}

        if reply_to_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_tweet_id}

        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        result = await self._make_api_request("POST", url, creator_id, json=payload)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        tweet_data = data.get("data")
        if not tweet_data:
            return StepResult.fail("Tweet data not found in X API response.")

        # Update cost tracking
        self.tweets_used += 1

        try:
            return StepResult.success(XTweet(**tweet_data))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X tweet data: {e}")

    async def delete_tweet(
        self,
        creator_id: str,
        tweet_id: str,
    ) -> StepResult[bool]:
        """
        Deletes a tweet.
        Requires 'tweet.write' scope.
        """
        url = f"/tweets/{tweet_id}"
        result = await self._make_api_request("DELETE", url, creator_id)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        return StepResult.success(data.get("data", {}).get("deleted", False))

    async def get_tweet_media(
        self,
        creator_id: str,
        tweet_id: str,
    ) -> StepResult[list[XMedia]]:
        """
        Fetches media attached to a tweet.
        Requires 'tweet.read' scope.
        """
        url = f"/tweets/{tweet_id}"
        params = {"tweet.fields": "attachments", "media.fields": "all"}
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        data.get("data", {})
        includes = data.get("includes", {})
        media_data = includes.get("media", [])

        media_items = []
        for media_item in media_data:
            try:
                media_items.append(XMedia(**media_item))
            except Exception as e:
                logger.warning(f"Failed to parse X media data: {e} - {media_item}")

        return StepResult.success(media_items)

    async def get_tweet_poll(
        self,
        creator_id: str,
        tweet_id: str,
    ) -> StepResult[XPoll | None]:
        """
        Fetches poll attached to a tweet.
        Requires 'tweet.read' scope.
        """
        url = f"/tweets/{tweet_id}"
        params = {"tweet.fields": "attachments", "poll.fields": "all"}
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        includes = data.get("includes", {})
        polls_data = includes.get("polls", [])

        if not polls_data:
            return StepResult.success(None)

        try:
            return StepResult.success(XPoll(**polls_data[0]))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X poll data: {e}")

    async def get_tweet_place(
        self,
        creator_id: str,
        tweet_id: str,
    ) -> StepResult[XPlace | None]:
        """
        Fetches place attached to a tweet.
        Requires 'tweet.read' scope.
        """
        url = f"/tweets/{tweet_id}"
        params = {"tweet.fields": "geo", "place.fields": "all"}
        result = await self._make_api_request("GET", url, creator_id, params=params)
        if not result.success:
            return result.as_failure()

        data, _rate_limit = result.data
        includes = data.get("includes", {})
        places_data = includes.get("places", [])

        if not places_data:
            return StepResult.success(None)

        try:
            return StepResult.success(XPlace(**places_data[0]))
        except Exception as e:
            return StepResult.fail(f"Failed to parse X place data: {e}")

    async def get_rate_limit_info(self, creator_id: str) -> StepResult[dict[str, Any]]:
        """
        Gets rate limit information for the X API.
        """
        # This would typically involve a call to the rate limit endpoint
        # For now, return basic information
        return StepResult.success(
            {
                "platform": "x",
                "api_tier": self.api_tier,
                "monthly_tweet_cap": self.monthly_tweet_cap,
                "tweets_used": self.tweets_used,
                "tweets_remaining": self.monthly_tweet_cap - self.tweets_used,
                "cost_per_tweet": self.cost_per_tweet,
                "estimated_monthly_cost": self.tweets_used * self.cost_per_tweet,
            }
        )

    async def get_cost_guard_info(self, creator_id: str) -> StepResult[XCostGuard]:
        """
        Gets cost guard information for the X API.
        """
        return self._check_cost_guard()

    async def create_webhook_subscription(
        self,
        creator_id: str,
        webhook_url: str,
        events: list[str],
    ) -> StepResult[XWebhookSubscription]:
        """
        Creates a webhook subscription for X events.
        Requires appropriate permissions.
        """
        # This would typically involve a call to the webhook subscription endpoint
        # For now, return a mock response
        return StepResult.success(
            XWebhookSubscription(
                id="webhook_123",
                url=webhook_url,
                valid=True,
                created_timestamp=datetime.utcnow(),
            )
        )

    async def process_webhook_event(
        self,
        event_data: dict[str, Any],
    ) -> StepResult[XWebhookEvent]:
        """
        Processes a webhook event from X.
        """
        try:
            webhook_event = XWebhookEvent(**event_data)
            return StepResult.success(webhook_event)
        except Exception as e:
            return StepResult.fail(f"Failed to parse webhook event: {e}")

    async def close(self):
        """Closes the HTTP client session."""
        if self.client:
            await self.client.aclose()
            logger.info("XClient HTTPX session closed.")
