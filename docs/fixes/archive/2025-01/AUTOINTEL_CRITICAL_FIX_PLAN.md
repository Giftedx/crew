# /autointel Critical Fix Implementation Plan

**Status**: 🔴 CRITICAL - Immediate fix required  
**Date**: 2025-10-02  
**Issue**: CrewAI tools receive empty data because orchestrator never populates shared context

## Problem Summary

The `/autointel` command fails because `autonomous_orchestrator.py` creates CrewAI tasks with truncated descriptions but NEVER calls `update_context()` on tool wrappers before `crew.kickoff()`. This means all tools receive empty `_shared_context` and fail to process the actual content.

## Fix Strategy

### 1. Add Context Population Helper Method

Add a reusable method to populate context on all agent tools:

```python
def _populate_tool_context(self, agents: list[Any], context_data: dict[str, Any]) -> None:
    """Populate shared context on all tools for all agents before crew execution.
    
    This ensures tools receive actual data instead of empty context.
    Critical for: TextAnalysisTool, FactCheckTool, MemoryStorageTool, etc.
    """
    for agent in agents:
        if hasattr(agent, 'tools'):
            for tool in agent.tools:
                if hasattr(tool, 'update_context'):
                    tool.update_context(context_data)
                    print(f"✅ Populated context for {tool.name} with keys: {list(context_data.keys())}")
```

### 2. Update All crew.kickoff() Call Sites

For each crew execution, add context population IMMEDIATELY before kickoff:

#### Mission Planning (Line ~1499)

```python
# Before:
crew_result = await asyncio.to_thread(planning_crew.kickoff)

# After:
self._populate_tool_context([planning_agent], {
    "url": url,
    "depth": depth,
    "mission_objectives": mission_objectives,
})
crew_result = await asyncio.to_thread(planning_crew.kickoff)
```

#### Content Analysis (Line ~1931)

```python
# Before:
crew_result = await asyncio.to_thread(analysis_crew.kickoff)

# After:
self._populate_tool_context([analysis_agent], {
    "transcript": transcript,
    "text": transcript,  # alias for TextAnalysisTool
    "enhanced_transcript": transcription_data.get("enhanced_transcript"),
    "media_info": media_info,
    "timeline_anchors": transcription_data.get("timeline_anchors", []),
    "source_url": source_url,
})
crew_result = await asyncio.to_thread(analysis_crew.kickoff)
```

#### Information Verification (Line ~2197)

```python
# Before:
crew_result = await asyncio.to_thread(verification_crew.kickoff)

# After:
self._populate_tool_context([verification_agent], {
    "transcript": analysis_data.get("transcript"),
    "text": analysis_data.get("transcript"),
    "analysis_data": analysis_data,
    "fact_data": fact_data,
    "content_metadata": analysis_data.get("content_metadata", {}),
})
crew_result = await asyncio.to_thread(verification_crew.kickoff)
```

#### Threat Analysis (Line ~2292)

```python
self._populate_tool_context([threat_agent], {
    "transcript": analysis_data.get("transcript"),
    "text": analysis_data.get("transcript"),
    "analysis_data": analysis_data,
    "verification_data": verification_data,
    "deception_indicators": analysis_data.get("deception_indicators", []),
})
crew_result = await asyncio.to_thread(threat_crew.kickoff)
```

### 3. Apply to ALL Crew Executions

Total crew.kickoff() locations to fix: **20+**

```bash
# All locations found:
Line 1499:  planning_crew.kickoff         # Mission Planning
Line 1707:  transcription_crew.kickoff    # Transcription Analysis
Line 1931:  analysis_crew.kickoff         # Content Analysis
Line 2197:  verification_crew.kickoff     # Information Verification
Line 2292:  threat_crew.kickoff           # Threat Analysis
Line 2407:  social_crew.kickoff           # Social Intelligence
Line 2583:  knowledge_crew.kickoff        # Knowledge Integration
Line 2688:  threat_crew.kickoff           # Advanced Threat (duplicate agent)
Line 2757:  profiling_crew.kickoff        # Behavioral Profiling
Line 2830:  research_crew.kickoff         # Research Synthesis
Line 5565:  pattern_crew.kickoff          # Pattern Recognition
Line 5626:  network_crew.kickoff          # Cross-Reference Intelligence
Line 5689:  prediction_crew.kickoff       # Predictive Threat Assessment
Line 5737:  multimodal_crew.kickoff       # Multi-Modal Synthesis
Line 5773:  graph_crew.kickoff            # Knowledge Graph Construction
Line 5811:  learning_crew.kickoff         # Autonomous Learning
Line 5849:  bandits_crew.kickoff          # Contextual Bandits
Line 5884:  community_crew.kickoff        # Community Intelligence
Line 5919:  adaptive_crew.kickoff         # Adaptive Workflow
Line 5952:  memory_crew.kickoff           # Memory Consolidation
```

### 4. Context Data Structure per Stage

#### Universal Context (all stages)

```python
{
    "url": source_url,
    "depth": depth,
    "workflow_id": workflow_id,
}
```

#### Acquisition Stage (lines 1531-1610)

```python
{
    "url": url,
    "download_info": download_info,
    "media_info": media_info,
}
```

#### Transcription Stage (lines 1640-1750)

```python
{
    "transcript": transcript,
    "text": transcript,
    "enhanced_transcript": enhanced_transcript,
    "media_info": media_info,
    "timeline_anchors": timeline_anchors,
    "quality_score": quality_score,
}
```

#### Analysis Stage (lines 1870-2000)

```python
{
    "transcript": transcript,
    "text": transcript,
    "enhanced_transcript": enhanced_transcript,
    "media_info": media_info,
    "transcription_data": transcription_data,
    "pipeline_analysis": pipeline_analysis_block,
}
```

#### Verification Stage (lines 2140-2230)

```python
{
    "transcript": analysis_data.get("transcript"),
    "text": analysis_data.get("transcript"),
    "analysis_data": analysis_data,
    "fact_data": fact_data,
    "claims": extracted_claims,
    "content_metadata": metadata,
}
```

### 5. Testing Strategy

After implementing the fix:

1. **Unit Test**: Verify context population

```python
def test_tool_context_population():
    orchestrator = AutonomousIntelligenceOrchestrator()
    mock_agent = MagicMock()
    mock_tool = MagicMock()
    mock_tool.update_context = MagicMock()
    mock_agent.tools = [mock_tool]
    
    orchestrator._populate_tool_context([mock_agent], {"test": "data"})
    
    mock_tool.update_context.assert_called_once_with({"test": "data"})
```

2. **Integration Test**: Verify tools receive data

```python
async def test_autointel_tools_receive_data():
    orchestrator = AutonomousIntelligenceOrchestrator()
    result = await orchestrator.execute_autonomous_intelligence_workflow(
        mock_interaction, 
        "https://www.youtube.com/watch?v=test",
        "standard"
    )
    
    # Verify TextAnalysisTool was called with actual transcript
    assert "transcript" in tool_calls
    assert len(tool_calls["transcript"]) > 500  # More than preview
```

3. **E2E Test**: Run actual /autointel command

```bash
# Test with real YouTube video
python -m scripts.run_autointel_local \
    --url "https://www.youtube.com/watch?v=xtFiJ8AVdW0" \
    --depth experimental
```

### 6. Rollout Plan

1. **Phase 1**: Add `_populate_tool_context()` helper method
2. **Phase 2**: Fix critical stages (acquisition, transcription, analysis, verification)
3. **Phase 3**: Fix remaining stages (threat, social, profiling, research)
4. **Phase 4**: Fix experimental stages (pattern, network, prediction, etc.)
5. **Phase 5**: Add comprehensive logging for context population
6. **Phase 6**: Run full test suite

### 7. Validation Checklist

- [ ] Helper method `_populate_tool_context()` added
- [ ] All 20+ crew.kickoff() calls have context population
- [ ] Tools receive correct data structures (not just descriptions)
- [ ] TextAnalysisTool gets full transcript (not 500 char preview)
- [ ] FactCheckTool gets extracted claims + context
- [ ] MemoryStorageTool gets complete analysis data
- [ ] No tools report "empty text" or "no data" errors
- [ ] E2E test passes with experimental depth
- [ ] Logging confirms context keys populated before each crew

### 8. Success Criteria

**Before Fix** (current state):

```
❌ Tools receive empty _shared_context
❌ TextAnalysisTool fails: "text parameter is empty"
❌ FactCheckTool fails: "no claims to verify"
❌ Memory tools fail: "no data to store"
```

**After Fix** (expected state):

```
✅ Tools receive populated _shared_context with full data
✅ TextAnalysisTool processes complete transcript
✅ FactCheckTool verifies extracted claims
✅ Memory tools store comprehensive analysis
✅ /autointel completes successfully with experimental depth
```

## Related Files

- `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py` - Main fix location
- `src/ultimate_discord_intelligence_bot/crewai_tool_wrappers.py` - Context mechanism
- `docs/AUTOINTEL_CRITICAL_ISSUES.md` - Original issue documentation
- `.github/copilot-instructions.md` - Pattern warnings

## References

- Issue documented in: `AUTOINTEL_CRITICAL_ISSUES.md`
- Broken pattern warned in: `.github/copilot-instructions.md` lines 68-82
- Tool wrapper context: `crewai_tool_wrappers.py` lines 156-184
- Aliasing logic: `crewai_tool_wrappers.py` lines 270-310
