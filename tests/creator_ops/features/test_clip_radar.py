"""
Integration tests for Clip Radar feature.

Tests cover:
- Live stream monitoring and moment detection
- Clip creation and metadata extraction
- Integration with Twitch and YouTube APIs
- End-to-end workflow validation
- Error handling and edge cases
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestClipRadar:
    """Test suite for Clip Radar feature functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ClipRadarConfig(
            enabled=True,
            check_interval=30,
            moment_threshold=0.8,
            min_clip_duration=10,
            max_clip_duration=60,
            platforms=["twitch", "youtube"],
            keywords=["hype", "epic", "amazing", "wow"],
            sentiment_threshold=0.7,
            engagement_threshold=100,
            auto_create_clips=True,
            notification_webhook="https://example.com/webhook",
        )
        self.clip_radar = ClipRadar(config=self.config)

    def test_initialization(self):
        """Test Clip Radar initialization."""
        assert self.clip_radar.config.enabled is True
        assert self.clip_radar.config.check_interval == 30
        assert self.clip_radar.config.moment_threshold == 0.8
        assert "twitch" in self.clip_radar.config.platforms
        assert "youtube" in self.clip_radar.config.platforms

    def test_start_monitoring_success(self):
        """Test successful monitoring start."""
        with patch.object(self.clip_radar, "_start_monitoring_thread") as mock_start:
            result = self.clip_radar.start_monitoring("test_user")

        assert result.success
        assert "monitoring_started" in result.data
        mock_start.assert_called_once_with("test_user")

    def test_stop_monitoring_success(self):
        """Test successful monitoring stop."""
        # Start monitoring first
        self.clip_radar._monitoring_active = True
        self.clip_radar._monitoring_thread = Mock()

        with patch.object(self.clip_radar._monitoring_thread, "join") as mock_join:
            result = self.clip_radar.stop_monitoring()

        assert result.success
        assert "monitoring_stopped" in result.data
        assert self.clip_radar._monitoring_active is False
        mock_join.assert_called_once()

    def test_detect_moment_success(self):
        """Test successful moment detection."""
        # Mock stream data
        stream_data = {
            "stream_id": "12345",
            "title": "Epic Gaming Session",
            "viewer_count": 1000,
            "chat_rate": 50,
            "timestamp": datetime.now(),
        }

        # Mock chat messages with high engagement
        chat_messages = [
            {"message": "This is AMAZING!", "sentiment": 0.9, "engagement": 150},
            {"message": "EPIC moment!", "sentiment": 0.8, "engagement": 120},
            {
                "message": "WOW that was incredible!",
                "sentiment": 0.95,
                "engagement": 200,
            },
        ]

        with patch.object(self.clip_radar, "_analyze_chat_engagement") as mock_analyze:
            mock_analyze.return_value = {
                "avg_sentiment": 0.88,
                "total_engagement": 470,
                "keyword_matches": 3,
                "moment_score": 0.9,
            }

            result = self.clip_radar.detect_moment(stream_data, chat_messages)

        assert result.success
        assert "moment" in result.data
        moment = result.data["moment"]
        assert isinstance(moment, ClipMoment)
        assert moment.moment_score >= self.config.moment_threshold
        assert moment.timestamp is not None

    def test_detect_moment_low_engagement(self):
        """Test moment detection with low engagement."""
        stream_data = {
            "stream_id": "12345",
            "title": "Quiet Stream",
            "viewer_count": 100,
            "chat_rate": 5,
            "timestamp": datetime.now(),
        }

        chat_messages = [
            {"message": "hello", "sentiment": 0.5, "engagement": 10},
            {"message": "hi there", "sentiment": 0.4, "engagement": 8},
        ]

        with patch.object(self.clip_radar, "_analyze_chat_engagement") as mock_analyze:
            mock_analyze.return_value = {
                "avg_sentiment": 0.45,
                "total_engagement": 18,
                "keyword_matches": 0,
                "moment_score": 0.3,
            }

            result = self.clip_radar.detect_moment(stream_data, chat_messages)

        assert result.success
        assert "moment" in result.data
        moment = result.data["moment"]
        assert moment.moment_score < self.config.moment_threshold
        assert not moment.is_clipworthy

    def test_create_clip_success(self):
        """Test successful clip creation."""
        moment = ClipMoment(
            moment_id="moment_123",
            stream_id="12345",
            timestamp=datetime.now(),
            moment_score=0.9,
            title="Epic Gaming Moment",
            description="Amazing gameplay sequence",
            start_time=120.0,
            end_time=150.0,
            keywords=["epic", "amazing"],
            sentiment_score=0.85,
            engagement_score=200,
            is_clipworthy=True,
        )

        with patch.object(self.clip_radar, "_create_twitch_clip") as mock_twitch:
            mock_twitch.return_value = StepResult.ok(
                data={"clip_id": "clip_123", "url": "https://clips.twitch.tv/clip_123"}
            )

            result = self.clip_radar.create_clip(moment, platform="twitch")

        assert result.success
        assert "clip" in result.data
        clip = result.data["clip"]
        assert clip["clip_id"] == "clip_123"
        assert clip["url"] == "https://clips.twitch.tv/clip_123"

    def test_create_clip_platform_not_supported(self):
        """Test clip creation with unsupported platform."""
        moment = ClipMoment(
            moment_id="moment_123",
            stream_id="12345",
            timestamp=datetime.now(),
            moment_score=0.9,
            title="Epic Moment",
            description="Test moment",
            start_time=120.0,
            end_time=150.0,
            keywords=["epic"],
            sentiment_score=0.85,
            engagement_score=200,
            is_clipworthy=True,
        )

        result = self.clip_radar.create_clip(moment, platform="unsupported_platform")

        assert not result.success
        assert "Unsupported platform" in result.error

    def test_create_clip_twitch_error(self):
        """Test clip creation with Twitch API error."""
        moment = ClipMoment(
            moment_id="moment_123",
            stream_id="12345",
            timestamp=datetime.now(),
            moment_score=0.9,
            title="Epic Moment",
            description="Test moment",
            start_time=120.0,
            end_time=150.0,
            keywords=["epic"],
            sentiment_score=0.85,
            engagement_score=200,
            is_clipworthy=True,
        )

        with patch.object(self.clip_radar, "_create_twitch_clip") as mock_twitch:
            mock_twitch.return_value = StepResult.fail("Twitch API error")

            result = self.clip_radar.create_clip(moment, platform="twitch")

        assert not result.success
        assert "Twitch API error" in result.error

    def test_analyze_chat_engagement_success(self):
        """Test chat engagement analysis."""
        chat_messages = [
            {"message": "This is AMAZING!", "sentiment": 0.9, "engagement": 150},
            {"message": "EPIC moment!", "sentiment": 0.8, "engagement": 120},
            {
                "message": "WOW that was incredible!",
                "sentiment": 0.95,
                "engagement": 200,
            },
            {"message": "hello", "sentiment": 0.5, "engagement": 10},
        ]

        result = self.clip_radar._analyze_chat_engagement(chat_messages)

        assert "avg_sentiment" in result
        assert "total_engagement" in result
        assert "keyword_matches" in result
        assert "moment_score" in result

        # Should detect keywords
        assert result["keyword_matches"] >= 3
        # Should have high sentiment
        assert result["avg_sentiment"] > 0.7
        # Should have high engagement
        assert result["total_engagement"] > 400

    def test_analyze_chat_engagement_empty_messages(self):
        """Test chat engagement analysis with empty messages."""
        result = self.clip_radar._analyze_chat_engagement([])

        assert result["avg_sentiment"] == 0.0
        assert result["total_engagement"] == 0
        assert result["keyword_matches"] == 0
        assert result["moment_score"] == 0.0

    def test_calculate_moment_score(self):
        """Test moment score calculation."""
        engagement_data = {
            "avg_sentiment": 0.85,
            "total_engagement": 300,
            "keyword_matches": 5,
            "moment_score": 0.0,  # Will be calculated
        }

        stream_data = {"viewer_count": 1000, "chat_rate": 50}

        score = self.clip_radar._calculate_moment_score(engagement_data, stream_data)

        # Should be high score due to good metrics
        assert score > 0.7
        assert score <= 1.0

    def test_calculate_moment_score_low_metrics(self):
        """Test moment score calculation with low metrics."""
        engagement_data = {
            "avg_sentiment": 0.3,
            "total_engagement": 20,
            "keyword_matches": 0,
            "moment_score": 0.0,
        }

        stream_data = {"viewer_count": 50, "chat_rate": 2}

        score = self.clip_radar._calculate_moment_score(engagement_data, stream_data)

        # Should be low score due to poor metrics
        assert score < 0.3

    def test_monitoring_workflow_e2e(self):
        """Test end-to-end monitoring workflow."""
        user_id = "test_user"

        # Mock stream data
        stream_data = {
            "stream_id": "12345",
            "title": "Epic Gaming Session",
            "viewer_count": 1000,
            "chat_rate": 50,
            "timestamp": datetime.now(),
            "is_live": True,
        }

        # Mock chat messages
        chat_messages = [
            {"message": "This is AMAZING!", "sentiment": 0.9, "engagement": 150},
            {"message": "EPIC moment!", "sentiment": 0.8, "engagement": 120},
            {
                "message": "WOW that was incredible!",
                "sentiment": 0.95,
                "engagement": 200,
            },
        ]

        with patch.object(self.clip_radar, "_get_stream_data") as mock_stream:
            with patch.object(self.clip_radar, "_get_chat_messages") as mock_chat:
                with patch.object(self.clip_radar, "_analyze_chat_engagement") as mock_analyze:
                    with patch.object(self.clip_radar, "_create_twitch_clip") as mock_clip:
                        mock_stream.return_value = StepResult.ok(data=stream_data)
                        mock_chat.return_value = StepResult.ok(data=chat_messages)
                        mock_analyze.return_value = {
                            "avg_sentiment": 0.88,
                            "total_engagement": 470,
                            "keyword_matches": 3,
                            "moment_score": 0.9,
                        }
                        mock_clip.return_value = StepResult.ok(
                            data={
                                "clip_id": "clip_123",
                                "url": "https://clips.twitch.tv/clip_123",
                            }
                        )

                        # Start monitoring
                        result = self.clip_radar.start_monitoring(user_id)
                        assert result.success

                        # Simulate monitoring cycle
                        result = self.clip_radar._monitoring_cycle(user_id)
                        assert result.success

    def test_notification_webhook_success(self):
        """Test successful notification webhook."""
        clip_data = {
            "clip_id": "clip_123",
            "url": "https://clips.twitch.tv/clip_123",
            "title": "Epic Moment",
            "moment_score": 0.9,
            "timestamp": datetime.now().isoformat(),
        }

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            result = self.clip_radar._send_notification(clip_data)

        assert result.success
        mock_post.assert_called_once_with(
            self.config.notification_webhook,
            json=clip_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

    def test_notification_webhook_failure(self):
        """Test notification webhook failure."""
        clip_data = {
            "clip_id": "clip_123",
            "url": "https://clips.twitch.tv/clip_123",
            "title": "Epic Moment",
            "moment_score": 0.9,
            "timestamp": datetime.now().isoformat(),
        }

        with patch("requests.post") as mock_post:
            mock_post.side_effect = Exception("Webhook error")

            result = self.clip_radar._send_notification(clip_data)

        assert not result.success
        assert "Webhook error" in result.error

    def test_concurrent_moment_detection(self):
        """Test concurrent moment detection."""
        import threading

        results = []
        errors = []

        def detect_moment_worker(stream_id):
            try:
                stream_data = {
                    "stream_id": stream_id,
                    "title": f"Stream {stream_id}",
                    "viewer_count": 1000,
                    "chat_rate": 50,
                    "timestamp": datetime.now(),
                }

                chat_messages = [
                    {
                        "message": "This is AMAZING!",
                        "sentiment": 0.9,
                        "engagement": 150,
                    },
                    {"message": "EPIC moment!", "sentiment": 0.8, "engagement": 120},
                ]

                with patch.object(self.clip_radar, "_analyze_chat_engagement") as mock_analyze:
                    mock_analyze.return_value = {
                        "avg_sentiment": 0.85,
                        "total_engagement": 270,
                        "keyword_matches": 2,
                        "moment_score": 0.8,
                    }

                    result = self.clip_radar.detect_moment(stream_data, chat_messages)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=detect_moment_worker, args=(f"stream_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests succeeded
        assert len(results) == 3
        assert len(errors) == 0
        assert all(result.success for result in results)

    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid configuration
        invalid_config = ClipRadarConfig(
            enabled=True,
            check_interval=-1,  # Invalid
            moment_threshold=2.0,  # Invalid (> 1.0)
            min_clip_duration=100,  # Invalid (> max_clip_duration)
            max_clip_duration=60,
            platforms=[],  # Invalid (empty)
            keywords=[],
            sentiment_threshold=0.7,
            engagement_threshold=100,
            auto_create_clips=True,
            notification_webhook="invalid_url",
        )

        clip_radar = ClipRadar(config=invalid_config)
        result = clip_radar._validate_config()

        assert not result.success
        assert "Invalid configuration" in result.error

    def test_platform_integration_twitch(self):
        """Test Twitch platform integration."""
        with patch.object(self.clip_radar, "_create_twitch_clip") as mock_twitch:
            mock_twitch.return_value = StepResult.ok(
                data={"clip_id": "clip_123", "url": "https://clips.twitch.tv/clip_123"}
            )

            moment = ClipMoment(
                moment_id="moment_123",
                stream_id="12345",
                timestamp=datetime.now(),
                moment_score=0.9,
                title="Epic Moment",
                description="Test moment",
                start_time=120.0,
                end_time=150.0,
                keywords=["epic"],
                sentiment_score=0.85,
                engagement_score=200,
                is_clipworthy=True,
            )

            result = self.clip_radar._create_twitch_clip(moment)

            assert result.success
            assert "clip_id" in result.data
            assert "url" in result.data

    def test_platform_integration_youtube(self):
        """Test YouTube platform integration."""
        with patch.object(self.clip_radar, "_create_youtube_clip") as mock_youtube:
            mock_youtube.return_value = StepResult.ok(
                data={
                    "clip_id": "clip_456",
                    "url": "https://youtube.com/watch?v=clip_456",
                }
            )

            moment = ClipMoment(
                moment_id="moment_123",
                stream_id="67890",
                timestamp=datetime.now(),
                moment_score=0.9,
                title="Epic Moment",
                description="Test moment",
                start_time=120.0,
                end_time=150.0,
                keywords=["epic"],
                sentiment_score=0.85,
                engagement_score=200,
                is_clipworthy=True,
            )

            result = self.clip_radar._create_youtube_clip(moment)

            assert result.success
            assert "clip_id" in result.data
            assert "url" in result.data


if __name__ == "__main__":
    pytest.main([__file__])
