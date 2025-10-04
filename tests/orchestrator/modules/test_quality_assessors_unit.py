"""
Unit tests for orchestrator/quality_assessors module.

Tests all quality assessment functions in isolation:
- detect_placeholder_responses
- validate_stage_data
- assess_content_coherence
- clamp_score
- assess_factual_accuracy
- assess_source_credibility
- assess_bias_levels
- assess_emotional_manipulation
- assess_logical_consistency
- assess_quality_trend
- calculate_overall_confidence
- assess_transcript_quality
"""

import logging
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.orchestrator import quality_assessors


class TestDetectPlaceholderResponses:
    """Test detect_placeholder_responses function."""

    def test_detects_short_transcript(self, caplog):
        """Test detection of placeholder via short transcript."""
        with caplog.at_level(logging.ERROR):
            quality_assessors.detect_placeholder_responses(
                "transcription", {"transcript": "Short"}, logger_instance=logging.getLogger()
            )

        assert "too short" in caplog.text.lower()

    def test_detects_placeholder_patterns_in_transcript(self, caplog):
        """Test detection of placeholder patterns."""
        with caplog.at_level(logging.ERROR):
            quality_assessors.detect_placeholder_responses(
                "transcription",
                {"transcript": "Your transcribed text goes here with more content"},
                logger_instance=logging.getLogger(),
            )

        assert "placeholder pattern" in caplog.text.lower()

    def test_accepts_valid_transcript(self, caplog):
        """Test no errors for valid long transcript."""
        with caplog.at_level(logging.ERROR):
            quality_assessors.detect_placeholder_responses(
                "transcription",
                {"transcript": "This is a valid transcript with substantial content " * 10},
                logger_instance=logging.getLogger(),
            )

        assert "TOOL EXECUTION FAILURE" not in caplog.text

    def test_detects_placeholder_in_analysis_insights(self, caplog):
        """Test detection in analysis insights."""
        with caplog.at_level(logging.ERROR):
            quality_assessors.detect_placeholder_responses(
                "analysis", {"insights": "TODO: Add real insights here"}, logger_instance=logging.getLogger()
            )

        assert "placeholder pattern" in caplog.text.lower()

    def test_increments_metrics_when_provided(self):
        """Test metrics counter incremented on detection."""
        mock_metrics = Mock()
        mock_counter = Mock()
        mock_metrics.counter.return_value = mock_counter

        quality_assessors.detect_placeholder_responses(
            "transcription", {"transcript": "Short"}, metrics_instance=mock_metrics
        )

        mock_metrics.counter.assert_called()
        mock_counter.inc.assert_called()


class TestValidateStageData:
    """Test validate_stage_data function."""

    def test_validates_complete_data(self):
        """Test validation passes with all required keys."""
        data = {"transcript": "text", "metadata": {}, "quality": 0.8}
        # Should not raise
        quality_assessors.validate_stage_data("transcription", ["transcript", "metadata"], data)

    def test_raises_on_missing_keys(self):
        """Test raises ValueError when keys missing."""
        data = {"transcript": "text"}

        with pytest.raises(ValueError) as exc_info:
            quality_assessors.validate_stage_data("transcription", ["transcript", "metadata", "quality"], data)

        assert "missing required keys" in str(exc_info.value).lower()
        assert "metadata" in str(exc_info.value)
        assert "quality" in str(exc_info.value)

    def test_accepts_empty_requirements(self):
        """Test validation passes with no requirements."""
        data = {"any": "data"}
        # Should not raise
        quality_assessors.validate_stage_data("any_stage", [], data)


class TestAssessContentCoherence:
    """Test assess_content_coherence function."""

    def test_assesses_high_quality_content(self):
        """Test high coherence for quality content."""
        analysis_data = {
            "transcript": "This is a comprehensive transcript. " * 30,
            "linguistic_patterns": {"complexity": "high"},
            "sentiment_analysis": {"overall": "positive"},
            "content_metadata": {"title": "Test", "platform": "YouTube", "word_count": 150, "quality_score": 0.9},
        }

        score = quality_assessors.assess_content_coherence(analysis_data)

        assert 0.7 <= score <= 1.0  # High quality content

    def test_assesses_low_quality_short_content(self):
        """Test low coherence for minimal content."""
        analysis_data = {"transcript": "Short text"}

        score = quality_assessors.assess_content_coherence(analysis_data)

        assert score < 0.5  # Low quality

    def test_returns_neutral_for_empty_data(self):
        """Test neutral score for empty data."""
        score = quality_assessors.assess_content_coherence({})

        assert 0.4 <= score <= 0.6  # Neutral

    def test_handles_exception_gracefully(self):
        """Test returns default on exception."""
        # Pass invalid data to trigger exception
        score = quality_assessors.assess_content_coherence(None)  # type: ignore

        assert score == 0.5  # Default


class TestClampScore:
    """Test clamp_score function."""

    def test_clamps_value_above_maximum(self):
        """Test clamping high values."""
        result = quality_assessors.clamp_score(1.5, 0.0, 1.0)

        assert result == 1.0

    def test_clamps_value_below_minimum(self):
        """Test clamping low values."""
        result = quality_assessors.clamp_score(-0.5, 0.0, 1.0)

        assert result == 0.0

    def test_preserves_value_in_range(self):
        """Test preserving valid values."""
        result = quality_assessors.clamp_score(0.75, 0.0, 1.0)

        assert result == 0.75

    def test_handles_custom_bounds(self):
        """Test custom min/max bounds."""
        result = quality_assessors.clamp_score(50, 10, 100)

        assert result == 50

    def test_handles_exception_returns_minimum(self):
        """Test exception handling returns minimum."""
        result = quality_assessors.clamp_score("invalid", 0.0, 1.0)  # type: ignore

        assert result == 0.0


class TestAssessFactualAccuracy:
    """Test assess_factual_accuracy function."""

    def test_assesses_high_accuracy_with_verified_claims(self):
        """Test high accuracy when claims verified."""
        verification_data = {"fact_checks": {"verified_claims": 8, "disputed_claims": 2, "evidence": [1, 2, 3]}}

        score = quality_assessors.assess_factual_accuracy(verification_data)

        assert score > 0.7  # High accuracy

    def test_assesses_low_accuracy_with_disputed_claims(self):
        """Test low accuracy when claims disputed."""
        verification_data = {"fact_checks": {"verified_claims": 2, "disputed_claims": 8}}

        score = quality_assessors.assess_factual_accuracy(verification_data)

        assert score < 0.5  # Low accuracy

    def test_handles_list_format_claims(self):
        """Test handling of list-format claims."""
        verification_data = {"fact_checks": {"verified_claims": ["claim1", "claim2"], "disputed_claims": ["claim3"]}}

        score = quality_assessors.assess_factual_accuracy(verification_data)

        assert score > 0.6  # More verified than disputed

    def test_returns_neutral_for_empty_data(self):
        """Test neutral score for no data."""
        score = quality_assessors.assess_factual_accuracy(None)

        assert score == 0.5

    def test_combines_verification_and_fact_data(self):
        """Test combining multiple data sources."""
        verification_data = {"fact_verification": {"verified_claims": 5, "disputed_claims": 1}}
        fact_data = {"fact_checks": {"verified_claims": 3, "disputed_claims": 0}}

        score = quality_assessors.assess_factual_accuracy(verification_data, fact_data)

        assert score > 0.7  # Combined high verification

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        # Invalid data type to trigger exception
        score = quality_assessors.assess_factual_accuracy("invalid")  # type: ignore

        assert score == 0.5


class TestAssessSourceCredibility:
    """Test assess_source_credibility function."""

    def test_assesses_high_credibility_validated_source(self):
        """Test high credibility for validated sources."""
        verification_data = {"source_validation": {"validated": True}}

        score = quality_assessors.assess_source_credibility(None, verification_data)

        assert score == 0.85

    def test_assesses_low_credibility_invalidated_source(self):
        """Test low credibility for invalidated sources."""
        verification_data = {"source_validation": {"validated": False}}

        score = quality_assessors.assess_source_credibility(None, verification_data)

        assert score == 0.35

    def test_combines_knowledge_and_verification_data(self):
        """Test combining multiple credibility signals."""
        knowledge_data = {"fact_check_results": {"source_reliability": 0.9}}
        verification_data = {"source_validation": {"validated": True}}

        score = quality_assessors.assess_source_credibility(knowledge_data, verification_data)

        assert score > 0.8  # High combined credibility

    def test_returns_neutral_for_no_data(self):
        """Test neutral score with no data."""
        score = quality_assessors.assess_source_credibility(None, None)

        assert score == 0.5

    def test_handles_string_reliability(self):
        """Test handling string reliability values."""
        knowledge_data = {"fact_check_results": {"source_reliability": "high"}}

        score = quality_assessors.assess_source_credibility(knowledge_data, None)

        # Should still return a valid score (handles string gracefully)
        assert 0.0 <= score <= 1.0

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        score = quality_assessors.assess_source_credibility("invalid", "invalid")  # type: ignore

        assert score == 0.5


class TestAssessBiasLevels:
    """Test assess_bias_levels function."""

    def test_assesses_low_bias_with_few_indicators(self):
        """Test low bias score when few indicators."""
        verification_data = {"bias_indicators": ["indicator1"]}

        score = quality_assessors.assess_bias_levels(None, verification_data)

        assert score > 0.5  # Low bias = high score

    def test_assesses_high_bias_with_many_indicators(self):
        """Test high bias score with many indicators."""
        verification_data = {"bias_indicators": ["bias1", "bias2", "bias3", "bias4", "bias5", "bias6"]}

        score = quality_assessors.assess_bias_levels(None, verification_data)

        assert score < 0.3  # High bias = low score (6 indicators * 0.1 penalty)

    def test_returns_neutral_for_empty_data(self):
        """Test neutral score for no data."""
        score = quality_assessors.assess_bias_levels(None, None)

        assert score == 0.7  # Default base score when no indicators

    def test_handles_dict_bias_indicators(self):
        """Test handling dict-format bias indicators."""
        verification_data = {"bias_indicators": {"signals": ["bias1", "bias2"]}}

        score = quality_assessors.assess_bias_levels(None, verification_data)

        # Should extract signals from dict format
        assert 0.0 <= score <= 1.0

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        score = quality_assessors.assess_bias_levels("invalid", "invalid")  # type: ignore

        assert score == 0.7  # Invalid inputs still return base score 0.7


class TestAssessEmotionalManipulation:
    """Test assess_emotional_manipulation function."""

    def test_detects_low_manipulation(self):
        """Test low manipulation score."""
        analysis_data = {"sentiment_analysis": {"intensity": 0.3}}

        score = quality_assessors.assess_emotional_manipulation(analysis_data)

        assert score > 0.7  # Low manipulation = high score

    def test_detects_high_manipulation(self):
        """Test high manipulation score."""
        analysis_data = {"sentiment_analysis": {"intensity": 0.9}}

        score = quality_assessors.assess_emotional_manipulation(analysis_data)

        assert score < 0.7  # High manipulation = lower score (1.0 - 0.9*0.5 = 0.55)

    def test_returns_neutral_for_no_data(self):
        """Test neutral score for missing data."""
        score = quality_assessors.assess_emotional_manipulation(None)

        assert score == 0.6  # Default

    def test_handles_missing_intensity(self):
        """Test handling dict without emotional_intensity."""
        sentiment_data = {"overall_sentiment": "positive"}

        score = quality_assessors.assess_emotional_manipulation(sentiment_data)

        assert score == 0.6  # Default when intensity missing

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        score = quality_assessors.assess_emotional_manipulation("invalid")  # type: ignore

        assert score == 0.6


class TestAssessLogicalConsistency:
    """Test assess_logical_consistency function."""

    def test_assesses_high_consistency(self):
        """Test high logical consistency."""
        verification_data = {"logical_consistency": {"score": 0.9}}

        score = quality_assessors.assess_logical_consistency(verification_data)

        assert score > 0.7

    def test_assesses_low_consistency(self):
        """Test low logical consistency."""
        verification_data = {"logical_consistency": {"score": 0.2}}

        score = quality_assessors.assess_logical_consistency(verification_data)

        assert score < 0.5

    def test_returns_default_for_no_data(self):
        """Test default score for no data."""
        score = quality_assessors.assess_logical_consistency(None)

        assert score == 0.6

    def test_handles_missing_score_key(self):
        """Test handling dict without score key."""
        verification_data = {"logical_consistency": {"analysis": "good"}}

        score = quality_assessors.assess_logical_consistency(verification_data)

        assert score == 0.6  # Default when score missing

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        score = quality_assessors.assess_logical_consistency("invalid")  # type: ignore

        assert score == 0.6


class TestAssessQualityTrend:
    """Test assess_quality_trend function."""

    def test_returns_improving_for_high_score(self):
        """Test improving trend for high quality."""
        trend = quality_assessors.assess_quality_trend(0.85)

        assert trend == "improving"

    def test_returns_stable_for_medium_score(self):
        """Test stable trend for medium quality."""
        trend = quality_assessors.assess_quality_trend(0.65)

        assert trend == "stable"

    def test_returns_declining_for_low_score(self):
        """Test declining trend for low quality."""
        trend = quality_assessors.assess_quality_trend(0.35)

        assert trend == "declining"

    def test_boundary_at_75_percent(self):
        """Test boundary between improving and stable."""
        assert quality_assessors.assess_quality_trend(0.75) == "improving"
        assert quality_assessors.assess_quality_trend(0.74) == "stable"

    def test_boundary_at_50_percent(self):
        """Test boundary between stable and declining."""
        assert quality_assessors.assess_quality_trend(0.5) == "stable"
        assert quality_assessors.assess_quality_trend(0.49) == "declining"

    def test_handles_exception_returns_stable(self):
        """Test exception handling."""
        trend = quality_assessors.assess_quality_trend("invalid")  # type: ignore

        assert trend == "stable"


class TestCalculateOverallConfidence:
    """Test calculate_overall_confidence function."""

    def test_calculates_confidence_for_single_source(self):
        """Test confidence with one data source."""
        confidence = quality_assessors.calculate_overall_confidence({"data": "source1"})

        assert confidence == 0.15

    def test_calculates_confidence_for_multiple_sources(self):
        """Test confidence with multiple sources."""
        confidence = quality_assessors.calculate_overall_confidence(
            {"data": "source1"}, {"data": "source2"}, {"data": "source3"}
        )

        assert abs(confidence - 0.45) < 0.01  # 3 * 0.15 (floating point tolerance)

    def test_caps_confidence_at_90_percent(self):
        """Test confidence capped at 0.9."""
        # 10 sources would be 1.5, but should cap at 0.9
        sources = [{"data": f"source{i}"} for i in range(10)]
        confidence = quality_assessors.calculate_overall_confidence(*sources)

        assert confidence == 0.9

    def test_ignores_none_sources(self):
        """Test None sources ignored."""
        confidence = quality_assessors.calculate_overall_confidence({"data": "source1"}, None, {"data": "source2"})

        assert confidence == 0.30  # Only 2 valid sources

    def test_ignores_non_dict_sources(self):
        """Test non-dict sources ignored."""
        confidence = quality_assessors.calculate_overall_confidence({"data": "source1"}, "invalid", ["also invalid"])

        assert confidence == 0.15  # Only 1 valid source

    def test_returns_default_for_no_valid_sources(self):
        """Test handling no valid sources."""
        confidence = quality_assessors.calculate_overall_confidence(None, "invalid")

        assert confidence == 0.0  # 0 valid sources

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        # Create mock that raises exception when used
        mock_source = Mock()
        mock_source.__bool__ = Mock(side_effect=Exception("Test error"))

        confidence = quality_assessors.calculate_overall_confidence(mock_source)

        assert confidence == 0.5


class TestAssessTranscriptQuality:
    """Test assess_transcript_quality function."""

    def test_assesses_high_quality_long_transcript(self):
        """Test high quality for comprehensive transcript."""
        transcript = "This is a comprehensive transcript. " * 50  # 200+ words

        score = quality_assessors.assess_transcript_quality(transcript)

        assert score > 0.7

    def test_assesses_medium_quality_moderate_transcript(self):
        """Test medium quality for moderate transcript."""
        transcript = "This is a moderate transcript. " * 15  # 60 words

        score = quality_assessors.assess_transcript_quality(transcript)

        assert 0.3 <= score <= 0.8  # 60 words gets 0.2 + other bonuses

    def test_assesses_low_quality_short_transcript(self):
        """Test low quality for short transcript."""
        transcript = "Short transcript"

        score = quality_assessors.assess_transcript_quality(transcript)

        assert score < 0.6  # Short transcript still gets some points

    def test_returns_zero_for_empty_transcript(self):
        """Test zero score for empty transcript."""
        score = quality_assessors.assess_transcript_quality("")

        assert score == 0.0

    def test_rewards_punctuation(self):
        """Test punctuation increases score."""
        with_punct = "This is a sentence. Another sentence! And a question?"
        without_punct = "This is a sentence Another sentence And a question"

        score_with = quality_assessors.assess_transcript_quality(with_punct)
        score_without = quality_assessors.assess_transcript_quality(without_punct)

        assert score_with > score_without

    def test_rewards_capitalization(self):
        """Test capitalization increases score."""
        with_caps = "This Is A Proper Transcript With Capitals And Structure"
        without_caps = "this is a transcript without capitals or structure"

        score_with = quality_assessors.assess_transcript_quality(with_caps)
        score_without = quality_assessors.assess_transcript_quality(without_caps)

        assert score_with > score_without

    def test_rewards_word_variety(self):
        """Test unique word ratio increases score."""
        varied = "The comprehensive analysis provides detailed insights about various topics and subjects"
        repetitive = "word word word word word word word word word word word word"

        score_varied = quality_assessors.assess_transcript_quality(varied)
        score_repetitive = quality_assessors.assess_transcript_quality(repetitive)

        assert score_varied > score_repetitive

    def test_handles_exception_returns_default(self):
        """Test exception handling."""
        score = quality_assessors.assess_transcript_quality(None)  # type: ignore

        assert score == 0.0  # None/empty returns 0.0 before exception handling


class TestIdentifyLearningOpportunities:
    """Test identify_learning_opportunities function."""

    def test_suggests_transcript_index_when_missing(self):
        """Test suggests transcript index when not present."""
        analysis_data = {}
        verification_data = {}

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data)

        assert any("transcript index" in opp.lower() for opp in opportunities)

    def test_suggests_timeline_anchors_when_missing(self):
        """Test suggests timeline anchors when not present."""
        analysis_data = {"transcript_index": {"some": "data"}}
        verification_data = {}

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data)

        assert any("timeline anchor" in opp.lower() for opp in opportunities)

    def test_suggests_fact_check_expansion_when_missing(self):
        """Test suggests fact-check expansion when not present."""
        analysis_data = {
            "transcript_index": {"some": "data"},
            "timeline_anchors": [{"time": 0}],
        }
        verification_data = {}

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data)

        assert any("fact-check" in opp.lower() for opp in opportunities)

    def test_checks_fact_data_fallback(self):
        """Test uses fact_data as fallback for fact_checks."""
        analysis_data = {
            "transcript_index": {"some": "data"},
            "timeline_anchors": [{"time": 0}],
        }
        verification_data = {}
        fact_data = {"fact_checks": {"verified_claims": 5}}

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data, fact_data)

        # Should NOT suggest fact-check expansion since fact_checks present in fact_data
        assert not any("fact-check" in opp.lower() for opp in opportunities)

    def test_suggests_bias_review_when_indicators_present(self):
        """Test suggests bias review when indicators detected."""
        analysis_data = {
            "transcript_index": {"some": "data"},
            "timeline_anchors": [{"time": 0}],
        }
        verification_data = {
            "fact_checks": {"verified": 5},
            "bias_indicators": ["confirmation_bias"],
        }

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data)

        assert any("bias indicator" in opp.lower() for opp in opportunities)

    def test_returns_default_when_no_opportunities(self):
        """Test returns default message when all checks pass."""
        analysis_data = {
            "transcript_index": {"some": "data"},
            "timeline_anchors": [{"time": 0}],
        }
        verification_data = {"fact_checks": {"verified": 5}}

        opportunities = quality_assessors.identify_learning_opportunities(analysis_data, verification_data)

        assert len(opportunities) == 1
        assert "retrospective" in opportunities[0].lower()

    def test_handles_none_values(self):
        """Test handles None values gracefully."""
        opportunities = quality_assessors.identify_learning_opportunities(None, None)  # type: ignore

        assert len(opportunities) > 0  # Should return opportunities, not crash


class TestGenerateEnhancementSuggestions:
    """Test generate_enhancement_suggestions function."""

    def test_creates_priority_actions_for_low_scores(self):
        """Test creates priority actions for scores below 0.4."""
        quality_dimensions = {
            "factual_accuracy": 0.3,
            "source_credibility": 0.2,
        }
        analysis_data = {}
        verification_data = {}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        assert len(result["priority_actions"]) == 2
        assert "urgent remediation" in result["priority_actions"][0].lower()

    def test_creates_watch_items_for_medium_scores(self):
        """Test creates watch items for scores 0.4-0.6."""
        quality_dimensions = {
            "factual_accuracy": 0.5,
            "source_credibility": 0.55,
        }
        analysis_data = {}
        verification_data = {}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        assert len(result["watch_items"]) == 2
        assert "monitor for drift" in result["watch_items"][0].lower()

    def test_no_actions_for_high_scores(self):
        """Test no actions/watch items for scores above 0.6."""
        quality_dimensions = {
            "factual_accuracy": 0.8,
            "source_credibility": 0.9,
        }
        analysis_data = {}
        verification_data = {}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        assert len(result["priority_actions"]) == 1
        assert "maintain current strategy" in result["priority_actions"][0].lower()
        assert len(result["watch_items"]) == 0

    def test_includes_context_metadata(self):
        """Test includes context from analysis/verification data."""
        quality_dimensions = {"factual_accuracy": 0.8}
        analysis_data = {"content_metadata": {"title": "Test Video", "platform": "YouTube"}}
        verification_data = {"source_validation": {"sources": ["credible.com"]}}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        assert result["context"]["title"] == "Test Video"
        assert result["context"]["platform"] == "YouTube"
        assert result["context"]["validated_sources"] is True

    def test_skips_non_numeric_dimensions(self):
        """Test skips non-numeric dimension values."""
        quality_dimensions = {
            "factual_accuracy": 0.3,
            "invalid_score": "not_a_number",  # type: ignore
        }
        analysis_data = {}
        verification_data = {}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        # Should only process factual_accuracy
        assert len(result["priority_actions"]) == 1

    def test_handles_empty_dimensions(self):
        """Test handles empty quality dimensions."""
        quality_dimensions = {}
        analysis_data = {}
        verification_data = {}

        result = quality_assessors.generate_enhancement_suggestions(
            quality_dimensions, analysis_data, verification_data
        )

        assert "priority_actions" in result
        assert "watch_items" in result
        assert "context" in result
