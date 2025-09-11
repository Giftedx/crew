# Advanced Prompt Compression

This document describes the multi-pass prompt compression pipeline guarded by the feature flag `ENABLE_PROMPT_COMPRESSION`.

## Overview

The compression pass runs inside `PromptEngine.optimise()` and is fully bypassed unless the environment variable `ENABLE_PROMPT_COMPRESSION` is present with a truthy value (`1|true|yes|on`). We intentionally require *env presence* so stale cached settings objects (from parallel import paths) cannot lock the flag in an enabled state after unset.

## Goals

- Reduce token usage (lower cost / latency)
- Stabilize noisy prompts (duplicate lines, excessive blank spacing)
- Preserve semantic fidelity while providing observability via metrics

## Pipeline Stages

1. Repeated blank line collapse (configurable max run length via `prompt_compression_max_repeated_blank_lines`, default `1`).
1. Consecutive identical line deduplication.
1. Intra-line space squeeze (except for indented/code-like lines beginning with 4 spaces or a tab to preserve code blocks).
1. Long section summarisation:
   - Sections are contiguous non-blank line groups.
   - If a section exceeds 40 lines (`MAX_SECTION_LINES` constant), retain the first and last 5 lines (`HEAD_TAIL_KEEP`) inserting a marker: `...[omitted N lines]...`.
1. Metric emission for compression effectiveness.

All stages are pure transforms; failures silently fall back to the original prompt.

## Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `prompt_compression_ratio` | Histogram | tenant, workspace, method | Ratio = compressed_tokens / original_tokens (method currently `optimise`). |

A ratio < 1.0 indicates net savings. Ratios are computed using the same token counting heuristics as the rest of the system (OpenAI model encodings when available, Transformers tokenizers, then whitespace fallback with long-unbroken heuristic).

## Configuration

| Setting | Source | Default | Effect |
|---------|--------|---------|--------|
| `ENABLE_PROMPT_COMPRESSION` | Environment variable | off | Enables pipeline. |
| `prompt_compression_max_repeated_blank_lines` | Settings (`core.settings.Settings`) | 1 | Upper bound of blank lines preserved in any blank run. |

## Flag Precedence & Caching

`PromptEngine.optimise()` combines three signals:

- Environment variable presence (authoritative)
- `enable_prompt_compression` attribute
- `enable_prompt_compression_flag` alias attribute

If the env var is *absent*, cached settings values are ignored to avoid order-dependent test leakage.

## Disabled Behavior

When disabled, `optimise()` returns the original prompt (no interior structural modifications). External callers may still strip or normalise independently if desired.

## Regression Test

`tests/test_prompt_compression.py::test_prompt_compression_enable_then_disable_regression` verifies the flag can be toggled off in-process without stale effects.

## Future Enhancements (Roadmap)

- Adaptive summarisation thresholds keyed to model context window.
- Language-aware whitespace handling (e.g. Markdown lists, tables).
- Entropy-based redundancy trimming (n-gram frequency analysis).
- Optional semantic diff check to abort if compression alters meaning beyond a threshold (guardrail mode).

---
For related retrieval and caching optimisations, see `docs/rag.md` and `docs/memory.md`.
