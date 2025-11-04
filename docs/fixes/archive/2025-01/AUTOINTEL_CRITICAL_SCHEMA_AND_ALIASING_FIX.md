# CRITICAL FIX: Pydantic Schema Generation + Parameter Aliasing Issues

## Executive Summary

The `/autointel` command fails in an infinite loop due to **TWO CRITICAL BUGS**:

### Bug #1: `**kwargs` Creates Required Parameter in Pydantic Schema

**Impact**: Multi-Platform Download Tool unusable - agents get Pydantic validation errors no matter what
 they try.

**Root Cause**: `_create_args_schema()` in `crewai_tool_wrappers.py` introspects `MultiPlatformDownloadTool.run(url, quality, **kwargs)` and creates:

```python
class MultiPlatformDownloadToolArgs(BaseModel):
    url: str = Field(..., description="url parameter")
    quality: str = Field(default="1080p", description="quality parameter")
    kwargs: Any = Field(..., description="kwargs parameter")  # ❌ WRONG! This should be **kwargs, not a named param
```

**What Happens**:

- Agent provides `{"url": "...", "quality": "best", "kwargs": {}}` → Tool rejects with `"YtDlpDownloadTool.run() got an unexpected keyword argument 'kwargs'"`
- Agent provides `{"url": "...", "quality": "best"}` → Pydantic rejects with `"Field required [type=missing, ...]: kwargs"`

**Catch-22**: Schema says `kwargs` required, but tool rejects it when provided!

### Bug #2: YouTube Download Tool Receives `None` for `video_url`

**Impact**: All YouTube downloads fail with `"expected string or bytes-like object, got 'NoneType'"`

**Root Cause**: Parameter aliasing logic not working - `video_url` parameter never gets populated from agent's input or shared context.

**Error Location**: `yt_dlp_download_tool.py:188`

```python
path_match = re.search(r"\[download\]\s+(.+?)\s+has already been downloaded", download_line)
# ❌ Fails when download_line is None because video_url was None
```

## The Fix

### Fix #1: Skip `**kwargs` in Pydantic Schema Generation

**File**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`
**Method**: `_create_args_schema()`

**Change**: Skip parameters with `kind == inspect.Parameter.VAR_KEYWORD` (i.e., `**kwargs`)

```python
# Extract parameters (skip 'self')
schema_fields = {}
for param_name, param in sig.parameters.items():
    if param_name == "self":
        continue

    # ✅ NEW: Skip **kwargs variadic keyword arguments
    if param.kind == inspect.Parameter.VAR_KEYWORD:
        continue

    # Skip keyword-only tenant/workspace params
    if param_name in ("tenant_id", "workspace_id") and param.kind == inspect.Parameter.KEYWORD_ONLY:
        continue
    # ... rest of schema generation
```

### Fix #2: Enhanced Parameter Aliasing for Download Tools

**Problem**: `video_url` not being aliased to `url` from agent input

**Solution**: Add comprehensive parameter aliasing in `_run()` method:

```python
# Alias common download tool parameters
if tool_cls.endswith("DownloadTool"):
    # video_url ← url (or source_url)
    if "video_url" not in final_kwargs and ("url" in final_kwargs or "source_url" in final_kwargs):
        final_kwargs["video_url"] = final_kwargs.get("url") or final_kwargs.get("source_url")

    # url ← video_url (or source_url)
    if "url" not in final_kwargs and ("video_url" in final_kwargs or "source_url" in final_kwargs):
        final_kwargs["url"] = final_kwargs.get("video_url") or final_kwargs.get("source_url")
```

### Fix #3: Validate Required Parameters Before Execution

**Add safety check** to fail fast with helpful error when required params are None:

```python
# Validate required download parameters
if tool_cls.endswith("DownloadTool"):
    url_param = final_kwargs.get("url") or final_kwargs.get("video_url")
    if not url_param:
        return StepResult.fail(
            error=f"{tool_cls} requires url/video_url parameter but received None. "
                  f"Provided kwargs: {list(final_kwargs.keys())}",
            tool=tool_cls
        )
```

## Testing Strategy

1. **Unit Test for Schema Generation**:

   ```python
   def test_kwargs_not_in_schema():
       tool = MultiPlatformDownloadTool()
       wrapper = CrewAIToolWrapper(tool)
       schema = wrapper.args_schema
       assert "kwargs" not in schema.model_fields
       assert "url" in schema.model_fields
       assert "quality" in schema.model_fields
   ```

2. **Integration Test for Parameter Aliasing**:

   ```python
   def test_video_url_aliasing():
       tool = YouTubeDownloadTool()
       wrapper = CrewAIToolWrapper(tool)
       # Provide 'url', expect 'video_url' aliased
       result = wrapper._run(url="https://youtube.com/watch?v=test")
       assert result.success or "video_url" in str(result.error)
   ```

3. **End-to-End Test**:

   ```bash
   python scripts/diagnose_autointel.py
   # Should complete acquisition task without infinite loop
   ```

## Implementation Checklist

- [ ] Add VAR_KEYWORD check to `_create_args_schema()`
- [ ] Add comprehensive parameter aliasing for download tools
- [ ] Add required parameter validation
- [ ] Add unit tests for schema generation
- [ ] Add integration tests for parameter aliasing
- [ ] Run diagnostic script to verify fix
- [ ] Update COPILOT_INSTRUCTIONS.md with new patterns

## Root Cause Analysis

**Why wasn't this caught earlier?**

1. **Unit tests mock tool execution** - they don't exercise Pydantic schema generation
2. **Integration tests use direct tool calls** - they bypass CrewAI wrappers
3. **No end-to-end tests with actual LLM agents** - first time seeing real CrewAI behavior

**Prevention Strategy**:

- Add E2E tests that exercise CrewAI agent→wrapper→tool flow
- Add schema validation tests for all wrapped tools
- Add parameter aliasing verification to test suite
