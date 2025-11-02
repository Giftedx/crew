"""
Tests for X (Twitter) API v2 client and models.
"""

from datetime import datetime
from platform.core.step_result import StepResult
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_client import XClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_models import (
    XURL,
    XAnnotation,
    XCashtag,
    XCostGuard,
    XError,
    XHashtag,
    XMedia,
    XMention,
    XMentionResponse,
    XMeta,
    XPlace,
    XPoll,
    XRateLimit,
    XResponse,
    XSearchResponse,
    XTimelineResponse,
    XTweet,
    XTweetResponse,
    XUser,
    XUserResponse,
    XWebhookEvent,
    XWebhookSubscription,
)


class TestXModels:
    """Test X (Twitter) Pydantic models."""

    def test_x_user_model(self):
        """Test XUser model."""
        user_data = {
            "id": "1234567890123456789",
            "username": "test_user",
            "name": "Test User",
            "description": "Test bio",
            "profile_image_url": "https://example.com/avatar.jpg",
            "public_metrics": {"followers_count": 1000, "following_count": 500, "tweet_count": 100, "listed_count": 10},
            "verified": True,
            "protected": False,
            "created_at": "2020-01-15T10:30:00.000Z",
            "location": "Test Location",
            "url": "https://test.com",
            "pinned_tweet_id": "1234567890123456789",
            "entities": {
                "url": {
                    "urls": [
                        {
                            "start": 0,
                            "end": 23,
                            "url": "https://test.com",
                            "expanded_url": "https://test.com",
                            "display_url": "test.com",
                        }
                    ]
                },
                "description": {"hashtags": [], "mentions": [], "urls": []},
            },
        }
        user = XUser(**user_data)
        assert user.id == "1234567890123456789"
        assert user.username == "test_user"
        assert user.name == "Test User"
        assert user.verified is True
        assert user.public_metrics["followers_count"] == 1000

    def test_x_tweet_model(self):
        """Test XTweet model."""
        tweet_data = {
            "id": "1234567890123456789",
            "text": "Test tweet content",
            "author_id": "1234567890123456789",
            "created_at": "2024-01-15T10:30:00.000Z",
            "public_metrics": {"retweet_count": 10, "reply_count": 5, "like_count": 100, "quote_count": 2},
            "context_annotations": [
                {
                    "domain": {"id": "47", "name": "Brand", "description": "Brands and Companies"},
                    "entity": {
                        "id": "1000000000000000000",
                        "name": "Test Brand",
                        "description": "Test brand description",
                    },
                }
            ],
            "entities": {"hashtags": [{"start": 0, "end": 5, "tag": "test"}], "mentions": [], "urls": []},
            "lang": "en",
            "possibly_sensitive": False,
            "reply_settings": "everyone",
            "source": "Twitter for iPhone",
            "conversation_id": "1234567890123456789",
        }
        tweet = XTweet(**tweet_data)
        assert tweet.id == "1234567890123456789"
        assert tweet.text == "Test tweet content"
        assert tweet.author_id == "1234567890123456789"
        assert tweet.public_metrics["like_count"] == 100
        assert tweet.entities["hashtags"][0]["tag"] == "test"

    def test_x_media_model(self):
        """Test XMedia model."""
        media_data = {
            "media_key": "3_1234567890123456789",
            "type": "photo",
            "url": "https://example.com/image.jpg",
            "preview_image_url": "https://example.com/preview.jpg",
            "alt_text": "Test image",
            "height": 1080,
            "width": 1920,
            "public_metrics": {"view_count": 1000},
        }
        media = XMedia(**media_data)
        assert media.media_key == "3_1234567890123456789"
        assert media.type == "photo"
        assert media.url == "https://example.com/image.jpg"
        assert media.height == 1080
        assert media.width == 1920

    def test_x_mention_model(self):
        """Test XMention model."""
        mention_data = {"start": 0, "end": 10, "username": "test_user", "id": "1234567890123456789"}
        mention = XMention(**mention_data)
        assert mention.start == 0
        assert mention.end == 10
        assert mention.username == "test_user"
        assert mention.id == "1234567890123456789"

    def test_x_hashtag_model(self):
        """Test XHashtag model."""
        hashtag_data = {"start": 0, "end": 5, "tag": "test"}
        hashtag = XHashtag(**hashtag_data)
        assert hashtag.start == 0
        assert hashtag.end == 5
        assert hashtag.tag == "test"

    def test_x_url_model(self):
        """Test XURL model."""
        url_data = {
            "start": 0,
            "end": 23,
            "url": "https://example.com",
            "expanded_url": "https://example.com",
            "display_url": "example.com",
            "title": "Example Website",
            "description": "An example website",
            "images": [{"url": "https://example.com/image.jpg", "width": 1200, "height": 630}],
        }
        url = XURL(**url_data)
        assert url.start == 0
        assert url.end == 23
        assert url.url == "https://example.com"
        assert url.title == "Example Website"
        assert len(url.images) == 1

    def test_x_cashtag_model(self):
        """Test XCashtag model."""
        cashtag_data = {"start": 0, "end": 4, "tag": "TEST"}
        cashtag = XCashtag(**cashtag_data)
        assert cashtag.start == 0
        assert cashtag.end == 4
        assert cashtag.tag == "TEST"

    def test_x_annotation_model(self):
        """Test XAnnotation model."""
        annotation_data = {
            "start": 0,
            "end": 10,
            "probability": 0.95,
            "type": "Person",
            "normalized_text": "Test Person",
        }
        annotation = XAnnotation(**annotation_data)
        assert annotation.start == 0
        assert annotation.end == 10
        assert annotation.probability == 0.95
        assert annotation.type == "Person"
        assert annotation.normalized_text == "Test Person"

    def test_x_error_model(self):
        """Test XError model."""
        error_data = {
            "message": "Invalid request",
            "type": "InvalidRequest",
            "code": 400,
            "title": "Bad Request",
            "detail": "The request was invalid",
            "parameter": "query",
            "resource_type": "tweet",
            "resource_id": "1234567890123456789",
            "value": "invalid_value",
        }
        error = XError(**error_data)
        assert error.message == "Invalid request"
        assert error.type == "InvalidRequest"
        assert error.code == 400
        assert error.title == "Bad Request"

    def test_x_meta_model(self):
        """Test XMeta model."""
        meta_data = {
            "result_count": 10,
            "next_token": "next_token_12345",
            "previous_token": "previous_token_67890",
            "newest_id": "1234567890123456789",
            "oldest_id": "1234567890123456790",
            "sent": "2024-01-15T10:30:00.000Z",
        }
        meta = XMeta(**meta_data)
        assert meta.result_count == 10
        assert meta.next_token == "next_token_12345"
        assert meta.previous_token == "previous_token_67890"
        assert meta.newest_id == "1234567890123456789"
        assert meta.oldest_id == "1234567890123456790"

    def test_x_rate_limit_model(self):
        """Test XRateLimit model."""
        rate_limit_data = {"limit": 300, "remaining": 250, "reset": "2024-01-15T11:00:00.000Z", "retry_after": 60}
        rate_limit = XRateLimit(**rate_limit_data)
        assert rate_limit.limit == 300
        assert rate_limit.remaining == 250
        assert rate_limit.reset == datetime.fromisoformat("2024-01-15T11:00:00.000Z")
        assert rate_limit.retry_after == 60

    def test_x_cost_guard_model(self):
        """Test XCostGuard model."""
        cost_guard_data = {
            "tier": "pro",
            "monthly_tweet_cap": 100000,
            "tweets_used": 5000,
            "tweets_remaining": 95000,
            "reset_date": "2024-02-15T00:00:00.000Z",
            "cost_per_tweet": 0.0005,
            "estimated_monthly_cost": 2.5,
        }
        cost_guard = XCostGuard(**cost_guard_data)
        assert cost_guard.tier == "pro"
        assert cost_guard.monthly_tweet_cap == 100000
        assert cost_guard.tweets_used == 5000
        assert cost_guard.tweets_remaining == 95000
        assert cost_guard.cost_per_tweet == 0.0005
        assert cost_guard.estimated_monthly_cost == 2.5

    def test_x_webhook_subscription_model(self):
        """Test XWebhookSubscription model."""
        subscription_data = {
            "id": "webhook_123",
            "url": "https://example.com/webhook",
            "valid": True,
            "created_timestamp": "2024-01-15T10:30:00.000Z",
        }
        subscription = XWebhookSubscription(**subscription_data)
        assert subscription.id == "webhook_123"
        assert subscription.url == "https://example.com/webhook"
        assert subscription.valid is True
        assert subscription.created_timestamp == datetime.fromisoformat("2024-01-15T10:30:00.000Z")

    def test_x_webhook_event_model(self):
        """Test XWebhookEvent model."""
        event_data = {
            "for_user_id": "1234567890123456789",
            "tweet_create_events": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "tweet_delete_events": [],
            "direct_message_events": [],
            "follow_events": [],
            "favorite_events": [],
            "block_events": [],
            "mute_events": [],
            "user_event": None,
        }
        event = XWebhookEvent(**event_data)
        assert event.for_user_id == "1234567890123456789"
        assert len(event.tweet_create_events) == 1
        assert event.tweet_create_events[0].text == "Test tweet"

    def test_x_response_model(self):
        """Test XResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {"result_count": 1, "newest_id": "1234567890123456789", "oldest_id": "1234567890123456789"},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0
        assert "users" in response.includes

    def test_x_tweet_response_model(self):
        """Test XTweetResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {"result_count": 1, "newest_id": "1234567890123456789", "oldest_id": "1234567890123456789"},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XTweetResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0

    def test_x_user_response_model(self):
        """Test XUserResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "username": "test_user",
                    "name": "Test User",
                    "description": "Test bio",
                    "profile_image_url": "https://example.com/avatar.jpg",
                    "public_metrics": {
                        "followers_count": 1000,
                        "following_count": 500,
                        "tweet_count": 100,
                        "listed_count": 10,
                    },
                    "verified": True,
                    "protected": False,
                    "created_at": "2020-01-15T10:30:00.000Z",
                    "location": "Test Location",
                    "url": "https://test.com",
                    "pinned_tweet_id": "1234567890123456789",
                    "entities": {
                        "url": {
                            "urls": [
                                {
                                    "start": 0,
                                    "end": 23,
                                    "url": "https://test.com",
                                    "expanded_url": "https://test.com",
                                    "display_url": "test.com",
                                }
                            ]
                        },
                        "description": {"hashtags": [], "mentions": [], "urls": []},
                    },
                }
            ],
            "meta": {"result_count": 1},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XUserResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0

    def test_x_search_response_model(self):
        """Test XSearchResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {"result_count": 1, "newest_id": "1234567890123456789", "oldest_id": "1234567890123456789"},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XSearchResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0

    def test_x_timeline_response_model(self):
        """Test XTimelineResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {"result_count": 1, "newest_id": "1234567890123456789", "oldest_id": "1234567890123456789"},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XTimelineResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0

    def test_x_mention_response_model(self):
        """Test XMentionResponse model."""
        response_data = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {"result_count": 1, "newest_id": "1234567890123456789", "oldest_id": "1234567890123456789"},
            "errors": [],
            "includes": {"users": [], "tweets": [], "media": [], "polls": [], "places": []},
        }
        response = XMentionResponse(**response_data)
        assert len(response.data) == 1
        assert response.meta.result_count == 1
        assert len(response.errors) == 0


class TestXClient:
    """Test X (Twitter) API v2 client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreatorOpsConfig()
        self.config.X_CLIENT_ID = "test_client_id"
        self.config.X_CLIENT_SECRET = "test_client_secret"
        self.config.X_REDIRECT_URI = "https://example.com/callback"
        self.config.X_API_TIER = "pro"
        self.config.X_API_TIMEOUT = 30
        mock_oauth_manager = Mock()
        mock_oauth_manager.get_access_token.return_value = StepResult.ok(data="mock_access_token")
        self.client = XClient(config=self.config, oauth_manager=mock_oauth_manager)

    def test_initialization(self):
        """Test client initialization."""
        assert self.client.client_id == "test_client_id"
        assert self.client.client_secret == "test_client_secret"
        assert self.client.redirect_uri == "https://example.com/callback"
        assert self.client.scope == "tweet.read,tweet.write,users.read,offline.access"
        assert self.client.api_tier == "pro"
        assert self.client.monthly_tweet_cap == 100000
        assert self.client.cost_per_tweet == 0.0005

    def test_get_monthly_tweet_cap(self):
        """Test monthly tweet cap calculation."""
        assert self.client._get_monthly_tweet_cap() == 100000
        self.client.api_tier = "free"
        assert self.client._get_monthly_tweet_cap() == 0
        self.client.api_tier = "basic"
        assert self.client._get_monthly_tweet_cap() == 10000
        self.client.api_tier = "enterprise"
        assert self.client._get_monthly_tweet_cap() == 1000000

    def test_get_cost_per_tweet(self):
        """Test cost per tweet calculation."""
        assert self.client._get_cost_per_tweet() == 0.0005
        self.client.api_tier = "free"
        assert self.client._get_cost_per_tweet() == 0.0
        self.client.api_tier = "basic"
        assert self.client._get_cost_per_tweet() == 0.001
        self.client.api_tier = "enterprise"
        assert self.client._get_cost_per_tweet() == 0.0001

    def test_check_rate_limit(self):
        """Test rate limit information extraction."""
        mock_response = Mock()
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
            "retry-after": "60",
        }
        rate_limit = self.client._check_rate_limit(mock_response)
        assert rate_limit.limit == 300
        assert rate_limit.remaining == 250
        assert rate_limit.reset == datetime.fromtimestamp(1640995200)
        assert rate_limit.retry_after == 60

    def test_check_cost_guard_success(self):
        """Test successful cost guard check."""
        self.client.tweets_used = 5000
        result = self.client._check_cost_guard()
        assert result.success
        assert isinstance(result.data, XCostGuard)
        assert result.data.tier == "pro"
        assert result.data.tweets_used == 5000
        assert result.data.tweets_remaining == 95000

    def test_check_cost_guard_failure(self):
        """Test failed cost guard check."""
        self.client.tweets_used = 100000
        result = self.client._check_cost_guard()
        assert not result.success
        assert "Monthly tweet cap exceeded" in result.error

    def test_get_user_by_username_success(self):
        """Test successful user retrieval by username."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "username": "test_user",
                "name": "Test User",
                "description": "Test bio",
                "profile_image_url": "https://example.com/avatar.jpg",
                "public_metrics": {
                    "followers_count": 1000,
                    "following_count": 500,
                    "tweet_count": 100,
                    "listed_count": 10,
                },
                "verified": True,
                "protected": False,
                "created_at": "2020-01-15T10:30:00.000Z",
                "location": "Test Location",
                "url": "https://test.com",
                "pinned_tweet_id": "1234567890123456789",
                "entities": {
                    "url": {
                        "urls": [
                            {
                                "start": 0,
                                "end": 23,
                                "url": "https://test.com",
                                "expanded_url": "https://test.com",
                                "display_url": "test.com",
                            }
                        ]
                    },
                    "description": {"hashtags": [], "mentions": [], "urls": []},
                },
            }
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_by_username("1234567890123456789", "test_user")
            assert result.success
            assert isinstance(result.data, XUser)
            assert result.data.id == "1234567890123456789"
            assert result.data.username == "test_user"

    def test_get_user_by_username_api_error(self):
        """Test user retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [
                {
                    "message": "User not found",
                    "type": "ResourceNotFound",
                    "code": 404,
                    "title": "Not Found",
                    "detail": "The requested user was not found",
                    "parameter": "username",
                    "resource_type": "user",
                    "resource_id": "test_user",
                    "value": "test_user",
                }
            ]
        }
        mock_response.headers = {}
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_by_username("1234567890123456789", "test_user")
            assert not result.success
            assert "User not found" in result.error

    def test_get_user_timeline_success(self):
        """Test successful user timeline retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {
                "result_count": 1,
                "newest_id": "1234567890123456789",
                "oldest_id": "1234567890123456789",
                "next_token": "next_token_12345",
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_timeline("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, tuple)
            tweets, next_token, rate_limit = result.data
            assert len(tweets) == 1
            assert tweets[0].id == "1234567890123456789"
            assert next_token == "next_token_12345"
            assert rate_limit.limit == 300

    def test_get_user_mentions_success(self):
        """Test successful user mentions retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "@test_user This is a mention!",
                    "author_id": "9876543210987654321",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {
                "result_count": 1,
                "newest_id": "1234567890123456789",
                "oldest_id": "1234567890123456789",
                "next_token": "next_mention_token_12345",
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_mentions("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, tuple)
            mentions, next_token, rate_limit = result.data
            assert len(mentions) == 1
            assert mentions[0].id == "1234567890123456789"
            assert next_token == "next_mention_token_12345"
            assert rate_limit.limit == 300

    def test_search_tweets_success(self):
        """Test successful tweet search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "1234567890123456789",
                    "text": "Test search result",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "meta": {
                "result_count": 1,
                "newest_id": "1234567890123456789",
                "oldest_id": "1234567890123456789",
                "next_token": "next_search_token_12345",
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.search_tweets("1234567890123456789", "test query")
            assert result.success
            assert isinstance(result.data, tuple)
            tweets, next_token, rate_limit = result.data
            assert len(tweets) == 1
            assert tweets[0].id == "1234567890123456789"
            assert next_token == "next_search_token_12345"
            assert rate_limit.limit == 300

    def test_get_tweet_success(self):
        """Test successful tweet retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "text": "Test tweet",
                "author_id": "1234567890123456789",
                "created_at": "2024-01-15T10:30:00.000Z",
                "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                "lang": "en",
                "possibly_sensitive": False,
                "reply_settings": "everyone",
                "source": "Twitter for iPhone",
                "conversation_id": "1234567890123456789",
            }
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_tweet("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, XTweet)
            assert result.data.id == "1234567890123456789"
            assert result.data.text == "Test tweet"

    def test_create_tweet_success(self):
        """Test successful tweet creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "text": "New test tweet",
                "author_id": "1234567890123456789",
                "created_at": "2024-01-15T10:30:00.000Z",
                "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                "lang": "en",
                "possibly_sensitive": False,
                "reply_settings": "everyone",
                "source": "Twitter for iPhone",
                "conversation_id": "1234567890123456789",
            }
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.create_tweet("1234567890123456789", "New test tweet")
            assert result.success
            assert isinstance(result.data, XTweet)
            assert result.data.id == "1234567890123456789"
            assert result.data.text == "New test tweet"
            assert self.client.tweets_used == 1

    def test_create_tweet_cost_guard_failure(self):
        """Test tweet creation with cost guard failure."""
        self.client.tweets_used = 100000
        result = self.client.create_tweet("1234567890123456789", "New test tweet")
        assert not result.success
        assert "Monthly tweet cap exceeded" in result.error

    def test_delete_tweet_success(self):
        """Test successful tweet deletion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"deleted": True}}
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.delete_tweet("1234567890123456789", "1234567890123456789")
            assert result.success
            assert result.data is True

    def test_get_tweet_media_success(self):
        """Test successful tweet media retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "text": "Test tweet with media",
                "author_id": "1234567890123456789",
                "created_at": "2024-01-15T10:30:00.000Z",
                "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                "lang": "en",
                "possibly_sensitive": False,
                "reply_settings": "everyone",
                "source": "Twitter for iPhone",
                "conversation_id": "1234567890123456789",
                "attachments": {"media_keys": ["3_1234567890123456789"]},
            },
            "includes": {
                "media": [
                    {
                        "media_key": "3_1234567890123456789",
                        "type": "photo",
                        "url": "https://example.com/image.jpg",
                        "preview_image_url": "https://example.com/preview.jpg",
                        "alt_text": "Test image",
                        "height": 1080,
                        "width": 1920,
                        "public_metrics": {"view_count": 1000},
                    }
                ]
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_tweet_media("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, list)
            assert len(result.data) == 1
            assert result.data[0].media_key == "3_1234567890123456789"
            assert result.data[0].type == "photo"

    def test_get_tweet_poll_success(self):
        """Test successful tweet poll retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "text": "Test tweet with poll",
                "author_id": "1234567890123456789",
                "created_at": "2024-01-15T10:30:00.000Z",
                "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                "lang": "en",
                "possibly_sensitive": False,
                "reply_settings": "everyone",
                "source": "Twitter for iPhone",
                "conversation_id": "1234567890123456789",
                "attachments": {"poll_ids": ["poll_1234567890123456789"]},
            },
            "includes": {
                "polls": [
                    {
                        "id": "poll_1234567890123456789",
                        "options": [
                            {"position": 1, "label": "Option 1", "votes": 10},
                            {"position": 2, "label": "Option 2", "votes": 5},
                        ],
                        "duration_minutes": 60,
                        "end_datetime": "2024-01-15T11:30:00.000Z",
                        "voting_status": "closed",
                    }
                ]
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_tweet_poll("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, XPoll)
            assert result.data.id == "poll_1234567890123456789"
            assert len(result.data.options) == 2
            assert result.data.duration_minutes == 60

    def test_get_tweet_place_success(self):
        """Test successful tweet place retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1234567890123456789",
                "text": "Test tweet with place",
                "author_id": "1234567890123456789",
                "created_at": "2024-01-15T10:30:00.000Z",
                "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                "lang": "en",
                "possibly_sensitive": False,
                "reply_settings": "everyone",
                "source": "Twitter for iPhone",
                "conversation_id": "1234567890123456789",
                "geo": {"place_id": "place_1234567890123456789"},
            },
            "includes": {
                "places": [
                    {
                        "id": "place_1234567890123456789",
                        "name": "Test Place",
                        "country_code": "US",
                        "place_type": "city",
                        "full_name": "Test Place, US",
                        "country": "United States",
                        "contained_within": [],
                        "geo": {"type": "Point", "bbox": [-74.0, 40.0, -73.0, 41.0], "properties": {}},
                    }
                ]
            },
        }
        mock_response.headers = {
            "x-rate-limit-limit": "300",
            "x-rate-limit-remaining": "250",
            "x-rate-limit-reset": "1640995200",
        }
        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_tweet_place("1234567890123456789", "1234567890123456789")
            assert result.success
            assert isinstance(result.data, XPlace)
            assert result.data.id == "place_1234567890123456789"
            assert result.data.name == "Test Place"
            assert result.data.country_code == "US"

    def test_get_rate_limit_info(self):
        """Test rate limit information retrieval."""
        result = self.client.get_rate_limit_info("1234567890123456789")
        assert result.success
        assert result.data["platform"] == "x"
        assert result.data["api_tier"] == "pro"
        assert result.data["monthly_tweet_cap"] == 100000
        assert result.data["tweets_used"] == 0
        assert result.data["tweets_remaining"] == 100000
        assert result.data["cost_per_tweet"] == 0.0005
        assert result.data["estimated_monthly_cost"] == 0.0

    def test_get_cost_guard_info(self):
        """Test cost guard information retrieval."""
        result = self.client.get_cost_guard_info("1234567890123456789")
        assert result.success
        assert isinstance(result.data, XCostGuard)
        assert result.data.tier == "pro"
        assert result.data.monthly_tweet_cap == 100000
        assert result.data.tweets_used == 0
        assert result.data.tweets_remaining == 100000
        assert result.data.cost_per_tweet == 0.0005
        assert result.data.estimated_monthly_cost == 0.0

    def test_create_webhook_subscription_success(self):
        """Test successful webhook subscription creation."""
        result = self.client.create_webhook_subscription(
            "1234567890123456789", "https://example.com/webhook", ["tweet_create_events", "tweet_delete_events"]
        )
        assert result.success
        assert isinstance(result.data, XWebhookSubscription)
        assert result.data.id == "webhook_123"
        assert result.data.url == "https://example.com/webhook"
        assert result.data.valid is True

    def test_process_webhook_event_success(self):
        """Test successful webhook event processing."""
        event_data = {
            "for_user_id": "1234567890123456789",
            "tweet_create_events": [
                {
                    "id": "1234567890123456789",
                    "text": "Test tweet",
                    "author_id": "1234567890123456789",
                    "created_at": "2024-01-15T10:30:00.000Z",
                    "public_metrics": {"retweet_count": 0, "reply_count": 0, "like_count": 0, "quote_count": 0},
                    "lang": "en",
                    "possibly_sensitive": False,
                    "reply_settings": "everyone",
                    "source": "Twitter for iPhone",
                    "conversation_id": "1234567890123456789",
                }
            ],
            "tweet_delete_events": [],
            "direct_message_events": [],
            "follow_events": [],
            "favorite_events": [],
            "block_events": [],
            "mute_events": [],
            "user_event": None,
        }
        result = self.client.process_webhook_event(event_data)
        assert result.success
        assert isinstance(result.data, XWebhookEvent)
        assert result.data.for_user_id == "1234567890123456789"
        assert len(result.data.tweet_create_events) == 1
        assert result.data.tweet_create_events[0].text == "Test tweet"

    def test_process_webhook_event_failure(self):
        """Test failed webhook event processing."""
        event_data = {"for_user_id": "1234567890123456789", "tweet_create_events": "invalid_format"}
        result = self.client.process_webhook_event(event_data)
        assert not result.success
        assert "Failed to parse webhook event" in result.error

    def test_get_user_by_username_no_token(self):
        """Test user retrieval without access token."""
        client = XClient()
        result = client.get_user_by_username("1234567890123456789", "test_user")
        assert not result.success
        assert "X access token not configured" in result.error

    def test_get_user_by_username_unsupported_region(self):
        """Test user retrieval with unsupported region."""
        self.config.default_region = "XX"
        client = XClient(config=self.config)
        result = client.get_user_by_username("1234567890123456789", "test_user")
        assert not result.success
        assert "Region not supported by X APIs" in result.error

    def test_get_fixture_response(self):
        """Test fixture response loading."""
        with patch("pathlib.Path.exists") as mock_exists, patch("builtins.open") as mock_open:
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
            response = self.client._get_fixture_response("user")
            assert response == {"test": "data"}

    def test_get_fixture_response_not_found(self):
        """Test fixture response loading when file not found."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False
            response = self.client._get_fixture_response("nonexistent")
            assert response == {}
