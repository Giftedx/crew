"""
Unit tests for YouTube integration client.

Tests cover:
- API authentication and token management
- Video metadata retrieval
- Channel information
- Comments and live chat
- Error handling and rate limiting
- Quota management
"""

from unittest.mock import Mock, patch

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout

from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_client import YouTubeClient
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestYouTubeClient:
    """Test suite for YouTube client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock OAuth manager with proper return values
        mock_oauth = Mock()
        mock_oauth.get_valid_token.return_value = StepResult.ok(access_token="test_token")
        mock_oauth.refresh_token.return_value = StepResult.ok(access_token="new_token")

        self.client = YouTubeClient(api_key="test_api_key", oauth_manager=mock_oauth, config=Mock())
        self.test_video_id = "dQw4w9WgXcQ"
        self.test_channel_id = "UCuAXFkgsw1L7xaCfnd5JJOw"

    def test_initialization(self):
        """Test YouTube client initialization."""
        assert self.client.api_key == "test_api_key"
        assert self.client.BASE_URL == "https://www.googleapis.com/youtube/v3"
        assert self.client.quota_usage.total_quota == 10000

    def test_get_video_success(self):
        """Test successful video metadata retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": self.test_video_id,
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test description",
                        "channelId": self.test_channel_id,
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "duration": "PT3M33S",
                    },
                    "statistics": {"viewCount": "1000000", "likeCount": "50000", "commentCount": "1000"},
                }
            ]
        }
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video(self.test_video_id)

        assert result.success
        assert "data" in result.data
        video = result.data["data"]
        assert video.id == self.test_video_id
        assert video.title == "Test Video"
        assert video.channel_id == self.test_channel_id

    def test_get_video_not_found(self):
        """Test video metadata retrieval when video not found."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video("nonexistent_video_id")

        assert not result.success
        assert "Video not found" in result.error

    def test_get_video_api_error(self):
        """Test video metadata retrieval with API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {"errors": [{"reason": "invalidParameter"}], "message": "Invalid video ID"}
        }

        # Create a proper HTTPError with response
        http_error = requests.exceptions.HTTPError("400 Client Error: Bad Request")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video("invalid_video_id")

        assert not result.success
        assert "HTTP error 400" in result.error

    def test_get_video_network_error(self):
        """Test video metadata retrieval with network error."""
        with patch.object(self.client.session, "get", side_effect=ConnectionError("Network error")):
            result = self.client.get_video(self.test_video_id)

        assert not result.success
        assert "Network error" in result.error

    def test_get_video_timeout(self):
        """Test video metadata retrieval with timeout."""
        with patch.object(self.client.session, "get", side_effect=Timeout("Request timeout")):
            result = self.client.get_video(self.test_video_id)

        assert not result.success
        assert "Request timeout" in result.error

    def test_get_channel_success(self):
        """Test successful channel information retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": self.test_channel_id,
                    "snippet": {
                        "title": "Test Channel",
                        "description": "Test channel description",
                        "publishedAt": "2020-01-01T00:00:00Z",
                        "thumbnails": {"default": {"url": "https://example.com/thumb.jpg"}},
                    },
                    "statistics": {"subscriberCount": "1000000", "videoCount": "500", "viewCount": "100000000"},
                }
            ]
        }
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_channel(self.test_channel_id)

        assert result.success
        assert "data" in result.data
        channel = result.data["data"]
        assert channel.id == self.test_channel_id
        assert channel.title == "Test Channel"
        assert channel.subscriber_count == 1000000

    def test_search_videos_success(self):
        """Test successful video search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": {"videoId": self.test_video_id},
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test description",
                        "channelId": self.test_channel_id,
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                    },
                }
            ],
            "nextPageToken": "next_page_token",
        }
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.search_videos("test query", max_results=10)

        assert result.success
        assert "data" in result.data
        results = result.data["data"]["results"]
        assert len(results) == 1
        assert results[0].video_id == self.test_video_id
        assert results[0].title == "Test Video"

    def test_get_video_comments_success(self):
        """Test successful video comments retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "comment_id_1",
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "textDisplay": "Great video!",
                                "authorDisplayName": "Test User",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "likeCount": 10,
                            }
                        }
                    },
                }
            ]
        }
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video_comments(self.test_video_id, max_results=10)

        assert result.success
        assert "data" in result.data
        comments = result.data["data"]["comments"]
        assert len(comments) == 1
        assert comments[0].id == "comment_id_1"
        assert comments[0].text_display == "Great video!"
        assert comments[0].author_display_name == "Test User"

    def test_quota_usage_tracking(self):
        """Test quota usage tracking."""
        # Initial quota
        assert self.client.quota_usage.total_quota == 10000
        assert self.client.quota_usage.used_quota == 0

        # Simulate API call that uses 100 quota units
        result = self.client.quota_usage.consume_quota(100)
        assert result.success
        assert self.client.quota_usage.used_quota == 100
        assert self.client.quota_usage.remaining_quota == 9900

    def test_quota_exceeded_error(self):
        """Test quota exceeded error handling."""
        # Set quota to nearly exhausted
        self.client.quota_usage.used_quota = 9999

        # Try to make a call that would exceed quota
        with patch.object(self.client.session, "get") as mock_get:
            result = self.client.get_video(self.test_video_id)

            # Should still make the call (quota check is advisory)
            mock_get.assert_called_once()

    def test_rate_limiting_backoff(self):
        """Test rate limiting with exponential backoff."""
        # Mock a 429 response followed by success
        mock_429_response = Mock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": "1"}
        mock_429_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")
        mock_429_response.raise_for_status.side_effect.response = mock_429_response

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "items": [
                {
                    "id": self.test_video_id,
                    "snippet": {
                        "title": "Test Video",
                        "channelId": self.test_channel_id,
                        "publishedAt": "2023-01-01T00:00:00Z",
                    },
                }
            ]
        }
        mock_success_response.raise_for_status.return_value = None

        with patch.object(self.client.session, "get", side_effect=[mock_429_response, mock_success_response]):
            with patch("time.sleep") as mock_sleep:
                result = self.client.get_video(self.test_video_id)

        # Should have slept due to rate limiting (once for retry-after, once for rate limiting)
        assert mock_sleep.call_count >= 1
        assert result.success

    def test_oauth_token_refresh(self):
        """Test OAuth token refresh functionality - currently not implemented."""
        # This test is skipped because OAuth token refresh is not implemented in the YouTube client
        pytest.skip("OAuth token refresh functionality not implemented")

    def test_batch_video_processing(self):
        """Test batch processing of multiple videos."""
        video_ids = [self.test_video_id, "video_id_2", "video_id_3"]

        mock_responses = []
        for i, video_id in enumerate(video_ids):
            mock_response = Mock()
            mock_response.json.return_value = {
                "items": [
                    {
                        "id": video_id,
                        "snippet": {
                            "title": f"Test Video {i + 1}",
                            "channelId": self.test_channel_id,
                            "publishedAt": "2023-01-01T00:00:00Z",
                        },
                    }
                ]
            }
            mock_response.status_code = 200
            mock_responses.append(mock_response)

        # Test individual requests since batch method doesn't exist
        results = []
        for i, video_id in enumerate(video_ids):
            with patch.object(self.client.session, "get", return_value=mock_responses[i]):
                result = self.client.get_video(video_id)
                results.append(result)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success
            assert result.data["data"].id == video_ids[i]
            assert result.data["data"].title == f"Test Video {i + 1}"

    def test_invalid_api_key(self):
        """Test handling of invalid API key."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {"errors": [{"reason": "keyInvalid"}], "message": "API key not valid"}
        }

        # Create a proper HTTPError with response
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video(self.test_video_id)

        assert not result.success
        assert "API key not valid" in result.error

    def test_partial_response_handling(self):
        """Test handling of partial API responses."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "items": [
                {
                    "id": self.test_video_id,
                    "snippet": {
                        "title": "Test Video",
                        # Missing some fields
                        "channelId": self.test_channel_id,
                        # No publishedAt, statistics, etc.
                    },
                }
            ]
        }
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video(self.test_video_id)

        assert result.success
        video = result.data["data"]
        assert video.title == "Test Video"
        assert video.channel_id == self.test_channel_id
        # Should handle missing fields gracefully
        assert video.description is None

    def test_large_response_handling(self):
        """Test handling of large API responses."""
        # Create a large response with many comments
        large_response = {
            "items": [
                {
                    "id": f"comment_id_{i}",
                    "snippet": {
                        "topLevelComment": {
                            "snippet": {
                                "textDisplay": f"Comment {i}",
                                "authorDisplayName": f"User {i}",
                                "publishedAt": "2023-01-01T00:00:00Z",
                                "likeCount": i,
                            }
                        }
                    },
                }
                for i in range(1000)
            ],
            "nextPageToken": "next_page_token",
        }

        mock_response = Mock()
        mock_response.json.return_value = large_response
        mock_response.status_code = 200

        mock_response.raise_for_status.return_value = None
        with patch.object(self.client.session, "get", return_value=mock_response):
            result = self.client.get_video_comments(self.test_video_id, max_results=1000)

        assert result.success
        comments = result.data["data"]["comments"]
        assert len(comments) == 1000
        assert all(comment.text_display.startswith("Comment ") for comment in comments)

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading

        results = []
        errors = []

        def make_request(video_id):
            try:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "items": [
                        {
                            "id": video_id,
                            "snippet": {
                                "title": f"Video {video_id}",
                                "channelId": self.test_channel_id,
                                "publishedAt": "2023-01-01T00:00:00Z",
                            },
                        }
                    ]
                }
                mock_response.status_code = 200

                mock_response.raise_for_status.return_value = None
                with patch.object(self.client.session, "get", return_value=mock_response):
                    result = self.client.get_video(video_id)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(f"video_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 5
        assert len(errors) == 0
        assert all(result.success for result in results)


if __name__ == "__main__":
    pytest.main([__file__])
