"""
Tests for TikTok API client and models.
"""

from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client import TikTokClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_models import (
    TikTokComment,
    TikTokInsights,
    TikTokUser,
    TikTokVideo,
    TikTokVideoList,
)


class TestTikTokModels:
    """Test TikTok Pydantic models."""

    def test_tiktok_user_model(self):
        """Test TikTokUser model."""
        user_data = {
            "open_id": "test_user_123",
            "union_id": "union_123",
            "avatar_url": "https://example.com/avatar.jpg",
            "display_name": "Test User",
            "follower_count": 1000000,
            "following_count": 500,
            "likes_count": 5000000,
            "video_count": 150,
            "is_verified": True,
        }

        user = TikTokUser(**user_data)

        assert user.open_id == "test_user_123"
        assert user.display_name == "Test User"
        assert user.follower_count == 1000000
        assert user.is_verified is True

    def test_tiktok_video_model(self):
        """Test TikTokVideo model."""
        video_data = {
            "id": "video_123",
            "title": "Test Video",
            "description": "Test description",
            "duration": 30,
            "cover_image_url": "https://example.com/cover.jpg",
            "view_count": 1000000,
            "like_count": 50000,
            "comment_count": 2500,
            "share_count": 1000,
            "created_time": "2024-01-15T10:30:00Z",
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "status": "PUBLISHED",
            "hashtags": ["test", "video"],
            "mentions": ["@user"],
        }

        video = TikTokVideo(**video_data)

        assert video.id == "video_123"
        assert video.title == "Test Video"
        assert video.duration == 30
        assert video.view_count == 1000000
        assert "test" in video.hashtags

    def test_tiktok_comment_model(self):
        """Test TikTokComment model."""
        comment_data = {
            "id": "comment_123",
            "text": "Great video!",
            "like_count": 150,
            "reply_count": 5,
            "created_time": "2024-01-15T11:00:00Z",
            "user": {
                "open_id": "commenter_123",
                "display_name": "Commenter",
                "avatar_url": "https://example.com/avatar.jpg",
                "is_verified": False,
            },
        }

        comment = TikTokComment(**comment_data)

        assert comment.id == "comment_123"
        assert comment.text == "Great video!"
        assert comment.like_count == 150
        assert comment.user.display_name == "Commenter"


class TestTikTokClient:
    """Test TikTok API client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreatorOpsConfig()
        # Add missing TikTok config attributes that TikTokClient expects
        self.config.tiktok_client_key = "test_client_key"
        self.config.tiktok_client_secret = "test_client_secret"
        self.config.tiktok_access_token = "test_access_token"
        self.config.default_region = "US"

        self.client = TikTokClient(config=self.config)

    def test_initialization(self):
        """Test client initialization."""
        assert self.client.client_key == "test_client_key"
        assert self.client.client_secret == "test_client_secret"
        assert self.client.access_token == "test_access_token"
        assert self.client.base_url == "https://open-api.tiktok.com"

    def test_get_headers(self):
        """Test header generation."""
        headers = self.client._get_headers()

        assert "Content-Type" in headers
        assert "User-Agent" in headers
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_access_token"

    def test_check_regional_eligibility(self):
        """Test regional eligibility check."""
        # Test supported region
        assert self.client._check_regional_eligibility("US") is True
        assert self.client._check_regional_eligibility("GB") is True

        # Test unsupported region
        assert self.client._check_regional_eligibility("XX") is False

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.httpx.Client")
    def test_get_user_info_success(self, mock_client):
        """Test successful user info retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "user": {
                    "open_id": "test_user_123",
                    "display_name": "Test User",
                    "follower_count": 1000000,
                    "is_verified": True,
                }
            },
            "error": None,
        }
        mock_response.headers = {}

        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Test
        result = self.client.get_user_info()

        assert result.success
        assert isinstance(result.data, TikTokUser)
        assert result.data.open_id == "test_user_123"
        assert result.data.display_name == "Test User"

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.httpx.Client")
    def test_get_user_info_api_error(self, mock_client):
        """Test user info retrieval with API error."""
        # Mock response with error
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": None,
            "error": {
                "code": "INVALID_TOKEN",
                "message": "Access token is invalid",
            },
        }
        mock_response.headers = {}

        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Test
        result = self.client.get_user_info()

        assert not result.success
        assert "Access token is invalid" in result.error

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.httpx.Client")
    def test_get_video_list_success(self, mock_client):
        """Test successful video list retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "videos": [
                    {
                        "id": "video_1",
                        "title": "Test Video 1",
                        "duration": 30,
                        "view_count": 1000000,
                        "created_time": "2024-01-15T10:30:00Z",
                        "privacy_level": "PUBLIC_TO_EVERYONE",
                        "status": "PUBLISHED",
                        "hashtags": ["test"],
                        "mentions": [],
                    }
                ],
                "cursor": "next_cursor",
                "has_more": True,
            },
            "error": None,
        }
        mock_response.headers = {}

        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Test
        result = self.client.get_video_list()

        assert result.success
        assert isinstance(result.data, TikTokVideoList)
        assert len(result.data.videos) == 1
        assert result.data.videos[0].id == "video_1"
        assert result.data.has_more is True

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.httpx.Client")
    def test_get_video_comments_success(self, mock_client):
        """Test successful video comments retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "comments": [
                    {
                        "id": "comment_1",
                        "text": "Great video!",
                        "like_count": 150,
                        "reply_count": 5,
                        "created_time": "2024-01-15T11:00:00Z",
                        "user": {
                            "open_id": "commenter_1",
                            "display_name": "Commenter",
                            "is_verified": False,
                        },
                    }
                ],
                "cursor": "next_cursor",
                "has_more": True,
            },
            "error": None,
        }
        mock_response.headers = {}

        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Test
        result = self.client.get_video_comments("video_123")

        assert result.success
        assert isinstance(result.data, list)
        assert len(result.data) == 1
        assert result.data[0].id == "comment_1"
        assert result.data[0].text == "Great video!"

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.httpx.Client")
    def test_get_video_insights_success(self, mock_client):
        """Test successful video insights retrieval."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "view_count": 1000000,
                "like_count": 50000,
                "comment_count": 2500,
                "share_count": 1000,
                "profile_views": 5000,
                "video_views_by_region": {"US": 400000, "GB": 200000},
                "video_views_by_age_group": {"18-24": 400000, "25-34": 300000},
                "video_views_by_gender": {"male": 450000, "female": 550000},
            },
            "error": None,
        }
        mock_response.headers = {}

        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Test
        result = self.client.get_video_insights("video_123")

        assert result.success
        assert isinstance(result.data, TikTokInsights)
        assert result.data.view_count == 1000000
        assert result.data.like_count == 50000
        assert "US" in result.data.video_views_by_region

    def test_get_user_info_no_token(self):
        """Test user info retrieval without access token."""
        client = TikTokClient()
        result = client.get_user_info()

        assert not result.success
        assert "TikTok access token not configured" in result.error

    def test_get_user_info_unsupported_region(self):
        """Test user info retrieval with unsupported region."""
        self.config.default_region = "XX"
        client = TikTokClient(config=self.config)
        result = client.get_user_info()

        assert not result.success
        assert "Region not supported by TikTok APIs" in result.error

    def test_get_rate_limit_info(self):
        """Test rate limit information retrieval."""
        self.client.rate_limit_remaining = 500
        self.client.rate_limit_reset = 1640995200

        info = self.client.get_rate_limit_info()

        assert info["remaining"] == 500
        assert info["reset"] == 1640995200
        assert "US" in info["supported_regions"]

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.Path.exists")
    @patch("builtins.open")
    def test_get_fixture_response(self, mock_open, mock_exists):
        """Test fixture response loading."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'

        response = self.client._get_fixture_response("user")

        assert response == {"test": "data"}

    @patch("ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client.Path.exists")
    def test_get_fixture_response_not_found(self, mock_exists):
        """Test fixture response loading when file not found."""
        mock_exists.return_value = False

        response = self.client._get_fixture_response("nonexistent")

        assert response == {}
