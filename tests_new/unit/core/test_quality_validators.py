"""Unit tests for quality validators module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import quality_validators


class TestQualityValidators:
    """Test suite for quality validators."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.mock_metrics = Mock()

    def test_detect_placeholder_responses_transcription_short(self):
        """Test placeholder detection for short transcript."""
        # Arrange
        task_name = "transcription"
        output_data = {"transcript": "Short"}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_transcription_placeholder_pattern(self):
        """Test placeholder detection for placeholder pattern in transcript."""
        # Arrange
        task_name = "transcription"
        output_data = {"transcript": "Your transcribed text goes here"}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_analysis_placeholder_insights(self):
        """Test placeholder detection for placeholder pattern in insights."""
        # Arrange
        task_name = "analysis"
        output_data = {"insights": "Example content here"}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_analysis_placeholder_themes(self):
        """Test placeholder detection for placeholder pattern in themes."""
        # Arrange
        task_name = "analysis"
        output_data = {"themes": ["placeholder theme"]}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_analysis_placeholder_fallacies(self):
        """Test placeholder detection for placeholder pattern in fallacies."""
        # Arrange
        task_name = "analysis"
        output_data = {"fallacies": {"test": "mock data"}}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.warning.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_verification_empty(self):
        """Test placeholder detection for empty verification results."""
        # Arrange
        task_name = "verification"
        output_data = {"verified_claims": [], "fact_check_results": {}}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_called()
        self.mock_metrics.counter.assert_called()

    def test_detect_placeholder_responses_no_placeholder_found(self):
        """Test placeholder detection when no placeholders are found."""
        # Arrange
        task_name = "transcription"
        output_data = {
            "transcript": "This is a valid transcript with sufficient content to pass validation and should not trigger any detection warnings or errors because it contains enough words and no suspicious patterns"
        }

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, self.mock_metrics)

        # Assert
        self.mock_logger.error.assert_not_called()
        self.mock_logger.warning.assert_not_called()

    def test_detect_placeholder_responses_without_metrics(self):
        """Test placeholder detection without metrics instance."""
        # Arrange
        task_name = "transcription"
        output_data = {"transcript": "Short"}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, self.mock_logger, None)

        # Assert
        self.mock_logger.error.assert_called()

    def test_validate_stage_data_success(self):
        """Test successful stage data validation."""
        # Arrange
        stage_name = "test_stage"
        required_keys = ["key1", "key2"]
        data = {"key1": "value1", "key2": "value2", "extra": "value"}

        # Act & Assert - should not raise
        quality_validators.validate_stage_data(stage_name, required_keys, data)

    def test_validate_stage_data_missing_keys(self):
        """Test stage data validation with missing keys."""
        # Arrange
        stage_name = "test_stage"
        required_keys = ["key1", "key2", "key3"]
        data = {"key1": "value1", "key2": "value2"}

        # Act & Assert
        try:
            quality_validators.validate_stage_data(stage_name, required_keys, data)
            raise AssertionError("Expected ValueError to be raised")
        except ValueError as e:
            assert "key3" in str(e)

    def test_validate_stage_data_empty_keys(self):
        """Test stage data validation with empty required keys."""
        # Arrange
        stage_name = "test_stage"
        required_keys = []
        data = {"key1": "value1"}

        # Act & Assert - should not raise
        quality_validators.validate_stage_data(stage_name, required_keys, data)

    def test_detect_placeholder_responses_with_custom_logger(self):
        """Test placeholder detection with custom logger."""
        # Arrange
        custom_logger = Mock()
        task_name = "transcription"
        output_data = {"transcript": "Short"}

        # Act
        quality_validators.detect_placeholder_responses(task_name, output_data, custom_logger, self.mock_metrics)

        # Assert
        custom_logger.error.assert_called()
        self.mock_logger.error.assert_not_called()
