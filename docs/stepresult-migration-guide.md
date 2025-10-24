# StepResult Migration Guide

This guide provides comprehensive instructions for migrating tools to use the StepResult pattern for consistent error handling and result normalization.

## Overview

The StepResult pattern is the standard way to handle tool execution results in the Ultimate Discord Intelligence Bot. It provides:

- Consistent error handling across all tools
- Granular error categorization
- Intelligent recovery strategies
- Enhanced debugging information
- PII filtering for safe logging

## Migration Checklist

### 1. Import StepResult

Add the StepResult import to your tool:

```python
from ultimate_discord_intelligence_bot.step_result import StepResult
```

### 2. Update Return Type Annotation

Change your tool's return type to StepResult:

```python
def run(self, input_data: str, tenant: str, workspace: str) -> StepResult:
    # Tool implementation
```

### 3. Replace Return Statements

Replace all return statements with StepResult methods:

#### Before (Legacy)

```python
def run(self, data: str) -> dict:
    try:
        result = process_data(data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

#### After (StepResult)

```python
def run(self, data: str) -> StepResult:
    try:
        result = process_data(data)
        return StepResult.ok(data=result)
    except Exception as e:
        return StepResult.fail(str(e))
```

## StepResult Methods

### Success Results

```python
# Basic success
return StepResult.ok(data={"key": "value"})

# Success with metadata
return StepResult.ok(
    data={"result": "processed"},
    metadata={"processing_time": 1.5}
)

# Success with warnings
return StepResult.success_with_warnings(
    warnings=["Deprecated API used"],
    data={"result": "processed"}
)
```

### Error Results

```python
# Basic error
return StepResult.fail("Operation failed")

# Error with category
return StepResult.fail(
    "Network timeout",
    error_category=ErrorCategory.TIMEOUT,
    retryable=True
)

# Specific error types
return StepResult.validation_error("Invalid input format")
return StepResult.network_error("Connection failed")
return StepResult.model_error("Inference failed")
return StepResult.database_error("Query failed")
```

### Special Results

```python
# Skipped operation
return StepResult.skip(reason="No data to process")

# Uncertain outcome
return StepResult.uncertain(data={"confidence": 0.6})

# Not found
return StepResult.not_found("Resource not found")

# Rate limited
return StepResult.rate_limited("API rate limit exceeded")
```

## Error Categories

Use appropriate error categories for better handling:

```python
from ultimate_discord_intelligence_bot.step_result import ErrorCategory

# Input validation errors
return StepResult.fail("Invalid input", error_category=ErrorCategory.VALIDATION)

# Network errors
return StepResult.fail("Connection failed", error_category=ErrorCategory.NETWORK)

# Service errors
return StepResult.fail("Service unavailable", error_category=ErrorCategory.SERVICE_UNAVAILABLE)

# Resource errors
return StepResult.fail("Out of memory", error_category=ErrorCategory.MEMORY_ERROR)
```

## Common Patterns

### Input Validation

```python
def run(self, input_data: str, tenant: str, workspace: str) -> StepResult:
    # Validate inputs
    if not input_data:
        return StepResult.validation_error("input_data is required")
    
    if not tenant or not workspace:
        return StepResult.validation_error("tenant and workspace are required")
    
    # Process data
    try:
        result = self._process_data(input_data, tenant, workspace)
        return StepResult.ok(data=result)
    except Exception as e:
        return StepResult.fail(f"Processing failed: {str(e)}")
```

### Tenant-Aware Operations

```python
def run(self, content: str, tenant: str, workspace: str) -> StepResult:
    try:
        # Use tenant context for isolation
        from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
        
        ctx = current_tenant()
        if not ctx:
            return StepResult.fail("Tenant context not available")
        
        # Process with tenant isolation
        result = self._process_with_tenant(content, tenant, workspace)
        return StepResult.ok(data=result)
        
    except Exception as e:
        return StepResult.fail(f"Tenant-aware processing failed: {str(e)}")
```

### Metrics Integration

```python
def run(self, data: str) -> StepResult:
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
    
    metrics = get_metrics()
    
    try:
        result = self._process_data(data)
        
        # Record success metrics
        metrics.counter(
            "tool_runs_total",
            labels={"tool": "my_tool", "outcome": "success"}
        ).inc()
        
        return StepResult.ok(data=result)
        
    except Exception as e:
        # Record error metrics
        metrics.counter(
            "tool_runs_total",
            labels={"tool": "my_tool", "outcome": "error"}
        ).inc()
        
        return StepResult.fail(str(e))
```

## Testing StepResult

### Unit Tests

```python
def test_tool_success():
    tool = MyTool()
    result = tool.run("test_input", "tenant", "workspace")
    
    assert result.success
    assert result.data["processed"] == "test_input"
    assert "status" in result.data

def test_tool_validation_error():
    tool = MyTool()
    result = tool.run("", "tenant", "workspace")
    
    assert not result.success
    assert result.error_category == ErrorCategory.VALIDATION
    assert "required" in result.error

def test_tool_network_error():
    tool = MyTool()
    with mock.patch('requests.get', side_effect=ConnectionError()):
        result = tool.run("test_input", "tenant", "workspace")
    
    assert not result.success
    assert result.error_category == ErrorCategory.NETWORK
    assert result.retryable
```

### Integration Tests

```python
def test_tool_integration():
    tool = MyTool()
    result = tool.run("test_input", "tenant", "workspace")
    
    # Check result structure
    assert isinstance(result, StepResult)
    assert hasattr(result, 'success')
    assert hasattr(result, 'data')
    
    # Check data access
    if result.success:
        assert "result" in result.data
    else:
        assert result.error is not None
```

## Troubleshooting

### Common Issues

1. **Missing StepResult import**

   ```python
   # Add this import
   from ultimate_discord_intelligence_bot.step_result import StepResult
   ```

2. **Incorrect return type annotation**

   ```python
   # Change from:
   def run(self, data: str) -> dict:
   
   # To:
   def run(self, data: str) -> StepResult:
   ```

3. **Using legacy return format**

   ```python
   # Don't do this:
   return {"status": "success", "data": result}
   
   # Do this instead:
   return StepResult.ok(data=result)
   ```

4. **Missing error handling**

   ```python
   # Always wrap in try-catch
   try:
       result = process_data()
       return StepResult.ok(data=result)
   except Exception as e:
       return StepResult.fail(str(e))
   ```

### Debugging

Use the debug information for troubleshooting:

```python
result = tool.run("input")
if not result.success:
    debug_info = result.get_debug_info()
    print(f"Error ID: {debug_info['error_id']}")
    print(f"Category: {debug_info['error_category']}")
    print(f"Severity: {debug_info['error_severity']}")
    print(f"Suggested actions: {debug_info['suggested_actions']}")
```

## Migration Examples

### Simple Tool Migration

```python
# Before
class SimpleTool:
    def run(self, text: str) -> dict:
        if not text:
            return {"status": "error", "error": "No text provided"}
        
        processed = text.upper()
        return {"status": "success", "result": processed}

# After
class SimpleTool(BaseTool):
    def run(self, text: str) -> StepResult:
        if not text:
            return StepResult.validation_error("No text provided")
        
        try:
            processed = text.upper()
            return StepResult.ok(data={"result": processed})
        except Exception as e:
            return StepResult.fail(str(e))
```

### Complex Tool Migration

```python
# Before
class ComplexTool:
    def run(self, data: dict, tenant: str) -> dict:
        try:
            # Validate inputs
            if not data.get("content"):
                return {"status": "error", "error": "Missing content"}
            
            # Process data
            result = self._process(data, tenant)
            
            # Return result
            return {
                "status": "success",
                "data": result,
                "metadata": {"processed_at": time.time()}
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

# After
class ComplexTool(BaseTool):
    def run(self, data: dict, tenant: str) -> StepResult:
        # Validate inputs
        if not data.get("content"):
            return StepResult.validation_error("Missing content")
        
        if not tenant:
            return StepResult.validation_error("Tenant is required")
        
        try:
            # Process data
            result = self._process(data, tenant)
            
            # Return success with metadata
            return StepResult.ok(
                data=result,
                metadata={"processed_at": time.time()}
            )
            
        except ValueError as e:
            return StepResult.validation_error(str(e))
        except ConnectionError as e:
            return StepResult.network_error(str(e))
        except Exception as e:
            return StepResult.fail(str(e))
```

## Best Practices

1. **Always use StepResult** - Never return raw dictionaries
2. **Use appropriate error categories** - Helps with error handling and recovery
3. **Include context in errors** - Makes debugging easier
4. **Test error paths** - Ensure all error conditions are handled
5. **Use tenant-aware design** - Pass tenant and workspace parameters
6. **Add metrics** - Track tool execution for monitoring
7. **Validate inputs** - Check inputs before processing
8. **Handle exceptions** - Wrap processing in try-catch blocks

## Conclusion

The StepResult pattern provides a robust foundation for tool development with consistent error handling, enhanced debugging capabilities, and better observability. Following this migration guide will ensure your tools integrate seamlessly with the Ultimate Discord Intelligence Bot system.
