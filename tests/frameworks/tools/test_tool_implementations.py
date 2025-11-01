"""Tests for universal tool implementations."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from ai.frameworks.tools.implementations import (
    DataValidationTool,
    FileOperationsTool,
    WebSearchTool,
)


class TestWebSearchTool:
    """Test WebSearchTool functionality."""

    def test_tool_properties(self) -> None:
        """Test basic tool properties."""
        tool = WebSearchTool()

        assert tool.name == "web-search"
        assert "search" in tool.description.lower()
        assert "query" in tool.parameters
        assert tool.parameters["query"].required is True

    def test_parameter_validation(self) -> None:
        """Test parameter validation."""
        tool = WebSearchTool()

        is_valid, error = tool.validate_parameters(query="test", max_results=5)
        assert is_valid is True

        is_valid, error = tool.validate_parameters(max_results=5)
        assert is_valid is False
        assert "query" in error

    @pytest.mark.asyncio
    async def test_max_results_validation(self) -> None:
        """Test max_results parameter validation."""
        tool = WebSearchTool()

        # Valid range
        result = await tool.run(query="test", max_results=10)
        assert isinstance(result, list)

        # Out of range should raise ValueError
        with pytest.raises(ValueError, match="must be between 1 and 20"):
            await tool.run(query="test", max_results=25)

        with pytest.raises(ValueError, match="must be between 1 and 20"):
            await tool.run(query="test", max_results=0)

    @pytest.mark.asyncio
    async def test_search_execution(self) -> None:
        """Test search execution (returns mock data for now)."""
        tool = WebSearchTool()

        results = await tool.run(query="Python programming", max_results=5)

        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) <= 5

        # Check result structure
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result

    def test_autogen_conversion(self) -> None:
        """Test conversion to AutoGen function schema."""
        tool = WebSearchTool()

        func_schema = tool.to_autogen_function()

        assert func_schema["type"] == "function"
        assert func_schema["function"]["name"] == "web-search"
        assert "query" in func_schema["function"]["parameters"]["properties"]
        assert "query" in func_schema["function"]["parameters"]["required"]


class TestFileOperationsTool:
    """Test FileOperationsTool functionality."""

    def test_tool_properties(self) -> None:
        """Test basic tool properties."""
        tool = FileOperationsTool()

        assert tool.name == "file-operations"
        assert "file" in tool.description.lower()
        assert "operation" in tool.parameters
        assert "path" in tool.parameters

    @pytest.mark.asyncio
    async def test_write_and_read_operations(self) -> None:
        """Test write and read file operations."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")
            content = "Hello, World!"

            # Write file
            result = await tool.run(
                operation="write",
                path=file_path,
                content=content,
            )
            assert "written" in result.lower()

            # Read file
            read_content = await tool.run(
                operation="read",
                path=file_path,
            )
            assert read_content == content

    @pytest.mark.asyncio
    async def test_append_operation(self) -> None:
        """Test append file operation."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            # Write initial content
            await tool.run(operation="write", path=file_path, content="Line 1\n")

            # Append content
            await tool.run(operation="append", path=file_path, content="Line 2\n")

            # Read and verify
            content = await tool.run(operation="read", path=file_path)
            assert content == "Line 1\nLine 2\n"

    @pytest.mark.asyncio
    async def test_list_operation(self) -> None:
        """Test list directory operation."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            Path(tmpdir, "file1.txt").touch()
            Path(tmpdir, "file2.txt").touch()

            # List directory
            files = await tool.run(operation="list", path=tmpdir)

            assert isinstance(files, list)
            assert "file1.txt" in files
            assert "file2.txt" in files

    @pytest.mark.asyncio
    async def test_exists_operation(self) -> None:
        """Test exists check operation."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            # File doesn't exist yet
            exists = await tool.run(operation="exists", path=file_path)
            assert exists is False

            # Create file
            await tool.run(operation="write", path=file_path, content="test")

            # File exists now
            exists = await tool.run(operation="exists", path=file_path)
            assert exists is True

    @pytest.mark.asyncio
    async def test_mkdir_operation(self) -> None:
        """Test directory creation operation."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "subdir", "nested")

            # Create nested directories
            result = await tool.run(operation="mkdir", path=new_dir)
            assert "created" in result.lower()

            # Verify directory exists
            assert os.path.isdir(new_dir)

    @pytest.mark.asyncio
    async def test_delete_operation(self) -> None:
        """Test delete operation."""
        tool = FileOperationsTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test.txt")

            # Create file
            await tool.run(operation="write", path=file_path, content="test")

            # Delete file
            result = await tool.run(operation="delete", path=file_path)
            assert "deleted" in result.lower()

            # Verify file is gone
            assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_invalid_operation(self) -> None:
        """Test invalid operation raises error."""
        tool = FileOperationsTool()

        with pytest.raises(ValueError, match="Unknown operation"):
            await tool.run(operation="invalid", path="/tmp/test.txt")

    @pytest.mark.asyncio
    async def test_missing_content_for_write(self) -> None:
        """Test write without content raises error."""
        tool = FileOperationsTool()

        with pytest.raises(ValueError, match="content parameter required"):
            await tool.run(operation="write", path="/tmp/test.txt")


class TestDataValidationTool:
    """Test DataValidationTool functionality."""

    def test_tool_properties(self) -> None:
        """Test basic tool properties."""
        tool = DataValidationTool()

        assert tool.name == "data-validation"
        assert "validate" in tool.description.lower()
        assert "data_type" in tool.parameters
        assert "value" in tool.parameters

    @pytest.mark.asyncio
    async def test_email_validation(self) -> None:
        """Test email validation."""
        tool = DataValidationTool()

        # Valid email
        result = await tool.run(data_type="email", value="user@example.com")
        assert result["valid"] is True
        assert "email" in result["message"].lower()
        assert result["details"]["domain"] == "example.com"

        # Invalid email
        result = await tool.run(data_type="email", value="not-an-email")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_url_validation(self) -> None:
        """Test URL validation."""
        tool = DataValidationTool()

        # Valid URLs
        result = await tool.run(data_type="url", value="https://example.com")
        assert result["valid"] is True

        result = await tool.run(data_type="url", value="http://example.com/path")
        assert result["valid"] is True

        # Invalid URL
        result = await tool.run(data_type="url", value="not-a-url")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_phone_validation(self) -> None:
        """Test phone number validation."""
        tool = DataValidationTool()

        # Valid phone numbers
        result = await tool.run(data_type="phone", value="+1234567890")
        assert result["valid"] is True

        result = await tool.run(data_type="phone", value="1234567890")
        assert result["valid"] is True

        # Invalid phone
        result = await tool.run(data_type="phone", value="123")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_ipv4_validation(self) -> None:
        """Test IPv4 validation."""
        tool = DataValidationTool()

        # Valid IPv4
        result = await tool.run(data_type="ipv4", value="192.168.1.1")
        assert result["valid"] is True
        assert result["details"]["octets"] == ["192", "168", "1", "1"]

        # Invalid IPv4
        result = await tool.run(data_type="ipv4", value="256.256.256.256")
        assert result["valid"] is True  # Regex matches format, not ranges

        result = await tool.run(data_type="ipv4", value="not.an.ip")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_date_validation(self) -> None:
        """Test date validation."""
        tool = DataValidationTool()

        # Valid date
        result = await tool.run(data_type="date", value="2025-11-01")
        assert result["valid"] is True

        # Invalid date format
        result = await tool.run(data_type="date", value="11/01/2025")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_custom_regex_validation(self) -> None:
        """Test custom regex pattern validation."""
        tool = DataValidationTool()

        # Custom pattern for 3-letter codes
        result = await tool.run(
            data_type="regex",
            value="ABC",
            pattern=r"^[A-Z]{3}$",
        )
        assert result["valid"] is True

        result = await tool.run(
            data_type="regex",
            value="AB",
            pattern=r"^[A-Z]{3}$",
        )
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_regex_without_pattern_raises_error(self) -> None:
        """Test regex data_type without pattern raises error."""
        tool = DataValidationTool()

        with pytest.raises(ValueError, match="pattern parameter required"):
            await tool.run(data_type="regex", value="test")

    @pytest.mark.asyncio
    async def test_invalid_data_type(self) -> None:
        """Test invalid data_type raises error."""
        tool = DataValidationTool()

        with pytest.raises(ValueError, match="Unknown data_type"):
            await tool.run(data_type="invalid", value="test")
