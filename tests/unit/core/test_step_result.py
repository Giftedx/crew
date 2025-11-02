"""Tests for StepResult."""

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestStepResult:
    """Test cases for StepResult."""

    def test_step_result_initialization(self):
        """Test StepResult initialization."""
        result = StepResult()
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "data")
        assert hasattr(result, "error")

    def test_step_result_success(self):
        """Test successful StepResult."""
        data = {"test": "data"}
        result = StepResult.ok(data=data)

        assert result.success is True
        assert result.data == data
        assert result.error is None

    def test_step_result_failure(self):
        """Test failed StepResult."""
        error = "Test error"
        result = StepResult.fail(error=error)

        assert result.success is False
        assert result.data is None
        assert result.error == error

    def test_step_result_with_status(self):
        """Test StepResult with status."""
        data = {"test": "data"}
        status = "success"
        result = StepResult(data=data, status=status)

        assert result.success is True
        assert result.data == data
        assert result.status == status

    def test_step_result_with_metadata(self):
        """Test StepResult with metadata."""
        data = {"test": "data"}
        metadata = {"processing_time": 1.5}
        result = StepResult(data=data, metadata=metadata)

        assert result.success is True
        assert result.data == data
        assert result.metadata == metadata

    def test_step_result_equality(self):
        """Test StepResult equality."""
        result1 = StepResult.ok(data={"test": "data"})
        result2 = StepResult.ok(data={"test": "data"})
        result3 = StepResult.fail(error="Test error")

        assert result1 == result2
        assert result1 != result3

    def test_step_result_string_representation(self):
        """Test StepResult string representation."""
        result = StepResult.ok(data={"test": "data"})

        assert "StepResult" in str(result)
        assert "success=True" in str(result)
        assert "data={'test': 'data'}" in str(result)

    def test_step_result_to_dict(self):
        """Test StepResult to_dict conversion."""
        data = {"test": "data"}
        metadata = {"processing_time": 1.5}
        result = StepResult(data=data, metadata=metadata)

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["data"] == data
        assert result_dict["metadata"] == metadata
        assert result_dict["error"] is None

    def test_step_result_from_dict(self):
        """Test StepResult from_dict conversion."""
        result_dict = {
            "success": True,
            "data": {"test": "data"},
            "metadata": {"processing_time": 1.5},
            "error": None,
        }

        result = StepResult.from_dict(result_dict)

        assert result.success is True
        assert result.data == {"test": "data"}
        assert result.metadata == {"processing_time": 1.5}
        assert result.error is None

    def test_step_result_chain_operations(self):
        """Test StepResult chain operations."""
        result = StepResult.ok(data={"initial": "data"})

        # Chain operations
        result = result.with_data({"updated": "data"})
        result = result.with_metadata({"processing_time": 1.5})

        assert result.success is True
        assert result.data == {"updated": "data"}
        assert result.metadata == {"processing_time": 1.5}

    def test_step_result_error_handling(self):
        """Test StepResult error handling."""
        result = StepResult.fail(error="Test error")

        assert result.success is False
        assert result.error == "Test error"
        assert result.data is None

    def test_step_result_validation(self):
        """Test StepResult validation."""
        # Valid success result
        result = StepResult.ok(data={"test": "data"})
        assert result.is_valid()

        # Valid failure result
        result = StepResult.fail(error="Test error")
        assert result.is_valid()

        # Invalid result - both data and error
        result = StepResult(data={"test": "data"}, error="Test error")
        assert not result.is_valid()

    def test_step_result_serialization(self):
        """Test StepResult serialization."""
        data = {"test": "data"}
        metadata = {"processing_time": 1.5}
        result = StepResult(data=data, metadata=metadata)

        # Test JSON serialization
        import json

        json_str = json.dumps(result.to_dict())
        result_dict = json.loads(json_str)

        new_result = StepResult.from_dict(result_dict)
        assert new_result == result

    def test_step_result_context_manager(self):
        """Test StepResult as context manager."""
        with StepResult.ok(data={"test": "data"}) as result:
            assert result.success is True
            assert result.data == {"test": "data"}

    def test_step_result_boolean_conversion(self):
        """Test StepResult boolean conversion."""
        success_result = StepResult.ok(data={"test": "data"})
        failure_result = StepResult.fail(error="Test error")

        assert bool(success_result) is True
        assert bool(failure_result) is False

    def test_step_result_contains(self):
        """Test StepResult contains operation."""
        result = StepResult.ok(data={"test": "data", "nested": {"key": "value"}})

        assert "test" in result
        assert "nested" in result
        assert "nonexistent" not in result

    def test_step_result_get(self):
        """Test StepResult get operation."""
        result = StepResult.ok(data={"test": "data"})

        assert result.get("test") == "data"
        assert result.get("nonexistent") is None
        assert result.get("nonexistent", "default") == "default"

    def test_step_result_items(self):
        """Test StepResult items operation."""
        result = StepResult.ok(data={"test": "data", "another": "value"})

        items = list(result.items())
        assert ("test", "data") in items
        assert ("another", "value") in items

    def test_step_result_keys(self):
        """Test StepResult keys operation."""
        result = StepResult.ok(data={"test": "data", "another": "value"})

        keys = list(result.keys())
        assert "test" in keys
        assert "another" in keys

    def test_step_result_values(self):
        """Test StepResult values operation."""
        result = StepResult.ok(data={"test": "data", "another": "value"})

        values = list(result.values())
        assert "data" in values
        assert "value" in values

    def test_step_result_len(self):
        """Test StepResult length operation."""
        result = StepResult.ok(data={"test": "data", "another": "value"})

        assert len(result) == 2

    def test_step_result_iteration(self):
        """Test StepResult iteration."""
        result = StepResult.ok(data={"test": "data", "another": "value"})

        items = list(result)
        assert ("test", "data") in items
        assert ("another", "value") in items
