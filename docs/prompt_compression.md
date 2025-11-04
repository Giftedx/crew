# Advanced Prompt Compression

**Current Implementation** (verified November 3, 2025):

- **Prompt Engine**: `src/ultimate_discord_intelligence_bot/services/prompt_engine.py`
- **DSPy Integration**: `src/platform/prompts/` (advanced prompt engineering)
- **Feature Flag**: `ENABLE_PROMPT_COMPRESSION` with source policy configuration
- **Metrics**: `prompt_compression_ratio` histogram for compression effectiveness

This document describes the multi-pass prompt compression pipeline guarded by feature flags and settings.

## Overview

The compression pass runs inside `PromptEngine.optimise()` and is conditionally enabled based on a configurable source policy:

- `ENABLE_PROMPT_COMPRESSION` (env boolean): "1|true|yes|on" to enable when using env policy.
- `PROMPT_COMPRESSION_SOURCE` (env): selects enablement source — `env` (default), `settings`, or `both`.
  - `env` (default): use only the env variable; if the env var is present but falsy, a truthy settings flag may still enable; if the env var is absent, settings are ignored (backward-compatible).
  - `settings`: ignore env; honor `settings.enable_prompt_compression` (or `settings.enable_prompt_compression_flag`).
  - `both`: enabled if either env or settings enable it.

These semantics match `ultimate_discord_intelligence_bot/services/prompt_engine.py` (`PromptEngine.optimise`).

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

A ratio < 1.0 indicates net savings. Ratios are computed using the same token counting heuristics as the rest of the system (OpenAI model encodings when available, Transformers tokenizers, then whitespace fallback with a long-unbroken heuristic). The fallback heuristic treats very long contiguous text (no whitespace) as approximately one token per ~4 characters to avoid dramatically underestimating budget usage.

## Configuration

| Setting | Source | Default | Effect |
|---------|--------|---------|--------|
| `ENABLE_PROMPT_COMPRESSION` | Environment variable | off | Enables pipeline under `env`/`both` policies. |
| `PROMPT_COMPRESSION_SOURCE` | Environment variable | `env` | Selects policy: `env` \| `settings` \| `both`. |
| `enable_prompt_compression` / `enable_prompt_compression_flag` | Settings (`core.settings.Settings`) | off | Enables pipeline under `settings`/`both` policies (and under `env` when env var present but falsy). |
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

See also: `docs/feature_flags.md` for enablement policies and environment sources.
