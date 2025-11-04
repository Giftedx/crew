# Tool Export Strategy - Development Guide

## Overview

This document outlines the standardized approach for exporting and managing tools in the Ultimate Discord Intelligence Bot project. The current system uses a dynamic import pattern to avoid circular dependencies and optional dependency issues.

## Current Architecture

### Dynamic Import Pattern

The project uses a `MAPPING` dictionary in `tools/__init__.py` to dynamically import tools:

```python
MAPPING = {
    "ToolName": ".tool_module_name",
    # ...
}

def __getattr__(name: str) -> Any:
    if name in MAPPING:
        module_path = MAPPING[name]
        try:
            module = importlib.import_module(module_path, package=__name__)
            return getattr(module, name)
        except Exception as e:
            # Provide stub implementation for missing dependencies
            return _make_stub(name, e)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Benefits

1. **Lazy Loading:** Tools are only imported when actually used
2. **Optional Dependencies:** Missing dependencies don't break the entire system
3. **Graceful Degradation:** Stub implementations provide fallback behavior
4. **Circular Import Prevention:** Avoids import cycles between modules

## Tool Registration Process

### 1. Create Tool File

Create a new tool file following the naming convention:

- File: `{tool_name}_tool.py`
- Class: `{ToolName}Tool`

Example:

```python
# File: src/ultimate_discord_intelligence_bot/tools/my_analysis_tool.py
from __future__ import annotations

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.step_result import StepResult

class MyAnalysisInput(BaseModel):
    content: str = Field(..., description="Content to analyze")

class MyAnalysisTool(BaseTool):
    name: str = "my_analysis"
    description: str = "Analyzes content for specific patterns"

    def _run(self, content: str) -> StepResult:
        try:
            # Tool implementation
            result = self._analyze_content(content)
            return StepResult.ok(data=result)
        except Exception as e:
            return StepResult.fail(f"Analysis failed: {e}")
```

### 2. Register in MAPPING

Add the tool to the `MAPPING` dictionary in `tools/__init__.py`:

```python
MAPPING = {
    # ... existing tools ...
    "MyAnalysisTool": ".my_analysis_tool",
}
```

### 3. Add to **all** List

Add the tool name to the `__all__` list for explicit exports:

```python
__all__ = [
    # ... existing tools ...
    "MyAnalysisTool",
]
```

### 4. Update Agent Configuration

Register the tool with relevant agents in `crew.py`:

```python
from .tools import MyAnalysisTool

@agent
def analysis_agent(self) -> Agent:
    return Agent(
        role="Content Analyst",
        goal="Analyze content for insights",
        backstory="Expert in content analysis",
        tools=[
            wrap_tool_for_crewai(MyAnalysisTool()),
            # ... other tools ...
        ],
    )
```

## Tool Categories and Organization

### Category-Based Grouping

Tools are organized by functional category in the MAPPING:

```python
MAPPING = {
    # Core analysis/download
    "AudioTranscriptionTool": ".audio_transcription_tool",
    "CharacterProfileTool": ".character_profile_tool",

    # RAG & Retrieval
    "LCSummarizeTool": ".lc_summarize_tool",
    "OfflineRAGTool": ".offline_rag_tool",

    # MCP & Research
    "MCPCallTool": ".mcp_call_tool",
    "ResearchAndBriefTool": ".research_and_brief_tool",

    # Social media + downloaders
    "InstagramDownloadTool": ".yt_dlp_download_tool",
    "YouTubeDownloadTool": ".yt_dlp_download_tool",
}
```

### Naming Conventions

1. **File Names:** `{function}_{type}_tool.py`
   - `audio_transcription_tool.py`
   - `memory_storage_tool.py`
   - `discord_post_tool.py`

2. **Class Names:** `{Function}{Type}Tool`
   - `AudioTranscriptionTool`
   - `MemoryStorageTool`
   - `DiscordPostTool`

3. **Tool Names:** `{function}_{type}` (lowercase, snake_case)
   - `audio_transcription`
   - `memory_storage`
   - `discord_post`

## Error Handling and Stub Implementation

### Stub Pattern

When a tool cannot be imported due to missing dependencies, a stub implementation is provided:

```python
def _make_stub(_tool_name: str, _error: Exception):
    class _MissingDependencyTool:
        name = _tool_name
        description = f"{_tool_name} is unavailable due to missing dependencies"

        def _run(self, *args, **kwargs) -> StepResult:
            return StepResult.fail(
                error=f"{_tool_name} is unavailable",
                details=str(_error)
            )

    _MissingDependencyTool.__name__ = _tool_name
    return _MissingDependencyTool
```

### Benefits of Stub Pattern

1. **Graceful Degradation:** System continues to work with reduced functionality
2. **Clear Error Messages:** Users understand why a tool is unavailable
3. **No Import Failures:** Prevents cascading import errors
4. **Development Flexibility:** Allows development without all dependencies

## Tool Development Best Practices

### 1. Input Validation

Always validate inputs using Pydantic models:

```python
class MyToolInput(BaseModel):
    content: str = Field(..., description="Content to process", min_length=1)
    max_length: int = Field(default=1000, description="Maximum length", gt=0)

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v
```

### 2. Error Handling

Use StepResult for consistent error handling:

```python
def _run(self, content: str) -> StepResult:
    try:
        if not content:
            return StepResult.fail("Content is required")

        result = self._process_content(content)
        return StepResult.ok(data=result)

    except ValueError as e:
        return StepResult.fail(f"Invalid input: {e}")
    except Exception as e:
        return StepResult.fail(f"Processing failed: {e}")
```

### 3. Type Hints

Always include complete type hints:

```python
from __future__ import annotations
from typing import Any, Dict, List, Optional

def _process_content(self, content: str) -> Dict[str, Any]:
    """Process content and return structured results."""
    # Implementation
    pass
```

### 4. Documentation

Include comprehensive docstrings:

```python
class MyAnalysisTool(BaseTool):
    """Advanced content analysis tool.

    This tool provides comprehensive analysis of text content including:
    - Sentiment analysis
    - Topic extraction
    - Key phrase identification
    - Readability scoring

    Args:
        content: The text content to analyze
        options: Optional analysis configuration

    Returns:
        StepResult containing analysis results

    Example:
        >>> tool = MyAnalysisTool()
        >>> result = tool._run("Sample text content")
        >>> if result.success:
        ...     print(result.data)
    """
```

## Testing Strategy

### Unit Tests

Create unit tests for each tool:

```python
import pytest
from ultimate_discord_intelligence_bot.tools import MyAnalysisTool
from ultimate_discord_intelligence_bot.step_result import StepResult

class TestMyAnalysisTool:
    def test_successful_analysis(self):
        tool = MyAnalysisTool()
        result = tool._run("Sample content")

        assert result.success
        assert "analysis" in result.data

    def test_empty_content(self):
        tool = MyAnalysisTool()
        result = tool._run("")

        assert not result.success
        assert "required" in result.error
```

### Integration Tests

Test tool integration with agents:

```python
def test_agent_with_tool():
    from ultimate_discord_intelligence_bot.crew import UltimateDiscordIntelligenceBotCrew

    crew = UltimateDiscordIntelligenceBotCrew()
    agent = crew.analysis_agent()

    assert MyAnalysisTool in [type(tool) for tool in agent.tools]
```

## Migration and Deprecation

### Deprecation Process

1. **Add Deprecation Warning:**

   ```python
   import warnings

   class DeprecatedTool(BaseTool):
       def __init__(self):
           warnings.warn(
               "DeprecatedTool is deprecated. Use NewTool instead.",
               DeprecationWarning,
               stacklevel=2
           )
   ```

2. **Update Documentation:**
   - Mark tool as deprecated in docs
   - Provide migration guide
   - Update examples

3. **Remove from MAPPING:**
   - Remove from `tools/__init__.py`
   - Update agent configurations
   - Remove tests

### Migration Guide Template

```markdown
## Tool Migration: OldTool → NewTool

### Overview
OldTool has been deprecated in favor of NewTool which provides better performance and additional features.

### Migration Steps

1. **Update Imports:**
   ```python
   # Old
   from ultimate_discord_intelligence_bot.tools import OldTool

   # New
   from ultimate_discord_intelligence_bot.tools import NewTool
   ```

2. **Update Usage:**

   ```python
   # Old
   result = old_tool._run(input_data)

   # New
   result = new_tool._run(input_data, new_option=True)
   ```

3. **Update Agent Configuration:**

   ```python
   # Old
   tools=[wrap_tool_for_crewai(OldTool())]

   # New
   tools=[wrap_tool_for_crewai(NewTool())]
   ```

### Breaking Changes

- Parameter `old_param` renamed to `new_param`
- Return format changed from dict to StepResult
- New required parameter `new_option`

### Timeline

- Deprecated: v1.2.0
- Removed: v2.0.0

```

## Performance Considerations

### Lazy Loading Benefits

1. **Faster Startup:** Only imported tools are loaded
2. **Memory Efficiency:** Unused tools don't consume memory
3. **Dependency Isolation:** Missing dependencies don't affect other tools

### Caching Strategy

Tools can implement caching for expensive operations:

```python
from functools import lru_cache

class MyAnalysisTool(BaseTool):
    @lru_cache(maxsize=1000)
    def _expensive_analysis(self, content_hash: str) -> Dict[str, Any]:
        # Expensive analysis that can be cached
        pass
```

## Monitoring and Observability

### Metrics Integration

Tools should integrate with the observability system:

```python
from ultimate_discord_intelligence_bot.obs.metrics import get_metrics

class MyAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__()
        self._metrics = get_metrics()
        self._success_counter = self._metrics.counter("my_analysis_success_total")
        self._error_counter = self._metrics.counter("my_analysis_error_total")

    def _run(self, content: str) -> StepResult:
        try:
            result = self._process_content(content)
            self._success_counter.inc()
            return StepResult.ok(data=result)
        except Exception as e:
            self._error_counter.inc()
            return StepResult.fail(str(e))
```

## Conclusion

The dynamic import pattern provides a robust foundation for tool management while maintaining flexibility and graceful degradation. Following these guidelines ensures:

- **Consistent tool development**
- **Easy maintenance and updates**
- **Graceful handling of missing dependencies**
- **Clear deprecation and migration paths**
- **Comprehensive testing coverage**

For questions or clarifications, refer to the tool consolidation report and existing tool implementations for examples.
