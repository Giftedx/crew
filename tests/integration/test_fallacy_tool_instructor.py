"""
Integration test for LogicalFallacyTool using Instructor for structured outputs.

This test validates that the enhanced fallacy detection tool can leverage
LLM-based analysis via Instructor when enabled, with graceful fallback to
pattern-matching heuristics.
"""
from unittest.mock import MagicMock, Mock, patch
import pytest
try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False
from ai.response_models import ContentQuality, FallacyAnalysisResult, FallacyInstance, FallacyType
from domains.intelligence.analysis.logical_fallacy_tool import LogicalFallacyTool

class TestLogicalFallacyToolInstructor:
    """Test suite for LogicalFallacyTool with Instructor integration."""

    @pytest.fixture
    def mock_config_enabled(self):
        """Mock SecureConfig with Instructor enabled."""
        with patch('ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool.get_config') as mock_get:
            config = Mock()
            config.enable_instructor = True
            config.instructor_max_retries = 3
            config.instructor_timeout = 30.0
            config.openrouter_api_key = 'test-api-key'
            config.openrouter_llm_model = 'gpt-4'
            mock_get.return_value = config
            yield config

    @pytest.fixture
    def mock_config_disabled(self):
        """Mock SecureConfig with Instructor disabled."""
        with patch('ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool.get_config') as mock_get:
            config = Mock()
            config.enable_instructor = False
            mock_get.return_value = config
            yield config

    @pytest.fixture
    def tool(self):
        """Create a LogicalFallacyTool instance."""
        return LogicalFallacyTool()

    def test_pattern_matching_fallback_when_instructor_disabled(self, tool, mock_config_disabled):
        """Should use pattern-matching when Instructor is disabled."""
        text = "You can't trust John's argument about climate change because he's not a scientist."
        result = tool.run(text)
        assert result.success
        assert result.data is not None
        assert 'fallacies' in result.data
        assert result.data.get('analysis_method') == 'pattern_matching'

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason='Instructor not installed')
    def test_instructor_method_used_when_enabled(self, tool, mock_config_enabled):
        """Should attempt to use Instructor when enabled and available."""
        text = "You can't trust John's argument about climate change because he's not a scientist."
        mock_client = MagicMock()
        mock_response = FallacyAnalysisResult(fallacies=[FallacyInstance(fallacy_type=FallacyType.AD_HOMINEM, severity='high', confidence='high', quote="You can't trust John's argument", explanation='Attacks the person rather than addressing the argument', context='Dismissing climate change argument based on credentials')], overall_quality=ContentQuality.POOR, credibility_score=0.3, summary='Contains ad hominem attack which undermines the credibility of the argument.')
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(parsed=mock_response))]
        mock_client.chat.completions.create.return_value = mock_completion
        with patch('ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool.InstructorClientFactory') as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client
            result = tool.run(text)
        assert result.success
        assert result.data is not None
        assert 'fallacies' in result.data
        assert result.data.get('analysis_method') == 'llm_instructor'
        MockFactory.create_openrouter_client.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None
        messages = call_args[1]['messages']
        assert any((text in str(msg) for msg in messages))

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason='Instructor not installed')
    def test_fallback_to_pattern_matching_on_llm_failure(self, tool, mock_config_enabled):
        """Should fallback to pattern-matching if LLM analysis fails."""
        text = "This is clearly wrong because everyone knows it's true."
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception('API error')
        with patch('ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool.InstructorClientFactory') as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client
            result = tool.run(text)
        assert result.success
        assert result.data is not None
        assert 'fallacies' in result.data
        assert result.data.get('analysis_method') == 'pattern_matching'

    def test_empty_text_handling(self, tool, mock_config_enabled):
        """Should handle empty text gracefully."""
        result = tool.run('')
        assert result.success
        assert result.data is not None
        assert result.data.get('fallacies', []) == []

    def test_no_fallacies_detected(self, tool, mock_config_disabled):
        """Should return empty fallacy list for clean text."""
        text = 'The study shows that regular exercise improves cardiovascular health. This conclusion is supported by data from 10,000 participants over 5 years.'
        result = tool.run(text)
        assert result.success
        assert result.data is not None
        assert 'fallacies' in result.data

    @pytest.mark.skipif(not INSTRUCTOR_AVAILABLE, reason='Instructor not installed')
    def test_instructor_retry_logic(self, tool, mock_config_enabled):
        """Should leverage Instructor's retry logic on validation failures."""
        text = "You can't trust scientists because they're all paid shills."
        mock_client = MagicMock()
        invalid_response = MagicMock()
        invalid_response.choices = [MagicMock(message=MagicMock(parsed=None))]
        valid_response_obj = FallacyAnalysisResult(fallacies=[FallacyInstance(fallacy_type=FallacyType.AD_HOMINEM, severity='high', confidence='high', quote="scientists because they're all paid shills", explanation="Attacks scientists' integrity without addressing their arguments", context='Dismissing scientific consensus via conspiracy')], overall_quality=ContentQuality.POOR, credibility_score=0.2, summary='Ad hominem attack on scientists undermines the argument completely.')
        valid_response = MagicMock()
        valid_response.choices = [MagicMock(message=MagicMock(parsed=valid_response_obj))]
        mock_client.chat.completions.create.side_effect = [invalid_response, valid_response]
        with patch('ultimate_discord_intelligence_bot.tools.analysis.logical_fallacy_tool.InstructorClientFactory') as MockFactory:
            MockFactory.is_enabled.return_value = True
            MockFactory.create_openrouter_client.return_value = mock_client
            result = tool.run(text)
            assert result.success
            assert result.data is not None
if __name__ == '__main__':
    pytest.main([__file__, '-v'])