"""Tests for Twitter API tool."""

import importlib.util
from unittest.mock import Mock, patch

import pytest


TWEEPY_AVAILABLE = importlib.util.find_spec("tweepy") is not None


class TestTwitterAPITool:
    """Test cases for Twitter API tool."""

    @pytest.fixture
    def tool(self):
        """Create TwitterAPITool instance."""
        from src.ultimate_discord_intelligence_bot.tools.acquisition.twitter_api_tool import TwitterAPITool

        return TwitterAPITool(bearer_token="test_token")

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == "twitter_api"

    @pytest.mark.skipif(not TWEEPY_AVAILABLE, reason="Tweepy not available")
    def test_search_tweets(self, tool):
        """Test searching for tweets."""
        # Mock API response
        mock_tweet = Mock()
        mock_tweet.id = "123456"
        mock_tweet.text = "Test tweet"
        mock_tweet.created_at = None
        mock_tweet.author_id = "user123"
        mock_tweet.public_metrics = {
            "retweet_count": 10,
            "like_count": 50,
            "reply_count": 5,
        }

        mock_response = Mock()
        mock_response.data = [mock_tweet]

        with patch.object(tool.api, "search_recent_tweets", return_value=mock_response):
            result = tool._run(
                query="test query", tenant="test", workspace="test", action="search_tweets", max_results=10
            )

            assert result.success
            assert len(result.data["results"]) == 1
            assert result.data["results"][0]["text"] == "Test tweet"

    @pytest.mark.skipif(not TWEEPY_AVAILABLE, reason="Tweepy not available")
    def test_get_tweet(self, tool):
        """Test getting a specific tweet."""
        # Mock API response
        mock_tweet = Mock()
        mock_tweet.id = "123456"
        mock_tweet.text = "Test tweet"
        mock_tweet.created_at = None
        mock_tweet.author_id = "user123"
        mock_tweet.public_metrics = {
            "retweet_count": 10,
            "like_count": 50,
            "reply_count": 5,
        }

        mock_response = Mock()
        mock_response.data = mock_tweet

        with patch.object(tool.api, "get_tweet", return_value=mock_response):
            result = tool._run(query="123456", tenant="test", workspace="test", action="get_tweet")

            assert result.success
            assert result.data["tweet"]["text"] == "Test tweet"

    def test_missing_credentials(self):
        """Test handling of missing credentials."""
        from src.ultimate_discord_intelligence_bot.tools.acquisition.twitter_api_tool import TwitterAPITool

        tool = TwitterAPITool()
        result = tool._run(query="test", tenant="test", workspace="test")

        assert not result.success
        assert "credentials" in result.error.lower()
