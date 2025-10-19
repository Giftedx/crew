"""Tests for AI quality calculators module."""

from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator.ai_quality_calculators import (
    calculate_ai_enhancement_level,
    calculate_ai_quality_score,
    calculate_overall_confidence,
    calculate_synthesis_confidence,
    calculate_synthesis_confidence_from_crew,
)


class TestCalculateAiQualityScore:
    """Test AI quality score calculation."""

    def test_calculate_ai_quality_score_with_weights(self):
        """Test AI quality score with weighted dimensions."""
        quality_dimensions = {
            "accuracy": 0.9,
            "completeness": 0.8,
            "consistency": 0.7,
            "clarity": 0.6,
            "relevance": 0.5,
        }

        result = calculate_ai_quality_score(quality_dimensions)

        # Weighted calculation: 0.9*0.3 + 0.8*0.2 + 0.7*0.2 + 0.6*0.15 + 0.5*0.15
        expected = 0.9 * 0.3 + 0.8 * 0.2 + 0.7 * 0.2 + 0.6 * 0.15 + 0.5 * 0.15
        assert result == expected

    def test_calculate_ai_quality_score_partial_dimensions(self):
        """Test AI quality score with partial dimensions."""
        quality_dimensions = {
            "accuracy": 0.9,
            "completeness": 0.8,
        }

        result = calculate_ai_quality_score(quality_dimensions)

        # Only accuracy (0.3) and completeness (0.2) weights used
        expected = (0.9 * 0.3 + 0.8 * 0.2) / (0.3 + 0.2)
        assert result == expected

    def test_calculate_ai_quality_score_fallback_average(self):
        """Test AI quality score fallback to average."""
        quality_dimensions = {
            "custom_dimension": 0.8,
            "another_dimension": 0.6,
        }

        result = calculate_ai_quality_score(quality_dimensions)

        # Should fall back to average of available scores
        expected = (0.8 + 0.6) / 2
        assert result == expected

    def test_calculate_ai_quality_score_empty_dimensions(self):
        """Test AI quality score with empty dimensions."""
        result = calculate_ai_quality_score({})
        assert result == 0.0

    def test_calculate_ai_quality_score_none_dimensions(self):
        """Test AI quality score with None dimensions."""
        result = calculate_ai_quality_score(None)
        assert result == 0.0

    def test_calculate_ai_quality_score_exception_handling(self):
        """Test AI quality score exception handling."""
        quality_dimensions = Mock()
        quality_dimensions.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_ai_quality_score(quality_dimensions)
        assert result == 0.0


class TestCalculateAiEnhancementLevel:
    """Test AI enhancement level calculation."""

    def test_calculate_ai_enhancement_level_shallow(self):
        """Test AI enhancement level for shallow depth."""
        result = calculate_ai_enhancement_level("shallow")
        assert result == 0.25

    def test_calculate_ai_enhancement_level_standard(self):
        """Test AI enhancement level for standard depth."""
        result = calculate_ai_enhancement_level("standard")
        assert result == 0.5

    def test_calculate_ai_enhancement_level_deep(self):
        """Test AI enhancement level for deep depth."""
        result = calculate_ai_enhancement_level("deep")
        assert result == 0.75

    def test_calculate_ai_enhancement_level_experimental(self):
        """Test AI enhancement level for experimental depth."""
        result = calculate_ai_enhancement_level("experimental")
        assert result == 1.0

    def test_calculate_ai_enhancement_level_case_insensitive(self):
        """Test AI enhancement level case insensitive."""
        result = calculate_ai_enhancement_level("DEEP")
        assert result == 0.75

    def test_calculate_ai_enhancement_level_unknown_depth(self):
        """Test AI enhancement level for unknown depth."""
        result = calculate_ai_enhancement_level("unknown")
        assert result == 0.5  # Default fallback

    def test_calculate_ai_enhancement_level_exception_handling(self):
        """Test AI enhancement level exception handling."""
        depth = Mock()
        depth.lower = Mock(side_effect=Exception("Test error"))

        result = calculate_ai_enhancement_level(depth)
        assert result == 0.5


class TestCalculateSynthesisConfidence:
    """Test synthesis confidence calculation."""

    def test_calculate_synthesis_confidence_with_factors(self):
        """Test synthesis confidence with explicit factors."""
        research_results = {
            "source_diversity": 0.8,
            "evidence_strength": 0.9,
            "cross_validation": 0.7,
        }

        result = calculate_synthesis_confidence(research_results)

        expected = (0.8 + 0.9 + 0.7) / 3
        assert abs(result - expected) < 1e-10

    def test_calculate_synthesis_confidence_fallback_text_analysis(self):
        """Test synthesis confidence fallback to text analysis."""
        research_results = {
            "description": "comprehensive synthesis with unified integration",
        }

        result = calculate_synthesis_confidence(research_results)

        # Should detect positive synthesis indicators
        assert result > 0.5

    def test_calculate_synthesis_confidence_negative_indicators(self):
        """Test synthesis confidence with negative indicators."""
        research_results = {
            "description": "fragmented and inconsistent research",
        }

        result = calculate_synthesis_confidence(research_results)

        # Should detect negative indicators
        assert result < 0.5

    def test_calculate_synthesis_confidence_empty_results(self):
        """Test synthesis confidence with empty results."""
        result = calculate_synthesis_confidence({})
        assert result == 0.0

    def test_calculate_synthesis_confidence_none_results(self):
        """Test synthesis confidence with None results."""
        result = calculate_synthesis_confidence(None)
        assert result == 0.0

    def test_calculate_synthesis_confidence_exception_handling(self):
        """Test synthesis confidence exception handling."""
        research_results = Mock()
        research_results.__str__ = Mock(side_effect=Exception("Test error"))

        result = calculate_synthesis_confidence(research_results)
        assert result == 0.0


class TestCalculateSynthesisConfidenceFromCrew:
    """Test synthesis confidence calculation from crew results."""

    def test_calculate_synthesis_confidence_from_crew_with_indicators(self):
        """Test synthesis confidence from crew with positive indicators."""
        crew_result = "Synthesis complete with comprehensive overview and unified analysis"

        result = calculate_synthesis_confidence_from_crew(crew_result)

        assert result > 0.0

    def test_calculate_synthesis_confidence_from_crew_no_indicators(self):
        """Test synthesis confidence from crew with no indicators."""
        crew_result = "Some random text without synthesis indicators"

        result = calculate_synthesis_confidence_from_crew(crew_result)

        assert result == 0.0

    def test_calculate_synthesis_confidence_from_crew_empty_result(self):
        """Test synthesis confidence from crew with empty result."""
        result = calculate_synthesis_confidence_from_crew("")
        assert result == 0.0

    def test_calculate_synthesis_confidence_from_crew_none_result(self):
        """Test synthesis confidence from crew with None result."""
        result = calculate_synthesis_confidence_from_crew(None)
        assert result == 0.0

    def test_calculate_synthesis_confidence_from_crew_exception_handling(self):
        """Test synthesis confidence from crew exception handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        result = calculate_synthesis_confidence_from_crew(crew_result)
        assert result == 0.0


class TestCalculateOverallConfidence:
    """Test overall confidence calculation from multiple sources."""

    def test_calculate_overall_confidence_with_dict_sources(self):
        """Test overall confidence with dictionary sources."""
        source1 = {"confidence": 0.8, "quality_score": 0.9}
        source2 = {"confidence": 0.7, "quality_score": 0.6}

        result = calculate_overall_confidence(source1, source2)

        expected = (0.8 + 0.7) / 2
        assert result == expected

    def test_calculate_overall_confidence_with_numeric_sources(self):
        """Test overall confidence with numeric sources."""
        result = calculate_overall_confidence(0.8, 0.7, 0.9)

        expected = (0.8 + 0.7 + 0.9) / 3
        assert result == expected

    def test_calculate_overall_confidence_with_string_sources(self):
        """Test overall confidence with string sources."""
        source1 = "This is confident and reliable analysis"
        source2 = "This is uncertain and speculative content"

        result = calculate_overall_confidence(source1, source2)

        # Should detect confidence vs uncertainty in strings
        assert 0.0 <= result <= 1.0

    def test_calculate_overall_confidence_mixed_sources(self):
        """Test overall confidence with mixed source types."""
        dict_source = {"confidence": 0.8}
        numeric_source = 0.7
        string_source = "confident analysis"

        result = calculate_overall_confidence(dict_source, numeric_source, string_source)

        assert 0.0 <= result <= 1.0

    def test_calculate_overall_confidence_empty_sources(self):
        """Test overall confidence with no sources."""
        result = calculate_overall_confidence()
        assert result == 0.0

    def test_calculate_overall_confidence_exception_handling(self):
        """Test overall confidence exception handling."""
        source = Mock()
        source.__iter__ = Mock(side_effect=Exception("Test error"))

        result = calculate_overall_confidence(source)
        assert result == 0.0
