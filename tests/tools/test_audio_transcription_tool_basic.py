"""Basic tests for AudioTranscriptionTool."""
from unittest.mock import patch
import pytest
from platform.core.step_result import StepResult
from domains.ingestion.providers.audio_transcription_tool import AudioTranscriptionTool

class TestAudioTranscriptionTool:
    """Test cases for AudioTranscriptionTool."""

    @pytest.fixture
    def tool(self):
        """Create AudioTranscriptionTool instance."""
        return AudioTranscriptionTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == 'Enhanced Whisper Audio Transcription'
        assert 'transcribe' in tool.description.lower()

    def test_run_with_missing_file(self, tool):
        """Test transcription with missing file."""
        with patch('os.path.exists', return_value=False):
            result = tool._run('nonexistent.mp4')
            assert not result.success
            assert 'not found' in result.error.lower()

    def test_run_with_valid_file_basic(self, tool):
        """Test basic transcription functionality."""
        with patch('os.path.exists', return_value=True):
            result = tool._run('test_audio.mp4')
            assert isinstance(result, StepResult)

    def test_cache_initialization(self, tool):
        """Test cache initialization."""
        tool_with_cache = AudioTranscriptionTool(enable_caching=True)
        assert tool_with_cache._cache is not None
        tool_without_cache = AudioTranscriptionTool(enable_caching=False)
        assert tool_without_cache._cache is None

    def test_model_id_configuration(self, tool):
        """Test model ID configuration."""
        assert 'distil-whisper' in tool._model_id
        custom_tool = AudioTranscriptionTool(model_id='custom-model')
        assert custom_tool._model_id == 'custom-model'

    def test_device_configuration(self, tool):
        """Test device configuration."""
        assert tool._device in ['cpu', 'cuda:0']
        custom_tool = AudioTranscriptionTool(device='cpu')
        assert custom_tool._device == 'cpu'

    def test_chunk_length_configuration(self, tool):
        """Test chunk length configuration."""
        assert tool._chunk_length_s == 30
        custom_tool = AudioTranscriptionTool(chunk_length_s=60)
        assert custom_tool._chunk_length_s == 60