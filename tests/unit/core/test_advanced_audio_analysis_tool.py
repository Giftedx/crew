"""Tests for AdvancedAudioAnalysisTool."""

from platform.core.step_result import StepResult
from unittest.mock import Mock, patch

from ultimate_discord_intelligence_bot.tools.advanced_audio_analysis_tool import AdvancedAudioAnalysisTool


class TestAdvancedAudioAnalysisTool:
    """Test suite for AdvancedAudioAnalysisTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = AdvancedAudioAnalysisTool()

    def test_tool_initialization(self):
        """Test tool initializes correctly."""
        assert self.tool.name == "advanced_audio_analysis_tool"
        assert "comprehensive audio analysis" in self.tool.description

    def test_run_with_missing_dependencies(self):
        """Test tool behavior when optional dependencies are missing."""
        with patch("ultimate_discord_intelligence_bot.tools.advanced_audio_analysis_tool.librosa", None):
            result = self.tool._run("test_audio.wav")
            assert not result.success
            assert "Optional dependencies" in result.error

    def test_run_with_valid_audio_file(self):
        """Test tool with valid audio file."""
        with patch("ultimate_discord_intelligence_bot.tools.advanced_audio_analysis_tool.librosa") as mock_librosa:
            mock_librosa.load.return_value = (Mock(), 22050)
            mock_librosa.feature.mfcc.return_value = Mock()
            mock_librosa.feature.spectral_centroid.return_value = Mock()
            result = self.tool._run("test_audio.wav")
            assert result.success
            assert "audio_analysis" in result.data

    def test_run_with_invalid_file(self):
        """Test tool with invalid file path."""
        result = self.tool._run("nonexistent.wav")
        assert not result.success
        assert "File not found" in result.error

    def test_run_with_unsupported_format(self):
        """Test tool with unsupported audio format."""
        result = self.tool._run("test.txt")
        assert not result.success
        assert "Unsupported audio format" in result.error

    def test_audio_properties_extraction(self):
        """Test audio properties extraction."""
        with patch("wave.open") as mock_wave:
            mock_wave.return_value.__enter__.return_value.getparams.return_value = Mock(
                nchannels=2, framerate=44100, nframes=1000, sampwidth=2
            )
            result = self.tool._run("test_audio.wav")
            assert isinstance(result, StepResult)
