"""
Basic tests for Creator Operations system.

Simple tests that don't require heavy dependencies like torch.
"""

from platform.core.step_result import StepResult

import pytest


class TestBasicCreatorOps:
    """Basic test suite for Creator Operations system."""

    def test_step_result_success(self):
        """Test StepResult success creation."""
        result = StepResult.ok(test="data")
        assert result.success
        assert result.data == {"test": "data"}
        assert result.error is None

    def test_step_result_failure(self):
        """Test StepResult failure creation."""
        result = StepResult.fail("Test error")
        assert not result.success
        assert result.error == "Test error"
        assert result.data == {}

    def test_step_result_with_status(self):
        """Test StepResult with custom status."""
        result = StepResult(success=True, data={"test": "data"}, custom_status="custom_status")
        assert result.success
        assert result.data == {"test": "data"}
        assert result.custom_status == "custom_status"

    def test_step_result_error_with_status(self):
        """Test StepResult error with custom status."""
        result = StepResult(success=False, error="Test error", custom_status="error_status")
        assert not result.success
        assert result.error == "Test error"
        assert result.custom_status == "error_status"


if __name__ == "__main__":
    pytest.main([__file__])
