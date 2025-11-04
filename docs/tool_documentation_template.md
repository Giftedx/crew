# Tool Documentation Template

## Standard Tool Documentation Format

All tools should follow this comprehensive documentation pattern:

```python
class MyTool(BaseTool[StepResult]):
    """Brief one-line description of what this tool does.

    Detailed description of the tool's purpose, capabilities, and when to use it.
    Include any important considerations, limitations, or dependencies.

    Args:
        content: Content to process (str or dict)
        tenant: Tenant identifier for data isolation
        workspace: Workspace identifier for organization
        **kwargs: Additional tool-specific parameters

    Returns:
        StepResult with processed data and metadata

    Raises:
        StepResult.fail: If processing fails for any reason

    Example:
        >>> tool = MyTool()
        >>> result = tool._run("content", "tenant1", "workspace1")
        >>> assert result.success
        >>> print(result.data)
    """

    name: str = "Tool Display Name"
    description: str = "Brief description for agent selection"

    def _run(self, content: str, tenant: str, workspace: str, **kwargs) -> StepResult:
        """Process content with comprehensive error handling and context.

        Args:
            content: The content to process
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier
            **kwargs: Additional parameters

        Returns:
            StepResult with processed data or error information
        """
        # Implementation here
        pass
```

## Documentation Requirements

### Class-Level Documentation

- **One-line summary**: Clear, concise description
- **Detailed description**: Purpose, capabilities, use cases
- **Args section**: All parameters with types and descriptions
- **Returns section**: StepResult structure and data format
- **Raises section**: Error conditions and handling
- **Example section**: Working code example

### Method Documentation

- **Purpose**: What the method does
- **Parameters**: All inputs with types
- **Returns**: StepResult structure
- **Error handling**: How errors are categorized and handled

### StepResult Standardization

- Use appropriate `ErrorCategory` enum values
- Include `ErrorContext` for debugging
- Mark retryable errors correctly
- Provide meaningful error messages

## Error Handling Patterns

### Standard Error Categories

```python
from ultimate_discord_intelligence_bot.step_result import (
    StepResult,
    ErrorCategory,
    ErrorContext
)

# Network errors (retryable)
return StepResult.network_error(
    error="Connection failed",
    context=ErrorContext(operation="download", component="YouTubeTool")
)

# Validation errors (not retryable)
return StepResult.validation_error(
    error="Invalid URL format",
    context=ErrorContext(operation="validate_input", component="YouTubeTool")
)

# Processing errors (may be retryable)
return StepResult.processing_error(
    error="Transcription failed",
    context=ErrorContext(operation="transcribe", component="AudioTool")
)
```

### Success Patterns

```python
# Standard success
return StepResult.ok(data=result)

# Success with warnings
return StepResult.success_with_warnings(
    warnings=["Low confidence transcription"],
    data=result
)

# Skipped operations
return StepResult.skip(
    reason="No content to process",
    data={"skipped": True}
)
```
