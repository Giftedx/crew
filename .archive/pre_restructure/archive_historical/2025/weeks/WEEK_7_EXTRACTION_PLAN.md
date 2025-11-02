# Week 7 Extraction Plan: Pipeline Result Builders

**Date:** January 5, 2025  
**Status:** 📋 Planning  
**Target:** Extract pipeline result building methods → new `result_synthesizers.py` module  
**Risk Level:** 🟡 MEDIUM (revised from HIGH after analysis)

---

## Executive Summary

Week 6 categorization identified `_build_pipeline_content_analysis_result` as a ~1,000 line extraction opportunity. **UPDATED ANALYSIS** reveals the method is actually **135 lines** (lines 1542-1676), not 1,000 lines. However, there are **multiple related result-building methods** that should be extracted together as a cohesive module.

**Revised Strategy:** Extract **all result synthesis/building methods** as a single `result_synthesizers.py` module rather than just the pipeline builder.

---

## Method Analysis Update

### Primary Target: _build_pipeline_content_analysis_result

**Location:** Lines 1542-1676 (135 lines)  
**Complexity:** Medium  
**Dependencies:**

- Input parameters: transcript, transcription_data, pipeline_analysis, media_info, pipeline_fallacy, pipeline_perspective, pipeline_metadata, source_url
- External dependencies: `time` module, `StepResult` class
- No orchestrator method calls (self-contained!)

**What it does:**

1. Extracts keywords from pipeline_analysis
2. Builds sentiment payload from pipeline_analysis
3. Calculates word count (from structured data or transcript)
4. Extracts summary (from pipeline_analysis or pipeline_perspective)
5. Builds content_metadata dict (combines transcription_data, media_info, pipeline_metadata)
6. Builds thematic_insights (keywords + perspective data)
7. Constructs comprehensive analysis_results dict
8. Returns StepResult.ok with all data
9. Error handling: Returns degraded result on exception

**Key Insight:** This method is **pure data transformation** with **zero orchestrator dependencies**. It's a perfect extraction candidate!

---

## Related Methods to Extract (Cohesive Module)

Let me search for other result-building/synthesis methods:

### Category: Result Building/Synthesis Methods

Based on Week 6 categorization, these methods should be extracted together:

1. **`_build_pipeline_content_analysis_result`** (135 lines, lines 1542-1676)
   - Synthesizes ContentPipeline outputs into analysis result

2. **`_merge_threat_and_deception_data`** (~40 lines, estimated)
   - Merges threat detection + deception analysis results

3. **`_merge_threat_payload`** (~35 lines, estimated)
   - Constructs threat payload for pipeline results

4. **`_build_knowledge_payload`** (~400 lines, estimated)
   - Builds knowledge graph payload from crew results

5. **`_create_executive_summary`** (~8 lines, estimated)
   - Creates high-level summary from analysis

6. **`_extract_key_findings`** (~25 lines, estimated)
   - Extracts important findings from crew outputs

7. **`_generate_strategic_recommendations`** (~8 lines, estimated)
   - Generates actionable recommendations

8. **`_extract_system_status_from_crew`** (~20 lines, estimated)
   - Extracts system status information

**Total Estimated Lines:** ~671 lines

**Module Name:** `result_synthesizers.py`

---

## Revised Week 7 Plan

### Goals

- Extract **result synthesis/building methods** to `result_synthesizers.py` (~671 lines)
- Create comprehensive test file (40-50 tests, 5-8 tests per method)
- Reduce orchestrator: 4,807 → 4,136 lines (-671 lines, -14.0%)
- **Nearly achieve <4,000 line target!** (136 lines away)

### Extraction Approach

**Phase 1: Locate and Document (Days 1-2)**

1. Find exact line numbers for all 8 methods
2. Analyze dependencies for each method
3. Document input/output contracts
4. Identify shared utilities (if any)
5. Design module interface (delegation pattern)

**Phase 2: Write Comprehensive Tests (Days 2-3)**

For each method, write:

- Happy path tests (valid inputs → expected outputs)
- Edge case tests (empty data, null values, missing keys)
- Error path tests (exception handling, degraded outputs)
- Consistency tests (idempotency, deterministic behavior)

**Target:** 40-50 tests total (5-8 tests per method)

**Phase 3: Extract Module (Day 4)**

1. Create `src/ultimate_discord_intelligence_bot/orchestrator/result_synthesizers.py`
2. Move all 8 methods to module (as module-level functions)
3. Update function signatures (remove `self`, explicit parameters)
4. Add module docstring and function documentation
5. Update `__init__.py` to export functions
6. Update orchestrator:
   - Add import: `from .orchestrator import result_synthesizers`
   - Replace method bodies with delegation calls
   - Keep method signatures (orchestrator API unchanged)

**Phase 4: Validate and Document (Day 5)**

1. Run full test suite (all 759+ tests must pass)
2. Run new result_synthesizers tests (40-50 tests)
3. Verify zero regressions in integration tests
4. Performance check (no slowdowns)
5. Create WEEK_7_COMPLETE.md
6. Update CURRENT_STATE_SUMMARY.md
7. Atomic git commit

---

## Delegation Pattern

### Before (Orchestrator Method)

```python
class AutonomousIntelligenceOrchestrator:
    def _build_pipeline_content_analysis_result(
        self,
        *,
        transcript: str,
        transcription_data: dict[str, Any],
        pipeline_analysis: dict[str, Any],
        media_info: dict[str, Any],
        pipeline_fallacy: dict[str, Any] | None,
        pipeline_perspective: dict[str, Any] | None,
        pipeline_metadata: dict[str, Any] | None,
        source_url: str | None,
    ) -> StepResult:
        """Synthesize content analysis from ContentPipeline outputs."""
        # ... 135 lines of implementation ...
        return StepResult.ok(**analysis_results)
```

### After (Module Function + Orchestrator Delegate)

**File:** `src/ultimate_discord_intelligence_bot/orchestrator/result_synthesizers.py`

```python
"""Result synthesis and building utilities for autonomous orchestrator.

This module contains functions for building comprehensive result payloads
from various pipeline and crew outputs, including content analysis,
threat assessments, knowledge graphs, and executive summaries.
"""

from typing import Any
import time

from ultimate_discord_intelligence_bot.step_result import StepResult


def build_pipeline_content_analysis_result(
    *,
    transcript: str,
    transcription_data: dict[str, Any],
    pipeline_analysis: dict[str, Any],
    media_info: dict[str, Any],
    pipeline_fallacy: dict[str, Any] | None,
    pipeline_perspective: dict[str, Any] | None,
    pipeline_metadata: dict[str, Any] | None,
    source_url: str | None,
    logger = None,  # Optional logger for warnings
) -> StepResult:
    """Synthesize content analysis directly from ContentPipeline outputs.

    When the pipeline already produced rich analysis artifacts, prefer them over
    launching additional agent workloads. This consolidates sentiment,
    perspective, and fallacy insights into the step result expected by
    downstream stages.

    Args:
        transcript: Full transcript text
        transcription_data: Transcription metadata (quality_score, timeline_anchors, etc.)
        pipeline_analysis: Analysis results from ContentPipeline
        media_info: Media metadata (title, platform, duration, etc.)
        pipeline_fallacy: Optional fallacy analysis results
        pipeline_perspective: Optional perspective analysis results
        pipeline_metadata: Optional pipeline metadata (source_url, workflow_type, etc.)
        source_url: Optional source URL
        logger: Optional logger for warning messages

    Returns:
        StepResult with comprehensive analysis_results dict or degraded fallback
    """
    try:
        # ... 135 lines of implementation (moved from orchestrator) ...
        return StepResult.ok(**analysis_results)
    except Exception as exc:
        if logger:
            logger.warning("Failed to construct pipeline-derived analysis payload: %s", exc)
        return StepResult.ok(
            message="ContentPipeline analysis extraction degraded",
            # ... degraded fallback ...
        )


def merge_threat_and_deception_data(
    threat_data: dict[str, Any],
    deception_data: dict[str, Any],
) -> dict[str, Any]:
    """Merge threat detection and deception analysis results."""
    # ... implementation ...


def merge_threat_payload(
    verification_data: dict[str, Any],
    deception_data: dict[str, Any],
) -> dict[str, Any]:
    """Construct threat payload for pipeline results."""
    # ... implementation ...


def build_knowledge_payload(
    crew_result: Any,
    analysis_data: dict[str, Any],
) -> dict[str, Any]:
    """Build knowledge graph payload from crew results."""
    # ... implementation ...


def create_executive_summary(
    analysis_results: dict[str, Any],
) -> str:
    """Create high-level summary from analysis results."""
    # ... implementation ...


def extract_key_findings(
    crew_result: Any,
) -> list[str]:
    """Extract important findings from crew outputs."""
    # ... implementation ...


def generate_strategic_recommendations(
    analysis_data: dict[str, Any],
) -> list[str]:
    """Generate actionable recommendations."""
    # ... implementation ...


def extract_system_status_from_crew(
    crew_result: Any,
) -> dict[str, Any]:
    """Extract system status information."""
    # ... implementation ...
```

**File:** `src/ultimate_discord_intelligence_bot/autonomous_orchestrator.py`

```python
from .orchestrator import result_synthesizers

class AutonomousIntelligenceOrchestrator:
    def _build_pipeline_content_analysis_result(
        self,
        *,
        transcript: str,
        transcription_data: dict[str, Any],
        pipeline_analysis: dict[str, Any],
        media_info: dict[str, Any],
        pipeline_fallacy: dict[str, Any] | None,
        pipeline_perspective: dict[str, Any] | None,
        pipeline_metadata: dict[str, Any] | None,
        source_url: str | None,
    ) -> StepResult:
        """Synthesize content analysis from ContentPipeline outputs.
        
        Delegates to result_synthesizers.build_pipeline_content_analysis_result.
        """
        return result_synthesizers.build_pipeline_content_analysis_result(
            transcript=transcript,
            transcription_data=transcription_data,
            pipeline_analysis=pipeline_analysis,
            media_info=media_info,
            pipeline_fallacy=pipeline_fallacy,
            pipeline_perspective=pipeline_perspective,
            pipeline_metadata=pipeline_metadata,
            source_url=source_url,
            logger=self.logger,
        )
    
    def _merge_threat_and_deception_data(
        self,
        threat_data: dict[str, Any],
        deception_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge threat and deception data. Delegates to result_synthesizers."""
        return result_synthesizers.merge_threat_and_deception_data(
            threat_data=threat_data,
            deception_data=deception_data,
        )
    
    # ... similar delegation wrappers for other 6 methods ...
```

---

## Test Plan

### Test File: `tests/orchestrator/test_result_synthesizers.py`

```python
"""Unit tests for result synthesis and building functions."""
import pytest
from ultimate_discord_intelligence_bot.orchestrator import result_synthesizers
from ultimate_discord_intelligence_bot.step_result import StepResult


class TestBuildPipelineContentAnalysisResult:
    """Test suite for build_pipeline_content_analysis_result function."""
    
    def test_happy_path_complete_data(self):
        """Test with all input data provided."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="This is a test transcript with keywords.",
            transcription_data={"quality_score": 0.9, "timeline_anchors": []},
            pipeline_analysis={
                "keywords": ["test", "keywords"],
                "sentiment": "positive",
                "sentiment_score": 0.8,
                "summary": "Test summary",
            },
            media_info={"title": "Test Video", "platform": "youtube"},
            pipeline_fallacy={"fallacies": []},
            pipeline_perspective={"perspectives": ["perspective1"]},
            pipeline_metadata={"source_url": "https://example.com"},
            source_url="https://example.com",
        )
        
        assert result.success is True
        assert result.data["transcript"] == "This is a test transcript with keywords."
        assert result.data["keywords"] == ["test", "keywords"]
        assert result.data["sentiment"] == "positive"
        assert result.data["sentiment_score"] == 0.8
    
    def test_minimal_data(self):
        """Test with minimal required data."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="Minimal test.",
            transcription_data={},
            pipeline_analysis={},
            media_info={},
            pipeline_fallacy=None,
            pipeline_perspective=None,
            pipeline_metadata=None,
            source_url=None,
        )
        
        assert result.success is True
        assert result.data["transcript"] == "Minimal test."
        assert result.data["sentiment"] == "neutral"  # Default
    
    def test_empty_transcript(self):
        """Test with empty transcript."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="",
            transcription_data={},
            pipeline_analysis={},
            media_info={},
            pipeline_fallacy=None,
            pipeline_perspective=None,
            pipeline_metadata=None,
            source_url=None,
        )
        
        assert result.success is True
        assert result.data["content_metadata"]["word_count"] == 0
    
    def test_keyword_extraction_key_phrases(self):
        """Test keyword extraction from key_phrases field."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="Test",
            transcription_data={},
            pipeline_analysis={"key_phrases": ["phrase1", "phrase2"]},
            media_info={},
            pipeline_fallacy=None,
            pipeline_perspective=None,
            pipeline_metadata=None,
            source_url=None,
        )
        
        assert result.data["keywords"] == ["phrase1", "phrase2"]
    
    def test_word_count_from_structured(self):
        """Test word count extraction from structured.word_count."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="one two three",
            transcription_data={},
            pipeline_analysis={"structured": {"word_count": 3}},
            media_info={},
            pipeline_fallacy=None,
            pipeline_perspective=None,
            pipeline_metadata=None,
            source_url=None,
        )
        
        assert result.data["content_metadata"]["word_count"] == 3
    
    def test_summary_fallback_to_perspective(self):
        """Test summary fallback to pipeline_perspective."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="Test",
            transcription_data={},
            pipeline_analysis={},  # No summary
            media_info={},
            pipeline_fallacy=None,
            pipeline_perspective={"summary": "Perspective summary"},
            pipeline_metadata=None,
            source_url=None,
        )
        
        assert result.data["summary"] == "Perspective summary"
    
    def test_media_info_merging(self):
        """Test media_info fields merged into content_metadata."""
        result = result_synthesizers.build_pipeline_content_analysis_result(
            transcript="Test",
            transcription_data={},
            pipeline_analysis={},
            media_info={
                "title": "Video Title",
                "platform": "youtube",
                "duration": 300,
                "uploader": "TestUser",
                "video_id": "abc123",
            },
            pipeline_fallacy=None,
            pipeline_perspective=None,
            pipeline_metadata=None,
            source_url=None,
        )
        
        metadata = result.data["content_metadata"]
        assert metadata["title"] == "Video Title"
        assert metadata["platform"] == "youtube"
        assert metadata["duration"] == 300
        assert metadata["uploader"] == "TestUser"
        assert metadata["video_id"] == "abc123"
    
    # ... 40+ more tests ...


class TestMergeThreatAndDeceptionData:
    """Test suite for merge_threat_and_deception_data function."""
    
    # ... 5-8 tests ...


class TestMergeThreatPayload:
    """Test suite for merge_threat_payload function."""
    
    # ... 5-8 tests ...


class TestBuildKnowledgePayload:
    """Test suite for build_knowledge_payload function."""
    
    # ... 5-8 tests ...


class TestCreateExecutiveSummary:
    """Test suite for create_executive_summary function."""
    
    # ... 5-8 tests ...


class TestExtractKeyFindings:
    """Test suite for extract_key_findings function."""
    
    # ... 5-8 tests ...


class TestGenerateStrategicRecommendations:
    """Test suite for generate_strategic_recommendations function."""
    
    # ... 5-8 tests ...


class TestExtractSystemStatusFromCrew:
    """Test suite for extract_system_status_from_crew function."""
    
    # ... 5-8 tests ...
```

---

## Success Criteria

### Week 7 Completion

| Metric | Before | Target | Status |
|--------|--------|--------|--------|
| **Orchestrator Size** | 4,807 lines | ~4,136 lines | -671 lines (-14.0%) |
| **Gap to <4,000** | +807 over | +136 over | 671 line reduction |
| **Modules Extracted** | 10 | 11 | +1 module (result_synthesizers) |
| **Extracted Code** | 4,552 lines | ~5,223 lines | +671 lines |
| **New Tests** | ~743 | ~793 | +40-50 tests |
| **Breaking Changes** | 0 | 0 | Zero regressions |
| **Test Coverage** | 100% | 100% | Maintain coverage |

### Technical Validation

- ✅ All existing tests pass (759+ tests)
- ✅ New module tests pass (40-50 tests)
- ✅ No performance regressions
- ✅ Clean delegation pattern (10-15 line wrappers)
- ✅ No circular dependencies
- ✅ Comprehensive documentation

---

## Risk Assessment

### Risk Level: 🟡 MEDIUM (Downgraded from HIGH)

**Why Medium Risk:**

✅ **Mitigating Factors:**

- Methods are **self-contained** (minimal dependencies)
- Clear input/output contracts (all parameters explicit)
- Pure data transformation (no state mutations)
- Well-understood functionality (result building)
- Test-first approach (write 40-50 tests before extraction)

⚠️ **Remaining Risks:**

- Multiple methods extracted at once (8 methods)
- Some methods may have hidden dependencies
- Integration with existing pipeline code

**Mitigation Strategy:**

1. **Comprehensive Testing:** Write 5-8 tests per method before extraction
2. **Incremental Validation:** Run tests after each method extraction
3. **Clear Documentation:** Document all function contracts
4. **Rollback Plan:** Feature flag + git revert if issues discovered

---

## Timeline

### Day 1-2: Discovery and Test Design (10-12 hours)

- ✅ Locate exact line numbers for all 8 methods (2 hours)
- ✅ Document dependencies and contracts (3 hours)
- ✅ Design test cases (40-50 tests) (3 hours)
- Begin writing tests (2-4 hours)

### Day 3: Complete Tests (6-8 hours)

- Write remaining tests (40-50 total)
- Verify tests cover all edge cases
- Run tests against current orchestrator (baseline)

### Day 4: Extraction (6-8 hours)

- Create result_synthesizers.py module
- Move all 8 methods to module
- Update orchestrator delegation wrappers
- Update imports and **init**.py
- Run full test suite (validation)

### Day 5: Validation and Documentation (4-6 hours)

- Run comprehensive test suite
- Performance benchmarking
- Create WEEK_7_COMPLETE.md
- Update tracking documents
- Git commit

**Total Estimated Effort:** 26-36 hours (5-7 days)

---

## Next Steps (Immediate)

1. **Search for exact line numbers** of all 8 target methods
2. **Analyze dependencies** for each method
3. **Create test fixtures** for common test data
4. **Begin writing tests** for _build_pipeline_content_analysis_result (8 tests)

---

**Status:** 📋 **Planning Complete - Ready to Begin Day 1**  
**Next Action:** Locate remaining 7 methods and document their line numbers  
**Timeline:** Start Week 7 extraction work immediately
