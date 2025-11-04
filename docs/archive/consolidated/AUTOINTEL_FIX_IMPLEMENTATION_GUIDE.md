# /autointel Fix Implementation Guide

## Quick Summary

**Problem**: 10 out of 20 CrewAI stages don't call `_populate_agent_tool_context` before `crew.kickoff()`, causing tools to receive empty data.

**Solution**: Add the missing context population calls before each affected crew execution.

## Critical Fixes (Do These First)

### Fix 1: Analysis Stage (Line ~1926)

The analysis stage HAS context population code but it silently fails in try/except!

**Current Code** (lines 1878-1926):

```python
try:
    self._populate_agent_tool_context(
        analysis_agent,
        {
            "transcript": transcript,
            "media_info": media_info,
            # ... context data
        },
    )
except Exception as _ctx_err:
    self.logger.warning(f"⚠️ Analysis agent context population FAILED: {_ctx_err}", exc_info=True)
    # PROBLEM: Continues execution anyway!

# Creates crew without verifying context was populated
analysis_crew = Crew(agents=[analysis_agent], tasks=[analysis_task], ...)
crew_result = await asyncio.to_thread(analysis_crew.kickoff)
```

**Fix**:

```python
try:
    self._populate_agent_tool_context(
        analysis_agent,
        {
            "transcript": transcript,
            "media_info": media_info,
            "timeline_anchors": transcription_data.get("timeline_anchors", []),
            "transcript_index": transcription_data.get("transcript_index", {}),
            "pipeline_analysis": pipeline_analysis_block,
            "pipeline_fallacy": pipeline_fallacy_block,
            "pipeline_perspective": pipeline_perspective_block,
            "pipeline_metadata": pipeline_metadata,
            "source_url": source_url or media_info.get("source_url"),
        },
    )
    self.logger.info(f"✅ Analysis context populated successfully")
except Exception as _ctx_err:
    self.logger.error(f"❌ Analysis context population FAILED: {_ctx_err}", exc_info=True)
    # Return early instead of continuing with empty data
    return StepResult.fail(
        error=f"Analysis context preparation failed: {_ctx_err}",
        step="analysis_context_population"
    )

# Now safe to execute crew
analysis_crew = Crew(agents=[analysis_agent], tasks=[analysis_task], ...)
crew_result = await asyncio.to_thread(analysis_crew.kickoff)
```

### Fix 2: Threat Analysis (Line ~2273)

**Current Code** (lines 2240-2273):

```python
# Data is extracted but never passed to tools
transcript = intelligence_data.get("transcript", "")
content_metadata = intelligence_data.get("content_metadata", {})
fact_checks = verification_data.get("fact_checks", {})
logical_analysis = verification_data.get("logical_analysis", {})
# ... more data

# Task description mentions "from shared context" but context is never populated!
threat_task = Task(
    description="Conduct comprehensive threat analysis using data from shared context",
    agent=threat_agent,
)
threat_crew = Crew(agents=[threat_agent], tasks=[threat_task], ...)
crew_result = await asyncio.to_thread(threat_crew.kickoff)  # BROKEN: empty context
```

**Fix - Insert BEFORE task creation**:

```python
# Extract data
transcript = intelligence_data.get("transcript", "")
content_metadata = intelligence_data.get("content_metadata", {})
sentiment_analysis = intelligence_data.get("sentiment_analysis", {})
fact_checks = verification_data.get("fact_checks", {})
logical_analysis = verification_data.get("logical_analysis", {})
credibility_assessment = verification_data.get("credibility_assessment", {})

if not transcript and not content_metadata:
    return StepResult.skip(reason="No content available for threat analysis")

# Populate context BEFORE creating crew
self._populate_agent_tool_context(
    threat_agent,
    {
        "transcript": transcript,
        "content_metadata": content_metadata,
        "sentiment_analysis": sentiment_analysis,
        "fact_checks": fact_checks,
        "logical_analysis": logical_analysis,
        "credibility_assessment": credibility_assessment,
        "verification_data": verification_data,
    }
)

# Now task description can be concise
threat_task = Task(
    description="Conduct comprehensive threat analysis using transcript and verification data from shared context",
    expected_output="Threat assessment with deception scores and manipulation indicators",
    agent=threat_agent,
)
threat_crew = Crew(agents=[threat_agent], tasks=[threat_task], ...)
crew_result = await asyncio.to_thread(threat_crew.kickoff)
```

### Fix 3: Behavioral Profiling (Line ~2727)

**Current Code** (lines 2704-2727):

```python
transcript = analysis_data.get("transcript", "")
if not transcript:
    return StepResult.skip(reason="No transcript for profiling")

behavioral_task = Task(
    description=f"Perform behavioral analysis using transcript and threat_data from shared context",
    agent=analysis_agent,
)
persona_task = Task(
    description="Create persona profile using threat_data from shared context",
    agent=persona_agent,
)
profiling_crew = Crew(agents=[analysis_agent, persona_agent], tasks=[...], ...)
crew_result = await asyncio.to_thread(profiling_crew.kickoff)  # BROKEN
```

**Fix - Insert BEFORE task creation**:

```python
transcript = analysis_data.get("transcript", "")
if not transcript:
    return StepResult.skip(reason="No transcript for profiling")

# Populate context for BOTH agents
shared_context = {
    "transcript": transcript,
    "analysis_data": analysis_data,
    "threat_data": threat_data,
    "threat_level": threat_data.get("threat_level", "unknown"),
    "content_metadata": analysis_data.get("content_metadata", {}),
}

self._populate_agent_tool_context(analysis_agent, shared_context)
self._populate_agent_tool_context(persona_agent, shared_context)

# Create tasks (descriptions can be concise now)
behavioral_task = Task(
    description="Perform comprehensive behavioral analysis using data from shared context",
    expected_output="Behavioral profile with personality traits and communication patterns",
    agent=analysis_agent,
)
persona_task = Task(
    description="Create detailed persona profile from behavioral patterns and threat indicators",
    expected_output="Persona dossier with trust metrics",
    agent=persona_agent,
)
profiling_crew = Crew(agents=[analysis_agent, persona_agent], tasks=[...], ...)
crew_result = await asyncio.to_thread(profiling_crew.kickoff)
```

## Medium Priority Fixes

### Fix 4: Research Synthesis (Line ~2790)

**Insert before line 2768**:

```python
transcript = analysis_data.get("transcript", "")
claims = verification_data.get("fact_checks", {})

if not transcript:
    return StepResult.skip(reason="No content for research")

# Populate context
self._populate_agent_tool_context(
    trend_agent,
    {
        "transcript": transcript,
        "claims": claims,
        "analysis_data": analysis_data,
        "verification_data": verification_data,
    }
)
self._populate_agent_tool_context(
    knowledge_agent,
    {
        "transcript": transcript,
        "verification_data": verification_data,
        "analysis_data": analysis_data,
    }
)

# Then create tasks and crew
research_task = Task(...)
integration_task = Task(...)
```

### Fix 5: Pattern Recognition (Line ~5524)

**Insert before line 5501**:

```python
# Prepare analysis data
pattern_context = {
    "analysis_results": analysis_data,
    "verification_results": verification_data,
    "threat_assessment": threat_data,
    "behavioral_profile": behavioral_data,
}

self._populate_agent_tool_context(analysis_agent, pattern_context)

pattern_task = Task(...)
pattern_crew = Crew(...)
crew_result = await asyncio.to_thread(pattern_crew.kickoff)
```

### Fix 6: Cross-Reference Network (Line ~5584)

**Insert before line 5560**:

```python
network_context = {
    "analysis_data": analysis_data,
    "verification_data": verification_data,
    "knowledge_graph_data": knowledge_data,
}

self._populate_agent_tool_context(recon_agent, network_context)
self._populate_agent_tool_context(knowledge_agent, network_context)

network_task = Task(...)
```

### Fix 7: Predictive Threat (Line ~5646)

**Insert before line 5622**:

```python
prediction_context = {
    "threat_data": threat_data,
    "behavioral_data": behavioral_data,
    "historical_patterns": analysis_data,
}

self._populate_agent_tool_context(threat_agent, prediction_context)

prediction_task = Task(...)
```

## Lower Priority Fixes (Experimental Stages)

### Fix 8: Community Intelligence (Line ~5832)

```python
community_context = {
    "social_intelligence": social_data,
    "community_data": community_data,
}
self._populate_agent_tool_context(community_agent, community_context)
```

### Fix 9: Real-Time Adaptive (Line ~5858)

```python
adaptive_context = {
    "current_state": current_state,
    "performance_data": performance_data,
}
self._populate_agent_tool_context(orchestrator_agent, adaptive_context)
```

### Fix 10: Memory Consolidation (Line ~5882)

```python
memory_context = {
    "all_results": aggregated_results,
    "knowledge_data": knowledge_data,
}
self._populate_agent_tool_context(knowledge_agent, memory_context)
```

## Testing After Fixes

### Quick Validation

Run this command to verify all crew.kickoff() calls have context population:

```bash
cd /home/crew

# Should return 20 (one for each crew.kickoff)
grep -B 30 "crew\.kickoff" src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py | \
  grep "_populate_agent_tool_context" | wc -l
```

### Integration Test

Create `tests/test_autointel_data_flow.py`:

```python
import pytest
from unittest.mock import Mock, patch
from ultimate_discord_intelligence_bot.autonomous_orchestrator import AutonomousIntelligenceOrchestrator

@pytest.mark.asyncio
async def test_all_stages_receive_context():
    """Validate that all crew stages receive proper context."""
    orchestrator = AutonomousIntelligenceOrchestrator()

    # Track context population calls
    context_calls = []
    original_populate = orchestrator._populate_agent_tool_context

    def track_populate(agent, context):
        context_calls.append({
            "agent": getattr(agent, "role", "unknown"),
            "has_data": bool(context and len(context) > 0),
        })
        return original_populate(agent, context)

    orchestrator._populate_agent_tool_context = track_populate

    # Mock interaction
    interaction = Mock()
    interaction.guild_id = "test_guild"
    interaction.channel.name = "test_channel"

    # Execute with real URL (will use mocked pipeline internally)
    await orchestrator.execute_autonomous_intelligence_workflow(
        interaction,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        depth="standard"
    )

    # Should have context population for all crew stages
    assert len(context_calls) >= 10, f"Only {len(context_calls)} context calls (expected 10+)"

    # All calls should have data
    for call in context_calls:
        assert call["has_data"], f"Agent {call['agent']} received empty context!"

    print(f"✅ All {len(context_calls)} stages received context data")
```

Run the test:

```bash
pytest tests/test_autointel_data_flow.py -v -s
```

### Manual Test

```bash
# Run the Discord bot
python -m ultimate_discord_intelligence_bot.setup_cli run discord

# In Discord, test the command
/autointel url:https://www.youtube.com/watch?v=xtFiJ8AVdW0 depth:standard

# Check logs for these messages:
# ✅ "Populated shared context on X tools for agent Y"
# ✅ "Analysis context populated successfully"
# ❌ Should NOT see "Context population FAILED"
```

## Success Checklist

After implementing all fixes:

- [ ] All 10 missing `_populate_agent_tool_context` calls added
- [ ] Analysis stage exception handling fixed (returns early on failure)
- [ ] Integration test passes
- [ ] Manual `/autointel` test completes successfully
- [ ] Logs show context population for all stages
- [ ] No "Context population FAILED" errors in logs
- [ ] Tools receive full transcript and metadata in all stages

## Rollback Plan

If fixes cause issues:

1. Git revert the changes to `autonomous_orchestrator.py`
2. Re-enable the old behavior where task descriptions contain full data
3. File detailed bug report with specific stage failures

## Next Steps After Fix

1. Add metrics for context population success rate
2. Add validation helper to check required context keys
3. Document the pattern in COPILOT_INSTRUCTIONS.md
4. Add pre-commit hook to validate new crew.kickoff() calls have context population

## Estimated Time

- Critical fixes (1-3): 2 hours
- Medium priority (4-7): 2 hours
- Low priority (8-10): 1 hour
- Testing: 1 hour
- **Total: ~6 hours**

## Need Help?

If you encounter issues:

1. Check that agent has `tools` attribute: `hasattr(agent, "tools")`
2. Verify tools have `update_context` method: `hasattr(tool, "update_context")`
3. Add debug logging: `self.logger.debug(f"Context keys: {list(context.keys())}")`
4. Test single stage in isolation before running full workflow
