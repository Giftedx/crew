---
title: Architecture Overview
origin: migrated_from_root:ARCHITECTURE.md
status: active
last_moved: 2025-09-02
---

## CrewAI Discord Bot Architecture

**Current Implementation** (verified November 3, 2025):

- **Pipeline**: 7 phases in `src/ultimate_discord_intelligence_bot/pipeline_components/orchestrator.py` (1637 lines)
- **Tools**: 111 across 9 categories
- **Agents**: 18 specialized agents
- **Architecture**: 3-layer (Platform/Domains/App)

<!-- Migrated from root ARCHITECTURE.md -->

This document summarises how the key pieces of the CrewAI content system fit together and highlights opportunities for optimisation.
together and highlights opportunities for optimisation.

### High level design

The repository centres around an asynchronous `ContentPipeline` that downloads
videos, uploads them to Google Drive, transcribes the audio, analyses the text
and posts a summary to Discord.  The pipeline accepts an optional `quality`
parameter so callers can cap the download resolution (default `1080p`). Each
stage is implemented as an isolated tool whose job is to interact with an
external service.  Downloads flow through a unified dispatcher so the pipeline
can ingest YouTube, Twitch, Kick, Twitter, Instagram, TikTok, Reddit and
Discord sources via the same entry point.

Source code location:

- Pipeline orchestrator: `src/ultimate_discord_intelligence_bot/pipeline.py` (class `ContentPipeline`)

```text
Video Platform -> Drive -> Transcription -> Analysis -> Discord
```

Configuration and secrets are supplied through environment variables as defined
in `src/ultimate_discord_intelligence_bot/settings.py`.  This keeps the project portable across Linux, macOS and
Windows.

### Agents and tasks

The `src/ultimate_discord_intelligence_bot/crew.py` file describes the higher level
CrewAI agents and tasks used when running the project under the CrewAI runtime.
Agents wrap language models with specific goals while tasks orchestrate those
agents to perform monitoring, downloading, analysis and posting activities.

### Tools

Each interaction with an external system is encapsulated in a tool living under
`src/ultimate_discord_intelligence_bot/tools/`.

- `yt_dlp_download_tool.py` – generic `yt-dlp` wrapper with subclasses for
  YouTube, Twitch, Kick, Instagram, TikTok, Reddit, Discord and X/Twitter downloads and an
  optional quality parameter to cap resolution.
- `multi_platform_download_tool.py` – dispatches to the appropriate downloader
  based on the URL (including `vm.tiktok.com`/`vt.tiktok.com` aliases) and
  returns `platform: "unknown"` for unsupported links.
- `drive_upload_tool.py` – uploads files to Google Drive and produces shareable
  links suitable for Discord embeds. If Google credentials are not configured or
  the Drive API is unavailable, the system automatically falls back to a bypass
  variant (`drive_upload_tool_bypass.py`) and marks the Drive step as skipped
  without failing the overall run.
- `audio_transcription_tool.py` – lazily loads Whisper models to transcribe
  audio.
- `text_analysis_tool.py` – performs sentiment and keyword extraction using
  NLTK (with a degraded stub fallback when NLTK is unavailable, so pipelines
  continue to run without hard dependency on NLTK data).
- `sentiment_tool.py` – standalone sentiment classifier using VADER or a
  simple lexical fallback.
- `logical_fallacy_tool.py` – flags basic logical fallacies in transcripts.
- `claim_extractor_tool.py` – stub for future factual claim extraction.
- `perspective_synthesizer_tool.py` – generates alternative viewpoints from the
  analysed text using the shared `PromptEngine`, `OpenRouterService` and
  `MemoryService` for contextual grounding.
- `discord_post_tool.py` – posts either embeds or direct uploads to Discord via a
  webhook.
- `discord_private_alert_tool.py` – sends operational alerts to a restricted
  webhook for monitoring.
- `tools/platform_resolver/` – lookup helpers turning platform handles into
  canonical channel or profile references. They support the creator profile
  system described below.

### Model Context Protocol (MCP)

CrewAI uses the MCP to let agents invoke tools safely.  In this project the
pipeline tools are simple functions but they can be exposed to MCP-aware agents
through the CrewAI framework.  The declarative agent and task configuration files
allow other MCP compatible runtimes to drive the same tools.
AST-based tests verify that those configuration files stay in sync with
`crew.py` and that each agent exposes the expected tools, preventing subtle
misconfigurations.

### Recent refactor

To simplify orchestration and improve reliability the pipeline now wraps all
step results in a small dataclass `StepResult`.  This removes repetitive status
handling, provides a typed interface for callers and ensures every stage returns
structured data.

### Global services

A set of lightweight services are available under
`src/ultimate_discord_intelligence_bot/services` to support efficient and grounded
language-model usage across the system:

- **PromptEngine** – central prompt builder and token counter using
  `tiktoken` and `transformers` tokenizers where available.
- **OpenRouterService** – dynamic model router with offline fallback.
  Defaults may be customised via `OPENROUTER_GENERAL_MODEL` and
  `OPENROUTER_ANALYSIS_MODEL`.
- **LearningEngine** – epsilon‑greedy policy that records routing rewards.
- **TokenMeter** – estimates request cost across models and enforces a
  per-request ceiling via `COST_MAX_PER_REQUEST`.
- **LLMCache** – deterministic prompt→response cache with configurable TTL so
  repeated prompts can be served without requerying models.
- **MemoryService** – minimal in-memory store for contextual lookups with
  optional case-insensitive metadata filtering. All entries are stored under a
  `<tenant>:<workspace>` namespace to prevent cross-tenant leakage. Calls may
  pass a `metadata` dictionary whose pairs must match stored metadata for a
  memory to be returned. Lookups honour a `limit` parameter where values below
  `1` or blank queries return no results. The service grounds the
  `PerspectiveSynthesizerTool`.
- **Profiles module** – dataclasses and a SQLite-backed `ProfileStore` to
  maintain verified creator, show and staff information. Seed data for the
  H3/H3 Podcast/Hasan ecosystem lives in `profiles.yaml` and resolution tools
  populate canonical IDs at runtime. The store now tracks cross-profile
  collaborations and exposes helper methods to record and query those links.
- **ContentPoller** – simple scheduler that updates profile `last_checked`
  timestamps, forming the basis of continuous ingestion.
- **EvaluationHarness** – runs prompts across models, logging latency and
  token usage for offline analysis and future training.

### Potential optimisations

- **Parallelism** – independent steps such as Drive uploads and transcription
  could be processed concurrently to reduce end-to-end latency.
- **Batch processing** – when monitoring multiple channels it may be more
  efficient to queue downloads and run them in batches.
- **Alternative tools** – open source libraries such as `pytube` or `discord.py`
  could replace shell invocations for tighter integration and better error
  reporting.
- **Caching** – caching of transcripts or analysis for unchanged videos would
  avoid redundant processing.

### Conclusion

The current architecture cleanly separates concerns into dedicated tools and a
coordinating pipeline.  The new `StepResult` abstraction further improves
maintainability.  With additional concurrency and caching the system can scale
further while remaining easy to reason about.
