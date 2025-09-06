---
title: Pipeline Concurrency Enhancement Plan
origin: PIPELINE_CONCURRENCY_ENHANCEMENT.md (root)
status: migrated
last_moved: 2025-09-02
---

## Overview

This document captures the proposed enhancements to increase concurrency within the media processing pipeline while preserving correctness, idempotency, and resource efficiency.

## Goals

1. Reduce end-to-end latency for multi‑asset ingests (playlists, bulk uploads) by parallelizing independent steps.
2. Maintain deterministic ordering guarantees where required (e.g., transcript → analysis dependency chain).
3. Limit peak memory and network usage through bounded worker pools and adaptive backpressure.
4. Provide observability hooks (per-step timing, queue depth, failure classification) to support tuning.

## Current State (Sequential Bottlenecks)

````text
download -> store -> transcribe -> segment -> embed -> extract entities -> summarize -> persist artifacts
````

All steps currently await completion before the next begins. For N media assets, overall latency is approximately:  sum_i (T_download_i + T_transcribe_i + T_analysis_i)

## Concurrency Model Principles

| Principle | Rationale | Implementation Sketch |
|-----------|-----------|------------------------|
| Bounded parallelism | Avoid resource starvation & API rate breaches | Sized asyncio.Semaphore / anyio CapacityLimiter |
| Work partitioning by step | Different steps have distinct cost profiles | Separate queues per step with worker tasks |
| Failure isolation | One asset's failure shouldn't block others | Per-asset error channel & resilient continuation |
| Backpressure | Prevent unbounded queue growth | Downstream queue size thresholds trigger upstream slowdown |
| Idempotent step execution | Safe retries | Content‐addressable temp artifact keys |

## Proposed Architecture

````mermaid
flowchart LR
  A[Ingest Dispatcher] --> DQ[Download Queue]
  DQ -->|workers| DL[Download Workers]
  DL --> SQ[Speech Queue]
  SQ -->|workers| ST[Transcription Workers]
  ST --> PQ[Preprocess Queue]
  PQ -->|workers| PP[Segmentation/Chunk Workers]
  PP --> EQ[Embedding Queue]
  EQ -->|workers| EM[Embed Workers]
  EM --> AQ[Analysis Queue]
  AQ -->|workers| AN[Entity/Summary Workers]
  AN --> P[Persist]
  classDef queue fill:#222,stroke:#555,stroke-width:1px;
  class DQ,SQ,PQ,EQ,AQ queue;
````

### Concurrency Controls

| Queue | Worker Count Basis | Notes |
|-------|--------------------|-------|
| Download | min(4, cpu*2) | I/O bound (network) |
| Speech | gpu or cpu cores / model concurrency (config) | I/O+CPU hybrid (depends on model) |
| Preprocess | max(2, cpu/2) | CPU text operations |
| Embed | model.max_concurrency | Respect provider quotas |
| Analysis | adaptive (latency SLO) | Adjust via feedback loop |

### Adaptive Backpressure

1. Track moving average of queue depths (EMA window 30s).
2. If downstream depth > HIGH_WATERMARK, upstream enqueue awaits with exponential backoff (capped).
3. If sustained high watermark > 5 mins, emit advisory event (for auto-scaling hook).

### Error Propagation & Retry

| Failure Type | Strategy | Max Attempts |
|--------------|----------|--------------|
| Transient network | Exponential backoff | 4 |
| Rate limit (429) | Jitter + token bucket consult | 5 |
| Permanent (4xx non-429) | No retry | 1 |
| GPU OOM | Reduce batch size then retry | 3 |

### Idempotency Mechanisms

| Step | Key Derivation | Notes |
|------|-----------------|-------|
| Download | sha256(url) | Avoid re-fetch |
| Transcription | media_hash + model_id | Distinguish by model version |
| Chunking | transcript_hash + policy_version | Policy changes bust cache |
| Embedding | chunk_hash + embed_model | Reuse across analyses |
| Analysis | chunk_hash + analysis_config_hash | Parameterized tasks |

## Observability Plan

Metrics (Prometheus labels: step, status):

| Metric | Type | Description |
|--------|------|-------------|
| pipeline_step_duration_seconds | Histogram | Per step latency |
| pipeline_queue_depth | Gauge | Current items in queue |
| pipeline_in_flight | Gauge | Active workers |
| pipeline_step_failures_total | Counter | Failures by reason |
| pipeline_retries_total | Counter | Retry counts |

Structured events (JSON lines):

````json
{"ts":"2025-09-02T12:00:00Z","event":"pipeline.enqueue","step":"download","asset_id":"abc"}
{"ts":"2025-09-02T12:00:02Z","event":"pipeline.start","step":"transcribe","asset_id":"abc"}
{"ts":"2025-09-02T12:00:07Z","event":"pipeline.complete","step":"transcribe","asset_id":"abc","duration_ms":5000}
````

## Phased Implementation

| Phase | Scope | Exit Criteria |
|-------|-------|---------------|
| 1 | Extract queues + workers for download/transcription | Parallel download + transcription reduces latency >=30% on 5 asset batch |
| 2 | Add embedding/analysis queues & metrics | Metrics exported + p95 embedding step latency < baseline |
| 3 | Adaptive backpressure + error taxonomy | Zero unhandled queue overflow warnings for 24h |
| 4 | Dynamic scaling hooks | Autoscaler adjusts worker counts based on queue depth EMA |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-parallelization -> 429s | Slower overall progress | Token bucket gating + dynamic reduction |
| Memory pressure (large transcripts) | OOM / eviction | Cap transcript batch size; stream processing fallback |
| Complex debugging | Longer MTTR | Rich structured events + correlation ids |

## Success Metrics

| KPI | Baseline | Target |
|-----|----------|--------|
| Mean latency (5 asset batch) | 100% | <=70% baseline |
| p95 step latency (transcription) | 100% | <=80% baseline |
| 429 rate per 1000 requests | >5 | <1 |
| Retries leading to success | n/a | >=85% transient failures recover |

## Next Actions

1. Scaffold queue abstractions + worker loop.
2. Implement Phase 1 instrumentation.
3. Benchmark & capture baseline metrics prior to enablement.

---
Generated 2025-09-02
