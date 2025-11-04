# CRITICAL: Parameter Filtering Breaking Tool Data Flow

**Date**: 2025-10-02
**Severity**: 🔴 **CRITICAL** - Blocks all /autointel workflows
**Status**: ⚠️ **ROOT CAUSE IDENTIFIED**

## Problem Summary

The `/autointel` command fails because **CrewAI tool wrappers are filtering out shared_context data before calling tools**, causing tools to receive empty or incomplete arguments.

## Root Cause Analysis

### The Data Flow (What Should Happen)

1. ✅ Autonomous orchestrator calls `_populate_agent_tool_context(agent, {"transcript": "...", "metadata": {...}, ...})`
2. ✅ Wrapper stores in `_shared_context`: `{"transcript": "...", "metadata": {...}, ...}`
3. ❌ **CrewAI agent calls tool** with its own args (or no args): `tool.run()` or `tool.run(text="short snippet")`
4. ✅ Wrapper merges: `final_kwargs = {**_shared_context, **crewai_args}`
5. ❌ **Wrapper filters out all non-signature parameters**: Only keeps params in tool's `def _run(self, text: str)` signature
6. ❌ **Tool receives filtered_kwargs**: `{"text": "short snippet"}` instead of full context
7. ❌ **Tool fails**: Missing data like transcript, metadata, sentiment_analysis, etc.

### The Specific Code Problem

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`
**Lines**: 230-268

```python
# Merge shared context with current kwargs for better data flow
if isinstance(self._shared_context, dict) and self._shared_context:
    merged_kwargs = {**self._shared_context, **final_kwargs}
    final_kwargs = merged_kwargs

# ❌ PROBLEM: Filter arguments to tool's signature
sig = inspect.signature(target_fn)
params = list(sig.parameters.values())
allowed = {
    p.name
    for p in params
    if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
}
has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)

if not has_var_kw:
    # ❌ THIS REMOVES ALL SHARED_CONTEXT DATA!
    filtered_kwargs = {k: v for k, v in final_kwargs.items() if k in allowed}
else:
    filtered_kwargs = dict(final_kwargs)

final_kwargs = filtered_kwargs  # Now missing most context!
```

### Example Failure Scenario

**Scenario**: Analysis stage with TextAnalysisTool

```python
# Stage setup (WORKS)
_populate_agent_tool_context(analysis_agent, {
    "transcript": "Full 5000-word transcript...",
    "media_info": {"title": "...", "platform": "YouTube", ...},
    "sentiment_analysis": {"label": "positive", ...},
    "timeline_anchors": [...]
})

# CrewAI agent decides to call tool (WORKS)
# Agent task description: "Analyze content using transcript from shared context"
# CrewAI internally does: tool.run()  # No explicit args!

# Wrapper merges context (WORKS)
final_kwargs = {
    "transcript": "Full 5000-word transcript...",
    "media_info": {...},
    "sentiment_analysis": {...},
    "timeline_anchors": [...]
}

# Wrapper inspects TextAnalysisTool._run signature (PROBLEM STARTS)
# Signature: def _run(self, text: str) -> StepResult
# allowed = {"text"}  # Only "text" parameter allowed!

# Wrapper filters (BREAKS DATA FLOW)
filtered_kwargs = {}  # ALL KEYS REMOVED because none match "text"!

# Aliasing tries to fix it (PARTIAL FIX)
if "text" in allowed and "text" not in final_kwargs:
    final_kwargs["text"] = _shared_context.get("transcript")
# Now: final_kwargs = {"text": "Full transcript..."}
# But lost: media_info, sentiment_analysis, timeline_anchors!

# Tool executes (FAILS OR DEGRADED)
tool._run(text="Full transcript...")  # Missing 75% of context!
```

## Impact

### Stages Affected

**ALL stages that use CrewAI agents with tools:**

- ✅ Stage 3: Content Acquisition (PipelineTool has **kwargs, works!)
- ❌ Stage 5: Content Analysis (TextAnalysisTool loses media_info, sentiment)
- ❌ Stage 6: Information Verification (FactCheckTool loses context)
- ❌ Stage 7: Threat Analysis (DeceptionScoringTool loses verification_data)
- ❌ Stage 8: Social Intelligence (XMonitorTool loses analysis_data)
- ❌ Stage 9: Behavioral Profiling (All profiling tools lose context)
- ❌ Stage 10: Knowledge Integration (MemoryStorageTool loses embeddings context)
- ❌ Stages 11-25: All experimental stages affected

### Symptoms Observed

1. **"Tools are failing"** - Tools receive incomplete arguments, trigger validation errors
2. **"Tools are being misused"** - Filtering changes intended tool invocations
3. **"Tools not receiving correct data"** - 75%+ of shared_context data is filtered out

## Solution Options

### Option 1: Preserve Shared Context (RECOMMENDED ✅)

**Strategy**: Don't filter parameters that come from `_shared_context`, only filter CrewAI's explicit args.

**Implementation**:

```python
# Track which params came from shared_context vs CrewAI
context_keys = set(_shared_context.keys()) if _shared_context else set()
crewai_keys = set(final_kwargs.keys()) - context_keys

# Only filter CrewAI's explicit arguments, preserve all shared_context
if not has_var_kw:
    filtered_kwargs = {
        k: v for k, v in final_kwargs.items()
        if k in allowed or k in context_keys  # ✅ Preserve context!
    }
else:
    filtered_kwargs = dict(final_kwargs)
```

**Pros:**

- ✅ Minimal code change (5 lines)
- ✅ Preserves all shared_context data
- ✅ Still filters invalid CrewAI args
- ✅ No tool signature changes needed

**Cons:**

- ⚠️ Tools receive unexpected kwargs (but most tools already handle this)

### Option 2: Add Comprehensive Aliasing

**Strategy**: Map all common shared_context keys to tool parameter names.

**Implementation**:

```python
# Extensive aliasing for common patterns
alias_map = {
    "transcript": ["text", "content", "input_text"],
    "media_info": ["metadata", "content_metadata"],
    "sentiment_analysis": ["sentiment", "sentiment_data"],
    # ... 20+ more mappings
}

for src_key, target_keys in alias_map.items():
    if src_key in _shared_context:
        for target in target_keys:
            if target in allowed and target not in final_kwargs:
                final_kwargs[target] = _shared_context[src_key]
```

**Pros:**

- ✅ More explicit parameter mapping
- ✅ Tools receive only expected parameters

**Cons:**

- ❌ Requires 50+ aliasing rules
- ❌ High maintenance burden
- ❌ Still loses data that isn't aliased

### Option 3: Modify All Tool Signatures

**Strategy**: Update all 50+ tools to accept `**kwargs` or a `context` parameter.

**Implementation**:

```python
# Before: def _run(self, text: str) -> StepResult
# After:  def _run(self, text: str, **context) -> StepResult
```

**Pros:**

- ✅ Clean architecture
- ✅ Tools explicitly support context

**Cons:**

- ❌ Massive refactoring (50+ files)
- ❌ Weeks of work
- ❌ High risk of regressions

## Recommended Fix

**Use Option 1: Preserve Shared Context**

This is the pragmatic solution that:

1. Fixes the immediate data flow problem
2. Requires minimal code changes
3. Maintains backward compatibility
4. Can be implemented and tested in <1 hour

## Implementation Plan

### Step 1: Update crewai_tool_wrappers.py

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`
**Lines**: ~225-268

```python
# BEFORE MERGE (track what's in shared_context)
context_keys = set(self._shared_context.keys()) if isinstance(self._shared_context, dict) else set()

# Merge shared context with current kwargs for better data flow
if isinstance(self._shared_context, dict) and self._shared_context:
    merged_kwargs = {**self._shared_context, **final_kwargs}
    final_kwargs = merged_kwargs

# Filter arguments to the wrapped tool's signature
# BUT: preserve all shared_context parameters regardless of signature
try:
    import inspect

    target_fn = None
    if hasattr(self._wrapped_tool, "run"):
        target_fn = self._wrapped_tool.run
    elif hasattr(self._wrapped_tool, "_run"):
        target_fn = self._wrapped_tool._run
    else:
        target_fn = self._wrapped_tool

    sig = inspect.signature(target_fn)
    params = list(sig.parameters.values())
    allowed = {
        p.name
        for p in params
        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    }
    has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params)

    # Aliasing: transcript -> text
    if "text" in allowed and "text" not in final_kwargs and isinstance(self._shared_context, dict):
        tx = self._shared_context.get("transcript")
        if isinstance(tx, str) and tx:
            final_kwargs.setdefault("text", tx)

    if not has_var_kw:
        # ✅ FIX: Preserve all context keys, only filter CrewAI explicit args
        filtered_kwargs = {
            k: v for k, v in final_kwargs.items()
            if k in allowed or k in context_keys
        }
    else:
        filtered_kwargs = dict(final_kwargs)

    final_kwargs = filtered_kwargs
except Exception:
    # If introspection fails, proceed with unfiltered kwargs
    pass
```

### Step 2: Update Tool Base Class (Optional Enhancement)

**File**: `src/ultimate_discord_intelligence_bot/tools/_base.py`

Add context handling to BaseTool:

```python
class BaseTool(BaseModel, ABC, Generic[T]):
    """Base class for all tools with context support."""

    def _extract_context_param(self, param_name: str, **kwargs) -> Any:
        """Helper to extract parameter from kwargs or ignore if missing."""
        return kwargs.get(param_name)

    def _get_text_input(self, **kwargs) -> str:
        """Flexible text extraction from various parameter names."""
        for key in ["text", "transcript", "content", "input_text"]:
            val = kwargs.get(key)
            if isinstance(val, str) and val:
                return val
        return ""
```

### Step 3: Add Logging for Diagnosis

Add debug logging to wrapper to track parameter flow:

```python
print(f"🔍 Context keys: {context_keys}")
print(f"🔍 CrewAI args: {set(final_kwargs.keys()) - context_keys}")
print(f"🔍 Allowed params: {allowed}")
print(f"🔍 Filtered result: {set(filtered_kwargs.keys())}")
```

### Step 4: Testing

1. **Unit Test**: Test wrapper with various tool signatures
2. **Integration Test**: Run full /autointel workflow with logging
3. **Validation**: Check that tools receive full context in logs

## Success Criteria

- ✅ All 25 stages execute without "missing parameter" errors
- ✅ Tools receive full shared_context data (transcript + metadata + analysis data)
- ✅ CrewAI can still override context with explicit arguments
- ✅ No regressions in existing tool behavior
- ✅ Logs show "✅ Tool executed successfully" for all stages

## Testing Command

```bash
# Discord
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:experimental

# Expected: 25 stages complete with tools receiving full context
# Check logs for: "🔍 Filtered result:" showing all context keys preserved
```

## Related Files

- `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py` - Main fix location
- `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py` - Context population calls
- `src/ultimate_discord_intelligence_bot/tools/_base.py` - Tool base class
- `docs/AUTOINTEL_CRITICAL_ISSUES.md` - Original issue documentation
- `AUTOINTEL_DATA_FLOW_ANALYSIS.md` - Previous data flow analysis
- `AUTOINTEL_FIXES_APPLIED.md` - Context population fixes

## Timeline

- **Discovered**: 2025-10-02 (after implementing context population fixes)
- **Root Cause Identified**: 2025-10-02 (parameter filtering too aggressive)
- **Fix Implementation**: 🔄 **IN PROGRESS**
- **Target Completion**: 2025-10-02 (same day)
