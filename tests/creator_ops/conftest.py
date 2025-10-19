"""
Simple pytest configuration for Creator Operations tests.

Provides basic fixtures without heavy dependencies.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


@pytest.fixture
def test_tenant():
    """Provide test tenant."""
    return "test_tenant"


@pytest.fixture
def test_workspace():
    """Provide test workspace."""
    return "test_workspace"


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
    oauth_manager.get_valid_token.return_value = StepResult.ok(data={"access_token": "valid_token"})
    oauth_manager.refresh_token.return_value = StepResult.ok(data={"access_token": "refreshed_token"})
    return oauth_manager


@pytest.fixture
def mock_circuit_breaker():
    """Provide mock circuit breaker."""
    circuit_breaker = Mock()
    circuit_breaker.call.return_value = "success"
    circuit_breaker.state = "closed"
    return circuit_breaker


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
            {"start_time": 0, "end_time": 300, "text": "Introduction segment", "speaker": "SPEAKER_00"},
            {"start_time": 300, "end_time": 900, "text": "Main content segment 1", "speaker": "SPEAKER_01"},
        ],
        "metadata": {
            "channel_id": "test_channel",
            "platform": "youtube",
            "published_at": datetime.now().isoformat(),
            "view_count": 100000,
            "like_count": 5000,
            "comment_count": 500,
            "engagement_rate": 0.055,
        },
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
            "engagement": 150,
        },
        {
            "message_id": "msg_2",
            "user_id": "user_2",
            "user_name": "Viewer2",
            "message": "EPIC moment!",
            "created_at": datetime.now(),
            "sentiment": 0.8,
            "engagement": 120,
        },
    ]


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Set up test logging."""
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "chaos: mark test as chaos test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
