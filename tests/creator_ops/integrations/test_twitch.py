"""
Unit tests for Twitch integration client.

Tests cover:
- Twitch API authentication and token management
- Stream metadata retrieval
- Chat message polling
- Clip creation and management
- Error handling and rate limiting
- Webhook/EventSub integration
"""
from datetime import datetime
from unittest.mock import Mock, patch
import pytest
from requests.exceptions import ConnectionError
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import TwitchClient
from platform.core.step_result import StepResult

class TestTwitchClient:
    """Test suite for Twitch client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TwitchClient(client_id='test_client_id', client_secret='test_client_secret', oauth_manager=Mock(), config=Mock())
        self.test_user_id = '12345'
        self.test_stream_id = '67890'

    def test_initialization(self):
        """Test Twitch client initialization."""
        assert self.client.client_id == 'test_client_id'
        assert self.client.client_secret == 'test_client_secret'
        assert self.client.BASE_URL == 'https://api.twitch.tv/helix'

    def test_get_user_success(self):
        """Test successful user information retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': self.test_user_id, 'login': 'testuser', 'display_name': 'TestUser', 'type': '', 'broadcaster_type': 'partner', 'description': 'Test user description', 'profile_image_url': 'https://example.com/profile.jpg', 'offline_image_url': 'https://example.com/offline.jpg', 'view_count': 1000000, 'created_at': '2020-01-01T00:00:00Z'}]}
        mock_response.status_code = 200
        with patch.object(self.client.session, 'get', return_value=mock_response):
            result = self.client.get_user(login='testuser')
        assert result.success
        assert 'data' in result.data
        user = result.data['data']
        assert user.id == self.test_user_id
        assert user.login == 'testuser'
        assert user.display_name == 'TestUser'
        assert user.broadcaster_type == 'partner'

    def test_get_user_info_not_found(self):
        """Test user information retrieval when user not found."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_user_info('nonexistent_user')
        assert not result.success
        assert 'User not found' in result.error

    def test_get_user_info_api_error(self):
        """Test user information retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad Request', 'status': 400, 'message': 'Invalid user login'}
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_user_info('invalid_user')
        assert not result.success
        assert 'API error' in result.error

    def test_get_user_info_network_error(self):
        """Test user information retrieval with network error."""
        with patch('requests.get', side_effect=ConnectionError('Network error')):
            result = self.client.get_user_info('testuser')
        assert not result.success
        assert 'Network error' in result.error

    def test_get_stream_info_success(self):
        """Test successful stream information retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': self.test_stream_id, 'user_id': self.test_user_id, 'user_login': 'testuser', 'user_name': 'TestUser', 'game_id': '509658', 'game_name': 'Just Chatting', 'type': 'live', 'title': 'Test Stream Title', 'viewer_count': 1000, 'started_at': '2023-01-01T00:00:00Z', 'language': 'en', 'thumbnail_url': 'https://example.com/thumb.jpg', 'tag_ids': ['6ea6bca4-4712-4ab9-a906-e3336a9d8039'], 'is_mature': False}]}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_stream_info(self.test_user_id)
        assert result.success
        assert 'stream' in result.data
        stream = result.data['stream']
        assert stream.stream_id == self.test_stream_id
        assert stream.user_id == self.test_user_id
        assert stream.title == 'Test Stream Title'
        assert stream.viewer_count == 1000
        assert stream.game_name == 'Just Chatting'

    def test_get_stream_info_not_live(self):
        """Test stream information retrieval when user is not live."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_stream_info(self.test_user_id)
        assert not result.success
        assert 'Stream not found' in result.error

    def test_get_chat_messages_success(self):
        """Test successful chat message retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': 'msg_1', 'user_id': '12345', 'user_login': 'viewer1', 'user_name': 'Viewer1', 'message': 'Hello streamer!', 'created_at': '2023-01-01T00:00:00Z', 'color': '#FF0000', 'badges': [], 'emotes': [], 'reply_parent_msg_id': None, 'reply_parent_user_id': None, 'reply_parent_user_login': None, 'reply_parent_user_name': None, 'reply_parent_msg_body': None, 'thread_parent_msg_id': None, 'thread_parent_user_login': None, 'thread_parent_user_name': None, 'thread_parent_msg_body': None}, {'id': 'msg_2', 'user_id': '67890', 'user_login': 'viewer2', 'user_name': 'Viewer2', 'message': 'Great stream!', 'created_at': '2023-01-01T00:01:00Z', 'color': '#00FF00', 'badges': ['subscriber/12'], 'emotes': ['25:0-4'], 'reply_parent_msg_id': None, 'reply_parent_user_id': None, 'reply_parent_user_login': None, 'reply_parent_user_name': None, 'reply_parent_msg_body': None, 'thread_parent_msg_id': None, 'thread_parent_user_login': None, 'thread_parent_user_name': None, 'thread_parent_msg_body': None}], 'pagination': {'cursor': 'next_cursor_token'}}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_chat_messages(self.test_user_id, limit=10)
        assert result.success
        assert 'messages' in result.data
        messages = result.data['messages']
        assert len(messages) == 2
        assert messages[0].message_id == 'msg_1'
        assert messages[0].message == 'Hello streamer!'
        assert messages[0].user_name == 'Viewer1'
        assert messages[1].message_id == 'msg_2'
        assert messages[1].message == 'Great stream!'
        assert messages[1].user_name == 'Viewer2'

    def test_create_clip_success(self):
        """Test successful clip creation."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': 'clip_123', 'url': 'https://clips.twitch.tv/clip_123', 'embed_url': 'https://clips.twitch.tv/embed?clip=clip_123', 'broadcaster_id': self.test_user_id, 'broadcaster_name': 'TestUser', 'creator_id': '12345', 'creator_name': 'ClipCreator', 'video_id': 'video_123', 'game_id': '509658', 'language': 'en', 'title': 'Amazing moment!', 'view_count': 1000, 'created_at': '2023-01-01T00:00:00Z', 'thumbnail_url': 'https://example.com/clip_thumb.jpg', 'duration': 30.0, 'vod_offset': 120}]}
        mock_response.status_code = 202
        with patch('requests.post', return_value=mock_response):
            result = self.client.create_clip(self.test_user_id, 'Amazing moment!')
        assert result.success
        assert 'clip' in result.data
        clip = result.data['clip']
        assert clip.clip_id == 'clip_123'
        assert clip.title == 'Amazing moment!'
        assert clip.broadcaster_id == self.test_user_id
        assert clip.duration == 30.0

    def test_create_clip_not_live(self):
        """Test clip creation when stream is not live."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad Request', 'status': 400, 'message': 'Stream is not live'}
        with patch('requests.post', return_value=mock_response):
            result = self.client.create_clip(self.test_user_id, 'Test clip')
        assert not result.success
        assert 'Stream is not live' in result.error

    def test_get_clip_info_success(self):
        """Test successful clip information retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': 'clip_123', 'url': 'https://clips.twitch.tv/clip_123', 'embed_url': 'https://clips.twitch.tv/embed?clip=clip_123', 'broadcaster_id': self.test_user_id, 'broadcaster_name': 'TestUser', 'creator_id': '12345', 'creator_name': 'ClipCreator', 'video_id': 'video_123', 'game_id': '509658', 'language': 'en', 'title': 'Amazing moment!', 'view_count': 1000, 'created_at': '2023-01-01T00:00:00Z', 'thumbnail_url': 'https://example.com/clip_thumb.jpg', 'duration': 30.0, 'vod_offset': 120}]}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_clip_info('clip_123')
        assert result.success
        assert 'clip' in result.data
        clip = result.data['clip']
        assert clip.clip_id == 'clip_123'
        assert clip.title == 'Amazing moment!'
        assert clip.view_count == 1000

    def test_get_clip_info_not_found(self):
        """Test clip information retrieval when clip not found."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_clip_info('nonexistent_clip')
        assert not result.success
        assert 'Clip not found' in result.error

    def test_oauth_token_management(self):
        """Test OAuth token management."""
        self.client.oauth_manager.get_valid_token.return_value = StepResult.ok(data={'access_token': 'valid_token'})
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            self.client.get_user_info('testuser')
        self.client.oauth_manager.get_valid_token.assert_called_once()

    def test_oauth_token_refresh(self):
        """Test OAuth token refresh functionality."""
        mock_401_response = Mock()
        mock_401_response.status_code = 401
        mock_401_response.json.return_value = {'error': 'Unauthorized', 'status': 401, 'message': 'Invalid token'}
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {'data': []}
        self.client.oauth_manager.refresh_token.return_value = StepResult.ok(data={'access_token': 'new_token'})
        with patch('requests.get', side_effect=[mock_401_response, mock_success_response]):
            result = self.client.get_user_info('testuser')
        self.client.oauth_manager.refresh_token.assert_called_once()
        assert result.success

    def test_rate_limiting_handling(self):
        """Test rate limiting with exponential backoff."""
        mock_429_response = Mock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {'Ratelimit-Reset': str(int(datetime.now().timestamp()) + 1)}
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {'data': []}
        with patch('requests.get', side_effect=[mock_429_response, mock_success_response]), patch('time.sleep') as mock_sleep:
            result = self.client.get_user_info('testuser')
        mock_sleep.assert_called_once()
        assert result.success

    def test_batch_user_lookup(self):
        """Test batch user lookup functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': '12345', 'login': 'user1', 'display_name': 'User1', 'type': '', 'broadcaster_type': '', 'description': '', 'profile_image_url': '', 'offline_image_url': '', 'view_count': 1000, 'created_at': '2020-01-01T00:00:00Z'}, {'id': '67890', 'login': 'user2', 'display_name': 'User2', 'type': '', 'broadcaster_type': '', 'description': '', 'profile_image_url': '', 'offline_image_url': '', 'view_count': 2000, 'created_at': '2020-01-01T00:00:00Z'}]}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.batch_get_user_info(['user1', 'user2'])
        assert result.success
        assert 'users' in result.data
        users = result.data['users']
        assert len(users) == 2
        assert users[0].login == 'user1'
        assert users[1].login == 'user2'

    def test_followers_retrieval(self):
        """Test followers retrieval functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'from_id': 'follower1', 'from_login': 'follower1', 'from_name': 'Follower1', 'to_id': self.test_user_id, 'to_login': 'testuser', 'to_name': 'TestUser', 'followed_at': '2023-01-01T00:00:00Z'}, {'from_id': 'follower2', 'from_login': 'follower2', 'from_name': 'Follower2', 'to_id': self.test_user_id, 'to_login': 'testuser', 'to_name': 'TestUser', 'followed_at': '2023-01-02T00:00:00Z'}], 'pagination': {'cursor': 'next_cursor_token'}, 'total': 1000}
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_followers(self.test_user_id, limit=10)
        assert result.success
        assert 'followers' in result.data
        followers = result.data['followers']
        assert len(followers) == 2
        assert followers[0].from_id == 'follower1'
        assert followers[1].from_id == 'follower2'

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        results = []
        errors = []

        def make_request(user_login):
            try:
                mock_response = Mock()
                mock_response.json.return_value = {'data': [{'id': '12345', 'login': user_login, 'display_name': user_login.title(), 'type': '', 'broadcaster_type': '', 'description': '', 'profile_image_url': '', 'offline_image_url': '', 'view_count': 1000, 'created_at': '2020-01-01T00:00:00Z'}]}
                mock_response.status_code = 200
                with patch('requests.get', return_value=mock_response):
                    result = self.client.get_user_info(user_login)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(f'user_{i}',))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        assert len(results) == 5
        assert len(errors) == 0
        assert all((result.success for result in results))

    def test_webhook_verification(self):
        """Test webhook verification functionality."""
        challenge = 'test_challenge'
        result = self.client.verify_webhook(challenge)
        assert result.success
        assert result.data == challenge

    def test_eventsub_subscription(self):
        """Test EventSub subscription functionality."""
        mock_response = Mock()
        mock_response.json.return_value = {'data': [{'id': 'subscription_123', 'status': 'enabled', 'type': 'stream.online', 'version': '1', 'condition': {'broadcaster_user_id': self.test_user_id}, 'transport': {'method': 'webhook', 'callback': 'https://example.com/webhook', 'secret': 'webhook_secret'}, 'created_at': '2023-01-01T00:00:00Z'}]}
        mock_response.status_code = 202
        with patch('requests.post', return_value=mock_response):
            result = self.client.create_eventsub_subscription('stream.online', {'broadcaster_user_id': self.test_user_id}, 'https://example.com/webhook')
        assert result.success
        assert 'subscription' in result.data
        subscription = result.data['subscription']
        assert subscription.subscription_id == 'subscription_123'
        assert subscription.status == 'enabled'
        assert subscription.type == 'stream.online'

    def test_large_response_handling(self):
        """Test handling of large API responses."""
        large_response = {'data': [{'id': f'msg_{i}', 'user_id': f'user_{i}', 'user_login': f'user_{i}', 'user_name': f'User{i}', 'message': f'Message {i}', 'created_at': '2023-01-01T00:00:00Z', 'color': '#FF0000', 'badges': [], 'emotes': [], 'reply_parent_msg_id': None, 'reply_parent_user_id': None, 'reply_parent_user_login': None, 'reply_parent_user_name': None, 'reply_parent_msg_body': None, 'thread_parent_msg_id': None, 'thread_parent_user_login': None, 'thread_parent_user_name': None, 'thread_parent_msg_body': None} for i in range(1000)], 'pagination': {'cursor': 'next_cursor_token'}}
        mock_response = Mock()
        mock_response.json.return_value = large_response
        mock_response.status_code = 200
        with patch('requests.get', return_value=mock_response):
            result = self.client.get_chat_messages(self.test_user_id, limit=1000)
        assert result.success
        messages = result.data['messages']
        assert len(messages) == 1000
        assert all((message.message.startswith('Message ') for message in messages))
if __name__ == '__main__':
    pytest.main([__file__])