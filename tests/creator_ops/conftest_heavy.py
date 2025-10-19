"""
Pytest configuration and fixtures for Creator Operations tests.

Provides common fixtures and configuration for all creator_ops tests.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from ultimate_discord_intelligence_bot.creator_ops.integrations.twitch_models import TwitchStream, TwitchUser
from ultimate_discord_intelligence_bot.creator_ops.integrations.youtube_models import YouTubeVideo
from ultimate_discord_intelligence_bot.creator_ops.media.asr import ASRResult, ASRSegment
from ultimate_discord_intelligence_bot.creator_ops.media.diarization import DiarizationResult, SpeakerSegment


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return CreatorOpsConfig(
        youtube_api_key="test_youtube_key",
        twitch_client_id="test_twitch_client_id",
        twitch_client_secret="test_twitch_client_secret",
        openai_api_key="test_openai_key",
        qdrant_url="http://localhost:6333",
        database_url="sqlite:///test.db",
        enable_asr=True,
        enable_diarization=True,
        enable_clip_radar=True,
        enable_repurposing=True,
        log_level="DEBUG"
    )


@pytest.fixture
def test_tenant():
    """Provide test tenant."""
    return "test_tenant"


@pytest.fixture
def test_workspace():
    """Provide test workspace."""
    return "test_workspace"


@pytest.fixture
def sample_youtube_video():
    """Provide sample YouTube video data."""
    return YouTubeVideo(
        video_id="dQw4w9WgXcQ",
        title="Test Video Title",
        description="Test video description",
        channel_id="test_channel_id",
        channel_title="Test Channel",
        published_at=datetime.now(),
        duration=300,
        view_count=1000000,
        like_count=50000,
        comment_count=1000,
        thumbnail_url="https://example.com/thumb.jpg",
        tags=["test", "video"],
        category_id="22",
        language="en",
        country="US"
    )


@pytest.fixture
def sample_twitch_stream():
    """Provide sample Twitch stream data."""
    return TwitchStream(
        stream_id="12345",
        user_id="67890",
        user_login="testuser",
        user_name="TestUser",
        game_id="509658",
        game_name="Just Chatting",
        stream_type="live",
        title="Test Stream Title",
        viewer_count=1000,
        started_at=datetime.now(),
        language="en",
        thumbnail_url="https://example.com/thumb.jpg",
        tag_ids=["6ea6bca4-4712-4ab9-a906-e3336a9d8039"],
        is_mature=False
    )


@pytest.fixture
def sample_twitch_user():
    """Provide sample Twitch user data."""
    return TwitchUser(
        user_id="67890",
        login="testuser",
        display_name="TestUser",
        user_type="",
        broadcaster_type="partner",
        description="Test user description",
        profile_image_url="https://example.com/profile.jpg",
        offline_image_url="https://example.com/offline.jpg",
        view_count=1000000,
        created_at=datetime.now()
    )


@pytest.fixture
def sample_asr_result():
    """Provide sample ASR result."""
    segments = [
        ASRSegment(
            start_time=0.0,
            end_time=5.0,
            text="Hello world",
            confidence=0.95,
            language="en",
            language_probability=0.98,
            no_speech_prob=0.02
        ),
        ASRSegment(
            start_time=5.0,
            end_time=10.0,
            text="This is a test",
            confidence=0.92,
            language="en",
            language_probability=0.98,
            no_speech_prob=0.03
        )
    ]

    return ASRResult(
        text="Hello world This is a test",
        language="en",
        language_probability=0.98,
        segments=segments,
        duration=10.0,
        model_name="base",
        processing_time=2.5
    )


@pytest.fixture
def sample_diarization_result():
    """Provide sample diarization result."""
    segments = [
        SpeakerSegment(
            speaker_id="SPEAKER_00",
            start_time=0.0,
            end_time=5.0,
            duration=5.0
        ),
        SpeakerSegment(
            speaker_id="SPEAKER_01",
            start_time=5.0,
            end_time=10.0,
            duration=5.0
        )
    ]

    return DiarizationResult(
        segments=segments,
        num_speakers=2,
        total_duration=10.0,
        model_name="pyannote/speaker-diarization-3.1",
        processing_time=3.0
    )


@pytest.fixture
def temp_audio_file():
    """Provide temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
        audio_file.write(b"fake_audio_data")
        audio_file_path = audio_file.name

    yield audio_file_path

    # Clean up
    if Path(audio_file_path).exists():
        Path(audio_file_path).unlink()


@pytest.fixture
def temp_video_file():
    """Provide temporary video file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_file:
        video_file.write(b"fake_video_data")
        video_file_path = video_file.name

    yield video_file_path

    # Clean up
    if Path(video_file_path).exists():
        Path(video_file_path).unlink()


@pytest.fixture
def mock_oauth_manager():
    """Provide mock OAuth manager."""
    oauth_manager = Mock()
    oauth_manager.get_valid_token.return_value = Mock(
        success=True,
        data={"access_token": "valid_token"}
    )
    oauth_manager.refresh_token.return_value = Mock(
        success=True,
        data={"access_token": "refreshed_token"}
    )
    return oauth_manager


@pytest.fixture
def mock_circuit_breaker():
    """Provide mock circuit breaker."""
    circuit_breaker = Mock()
    circuit_breaker.call.return_value = "success"
    circuit_breaker.state = "closed"
    return circuit_breaker


@pytest.fixture
def mock_store_manager():
    """Provide mock store manager."""
    store_manager = Mock()
    store_manager.health_check.return_value = Mock(
        success=True,
        data={"status": "healthy"}
    )
    store_manager.add_memory_item.return_value = Mock(
        success=True,
        data={"id": "memory_123"}
    )
    store_manager.get_memory_item.return_value = Mock(
        success=True,
        data={"item": {"id": "memory_123", "content": "test content"}}
    )
    return store_manager


@pytest.fixture
def sample_episode_data():
    """Provide sample episode data."""
    return {
        "episode_id": "episode_123",
        "title": "Test Episode",
        "description": "Test episode description",
        "duration": 3600,
        "transcript": "This is a test episode transcript with multiple segments.",
        "segments": [
            {
                "start_time": 0,
                "end_time": 300,
                "text": "Introduction segment",
                "speaker": "SPEAKER_00"
            },
            {
                "start_time": 300,
                "end_time": 900,
                "text": "Main content segment 1",
                "speaker": "SPEAKER_01"
            },
            {
                "start_time": 900,
                "end_time": 1500,
                "text": "Main content segment 2",
                "speaker": "SPEAKER_00"
            },
            {
                "start_time": 1500,
                "end_time": 1800,
                "text": "Conclusion segment",
                "speaker": "SPEAKER_01"
            }
        ],
        "metadata": {
            "channel_id": "test_channel",
            "platform": "youtube",
            "published_at": datetime.now().isoformat(),
            "view_count": 100000,
            "like_count": 5000,
            "comment_count": 500,
            "engagement_rate": 0.055
        }
    }


@pytest.fixture
def sample_chat_messages():
    """Provide sample chat messages."""
    return [
        {
            "message_id": "msg_1",
            "user_id": "user_1",
            "user_name": "Viewer1",
            "message": "This is AMAZING!",
            "created_at": datetime.now(),
            "sentiment": 0.9,
            "engagement": 150
        },
        {
            "message_id": "msg_2",
            "user_id": "user_2",
            "user_name": "Viewer2",
            "message": "EPIC moment!",
            "created_at": datetime.now(),
            "sentiment": 0.8,
            "engagement": 120
        },
        {
            "message_id": "msg_3",
            "user_id": "user_3",
            "user_name": "Viewer3",
            "message": "WOW that was incredible!",
            "created_at": datetime.now(),
            "sentiment": 0.95,
            "engagement": 200
        },
        {
            "message_id": "msg_4",
            "user_id": "user_4",
            "user_name": "Viewer4",
            "message": "hello",
            "created_at": datetime.now(),
            "sentiment": 0.5,
            "engagement": 10
        }
    ]


@pytest.fixture
def sample_clip_data():
    """Provide sample clip data."""
    return {
        "clip_id": "clip_123",
        "title": "Epic Gaming Moment",
        "description": "Amazing gameplay sequence",
        "url": "https://clips.twitch.tv/clip_123",
        "embed_url": "https://clips.twitch.tv/embed?clip=clip_123",
        "duration": 30.0,
        "view_count": 1000,
        "created_at": datetime.now().isoformat(),
        "platform": "twitch",
        "stream_id": "12345",
        "moment_score": 0.9,
        "keywords": ["epic", "amazing", "gaming"],
        "sentiment_score": 0.85,
        "engagement_score": 200
    }


@pytest.fixture
def sample_short_data():
    """Provide sample short data."""
    return {
        "short_id": "short_1",
        "title": "Introduction Short",
        "description": "Quick intro to the episode",
        "start_time": 0,
        "end_time": 300,
        "duration": 300,
        "format": "vertical",
        "platform": "tiktok",
        "content_score": 0.9,
        "engagement_potential": 0.85,
        "target_audience": "gaming_enthusiasts",
        "hashtags": ["#gaming", "#epic", "#short"]
    }


@pytest.fixture
def sample_intelligence_pack():
    """Provide sample intelligence pack."""
    return {
        "episode_id": "episode_123",
        "summary": "Test episode summary with key insights and highlights.",
        "key_points": [
            "Key insight 1: Important information",
            "Key insight 2: Significant finding",
            "Key insight 3: Notable observation"
        ],
        "topics": ["gaming", "technology", "entertainment"],
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "engagement_score": 0.78,
        "content_quality_score": 0.92,
        "recommendations": [
            "Consider creating more content on this topic",
            "Engage with audience comments",
            "Collaborate with similar creators"
        ],
        "trends": [
            "Gaming content trending up 15%",
            "Technology discussions increasing",
            "Entertainment content performing well"
        ],
        "competitor_analysis": {
            "similar_content_count": 25,
            "average_engagement": 0.65,
            "performance_vs_competitors": "above_average"
        },
        "generated_at": datetime.now().isoformat(),
        "model_version": "1.0",
        "confidence_score": 0.88
    }


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up test logging."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@pytest.fixture
def mock_requests_session():
    """Provide mock requests session."""
    session = Mock()
    session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"data": []}
    )
    session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"success": True}
    )
    return session


@pytest.fixture
def mock_async_context_manager():
    """Provide mock async context manager."""
    context_manager = Mock()
    context_manager.__aenter__ = Mock(return_value=Mock())
    context_manager.__aexit__ = Mock(return_value=None)
    return context_manager


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "chaos: mark test as chaos test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add slow marker to tests that take more than 1 second
        if "chaos" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Add chaos marker to chaos tests
        if "chaos" in item.nodeid:
            item.add_marker(pytest.mark.chaos)
