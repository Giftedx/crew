# /autointel Command - Critical Fixes V2

**Status**: 🔴 CRITICAL - Multiple data flow and tool invocation issues
**Date**: 2025-10-02
**Affected Command**: `/autointel url:... depth:experimental`
**User Report**: Command executed: `/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:Experimental - Cutting-Edge AI`

## Executive Summary

The `/autointel` command has critical failures in tool invocation and data flow. While the `_populate_agent_tool_context()` method was implemented to fix data flow issues, the fundamental problem persists: **CrewAI's LLM cannot see the shared_context when deciding what parameters to pass to tools**.

## Root Cause Analysis

### The LLM Parameter Generation Gap

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Orchestrator populates shared_context on tool wrappers       │
│    ✅ _populate_agent_tool_context() called successfully        │
│    ✅ Context includes: transcript, media_info, metadata         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CrewAI Task created with description                         │
│    ⚠️  Description mentions transcript is in "shared context"   │
│    ⚠️  But LLM doesn't inspect wrapper instance variables       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. CrewAI LLM decides to call TextAnalysisTool                  │
│    🔍 LLM sees: args_schema with required 'text' parameter      │
│    ❌ LLM DOESN'T see: _shared_context instance variable        │
│    ❌ LLM DOESN'T see: aliasing logic in wrapper._run()         │
│    📝 LLM decision: Must provide 'text' parameter explicitly    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. LLM generates tool call                                      │
│    ❌ PROBLEM: LLM doesn't have transcript in its context       │
│    ❌ PROBLEM: LLM generates: tool.run(text="")                 │
│    ❌ PROBLEM: Or omits 'text' parameter entirely               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Wrapper._run() executes with empty/missing parameters        │
│    ✅ Aliasing logic runs (tries to fix parameters)             │
│    ⚠️  But if LLM passed text="", aliasing might not override  │
│    ❌ Tool executes with empty data → meaningless result        │
└─────────────────────────────────────────────────────────────────┘
```

### Code Evidence

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
# Line 88-148: Args schema generation
@staticmethod
def _create_args_schema(wrapped_tool: Any) -> type[BaseModel] | None:
    """Create a Pydantic schema from the wrapped tool's run() signature."""
    # ...
    if param.default != inspect.Parameter.empty:
        schema_fields[param_name] = (field_type, param.default)
    else:
        # ❌ PROBLEM: Required parameter with no indication it can come from shared_context
        schema_fields[param_name] = (field_type, Field(..., description=f"{param_name} parameter"))
```

**Current behavior**:

- `TextAnalysisTool.run(text: str)` → LLM sees `text` as REQUIRED
- LLM has no transcript in its context
- LLM calls `tool.run(text="")` (empty string to satisfy requirement)

**What LLM should see**:

- `text: str | None = Field(None, description="Text to analyze. Available from shared context if not provided.")`
- This signals the LLM it's OK to omit the parameter

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
# Lines 244-333: Aliasing logic
def _run(self, *args, **kwargs) -> Any:
    # ... complex aliasing logic ...

    # ✅ This logic is GOOD but runs TOO LATE
    if isinstance(self._shared_context, dict) and self._shared_context:
        transcript_data = (
            self._shared_context.get("transcript")
            or self._shared_context.get("enhanced_transcript")
            or self._shared_context.get("text")
            or ""
        )
        if "text" in allowed and "text" not in final_kwargs and transcript_data:
            final_kwargs["text"] = transcript_data  # ✅ Correct aliasing
```

**Problem**: This aliasing happens AFTER the LLM has already called `tool.run(text="")`. If the LLM passed `text=""`, then `"text" in final_kwargs` is True, so aliasing is skipped!

## Specific Failures

### 1. TextAnalysisTool - Empty Text Analysis

```python
# What happens:
LLM: "I need to analyze the transcript"
LLM: *sees TextAnalysisTool with required 'text' parameter*
LLM: *doesn't have transcript in context*
LLM: *calls tool.run(text="")* or *omits text parameter*
Wrapper: *checks if "text" in final_kwargs* → YES (but it's empty!)
Wrapper: *skips aliasing* → tool runs with text=""
Result: Empty or meaningless analysis
```

### 2. LogicalFallacyTool - No Content to Analyze

```python
# Same pattern:
LLM: *calls tool.run(text="")*
Tool: *analyzes empty string*
Result: No fallacies detected (because no content!)
```

### 3. FactCheckTool - Missing Claims

```python
# Variation:
LLM: *sees 'claim' parameter is required*
LLM: *doesn't have claims extracted yet*
LLM: *calls tool.run(claim="")*
Result: Fact check fails or returns "unable to verify"
```

### 4. MemoryStorageTool - Empty Content Stored

```python
# Cascading failure:
LLM: *calls tool.run(text="")*
Tool: *stores empty content in vector DB*
Result: Memory pollution, future searches return nothing
```

## Why Existing Fixes Aren't Sufficient

### Issue 1: Aliasing Priority

```python
# Current code (line 251-252):
if isinstance(self._shared_context, dict) and self._shared_context:
    merged_kwargs = {**self._shared_context, **final_kwargs}  # ❌ final_kwargs overrides!
```

This means if LLM passed `text=""`, it will OVERRIDE the transcript from shared_context!

**Fix needed**: Check if parameter is empty/falsy before allowing override:

```python
# Better approach:
merged_kwargs = {**self._shared_context}
for k, v in final_kwargs.items():
    # Only override if explicitly provided AND non-empty
    if v not in (None, "", [], {}):
        merged_kwargs[k] = v
```

### Issue 2: No Validation

```python
# Current code has NO validation that critical data is present
# Tool just executes with whatever it received
```

**Fix needed**: Add validation layer:

```python
# After aliasing, before tool execution:
if tool_cls in ("TextAnalysisTool", "LogicalFallacyTool", "PerspectiveSynthesizerTool"):
    if not final_kwargs.get("text"):
        raise ValueError(f"{tool_cls} requires non-empty 'text' parameter")
```

### Issue 3: Args Schema Misleading

```python
# Current: Field(..., description=f"{param_name} parameter")
# LLM interprets this as: "I MUST provide this parameter"

# Better: Field(None, description=f"{param_name} (available from shared context)")
# LLM interprets this as: "I can omit this, it will be provided automatically"
```

## Implementation Plan

### Phase 1: Immediate Fixes (High Impact, Low Risk)

#### Fix 1.1: Improve Args Schema Generation ✅ RECOMMENDED

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
@staticmethod
def _create_args_schema(wrapped_tool: Any) -> type[BaseModel] | None:
    """Create a Pydantic schema from the wrapped tool's run() signature."""
    # ... existing code ...

    # NEW: Identify parameters that can come from shared_context
    SHARED_CONTEXT_PARAMS = {
        "text", "transcript", "content", "claim", "claims",
        "url", "source_url", "metadata", "media_info",
        "query", "question"
    }

    for param_name, param in sig.parameters.items():
        # ... existing code ...

        # NEW: Make shared-context parameters optional with helpful description
        if param_name in SHARED_CONTEXT_PARAMS:
            field_desc = f"{param_name} (automatically provided from shared context if not specified)"
            # Make parameter optional even if signature says required
            if param.annotation != inspect.Parameter.empty:
                # Union with None to make optional
                from typing import Union
                field_type = Union[param.annotation, None]
            else:
                field_type = Any

            schema_fields[param_name] = (field_type, Field(None, description=field_desc))
        elif param.default != inspect.Parameter.empty:
            schema_fields[param_name] = (field_type, param.default)
        else:
            schema_fields[param_name] = (field_type, Field(..., description=f"{param_name} parameter"))
```

**Impact**: LLM will understand it can omit these parameters, reducing empty-string calls.

#### Fix 1.2: Fix Aliasing Priority

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
# Line ~251: REPLACE this:
if isinstance(self._shared_context, dict) and self._shared_context:
    merged_kwargs = {**self._shared_context, **final_kwargs}
    final_kwargs = merged_kwargs

# WITH this:
if isinstance(self._shared_context, dict) and self._shared_context:
    merged_kwargs = {**self._shared_context}  # Start with shared context
    for k, v in final_kwargs.items():
        # Only override if value is meaningful (not empty/None)
        if v not in (None, "", [], {}):
            merged_kwargs[k] = v
        else:
            # LLM passed empty value - keep shared_context value if available
            if k not in merged_kwargs:
                merged_kwargs[k] = v  # Keep the empty value if no shared_context alternative
    final_kwargs = merged_kwargs
```

**Impact**: Prevents empty LLM parameters from overriding good shared_context data.

#### Fix 1.3: Add Data Validation

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
# After filtering, before tool execution (~line 370):

# NEW: Validate critical parameters are non-empty for data-dependent tools
DATA_DEPENDENT_TOOLS = {
    "TextAnalysisTool": ["text"],
    "LogicalFallacyTool": ["text"],
    "PerspectiveSynthesizerTool": ["text"],
    "FactCheckTool": ["claim"],
    "ClaimExtractorTool": ["text"],
    "DeceptionScoringTool": ["text"],
    "MemoryStorageTool": ["text"],
}

if tool_cls in DATA_DEPENDENT_TOOLS:
    required_params = DATA_DEPENDENT_TOOLS[tool_cls]
    for param in required_params:
        value = filtered_kwargs.get(param)
        if not value or (isinstance(value, str) and not value.strip()):
            # Try to provide helpful diagnostic
            available_context = list(self._shared_context.keys()) if self._shared_context else []
            error_msg = (
                f"❌ {tool_cls} called with empty '{param}' parameter. "
                f"Available context keys: {available_context}. "
                f"This indicates a data flow issue - the LLM doesn't have access to the required data."
            )
            print(error_msg)
            self.logger.error(error_msg)

            # Return StepResult.fail instead of allowing tool to run with empty data
            return StepResult.fail(
                error=f"Missing required data: {param}",
                step=f"{tool_cls}_validation"
            )
```

**Impact**: Fails fast with clear diagnostics instead of running tools with empty data.

### Phase 2: Enhanced Task Descriptions

**File**: `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`

```python
# Line ~1926: UPDATE this task description:
analysis_task = Task(
    description=dedent(
        f"""
        Analyze content from {platform} video: '{title}' (URL: {source_url})

        Duration: {duration}

        IMPORTANT: The complete transcript ({len(transcript)} characters) and all media metadata
        are available in the shared tool context. DO NOT pass the transcript as a parameter -
        tools will automatically access it from shared context.

        Task: Use TextAnalysisTool to map linguistic patterns, sentiment signals, and thematic
        insights. The tool has direct access to the transcript via shared context.

        Quality Score: {transcription_data.get("quality_score", 0)}
        Timeline anchors: {len(transcription_data.get("timeline_anchors", []))} available
        """
    ).strip(),
    # ... rest of task config
)
```

**Impact**: Explicitly tells LLM not to pass data as parameters.

### Phase 3: Diagnostic Logging

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`

```python
# Line ~147 (in update_context):
def update_context(self, context: dict[str, Any]) -> None:
    """Update shared context for data flow between tools."""
    # ... existing code ...

    # NEW: Track context updates for debugging
    try:
        from obs.metrics import get_metrics
        metrics = get_metrics()
        metrics.counter(
            "crewai_shared_context_updates",
            labels={
                "tool": self.name,
                "has_transcript": "transcript" in context or "text" in context,
                "has_media_info": "media_info" in context,
                "context_keys": len(context)
            }
        ).inc()
    except Exception:
        pass

# Line ~350 (after aliasing):
# NEW: Log what parameters were actually passed vs what came from context
if self._shared_context:
    context_sourced = [k for k in final_kwargs.keys() if k in self._shared_context]
    llm_sourced = [k for k in final_kwargs.keys() if k not in self._shared_context]
    print(f"📊 Parameter sources - Context: {context_sourced}, LLM: {llm_sourced}")
```

## Testing Strategy

### Test 1: Validate Shared Context Flow

```python
def test_shared_context_prevents_empty_parameters():
    """Test that shared context prevents LLM from passing empty parameters."""
    from ultimate_discord_intelligence_bot.tools import TextAnalysisTool
    from ultimate_discord_intelligence_bot.crewai_tool_wrappers import wrap_tool_for_crewai

    tool = TextAnalysisTool()
    wrapper = wrap_tool_for_crewai(tool)

    # Populate context
    wrapper.update_context({"text": "Test transcript content"})

    # Simulate LLM calling with empty parameter
    result = wrapper._run(text="")

    # Should use shared context, not empty string
    assert result.success
    assert "Test transcript content" in str(result.data)
```

### Test 2: Validate Args Schema

```python
def test_args_schema_marks_shared_context_params_optional():
    """Test that parameters available from shared_context are marked optional."""
    from ultimate_discord_intelligence_bot.tools import TextAnalysisTool
    from ultimate_discord_intelligence_bot.crewai_tool_wrappers import CrewAIToolWrapper

    tool = TextAnalysisTool()
    wrapper = CrewAIToolWrapper(tool)

    schema = wrapper.args_schema
    if schema:
        # Check that 'text' field is optional (has default None)
        text_field = schema.__fields__.get("text")
        assert text_field is not None
        assert text_field.default is None  # Should be optional
        assert "shared context" in text_field.field_info.description.lower()
```

## Expected Outcomes

After implementing these fixes:

1. ✅ LLM will understand it can omit shared-context parameters
2. ✅ Empty LLM parameters won't override good shared_context data
3. ✅ Tools will fail fast with clear diagnostics if data is missing
4. ✅ Logs will show exact parameter sources for debugging
5. ✅ Integration tests will validate full data flow

## Rollout Plan

1. **Implement fixes in order**: Args schema → Aliasing → Validation → Logging
2. **Test each fix independently**: Unit tests for each component
3. **Run integration test**: Full /autointel workflow with real data
4. **Monitor production**: Check logs for "❌ {Tool} called with empty parameter" errors
5. **Iterate**: If issues persist, consider Phase 4 (direct tool calls) as per COPILOT_INSTRUCTIONS

## Related Files

- `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py` - Main fixes
- `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py` - Task descriptions
- `docs/AUTOINTEL_CRITICAL_ISSUES.md` - Original issue documentation
- `.github/copilot-instructions.md` - Repository guidelines

---

**Next Steps**: Implement Phase 1 fixes and run integration tests.
