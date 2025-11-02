"""X (Twitter) API v2 integration client."""

from __future__ import annotations

import logging
from platform.core.step_result import StepResult
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class XClient:
    """X (Twitter) API v2 client for creator operations."""

    def __init__(self, bearer_token: str, api_key: str | None = None, api_secret: str | None = None):
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.twitter.com/2"
        self.headers = {"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None, method: str = "GET") -> StepResult:
        """Make authenticated request to X API."""
        try:
            params = params or {}
            url = f"{self.base_url}/{endpoint}"

            async def _request():
                async with httpx.AsyncClient() as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=self.headers, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=self.headers, json=params)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    response.raise_for_status()
                    return response.json()

            import asyncio

            data = asyncio.run(_request())
            return StepResult.ok(data=data)
        except httpx.HTTPError as e:
            logger.error(f"X API request failed: {e}")
            return StepResult.fail(f"X API request failed: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error in X API request: {e}")
            return StepResult.fail(f"Unexpected error: {e!s}")

    def get_user_by_username(self, username: str, user_fields: list[str] | None = None) -> StepResult:
        """Get user by username."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified", "description"]
        params = {"usernames": username, "user.fields": ",".join(user_fields)}
        return self._make_request("users/by/username/usernames", params)

    def get_user_by_id(self, user_id: str, user_fields: list[str] | None = None) -> StepResult:
        """Get user by ID."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified", "description"]
        params = {"user.fields": ",".join(user_fields)}
        return self._make_request(f"users/{user_id}", params)

    def get_user_tweets(self, user_id: str, max_results: int = 10, tweet_fields: list[str] | None = None) -> StepResult:
        """Get user's tweets."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations"]
        params = {"max_results": min(max_results, 100), "tweet.fields": ",".join(tweet_fields)}
        return self._make_request(f"users/{user_id}/tweets", params)

    def get_tweet(self, tweet_id: str, tweet_fields: list[str] | None = None) -> StepResult:
        """Get tweet by ID."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations", "author_id"]
        params = {"tweet.fields": ",".join(tweet_fields)}
        return self._make_request(f"tweets/{tweet_id}", params)

    def search_tweets(self, query: str, max_results: int = 10, tweet_fields: list[str] | None = None) -> StepResult:
        """Search tweets."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations", "author_id"]
        params = {"query": query, "max_results": min(max_results, 100), "tweet.fields": ",".join(tweet_fields)}
        return self._make_request("tweets/search/recent", params)

    def get_tweet_mentions(
        self, user_id: str, max_results: int = 10, tweet_fields: list[str] | None = None
    ) -> StepResult:
        """Get tweets mentioning a user."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations", "author_id"]
        params = {"max_results": min(max_results, 100), "tweet.fields": ",".join(tweet_fields)}
        return self._make_request(f"users/{user_id}/mentions", params)

    def get_tweet_replies(
        self, tweet_id: str, max_results: int = 10, tweet_fields: list[str] | None = None
    ) -> StepResult:
        """Get replies to a tweet."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations", "author_id"]
        params = {"max_results": min(max_results, 100), "tweet.fields": ",".join(tweet_fields)}
        return self._make_request(f"tweets/{tweet_id}/replies", params)

    def get_user_followers(
        self, user_id: str, max_results: int = 10, user_fields: list[str] | None = None
    ) -> StepResult:
        """Get user's followers."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified"]
        params = {"max_results": min(max_results, 100), "user.fields": ",".join(user_fields)}
        return self._make_request(f"users/{user_id}/followers", params)

    def get_user_following(
        self, user_id: str, max_results: int = 10, user_fields: list[str] | None = None
    ) -> StepResult:
        """Get users that a user is following."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified"]
        params = {"max_results": min(max_results, 100), "user.fields": ",".join(user_fields)}
        return self._make_request(f"users/{user_id}/following", params)

    def get_trending_topics(self, woeid: int = 1) -> StepResult:
        """Get trending topics (requires Twitter API v1.1)."""
        return StepResult.fail("Trending topics require Twitter API v1.1")

    def get_tweet_likes(self, tweet_id: str, max_results: int = 10, user_fields: list[str] | None = None) -> StepResult:
        """Get users who liked a tweet."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified"]
        params = {"max_results": min(max_results, 100), "user.fields": ",".join(user_fields)}
        return self._make_request(f"tweets/{tweet_id}/liking_users", params)

    def get_tweet_retweets(
        self, tweet_id: str, max_results: int = 10, user_fields: list[str] | None = None
    ) -> StepResult:
        """Get users who retweeted a tweet."""
        if not user_fields:
            user_fields = ["id", "name", "username", "public_metrics", "verified"]
        params = {"max_results": min(max_results, 100), "user.fields": ",".join(user_fields)}
        return self._make_request(f"tweets/{tweet_id}/retweeted_by", params)

    def get_tweet_quotes(
        self, tweet_id: str, max_results: int = 10, tweet_fields: list[str] | None = None
    ) -> StepResult:
        """Get quotes of a tweet."""
        if not tweet_fields:
            tweet_fields = ["id", "text", "created_at", "public_metrics", "context_annotations", "author_id"]
        params = {"max_results": min(max_results, 100), "tweet.fields": ",".join(tweet_fields)}
        return self._make_request(f"tweets/{tweet_id}/quote_tweets", params)

    def get_spaces(self, space_ids: list[str], space_fields: list[str] | None = None) -> StepResult:
        """Get spaces information."""
        if not space_fields:
            space_fields = ["id", "title", "state", "created_at", "host_ids", "participant_count"]
        params = {"ids": ",".join(space_ids), "space.fields": ",".join(space_fields)}
        return self._make_request("spaces", params)

    def get_user_spaces(self, user_id: str, space_fields: list[str] | None = None) -> StepResult:
        """Get spaces created by a user."""
        if not space_fields:
            space_fields = ["id", "title", "state", "created_at", "host_ids", "participant_count"]
        params = {"space.fields": ",".join(space_fields)}
        return self._make_request(f"users/{user_id}/spaces", params)

    def get_lists(self, list_ids: list[str], list_fields: list[str] | None = None) -> StepResult:
        """Get lists information."""
        if not list_fields:
            list_fields = ["id", "name", "description", "follower_count", "member_count"]
        params = {"ids": ",".join(list_ids), "list.fields": ",".join(list_fields)}
        return self._make_request("lists", params)

    def get_user_lists(self, user_id: str, list_fields: list[str] | None = None) -> StepResult:
        """Get lists owned by a user."""
        if not list_fields:
            list_fields = ["id", "name", "description", "follower_count", "member_count"]
        params = {"list.fields": ",".join(list_fields)}
        return self._make_request(f"users/{user_id}/owned_lists", params)

    def extract_user_id_from_url(self, url: str) -> str | None:
        """Extract user ID from X URL."""
        import re

        patterns = ["twitter\\.com/([^/?]+)", "x\\.com/([^/?]+)"]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_tweet_id_from_url(self, url: str) -> str | None:
        """Extract tweet ID from X URL."""
        import re

        patterns = ["twitter\\.com/[^/]+/status/(\\d+)", "x\\.com/[^/]+/status/(\\d+)"]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def health_check(self) -> StepResult:
        """Perform health check on X client."""
        try:
            result = self.get_user_by_username("twitter")
            if result.success:
                return StepResult.ok(
                    data={
                        "service": "x_twitter",
                        "status": "healthy",
                        "bearer_token_configured": bool(self.bearer_token),
                        "api_key_configured": bool(self.api_key),
                    }
                )
            else:
                return StepResult.fail("X API health check failed")
        except Exception as e:
            logger.error(f"X client health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e!s}")
