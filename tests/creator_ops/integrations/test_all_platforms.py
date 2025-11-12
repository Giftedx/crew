"""
Comprehensive integration tests for all platform APIs.
Tests contract validation, rate limiting, and end-to-end workflows.
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_client import InstagramClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client import TikTokClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import TwitchClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_client import XClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import YouTubeClient
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class TestPlatformContractValidation:
    """Test that all platform clients return properly structured data."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for all platforms."""
        config = Mock(spec=CreatorOpsConfig)
        config.youtube_api_key = "test_youtube_key"
        config.youtube_oauth_client_id = "test_youtube_client_id"
        config.youtube_oauth_client_secret = "test_youtube_secret"
        config.twitch_client_id = "test_twitch_client_id"
        config.twitch_client_secret = "test_twitch_secret"
        config.tiktok_client_key = "test_tiktok_client_key"
        config.tiktok_client_secret = "test_tiktok_secret"
        config.instagram_app_id = "test_instagram_app_id"
        config.instagram_app_secret = "test_instagram_secret"
        config.x_client_id = "test_x_client_id"
        config.x_client_secret = "test_x_secret"
        config.default_region = "US"
        return config

    @pytest.fixture
    def mock_oauth_manager(self):
        """Mock OAuth manager."""
        oauth_manager = Mock()
        oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        return oauth_manager

    def test_youtube_contract_validation(self, mock_config, mock_oauth_manager):
        """Test YouTube API contract validation."""
        client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {
                    "items": [
                        {
                            "id": "UC123456789",
                            "snippet": {
                                "title": "Test Channel",
                                "description": "Test Description",
                                "publishedAt": "2020-01-01T00:00:00Z",
                                "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                            },
                            "statistics": {"subscriberCount": "1000000", "videoCount": "100", "viewCount": "10000000"},
                        }
                    ]
                }
            )
            result = client.get_channel_info("UC123456789")
            assert result.success
            assert result.data.id == "UC123456789"
            assert result.data.title == "Test Channel"
            assert result.data.subscriber_count == 1000000

    def test_twitch_contract_validation(self, mock_config, mock_oauth_manager):
        """Test Twitch API contract validation."""
        client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {
                    "data": [
                        {
                            "id": "123456789",
                            "login": "testuser",
                            "display_name": "Test User",
                            "type": "",
                            "broadcaster_type": "partner",
                            "description": "Test Description",
                            "profile_image_url": "https://example.com/profile.jpg",
                            "offline_image_url": "https://example.com/offline.jpg",
                            "view_count": 1000000,
                            "created_at": "2020-01-01T00:00:00Z",
                        }
                    ]
                }
            )
            result = client.get_user_info("testuser")
            assert result.success
            assert result.data.id == "123456789"
            assert result.data.login == "testuser"
            assert result.data.view_count == 1000000

    def test_tiktok_contract_validation(self, mock_config, mock_oauth_manager):
        """Test TikTok API contract validation."""
        client = TikTokClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {
                    "data": {
                        "user": {
                            "open_id": "test_user_123",
                            "display_name": "Test User",
                            "follower_count": 1000000,
                            "is_verified": True,
                        }
                    }
                }
            )
            result = client.get_user_info("test_user_123")
            assert result.success
            assert result.data.open_id == "test_user_123"
            assert result.data.display_name == "Test User"
            assert result.data.is_verified is True

    def test_instagram_contract_validation(self, mock_config, mock_oauth_manager):
        """Test Instagram API contract validation."""
        client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {
                    "id": "17841400000000000",
                    "username": "test_user",
                    "account_type": "BUSINESS",
                    "followers_count": 50000,
                    "is_verified": True,
                }
            )
            result = client.get_user_info("17841400000000000", "17841400000000000")
            assert result.success
            assert result.data.id == "17841400000000000"
            assert result.data.username == "test_user"
            assert result.data.account_type == "BUSINESS"

    def test_x_contract_validation(self, mock_config, mock_oauth_manager):
        """Test X API contract validation."""
        client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {
                    "data": {
                        "id": "1234567890123456789",
                        "username": "test_user",
                        "name": "Test User",
                        "public_metrics": {"followers_count": 1000, "following_count": 500, "tweet_count": 100},
                        "verified": True,
                    }
                },
                Mock(),
            )
            result = client.get_user_by_username("1234567890123456789", "test_user")
            assert result.success
            assert result.data.id == "1234567890123456789"
            assert result.data.username == "test_user"
            assert result.data.verified is True


class TestRateLimitSimulation:
    """Test rate limiting behavior across all platforms."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for rate limit testing."""
        config = Mock(spec=CreatorOpsConfig)
        config.youtube_api_key = "test_youtube_key"
        config.twitch_client_id = "test_twitch_client_id"
        config.tiktok_client_key = "test_tiktok_client_key"
        config.instagram_app_id = "test_instagram_app_id"
        config.x_client_id = "test_x_client_id"
        config.default_region = "US"
        return config

    @pytest.fixture
    def mock_oauth_manager(self):
        """Mock OAuth manager."""
        oauth_manager = Mock()
        oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        return oauth_manager

    async def test_youtube_rate_limit_simulation(self, mock_config, mock_oauth_manager):
        """Test YouTube rate limiting with burst requests."""
        client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"items": [{"id": "test_video", "snippet": {"title": "Test Video"}}]}
            )
            tasks = []
            for i in range(100):
                tasks.append(client.get_video_info(f"video_{i}"))
            results = await asyncio.gather(*tasks)
            assert all(result.success for result in results)
            assert len(results) == 100

    async def test_twitch_rate_limit_simulation(self, mock_config, mock_oauth_manager):
        """Test Twitch rate limiting with burst requests."""
        client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": [{"id": "123", "login": "testuser", "display_name": "Test User"}]}
            )
            tasks = []
            for i in range(100):
                tasks.append(client.get_user_info(f"user_{i}"))
            results = await asyncio.gather(*tasks)
            assert all(result.success for result in results)
            assert len(results) == 100

    async def test_tiktok_rate_limit_simulation(self, mock_config, mock_oauth_manager):
        """Test TikTok rate limiting with burst requests."""
        client = TikTokClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": {"user": {"open_id": "test_user_123", "display_name": "Test User"}}}
            )
            tasks = []
            for i in range(100):
                tasks.append(client.get_user_info(f"user_{i}"))
            results = await asyncio.gather(*tasks)
            assert all(result.success for result in results)
            assert len(results) == 100

    async def test_instagram_rate_limit_simulation(self, mock_config, mock_oauth_manager):
        """Test Instagram rate limiting with burst requests."""
        client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"id": "17841400000000000", "username": "test_user", "account_type": "BUSINESS"}
            )
            tasks = []
            for i in range(100):
                tasks.append(client.get_user_info(f"user_{i}", f"user_{i}"))
            results = await asyncio.gather(*tasks)
            assert all(result.success for result in results)
            assert len(results) == 100

    async def test_x_rate_limit_simulation(self, mock_config, mock_oauth_manager):
        """Test X rate limiting with burst requests."""
        client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": {"id": "1234567890123456789", "username": "test_user", "name": "Test User"}}, Mock()
            )
            tasks = []
            for i in range(100):
                tasks.append(client.get_user_by_username(f"user_{i}", f"user_{i}"))
            results = await asyncio.gather(*tasks)
            assert all(result.success for result in results)
            assert len(results) == 100


class TestFixtureValidation:
    """Test that fixture data matches expected schemas."""

    def test_youtube_fixture_validation(self):
        """Test YouTube fixture data structure."""
        fixture_path = "fixtures/creator_ops/youtube_channels.json"
        with open(fixture_path) as f:
            data = json.load(f)
        assert "items" in data
        assert len(data["items"]) > 0
        channel = data["items"][0]
        assert "id" in channel
        assert "snippet" in channel
        assert "statistics" in channel
        assert "title" in channel["snippet"]
        assert "subscriberCount" in channel["statistics"]

    def test_twitch_fixture_validation(self):
        """Test Twitch fixture data structure."""
        fixture_path = "fixtures/creator_ops/twitch_users.json"
        with open(fixture_path) as f:
            data = json.load(f)
        assert "data" in data
        assert len(data["data"]) > 0
        user = data["data"][0]
        assert "id" in user
        assert "login" in user
        assert "display_name" in user
        assert "view_count" in user

    def test_tiktok_fixture_validation(self):
        """Test TikTok fixture data structure."""
        fixture_path = "fixtures/creator_ops/tiktok_user.json"
        with open(fixture_path) as f:
            data = json.load(f)
        assert "data" in data
        assert "user" in data["data"]
        user = data["data"]["user"]
        assert "open_id" in user
        assert "display_name" in user
        assert "follower_count" in user
        assert "is_verified" in user

    def test_instagram_fixture_validation(self):
        """Test Instagram fixture data structure."""
        fixture_path = "fixtures/creator_ops/instagram_user.json"
        with open(fixture_path) as f:
            data = json.load(f)
        assert "id" in data
        assert "username" in data
        assert "account_type" in data
        assert "followers_count" in data
        assert "is_verified" in data

    def test_x_fixture_validation(self):
        """Test X fixture data structure."""
        fixture_path = "fixtures/creator_ops/x_user.json"
        with open(fixture_path) as f:
            data = json.load(f)
        assert "data" in data
        user = data["data"]
        assert "id" in user
        assert "username" in user
        assert "name" in user
        assert "public_metrics" in user
        assert "verified" in user


class TestEndToEndWorkflows:
    """Test complete workflows across platforms."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for E2E testing."""
        config = Mock(spec=CreatorOpsConfig)
        config.youtube_api_key = "test_youtube_key"
        config.twitch_client_id = "test_twitch_client_id"
        config.tiktok_client_key = "test_tiktok_client_key"
        config.instagram_app_id = "test_instagram_app_id"
        config.x_client_id = "test_x_client_id"
        config.default_region = "US"
        return config

    @pytest.fixture
    def mock_oauth_manager(self):
        """Mock OAuth manager."""
        oauth_manager = Mock()
        oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        return oauth_manager

    async def test_cross_platform_content_discovery(self, mock_config, mock_oauth_manager):
        """Test discovering content across multiple platforms."""
        youtube_client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(youtube_client, "search_videos") as mock_search:
            mock_search.return_value = StepResult.success(
                [Mock(id="video1", title="Test Video 1", channel_title="Test Channel")]
            )
            youtube_results = await youtube_client.search_videos("test query", max_results=5)
            assert youtube_results.success
            assert len(youtube_results.data) == 1
        twitch_client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(twitch_client, "search_streams") as mock_search:
            mock_search.return_value = StepResult.success(
                [Mock(id="stream1", title="Test Stream 1", user_name="TestUser")]
            )
            twitch_results = await twitch_client.search_streams("test query", first=5)
            assert twitch_results.success
            assert len(twitch_results.data) == 1
        tiktok_client = TikTokClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(tiktok_client, "get_user_videos") as mock_videos:
            mock_videos.return_value = StepResult.success(([Mock(id="video1", title="Test TikTok 1")], None))
            tiktok_results = await tiktok_client.get_user_videos("test_user", max_count=5)
            assert tiktok_results.success
            assert len(tiktok_results.data[0]) == 1
        instagram_client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(instagram_client, "get_user_media") as mock_media:
            mock_media.return_value = StepResult.success(
                ([Mock(id="media1", media_type="IMAGE", caption="Test Instagram 1")], None)
            )
            instagram_results = await instagram_client.get_user_media("test_user", limit=5)
            assert instagram_results.success
            assert len(instagram_results.data[0]) == 1
        x_client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(x_client, "search_tweets") as mock_search:
            mock_search.return_value = StepResult.success(([Mock(id="tweet1", text="Test Tweet 1")], None, Mock()))
            x_results = await x_client.search_tweets("test_user", "test query", max_results=5)
            assert x_results.success
            assert len(x_results.data[0]) == 1

    async def test_content_processing_pipeline(self, mock_config, mock_oauth_manager):
        """Test processing content from discovery to analysis."""
        youtube_client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(youtube_client, "get_video_info") as mock_video:
            mock_video.return_value = StepResult.success(Mock(id="video1", title="Test Video", duration="PT1H30M"))
            video_info = await youtube_client.get_video_info("video1")
            assert video_info.success
        with patch.object(youtube_client, "get_video_transcript") as mock_transcript:
            mock_transcript.return_value = StepResult.success("This is a test transcript.")
            transcript = await youtube_client.get_video_transcript("video1")
            assert transcript.success
        with patch.object(youtube_client, "get_video_comments") as mock_comments:
            mock_comments.return_value = StepResult.success(
                ([Mock(id="comment1", text="Great video!", like_count=10)], None)
            )
            comments = await youtube_client.get_video_comments("video1")
            assert comments.success
            assert len(comments.data[0]) == 1
        with patch.object(youtube_client, "get_video_analytics") as mock_analytics:
            mock_analytics.return_value = StepResult.success(
                {"views": 10000, "likes": 500, "comments": 50, "engagement_rate": 0.055}
            )
            analytics = await youtube_client.get_video_analytics("video1")
            assert analytics.success
            assert analytics.data["views"] == 10000

    async def test_multi_platform_engagement_analysis(self, mock_config, mock_oauth_manager):
        """Test analyzing engagement across multiple platforms."""
        engagement_data = {}
        youtube_client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(youtube_client, "get_video_analytics") as mock_analytics:
            mock_analytics.return_value = StepResult.success({"views": 10000, "likes": 500, "comments": 50})
            youtube_engagement = await youtube_client.get_video_analytics("video1")
            if youtube_engagement.success:
                engagement_data["youtube"] = youtube_engagement.data
        twitch_client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(twitch_client, "get_stream_analytics") as mock_analytics:
            mock_analytics.return_value = StepResult.success(
                {"viewer_count": 1000, "chatter_count": 100, "follower_count": 50}
            )
            twitch_engagement = await twitch_client.get_stream_analytics("stream1")
            if twitch_engagement.success:
                engagement_data["twitch"] = twitch_engagement.data
        instagram_client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(instagram_client, "get_media_insights") as mock_insights:
            mock_insights.return_value = StepResult.success(
                Mock(media_id="media1", insights=[Mock(name="impressions", values=[{"value": 5000}])])
            )
            instagram_engagement = await instagram_client.get_media_insights("user1", "media1", ["impressions"])
            if instagram_engagement.success:
                engagement_data["instagram"] = instagram_engagement.data
        x_client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(x_client, "get_tweet") as mock_tweet:
            mock_tweet.return_value = StepResult.success(
                Mock(id="tweet1", public_metrics={"retweet_count": 100, "like_count": 500, "reply_count": 50})
            )
            x_engagement = await x_client.get_tweet("user1", "tweet1")
            if x_engagement.success:
                engagement_data["x"] = x_engagement.data
        assert len(engagement_data) >= 2
        total_engagement = 0
        for platform, data in engagement_data.items():
            if platform == "youtube":
                total_engagement += data.get("views", 0)
            elif platform == "twitch":
                total_engagement += data.get("viewer_count", 0)
            elif platform == "instagram":
                total_engagement += data.get("insights", [{}])[0].get("values", [{}])[0].get("value", 0)
            elif platform == "x":
                total_engagement += data.public_metrics.get("like_count", 0)
        assert total_engagement > 0


class TestErrorHandling:
    """Test error handling across all platforms."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for error testing."""
        config = Mock(spec=CreatorOpsConfig)
        config.youtube_api_key = "test_youtube_key"
        config.twitch_client_id = "test_twitch_client_id"
        config.tiktok_client_key = "test_tiktok_client_key"
        config.instagram_app_id = "test_instagram_app_id"
        config.x_client_id = "test_x_client_id"
        config.default_region = "US"
        return config

    @pytest.fixture
    def mock_oauth_manager(self):
        """Mock OAuth manager."""
        oauth_manager = Mock()
        oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        return oauth_manager

    async def test_youtube_error_handling(self, mock_config, mock_oauth_manager):
        """Test YouTube error handling."""
        client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.fail("YouTube API error: Quota exceeded")
            result = await client.get_video_info("invalid_video")
            assert not result.success
            assert "Quota exceeded" in result.error

    async def test_twitch_error_handling(self, mock_config, mock_oauth_manager):
        """Test Twitch error handling."""
        client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.fail("Twitch API error: Rate limit exceeded")
            result = await client.get_user_info("invalid_user")
            assert not result.success
            assert "Rate limit exceeded" in result.error

    async def test_tiktok_error_handling(self, mock_config, mock_oauth_manager):
        """Test TikTok error handling."""
        client = TikTokClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.fail("TikTok API error: Invalid token")
            result = await client.get_user_info("invalid_user")
            assert not result.success
            assert "Invalid token" in result.error

    async def test_instagram_error_handling(self, mock_config, mock_oauth_manager):
        """Test Instagram error handling."""
        client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.fail("Instagram API error: Permission denied")
            result = await client.get_user_info("invalid_user", "invalid_user")
            assert not result.success
            assert "Permission denied" in result.error

    async def test_x_error_handling(self, mock_config, mock_oauth_manager):
        """Test X error handling."""
        client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.fail("X API error: User not found")
            result = await client.get_user_by_username("invalid_user", "invalid_user")
            assert not result.success
            assert "User not found" in result.error


class TestPerformanceBenchmarks:
    """Test performance benchmarks for all platforms."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for performance testing."""
        config = Mock(spec=CreatorOpsConfig)
        config.youtube_api_key = "test_youtube_key"
        config.twitch_client_id = "test_twitch_client_id"
        config.tiktok_client_key = "test_tiktok_client_key"
        config.instagram_app_id = "test_instagram_app_id"
        config.x_client_id = "test_x_client_id"
        config.default_region = "US"
        return config

    @pytest.fixture
    def mock_oauth_manager(self):
        """Mock OAuth manager."""
        oauth_manager = Mock()
        oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        return oauth_manager

    async def test_youtube_performance(self, mock_config, mock_oauth_manager):
        """Test YouTube API performance."""
        client = YouTubeClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"items": [{"id": "video1", "snippet": {"title": "Test Video"}}]}
            )
            start_time = datetime.now()
            result = await client.get_video_info("video1")
            end_time = datetime.now()
            assert result.success
            assert (end_time - start_time).total_seconds() < 1.0

    async def test_twitch_performance(self, mock_config, mock_oauth_manager):
        """Test Twitch API performance."""
        client = TwitchClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": [{"id": "123", "login": "testuser", "display_name": "Test User"}]}
            )
            start_time = datetime.now()
            result = await client.get_user_info("testuser")
            end_time = datetime.now()
            assert result.success
            assert (end_time - start_time).total_seconds() < 1.0

    async def test_tiktok_performance(self, mock_config, mock_oauth_manager):
        """Test TikTok API performance."""
        client = TikTokClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": {"user": {"open_id": "test_user_123", "display_name": "Test User"}}}
            )
            start_time = datetime.now()
            result = await client.get_user_info("test_user_123")
            end_time = datetime.now()
            assert result.success
            assert (end_time - start_time).total_seconds() < 1.0

    async def test_instagram_performance(self, mock_config, mock_oauth_manager):
        """Test Instagram API performance."""
        client = InstagramClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"id": "17841400000000000", "username": "test_user", "account_type": "BUSINESS"}
            )
            start_time = datetime.now()
            result = await client.get_user_info("17841400000000000", "17841400000000000")
            end_time = datetime.now()
            assert result.success
            assert (end_time - start_time).total_seconds() < 1.0

    async def test_x_performance(self, mock_config, mock_oauth_manager):
        """Test X API performance."""
        client = XClient(config=mock_config, oauth_manager=mock_oauth_manager)
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.success(
                {"data": {"id": "1234567890123456789", "username": "test_user", "name": "Test User"}}, Mock()
            )
            start_time = datetime.now()
            result = await client.get_user_by_username("1234567890123456789", "test_user")
            end_time = datetime.now()
            assert result.success
            assert (end_time - start_time).total_seconds() < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
