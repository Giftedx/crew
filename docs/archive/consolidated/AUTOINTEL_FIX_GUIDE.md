# /autointel Command - Immediate Fix Guide

## Quick Diagnosis

Run this to see the data flow issue:

```bash
# Enable debug logging
export ENABLE_CREW_STEP_VERBOSE=1

# Run your command
# You'll see tools being called with empty/wrong parameters
```

## Immediate Workaround

### Option 1: Use ContentPipeline Directly (Bypasses /autointel)

The ContentPipeline works correctly because it calls tools directly:

```python
# In Python REPL or script:
from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline
import asyncio

pipeline = ContentPipeline()
result = asyncio.run(pipeline.process_video(
    url="https://www.youtube.com/watch?v=xtFiJ8AVdW0",
    quality="1080p"
))

print(result)  # Full results with transcript, analysis, etc.
```

### Option 2: Disable Experimental Depth

The experimental depth (25 stages) has the most CrewAI agent usage. Use a simpler depth:

```
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:standard
```

Standard depth (10 stages) uses more direct tool calls and fewer CrewAI agents.

## Permanent Fix (For Developers)

### Step 1: Add Shared Context Population

Edit `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`:

```python
def _populate_agent_tool_context(self, agent: Any, context_data: dict[str, Any]) -> None:
    """Populate shared context on all tool wrappers for an agent."""
    if not hasattr(agent, 'tools'):
        return

    for tool in agent.tools:
        if hasattr(tool, 'update_context'):
            tool.update_context(context_data)
            self.logger.debug(f"Populated context for {tool.name}: {list(context_data.keys())}")
```

### Step 2: Use Before Each crew.kickoff()

In `_execute_specialized_content_analysis`:

```python
# BEFORE creating the crew, populate context
analysis_agent = self.agent_coordinators["analysis_cartographer"]

# Populate shared context with full data
self._populate_agent_tool_context(analysis_agent, {
    "text": transcript,  # Full transcript, not preview
    "transcript": transcript,
    "metadata": {
        "title": title,
        "platform": platform,
        "url": source_url,
        "duration": duration
    },
    "transcription_data": transcription_data,
    "media_info": media_info
})

# NOW create and execute crew
analysis_crew = Crew(agents=[analysis_agent], tasks=[analysis_task], ...)
crew_result = await asyncio.to_thread(analysis_crew.kickoff)
```

### Step 3: Repeat for All Stages

Apply the same pattern to:

- `_execute_specialized_information_verification` (populate with analysis_data, claims)
- `_execute_specialized_deception_analysis` (populate with verification_data)
- `_execute_specialized_social_intelligence` (populate with intelligence_data)
- `_execute_specialized_behavioral_analysis` (populate with all prior data)
- `_execute_specialized_knowledge_integration` (populate with all accumulated data)
- All other stages that use CrewAI agents

### Step 4: Add Validation

Before crew.kickoff(), validate required data is present:

```python
def _validate_stage_data(self, stage_name: str, required_keys: list[str], data: dict) -> None:
    """Validate that required data keys are present before stage execution."""
    missing = [k for k in required_keys if k not in data or not data[k]]
    if missing:
        raise ValueError(
            f"Stage {stage_name} missing required data: {missing}. "
            f"Available keys: {list(data.keys())}"
        )

# Use before each stage:
self._validate_stage_data("content_analysis", ["transcript", "metadata"], {
    "transcript": transcript,
    "metadata": metadata
})
```

## Testing the Fix

### Create Integration Test

```python
# tests/test_autointel_data_flow.py
import pytest
from unittest.mock import Mock, AsyncMock
from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator

@pytest.mark.asyncio
async def test_autointel_data_flow_to_tools():
    """Verify data flows correctly from orchestrator to tools."""
    orchestrator = AutonomousIntelligenceOrchestrator()

    # Mock interaction
    interaction = Mock()
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    interaction.guild_id = "123"
    interaction.channel = Mock(name="test-channel")

    # Track tool calls
    tool_calls = []

    def track_tool_call(tool_name, **kwargs):
        tool_calls.append({"tool": tool_name, "kwargs": kwargs})
        return StepResult.ok()

    # Patch tools to track calls
    # ... (patch TextAnalysisTool, FactCheckTool, etc.)

    # Execute workflow
    await orchestrator.execute_autonomous_intelligence_workflow(
        interaction,
        url="https://www.youtube.com/watch?v=test",
        depth="standard"
    )

    # Validate tools received correct data
    text_analysis_call = next(c for c in tool_calls if c["tool"] == "TextAnalysisTool")
    assert "text" in text_analysis_call["kwargs"]
    assert len(text_analysis_call["kwargs"]["text"]) > 100  # Not empty!

    # Validate data propagation
    fact_check_call = next(c for c in tool_calls if c["tool"] == "FactCheckTool")
    assert "claims" in fact_check_call["kwargs"]  # Has claims from analysis
```

### Run Test

```bash
pytest tests/test_autointel_data_flow.py -v
```

## Verification Checklist

After implementing fixes:

- [ ] Tools receive non-empty data (check logs for "text: ''" vs "text: 'actual content'")
- [ ] Shared context is populated (check logs for "Populated context for...")
- [ ] Analysis results contain actual insights (not empty/default values)
- [ ] Memory tools store actual content (check Qdrant collections)
- [ ] Final Discord message contains real analysis (not "fallback" or "unavailable")
- [ ] Integration test passes with real YouTube URL
- [ ] All 4 depth levels work (standard, deep, comprehensive, experimental)

## Monitoring

Add metrics to track data flow health:

```python
# In orchestrator, after populating context:
self.metrics.counter(
    "autointel_context_populated",
    labels={
        "stage": stage_name,
        "keys_count": len(context_data),
        "has_transcript": "transcript" in context_data
    }
).inc()

# In tool wrappers, track context usage:
self.metrics.counter(
    "tool_context_usage",
    labels={
        "tool": self.name,
        "context_available": bool(self._shared_context),
        "context_keys": len(self._shared_context)
    }
).inc()
```

## Related Files

- **Root cause analysis**: `docs/AUTOINTEL_CRITICAL_ISSUES.md`
- **Orchestrator**: `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`
- **Tool wrappers**: `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py`
- **Crew definitions**: `src/ultimate_discord_intelligence_bot/crew.py`
- **Pipeline (working reference)**: `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py`

## Questions?

If you need help implementing these fixes, check:

1. How ContentPipeline calls tools directly (it works correctly)
2. How tool wrappers merge shared_context with kwargs
3. The update_context() method signature and usage
