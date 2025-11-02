"""Tests for CharacterProfileTool."""
from unittest.mock import patch
import pytest
from platform.core.step_result import StepResult
from domains.intelligence.analysis.character_profile_tool import CharacterProfileTool

class TestCharacterProfileTool:
    """Test cases for CharacterProfileTool."""

    @pytest.fixture
    def tool(self):
        """Create CharacterProfileTool instance."""
        return CharacterProfileTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == 'character_profile'
        assert 'character' in tool.description.lower()

    def test_run_with_valid_text(self, tool):
        """Test character profiling with valid text."""
        with patch.object(tool, '_analyze_character') as mock_analyze:
            mock_analyze.return_value = StepResult.ok(data={'character_name': 'John Doe', 'personality_traits': ['confident', 'analytical'], 'speaking_style': 'formal', 'confidence_score': 0.85})
            result = tool._run('John Doe is a confident and analytical speaker who presents formal arguments.')
            assert result.success
            assert 'character_name' in result.data
            mock_analyze.assert_called_once()

    def test_run_with_empty_text(self, tool):
        """Test character profiling with empty text."""
        result = tool._run('')
        assert not result.success
        assert 'empty' in result.error.lower()

    def test_run_with_short_text(self, tool):
        """Test character profiling with insufficient text."""
        result = tool._run('Hi')
        assert not result.success
        assert 'insufficient' in result.error.lower()

    def test_analyze_character_success(self, tool):
        """Test successful character analysis."""
        text = 'Dr. Smith is a renowned scientist who speaks with authority and precision.'
        with patch.object(tool, '_extract_personality_traits') as mock_traits:
            with patch.object(tool, '_analyze_speaking_style') as mock_style:
                with patch.object(tool, '_calculate_confidence') as mock_confidence:
                    mock_traits.return_value = ['authoritative', 'precise']
                    mock_style.return_value = 'formal'
                    mock_confidence.return_value = 0.9
                    result = tool._analyze_character(text)
                    assert result.success
                    assert result.data['personality_traits'] == ['authoritative', 'precise']
                    assert result.data['speaking_style'] == 'formal'
                    assert result.data['confidence_score'] == 0.9

    def test_extract_personality_traits(self, tool):
        """Test personality trait extraction."""
        text = 'The speaker is confident, analytical, and persuasive in their arguments.'
        traits = tool._extract_personality_traits(text)
        assert isinstance(traits, list)
        assert len(traits) > 0
        assert all((isinstance(trait, str) for trait in traits))

    def test_analyze_speaking_style(self, tool):
        """Test speaking style analysis."""
        formal_text = 'The evidence clearly indicates that this hypothesis is supported by the data.'
        casual_text = 'So like, I think this is probably true, you know?'
        formal_style = tool._analyze_speaking_style(formal_text)
        casual_style = tool._analyze_speaking_style(casual_text)
        assert formal_style in ['formal', 'academic', 'professional']
        assert casual_style in ['casual', 'conversational', 'informal']

    def test_calculate_confidence(self, tool):
        """Test confidence calculation."""
        high_quality_text = 'Dr. Johnson, a renowned expert in the field, presents a comprehensive analysis of the data.'
        low_quality_text = 'Um, I think maybe this could be true?'
        high_confidence = tool._calculate_confidence(high_quality_text)
        low_confidence = tool._calculate_confidence(low_quality_text)
        assert 0 <= high_confidence <= 1
        assert 0 <= low_confidence <= 1
        assert high_confidence > low_confidence

    def test_handle_analysis_error(self, tool):
        """Test error handling in character analysis."""
        with patch.object(tool, '_extract_personality_traits') as mock_traits:
            mock_traits.side_effect = Exception('Analysis failed')
            result = tool._analyze_character('test text')
            assert not result.success
            assert 'failed' in result.error.lower()

    def test_validate_input_text(self, tool):
        """Test input text validation."""
        assert tool._validate_input_text('This is a valid text for analysis.') is True
        assert tool._validate_input_text('') is False
        assert tool._validate_input_text('Hi') is False
        assert tool._validate_input_text(None) is False