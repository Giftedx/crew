"""Tests for Reddit API tool."""

import importlib.util
from unittest.mock import Mock, patch

import pytest


PRAW_AVAILABLE = importlib.util.find_spec("praw") is not None


class TestRedditAPITool:
    """Test cases for Reddit API tool."""

    @pytest.fixture
    def tool(self):
        """Create RedditAPITool instance."""
        from src.ultimate_discord_intelligence_bot.tools.acquisition.reddit_api_tool import RedditAPITool

        return RedditAPITool(client_id="test_id", client_secret="test_secret", user_agent="test")

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == "reddit_api"

    @pytest.mark.skipif(not PRAW_AVAILABLE, reason="PRAW not available")
    def test_fetch_post(self, tool):
        """Test fetching a Reddit post."""
        # Mock Reddit submission
        mock_submission = Mock()
        mock_submission.id = "test_id"
        mock_submission.title = "Test Post"
        mock_submission.selftext = "Test content"
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value="test_user")
        mock_submission.subreddit.__str__ = Mock(return_value="test_subreddit")
        mock_submission.score = 100
        mock_submission.upvote_ratio = 0.95
        mock_submission.num_comments = 50
        mock_submission.created_utc = 1640995200
        mock_submission.url = "https://example.com"
        mock_submission.permalink = "/r/test/comments/test"
        mock_submission.is_self = True
        mock_submission.is_video = False
        mock_submission.is_gallery = False

        with patch.object(tool.reddit, "submission", return_value=mock_submission):
            result = tool._run(
                url="https://reddit.com/r/test/comments/test", tenant="test", workspace="test", action="fetch_post"
            )

            assert result.success
            assert result.data["post"]["title"] == "Test Post"

    @pytest.mark.skipif(not PRAW_AVAILABLE, reason="PRAW not available")
    def test_fetch_subreddit(self, tool):
        """Test fetching posts from a subreddit."""
        # Mock subreddit
        mock_submission = Mock()
        mock_submission.id = "test_id"
        mock_submission.title = "Test Post"
        mock_submission.author = Mock()
        mock_submission.author.__str__ = Mock(return_value="test_user")
        mock_submission.score = 50
        mock_submission.num_comments = 10
        mock_submission.url = "https://example.com"
        mock_submission.permalink = "/r/test/comments/test"

        mock_subreddit = Mock()
        mock_subreddit.hot.return_value = [mock_submission]

        with patch.object(tool.reddit, "subreddit", return_value=mock_subreddit):
            result = tool._run(url="programming", tenant="test", workspace="test", action="fetch_subreddit", limit=5)

            assert result.success
            assert len(result.data["posts"]) == 1

    def test_missing_credentials(self):
        """Test handling of missing credentials."""
        from src.ultimate_discord_intelligence_bot.tools.acquisition.reddit_api_tool import RedditAPITool

        tool = RedditAPITool()
        result = tool._run(url="test", tenant="test", workspace="test")

        assert not result.success
        assert "credentials" in result.error.lower()
