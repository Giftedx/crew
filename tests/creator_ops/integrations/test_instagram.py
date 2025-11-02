"""
Tests for Instagram Graph API client and models.
"""
from unittest.mock import Mock, patch
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_client import InstagramClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_models import InstagramAccountInsight, InstagramComment, InstagramError, InstagramHashtag, InstagramInsight, InstagramLongLivedToken, InstagramMedia, InstagramMediaInsight, InstagramMention, InstagramResponse, InstagramStory, InstagramUser, InstagramWebhookEvent, InstagramWebhookSubscription
from platform.core.step_result import StepResult

class TestInstagramModels:
    """Test Instagram Pydantic models."""

    def test_instagram_user_model(self):
        """Test InstagramUser model."""
        user_data = {'id': '17841400000000000', 'username': 'test_user', 'account_type': 'BUSINESS', 'media_count': 100, 'followers_count': 50000, 'follows_count': 200, 'name': 'Test User', 'biography': 'Test bio', 'website': 'https://test.com', 'profile_picture_url': 'https://example.com/avatar.jpg', 'is_verified': True, 'is_private': False, 'is_business': True, 'is_creator': False}
        user = InstagramUser(**user_data)
        assert user.id == '17841400000000000'
        assert user.username == 'test_user'
        assert user.account_type == 'BUSINESS'
        assert user.followers_count == 50000
        assert user.is_verified is True

    def test_instagram_media_model(self):
        """Test InstagramMedia model."""
        media_data = {'id': '17900000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/image.jpg', 'permalink': 'https://www.instagram.com/p/ABC123/', 'caption': 'Test caption', 'timestamp': '2024-01-15T10:30:00+0000', 'like_count': 1000, 'comments_count': 50, 'thumbnail_url': 'https://example.com/thumb.jpg'}
        media = InstagramMedia(**media_data)
        assert media.id == '17900000000000000'
        assert media.media_type == 'IMAGE'
        assert media.media_url == 'https://example.com/image.jpg'
        assert media.like_count == 1000

    def test_instagram_comment_model(self):
        """Test InstagramComment model."""
        comment_data = {'id': '18000000000000000', 'text': 'Great post!', 'timestamp': '2024-01-15T10:35:00+0000', 'like_count': 10, 'hidden': False, 'user': {'id': '17841400000000001', 'username': 'commenter', 'account_type': 'PERSONAL', 'media_count': 25, 'followers_count': 500, 'follows_count': 100, 'name': 'Commenter', 'is_verified': False, 'is_private': False, 'is_business': False, 'is_creator': False}}
        comment = InstagramComment(**comment_data)
        assert comment.id == '18000000000000000'
        assert comment.text == 'Great post!'
        assert comment.like_count == 10
        assert comment.user.username == 'commenter'

    def test_instagram_story_model(self):
        """Test InstagramStory model."""
        story_data = {'id': '18100000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/story.jpg', 'permalink': 'https://www.instagram.com/stories/test_user/18100000000000000/', 'timestamp': '2024-01-15T09:00:00+0000', 'expires_at': '2024-01-16T09:00:00+0000', 'impressions': 1000, 'reach': 900, 'replies': 5, 'taps_forward': 10, 'taps_back': 5, 'exits': 20}
        story = InstagramStory(**story_data)
        assert story.id == '18100000000000000'
        assert story.media_type == 'IMAGE'
        assert story.impressions == 1000
        assert story.reach == 900

    def test_instagram_insight_model(self):
        """Test InstagramInsight model."""
        insight_data = {'name': 'impressions', 'period': 'day', 'values': [{'value': 1000, 'end_time': '2024-01-15T00:00:00+0000'}], 'title': 'Impressions', 'description': 'Total number of times your content was viewed', 'id': '17841400000000000/insights/impressions/day'}
        insight = InstagramInsight(**insight_data)
        assert insight.name == 'impressions'
        assert insight.period == 'day'
        assert insight.title == 'Impressions'
        assert len(insight.values) == 1

    def test_instagram_hashtag_model(self):
        """Test InstagramHashtag model."""
        hashtag_data = {'name': 'gaming', 'media_count': 1000000}
        hashtag = InstagramHashtag(**hashtag_data)
        assert hashtag.name == 'gaming'
        assert hashtag.media_count == 1000000

    def test_instagram_mention_model(self):
        """Test InstagramMention model."""
        mention_data = {'username': 'test_user', 'id': '17841400000000000'}
        mention = InstagramMention(**mention_data)
        assert mention.username == 'test_user'
        assert mention.id == '17841400000000000'

    def test_instagram_error_model(self):
        """Test InstagramError model."""
        error_data = {'message': 'Invalid access token', 'type': 'OAuthException', 'code': 190, 'error_subcode': 463, 'fbtrace_id': 'ABC123DEF456'}
        error = InstagramError(**error_data)
        assert error.message == 'Invalid access token'
        assert error.type == 'OAuthException'
        assert error.code == 190

    def test_instagram_long_lived_token_model(self):
        """Test InstagramLongLivedToken model."""
        token_data = {'access_token': 'long_lived_token_123', 'token_type': 'bearer', 'expires_in': 5183944}
        token = InstagramLongLivedToken(**token_data)
        assert token.access_token == 'long_lived_token_123'
        assert token.token_type == 'bearer'
        assert token.expires_in == 5183944

    def test_instagram_webhook_subscription_model(self):
        """Test InstagramWebhookSubscription model."""
        subscription_data = {'object': 'instagram', 'callback_url': 'https://example.com/webhook', 'fields': ['comments', 'likes'], 'verify_token': 'verify_token_123'}
        subscription = InstagramWebhookSubscription(**subscription_data)
        assert subscription.object == 'instagram'
        assert subscription.callback_url == 'https://example.com/webhook'
        assert 'comments' in subscription.fields

    def test_instagram_webhook_event_model(self):
        """Test InstagramWebhookEvent model."""
        event_data = {'object': 'instagram', 'entry': [{'id': '17841400000000000', 'time': 1640995200, 'changes': [{'field': 'comments', 'value': {'id': '18000000000000000', 'text': 'New comment'}}]}], 'id': 'webhook_event_123'}
        event = InstagramWebhookEvent(**event_data)
        assert event.object == 'instagram'
        assert len(event.entry) == 1
        assert event.entry[0]['id'] == '17841400000000000'

    def test_instagram_media_insight_model(self):
        """Test InstagramMediaInsight model."""
        insight_data = {'media_id': '17900000000000000', 'insights': [{'name': 'impressions', 'period': 'day', 'values': [{'value': 1000, 'end_time': '2024-01-15T00:00:00+0000'}], 'title': 'Impressions', 'description': 'Total number of times your content was viewed', 'id': '17900000000000000/insights/impressions/day'}], 'timestamp': '2024-01-15T10:30:00+0000'}
        media_insight = InstagramMediaInsight(**insight_data)
        assert media_insight.media_id == '17900000000000000'
        assert len(media_insight.insights) == 1
        assert media_insight.insights[0].name == 'impressions'

    def test_instagram_account_insight_model(self):
        """Test InstagramAccountInsight model."""
        insight_data = {'account_id': '17841400000000000', 'insights': [{'name': 'impressions', 'period': 'day', 'values': [{'value': 1000, 'end_time': '2024-01-15T00:00:00+0000'}], 'title': 'Impressions', 'description': 'Total number of times your content was viewed', 'id': '17841400000000000/insights/impressions/day'}], 'timestamp': '2024-01-15T10:30:00+0000', 'period': 'day'}
        account_insight = InstagramAccountInsight(**insight_data)
        assert account_insight.account_id == '17841400000000000'
        assert len(account_insight.insights) == 1
        assert account_insight.period == 'day'

    def test_instagram_response_model(self):
        """Test InstagramResponse model."""
        response_data = {'data': [{'id': '17900000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/image.jpg', 'permalink': 'https://www.instagram.com/p/ABC123/', 'timestamp': '2024-01-15T10:30:00+0000', 'like_count': 1000, 'comments_count': 50}], 'paging': {'cursors': {'before': 'before_cursor_12345', 'after': 'after_cursor_67890'}, 'next': 'https://graph.facebook.com/v18.0/17841400000000000/media?access_token=...&after=after_cursor_67890'}}
        response = InstagramResponse(**response_data)
        assert len(response.data) == 1
        assert response.paging is not None
        assert response.paging.cursors is not None
        assert response.paging.cursors['after'] == 'after_cursor_67890'

class TestInstagramClient:
    """Test Instagram Graph API client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreatorOpsConfig()
        self.config.INSTAGRAM_APP_ID = 'test_app_id'
        self.config.INSTAGRAM_APP_SECRET = 'test_app_secret'
        self.config.INSTAGRAM_REDIRECT_URI = 'https://example.com/callback'
        self.config.INSTAGRAM_WEBHOOK_VERIFY_TOKEN = 'test_verify_token'
        self.config.INSTAGRAM_API_TIMEOUT = 30
        mock_oauth_manager = Mock()
        mock_oauth_manager.get_access_token.return_value = StepResult.ok(data='mock_access_token')
        self.client = InstagramClient(config=self.config, oauth_manager=mock_oauth_manager)

    def test_initialization(self):
        """Test client initialization."""
        assert self.client.app_id == 'test_app_id'
        assert self.client.app_secret == 'test_app_secret'
        assert self.client.redirect_uri == 'https://example.com/callback'
        assert self.client.scope == 'instagram_basic,instagram_manage_insights,instagram_manage_comments,instagram_manage_messages'

    def test_get_headers(self):
        """Test header generation."""
        headers = self.client._get_headers()
        assert 'Content-Type' in headers
        assert 'User-Agent' in headers
        assert 'Authorization' in headers
        assert headers['Authorization'] == 'Bearer test_access_token'

    def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': '17841400000000000', 'username': 'test_user', 'account_type': 'BUSINESS', 'followers_count': 50000, 'is_verified': True}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_info('17841400000000000')
            assert result.success
            assert isinstance(result.data, InstagramUser)
            assert result.data.id == '17841400000000000'
            assert result.data.username == 'test_user'

    def test_get_user_info_api_error(self):
        """Test user info retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': {'message': 'Invalid access token', 'type': 'OAuthException', 'code': 190}}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_info('17841400000000000')
            assert not result.success
            assert 'Invalid access token' in result.error

    def test_get_user_media_success(self):
        """Test successful user media retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '17900000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/image.jpg', 'permalink': 'https://www.instagram.com/p/ABC123/', 'timestamp': '2024-01-15T10:30:00+0000', 'like_count': 1000, 'comments_count': 50}], 'paging': {'cursors': {'after': 'after_cursor_67890'}}}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_media('17841400000000000')
            assert result.success
            assert isinstance(result.data, tuple)
            media_items, next_cursor = result.data
            assert len(media_items) == 1
            assert media_items[0].id == '17900000000000000'
            assert next_cursor == 'after_cursor_67890'

    def test_get_media_comments_success(self):
        """Test successful media comments retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '18000000000000000', 'text': 'Great post!', 'timestamp': '2024-01-15T10:35:00+0000', 'like_count': 10, 'hidden': False}], 'paging': {'cursors': {'after': 'after_comment_cursor_67890'}}}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_media_comments('17841400000000000', '17900000000000000')
            assert result.success
            assert isinstance(result.data, tuple)
            comments, _next_cursor = result.data
            assert len(comments) == 1
            assert comments[0].id == '18000000000000000'
            assert comments[0].text == 'Great post!'

    def test_get_user_stories_success(self):
        """Test successful user stories retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '18100000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/story.jpg', 'permalink': 'https://www.instagram.com/stories/test_user/18100000000000000/', 'timestamp': '2024-01-15T09:00:00+0000', 'expires_at': '2024-01-16T09:00:00+0000', 'impressions': 1000, 'reach': 900, 'replies': 5, 'taps_forward': 10, 'taps_back': 5, 'exits': 20}]}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_user_stories('17841400000000000')
            assert result.success
            assert isinstance(result.data, list)
            assert len(result.data) == 1
            assert result.data[0].id == '18100000000000000'
            assert result.data[0].impressions == 1000

    def test_get_media_insights_success(self):
        """Test successful media insights retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'name': 'impressions', 'period': 'day', 'values': [{'value': 1000, 'end_time': '2024-01-15T00:00:00+0000'}], 'title': 'Impressions', 'description': 'Total number of times your content was viewed', 'id': '17900000000000000/insights/impressions/day'}]}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_media_insights('17841400000000000', '17900000000000000', ['impressions'])
            assert result.success
            assert isinstance(result.data, InstagramMediaInsight)
            assert result.data.media_id == '17900000000000000'
            assert len(result.data.insights) == 1
            assert result.data.insights[0].name == 'impressions'

    def test_get_account_insights_success(self):
        """Test successful account insights retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'name': 'impressions', 'period': 'day', 'values': [{'value': 1000, 'end_time': '2024-01-15T00:00:00+0000'}], 'title': 'Impressions', 'description': 'Total number of times your content was viewed', 'id': '17841400000000000/insights/impressions/day'}]}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_account_insights('17841400000000000', ['impressions'])
            assert result.success
            assert isinstance(result.data, InstagramAccountInsight)
            assert result.data.account_id == '17841400000000000'
            assert len(result.data.insights) == 1
            assert result.data.insights[0].name == 'impressions'

    def test_search_hashtags_success(self):
        """Test successful hashtag search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'name': 'gaming', 'media_count': 1000000}]}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.search_hashtags('17841400000000000', 'gaming')
            assert result.success
            assert isinstance(result.data, list)
            assert len(result.data) == 1
            assert result.data[0].name == 'gaming'
            assert result.data[0].media_count == 1000000

    def test_get_hashtag_media_success(self):
        """Test successful hashtag media retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': '17900000000000000', 'media_type': 'IMAGE', 'media_url': 'https://example.com/image.jpg', 'permalink': 'https://www.instagram.com/p/ABC123/', 'timestamp': '2024-01-15T10:30:00+0000', 'like_count': 1000, 'comments_count': 50}], 'paging': {'cursors': {'after': 'after_cursor_67890'}}}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_hashtag_media('17841400000000000', 'gaming')
            assert result.success
            assert isinstance(result.data, tuple)
            media_items, next_cursor = result.data
            assert len(media_items) == 1
            assert media_items[0].id == '17900000000000000'
            assert next_cursor == 'after_cursor_67890'

    def test_create_webhook_subscription_success(self):
        """Test successful webhook subscription creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'object': 'instagram', 'callback_url': 'https://example.com/webhook', 'fields': ['comments', 'likes'], 'verify_token': 'verify_token_123'}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.create_webhook_subscription('17841400000000000', 'https://example.com/webhook', ['comments', 'likes'], 'verify_token_123')
            assert result.success
            assert isinstance(result.data, InstagramWebhookSubscription)
            assert result.data.object == 'instagram'
            assert result.data.callback_url == 'https://example.com/webhook'

    def test_get_long_lived_token_success(self):
        """Test successful long-lived token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'long_lived_token_123', 'token_type': 'bearer', 'expires_in': 5183944}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.get_long_lived_token('17841400000000000', 'short_lived_token_123')
            assert result.success
            assert isinstance(result.data, InstagramLongLivedToken)
            assert result.data.access_token == 'long_lived_token_123'
            assert result.data.token_type == 'bearer'

    def test_refresh_long_lived_token_success(self):
        """Test successful long-lived token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'refreshed_token_123', 'token_type': 'bearer', 'expires_in': 5183944}
        mock_response.headers = {}
        with patch('httpx.Client') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__enter__.return_value = mock_client_instance
            result = self.client.refresh_long_lived_token('17841400000000000', 'long_lived_token_123')
            assert result.success
            assert isinstance(result.data, InstagramLongLivedToken)
            assert result.data.access_token == 'refreshed_token_123'
            assert result.data.token_type == 'bearer'

    def test_verify_webhook_success(self):
        """Test successful webhook verification."""
        result = self.client.verify_webhook('subscribe', 'test_verify_token', 'challenge_123')
        assert result.success
        assert result.data == 'challenge_123'

    def test_verify_webhook_failure(self):
        """Test failed webhook verification."""
        result = self.client.verify_webhook('subscribe', 'wrong_token', 'challenge_123')
        assert not result.success
        assert 'Webhook verification failed' in result.error

    def test_process_webhook_event_success(self):
        """Test successful webhook event processing."""
        event_data = {'object': 'instagram', 'entry': [{'id': '17841400000000000', 'time': 1640995200, 'changes': [{'field': 'comments', 'value': {'id': '18000000000000000', 'text': 'New comment'}}]}], 'id': 'webhook_event_123'}
        result = self.client.process_webhook_event(event_data)
        assert result.success
        assert isinstance(result.data, InstagramWebhookEvent)
        assert result.data.object == 'instagram'
        assert len(result.data.entry) == 1

    def test_process_webhook_event_failure(self):
        """Test failed webhook event processing."""
        event_data = {'object': 'instagram', 'entry': 'invalid_entry_format'}
        result = self.client.process_webhook_event(event_data)
        assert not result.success
        assert 'Failed to parse webhook event' in result.error

    def test_get_rate_limit_info(self):
        """Test rate limit information retrieval."""
        result = self.client.get_rate_limit_info('17841400000000000')
        assert result.success
        assert result.data['platform'] == 'instagram'
        assert result.data['rate_limit_type'] == 'app_based'

    def test_get_user_info_no_token(self):
        """Test user info retrieval without access token."""
        client = InstagramClient()
        result = client.get_user_info('17841400000000000')
        assert not result.success
        assert 'Instagram access token not configured' in result.error

    def test_get_user_info_unsupported_region(self):
        """Test user info retrieval with unsupported region."""
        self.config.default_region = 'XX'
        client = InstagramClient(config=self.config)
        result = client.get_user_info('17841400000000000')
        assert not result.success
        assert 'Region not supported by Instagram APIs' in result.error

    def test_get_fixture_response(self):
        """Test fixture response loading."""
        with patch('pathlib.Path.exists') as mock_exists, patch('builtins.open') as mock_open:
            mock_exists.return_value = True
            mock_open.return_value.__enter__.return_value.read.return_value = '{"test": "data"}'
            response = self.client._get_fixture_response('user')
            assert response == {'test': 'data'}

    def test_get_fixture_response_not_found(self):
        """Test fixture response loading when file not found."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            response = self.client._get_fixture_response('nonexistent')
            assert response == {}