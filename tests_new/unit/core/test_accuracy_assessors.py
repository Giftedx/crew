"""Unit tests for accuracy assessors module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import accuracy_assessors


class TestAccuracyAssessors:
    """Test suite for accuracy assessors."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_clamp_score_normal_value(self):
        """Test clamp_score with normal value."""
        # Act
        result = accuracy_assessors.clamp_score(0.5)

        # Assert
        assert result == 0.5

    def test_clamp_score_above_maximum(self):
        """Test clamp_score with value above maximum."""
        # Act
        result = accuracy_assessors.clamp_score(1.5)

        # Assert
        assert result == 1.0

    def test_clamp_score_below_minimum(self):
        """Test clamp_score with value below minimum."""
        # Act
        result = accuracy_assessors.clamp_score(-0.5)

        # Assert
        assert result == 0.0

    def test_clamp_score_custom_bounds(self):
        """Test clamp_score with custom bounds."""
        # Act
        result = accuracy_assessors.clamp_score(5.0, 0.0, 10.0)

        # Assert
        assert result == 5.0

    def test_clamp_score_invalid_value(self):
        """Test clamp_score with invalid value."""
        # Act
        result = accuracy_assessors.clamp_score("invalid")

        # Assert
        assert result == 0.0  # Default minimum

    def test_assess_factual_accuracy_with_verification_data(self):
        """Test factual accuracy assessment with verification data."""
        # Arrange
        verification_data = {
            "fact_checks": {
                "verified_claims": 5,
                "disputed_claims": 1,
                "evidence": ["evidence1", "evidence2"],
            }
        }

        # Act
        result = accuracy_assessors.assess_factual_accuracy(verification_data, None, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should be good accuracy

    def test_assess_factual_accuracy_with_fact_data(self):
        """Test factual accuracy assessment with fact data."""
        # Arrange
        fact_data = {
            "fact_checks": {
                "verified_claims": 3,
                "disputed_claims": 2,
                "evidence": ["evidence1"],
            }
        }

        # Act
        result = accuracy_assessors.assess_factual_accuracy(None, fact_data, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_factual_accuracy_with_lists(self):
        """Test factual accuracy assessment with list data."""
        # Arrange
        verification_data = {
            "fact_verification": {
                "verified_claims": ["claim1", "claim2", "claim3"],
                "disputed_claims": ["claim4"],
                "evidence": ["evidence1", "evidence2", "evidence3"],
            }
        }

        # Act
        result = accuracy_assessors.assess_factual_accuracy(verification_data, None, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_factual_accuracy_no_claims(self):
        """Test factual accuracy assessment with no claims."""
        # Arrange
        verification_data = {"fact_checks": {"verified_claims": 0, "disputed_claims": 0}}

        # Act
        result = accuracy_assessors.assess_factual_accuracy(verification_data, None, self.mock_logger)

        # Assert
        assert result == 0.5  # Default score

    def test_assess_factual_accuracy_exception_handling(self):
        """Test factual accuracy assessment with exception handling."""
        # Arrange
        verification_data = {"fact_checks": Mock(side_effect=Exception("Test error"))}

        # Act
        result = accuracy_assessors.assess_factual_accuracy(verification_data, None, self.mock_logger)

        # Assert
        assert result == 0.5  # Default fallback score

    def test_assess_source_credibility_validated_true(self):
        """Test source credibility assessment with validated true."""
        # Arrange
        verification_data = {"source_validation": {"validated": True}}

        # Act
        result = accuracy_assessors.assess_source_credibility(None, verification_data, self.mock_logger)

        # Assert
        assert result == 0.85

    def test_assess_source_credibility_validated_false(self):
        """Test source credibility assessment with validated false."""
        # Arrange
        verification_data = {"source_validation": {"validated": False}}

        # Act
        result = accuracy_assessors.assess_source_credibility(None, verification_data, self.mock_logger)

        # Assert
        assert result == 0.35

    def test_assess_source_credibility_with_reliability_score(self):
        """Test source credibility assessment with reliability score."""
        # Arrange
        knowledge_data = {"fact_check_results": {"source_reliability": 0.8}}

        # Act
        result = accuracy_assessors.assess_source_credibility(knowledge_data, None, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_source_credibility_with_reliability_string(self):
        """Test source credibility assessment with reliability string."""
        # Arrange
        knowledge_data = {"fact_check_results": {"source_reliability": "high"}}

        # Act
        result = accuracy_assessors.assess_source_credibility(knowledge_data, None, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_source_credibility_with_metadata(self):
        """Test source credibility assessment with metadata."""
        # Arrange
        knowledge_data = {
            "content_metadata": {
                "source_url": "https://example.com",
                "platform": "youtube",
            }
        }

        # Act
        result = accuracy_assessors.assess_source_credibility(knowledge_data, None, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0
        assert result > 0.5  # Should have bonus for metadata

    def test_assess_source_credibility_with_credibility_assessment(self):
        # Arrange
        verification_data = {"credibility_assessment": {"score": 0.9}}

        # Act
        result = accuracy_assessors.assess_source_credibility(None, verification_data, self.mock_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_source_credibility_exception_handling(self):
        """Test source credibility assessment with exception handling."""
        # Arrange
        verification_data = {"source_validation": Mock(side_effect=Exception("Test error"))}

        # Act
        result = accuracy_assessors.assess_source_credibility(None, verification_data, self.mock_logger)

        # Assert
        assert result == 0.5  # Default fallback score

    def test_assess_factual_accuracy_with_custom_logger(self):
        """Test factual accuracy assessment with custom logger."""
        # Arrange
        custom_logger = Mock()
        verification_data = {"fact_checks": {"verified_claims": 3, "disputed_claims": 1}}

        # Act
        result = accuracy_assessors.assess_factual_accuracy(verification_data, None, custom_logger)

        # Assert
        assert 0.0 <= result <= 1.0

    def test_assess_source_credibility_with_custom_logger(self):
        """Test source credibility assessment with custom logger."""
        # Arrange
        custom_logger = Mock()
        verification_data = {"source_validation": {"validated": True}}

        # Act
        result = accuracy_assessors.assess_source_credibility(None, verification_data, custom_logger)

        # Assert
        assert result == 0.85
