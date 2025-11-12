"""Test template demonstrating comprehensive tool testing patterns.

This template shows how to properly test tools with:
- Unit tests for all methods
- Error scenario testing
- Input validation testing
- Tenant isolation testing
- Mock usage patterns
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.template_tool import SpecializedTool, TemplateTool


class TestTemplateTool:
    """Comprehensive test suite for TemplateTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tool = TemplateTool()
        self.valid_input = "test input data"
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"

    def test_successful_execution(self) -> None:
        """Test successful tool execution."""
        result = self.tool.run(self.valid_input, self.tenant, self.workspace)
        assert result.success
        assert result.data is not None
        assert "processed_text" in result.data
        assert result.data["processed_text"] == "TEST INPUT DATA"
        assert result.data["word_count"] == 3
        assert result.data["char_count"] == 17
        assert result.metadata["tool"] == "Template Tool"
        assert result.metadata["tenant"] == self.tenant

    def test_input_validation_empty_input(self) -> None:
        """Test validation with empty input."""
        result = self.tool.run("", self.tenant, self.workspace)
        assert not result.success
        assert "must be a non-empty string" in result.error

    def test_input_validation_none_input(self) -> None:
        """Test validation with None input."""
        result = self.tool.run(None, self.tenant, self.workspace)
        assert not result.success
        assert "must be a non-empty string" in result.error

    def test_input_validation_invalid_tenant(self) -> None:
        """Test validation with invalid tenant."""
        result = self.tool.run(self.valid_input, "", self.workspace)
        assert not result.success
        assert "tenant must be a non-empty string" in result.error

    def test_input_validation_invalid_workspace(self) -> None:
        """Test validation with invalid workspace."""
        result = self.tool.run(self.valid_input, self.tenant, "")
        assert not result.success
        assert "workspace must be a non-empty string" in result.error

    def test_input_validation_too_long(self) -> None:
        """Test validation with input that's too long."""
        long_input = "x" * 10001
        result = self.tool.run(long_input, self.tenant, self.workspace)
        assert not result.success
        assert "too long" in result.error

    def test_tenant_isolation(self) -> None:
        """Test that tenant isolation works correctly."""
        result1 = self.tool.run(self.valid_input, "tenant1", self.workspace)
        result2 = self.tool.run(self.valid_input, "tenant2", self.workspace)
        assert result1.success
        assert result2.success
        tenant_result1 = result1.data["tenant_specific_result"]
        tenant_result2 = result2.data["tenant_specific_result"]
        assert tenant_result1.startswith("tenant1:")
        assert tenant_result2.startswith("tenant2:")
        assert tenant_result1 != tenant_result2

    def test_workspace_isolation(self) -> None:
        """Test that workspace isolation works correctly."""
        result1 = self.tool.run(self.valid_input, self.tenant, "workspace1")
        result2 = self.tool.run(self.valid_input, self.tenant, "workspace2")
        assert result1.success
        assert result2.success
        tenant_result1 = result1.data["tenant_specific_result"]
        tenant_result2 = result2.data["tenant_specific_result"]
        assert "workspace1" in tenant_result1
        assert "workspace2" in tenant_result2
        assert tenant_result1 != tenant_result2

    def test_metadata_inclusion(self) -> None:
        """Test that metadata is properly included."""
        result = self.tool.run(self.valid_input, self.tenant, self.workspace)
        assert result.success
        assert result.metadata["tool"] == "Template Tool"
        assert result.metadata["tenant"] == self.tenant
        assert result.metadata["workspace"] == self.workspace
        assert result.metadata["input_length"] == len(self.valid_input)

    @patch("ultimate_discord_intelligence_bot.tools.template_tool.logger")
    def test_logging_on_success(self, mock_logger: Mock) -> None:
        """Test that success is properly logged."""
        result = self.tool.run(self.valid_input, self.tenant, self.workspace)
        assert result.success
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "completed successfully" in log_call_args
        assert self.tenant in log_call_args

    @patch("ultimate_discord_intelligence_bot.tools.template_tool.logger")
    def test_logging_on_error(self, mock_logger: Mock) -> None:
        """Test that errors are properly logged."""
        result = self.tool.run("", self.tenant, self.workspace)
        assert not result.success
        mock_logger.error.assert_called_once()
        log_call_args = mock_logger.error.call_args[0][0]
        assert "Validation error" in log_call_args

    def test_stepresult_compatibility(self) -> None:
        """Test that StepResult is properly compatible with dict interface."""
        result = self.tool.run(self.valid_input, self.tenant, self.workspace)
        assert result["status"] == "success"
        assert "processed_text" in result["data"]
        result_dict = dict(result)
        assert result_dict["status"] == "success"
        assert "data" in result_dict


class TestSpecializedTool:
    """Test suite for SpecializedTool."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.special_param = "special_value"
        self.tool = SpecializedTool(special_param=self.special_param)
        self.valid_input = "test input"
        self.tenant = "test_tenant"
        self.workspace = "test_workspace"

    def test_specialized_initialization(self) -> None:
        """Test that specialized tool initializes correctly."""
        assert self.tool.special_param == self.special_param
        assert self.tool.name == "Specialized Tool"

    def test_specialized_processing(self) -> None:
        """Test that specialized processing works correctly."""
        result = self.tool.run(self.valid_input, self.tenant, self.workspace)
        assert result.success
        assert result.data["special_processing"] == f"Processed with {self.special_param}"
        assert result.data["special_param"] == self.special_param
        assert result.data["processed_text"] == "TEST INPUT"
        assert result.data["word_count"] == 2

    def test_default_special_param(self) -> None:
        """Test that default special parameter works."""
        tool = SpecializedTool()
        result = tool.run(self.valid_input, self.tenant, self.workspace)
        assert result.success
        assert result.data["special_processing"] == "Processed with default"
        assert result.data["special_param"] == "default"


class TestToolErrorScenarios:
    """Test various error scenarios across tools."""

    def test_network_timeout_simulation(self) -> None:
        """Test how tools handle simulated network timeouts."""
        tool = TemplateTool()
        with patch.object(tool, "_process_data", side_effect=TimeoutError("Network timeout")):
            result = tool.run("test", "tenant", "workspace")
            assert not result.success
            assert "Tool execution failed" in result.error

    def test_memory_error_simulation(self) -> None:
        """Test how tools handle simulated memory errors."""
        tool = TemplateTool()
        with patch.object(tool, "_process_data", side_effect=MemoryError("Out of memory")):
            result = tool.run("test", "tenant", "workspace")
            assert not result.success
            assert "Tool execution failed" in result.error

    def test_validation_error_propagation(self) -> None:
        """Test that validation errors are properly propagated."""
        tool = TemplateTool()
        with patch.object(tool, "_validate_inputs", return_value=StepResult.fail("Custom validation error")):
            result = tool.run("test", "tenant", "workspace")
            assert not result.success
            assert "Custom validation error" in result.error


@pytest.mark.parametrize(
    "input_data,expected_success",
    [
        ("normal text", True),
        ("text with numbers 123", True),
        ("text with symbols !@#$%", True),
        ("", False),
        ("x" * 10001, False),
    ],
)
def test_input_validation_parameterized(input_data: str, expected_success: bool) -> None:
    """Test input validation with various inputs."""
    tool = TemplateTool()
    result = tool.run(input_data, "tenant", "workspace")
    assert result.success == expected_success


@pytest.fixture
def tool_instance() -> TemplateTool:
    """Fixture providing a tool instance."""
    return TemplateTool()


@pytest.fixture
def specialized_tool_instance() -> SpecializedTool:
    """Fixture providing a specialized tool instance."""
    return SpecializedTool(special_param="test_param")


def test_tool_with_fixtures(tool_instance: TemplateTool, specialized_tool_instance: SpecializedTool) -> None:
    """Test tools using fixtures."""
    result1 = tool_instance.run("test", "tenant", "workspace")
    result2 = specialized_tool_instance.run("test", "tenant", "workspace")
    assert result1.success
    assert result2.success
    assert result2.data["special_param"] == "test_param"


if __name__ == "__main__":
    pytest.main([__file__])
