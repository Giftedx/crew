"""Tests for persona confidence calculators module."""

from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator.persona_confidence_calculators import (
    calculate_agent_confidence_from_crew,
    calculate_contextual_relevance,
    calculate_persona_confidence,
    calculate_persona_confidence_from_crew,
)


class TestCalculatePersonaConfidence:
    """Test persona confidence calculation from behavioral data."""

    def test_calculate_persona_confidence_with_scores(self):
        """Test persona confidence with explicit scores."""
        behavioral_data = {
            "consistency_score": 0.8,
            "authenticity_score": 0.9,
            "reliability_score": 0.7,
        }

        result = calculate_persona_confidence(behavioral_data)

        expected = (0.8 + 0.9 + 0.7) / 3
        assert abs(result - expected) < 1e-10

    def test_calculate_persona_confidence_partial_scores(self):
        """Test persona confidence with partial scores."""
        behavioral_data = {
            "consistency_score": 0.8,
            "authenticity_score": 0.9,
        }

        result = calculate_persona_confidence(behavioral_data)

        expected = (0.8 + 0.9) / 2
        assert result == expected

    def test_calculate_persona_confidence_fallback_text_analysis(self):
        """Test persona confidence fallback to text analysis."""
        behavioral_data = {
            "description": "consistent and authentic behavior patterns",
        }

        result = calculate_persona_confidence(behavioral_data)

        # Should detect positive indicators
        assert result > 0.5

    def test_calculate_persona_confidence_negative_indicators(self):
        """Test persona confidence with negative indicators."""
        behavioral_data = {
            "description": "inconsistent and fake behavior patterns",
        }

        result = calculate_persona_confidence(behavioral_data)

        # Should detect negative indicators
        assert result < 0.5

    def test_calculate_persona_confidence_empty_data(self):
        """Test persona confidence with empty data."""
        result = calculate_persona_confidence({})
        assert result == 0.0

    def test_calculate_persona_confidence_none_data(self):
        """Test persona confidence with None data."""
        result = calculate_persona_confidence(None)
        assert result == 0.0

    def test_calculate_persona_confidence_exception_handling(self):
        """Test persona confidence exception handling."""
        behavioral_data = Mock()
        behavioral_data.__str__ = Mock(side_effect=Exception("Test error"))

        result = calculate_persona_confidence(behavioral_data)
        assert result == 0.0


class TestCalculatePersonaConfidenceFromCrew:
    """Test persona confidence calculation from crew results."""

    def test_calculate_persona_confidence_from_crew_with_indicators(self):
        """Test persona confidence from crew with positive indicators."""
        crew_result = "The analysis shows consistent personality traits and authentic behavior patterns"

        result = calculate_persona_confidence_from_crew(crew_result)

        assert result > 0.0

    def test_calculate_persona_confidence_from_crew_no_indicators(self):
        """Test persona confidence from crew with no indicators."""
        crew_result = "Some random text without persona indicators"

        result = calculate_persona_confidence_from_crew(crew_result)

        assert result == 0.0

    def test_calculate_persona_confidence_from_crew_empty_result(self):
        """Test persona confidence from crew with empty result."""
        result = calculate_persona_confidence_from_crew("")
        assert result == 0.0

    def test_calculate_persona_confidence_from_crew_none_result(self):
        """Test persona confidence from crew with None result."""
        result = calculate_persona_confidence_from_crew(None)
        assert result == 0.0

    def test_calculate_persona_confidence_from_crew_exception_handling(self):
        """Test persona confidence from crew exception handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        result = calculate_persona_confidence_from_crew(crew_result)
        assert result == 0.0


class TestCalculateAgentConfidenceFromCrew:
    """Test agent confidence calculation from crew results."""

    def test_calculate_agent_confidence_from_crew_success_indicators(self):
        """Test agent confidence from crew with success indicators."""
        crew_result = "Task completed successfully and objective achieved"

        result = calculate_agent_confidence_from_crew(crew_result)

        assert result > 0.0

    def test_calculate_agent_confidence_from_crew_error_indicators(self):
        """Test agent confidence from crew with error indicators."""
        crew_result = "Task failed with errors and incomplete processing"

        result = calculate_agent_confidence_from_crew(crew_result)

        assert result < 0.5  # Should be penalized for errors

    def test_calculate_agent_confidence_from_crew_mixed_indicators(self):
        """Test agent confidence from crew with mixed indicators."""
        crew_result = "Analysis complete but encountered some errors"

        result = calculate_agent_confidence_from_crew(crew_result)

        # Should be between success and failure
        assert 0.0 <= result <= 1.0

    def test_calculate_agent_confidence_from_crew_neutral(self):
        """Test agent confidence from crew with neutral indicators."""
        crew_result = "Some neutral text without clear indicators"

        result = calculate_agent_confidence_from_crew(crew_result)

        assert result == 0.5  # Neutral confidence

    def test_calculate_agent_confidence_from_crew_empty_result(self):
        """Test agent confidence from crew with empty result."""
        result = calculate_agent_confidence_from_crew("")
        assert result == 0.0

    def test_calculate_agent_confidence_from_crew_none_result(self):
        """Test agent confidence from crew with None result."""
        result = calculate_agent_confidence_from_crew(None)
        assert result == 0.0

    def test_calculate_agent_confidence_from_crew_exception_handling(self):
        """Test agent confidence from crew exception handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        result = calculate_agent_confidence_from_crew(crew_result)
        assert result == 0.0


class TestCalculateContextualRelevance:
    """Test contextual relevance calculation."""

    def test_calculate_contextual_relevance_high_relevance(self):
        """Test contextual relevance with high relevance content."""
        content = "This is about machine learning and artificial intelligence"
        context = "machine learning artificial intelligence domain"

        result = calculate_contextual_relevance(content, context)

        assert result > 0.0

    def test_calculate_contextual_relevance_low_relevance(self):
        """Test contextual relevance with low relevance content."""
        content = "This is about cooking recipes and food preparation"
        context = "machine learning artificial intelligence domain"

        result = calculate_contextual_relevance(content, context)

        assert result < 0.5

    def test_calculate_contextual_relevance_empty_content(self):
        """Test contextual relevance with empty content."""
        result = calculate_contextual_relevance("", {"topic": "test"})
        assert result == 0.0

    def test_calculate_contextual_relevance_empty_context(self):
        """Test contextual relevance with empty context."""
        result = calculate_contextual_relevance("test content", {})
        assert result == 0.0

    def test_calculate_contextual_relevance_none_content(self):
        """Test contextual relevance with None content."""
        result = calculate_contextual_relevance(None, {"topic": "test"})
        assert result == 0.0

    def test_calculate_contextual_relevance_none_context(self):
        """Test contextual relevance with None context."""
        result = calculate_contextual_relevance("test content", None)
        assert result == 0.0

    def test_calculate_contextual_relevance_exception_handling(self):
        """Test contextual relevance exception handling."""
        content = Mock()
        content.lower = Mock(side_effect=Exception("Test error"))

        result = calculate_contextual_relevance(content, {"topic": "test"})
        assert result == 0.0
