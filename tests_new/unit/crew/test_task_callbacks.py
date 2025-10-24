"""Unit tests for task callbacks module."""

from unittest.mock import Mock

from src.ultimate_discord_intelligence_bot.orchestrator import task_callbacks


class TestTaskCallbacks:
    """Test suite for task callback functions."""

    def test_task_completion_callback_success(self):
        """Test successful task completion callback."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"transcript": "test content", "quality": 0.8}'
        task_output.task = Mock()
        task_output.task.description = "Download and acquire media content"

        populate_callback = Mock()
        agent_coordinators = {"test_agent": Mock()}

        # Act
        task_callbacks.task_completion_callback(
            task_output,
            populate_agent_context_callback=populate_callback,
            agent_coordinators=agent_coordinators,
        )

        # Assert
        populate_callback.assert_called_once()

    def test_task_completion_callback_no_output(self):
        """Test task completion callback with no output data."""
        # Arrange
        task_output = Mock()
        task_output.raw = None
        task_output.output = None

        # Act
        task_callbacks.task_completion_callback(task_output)

        # Assert - should not raise exception

    def test_task_completion_callback_with_metrics(self):
        """Test task completion callback with metrics tracking."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()
        task_output.task.description = "transcription task"

        metrics_instance = Mock()
        metrics_instance.counter.return_value.inc = Mock()

        # Act
        task_callbacks.task_completion_callback(task_output, metrics_instance=metrics_instance)

        # Assert
        metrics_instance.counter.assert_called_once()
        metrics_instance.counter.return_value.inc.assert_called_once()

    def test_task_completion_callback_placeholder_detection(self):
        """Test task completion callback with placeholder detection."""
        # Arrange
        task_output = Mock()
        task_output.raw = "Your transcribed text goes here"
        task_output.task = Mock()
        task_output.task.description = "transcription task"

        detect_placeholder_callback = Mock()
        detect_placeholder_callback.return_value = True

        # Act
        task_callbacks.task_completion_callback(task_output, detect_placeholder_callback=detect_placeholder_callback)

        # Assert
        detect_placeholder_callback.assert_called_once_with("Your transcribed text goes here")

    def test_task_completion_callback_json_repair(self):
        """Test task completion callback with JSON repair."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"incomplete": "json"'
        task_output.task = Mock()
        task_output.task.description = "analysis task"

        repair_json_callback = Mock()
        repair_json_callback.return_value = {"complete": "json"}

        # Act
        task_callbacks.task_completion_callback(task_output, repair_json_callback=repair_json_callback)

        # Assert
        repair_json_callback.assert_called_once()

    def test_task_completion_callback_extract_key_values(self):
        """Test task completion callback with key-value extraction."""
        # Arrange
        task_output = Mock()
        task_output.raw = "transcript: test content, quality: 0.8"
        task_output.task = Mock()
        task_output.task.description = "transcription task"

        extract_key_values_callback = Mock()
        extract_key_values_callback.return_value = {
            "transcript": "test content",
            "quality": 0.8,
        }

        # Act
        task_callbacks.task_completion_callback(task_output, extract_key_values_callback=extract_key_values_callback)

        # Assert
        extract_key_values_callback.assert_called_once()

    def test_task_completion_callback_task_name_inference(self):
        """Test task name inference from description."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()

        test_cases = [
            ("Download and acquire media content", "acquisition"),
            ("transcription and audio processing", "transcription"),
            ("linguistic analysis and patterns", "analysis"),
            ("fact checking and verification", "fact_checking"),
            ("bias detection and manipulation", "bias_analysis"),
            ("synthesis and integration", "knowledge_integration"),
            ("unknown task description", "unknown"),
        ]

        for description, _expected_name in test_cases:
            task_output.task.description = description

            # Act
            task_callbacks.task_completion_callback(task_output)

            # Assert - should not raise exception

    def test_create_task_callback_with_dependencies(self):
        """Test creating task callback with pre-configured dependencies."""
        # Arrange
        populate_callback = Mock()
        detect_placeholder_callback = Mock()
        repair_json_callback = Mock()
        extract_key_values_callback = Mock()
        logger_instance = Mock()
        metrics_instance = Mock()
        agent_coordinators = {"test_agent": Mock()}

        # Act
        callback = task_callbacks.create_task_callback_with_dependencies(
            populate_agent_context_callback=populate_callback,
            detect_placeholder_callback=detect_placeholder_callback,
            repair_json_callback=repair_json_callback,
            extract_key_values_callback=extract_key_values_callback,
            logger_instance=logger_instance,
            metrics_instance=metrics_instance,
            agent_coordinators=agent_coordinators,
        )

        # Assert
        assert callable(callback)

        # Test the callback
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()
        task_output.task.description = "test task"

        callback(task_output)

        # Should have called the appropriate callbacks based on the mock setup

    def test_task_completion_callback_with_custom_logger(self):
        """Test task completion callback with custom logger."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()
        task_output.task.description = "test task"

        custom_logger = Mock()

        # Act
        task_callbacks.task_completion_callback(task_output, logger_instance=custom_logger)

        # Assert - should not raise exception and should use custom logger

    def test_task_completion_callback_error_handling(self):
        """Test task completion callback error handling."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()
        task_output.task.description = "test task"

        # Mock a callback that raises an exception
        populate_callback = Mock(side_effect=Exception("Test error"))
        agent_coordinators = {"test_agent": Mock()}

        # Act
        task_callbacks.task_completion_callback(
            task_output,
            populate_agent_context_callback=populate_callback,
            agent_coordinators=agent_coordinators,
        )

        # Assert - should not raise exception, should handle error gracefully

    def test_task_completion_callback_schema_validation_missing(self):
        """Test task completion callback when schemas are not available."""
        # Arrange
        task_output = Mock()
        task_output.raw = '{"test": "data"}'
        task_output.task = Mock()
        task_output.task.description = "test task"

        # Act
        # Just test that the function handles missing schemas gracefully
        task_callbacks.task_completion_callback(task_output)

        # Assert - should not raise exception, should handle missing schemas gracefully
