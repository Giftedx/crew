"""Tests for AudioTranscriptionTool."""

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.acquisition.audio_transcription_tool import AudioTranscriptionTool


class TestAudioTranscriptionTool:
    """Test cases for AudioTranscriptionTool."""

    @pytest.fixture
    def tool(self):
        """Create AudioTranscriptionTool instance."""
        return AudioTranscriptionTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == "Enhanced Whisper Audio Transcription"
        assert "transcribe" in tool.description.lower()

    def test_run_with_valid_audio_path(self, tool):
        """Test transcription with valid audio path."""
        with patch("os.path.exists", return_value=True), patch.object(tool, "transcriber") as mock_transcriber:
            mock_transcriber.return_value = {
                "text": "This is a test transcript",
                "chunks": [{"timestamp": [0.0, 5.0], "text": "This is a test transcript"}],
            }

            result = tool._run("test_audio.mp4")

            assert result.success
            assert "transcript" in result.data
            mock_transcriber.assert_called_once()

    def test_run_with_missing_file(self, tool):
        """Test transcription with missing file."""
        with patch("os.path.exists", return_value=False):
            result = tool._run("nonexistent.mp4")

            assert not result.success
            assert "not found" in result.error.lower()

    def test_run_with_invalid_format(self, tool):
        """Test transcription with invalid audio format."""
        with patch("os.path.exists", return_value=True):
            with patch.object(tool, "_transcribe_audio") as mock_transcribe:
                mock_transcribe.side_effect = Exception("Unsupported format")

                result = tool._run("invalid.txt")

                assert not result.success
                assert "format" in result.error.lower()

    def test_transcribe_audio_success(self, tool):
        """Test successful audio transcription."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='{"text": "Transcribed text", "confidence": 0.9}')

            result = tool._transcribe_audio("test.mp4")

            assert result.success
            assert result.data["transcript"] == "Transcribed text"
            assert result.data["confidence"] == 0.9

    def test_transcribe_audio_failure(self, tool):
        """Test audio transcription failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stderr="Transcription failed")

            result = tool._transcribe_audio("test.mp4")

            assert not result.success
            assert "failed" in result.error.lower()

    def test_validate_audio_file(self, tool):
        """Test audio file validation."""
        # Test valid file
        with patch("os.path.exists", return_value=True):
            assert tool._validate_audio_file("test.mp4") is True

        # Test missing file
        with patch("os.path.exists", return_value=False):
            assert tool._validate_audio_file("missing.mp4") is False

    def test_extract_metadata(self, tool):
        """Test metadata extraction."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout='{"duration": 120, "format": "mp4"}')

            metadata = tool._extract_metadata("test.mp4")

            assert metadata["duration"] == 120
            assert metadata["format"] == "mp4"

    def test_handle_transcription_error(self, tool):
        """Test error handling in transcription."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("whisper not found")

            result = tool._transcribe_audio("test.mp4")

            assert not result.success
            assert "whisper" in result.error.lower()
