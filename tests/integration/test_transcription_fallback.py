"""Integration tests for transcription fallback chain.

Tests the graceful degradation from faster-whisper → whisper → plaintext
when ML dependencies are unavailable.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_audio_file(tmp_path: Path) -> Path:
    """Create a sample audio file for testing."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_text("dummy audio content")
    return audio_file


@pytest.fixture
def sample_plaintext_transcript(tmp_path: Path) -> Path:
    """Create a plaintext transcript file for fallback testing."""
    transcript_file = tmp_path / "test_transcript.txt"
    transcript_file.write_text("This is line one.\nThis is line two.\nThis is line three.")
    return transcript_file


def test_transcription_fallback_to_plaintext_when_whisper_unavailable(
    sample_plaintext_transcript: Path,
) -> None:
    """Test that transcription falls back to plaintext when whisper is unavailable."""
    # Import the transcribe module
    from domains.intelligence.analysis.transcribe import run_whisper

    # Mock whisper and faster_whisper as unavailable
    with (
        patch.dict(sys.modules, {"whisper": None, "faster_whisper": None}),
        patch("domains.intelligence.analysis.transcribe.record_degradation") as mock_degradation,
    ):
        # Run transcription - should fall back to plaintext
        result = run_whisper(str(sample_plaintext_transcript))

        # Verify plaintext fallback was used
        assert len(result.segments) == 3
        assert result.segments[0].text == "This is line one."
        assert result.segments[1].text == "This is line two."
        assert result.segments[2].text == "This is line three."

        # Verify degradation was recorded
        assert mock_degradation.call_count >= 1
        call_kwargs = mock_degradation.call_args[1]
        assert call_kwargs["component"] == "transcribe"
        assert "whisper" in call_kwargs["event_type"].lower()


def test_transcription_returns_segments_structure() -> None:
    """Test that transcription returns proper Segment structure."""
    from domains.intelligence.analysis.transcribe import Segment, Transcript

    # Create manual transcript
    segments = [
        Segment(start=0.0, end=5.0, text="First segment"),
        Segment(start=5.0, end=10.0, text="Second segment"),
    ]
    transcript = Transcript(segments=segments)

    # Verify structure
    assert len(transcript.segments) == 2
    assert transcript.segments[0].start == 0.0
    assert transcript.segments[0].end == 5.0
    assert transcript.segments[0].text == "First segment"


def test_ml_feature_stub_raises_helpful_error() -> None:
    """Test that ML feature stubs provide helpful error messages."""
    from ultimate_discord_intelligence_bot.creator_ops.media import WhisperASR

    # If whisper is actually available, skip this test
    if not callable(WhisperASR):
        pytest.skip("WhisperASR is actually available (ML deps installed)")

    # Try to instantiate stub - should raise helpful error
    with pytest.raises(RuntimeError) as exc_info:
        WhisperASR()

    error_message = str(exc_info.value)
    assert "WhisperASR requires ML dependencies" in error_message
    assert "pip install -e '.[ml]'" in error_message
    assert "torch" in error_message or "whisper" in error_message


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Degradation recording may differ on Windows",
)
def test_degradation_recording_called_on_fallback(sample_plaintext_transcript: Path) -> None:
    """Verify that degradation is properly recorded when falling back."""
    from domains.intelligence.analysis.transcribe import run_whisper

    with (
        patch.dict(sys.modules, {"whisper": None, "faster_whisper": None}),
        patch("domains.intelligence.analysis.transcribe.record_degradation") as mock_degradation,
    ):
        run_whisper(str(sample_plaintext_transcript))

        # Should record degradation for whisper fallback
        degradation_calls = [call[1] for call in mock_degradation.call_args_list]
        assert any("whisper" in call.get("event_type", "").lower() for call in degradation_calls)
        assert any(call.get("severity") == "warn" for call in degradation_calls)
