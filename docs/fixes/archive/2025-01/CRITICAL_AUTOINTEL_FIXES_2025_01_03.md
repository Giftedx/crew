# Critical /autointel Fixes - January 3, 2025

## Problem Summary

The `/autointel` command is fundamentally broken with multiple cascading failures:

1. **Parameter Filtering Catastrophe**: Tools receive ZERO context data - everything filtered out
2. **Content Analysis Failure**: Final report analyzes error messages instead of video content
3. **Tool Misuse**: Verification Director calls Claim Extractor 22 times with same input
4. **Missing Tool Usage**: MemoryStorageTool and GraphMemoryTool never called
5. **Context Propagation Failure**: 30+ redundant context updates, data not flowing to tools
6. **JSON Extraction Issues**: Task outputs can't be parsed for downstream use

## Root Cause Analysis

### Issue #1: Parameter Filtering strips ALL context

**Location**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py` lines 630-650

**Problem**:

```python
# Only keeps parameters in tool signature
filtered_kwargs = {k: v for k, v in final_kwargs.items() if k in allowed}
```

This filters out `transcript`, `insights`, `themes`, `perspectives` - ALL the data tools need!

**Fix**: Merge context as `_context` parameter for context-aware tools:

```python
# Keep signature params PLUS add full context as _context
filtered_kwargs = {k: v for k, v in final_kwargs.items() if k in allowed}
# Add full context for tools that can use it
if context_keys:
    filtered_kwargs["_context"] = {k: v for k, v in final_kwargs.items() if k in context_keys}
```

### Issue #2: Claim Extraction Loop

**Location**: Verification task calls ClaimExtractorTool 22 times

**Problem**:

- Task expects 3-5 claims
- Tool returns 1 claim per call
- Agent repeats same input hoping for different output
- Hits max iterations and gives up

**Fix**: Make tool extract MULTIPLE claims per call OR change task to accept partial results

### Issue #3: Missing Tool Enforcement

**Location**: Knowledge Integration task description

**Problem**: Says "Use MemoryStorageTool" but doesn't enforce it

**Fix**: Add output validation that requires tool_results to include specific tool names

### Issue #4: Content Not Reaching Analysis

**Problem**: Despite successful download/transcription, analysis sees errors not content

**Fix**: Ensure global crew context actually populated in tool `_shared_context`

## Implementation Plan

1. Fix parameter filtering to preserve context
2. Improve claim extraction to return multiple claims
3. Add tool usage validation
4. Fix JSON extraction from task outputs
5. Add max tool call limits per task
6. Improve verification task instructions

## Testing Checklist

- [ ] Verify transcript flows to Analysis Cartographer
- [ ] Confirm tools receive `_context` parameter with full data
- [ ] Check final report mentions actual video content (not errors)
- [ ] Validate MemoryStorageTool and GraphMemoryTool execute
- [ ] Ensure no tool called >10 times per task
- [ ] Verify JSON extraction succeeds for all tasks
