"""Twitter/X API integration tool for enhanced Twitter content acquisition."""

from __future__ import annotations

import logging


try:
    import tweepy

    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    tweepy = None  # type: ignore[assignment,misc]

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


_logger = logging.getLogger(__name__)


class TwitterAPITool(BaseTool[StepResult]):
    """Twitter/X API integration for content retrieval and analysis."""

    name: str = "twitter_api"
    description: str = (
        "Retrieve Twitter/X content using the official API. Supports tweets, user profiles, trends, and search."
    )

    def __init__(
        self,
        bearer_token: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        access_token: str | None = None,
        access_token_secret: str | None = None,
    ):
        super().__init__()
        self.bearer_token = bearer_token
        self.api = None

        if TWEEPY_AVAILABLE and bearer_token:
            # Use OAuth 2.0 Bearer Token for read-only access
            self.api = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True,
            )

    def _run(
        self,
        query: str,
        tenant: str,
        workspace: str,
        action: str = "search_tweets",
        max_results: int = 10,
    ) -> StepResult:
        """Run Twitter API operation."""
        if not TWEEPY_AVAILABLE:
            return self._handle_error(
                ImportError("Tweepy not available. Install with: pip install tweepy"),
                context="Twitter API dependency missing",
                error_category=ErrorCategory.DEPENDENCY,
            )

        if not self.api:
            return self._handle_error(
                ValueError("Twitter API credentials not configured"),
                context="Missing Twitter API credentials",
                error_category=ErrorCategory.CONFIGURATION,
            )

        try:
            if action == "search_tweets":
                return self._search_tweets(query, max_results)
            elif action == "get_tweet":
                return self._get_tweet(query)
            elif action == "get_user":
                return self._get_user(query)
            elif action == "get_trends":
                return self._get_trends(query)
            else:
                return self._handle_error(
                    ValueError(f"Unknown action: {action}"),
                    context=f"Unsupported action: {action}",
                    error_category=ErrorCategory.INPUT,
                )
        except Exception as e:
            return self._handle_error(
                e,
                context=f"Twitter API operation failed: {action}",
                error_category=ErrorCategory.EXTERNAL_SERVICE,
            )

    def _search_tweets(self, query: str, max_results: int) -> StepResult:
        """Search for tweets."""
        try:
            tweets = self.api.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=["created_at", "author_id", "public_metrics"],
            )

            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append(
                        {
                            "id": tweet.id,
                            "text": tweet.text,
                            "created_at": str(tweet.created_at) if tweet.created_at else None,
                            "author_id": tweet.author_id,
                            "metrics": {
                                "retweet_count": tweet.public_metrics.get("retweet_count", 0),
                                "like_count": tweet.public_metrics.get("like_count", 0),
                                "reply_count": tweet.public_metrics.get("reply_count", 0),
                            }
                            if tweet.public_metrics
                            else {},
                        }
                    )

            return StepResult.ok(data={"query": query, "results": results})

        except Exception as e:
            return self._handle_error(
                e,
                context=f"Failed to search tweets: {query}",
                error_category=ErrorCategory.EXTERNAL_SERVICE,
            )

    def _get_tweet(self, tweet_id: str) -> StepResult:
        """Get a specific tweet by ID."""
        try:
            tweet = self.api.get_tweet(
                id=tweet_id,
                tweet_fields=["created_at", "author_id", "public_metrics"],
            )

            if not tweet.data:
                return self._handle_error(
                    ValueError(f"Tweet not found: {tweet_id}"),
                    context="Tweet not found",
                    error_category=ErrorCategory.INPUT,
                )

            tweet_data = {
                "id": tweet.data.id,
                "text": tweet.data.text,
                "created_at": str(tweet.data.created_at) if tweet.data.created_at else None,
                "author_id": tweet.data.author_id,
                "metrics": {
                    "retweet_count": tweet.data.public_metrics.get("retweet_count", 0),
                    "like_count": tweet.data.public_metrics.get("like_count", 0),
                    "reply_count": tweet.data.public_metrics.get("reply_count", 0),
                }
                if tweet.data.public_metrics
                else {},
            }

            return StepResult.ok(data={"tweet": tweet_data})

        except Exception as e:
            return self._handle_error(
                e,
                context=f"Failed to get tweet: {tweet_id}",
                error_category=ErrorCategory.EXTERNAL_SERVICE,
            )

    def _get_user(self, username: str) -> StepResult:
        """Get a user's profile."""
        try:
            user = self.api.get_user(username=username)

            if not user.data:
                return self._handle_error(
                    ValueError(f"User not found: {username}"),
                    context="User not found",
                    error_category=ErrorCategory.INPUT,
                )

            user_data = {
                "id": user.data.id,
                "username": user.data.username,
                "name": user.data.name,
                "description": user.data.description,
                "followers_count": user.data.public_metrics.get("followers_count", 0)
                if user.data.public_metrics
                else 0,
                "following_count": user.data.public_metrics.get("following_count", 0)
                if user.data.public_metrics
                else 0,
                "tweet_count": user.data.public_metrics.get("tweet_count", 0) if user.data.public_metrics else 0,
            }

            return StepResult.ok(data={"user": user_data})

        except Exception as e:
            return self._handle_error(
                e,
                context=f"Failed to get user: {username}",
                error_category=ErrorCategory.EXTERNAL_SERVICE,
            )

    def _get_trends(self, woeid: str) -> StepResult:
        """Get trending topics."""
        try:
            # Note: Twitter API v2 doesn't have trends endpoint
            # This is a placeholder for future implementation
            return self._handle_error(
                NotImplementedError("Trends endpoint not available in API v2"),
                context="Trends endpoint not implemented",
                error_category=ErrorCategory.FEATURE,
            )

        except Exception as e:
            return self._handle_error(
                e,
                context="Failed to get trends",
                error_category=ErrorCategory.EXTERNAL_SERVICE,
            )
