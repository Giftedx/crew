# CrewAI Discord Bot Architecture

This document summarises how the key pieces of the CrewAI content system fit
together and highlights opportunities for optimisation.

## High level design

The repository centres around an asynchronous `ContentPipeline` that downloads
videos, uploads them to Google Drive, transcribes the audio, analyses the text
and posts a summary to Discord.  Each stage is implemented as an isolated tool
whose job is to interact with an external service.

```
YouTube -> Drive -> Transcription -> Analysis -> Discord
```

Configuration and secrets are supplied through environment variables as defined
in `settings.py`.  This keeps the project portable across Linux, macOS and
Windows.

## Agents and tasks

The `config/agents.yaml` and `config/tasks.yaml` files describe the higher level
CrewAI agents and tasks used when running the project under the CrewAI runtime.
Agents wrap language models with specific goals while tasks orchestrate those
agents to perform monitoring, downloading, analysis and posting activities.

## Tools

Each interaction with an external system is encapsulated in a tool living under
`tools/`.

- `youtube_download_tool.py` – uses `yt-dlp` to fetch videos and returns metadata
  including the local file path.
- `drive_upload_tool.py` – uploads files to Google Drive and produces shareable
  links suitable for Discord embeds.
- `audio_transcription_tool.py` – lazily loads Whisper models to transcribe
  audio.
- `text_analysis_tool.py` – performs sentiment and keyword extraction using
  NLTK.
- `discord_post_tool.py` – posts either embeds or direct uploads to Discord via a
  webhook.

Custom tools exist for Instagram, TikTok and other platforms, following the same
pattern.

## Model Context Protocol (MCP)

CrewAI uses the MCP to let agents invoke tools safely.  In this project the
pipeline tools are simple functions but they can be exposed to MCP-aware agents
through the CrewAI framework.  The declarative agent and task configuration files
allow other MCP compatible runtimes to drive the same tools.

## Recent refactor

To simplify orchestration and improve reliability the pipeline now wraps all
step results in a small dataclass `StepResult`.  This removes repetitive status
handling, provides a typed interface for callers and ensures every stage returns
structured data.

## Potential optimisations

- **Parallelism** – independent steps such as Drive uploads and transcription
  could be processed concurrently to reduce end-to-end latency.
- **Batch processing** – when monitoring multiple channels it may be more
  efficient to queue downloads and run them in batches.
- **Alternative tools** – open source libraries such as `pytube` or `discord.py`
  could replace shell invocations for tighter integration and better error
  reporting.
- **Caching** – caching of transcripts or analysis for unchanged videos would
  avoid redundant processing.

## Conclusion

The current architecture cleanly separates concerns into dedicated tools and a
coordinating pipeline.  The new `StepResult` abstraction further improves
maintainability.  With additional concurrency and caching the system can scale
further while remaining easy to reason about.
