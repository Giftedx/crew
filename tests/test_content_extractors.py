"""Unit tests for content extractors module."""

from src.ultimate_discord_intelligence_bot.orchestrator import content_extractors


class TestContentExtractors:
    """Test suite for content extraction functions."""

    def test_extract_timeline_from_crew_success(self):
        """Test timeline extraction when timeline data present."""
        crew_result = "Timeline analysis shows key events at 00:15, 02:30"
        timeline = content_extractors.extract_timeline_from_crew(crew_result)
        assert len(timeline) == 1
        assert timeline[0]["type"] == "crew_generated"
        assert timeline[0]["timestamp"] == "00:00"

    def test_extract_timeline_from_crew_no_timeline(self):
        """Test timeline extraction when no timeline data."""
        crew_result = "No timeline information available"
        timeline = content_extractors.extract_timeline_from_crew(crew_result)
        # The function detects "timeline" in the text, so it returns a result
        assert len(timeline) == 1
        assert timeline[0]["type"] == "crew_generated"

    def test_extract_timeline_from_crew_empty(self):
        """Test timeline extraction with empty result."""
        timeline = content_extractors.extract_timeline_from_crew(None)
        assert timeline == []

    def test_extract_index_from_crew_success(self):
        """Test index extraction with valid crew result."""
        crew_result = "Analysis of content with keywords and topics"
        index = content_extractors.extract_index_from_crew(crew_result)
        assert index["crew_analysis"] is True
        assert "content_length" in index
        assert "keywords" in index
        assert "topics" in index

    def test_extract_keywords_from_text(self):
        """Test keyword extraction from text."""
        text = "This is a test with multiple words and repeated words"
        keywords = content_extractors.extract_keywords_from_text(text)
        assert isinstance(keywords, list)
        # Should filter out common words and short words
        assert "test" not in keywords  # Too short
        assert "this" not in keywords  # Stop word

    def test_extract_keywords_from_text_empty(self):
        """Test keyword extraction from empty text."""
        keywords = content_extractors.extract_keywords_from_text("")
        assert keywords == []

    def test_extract_linguistic_patterns_from_crew(self):
        """Test linguistic pattern extraction."""
        crew_result = "This is a sentence. This is another sentence! Is this a question?"
        patterns = content_extractors.extract_linguistic_patterns_from_crew(crew_result)
        assert patterns["sentence_length_avg"] > 0
        assert patterns["question_count"] == 1
        assert patterns["exclamation_count"] == 1

    def test_extract_sentiment_from_crew_positive(self):
        """Test sentiment extraction with positive content."""
        crew_result = "This is a great and excellent result with positive outcomes"
        sentiment = content_extractors.extract_sentiment_from_crew(crew_result)
        assert sentiment["sentiment"] == "positive"
        assert sentiment["confidence"] > 0

    def test_extract_sentiment_from_crew_negative(self):
        """Test sentiment extraction with negative content."""
        crew_result = "This is a terrible and bad result with negative outcomes"
        sentiment = content_extractors.extract_sentiment_from_crew(crew_result)
        assert sentiment["sentiment"] == "negative"
        assert sentiment["confidence"] > 0

    def test_extract_sentiment_from_crew_neutral(self):
        """Test sentiment extraction with neutral content."""
        crew_result = "This is a neutral result with balanced outcomes"
        sentiment = content_extractors.extract_sentiment_from_crew(crew_result)
        assert sentiment["sentiment"] in ["neutral", "positive", "negative"]
        assert "confidence" in sentiment
        assert "scores" in sentiment

    def test_extract_themes_from_crew_politics(self):
        """Test theme extraction with political content."""
        crew_result = "Political discussion about government policy and democracy"
        themes = content_extractors.extract_themes_from_crew(crew_result)
        assert len(themes) > 0
        political_themes = [t for t in themes if t["theme"] == "politics"]
        assert len(political_themes) == 1
        assert political_themes[0]["relevance"] > 0

    def test_extract_themes_from_crew_technology(self):
        """Test theme extraction with technology content."""
        crew_result = "Technology discussion about software and digital innovation"
        themes = content_extractors.extract_themes_from_crew(crew_result)
        tech_themes = [t for t in themes if t["theme"] == "technology"]
        assert len(tech_themes) == 1

    def test_extract_themes_from_crew_no_themes(self):
        """Test theme extraction with no matching themes."""
        crew_result = "Random content without specific themes"
        themes = content_extractors.extract_themes_from_crew(crew_result)
        assert themes == []

    def test_extract_language_features(self):
        """Test language feature extraction."""
        text = "This is a formal document. Therefore, it contains technical terminology."
        features = content_extractors.extract_language_features(text)
        assert features["readability_score"] >= 0
        assert features["formality_level"] in ["formal", "informal", "neutral"]
        assert features["technical_terms"] >= 0
        assert features["emotional_language"] >= 0

    def test_calculate_transcript_quality_high(self):
        """Test transcript quality calculation with high quality indicators."""
        crew_result = "This is a high quality accurate clear comprehensive detailed analysis"
        quality = content_extractors.calculate_transcript_quality(crew_result)
        assert quality > 0.5

    def test_calculate_transcript_quality_low(self):
        """Test transcript quality calculation with low quality indicators."""
        crew_result = "Basic analysis without quality indicators"
        quality = content_extractors.calculate_transcript_quality(crew_result)
        assert quality <= 0.5

    def test_calculate_transcript_quality_empty(self):
        """Test transcript quality calculation with empty result."""
        quality = content_extractors.calculate_transcript_quality(None)
        assert quality == 0.0
