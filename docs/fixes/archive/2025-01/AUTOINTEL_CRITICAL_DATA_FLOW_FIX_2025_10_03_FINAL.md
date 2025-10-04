# /autointel Critical Data Flow Fix - 2025-10-03

## Executive Summary

This document describes **critical architectural flaws** discovered in the `/autointel` command and provides a comprehensive fix. The issues prevented tools from receiving correct data, causing widespread failures across the autonomous intelligence workflow.

## Root Cause Analysis

### 🔴 CRITICAL ISSUE #1: Misunderstanding CrewAI Data Flow

**What We Thought:**

```python
# Task 1 downloads media
acquisition_task = Task(
    description="Download from {url}",
    agent=acquisition_agent
)

# Task 2 transcribes - we thought it would automatically get the file_path
transcription_task = Task(
    description="Transcribe the media",
    agent=transcription_agent,
    context=[acquisition_task]  # ← We thought this passed structured data!
)
```

**What Actually Happens:**

```
1. acquisition_task completes with: {"file_path": "/tmp/video.mp4", "title": "My Video"}
2. CrewAI converts this to TEXT: '{"file_path": "/tmp/video.mp4", "title": "My Video"}'
3. This TEXT is appended to transcription_task's LLM PROMPT
4. The LLM reads: "Transcribe the media. Previous output: {JSON text here}"
5. LLM decides to call AudioTranscriptionTool
6. LLM must EXTRACT file_path from the text and pass it as a parameter
7. If extraction fails → LLM passes placeholder like "the media file"
8. Tool receives placeholder → FAILS
```

**The Fundamental Truth:**

- `context=[previous_task]` passes **OUTPUT TEXT** to the next agent's **LLM PROMPT**
- It does **NOT** pass **STRUCTURED DATA** to tools
- Tools receive parameters from **LLM function calls**, not from task context
- The LLM must **parse previous output text** and **extract required fields**

### 🔴 CRITICAL ISSUE #2: Missing Data Propagation

**The Problem:**

```python
# PipelineTool returns StepResult with structured data
result = StepResult.ok(
    file_path="/tmp/video.mp4",
    title="My Video",
    transcript="Full transcript here..."
)

# But this data NEVER updates _GLOBAL_CREW_CONTEXT
# Next task's tools have EMPTY context!
```

**Why It Matters:**

- Tool wrappers have extensive aliasing logic to map `_shared_context` → tool parameters
- Example: `_shared_context["transcript"]` → `tool.run(text=transcript)`
- But if context is never updated, aliasing fails
- Tools receive `None` or placeholder values

### 🔴 CRITICAL ISSUE #3: Vague Task Descriptions

**Bad (Current):**

```python
transcription_task = Task(
    description="Extract audio from the downloaded media file and transcribe it to text.",
    agent=transcription_agent,
    context=[acquisition_task]
)
```

**Why It Fails:**

- LLM sees: "Extract audio from the downloaded media file"
- LLM thinks: "What file? Where is it?"
- LLM generates: `AudioTranscriptionTool(file_path="the downloaded media file")`
- Tool receives placeholder → FAILS

**Good (Fixed):**

```python
transcription_task = Task(
    description=(
        "STEP 1: Extract the 'file_path' field from the previous task's JSON output. "
        "STEP 2: Use AudioTranscriptionTool with the file_path parameter. "
        "CRITICAL: Pass the exact file_path value, not a placeholder."
    ),
    agent=transcription_agent,
    context=[acquisition_task]
)
```

**Why It Works:**

- Explicitly tells LLM to look for `file_path` in previous output
- Provides step-by-step instructions
- Warns against using placeholders

## The Fix

### 1. Task Completion Callbacks

Added `_task_completion_callback()` method that:

- Extracts JSON from task output text (looks for ```json``` blocks or JSON patterns)
- Updates `_GLOBAL_CREW_CONTEXT` with extracted structured data
- Propagates data to all cached agent tools

**Code:**

```python
def _task_completion_callback(self, task_output: Any) -> None:
    """Extract structured data from task output and update global context."""
    try:
        # Extract JSON from output text
        import json, re
        raw = str(task_output.raw) if hasattr(task_output, 'raw') else str(task_output)
        
        # Look for JSON blocks
        json_match = re.search(r'```json\s*({.*?})\s*```', raw, re.DOTALL)
        if not json_match:
            json_match = re.search(r'({\s*"[^"]+"\s*:.*?})', raw, re.DOTALL)
        
        if json_match:
            output_data = json.loads(json_match.group(1))
            
            # Update global context
            from .crewai_tool_wrappers import _GLOBAL_CREW_CONTEXT
            _GLOBAL_CREW_CONTEXT.update(output_data)
            
            # Update all cached agent tools
            for agent in self.agent_coordinators.values():
                self._populate_agent_tool_context(agent, output_data)
    except Exception as e:
        self.logger.error(f"Callback failed: {e}")
```

### 2. Explicit Task Descriptions

Changed from vague to explicit, step-by-step instructions:

**Before:**

```python
Task(description="Download from {url}")
```

**After:**

```python
Task(
    description=(
        "Download and acquire media content from {url}. "
        "Use the appropriate download tool for the platform. "
        "CRITICAL: Return your results as JSON with these exact keys: "
        "file_path, title, description, author, duration, platform. "
        "Wrap the JSON in ```json``` code blocks for easy parsing."
    ),
    callback=self._task_completion_callback  # ← Extracts and propagates data
)
```

**Key Changes:**

- ✅ Tells LLM to return JSON with specific keys
- ✅ Requests ```json``` code blocks for easy extraction
- ✅ Adds callback to extract and propagate the data

### 3. Data Extraction Instructions

For dependent tasks, explicitly instruct the LLM to extract from previous output:

```python
Task(
    description=(
        "STEP 1: Extract the 'file_path' field from the previous task's JSON output. "
        "STEP 2: Use AudioTranscriptionTool with the file_path parameter to transcribe. "
        "STEP 3: Return results as JSON with keys: transcript, timeline_anchors. "
        "CRITICAL: Pass the exact file_path value, not 'the file path' placeholder."
    ),
    context=[acquisition_task],
    callback=self._task_completion_callback
)
```

## Data Flow After Fix

```
┌─────────────────────────────────────────────────────────────────┐
│ Task 1: Acquisition                                             │
│ - LLM calls MultiPlatformDownloadTool(url="https://...")       │
│ - Tool returns: {"file_path": "/tmp/vid.mp4", "title": "..."}  │
│ - LLM formats as: ```json\n{"file_path": "...", ...}\n```      │
│ - Callback extracts JSON → updates _GLOBAL_CREW_CONTEXT        │
│ - Callback updates all agent tools with new context            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Task 2: Transcription (context=[Task1])                        │
│ - LLM receives: "Previous: ```json\n{file_path: /tmp/vid.mp4}" │
│ - LLM reads instruction: "Extract 'file_path' from JSON"       │
│ - LLM calls: AudioTranscriptionTool(file_path="/tmp/vid.mp4")  │
│ - If LLM fails, wrapper checks _GLOBAL_CREW_CONTEXT            │
│ - Wrapper aliases: context["file_path"] → tool parameter       │
│ - Tool executes successfully with correct file path            │
│ - Returns: {"transcript": "...", "timeline_anchors": [...]}    │
│ - Callback extracts → updates context for Task 3               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Task 3: Analysis (context=[Task2])                             │
│ - LLM receives: "Previous: ```json\n{transcript: ...}"         │
│ - LLM reads: "Extract 'transcript' field from JSON"            │
│ - LLM calls: TextAnalysisTool(text="Full transcript...")       │
│ - Wrapper aliasing: context["transcript"] → text parameter     │
│ - All analysis tools receive correct transcript data           │
│ - Returns insights, themes, fallacies, perspectives            │
│ - Callback propagates for Task 4                               │
└─────────────────────────────────────────────────────────────────┘
```

## Files Modified

1. **`src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`**:
   - Added `_task_completion_callback()` method
   - Updated all task descriptions in `_build_intelligence_crew()`
   - Added explicit data extraction instructions
   - Added callbacks to all tasks

## Testing the Fix

### Before Fix (Expected Failures)

```bash
/autointel url:https://www.youtube.com/watch?v=... depth:experimental

# Errors you would see:
# - "AudioTranscriptionTool requires file_path but got 'the media file'"
# - "TextAnalysisTool requires text but got 'the transcript'"
# - "FactCheckTool requires claim but got 'the content'"
```

### After Fix (Expected Success)

```bash
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:experimental

# Should see:
# ✅ Task 1 complete: Extracted file_path, title, metadata
# 📦 Updated global context with 6 keys
# ✅ Task 2 complete: Transcribed /tmp/video_abc123.mp4
# 📦 Updated global context with transcript (15000 chars)
# ✅ Task 3 complete: Analysis with 12 insights, 3 fallacies
# 📦 Updated global context with analysis results
# ✅ Task 4 complete: Verified 8 claims, assessed trustworthiness
# ✅ Task 5 complete: Integrated knowledge, generated briefing
```

## Key Learnings

1. **CrewAI task context ≠ tool parameters**
   - Context passes text to LLM prompts
   - Tools get parameters from LLM function calls
   - LLM must extract structured data from text

2. **Be explicit with LLMs**
   - "Transcribe the media" → fails
   - "Extract file_path from JSON and pass to AudioTranscriptionTool" → works

3. **Propagate data between tasks**
   - Task outputs must update global context
   - Use callbacks to extract and propagate
   - Update all agent tools with new data

4. **Return structured outputs**
   - Request JSON with specific keys
   - Use ```json``` code blocks for easy parsing
   - Extract and store for next tasks

## Related Documentation

- CrewAI Tasks: <https://docs.crewai.com/concepts/tasks>
- CrewAI Collaboration: <https://docs.crewai.com/concepts/collaboration>
- Tool Wrappers: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`
- Copilot Instructions: `.github/copilot-instructions.md`

## Author

**Fix Date:** 2025-10-03  
**Analysis by:** AI Agent (Claude/Copilot)  
**Validated:** Ready for testing
