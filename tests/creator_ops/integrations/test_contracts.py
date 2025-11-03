"""
Contract tests for platform API integrations.
Tests that API responses match expected schemas and behaviors.
"""

from platform.core.step_result import StepResult
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.instagram_client import InstagramClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.tiktok_client import TikTokClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_client import TwitchClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.x_client import XClient
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import YouTubeClient


class TestYouTubeContract:
    """Contract tests for YouTube API integration."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def oauth_manager(self):
        manager = Mock()
        manager.get_access_token.return_value = StepResult.ok("mock_token")
        return manager

    @pytest.fixture
    def client(self, config, oauth_manager):
        return YouTubeClient(config=config, oauth_manager=oauth_manager)

    def test_get_video_info_contract(self, client):
        """Test that get_video_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": "test_video_id",
                            "snippet": {
                                "title": "Test Video",
                                "description": "Test Description",
                                "channelId": "test_channel_id",
                                "channelTitle": "Test Channel",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                            },
                            "statistics": {"viewCount": "1000", "likeCount": "100", "commentCount": "50"},
                        }
                    ]
                }
            )
            result = client.get_video_info("test_video_id")
            assert result.success
            assert "video_id" in result.data
            assert "title" in result.data
            assert "description" in result.data
            assert "channel_id" in result.data
            assert "channel_title" in result.data
            assert "published_at" in result.data
            assert "thumbnail_url" in result.data
            assert "view_count" in result.data
            assert "like_count" in result.data
            assert "comment_count" in result.data

    def test_get_channel_info_contract(self, client):
        """Test that get_channel_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": "test_channel_id",
                            "snippet": {
                                "title": "Test Channel",
                                "description": "Test Channel Description",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "thumbnails": {"default": {"url": "https://example.com/channel_thumb.jpg"}},
                            },
                            "statistics": {"subscriberCount": "10000", "videoCount": "100", "viewCount": "1000000"},
                        }
                    ]
                }
            )
            result = client.get_channel_info("test_channel_id")
            assert result.success
            assert "channel_id" in result.data
            assert "title" in result.data
            assert "description" in result.data
            assert "published_at" in result.data
            assert "thumbnail_url" in result.data
            assert "subscriber_count" in result.data
            assert "video_count" in result.data
            assert "view_count" in result.data

    def test_get_video_comments_contract(self, client):
        """Test that get_video_comments returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": "comment_id",
                            "snippet": {
                                "topLevelComment": {
                                    "snippet": {
                                        "textDisplay": "Test comment",
                                        "authorDisplayName": "Test User",
                                        "publishedAt": "2023-01-01T00:00:00Z",
                                        "likeCount": 5,
                                    }
                                }
                            },
                        }
                    ]
                }
            )
            result = client.get_video_comments("test_video_id")
            assert result.success
            assert "comments" in result.data
            assert len(result.data["comments"]) > 0
            comment = result.data["comments"][0]
            assert "comment_id" in comment
            assert "text" in comment
            assert "author_name" in comment
            assert "published_at" in comment
            assert "like_count" in comment

    def test_get_video_captions_contract(self, client):
        """Test that get_video_captions returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": "caption_id",
                            "snippet": {
                                "language": "en",
                                "name": "English",
                                "isDraft": False,
                                "isAutoGenerated": False,
                            },
                        }
                    ]
                }
            )
            result = client.get_video_captions("test_video_id")
            assert result.success
            assert "captions" in result.data
            assert len(result.data["captions"]) > 0
            caption = result.data["captions"][0]
            assert "caption_id" in caption
            assert "language" in caption
            assert "name" in caption
            assert "is_draft" in caption
            assert "is_auto_generated" in caption

    def test_search_videos_contract(self, client):
        """Test that search_videos returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": {"videoId": "test_video_id"},
                            "snippet": {
                                "title": "Test Video",
                                "description": "Test Description",
                                "channelId": "test_channel_id",
                                "channelTitle": "Test Channel",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                            },
                        }
                    ]
                }
            )
            result = client.search_videos("test query")
            assert result.success
            assert "videos" in result.data
            assert len(result.data["videos"]) > 0
            video = result.data["videos"][0]
            assert "video_id" in video
            assert "title" in video
            assert "description" in video
            assert "channel_id" in video
            assert "channel_title" in video
            assert "published_at" in video
            assert "thumbnail_url" in video

    def test_get_live_chat_messages_contract(self, client):
        """Test that get_live_chat_messages returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "items": [
                        {
                            "id": "message_id",
                            "snippet": {
                                "type": "textMessageEvent",
                                "liveChatId": "live_chat_id",
                                "authorChannelId": "author_channel_id",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "textMessageDetails": {"messageText": "Test message"},
                            },
                            "authorDetails": {
                                "channelId": "author_channel_id",
                                "displayName": "Test User",
                                "isChatModerator": False,
                                "isChatOwner": False,
                                "isChatSponsor": False,
                                "isVerified": False,
                            },
                        }
                    ]
                }
            )
            result = client.get_live_chat_messages("live_chat_id")
            assert result.success
            assert "messages" in result.data
            assert len(result.data["messages"]) > 0
            message = result.data["messages"][0]
            assert "message_id" in message
            assert "text" in message
            assert "author_name" in message
            assert "author_channel_id" in message
            assert "published_at" in message
            assert "is_moderator" in message
            assert "is_owner" in message
            assert "is_sponsor" in message


class TestTwitchContract:
    """Contract tests for Twitch API integration."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def oauth_manager(self):
        manager = Mock()
        manager.get_access_token.return_value = StepResult.ok("mock_token")
        return manager

    @pytest.fixture
    def client(self, config, oauth_manager):
        return TwitchClient(config=config, oauth_manager=oauth_manager)

    def test_get_user_info_contract(self, client):
        """Test that get_user_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "123456789",
                            "login": "testuser",
                            "display_name": "Test User",
                            "type": "",
                            "broadcaster_type": "partner",
                            "description": "Test description",
                            "profile_image_url": "https://example.com/profile.jpg",
                            "offline_image_url": "https://example.com/offline.jpg",
                            "view_count": 1000000,
                            "created_at": "2023-01-01T00:00:00Z",
                        }
                    ]
                }
            )
            result = client.get_user_info("testuser")
            assert result.success
            assert "user_id" in result.data
            assert "login" in result.data
            assert "display_name" in result.data
            assert "broadcaster_type" in result.data
            assert "description" in result.data
            assert "profile_image_url" in result.data
            assert "offline_image_url" in result.data
            assert "view_count" in result.data
            assert "created_at" in result.data

    def test_get_stream_info_contract(self, client):
        """Test that get_stream_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "stream_id",
                            "user_id": "123456789",
                            "user_login": "testuser",
                            "user_name": "Test User",
                            "game_id": "game_id",
                            "game_name": "Test Game",
                            "type": "live",
                            "title": "Test Stream",
                            "viewer_count": 1000,
                            "started_at": "2023-01-01T00:00:00Z",
                            "language": "en",
                            "thumbnail_url": "https://example.com/thumb.jpg",
                            "tag_ids": ["tag1", "tag2"],
                            "is_mature": False,
                        }
                    ]
                }
            )
            result = client.get_stream_info("testuser")
            assert result.success
            assert "stream_id" in result.data
            assert "user_id" in result.data
            assert "user_login" in result.data
            assert "user_name" in result.data
            assert "game_id" in result.data
            assert "game_name" in result.data
            assert "type" in result.data
            assert "title" in result.data
            assert "viewer_count" in result.data
            assert "started_at" in result.data
            assert "language" in result.data
            assert "thumbnail_url" in result.data
            assert "tag_ids" in result.data
            assert "is_mature" in result.data

    def test_get_video_info_contract(self, client):
        """Test that get_video_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "video_id",
                            "stream_id": "stream_id",
                            "user_id": "123456789",
                            "user_login": "testuser",
                            "user_name": "Test User",
                            "title": "Test Video",
                            "description": "Test description",
                            "created_at": "2023-01-01T00:00:00Z",
                            "published_at": "2023-01-01T00:00:00Z",
                            "url": "https://example.com/video.mp4",
                            "thumbnail_url": "https://example.com/thumb.jpg",
                            "viewable": "public",
                            "view_count": 1000,
                            "language": "en",
                            "type": "archive",
                            "duration": "1h30m45s",
                        }
                    ]
                }
            )
            result = client.get_video_info("video_id")
            assert result.success
            assert "video_id" in result.data
            assert "stream_id" in result.data
            assert "user_id" in result.data
            assert "user_login" in result.data
            assert "user_name" in result.data
            assert "title" in result.data
            assert "description" in result.data
            assert "created_at" in result.data
            assert "published_at" in result.data
            assert "url" in result.data
            assert "thumbnail_url" in result.data
            assert "viewable" in result.data
            assert "view_count" in result.data
            assert "language" in result.data
            assert "type" in result.data
            assert "duration" in result.data

    def test_get_clip_info_contract(self, client):
        """Test that get_clip_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "clip_id",
                            "url": "https://clips.twitch.tv/clip_id",
                            "embed_url": "https://clips.twitch.tv/embed?clip=clip_id",
                            "broadcaster_id": "123456789",
                            "broadcaster_name": "Test User",
                            "creator_id": "987654321",
                            "creator_name": "Clip Creator",
                            "video_id": "video_id",
                            "game_id": "game_id",
                            "title": "Test Clip",
                            "view_count": 1000,
                            "created_at": "2023-01-01T00:00:00Z",
                            "thumbnail_url": "https://example.com/clip_thumb.jpg",
                            "duration": 30,
                        }
                    ]
                }
            )
            result = client.get_clip_info("clip_id")
            assert result.success
            assert "clip_id" in result.data
            assert "url" in result.data
            assert "embed_url" in result.data
            assert "broadcaster_id" in result.data
            assert "broadcaster_name" in result.data
            assert "creator_id" in result.data
            assert "creator_name" in result.data
            assert "video_id" in result.data
            assert "game_id" in result.data
            assert "title" in result.data
            assert "view_count" in result.data
            assert "created_at" in result.data
            assert "thumbnail_url" in result.data
            assert "duration" in result.data

    def test_get_chat_messages_contract(self, client):
        """Test that get_chat_messages returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "message_id",
                            "user_id": "123456789",
                            "user_name": "testuser",
                            "user_login": "testuser",
                            "message": "Test message",
                            "timestamp": "2023-01-01T00:00:00Z",
                            "message_type": "chat",
                            "badges": ["subscriber/6", "premium/1"],
                            "color": "#FF0000",
                            "emotes": ["25:0-4"],
                            "reply_parent_msg_id": None,
                            "reply_parent_user_id": None,
                            "reply_parent_user_login": None,
                            "reply_parent_display_name": None,
                            "reply_parent_msg_body": None,
                            "thread_parent_msg_id": None,
                            "thread_parent_user_login": None,
                            "thread_parent_display_name": None,
                            "thread_parent_msg_body": None,
                        }
                    ]
                }
            )
            result = client.get_chat_messages("channel_id")
            assert result.success
            assert "messages" in result.data
            assert len(result.data["messages"]) > 0
            message = result.data["messages"][0]
            assert "message_id" in message
            assert "user_id" in message
            assert "user_name" in message
            assert "user_login" in message
            assert "message" in message
            assert "timestamp" in message
            assert "message_type" in message
            assert "badges" in message
            assert "color" in message
            assert "emotes" in message


class TestTikTokContract:
    """Contract tests for TikTok API integration."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def oauth_manager(self):
        manager = Mock()
        manager.get_access_token.return_value = StepResult.ok("mock_token")
        return manager

    @pytest.fixture
    def client(self, config, oauth_manager):
        return TikTokClient(config=config, oauth_manager=oauth_manager)

    def test_get_user_info_contract(self, client):
        """Test that get_user_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": {
                        "user": {
                            "open_id": "user_open_id",
                            "union_id": "user_union_id",
                            "avatar_url": "https://example.com/avatar.jpg",
                            "avatar_url_100": "https://example.com/avatar_100.jpg",
                            "avatar_url_200": "https://example.com/avatar_200.jpg",
                            "display_name": "Test User",
                            "bio_description": "Test bio",
                            "profile_deep_link": "https://example.com/profile",
                            "is_verified": True,
                            "follower_count": 10000,
                            "following_count": 1000,
                            "likes_count": 50000,
                            "video_count": 100,
                        }
                    }
                }
            )
            result = client.get_user_info("user_open_id")
            assert result.success
            assert "open_id" in result.data
            assert "union_id" in result.data
            assert "avatar_url" in result.data
            assert "avatar_url_100" in result.data
            assert "avatar_url_200" in result.data
            assert "display_name" in result.data
            assert "bio_description" in result.data
            assert "profile_deep_link" in result.data
            assert "is_verified" in result.data
            assert "follower_count" in result.data
            assert "following_count" in result.data
            assert "likes_count" in result.data
            assert "video_count" in result.data

    def test_get_user_videos_contract(self, client):
        """Test that get_user_videos returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": {
                        "videos": [
                            {
                                "id": "video_id",
                                "create_time": 1672531200,
                                "cover_image_url": "https://example.com/cover.jpg",
                                "share_url": "https://example.com/share",
                                "video_description": "Test video description",
                                "duration": 30,
                                "height": 1920,
                                "width": 1080,
                                "origin_cover_image_url": "https://example.com/origin_cover.jpg",
                                "play_addr": {"url_list": ["https://example.com/video.mp4"]},
                                "ratio": "9:16",
                                "reflow_cover_image_url": "https://example.com/reflow_cover.jpg",
                                "video_id": "video_id",
                                "video_quality": "normal",
                            }
                        ]
                    }
                }
            )
            result = client.get_user_videos("user_open_id")
            assert result.success
            assert "videos" in result.data
            assert len(result.data["videos"]) > 0
            video = result.data["videos"][0]
            assert "video_id" in video
            assert "create_time" in video
            assert "cover_image_url" in video
            assert "share_url" in video
            assert "video_description" in video
            assert "duration" in video
            assert "height" in video
            assert "width" in video
            assert "origin_cover_image_url" in video
            assert "play_addr" in video
            assert "ratio" in video
            assert "reflow_cover_image_url" in video
            assert "video_quality" in video

    def test_get_video_comments_contract(self, client):
        """Test that get_video_comments returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": {
                        "comments": [
                            {
                                "comment_id": "comment_id",
                                "comment": "Test comment",
                                "create_time": 1672531200,
                                "digg_count": 10,
                                "reply_comment_total": 5,
                                "reply_to_comment_id": None,
                                "reply_to_user_id": None,
                                "text_extra": [],
                                "user": {
                                    "avatar_url": "https://example.com/avatar.jpg",
                                    "display_name": "Test User",
                                    "open_id": "user_open_id",
                                    "union_id": "user_union_id",
                                },
                            }
                        ]
                    }
                }
            )
            result = client.get_video_comments("video_id")
            assert result.success
            assert "comments" in result.data
            assert len(result.data["comments"]) > 0
            comment = result.data["comments"][0]
            assert "comment_id" in comment
            assert "comment" in comment
            assert "create_time" in comment
            assert "digg_count" in comment
            assert "reply_comment_total" in comment
            assert "reply_to_comment_id" in comment
            assert "reply_to_user_id" in comment
            assert "text_extra" in comment
            assert "user" in comment
            user = comment["user"]
            assert "avatar_url" in user
            assert "display_name" in user
            assert "open_id" in user
            assert "union_id" in user

    def test_get_video_insights_contract(self, client):
        """Test that get_video_insights returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": {
                        "list": [
                            {
                                "date": "2023-01-01",
                                "video_id": "video_id",
                                "video_title": "Test Video",
                                "video_description": "Test description",
                                "like_count": 1000,
                                "comment_count": 100,
                                "share_count": 50,
                                "view_count": 10000,
                                "profile_views": 500,
                                "video_play_time": 30000,
                                "video_views": 10000,
                                "real_time_result": {
                                    "like_count": 1000,
                                    "comment_count": 100,
                                    "share_count": 50,
                                    "view_count": 10000,
                                },
                            }
                        ]
                    }
                }
            )
            result = client.get_video_insights("user_open_id", "video_id")
            assert result.success
            assert "insights" in result.data
            assert len(result.data["insights"]) > 0
            insight = result.data["insights"][0]
            assert "date" in insight
            assert "video_id" in insight
            assert "video_title" in insight
            assert "video_description" in insight
            assert "like_count" in insight
            assert "comment_count" in insight
            assert "share_count" in insight
            assert "view_count" in insight
            assert "profile_views" in insight
            assert "video_play_time" in insight
            assert "video_views" in insight
            assert "real_time_result" in insight
            real_time = insight["real_time_result"]
            assert "like_count" in real_time
            assert "comment_count" in real_time
            assert "share_count" in real_time
            assert "view_count" in real_time


class TestInstagramContract:
    """Contract tests for Instagram API integration."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def oauth_manager(self):
        manager = Mock()
        manager.get_access_token.return_value = StepResult.ok("mock_token")
        return manager

    @pytest.fixture
    def client(self, config, oauth_manager):
        return InstagramClient(config=config, oauth_manager=oauth_manager)

    def test_get_user_info_contract(self, client):
        """Test that get_user_info returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "id": "17841400000000000",
                    "username": "testuser",
                    "account_type": "BUSINESS",
                    "media_count": 100,
                    "followers_count": 10000,
                    "follows_count": 1000,
                    "name": "Test User",
                    "biography": "Test bio",
                    "website": "https://example.com",
                    "profile_picture_url": "https://example.com/profile.jpg",
                }
            )
            result = client.get_user_info("user_id", "testuser")
            assert result.success
            assert "user_id" in result.data
            assert "username" in result.data
            assert "account_type" in result.data
            assert "media_count" in result.data
            assert "followers_count" in result.data
            assert "follows_count" in result.data
            assert "name" in result.data
            assert "biography" in result.data
            assert "website" in result.data
            assert "profile_picture_url" in result.data

    def test_get_user_media_contract(self, client):
        """Test that get_user_media returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "media_id",
                            "media_type": "IMAGE",
                            "media_url": "https://example.com/media.jpg",
                            "username": "testuser",
                            "timestamp": "2023-01-01T00:00:00+0000",
                            "caption": "Test caption",
                            "permalink": "https://example.com/p/ABC123",
                            "thumbnail_url": "https://example.com/thumb.jpg",
                            "like_count": 1000,
                            "comments_count": 100,
                            "children": {
                                "data": [
                                    {
                                        "id": "child_media_id",
                                        "media_type": "VIDEO",
                                        "media_url": "https://example.com/video.mp4",
                                    }
                                ]
                            },
                        }
                    ]
                }
            )
            result = client.get_user_media("user_id")
            assert result.success
            assert "media" in result.data
            assert len(result.data["media"]) > 0
            media = result.data["media"][0]
            assert "media_id" in media
            assert "media_type" in media
            assert "media_url" in media
            assert "username" in media
            assert "timestamp" in media
            assert "caption" in media
            assert "permalink" in media
            assert "thumbnail_url" in media
            assert "like_count" in media
            assert "comments_count" in media
            assert "children" in media

    def test_get_media_comments_contract(self, client):
        """Test that get_media_comments returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "comment_id",
                            "text": "Test comment",
                            "timestamp": "2023-01-01T00:00:00+0000",
                            "like_count": 5,
                            "media": {"id": "media_id"},
                            "user": {"id": "user_id", "username": "testuser", "account_type": "PERSONAL"},
                            "replies": {
                                "data": [
                                    {
                                        "id": "reply_id",
                                        "text": "Test reply",
                                        "timestamp": "2023-01-01T00:01:00+0000",
                                        "like_count": 2,
                                        "user": {
                                            "id": "reply_user_id",
                                            "username": "replyuser",
                                            "account_type": "PERSONAL",
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                }
            )
            result = client.get_media_comments("media_id")
            assert result.success
            assert "comments" in result.data
            assert len(result.data["comments"]) > 0
            comment = result.data["comments"][0]
            assert "comment_id" in comment
            assert "text" in comment
            assert "timestamp" in comment
            assert "like_count" in comment
            assert "media_id" in comment
            assert "user" in comment
            assert "replies" in comment
            user = comment["user"]
            assert "user_id" in user
            assert "username" in user
            assert "account_type" in user
            replies = comment["replies"]
            assert "data" in replies
            assert len(replies["data"]) > 0
            reply = replies["data"][0]
            assert "reply_id" in reply
            assert "text" in reply
            assert "timestamp" in reply
            assert "like_count" in reply
            assert "user" in reply

    def test_get_user_stories_contract(self, client):
        """Test that get_user_stories returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "story_id",
                            "media_type": "VIDEO",
                            "media_url": "https://example.com/story.mp4",
                            "timestamp": "2023-01-01T00:00:00+0000",
                            "permalink": "https://example.com/s/ABC123",
                            "thumbnail_url": "https://example.com/story_thumb.jpg",
                            "like_count": 100,
                            "comments_count": 10,
                            "reactions": {
                                "data": [{"reaction_type": "like", "user": {"id": "user_id", "username": "testuser"}}]
                            },
                        }
                    ]
                }
            )
            result = client.get_user_stories("user_id")
            assert result.success
            assert "stories" in result.data
            assert len(result.data["stories"]) > 0
            story = result.data["stories"][0]
            assert "story_id" in story
            assert "media_type" in story
            assert "media_url" in story
            assert "timestamp" in story
            assert "permalink" in story
            assert "thumbnail_url" in story
            assert "like_count" in story
            assert "comments_count" in story
            assert "reactions" in story

    def test_get_media_insights_contract(self, client):
        """Test that get_media_insights returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "media_id",
                            "impressions": 10000,
                            "reach": 8000,
                            "likes": 1000,
                            "comments": 100,
                            "saves": 50,
                            "shares": 25,
                            "video_views": 5000,
                            "video_plays": 4500,
                            "profile_visits": 200,
                            "website_clicks": 50,
                            "email_contacts": 10,
                            "phone_call_clicks": 5,
                            "text_message_clicks": 3,
                            "get_directions_clicks": 2,
                            "follows": 15,
                            "unfollows": 5,
                            "engagement": 0.12,
                            "reach_rate": 0.08,
                            "impression_rate": 0.1,
                        }
                    ]
                }
            )
            result = client.get_media_insights("media_id")
            assert result.success
            assert "insights" in result.data
            assert len(result.data["insights"]) > 0
            insight = result.data["insights"][0]
            assert "media_id" in insight
            assert "impressions" in insight
            assert "reach" in insight
            assert "likes" in insight
            assert "comments" in insight
            assert "saves" in insight
            assert "shares" in insight
            assert "video_views" in insight
            assert "video_plays" in insight
            assert "profile_visits" in insight
            assert "website_clicks" in insight
            assert "email_contacts" in insight
            assert "phone_call_clicks" in insight
            assert "text_message_clicks" in insight
            assert "get_directions_clicks" in insight
            assert "follows" in insight
            assert "unfollows" in insight
            assert "engagement" in insight
            assert "reach_rate" in insight
            assert "impression_rate" in insight


class TestXContract:
    """Contract tests for X API integration."""

    @pytest.fixture
    def config(self):
        return Mock(spec=CreatorOpsConfig)

    @pytest.fixture
    def oauth_manager(self):
        manager = Mock()
        manager.get_access_token.return_value = StepResult.ok("mock_token")
        return manager

    @pytest.fixture
    def client(self, config, oauth_manager):
        return XClient(config=config, oauth_manager=oauth_manager)

    def test_get_user_by_username_contract(self, client):
        """Test that get_user_by_username returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": {
                        "id": "1234567890123456789",
                        "username": "testuser",
                        "name": "Test User",
                        "created_at": "2023-01-01T00:00:00.000Z",
                        "description": "Test description",
                        "entities": {
                            "description": {
                                "urls": [
                                    {
                                        "start": 0,
                                        "end": 23,
                                        "url": "https://example.com",
                                        "expanded_url": "https://example.com",
                                        "display_url": "example.com",
                                    }
                                ]
                            }
                        },
                        "location": "Test Location",
                        "pinned_tweet_id": "1234567890123456789",
                        "profile_image_url": "https://example.com/profile.jpg",
                        "protected": False,
                        "public_metrics": {
                            "followers_count": 10000,
                            "following_count": 1000,
                            "tweet_count": 100,
                            "listed_count": 50,
                        },
                        "url": "https://example.com",
                        "verified": True,
                        "verified_type": "blue",
                    }
                },
                Mock(),
            )
            result = client.get_user_by_username("testuser", "testuser")
            assert result.success
            assert "user_id" in result.data
            assert "username" in result.data
            assert "name" in result.data
            assert "created_at" in result.data
            assert "description" in result.data
            assert "entities" in result.data
            assert "location" in result.data
            assert "pinned_tweet_id" in result.data
            assert "profile_image_url" in result.data
            assert "protected" in result.data
            assert "public_metrics" in result.data
            assert "url" in result.data
            assert "verified" in result.data
            assert "verified_type" in result.data

    def test_get_user_tweets_contract(self, client):
        """Test that get_user_tweets returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "1234567890123456789",
                            "text": "Test tweet",
                            "created_at": "2023-01-01T00:00:00.000Z",
                            "author_id": "1234567890123456789",
                            "conversation_id": "1234567890123456789",
                            "in_reply_to_user_id": None,
                            "referenced_tweets": [],
                            "attachments": {
                                "media_keys": ["media_key"],
                                "poll_ids": [],
                                "urls": [
                                    {
                                        "start": 0,
                                        "end": 23,
                                        "url": "https://example.com",
                                        "expanded_url": "https://example.com",
                                        "display_url": "example.com",
                                        "images": [
                                            {"url": "https://example.com/image.jpg", "width": 1200, "height": 630}
                                        ],
                                        "status": 200,
                                        "title": "Test Title",
                                        "description": "Test Description",
                                        "unwound_url": "https://example.com",
                                    }
                                ],
                            },
                            "entities": {
                                "hashtags": [{"start": 0, "end": 9, "tag": "test"}],
                                "mentions": [{"start": 0, "end": 9, "username": "testuser"}],
                                "urls": [
                                    {
                                        "start": 0,
                                        "end": 23,
                                        "url": "https://example.com",
                                        "expanded_url": "https://example.com",
                                        "display_url": "example.com",
                                    }
                                ],
                            },
                            "public_metrics": {
                                "retweet_count": 10,
                                "reply_count": 5,
                                "like_count": 100,
                                "quote_count": 2,
                            },
                            "context_annotations": [
                                {
                                    "domain": {
                                        "id": "domain_id",
                                        "name": "Test Domain",
                                        "description": "Test Domain Description",
                                    },
                                    "entity": {
                                        "id": "entity_id",
                                        "name": "Test Entity",
                                        "description": "Test Entity Description",
                                    },
                                }
                            ],
                            "lang": "en",
                            "source": "Twitter Web App",
                            "withheld": {"copyright": False, "country_codes": []},
                        }
                    ]
                },
                Mock(),
            )
            result = client.get_user_tweets("user_id")
            assert result.success
            assert "tweets" in result.data
            assert len(result.data["tweets"]) > 0
            tweet = result.data["tweets"][0]
            assert "tweet_id" in tweet
            assert "text" in tweet
            assert "created_at" in tweet
            assert "author_id" in tweet
            assert "conversation_id" in tweet
            assert "in_reply_to_user_id" in tweet
            assert "referenced_tweets" in tweet
            assert "attachments" in tweet
            assert "entities" in tweet
            assert "public_metrics" in tweet
            assert "context_annotations" in tweet
            assert "lang" in tweet
            assert "source" in tweet
            assert "withheld" in tweet

    def test_get_tweet_mentions_contract(self, client):
        """Test that get_tweet_mentions returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "1234567890123456789",
                            "text": "@testuser Test mention",
                            "created_at": "2023-01-01T00:00:00.000Z",
                            "author_id": "9876543210987654321",
                            "conversation_id": "1234567890123456789",
                            "in_reply_to_user_id": "1234567890123456789",
                            "referenced_tweets": [{"type": "replied_to", "id": "1234567890123456789"}],
                            "attachments": {"media_keys": [], "poll_ids": [], "urls": []},
                            "entities": {
                                "hashtags": [],
                                "mentions": [{"start": 0, "end": 9, "username": "testuser"}],
                                "urls": [],
                            },
                            "public_metrics": {
                                "retweet_count": 5,
                                "reply_count": 2,
                                "like_count": 50,
                                "quote_count": 1,
                            },
                            "context_annotations": [],
                            "lang": "en",
                            "source": "Twitter Web App",
                            "withheld": {"copyright": False, "country_codes": []},
                        }
                    ]
                },
                Mock(),
            )
            result = client.get_tweet_mentions("user_id")
            assert result.success
            assert "mentions" in result.data
            assert len(result.data["mentions"]) > 0
            mention = result.data["mentions"][0]
            assert "tweet_id" in mention
            assert "text" in mention
            assert "created_at" in mention
            assert "author_id" in mention
            assert "conversation_id" in mention
            assert "in_reply_to_user_id" in mention
            assert "referenced_tweets" in mention
            assert "attachments" in mention
            assert "entities" in mention
            assert "public_metrics" in mention
            assert "context_annotations" in mention
            assert "lang" in mention
            assert "source" in mention
            assert "withheld" in mention

    def test_search_tweets_contract(self, client):
        """Test that search_tweets returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "data": [
                        {
                            "id": "1234567890123456789",
                            "text": "Test search result",
                            "created_at": "2023-01-01T00:00:00.000Z",
                            "author_id": "1234567890123456789",
                            "conversation_id": "1234567890123456789",
                            "in_reply_to_user_id": None,
                            "referenced_tweets": [],
                            "attachments": {"media_keys": [], "poll_ids": [], "urls": []},
                            "entities": {
                                "hashtags": [{"start": 0, "end": 9, "tag": "test"}],
                                "mentions": [],
                                "urls": [],
                            },
                            "public_metrics": {
                                "retweet_count": 20,
                                "reply_count": 10,
                                "like_count": 200,
                                "quote_count": 5,
                            },
                            "context_annotations": [],
                            "lang": "en",
                            "source": "Twitter Web App",
                            "withheld": {"copyright": False, "country_codes": []},
                        }
                    ]
                },
                Mock(),
            )
            result = client.search_tweets("test query")
            assert result.success
            assert "tweets" in result.data
            assert len(result.data["tweets"]) > 0
            tweet = result.data["tweets"][0]
            assert "tweet_id" in tweet
            assert "text" in tweet
            assert "created_at" in tweet
            assert "author_id" in tweet
            assert "conversation_id" in tweet
            assert "in_reply_to_user_id" in tweet
            assert "referenced_tweets" in tweet
            assert "attachments" in tweet
            assert "entities" in tweet
            assert "public_metrics" in tweet
            assert "context_annotations" in tweet
            assert "lang" in tweet
            assert "source" in tweet
            assert "withheld" in tweet

    def test_upload_media_contract(self, client):
        """Test that upload_media returns expected data structure."""
        with patch.object(client, "_make_api_request") as mock_request:
            mock_request.return_value = StepResult.ok(
                {
                    "media_id": "1234567890123456789",
                    "media_id_string": "1234567890123456789",
                    "size": 1024,
                    "expires_after_secs": 3600,
                    "processing_info": {"state": "in_progress", "check_after_secs": 30, "progress_percent": 50},
                },
                Mock(),
            )
            result = client.upload_media("test_file.jpg", "image/jpeg")
            assert result.success
            assert "media_id" in result.data
            assert "media_id_string" in result.data
            assert "size" in result.data
            assert "expires_after_secs" in result.data
            assert "processing_info" in result.data
            processing_info = result.data["processing_info"]
            assert "state" in processing_info
            assert "check_after_secs" in processing_info
            assert "progress_percent" in processing_info
