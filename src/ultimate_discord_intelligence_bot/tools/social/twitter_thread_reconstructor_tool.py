"""Twitter/X thread reconstruction and analysis tool."""

from __future__ import annotations

import time
from typing import TypedDict

from ultimate_discord_intelligence_bot.step_result import StepResult

from .._base import BaseTool


class Tweet(TypedDict, total=False):
    """Individual tweet data structure."""

    tweet_id: str
    author_handle: str
    author_name: str
    content: str
    timestamp: float
    reply_to_tweet_id: str | None
    quote_tweet_id: str | None
    retweet_count: int
    like_count: int
    reply_count: int
    quote_count: int
    hashtags: list[str]
    mentions: list[str]
    urls: list[str]
    media_urls: list[str]
    is_retweet: bool
    is_quote_tweet: bool
    original_author: str | None  # For retweets/quotes


class TwitterThread(TypedDict, total=False):
    """Complete Twitter thread structure."""

    thread_id: str
    root_tweet_id: str
    author_handle: str
    author_name: str
    tweets: list[Tweet]
    total_tweets: int
    total_engagement: int
    thread_topic: str | None
    hashtags: list[str]
    mentions: list[str]
    urls: list[str]
    created_timestamp: float
    last_updated: float
    thread_summary: str | None


class TwitterThreadAnalysis(TypedDict, total=False):
    """Analysis of Twitter thread engagement and propagation."""

    thread_id: str
    engagement_metrics: dict[str, int]
    viral_score: float
    engagement_velocity: float
    peak_engagement_time: float
    audience_reach: int
    sentiment_analysis: dict[str, float]
    topic_classification: list[str]
    influence_impact: float


class TwitterThreadReconstructionResult(TypedDict, total=False):
    """Result of Twitter thread reconstruction."""

    tweet_url: str
    thread_found: bool
    thread_data: TwitterThread | None
    thread_analysis: TwitterThreadAnalysis | None
    quote_tweets: list[Tweet]
    replies: list[Tweet]
    processing_time_seconds: float
    errors: list[str]


class TwitterThreadReconstructorTool(BaseTool[StepResult]):
    """Reconstruct and analyze Twitter/X threads."""

    name: str = "Twitter Thread Reconstructor"
    description: str = (
        "Reconstruct full thread context, extract quote tweets and replies, "
        "analyze engagement patterns, and track viral propagation"
    )

    def __init__(self) -> None:
        super().__init__()
        self._reconstructed_threads: dict[str, TwitterThread] = {}
        self._thread_analyses: dict[str, TwitterThreadAnalysis] = {}

    def _run(self, tweet_url: str, tenant: str, workspace: str) -> StepResult:
        """
        Reconstruct and analyze a Twitter thread.

        Args:
            tweet_url: URL of the tweet to reconstruct thread from
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with thread reconstruction data
        """
        try:
            if not tweet_url:
                return StepResult.fail("Tweet URL is required")

            start_time = time.time()

            # Extract tweet ID from URL
            tweet_id = self._extract_tweet_id(tweet_url)

            if not tweet_id:
                return StepResult.fail("Could not extract tweet ID from URL")

            # Check if already reconstructed
            if tweet_id in self._reconstructed_threads:
                thread_data = self._reconstructed_threads[tweet_id]
                thread_analysis = self._thread_analyses.get(tweet_id)

                result = TwitterThreadReconstructionResult(
                    tweet_url=tweet_url,
                    thread_found=True,
                    thread_data=thread_data,
                    thread_analysis=thread_analysis,
                    quote_tweets=[],
                    replies=[],
                    processing_time_seconds=time.time() - start_time,
                    errors=[],
                )

                return StepResult.ok(data=result)

            # Reconstruct thread
            thread_data = self._reconstruct_thread(tweet_id, tenant, workspace)

            if not thread_data:
                result = TwitterThreadReconstructionResult(
                    tweet_url=tweet_url,
                    thread_found=False,
                    thread_data=None,
                    thread_analysis=None,
                    quote_tweets=[],
                    replies=[],
                    processing_time_seconds=time.time() - start_time,
                    errors=["Could not reconstruct thread"],
                )

                return StepResult.ok(data=result)

            # Analyze thread
            thread_analysis = self._analyze_thread(thread_data, tenant, workspace)

            # Get quote tweets and replies
            quote_tweets = self._get_quote_tweets(tweet_id, tenant, workspace)
            replies = self._get_replies(tweet_id, tenant, workspace)

            # Cache results
            self._reconstructed_threads[tweet_id] = thread_data
            if thread_analysis:
                self._thread_analyses[tweet_id] = thread_analysis

            result = TwitterThreadReconstructionResult(
                tweet_url=tweet_url,
                thread_found=True,
                thread_data=thread_data,
                thread_analysis=thread_analysis,
                quote_tweets=quote_tweets,
                replies=replies,
                processing_time_seconds=time.time() - start_time,
                errors=[],
            )

            return StepResult.ok(data=result)

        except Exception as e:
            return StepResult.fail(f"Twitter thread reconstruction failed: {e!s}")

    def _extract_tweet_id(self, tweet_url: str) -> str | None:
        """Extract tweet ID from Twitter URL."""
        try:
            # Handle various Twitter URL formats
            if "twitter.com" in tweet_url or "x.com" in tweet_url:
                # Extract ID from URL pattern
                parts = tweet_url.split("/")
                if len(parts) >= 6:
                    tweet_id = parts[-1].split("?")[0]  # Remove query parameters
                    return tweet_id
            return None
        except Exception:
            return None

    def _reconstruct_thread(self, tweet_id: str, tenant: str, workspace: str) -> TwitterThread | None:
        """Reconstruct the complete thread from a tweet ID."""
        try:
            # Mock implementation - in real system, would use Twitter API v2
            current_time = time.time()

            # Get root tweet
            root_tweet = self._get_tweet_data(tweet_id, tenant, workspace)

            if not root_tweet:
                return None

            # Find thread tweets (replies in sequence)
            thread_tweets = [root_tweet]
            current_tweet = root_tweet

            # Follow the thread chain
            for _i in range(10):  # Max 10 tweets in thread
                next_tweet = self._get_next_thread_tweet(current_tweet, tenant, workspace)
                if not next_tweet:
                    break

                thread_tweets.append(next_tweet)
                current_tweet = next_tweet

            # Create thread structure
            thread_id = f"thread_{tweet_id}"
            author_handle = root_tweet["author_handle"]
            author_name = root_tweet["author_name"]

            # Calculate total engagement
            total_engagement = sum(
                tweet["retweet_count"] + tweet["like_count"] + tweet["reply_count"] + tweet["quote_count"]
                for tweet in thread_tweets
            )

            # Extract thread metadata
            all_hashtags = []
            all_mentions = []
            all_urls = []

            for tweet in thread_tweets:
                all_hashtags.extend(tweet["hashtags"])
                all_mentions.extend(tweet["mentions"])
                all_urls.extend(tweet["urls"])

            # Remove duplicates
            all_hashtags = list(set(all_hashtags))
            all_mentions = list(set(all_mentions))
            all_urls = list(set(all_urls))

            # Generate thread summary
            thread_summary = self._generate_thread_summary(thread_tweets)

            thread = TwitterThread(
                thread_id=thread_id,
                root_tweet_id=tweet_id,
                author_handle=author_handle,
                author_name=author_name,
                tweets=thread_tweets,
                total_tweets=len(thread_tweets),
                total_engagement=total_engagement,
                thread_topic=self._classify_thread_topic(thread_tweets),
                hashtags=all_hashtags,
                mentions=all_mentions,
                urls=all_urls,
                created_timestamp=root_tweet["timestamp"],
                last_updated=current_time,
                thread_summary=thread_summary,
            )

            return thread

        except Exception as e:
            print(f"Error reconstructing thread for tweet {tweet_id}: {e}")
            return None

    def _get_tweet_data(self, tweet_id: str, tenant: str, workspace: str) -> Tweet | None:
        """Get tweet data from Twitter API."""
        try:
            # Mock implementation - in real system, would use Twitter API v2
            current_time = time.time()

            return Tweet(
                tweet_id=tweet_id,
                author_handle="example_user",
                author_name="Example User",
                content="This is an example tweet with #hashtags and @mentions",
                timestamp=current_time - 3600,  # 1 hour ago
                reply_to_tweet_id=None,
                quote_tweet_id=None,
                retweet_count=100,
                like_count=500,
                reply_count=50,
                quote_count=25,
                hashtags=["#example", "#twitter"],
                mentions=["@friend1", "@friend2"],
                urls=["https://example.com"],
                media_urls=[],
                is_retweet=False,
                is_quote_tweet=False,
                original_author=None,
            )
        except Exception:
            return None

    def _get_next_thread_tweet(self, current_tweet: Tweet, tenant: str, workspace: str) -> Tweet | None:
        """Get the next tweet in the thread sequence."""
        try:
            # Mock implementation - in real system, would find replies that continue the thread
            time.time()

            # Simulate finding a thread continuation
            if current_tweet["tweet_id"].endswith("_1"):
                return Tweet(
                    tweet_id=f"{current_tweet['tweet_id']}_2",
                    author_handle=current_tweet["author_handle"],
                    author_name=current_tweet["author_name"],
                    content="This is the continuation of the thread...",
                    timestamp=current_tweet["timestamp"] + 60,  # 1 minute later
                    reply_to_tweet_id=current_tweet["tweet_id"],
                    quote_tweet_id=None,
                    retweet_count=50,
                    like_count=200,
                    reply_count=20,
                    quote_count=10,
                    hashtags=current_tweet["hashtags"],
                    mentions=current_tweet["mentions"],
                    urls=[],
                    media_urls=[],
                    is_retweet=False,
                    is_quote_tweet=False,
                    original_author=None,
                )

            return None

        except Exception:
            return None

    def _generate_thread_summary(self, tweets: list[Tweet]) -> str:
        """Generate a summary of the thread content."""
        try:
            # Mock implementation - in real system, would use LLM to summarize
            total_content = " ".join(tweet["content"] for tweet in tweets)

            # Simple summary (in real system, would use more sophisticated summarization)
            summary = total_content[:200] + "..." if len(total_content) > 200 else total_content

            return summary

        except Exception:
            return "Thread summary unavailable"

    def _classify_thread_topic(self, tweets: list[Tweet]) -> str | None:
        """Classify the main topic of the thread."""
        try:
            # Mock implementation - in real system, would use topic classification
            all_hashtags = []
            for tweet in tweets:
                all_hashtags.extend(tweet["hashtags"])

            if not all_hashtags:
                return "General Discussion"

            # Return most common hashtag as topic
            from collections import Counter

            hashtag_counts = Counter(all_hashtags)
            return hashtag_counts.most_common(1)[0][0] if hashtag_counts else None

        except Exception:
            return None

    def _analyze_thread(self, thread: TwitterThread, tenant: str, workspace: str) -> TwitterThreadAnalysis | None:
        """Analyze thread engagement and viral potential."""
        try:
            # Calculate engagement metrics
            total_retweets = sum(tweet["retweet_count"] for tweet in thread["tweets"])
            total_likes = sum(tweet["like_count"] for tweet in thread["tweets"])
            total_replies = sum(tweet["reply_count"] for tweet in thread["tweets"])
            total_quotes = sum(tweet["quote_count"] for tweet in thread["tweets"])

            engagement_metrics = {
                "total_retweets": total_retweets,
                "total_likes": total_likes,
                "total_replies": total_replies,
                "total_quotes": total_quotes,
                "total_engagement": total_retweets + total_likes + total_replies + total_quotes,
            }

            # Calculate viral score (0-1)
            viral_score = min(engagement_metrics["total_engagement"] / 10000, 1.0)

            # Calculate engagement velocity (engagement per hour)
            time_span_hours = (time.time() - thread["created_timestamp"]) / 3600
            engagement_velocity = engagement_metrics["total_engagement"] / max(time_span_hours, 1)

            # Mock sentiment analysis
            sentiment_analysis = {"positive": 0.6, "neutral": 0.3, "negative": 0.1}

            # Mock topic classification
            topic_classification = ["Technology", "Social Media", "Discussion"]

            # Calculate influence impact
            influence_impact = min(viral_score * engagement_velocity / 100, 1.0)

            return TwitterThreadAnalysis(
                thread_id=thread["thread_id"],
                engagement_metrics=engagement_metrics,
                viral_score=viral_score,
                engagement_velocity=engagement_velocity,
                peak_engagement_time=thread["created_timestamp"] + 3600,  # Mock peak time
                audience_reach=engagement_metrics["total_engagement"] * 10,  # Mock reach calculation
                sentiment_analysis=sentiment_analysis,
                topic_classification=topic_classification,
                influence_impact=influence_impact,
            )

        except Exception as e:
            print(f"Error analyzing thread {thread['thread_id']}: {e}")
            return None

    def _get_quote_tweets(self, tweet_id: str, tenant: str, workspace: str) -> list[Tweet]:
        """Get quote tweets of the original tweet."""
        try:
            # Mock implementation - in real system, would use Twitter API
            quote_tweets: list[Tweet] = []
            current_time = time.time()

            # Generate mock quote tweets
            for i in range(3):  # Mock 3 quote tweets
                quote_tweet = Tweet(
                    tweet_id=f"quote_{tweet_id}_{i}",
                    author_handle=f"quote_user_{i}",
                    author_name=f"Quote User {i}",
                    content=f"This is a quote tweet {i} with additional commentary",
                    timestamp=current_time - (i * 1800),  # Each 30 minutes earlier
                    reply_to_tweet_id=None,
                    quote_tweet_id=tweet_id,
                    retweet_count=10 + i,
                    like_count=50 + (i * 10),
                    reply_count=5 + i,
                    quote_count=2 + i,
                    hashtags=["#quote", "#discussion"],
                    mentions=[],
                    urls=[],
                    media_urls=[],
                    is_retweet=False,
                    is_quote_tweet=True,
                    original_author="example_user",
                )
                quote_tweets.append(quote_tweet)

            return quote_tweets

        except Exception:
            return []

    def _get_replies(self, tweet_id: str, tenant: str, workspace: str) -> list[Tweet]:
        """Get replies to the original tweet."""
        try:
            # Mock implementation - in real system, would use Twitter API
            replies: list[Tweet] = []
            current_time = time.time()

            # Generate mock replies
            for i in range(5):  # Mock 5 replies
                reply = Tweet(
                    tweet_id=f"reply_{tweet_id}_{i}",
                    author_handle=f"reply_user_{i}",
                    author_name=f"Reply User {i}",
                    content=f"This is a reply {i} to the original tweet",
                    timestamp=current_time - (i * 900),  # Each 15 minutes earlier
                    reply_to_tweet_id=tweet_id,
                    quote_tweet_id=None,
                    retweet_count=2 + i,
                    like_count=10 + (i * 5),
                    reply_count=1 + i,
                    quote_count=0,
                    hashtags=[],
                    mentions=["example_user"],
                    urls=[],
                    media_urls=[],
                    is_retweet=False,
                    is_quote_tweet=False,
                    original_author=None,
                )
                replies.append(reply)

            return replies

        except Exception:
            return []

    def get_reconstructed_thread(self, tweet_id: str) -> TwitterThread | None:
        """Get a previously reconstructed thread."""
        return self._reconstructed_threads.get(tweet_id)

    def get_thread_analysis(self, tweet_id: str) -> TwitterThreadAnalysis | None:
        """Get analysis for a previously analyzed thread."""
        return self._thread_analyses.get(tweet_id)

    def get_reconstructed_count(self) -> int:
        """Get the total number of reconstructed threads."""
        return len(self._reconstructed_threads)
