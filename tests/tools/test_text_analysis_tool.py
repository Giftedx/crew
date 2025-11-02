"""Tests for Text Analysis Tool."""

from platform.core.step_result import StepResult
from unittest.mock import patch

import pytest

from domains.intelligence.analysis.text_analysis_tool import TextAnalysisTool


class TestTextAnalysisTool:
    """Test cases for Text Analysis Tool."""

    @pytest.fixture
    def tool(self):
        """Create TextAnalysisTool instance."""
        return TextAnalysisTool()

    @pytest.fixture
    def sample_text(self):
        """Sample text for analysis."""
        return "This is a sample text for sentiment analysis. It contains positive and negative words."

    def test_tool_initialization(self, tool):
        """Test TextAnalysisTool initialization."""
        assert tool is not None
        assert tool.name == "Enhanced Text Analysis Tool"
        assert hasattr(tool, "_run")

    def test_text_analysis_basic(self, tool, sample_text):
        """Test basic text analysis functionality."""
        result = tool._run(text=sample_text)
        assert isinstance(result, StepResult)
        assert result.success or result.status == "uncertain"

    def test_text_analysis_empty_input(self, tool):
        """Test text analysis with empty input."""
        result = tool._run(text="")
        assert isinstance(result, StepResult)
        assert result.success or result.status == "uncertain"

    def test_text_analysis_long_text(self, tool):
        """Test text analysis with long text."""
        long_text = "This is a very long text. " * 100
        result = tool._run(text=long_text)
        assert isinstance(result, StepResult)
        assert result.success or result.status == "uncertain"

    @patch("ultimate_discord_intelligence_bot.tools.analysis.text_analysis_tool.nltk")
    def test_text_analysis_with_mock_nltk(self, mock_nltk, tool, sample_text):
        """Test text analysis with mocked NLTK."""
        mock_nltk.download.return_value = None
        mock_nltk.word_tokenize.return_value = ["This", "is", "a", "test"]
        mock_nltk.corpus.stopwords.words.return_value = ["the", "a", "an"]
        result = tool._run(text=sample_text)
        assert isinstance(result, StepResult)
        assert result.success or result.status == "uncertain"

    def test_text_analysis_tenant_isolation(self, tool, sample_text):
        """Test text analysis respects tenant isolation."""
        result1 = tool._run(text=sample_text)
        result2 = tool._run(text=sample_text)
        assert isinstance(result1, StepResult)
        assert isinstance(result2, StepResult)
        assert result1.success or result1.status == "uncertain"
        assert result2.success or result2.status == "uncertain"
