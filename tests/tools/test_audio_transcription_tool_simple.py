"""Simplified tests for AudioTranscriptionTool."""
from unittest.mock import patch
import pytest
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

    def test_run_with_valid_file(self, tool):
        """Test transcription with valid file."""
        with patch('os.path.exists', return_value=True), patch.object(tool, 'transcriber') as mock_transcriber:
            mock_transcriber.return_value = {'text': 'This is a test transcript', 'chunks': [{'timestamp': [0.0, 5.0], 'text': 'This is a test transcript'}]}
            result = tool._run('test_audio.mp4')
            assert result.success
            assert 'transcript' in result.data

    def test_run_with_transcription_error(self, tool):
        """Test transcription with error."""
        with patch('os.path.exists', return_value=True), patch.object(tool, 'transcriber') as mock_transcriber:
            mock_transcriber.side_effect = Exception('Transcription failed')
            result = tool._run('test_audio.mp4')
            assert not result.success
            assert 'failed' in result.error.lower()

    def test_cache_functionality(self, tool):
        """Test cache functionality when enabled."""
        with patch('os.path.exists', return_value=True), patch.object(tool, '_cache') as mock_cache:
            mock_cache.get_transcription.return_value = {'transcript': 'Cached transcript', 'segments': []}
            result = tool._run('test_audio.mp4', video_id='test_video')
            assert result.success
            assert result.data.get('cached') is True

    def test_segments_processing(self, tool):
        """Test segments processing."""
        with patch('os.path.exists', return_value=True), patch.object(tool, 'transcriber') as mock_transcriber:
            mock_transcriber.return_value = {'text': 'Full transcript', 'chunks': [{'timestamp': [0.0, 2.0], 'text': 'First segment'}, {'timestamp': [2.0, 4.0], 'text': 'Second segment'}]}
            result = tool._run('test_audio.mp4')
            assert result.success
            assert 'segments' in result.data
            segments = result.data['segments']
            assert len(segments) == 2
            assert segments[0]['start'] == 0.0
            assert segments[0]['end'] == 2.0