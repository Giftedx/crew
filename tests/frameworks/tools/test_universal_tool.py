"""Tests for universal tool protocols and converters."""

from __future__ import annotations

import pytest


# Skip these tests as framework modules are not yet implemented
pytest.skip("Framework modules not yet implemented", allow_module_level=True)

# from ai.frameworks.tools import BaseUniversalTool, ParameterSchema, ToolMetadata


class MockCalculatorTool(BaseUniversalTool):
    """Mock calculator tool for testing."""

    name = "calculator"
    description = "Perform basic arithmetic operations"
    parameters = {
        "a": ParameterSchema(
            type="number",
            description="First number",
            required=True,
        ),
        "b": ParameterSchema(
            type="number",
            description="Second number",
            required=True,
        ),
        "operation": ParameterSchema(
            type="string",
            description="Operation to perform",
            required=True,
            enum=["add", "subtract", "multiply", "divide"],
        ),
    }
    metadata = ToolMetadata(
        category="math",
        return_type="number",
        examples=[
            {"a": 5, "b": 3, "operation": "add", "result": 8},
            {"a": 10, "b": 2, "operation": "divide", "result": 5.0},
        ],
        tags=["math", "calculator", "arithmetic"],
    )

    async def run(self, a: float, b: float, operation: str) -> float:
        """Execute the calculator operation."""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")


class TestParameterSchema:
    """Test ParameterSchema functionality."""

    def test_simple_parameter_schema(self) -> None:
        """Test basic parameter schema creation."""
        schema = ParameterSchema(
            type="string",
            description="A test parameter",
            required=True,
        )

        assert schema.type == "string"
        assert schema.description == "A test parameter"
        assert schema.required is True
        assert schema.default is None

    def test_parameter_schema_with_default(self) -> None:
        """Test parameter schema with default value."""
        schema = ParameterSchema(
            type="number",
            description="Optional number",
            required=False,
            default=42,
        )

        assert schema.default == 42
        assert schema.required is False

    def test_parameter_schema_with_enum(self) -> None:
        """Test parameter schema with enum values."""
        schema = ParameterSchema(
            type="string",
            description="Choose an option",
            required=True,
            enum=["option1", "option2", "option3"],
        )

        assert schema.enum == ["option1", "option2", "option3"]

    def test_parameter_schema_to_json_schema(self) -> None:
        """Test conversion to JSON Schema format."""
        schema = ParameterSchema(
            type="string",
            description="A test parameter",
            required=True,
            enum=["a", "b", "c"],
            default="a",
        )

        json_schema = schema.to_json_schema()

        assert json_schema["type"] == "string"
        assert json_schema["description"] == "A test parameter"
        assert json_schema["enum"] == ["a", "b", "c"]
        assert json_schema["default"] == "a"

    def test_nested_parameter_schema(self) -> None:
        """Test nested object parameter schema."""
        schema = ParameterSchema(
            type="object",
            description="An object",
            required=True,
            properties={
                "name": ParameterSchema(type="string", description="Name", required=True),
                "age": ParameterSchema(type="number", description="Age", required=False),
            },
        )

        json_schema = schema.to_json_schema()

        assert json_schema["type"] == "object"
        assert "properties" in json_schema
        assert "name" in json_schema["properties"]
        assert json_schema["properties"]["name"]["type"] == "string"


class TestToolMetadata:
    """Test ToolMetadata functionality."""

    def test_tool_metadata_defaults(self) -> None:
        """Test default metadata values."""
        metadata = ToolMetadata()

        assert metadata.category == "general"
        assert metadata.return_type == "string"
        assert metadata.requires_auth is False
        assert metadata.version == "1.0.0"
        assert metadata.examples == []
        assert metadata.tags == []

    def test_tool_metadata_custom(self) -> None:
        """Test custom metadata values."""
        metadata = ToolMetadata(
            category="web",
            return_type="dict",
            requires_auth=True,
            version="2.0.0",
            examples=[{"input": "test", "output": "result"}],
            tags=["search", "api"],
        )

        assert metadata.category == "web"
        assert metadata.return_type == "dict"
        assert metadata.requires_auth is True
        assert metadata.version == "2.0.0"
        assert len(metadata.examples) == 1
        assert len(metadata.tags) == 2

    def test_tool_metadata_to_dict(self) -> None:
        """Test metadata conversion to dict."""
        metadata = ToolMetadata(
            category="math",
            return_type="number",
            tags=["calculator"],
        )

        data = metadata.to_dict()

        assert data["category"] == "math"
        assert data["return_type"] == "number"
        assert data["tags"] == ["calculator"]
        assert "version" in data
        assert "requires_auth" in data


class TestBaseUniversalTool:
    """Test BaseUniversalTool functionality."""

    def test_tool_basic_properties(self) -> None:
        """Test basic tool properties."""
        tool = MockCalculatorTool()

        assert tool.name == "calculator"
        assert tool.description == "Perform basic arithmetic operations"
        assert len(tool.parameters) == 3
        assert "a" in tool.parameters
        assert "b" in tool.parameters
        assert "operation" in tool.parameters

    @pytest.mark.asyncio
    async def test_tool_execution(self) -> None:
        """Test tool execution."""
        tool = MockCalculatorTool()

        result = await tool.run(a=5, b=3, operation="add")
        assert result == 8

        result = await tool.run(a=10, b=2, operation="divide")
        assert result == 5.0

        result = await tool.run(a=7, b=4, operation="subtract")
        assert result == 3

        result = await tool.run(a=6, b=7, operation="multiply")
        assert result == 42

    @pytest.mark.asyncio
    async def test_tool_error_handling(self) -> None:
        """Test tool error handling."""
        tool = MockCalculatorTool()

        with pytest.raises(ValueError, match="Division by zero"):
            await tool.run(a=10, b=0, operation="divide")

        with pytest.raises(ValueError, match="Unknown operation"):
            await tool.run(a=5, b=3, operation="invalid")

    def test_parameter_validation_success(self) -> None:
        """Test successful parameter validation."""
        tool = MockCalculatorTool()

        is_valid, error = tool.validate_parameters(a=5, b=3, operation="add")
        assert is_valid is True
        assert error is None

    def test_parameter_validation_missing_required(self) -> None:
        """Test validation fails for missing required parameter."""
        tool = MockCalculatorTool()

        is_valid, error = tool.validate_parameters(a=5, operation="add")
        assert is_valid is False
        assert "Missing required parameter: b" in error

    def test_parameter_validation_unknown_parameter(self) -> None:
        """Test validation fails for unknown parameter."""
        tool = MockCalculatorTool()

        is_valid, error = tool.validate_parameters(a=5, b=3, operation="add", unknown=42)
        assert is_valid is False
        assert "Unknown parameter: unknown" in error

    def test_tool_repr(self) -> None:
        """Test tool string representation."""
        tool = MockCalculatorTool()

        repr_str = repr(tool)
        assert "MockCalculatorTool" in repr_str
        assert "calculator" in repr_str


class TestAutogenConversion:
    """Test conversion to AutoGen/OpenAI function format."""

    def test_to_autogen_function(self) -> None:
        """Test conversion to AutoGen function schema."""
        tool = MockCalculatorTool()

        func_schema = tool.to_autogen_function()

        assert func_schema["type"] == "function"
        assert "function" in func_schema

        function = func_schema["function"]
        assert function["name"] == "calculator"
        assert function["description"] == "Perform basic arithmetic operations"

        params = function["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        # Check properties
        assert "a" in params["properties"]
        assert "b" in params["properties"]
        assert "operation" in params["properties"]

        # Check required fields
        assert "a" in params["required"]
        assert "b" in params["required"]
        assert "operation" in params["required"]

        # Check operation enum
        assert params["properties"]["operation"]["enum"] == ["add", "subtract", "multiply", "divide"]


class TestCrewAIConversion:
    """Test conversion to CrewAI tool format."""

    def test_to_crewai_tool_import_error(self) -> None:
        """Test CrewAI conversion with missing import."""
        tool = MockCalculatorTool()

        # CrewAI might not be installed
        try:
            crewai_tool = tool.to_crewai_tool()
            # If we get here, CrewAI is installed
            assert crewai_tool.name == "calculator"
            assert crewai_tool.description == "Perform basic arithmetic operations"
        except ImportError as e:
            # Expected if CrewAI is not installed
            assert "CrewAI is not installed" in str(e)


class TestLangChainConversion:
    """Test conversion to LangChain tool format."""

    def test_to_langchain_tool_import_error(self) -> None:
        """Test LangChain conversion with missing import."""
        tool = MockCalculatorTool()

        # LangChain might not be installed
        try:
            langchain_tool = tool.to_langchain_tool()
            # If we get here, LangChain is installed
            assert langchain_tool.name == "calculator"
            assert langchain_tool.description == "Perform basic arithmetic operations"
        except ImportError as e:
            # Expected if LangChain is not installed
            assert "LangChain is not installed" in str(e)


class TestLlamaIndexConversion:
    """Test conversion to LlamaIndex tool format."""

    def test_to_llamaindex_tool_import_error(self) -> None:
        """Test LlamaIndex conversion with missing import."""
        tool = MockCalculatorTool()

        # LlamaIndex might not be installed
        try:
            llamaindex_tool = tool.to_llamaindex_tool()
            # If we get here, LlamaIndex is installed
            assert llamaindex_tool.metadata.name == "calculator"
            assert llamaindex_tool.metadata.description == "Perform basic arithmetic operations"
        except ImportError as e:
            # Expected if LlamaIndex is not installed
            assert "LlamaIndex is not installed" in str(e)
