"""Reddit API integration tool for enhanced Reddit content acquisition."""

from __future__ import annotations
import logging

try:
    import praw

    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    praw = None
from platform.core.step_result import ErrorCategory, StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool

_logger = logging.getLogger(__name__)


class RedditAPITool(BaseTool[StepResult]):
    """Reddit API integration for content retrieval and analysis."""

    name: str = "reddit_api"
    description: str = "Retrieve Reddit content using the official Reddit API. Supports posts, comments, subreddit searches, and user profiles."

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str = "UltimateDiscordIntelligenceBot/1.0",
    ):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.reddit = None
        if PRAW_AVAILABLE and client_id and client_secret:
            self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

    def _run(self, url: str, tenant: str, workspace: str, action: str = "fetch_post", limit: int = 10) -> StepResult:
        """Run Reddit API operation."""
        if not PRAW_AVAILABLE:
            return self._handle_error(
                ImportError("PRAW not available. Install with: pip install praw"),
                context="Reddit API dependency missing",
                error_category=ErrorCategory.DEPENDENCY,
            )
        if not self.reddit:
            return self._handle_error(
                ValueError("Reddit API credentials not configured"),
                context="Missing Reddit API credentials",
                error_category=ErrorCategory.CONFIGURATION,
            )
        try:
            if action == "fetch_post":
                return self._fetch_post(url)
            elif action == "fetch_subreddit":
                return self._fetch_subreddit(url, limit)
            elif action == "search_subreddit":
                return self._search_subreddit(url, limit)
            elif action == "fetch_user":
                return self._fetch_user(url, limit)
            else:
                return self._handle_error(
                    ValueError(f"Unknown action: {action}"),
                    context=f"Unsupported action: {action}",
                    error_category=ErrorCategory.INPUT,
                )
        except Exception as e:
            return self._handle_error(
                e, context=f"Reddit API operation failed: {action}", error_category=ErrorCategory.EXTERNAL_SERVICE
            )

    def _fetch_post(self, url: str) -> StepResult:
        """Fetch a Reddit post by URL."""
        try:
            submission = self.reddit.submission(url=url)
            post_data = {
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext,
                "author": str(submission.author) if submission.author else None,
                "subreddit": str(submission.subreddit),
                "score": submission.score,
                "upvote_ratio": submission.upvote_ratio,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": submission.url,
                "permalink": submission.permalink,
                "is_self": submission.is_self,
                "is_video": submission.is_video,
                "is_gallery": submission.is_gallery,
            }
            return StepResult.ok(data={"post": post_data})
        except Exception as e:
            return self._handle_error(
                e, context="Failed to fetch Reddit post", error_category=ErrorCategory.EXTERNAL_SERVICE
            )

    def _fetch_subreddit(self, subreddit_name: str, limit: int) -> StepResult:
        """Fetch posts from a subreddit."""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            for submission in subreddit.hot(limit=limit):
                posts.append(
                    {
                        "id": submission.id,
                        "title": submission.title,
                        "author": str(submission.author) if submission.author else None,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "url": submission.url,
                        "permalink": submission.permalink,
                    }
                )
            return StepResult.ok(data={"subreddit": subreddit_name, "posts": posts})
        except Exception as e:
            return self._handle_error(
                e, context=f"Failed to fetch subreddit: {subreddit_name}", error_category=ErrorCategory.EXTERNAL_SERVICE
            )

    def _search_subreddit(self, query: str, limit: int) -> StepResult:
        """Search across Reddit."""
        try:
            results = []
            for submission in self.reddit.subreddit("all").search(query, limit=limit):
                results.append(
                    {
                        "id": submission.id,
                        "title": submission.title,
                        "subreddit": str(submission.subreddit),
                        "score": submission.score,
                        "url": submission.url,
                    }
                )
            return StepResult.ok(data={"query": query, "results": results})
        except Exception as e:
            return self._handle_error(
                e, context=f"Failed to search Reddit: {query}", error_category=ErrorCategory.EXTERNAL_SERVICE
            )

    def _fetch_user(self, username: str, limit: int) -> StepResult:
        """Fetch a user's posts."""
        try:
            user = self.reddit.redditor(username)
            posts = []
            for submission in user.submissions.new(limit=limit):
                posts.append(
                    {
                        "id": submission.id,
                        "title": submission.title,
                        "subreddit": str(submission.subreddit),
                        "score": submission.score,
                        "url": submission.url,
                    }
                )
            return StepResult.ok(data={"username": username, "posts": posts})
        except Exception as e:
            return self._handle_error(
                e, context=f"Failed to fetch user: {username}", error_category=ErrorCategory.EXTERNAL_SERVICE
            )
