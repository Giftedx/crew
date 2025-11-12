"""Template tool demonstrating proper StepResult usage and type safety.

This template shows the correct patterns for implementing tools with:
- Complete type annotations
- Proper StepResult usage
- Input validation
- Error handling
- Tenant-aware design
"""

from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, ErrorContext, StepResult
from ultimate_discord_intelligence_bot.tools._base import BaseTool


logger = logging.getLogger(__name__)


class TemplateTool(BaseTool):
    """Template tool showing proper implementation patterns.

    This tool demonstrates the correct way to implement a tool with:
    - Complete type annotations
    - Proper StepResult usage
    - Input validation
    - Error handling
    - Tenant-aware design
    """

    name: str = "Template Tool"
    description: str = "A template showing proper tool implementation patterns"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the tool with optional configuration.

        Args:
            **kwargs: Tool-specific configuration options
        """
        super().__init__(**kwargs)

    def run(self, input_data: str, tenant: str = "default", workspace: str = "default", **kwargs: Any) -> StepResult:
        """Execute the tool with proper error handling and validation.

        Args:
            input_data: The input data to process
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization
            **kwargs: Additional tool-specific parameters

        Returns:
            StepResult with processed data or error information
        """
        try:
            validation_result = self._validate_inputs(input_data, tenant, workspace)
            if not validation_result.success:
                return validation_result
            result = self._process_data(input_data, tenant, workspace, **kwargs)
            logger.info(f"Tool {self.name} completed successfully for tenant {tenant}")
            return StepResult.ok(
                data=result,
                metadata={"tool": self.name, "tenant": tenant, "workspace": workspace, "input_length": len(input_data)},
            )
        except ValueError as e:
            logger.error(f"Validation error in {self.name}: {e}")
            return StepResult.validation_error(
                str(e),
                error_category=ErrorCategory.VALIDATION,
                metadata={"tool": self.name, "error_type": "ValueError"},
            )
        except Exception as e:
            logger.error(f"Unexpected error in {self.name}: {e}", exc_info=True)
            return StepResult.fail(
                f"Tool execution failed: {e!s}",
                error_category=ErrorCategory.PROCESSING,
                error_context=ErrorContext(
                    operation="tool_execution", component=self.name, details={"exception_type": type(e).__name__}
                ),
                metadata={"tool": self.name, "error_type": type(e).__name__},
            )

    def _validate_inputs(self, input_data: str, tenant: str, workspace: str) -> StepResult:
        """Validate input parameters.

        Args:
            input_data: The input data to validate
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating validation success or failure
        """
        if not input_data or not isinstance(input_data, str):
            return StepResult.validation_error(
                "input_data must be a non-empty string",
                error_category=ErrorCategory.INVALID_VALUE,
                metadata={"parameter": "input_data", "type": type(input_data).__name__},
            )
        if not tenant or not isinstance(tenant, str):
            return StepResult.validation_error(
                "tenant must be a non-empty string",
                error_category=ErrorCategory.MISSING_REQUIRED_FIELD,
                metadata={"parameter": "tenant"},
            )
        if not workspace or not isinstance(workspace, str):
            return StepResult.validation_error(
                "workspace must be a non-empty string",
                error_category=ErrorCategory.MISSING_REQUIRED_FIELD,
                metadata={"parameter": "workspace"},
            )
        if len(input_data) > 10000:
            return StepResult.validation_error(
                "input_data too long (max 10000 characters)",
                error_category=ErrorCategory.CONSTRAINT_VIOLATION,
                metadata={"parameter": "input_data", "length": len(input_data), "max_length": 10000},
            )
        return StepResult.ok(data={"validated": True})

    def _process_data(self, input_data: str, tenant: str, workspace: str, **kwargs: Any) -> dict[str, Any]:
        """Process the input data.

        Args:
            input_data: The input data to process
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            **kwargs: Additional processing parameters

        Returns:
            Dictionary containing processed results

        Raises:
            ValueError: If processing fails due to invalid data
            Exception: For other processing errors
        """
        processed_text = input_data.strip().upper()
        word_count = len(processed_text.split())
        char_count = len(processed_text)
        tenant_specific_result = f"{tenant}:{workspace}:{processed_text}"
        return {
            "processed_text": processed_text,
            "word_count": word_count,
            "char_count": char_count,
            "tenant_specific_result": tenant_specific_result,
            "processing_metadata": {"tenant": tenant, "workspace": workspace, "original_length": len(input_data)},
        }


class SpecializedTool(TemplateTool):
    """Example specialized tool showing inheritance patterns."""

    name: str = "Specialized Tool"
    description: str = "A specialized tool that extends the template"

    def __init__(self, special_param: str = "default", **kwargs: Any) -> None:
        """Initialize with specialized parameters.

        Args:
            special_param: Specialized configuration parameter
            **kwargs: Additional parameters passed to parent
        """
        super().__init__(**kwargs)
        self.special_param = special_param

    def _process_data(self, input_data: str, tenant: str, workspace: str, **kwargs: Any) -> dict[str, Any]:
        """Override processing with specialized logic."""
        base_result = super()._process_data(input_data, tenant, workspace, **kwargs)
        base_result["special_processing"] = f"Processed with {self.special_param}"
        base_result["special_param"] = self.special_param
        return base_result


__all__ = ["SpecializedTool", "TemplateTool"]
