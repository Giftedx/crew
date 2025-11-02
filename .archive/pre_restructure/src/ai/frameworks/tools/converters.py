"""Universal tool conversion implementations.

This module provides the BaseUniversalTool class with default implementations
of framework-specific conversion methods.
"""

from __future__ import annotations

import asyncio
from typing import Any, ClassVar

import structlog

from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class BaseUniversalTool:
    """Base implementation of UniversalTool with framework conversions.

    Subclasses should define:
    - name: str
    - description: str
    - parameters: dict[str, ParameterSchema]
    - async def run(self, **kwargs) -> Any

    This base class provides default implementations of all conversion methods.
    """

    name: str = "base-tool"
    description: str = "Base universal tool"
    parameters: ClassVar[dict[str, ParameterSchema]] = {}
    metadata: ToolMetadata = ToolMetadata()

    async def run(self, **kwargs: Any) -> Any:
        """Execute the tool. Subclasses must override this."""
        raise NotImplementedError(f"Tool {self.name} must implement run()")

    def validate_parameters(self, **kwargs: Any) -> tuple[bool, str | None]:
        """Validate provided parameters against schema."""
        # Check for required parameters
        for param_name, param_schema in self.parameters.items():
            if param_schema.required and param_name not in kwargs:
                return False, f"Missing required parameter: {param_name}"

        # Check for unknown parameters
        for param_name in kwargs:
            if param_name not in self.parameters:
                return False, f"Unknown parameter: {param_name}"

        return True, None

    def to_crewai_tool(self) -> Any:
        """Convert to CrewAI BaseTool format."""
        try:
            from crewai.tools import BaseTool
        except ImportError as e:
            logger.error("crewai_not_installed", tool=self.name)
            raise ImportError("CrewAI is not installed. Install with: pip install crewai") from e

        # Create a custom BaseTool subclass
        tool_instance = self

        class CrewAIToolWrapper(BaseTool):
            name: str = tool_instance.name
            description: str = tool_instance.description

            def _run(self, **kwargs: Any) -> Any:
                """Synchronous wrapper for async run method."""
                # Validate parameters
                is_valid, error = tool_instance.validate_parameters(**kwargs)
                if not is_valid:
                    raise ValueError(error)

                # Run the async method
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                return loop.run_until_complete(tool_instance.run(**kwargs))

        return CrewAIToolWrapper()

    def to_langchain_tool(self) -> Any:
        """Convert to LangChain StructuredTool format."""
        try:
            from langchain_core.tools import StructuredTool
        except ImportError as e:
            logger.error("langchain_not_installed", tool=self.name)
            raise ImportError("LangChain is not installed. Install with: pip install langchain-core") from e

        # Create async function wrapper
        async def async_func(**kwargs: Any) -> Any:
            is_valid, error = self.validate_parameters(**kwargs)
            if not is_valid:
                raise ValueError(error)
            return await self.run(**kwargs)

        # Build parameter description
        {name: schema.description for name, schema in self.parameters.items()}

        return StructuredTool.from_function(
            coroutine=async_func,
            name=self.name,
            description=self.description,
            args_schema=None,  # Could create Pydantic model here
            return_direct=False,
        )

    def to_autogen_function(self) -> dict[str, Any]:
        """Convert to AutoGen/OpenAI function calling format."""
        # Build properties from parameters
        properties = {}
        required = []

        for param_name, param_schema in self.parameters.items():
            properties[param_name] = param_schema.to_json_schema()
            if param_schema.required:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_llamaindex_tool(self) -> Any:
        """Convert to LlamaIndex FunctionTool format."""
        try:
            from llama_index.core.tools import FunctionTool
        except ImportError as e:
            logger.error("llamaindex_not_installed", tool=self.name)
            raise ImportError("LlamaIndex is not installed. Install with: pip install llama-index-core") from e

        # Create async wrapper function
        async def async_func(**kwargs: Any) -> Any:
            is_valid, error = self.validate_parameters(**kwargs)
            if not is_valid:
                raise ValueError(error)
            return await self.run(**kwargs)

        return FunctionTool.from_defaults(
            async_fn=async_func,
            name=self.name,
            description=self.description,
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}')"
