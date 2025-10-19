"""Unit tests for content quality assessors module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import content_quality_assessors


class TestContentQualityAssessors:
    """Test suite for content quality assessors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_assess_content_coherence_good_transcript(self):
        """Test content coherence assessment with good transcript."""
        # Arrange
        analysis_data = {
            "transcript": "This is a comprehensive transcript with sufficient content. It contains multiple sentences and provides detailed information about the topic being discussed. The content is well-structured and coherent.",
            "linguistic_patterns": {"pattern1": "value1"},
            "sentiment_analysis": {"positive": 0.6},
            "content_metadata": {"title": "Test", "platform": "youtube", "word_count": 100, "quality_score": 0.8},
        }

        # Act
        result = content_quality_assessors.assess_content_coherence(analysis_data, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be good coherence

    def test_assess_content_coherence_short_transcript(self):
        """Test content coherence assessment with short transcript."""
        # Arrange
        analysis_data = {
            "transcript": "Short",
            "linguistic_patterns": {},
            "sentiment_analysis": {},
            "content_metadata": {},
        }

        # Act
        result = content_quality_assessors.assess_content_coherence(analysis_data, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result < 0.5  # Should be lower coherence due to short transcript

    def test_assess_content_coherence_empty_data(self):
        """Test content coherence assessment with empty data."""
        # Arrange
        analysis_data = {}

        # Act
        result = content_quality_assessors.assess_content_coherence(analysis_data, self.mock_logger)

        # Assert
        assert result == 0.5  # Default neutral score

    def test_assess_content_coherence_exception_handling(self):
        """Test content coherence assessment with exception handling."""
        # Arrange
        analysis_data = {"transcript": Mock(side_effect=Exception("Test error"))}

        # Act
        result = content_quality_assessors.assess_content_coherence(analysis_data, self.mock_logger)

        # Assert
        assert result == 0.5  # Default fallback score

    def test_assess_transcript_quality_good_transcript(self):
        """Test transcript quality assessment with good transcript."""
        # Arrange
        transcript = "This is a comprehensive transcript with sufficient content. It contains multiple sentences and provides detailed information about the topic being discussed. The content is well-structured and coherent with proper punctuation and capitalization."

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be good quality

    def test_assess_transcript_quality_empty_transcript(self):
        """Test transcript quality assessment with empty transcript."""
        # Arrange
        transcript = ""

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert result == 0.0

    def test_assess_transcript_quality_short_transcript(self):
        """Test transcript quality assessment with short transcript."""
        # Arrange
        transcript = "Short"

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result <= 0.5  # Should be lower or equal quality

    def test_assess_transcript_quality_no_punctuation(self):
        """Test transcript quality assessment with no punctuation."""
        # Arrange
        transcript = "This is a transcript with no punctuation it lacks proper sentence structure and capitalization"

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_transcript_quality_exception_handling(self):
        """Test transcript quality assessment with exception handling."""
        # Arrange
        transcript = Mock(side_effect=Exception("Test error"))

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert result == 0.5  # Default fallback score

    def test_assess_transcript_quality_repeated_words(self):
        """Test transcript quality assessment with many repeated words."""
        # Arrange
        transcript = (
            "word word word word word word word word word word word word word word word word word word word word"
        )

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        # Should have lower uniqueness ratio penalty

    def test_assess_content_coherence_with_custom_logger(self):
        """Test content coherence assessment with custom logger."""
        # Arrange
        custom_logger = Mock()
        analysis_data = {"transcript": "Test transcript"}

        # Act
        result = content_quality_assessors.assess_content_coherence(analysis_data, custom_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_transcript_quality_with_custom_logger(self):
        """Test transcript quality assessment with custom logger."""
        # Arrange
        custom_logger = Mock()
        transcript = "Test transcript"

        # Act
        result = content_quality_assessors.assess_transcript_quality(transcript, custom_logger)

        # Assert
        assert 0.0 <= result <= 1.0
