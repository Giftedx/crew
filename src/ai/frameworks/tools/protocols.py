"""Universal tool protocols and data models.

This module defines the core abstractions for creating tools that work across
multiple AI frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ParameterSchema:
    """Schema definition for a tool parameter.

    This follows JSON Schema conventions and can be converted to framework-specific
    parameter representations.

    Attributes:
        type: Parameter type (string, number, boolean, object, array)
        description: Human-readable description for LLMs
        required: Whether this parameter is required
        default: Default value if not provided
        enum: List of allowed values (for restricted parameters)
        items: Schema for array items (if type is array)
        properties: Nested properties (if type is object)
    """

    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None
    items: ParameterSchema | None = None
    properties: dict[str, ParameterSchema] | None = None

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format (for OpenAI function calling)."""
        schema: dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }

        if self.enum is not None:
            schema["enum"] = self.enum

        if self.default is not None:
            schema["default"] = self.default

        if self.items is not None:
            schema["items"] = self.items.to_json_schema()

        if self.properties is not None:
            schema["properties"] = {name: prop.to_json_schema() for name, prop in self.properties.items()}

        return schema


@dataclass
class ToolMetadata:
    """Metadata for a universal tool.

    This provides additional information beyond the core tool definition,
    useful for documentation, discovery, and security.

    Attributes:
        category: Tool category (e.g., "web", "code", "data")
        return_type: Description of return value type
        examples: Example invocations with inputs and outputs
        requires_auth: Whether tool requires authentication
        version: Tool version for compatibility tracking
        tags: Searchable tags for discovery
    """

    category: str = "general"
    return_type: str = "string"
    examples: list[dict[str, Any]] = field(default_factory=list)
    requires_auth: bool = False
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "category": self.category,
            "return_type": self.return_type,
            "examples": self.examples,
            "requires_auth": self.requires_auth,
            "version": self.version,
            "tags": self.tags,
        }


@runtime_checkable
class UniversalTool(Protocol):
    """Protocol for tools that work across multiple AI frameworks.

    A UniversalTool provides a standard interface and can convert itself to
    framework-specific tool formats (CrewAI, LangChain, AutoGen, LlamaIndex).

    Implementations should provide:
    - name: Unique tool identifier (kebab-case recommended)
    - description: Natural language description for LLMs
    - parameters: Dict of parameter names to ParameterSchema
    - run: Async method that executes the tool
    - Conversion methods for each target framework

    Example:
        ```python
        class WebSearchTool(BaseUniversalTool):
            name = "web-search"
            description = "Search the web for information"
            parameters = {
                "query": ParameterSchema(
                    type="string",
                    description="Search query",
                    required=True
                )
            }

            async def run(self, query: str) -> str:
                # Implementation
                pass
        ```
    """

    name: str
    description: str
    parameters: dict[str, ParameterSchema]
    metadata: ToolMetadata

    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool parameters matching the parameters schema

        Returns:
            Tool execution result (type depends on tool)
        """
        ...

    def to_crewai_tool(self) -> Any:
        """Convert to CrewAI BaseTool format.

        Returns:
            CrewAI BaseTool instance

        Raises:
            ImportError: If CrewAI is not installed
        """
        ...

    def to_langchain_tool(self) -> Any:
        """Convert to LangChain Tool format.

        Returns:
            LangChain StructuredTool instance

        Raises:
            ImportError: If LangChain is not installed
        """
        ...

    def to_autogen_function(self) -> dict[str, Any]:
        """Convert to AutoGen/OpenAI function calling format.

        Returns:
            Dict with OpenAI function schema
        """
        ...

    def to_llamaindex_tool(self) -> Any:
        """Convert to LlamaIndex FunctionTool format.

        Returns:
            LlamaIndex FunctionTool instance

        Raises:
            ImportError: If LlamaIndex is not installed
        """
        ...

    def validate_parameters(self, **kwargs: Any) -> tuple[bool, str | None]:
        """Validate that provided parameters match the schema.

        Args:
            **kwargs: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...
