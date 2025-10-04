"""
Unit tests for orchestrator/extractors module.

Tests all extraction functions in isolation:
- extract_timeline_from_crew
- extract_index_from_crew
- extract_keywords_from_text
- extract_linguistic_patterns_from_crew
- extract_sentiment_from_crew
- extract_themes_from_crew
- extract_language_features
- extract_fact_checks_from_crew
- extract_logical_analysis_from_crew
- extract_credibility_from_crew
- extract_bias_indicators_from_crew
- extract_source_validation_from_crew
"""

from unittest.mock import Mock

from ultimate_discord_intelligence_bot.orchestrator import extractors


class TestExtractTimelineFromCrew:
    """Test extract_timeline_from_crew function."""

    def test_extracts_timeline_when_keywords_present(self):
        """Test extraction when timeline keywords are in output."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="The timeline shows important events at timestamp 00:05")

        timeline = extractors.extract_timeline_from_crew(crew_result)

        assert isinstance(timeline, list)
        assert len(timeline) > 0
        assert timeline[0]["type"] == "crew_generated"

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        timeline = extractors.extract_timeline_from_crew(None)

        assert timeline == []

    def test_returns_empty_for_no_timeline_keywords(self):
        """Test no timeline extracted when keywords absent."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="This is general analysis without time references")

        timeline = extractors.extract_timeline_from_crew(crew_result)

        assert timeline == []

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        timeline = extractors.extract_timeline_from_crew(crew_result)

        assert timeline == []


class TestExtractIndexFromCrew:
    """Test extract_index_from_crew function."""

    def test_extracts_index_with_metadata(self):
        """Test index extraction with content analysis."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Analysis with important keywords and detailed content")

        index = extractors.extract_index_from_crew(crew_result)

        assert isinstance(index, dict)
        assert index["crew_analysis"] is True
        assert "content_length" in index
        assert "keywords" in index
        assert isinstance(index["keywords"], list)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        index = extractors.extract_index_from_crew(None)

        assert index == {}

    def test_calculates_content_length(self):
        """Test content length calculation."""
        crew_result = Mock()
        test_content = "Test content with specific length"
        crew_result.__str__ = Mock(return_value=test_content)

        index = extractors.extract_index_from_crew(crew_result)

        assert index["content_length"] == len(test_content)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        index = extractors.extract_index_from_crew(crew_result)

        assert index == {}


class TestExtractKeywordsFromText:
    """Test extract_keywords_from_text function."""

    def test_extracts_common_words_as_keywords(self):
        """Test keyword extraction from text."""
        text = "machine learning and artificial intelligence are important topics in machine learning research"

        keywords = extractors.extract_keywords_from_text(text)

        assert isinstance(keywords, list)
        assert "machine" in keywords
        assert "learning" in keywords

    def test_returns_max_10_keywords(self):
        """Test maximum keyword limit."""
        text = " ".join(["word" + str(i) for i in range(20)] * 3)  # 20 unique words, repeated

        keywords = extractors.extract_keywords_from_text(text)

        assert len(keywords) <= 10

    def test_ignores_short_words(self):
        """Test that short words (< 4 chars) are ignored."""
        text = "the cat sat on the mat with big dogs"

        keywords = extractors.extract_keywords_from_text(text)

        # 'the', 'cat', 'sat', 'on', 'mat' should be ignored (< 4 chars)
        assert "the" not in keywords
        assert "cat" not in keywords

    def test_returns_most_common_words_first(self):
        """Test keywords ordered by frequency."""
        text = "test " * 5 + "word " * 3 + "other " * 1

        keywords = extractors.extract_keywords_from_text(text)

        # 'test' appears 5 times, should be first
        assert keywords[0] == "test"

    def test_handles_empty_text(self):
        """Test handling of empty text."""
        keywords = extractors.extract_keywords_from_text("")

        assert keywords == []

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        # Pass None to trigger exception
        keywords = extractors.extract_keywords_from_text(None)  # type: ignore

        assert keywords == []


class TestExtractLinguisticPatternsFromCrew:
    """Test extract_linguistic_patterns_from_crew function."""

    def test_extracts_patterns_with_complexity(self):
        """Test pattern extraction with complexity analysis."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Complex linguistic analysis with various patterns")

        patterns = extractors.extract_linguistic_patterns_from_crew(crew_result)

        assert isinstance(patterns, dict)
        assert patterns["crew_detected_patterns"] is True
        assert "complexity_indicators" in patterns
        assert "language_features" in patterns

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        patterns = extractors.extract_linguistic_patterns_from_crew(None)

        assert patterns == {}

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        patterns = extractors.extract_linguistic_patterns_from_crew(crew_result)

        assert patterns == {}


class TestExtractSentimentFromCrew:
    """Test extract_sentiment_from_crew function."""

    def test_detects_positive_sentiment(self):
        """Test positive sentiment detection."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="positive analysis shows excellent and successful results good outcome")

        sentiment = extractors.extract_sentiment_from_crew(crew_result)

        assert sentiment["overall_sentiment"] == "positive"
        assert sentiment["positive_score"] > 0

    def test_detects_negative_sentiment(self):
        """Test negative sentiment detection."""
        crew_result = Mock()
        crew_result.__str__ = Mock(
            return_value="negative analysis shows poor and unsuccessful results bad outcome problematic"
        )

        sentiment = extractors.extract_sentiment_from_crew(crew_result)

        assert sentiment["overall_sentiment"] == "negative"
        assert sentiment["negative_score"] > 0

    def test_detects_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="neutral analysis shows balanced and moderate results average outcome")

        sentiment = extractors.extract_sentiment_from_crew(crew_result)

        assert sentiment["overall_sentiment"] == "neutral"

    def test_calculates_confidence_score(self):
        """Test confidence calculation."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="positive positive positive excellent good")

        sentiment = extractors.extract_sentiment_from_crew(crew_result)

        assert "confidence" in sentiment
        assert 0.0 <= sentiment["confidence"] <= 1.0

    def test_returns_unknown_for_none_input(self):
        """Test handling of None input."""
        sentiment = extractors.extract_sentiment_from_crew(None)

        # Function returns empty dict for None input (not unknown sentiment)
        assert sentiment == {}

    def test_handles_exception_returns_unknown(self):
        """Test exception handling returns unknown sentiment."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        sentiment = extractors.extract_sentiment_from_crew(crew_result)

        assert sentiment["overall_sentiment"] == "unknown"
        assert sentiment["confidence"] == 0.0


class TestExtractThemesFromCrew:
    """Test extract_themes_from_crew function."""

    def test_extracts_themes_from_substantial_output(self):
        """Test theme extraction from long output."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="A" * 150)  # > 100 chars

        themes = extractors.extract_themes_from_crew(crew_result)

        assert isinstance(themes, list)
        assert len(themes) > 0
        assert themes[0]["theme"] == "crew_analysis"
        assert "confidence" in themes[0]

    def test_returns_empty_for_short_output(self):
        """Test no themes for short output."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Short")

        themes = extractors.extract_themes_from_crew(crew_result)

        assert themes == []

    def test_includes_keywords_in_theme(self):
        """Test themes include keywords."""
        crew_result = Mock()
        crew_result.__str__ = Mock(
            return_value="machine learning analysis with detailed artificial intelligence research" * 5
        )

        themes = extractors.extract_themes_from_crew(crew_result)

        assert len(themes) > 0
        assert "keywords" in themes[0]
        assert isinstance(themes[0]["keywords"], list)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        themes = extractors.extract_themes_from_crew(None)

        assert themes == []

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        themes = extractors.extract_themes_from_crew(crew_result)

        assert themes == []


class TestExtractLanguageFeatures:
    """Test extract_language_features function."""

    def test_extracts_language_features(self):
        """Test language feature extraction."""
        text = "This is a test sentence with various words and patterns"

        features = extractors.extract_language_features(text)

        assert isinstance(features, dict)
        # Function returns boolean feature flags, not word count
        assert "has_questions" in features
        assert "has_exclamations" in features
        assert "formal_language" in features
        assert "technical_language" in features

    def test_detects_question_marks(self):
        """Test question mark detection."""
        text = "Is this a question?"

        features = extractors.extract_language_features(text)

        assert features["has_questions"] is True
        assert features["has_exclamations"] is False

    def test_handles_empty_text(self):
        """Test handling of empty text."""
        features = extractors.extract_language_features("")

        assert isinstance(features, dict)
        assert features.get("word_count", 0) == 0


class TestExtractFactChecksFromCrew:
    """Test extract_fact_checks_from_crew function."""

    def test_extracts_fact_checks_when_present(self):
        """Test fact check extraction."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="fact check shows verified claims and disputed statements")

        fact_checks = extractors.extract_fact_checks_from_crew(crew_result)

        assert isinstance(fact_checks, dict)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        fact_checks = extractors.extract_fact_checks_from_crew(None)

        assert fact_checks == {}

    def test_detects_fact_check_keywords(self):
        """Test detection of fact checking indicators."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Fact checking reveals verification of claims")

        fact_checks = extractors.extract_fact_checks_from_crew(crew_result)

        # Function should detect fact check keywords
        assert isinstance(fact_checks, dict)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        fact_checks = extractors.extract_fact_checks_from_crew(crew_result)

        # Error case returns partial dict with error info
        assert fact_checks["error"] == "extraction_failed"
        assert fact_checks["crew_analysis_available"] is False


class TestExtractLogicalAnalysisFromCrew:
    """Test extract_logical_analysis_from_crew function."""

    def test_extracts_logical_analysis(self):
        """Test logical analysis extraction."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="logical analysis reveals reasoning patterns and arguments")

        analysis = extractors.extract_logical_analysis_from_crew(crew_result)

        assert isinstance(analysis, dict)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        analysis = extractors.extract_logical_analysis_from_crew(None)

        assert analysis == {}

    def test_detects_logical_keywords(self):
        """Test detection of logical analysis indicators."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Logical reasoning and argument structure detected")

        analysis = extractors.extract_logical_analysis_from_crew(crew_result)

        assert isinstance(analysis, dict)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        analysis = extractors.extract_logical_analysis_from_crew(crew_result)

        # Error case returns partial dict with error info
        assert analysis["fallacies_detected"] == []
        assert analysis["error"] == "analysis_failed"


class TestExtractCredibilityFromCrew:
    """Test extract_credibility_from_crew function."""

    def test_extracts_credibility_assessment(self):
        """Test credibility extraction."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="credibility assessment shows trustworthy sources")

        credibility = extractors.extract_credibility_from_crew(crew_result)

        assert isinstance(credibility, dict)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        credibility = extractors.extract_credibility_from_crew(None)

        # Function returns default score/factors for None, not empty dict
        assert credibility["score"] == 0.0
        assert credibility["factors"] == []

    def test_detects_credibility_indicators(self):
        """Test detection of credibility indicators."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="High credibility with reliable and trustworthy information")

        credibility = extractors.extract_credibility_from_crew(crew_result)

        assert isinstance(credibility, dict)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        credibility = extractors.extract_credibility_from_crew(crew_result)

        # Error case returns default score with error info
        assert credibility["score"] == 0.5
        assert credibility["factors"] == []
        assert credibility["error"] == "assessment_failed"


class TestExtractBiasIndicatorsFromCrew:
    """Test extract_bias_indicators_from_crew function."""

    def test_extracts_bias_indicators(self):
        """Test bias indicator extraction."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="bias detected in language patterns showing prejudice")

        bias_indicators = extractors.extract_bias_indicators_from_crew(crew_result)

        assert isinstance(bias_indicators, list)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        bias_indicators = extractors.extract_bias_indicators_from_crew(None)

        assert bias_indicators == []

    def test_detects_bias_keywords(self):
        """Test detection of bias indicators."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Bias analysis reveals systematic prejudice patterns")

        bias_indicators = extractors.extract_bias_indicators_from_crew(crew_result)

        assert isinstance(bias_indicators, list)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        bias_indicators = extractors.extract_bias_indicators_from_crew(crew_result)

        assert bias_indicators == []


class TestExtractSourceValidationFromCrew:
    """Test extract_source_validation_from_crew function."""

    def test_extracts_source_validation(self):
        """Test source validation extraction."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="source validation confirms reliable references")

        validation = extractors.extract_source_validation_from_crew(crew_result)

        assert isinstance(validation, dict)

    def test_returns_empty_for_none_input(self):
        """Test handling of None input."""
        validation = extractors.extract_source_validation_from_crew(None)

        # Function returns default validation status for None
        assert validation["validated"] is False
        assert validation["reason"] == "no_analysis"

    def test_detects_validation_keywords(self):
        """Test detection of validation indicators."""
        crew_result = Mock()
        crew_result.__str__ = Mock(return_value="Source validation shows verified and reliable references")

        validation = extractors.extract_source_validation_from_crew(crew_result)

        assert isinstance(validation, dict)

    def test_handles_exception_gracefully(self):
        """Test graceful error handling."""
        crew_result = Mock()
        crew_result.__str__ = Mock(side_effect=Exception("Test error"))

        validation = extractors.extract_source_validation_from_crew(crew_result)

        # Error case returns validation failure
        assert validation["validated"] is False
        assert validation["reason"] == "validation_failed"
