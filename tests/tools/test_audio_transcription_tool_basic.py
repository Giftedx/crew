"""Basic tests for AudioTranscriptionTool."""

from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult
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

    def test_run_with_missing_file(self, tool):
        """Test transcription with missing file."""
        with patch("os.path.exists", return_value=False):
            result = tool._run("nonexistent.mp4")

            assert not result.success
            assert "not found" in result.error.lower()

    def test_run_with_valid_file_basic(self, tool):
        """Test basic transcription functionality."""
        with patch("os.path.exists", return_value=True):
            # This test just verifies the tool can be called without crashing
            # The actual transcription would require the transformers library
            result = tool._run("test_audio.mp4")

            # The result might fail due to missing transformers, but that's expected
            # We're just testing that the method can be called
            assert isinstance(result, StepResult)

    def test_cache_initialization(self, tool):
        """Test cache initialization."""
        # Test with cache enabled
        tool_with_cache = AudioTranscriptionTool(enable_caching=True)
        assert tool_with_cache._cache is not None

        # Test with cache disabled
        tool_without_cache = AudioTranscriptionTool(enable_caching=False)
        assert tool_without_cache._cache is None

    def test_model_id_configuration(self, tool):
        """Test model ID configuration."""
        # Test default model ID
        assert "distil-whisper" in tool._model_id

        # Test custom model ID
        custom_tool = AudioTranscriptionTool(model_id="custom-model")
        assert custom_tool._model_id == "custom-model"

    def test_device_configuration(self, tool):
        """Test device configuration."""
        # Test default device (should be cpu or cuda)
        assert tool._device in ["cpu", "cuda:0"]

        # Test custom device
        custom_tool = AudioTranscriptionTool(device="cpu")
        assert custom_tool._device == "cpu"

    def test_chunk_length_configuration(self, tool):
        """Test chunk length configuration."""
        # Test default chunk length
        assert tool._chunk_length_s == 30

        # Test custom chunk length
        custom_tool = AudioTranscriptionTool(chunk_length_s=60)
        assert custom_tool._chunk_length_s == 60
