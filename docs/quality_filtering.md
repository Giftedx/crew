# Quality Filtering & Lightweight Processing

This document describes the Week 4 optimization: early transcript quality assessment enabling a *lightweight processing* path that skips full analysis for low‑value content.

## Overview

1. Transcription completes as usual.
2. Quality assessment runs (feature‑flag controlled by `ENABLE_QUALITY_FILTERING`).
3. If transcript fails majority of quality thresholds, pipeline records a bypass and executes a lightweight finalization path (fast summary + minimal memory write) instead of the full analysis fan‑out.
4. If assessment fails (tool error), pipeline safely falls back to full analysis.

## Feature Flag

| Env Var | Default | Effect |
|---------|---------|--------|
| `ENABLE_QUALITY_FILTERING` | `1` | Enable quality gating logic (set to `0` to always run full analysis). |

## Threshold Environment Variables

The `ContentQualityAssessmentTool` reads minimum thresholds *at import time*:

| Env Var | Default | Purpose |
|---------|---------|---------|
| `QUALITY_MIN_WORD_COUNT` | `500` | Minimum word count for a strong transcript. |
| `QUALITY_MIN_SENTENCE_COUNT` | `10` | Minimum sentence count for structure. |
| `QUALITY_MIN_COHERENCE` | `0.6` | Minimum coherence score (diversity + sentence length consistency). |
| `QUALITY_MIN_OVERALL` | `0.65` | Minimum aggregated weighted score. |

> IMPORTANT: Because these are evaluated when the class is imported, tests that need different thresholds must either:
>
> * Set env vars **before** importing the tool, or
> * Override class attributes directly (e.g., `ContentQualityAssessmentTool.MIN_WORD_COUNT = 150`).

## Processing Decision Logic

```text
word_count >= MIN_WORD_COUNT
sentence_count >= MIN_SENTENCE_COUNT
coherence_score >= MIN_COHERENCE_SCORE
overall_quality_score >= MIN_OVERALL_SCORE
```

A *majority* (≥ 3 of 4) passing triggers full processing. Otherwise the pipeline executes the lightweight path.

## Returned Fields (Tool)

The tool returns a `StepResult.ok(result={ ... })` with nested fields:

* `quality_metrics` (dict)
* `should_process_fully` (bool)
* `should_process` (alias for pipeline compatibility)
* `overall_score`
* `recommendation` (categorical: `full_analysis|standard_analysis|basic_analysis|minimal_processing`)
* `recommendation_details` (alias for pipeline compatibility)
* `bypass_reason` (string or `None`)

The orchestrator unwraps nested `result` if present.

## Lightweight Path Output

When bypassing full analysis, the pipeline finalizes with a payload containing at least:

```json
{
  "status": "success",
  "processing_type": "lightweight",
  "quality_score": 0.53,
  "summary": "Basic content processed",
  "title": "Example Title",
  "bypass_reason": "insufficient_content (words: 120 < 500)",
  "memory_stored": true,
  "time_saved_estimate": "60-75%"
}
```

(Planned improvement: include raw quality metric snapshot for observability.)

## Metrics & Observability

The phase reuses existing pipeline metric families where available:

* `PIPELINE_STEPS_COMPLETED{step="quality_filtering"}` incremented on pass path
* `PIPELINE_STEPS_SKIPPED{step="quality_filtering"}` incremented on bypass path
* `PIPELINE_STEP_DURATION{step="lightweight_processing"}` duration of lightweight finalization

Span attributes (OpenTelemetry) added:

* `quality_bypass` (bool)
* `bypass_reason` (string)
* `quality_score` (float)
* `processing_type` (when lightweight)

## Failure Behavior

| Failure Mode | Behavior |
|--------------|----------|
| Tool returns `success=False` | Log warning, continue with full analysis (safe fallback). |
| Tool raises import/runtime exception | Same as above (full analysis). |
| Lightweight memory store fails or times out | Logged; pipeline still returns success (does not upgrade to error). |

## Testing Strategy

Tests in `tests/test_quality_filtering_integration.py` cover:

* Low-quality transcript → bypass (`should_process` False)
* High-quality transcript (after threshold overrides) → full processing (`should_process` True)

Recommended future tests:

* End-to-end pipeline run with forced low-quality transcript validating `processing_type == 'lightweight'`.
* Threshold edge boundaries (exactly 3 vs 2 checks passing).
* Tool failure injection (simulated exception) asserting fallback to full path.

## Extensibility Notes

Future enhancements may include:

* Persisting full `quality_metrics` in lightweight memory payload (observability / analytics)
* Prometheus counters for bypass / failure reasons by category
* Adaptive thresholding using historical corpus statistics or tenant-level baselines
* Early partial transcript scoring during streaming transcription

## Quick Reference

| Scenario | Expected Path |
|----------|---------------|
| 2 or fewer checks pass | Lightweight |
| 3 or 4 checks pass | Full analysis |
| Tool error | Full analysis |
| Feature flag disabled | Full analysis |

---

For questions or follow-up improvements, see orchestrator `_quality_filtering_phase` and `ContentQualityAssessmentTool` implementation.
