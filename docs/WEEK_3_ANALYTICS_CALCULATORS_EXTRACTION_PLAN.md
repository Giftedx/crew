# Week 3: Analytics Calculators Extraction Plan

**Date:** January 4, 2025  
**Target Module:** `analytics_calculators.py`  
**Estimated Scope:** 28 calculation + 6 generation methods (~800-1000 lines)  
**Expected Orchestrator Reduction:** 15-18% (5,655 → ~4,800 lines)  
**Timeline:** 6-8 hours implementation + 2 hours validation/documentation

---

## Executive Summary

Week 3 focuses on extracting **analytics and calculation logic** from the orchestrator into a dedicated `analytics_calculators.py` module. This includes 28 `_calculate_*` methods and 6 `_generate_*` methods that perform statistical computations, score calculations, confidence metrics, and insight generation.

**Key Insight:** These methods are **already highly stateless** - most are pure functions that take data inputs and return computed values without side effects. This makes them ideal candidates for extraction with minimal refactoring.

---

## Target Methods (34 total)

### Category 1: Threat & Risk Calculations (12 methods)

| Method | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `_calculate_threat_level()` | ~30 | Low | None (pure) |
| `_calculate_threat_level_from_crew()` | ~25 | Low | extractors |
| `_calculate_comprehensive_threat_score()` | ~130 | High | Multiple threat sources |
| `_calculate_comprehensive_threat_score_from_crew()` | ~110 | High | extractors |
| `_calculate_basic_threat_from_data()` | ~45 | Medium | None (pure) |
| `_calculate_behavioral_risk()` | ~20 | Low | None (pure) |
| `_calculate_behavioral_risk_from_crew()` | ~25 | Low | extractors |
| `_calculate_composite_deception_score()` | ~35 | Medium | StepResult |
| `_calculate_persona_confidence()` | ~10 | Low | None (pure) |
| `_calculate_persona_confidence_from_crew()` | ~25 | Low | extractors |
| `_calculate_agent_confidence_from_crew()` | ~25 | Low | extractors |
| `_calculate_contextual_relevance()` | ~10 | Low | None (pure) |

**Total Lines:** ~490 lines

### Category 2: Quality & Confidence Metrics (8 methods)

| Method | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `_calculate_ai_quality_score()` | ~8 | Low | None (pure) |
| `_calculate_ai_enhancement_level()` | ~30 | Low | None (pure) |
| `_calculate_confidence_interval()` | ~35 | Medium | Statistics |
| `_calculate_synthesis_confidence()` | ~10 | Low | None (pure) |
| `_calculate_synthesis_confidence_from_crew()` | ~20 | Low | extractors |
| `_calculate_verification_confidence_from_crew()` | ~5 | Low | extractors |
| `_calculate_overall_confidence()` | ~15 | Low | None (pure) |
| `_calculate_transcript_quality()` | ~30 | Medium | extractors |

**Total Lines:** ~153 lines

### Category 3: Summary & Statistics (4 methods)

| Method | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `_calculate_summary_statistics()` | ~75 | High | Multiple sources |
| `_calculate_enhanced_summary_statistics()` | ~30 | Medium | None (pure) |
| `_calculate_data_completeness()` | ~15 | Low | None (pure) |
| `_calculate_consolidation_metrics_from_crew()` | ~75 | Medium | extractors |

**Total Lines:** ~195 lines

### Category 4: Resource Planning (4 methods)

| Method | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `_calculate_resource_requirements()` (line 985) | ~80 | High | Depth config |
| `_calculate_resource_requirements()` (line 4514) | ~80 | High | Depth config |
| `_calculate_contextual_relevance_from_crew()` | ~20 | Low | extractors |
| `_calculate_analysis_confidence_from_crew()` | ~35 | Medium | extractors |

**Total Lines:** ~215 lines

**Note:** Lines 985 and 4514 appear to be duplicate methods - will consolidate during extraction.

### Category 5: Insight Generation (6 methods)

| Method | Lines | Complexity | Dependencies |
|--------|-------|------------|--------------|
| `_generate_specialized_insights()` | ~50 | Medium | None (pure) |
| `_generate_autonomous_insights()` | ~105 | High | Complex logic |
| `_generate_ai_recommendations()` | ~80 | High | Quality dimensions |
| `_generate_enhancement_suggestions()` | ~35 | Medium | Quality data |
| `_generate_strategic_recommendations()` | ~40 | Medium | Multiple sources |
| `_generate_comprehensive_intelligence_insights()` | ~60 | High | All results |

**Total Lines:** ~370 lines

---

## Total Extraction Impact

| Metric | Value |
|--------|-------|
| **Methods to Extract** | 34 methods |
| **Estimated Lines** | ~1,423 lines (raw) |
| **With Docstrings/Imports** | ~1,000 lines (net reduction) |
| **Orchestrator Before** | 5,655 lines |
| **Orchestrator After** | ~4,655 lines |
| **Reduction** | -1,000 lines (-17.7%) |
| **Progress to <5,000 Target** | Will **EXCEED TARGET** 🎯 |

**Major Milestone:** This extraction will **achieve our <5,000 line goal** in Week 3 (2 weeks ahead of original Week 5 target)!

---

## Design Approach

### Module Structure

```python
# src/ultimate_discord_intelligence_bot/orchestrator/analytics_calculators.py

"""Analytics and statistical calculation functions for intelligence workflows.

This module provides pure computational functions for:
- Threat and risk scoring
- Confidence and quality metrics
- Summary statistics
- Resource planning
- Insight generation

All functions are stateless and can be used standalone or integrated
into the orchestrator workflow.
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
def _get_extractors():
    from . import extractors
    return extractors

# ============================================================================
# Category 1: Threat & Risk Calculations
# ============================================================================

def calculate_threat_level(deception_result: Any, fallacy_result: Any) -> str:
    """Calculate threat level from deception and fallacy analysis."""
    # Implementation...

def calculate_threat_level_from_crew(crew_result: Any) -> str:
    """Extract and calculate threat level from crew result."""
    # Implementation...

# ... (30+ more functions)

# ============================================================================
# Category 5: Insight Generation
# ============================================================================

def generate_autonomous_insights(results: dict[str, Any]) -> list[str]:
    """Generate autonomous intelligence insights from analysis results."""
    # Implementation...
```

### Key Design Principles

1. **Pure Functions:** All calculations are stateless (no `self`, no side effects)
2. **Optional Logger:** Each function accepts `log: logging.Logger | None = None` parameter
3. **Lazy Imports:** Use `_get_extractors()` helper to avoid circular dependencies
4. **Type Hints:** Full type annotations for all parameters and returns
5. **Defensive Programming:** Try/except blocks with sensible defaults
6. **Backward Compatible:** Orchestrator keeps wrapper methods that delegate

---

## Implementation Steps

### Step 1: Create Module (30 minutes)

**Tasks:**

1. Create `src/ultimate_discord_intelligence_bot/orchestrator/analytics_calculators.py`
2. Add module docstring
3. Add imports and lazy import helpers
4. Create section comments for 5 categories

**File Structure:**

```python
# Module header + docstring
# Imports (typing, logging, StepResult)
# Lazy import helpers
# Category 1: Threat & Risk (12 functions)
# Category 2: Quality & Confidence (8 functions)
# Category 3: Summary & Statistics (4 functions)
# Category 4: Resource Planning (4 functions)
# Category 5: Insight Generation (6 functions)
```

### Step 2: Extract Threat & Risk Methods (90 minutes)

**Order of Extraction:**

1. Simple calculations first (threat_level, behavioral_risk, persona_confidence)
2. Medium complexity next (composite_deception_score, contextual_relevance)
3. Complex calculations last (comprehensive_threat_score)

**Pattern:**

```python
# BEFORE (in orchestrator)
def _calculate_threat_level(self, deception_result: Any, fallacy_result: Any) -> str:
    """Calculate threat level from deception and fallacy analysis."""
    try:
        # ... implementation ...
    except Exception:
        self.logger.warning("Error calculating threat level")
        return "unknown"

# AFTER (in analytics_calculators.py)
def calculate_threat_level(
    deception_result: Any, 
    fallacy_result: Any,
    log: logging.Logger | None = None
) -> str:
    """Calculate threat level from deception and fallacy analysis."""
    _logger = log or logger
    try:
        # ... implementation (no self references) ...
    except Exception:
        _logger.warning("Error calculating threat level")
        return "unknown"

# AFTER (in orchestrator - delegation)
def _calculate_threat_level(self, deception_result: Any, fallacy_result: Any) -> str:
    """Delegates to analytics_calculators.calculate_threat_level."""
    return analytics_calculators.calculate_threat_level(
        deception_result, fallacy_result, self.logger
    )
```

### Step 3: Extract Quality & Confidence Methods (60 minutes)

**Focus:** 8 methods, mostly simple pure functions
**Key Challenge:** Some reference `self.logger` - replace with parameter

### Step 4: Extract Summary & Statistics Methods (60 minutes)

**Focus:** 4 methods, including complex `_calculate_summary_statistics`
**Key Challenge:** Many data sources - ensure all params passed correctly

### Step 5: Extract Resource Planning Methods (45 minutes)

**Focus:** 4 methods, consolidate duplicate `_calculate_resource_requirements`
**Action:** Keep single version, remove duplicate

### Step 6: Extract Insight Generation Methods (90 minutes)

**Focus:** 6 methods with complex logic
**Key Challenge:** `_generate_autonomous_insights` is 105 lines - ensure clean extraction

### Step 7: Update Orchestrator (60 minutes)

**Tasks:**

1. Add `analytics_calculators` import at top
2. Replace 34 method implementations with delegations
3. Keep wrapper methods for backward compatibility
4. Ensure all `self.logger` passed to functions

**Import Statement:**

```python
from . import (
    analytics_calculators,  # NEW
    crew_builders,
    data_transformers,
    discord_helpers,
    error_handlers,
    extractors,
    quality_assessors,
    system_validators,
)
```

### Step 8: Register Module (5 minutes)

Update `src/ultimate_discord_intelligence_bot/orchestrator/__init__.py`:

```python
from . import (
    analytics_calculators,  # NEW
    crew_builders,
    data_transformers,
    discord_helpers,
    error_handlers,
    extractors,
    quality_assessors,
    system_validators,
)

__all__ = [
    "analytics_calculators",  # NEW
    "crew_builders",
    "data_transformers",
    "discord_helpers",
    "error_handlers",
    "extractors",
    "quality_assessors",
    "system_validators",
]
```

---

## Validation Plan

### Test Strategy

**Good News:** Existing tests already validate these calculations through orchestrator integration!

**Approach:**

1. Run full orchestrator test suite (`pytest tests/orchestrator/ -v`)
2. Verify 280/281 tests still passing
3. Check for import errors
4. Validate delegation pattern working

**No New Tests Needed:** Week 2 pattern confirmed - existing tests validate via orchestrator.

### Validation Checklist

- [ ] Module imports successfully
- [ ] No circular import errors
- [ ] All 280+ orchestrator tests passing
- [ ] Fast tests passing (36/36)
- [ ] Lint checks clean
- [ ] Format compliance
- [ ] File size reduced by ~1,000 lines

---

## Risk Assessment

### LOW RISK ✅

**Why Low Risk:**

1. **Pure functions:** Most calculations are stateless
2. **Existing tests:** 280+ tests validate behavior
3. **Proven pattern:** Week 2 delegation pattern works perfectly
4. **No breaking changes:** Wrapper methods preserve API

### Potential Issues & Mitigations

**Issue 1: Circular Imports with Extractors**

- **Mitigation:** Use lazy import pattern (`_get_extractors()`)
- **Precedent:** Week 2 metrics import fix

**Issue 2: Duplicate `_calculate_resource_requirements`**

- **Mitigation:** Compare implementations, keep best version, remove duplicate
- **Impact:** Additional line reduction (bonus!)

**Issue 3: Complex `_generate_autonomous_insights` (105 lines)**

- **Mitigation:** Extract carefully, test thoroughly
- **Fallback:** Can split into helper functions if needed

---

## Success Criteria

### Must Have (Critical)

- [ ] All 34 methods extracted to analytics_calculators.py
- [ ] Orchestrator reduced by ~1,000 lines (5,655 → ~4,655)
- [ ] **<5,000 line target ACHIEVED** 🎯
- [ ] All 280+ tests passing (0 regressions)
- [ ] No import errors
- [ ] Backward compatibility maintained

### Should Have (Important)

- [ ] Module properly documented
- [ ] Clean separation of 5 categories
- [ ] Lazy imports for dependencies
- [ ] Optional logger parameter pattern

### Nice to Have (Bonus)

- [ ] Consolidate duplicate methods (extra reduction)
- [ ] Extraction summary document
- [ ] Updated INDEX.md

---

## Timeline & Estimates

| Phase | Task | Estimated Time |
|-------|------|----------------|
| **Planning** | Method identification (DONE) | 1 hour ✅ |
| | Plan documentation (THIS DOC) | 1 hour |
| **Implementation** | Create module structure | 30 min |
| | Extract Category 1 (Threat) | 90 min |
| | Extract Category 2 (Quality) | 60 min |
| | Extract Category 3 (Summary) | 60 min |
| | Extract Category 4 (Resource) | 45 min |
| | Extract Category 5 (Insights) | 90 min |
| | Update orchestrator delegations | 60 min |
| | Register module | 5 min |
| **Validation** | Run tests | 15 min |
| | Fix any issues | 30 min |
| | Format + lint | 10 min |
| **Documentation** | Extraction summary | 30 min |
| | Update INDEX.md | 10 min |
| | Git commit | 5 min |
| **TOTAL** | | **8.5 hours** |

**Optimistic:** 6 hours (if no issues)  
**Realistic:** 8.5 hours  
**Pessimistic:** 10 hours (if complex refactoring needed)

---

## Next Session Action Items

### Immediate (Start of Next Session)

1. **Create analytics_calculators.py module** (30 min)
   - Module docstring
   - Section comments
   - Lazy import helpers

2. **Begin Category 1 extraction** (90 min)
   - Start with simple methods
   - Test after each 3-4 methods
   - Validate no regressions

3. **Continue methodically through categories** (4 hours)
   - One category at a time
   - Test frequently
   - Document any issues

### Definition of Done

**Week 3 extraction is complete when:**

✅ All 34 methods extracted  
✅ Orchestrator <4,700 lines  
✅ All tests passing (280+/281)  
✅ No import errors  
✅ Module registered and exported  
✅ Extraction summary created  
✅ Changes committed to git  

**Bonus Achievement:** <5,000 line target reached in Week 3 (2 weeks early)! 🎉

---

## Long-Term Vision

### After Week 3

**Orchestrator State:**

- ~4,655 lines (from original 7,834)
- **41.8% reduction** 🎯
- **<5,000 line target ACHIEVED**
- 8 extracted modules (3,000+ lines)

**Remaining Opportunities:**

- Workflow state management (~100-150 lines)
- Session management (~50-80 lines)
- Final cleanup and polish (~50-100 lines)

**Target End State (Week 4-5):**

- Orchestrator: **<4,500 lines**
- Total reduction: **>43%**
- 9-10 extracted modules
- Ready for performance optimization phase

---

## Comparison to Original Plan

**Original Plan (from NEXT_STEPS_LOGICAL_PROGRESSION.md):**

- Week 3: Extract result_processors.py (~450 lines)
- Week 4: Extract analytics_calculators.py (~250 lines)
- Achieve <5,000 by Week 5

**Revised Reality:**

- Week 3: Extract analytics_calculators.py (~1,000 lines)
- **Achieve <5,000 in Week 3** (2 weeks early!)
- Week 4: Final cleanup + optimization prep

**Why the Change:**

- analytics_calculators is larger and more cohesive than estimated
- Methods are highly stateless (easier to extract)
- result_processors methods may already be delegating to data_transformers
- Better to extract one large cohesive module than two small ones

---

**Status:** 📋 **READY TO EXECUTE**  
**Risk Level:** 🟢 **LOW**  
**Expected Outcome:** 🎯 **<5,000 LINE TARGET ACHIEVED**  
**Timeline:** 8.5 hours implementation + validation

---

*Created: January 4, 2025*  
*Staff+ Engineering Agent - Week 3 Planning*
