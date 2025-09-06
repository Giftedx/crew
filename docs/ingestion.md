# Ingestion Guide

This document describes the comprehensive ingestion pipeline for multi-platform content.
It supports fetching metadata and transcripts from YouTube, Twitch, and TikTok,
transcribing audio when transcripts are missing, content analysis and segmentation,
and pushing processed chunks into a Qdrant vector store for later retrieval.

## Supported Platforms

- **YouTube** - Videos, channels, playlists with captions and metadata
- **Twitch** - Streams, clips, and chat integration  
- **TikTok** - Short-form videos with audio transcription
- **Multi-platform** - Unified dispatcher for URL routing

## Running a one-shot ingest

```bash
python -m ingest <url> --tenant <tenant> --workspace <workspace>
```

Examples:
```bash
# YouTube video
python -m ingest https://youtu.be/dummy --tenant default --workspace main

# Twitch clip  
python -m ingest https://clips.twitch.tv/dummy --tenant default --workspace main

# TikTok video (including short links)
python -m ingest https://vm.tiktok.com/dummy --tenant default --workspace main
```

## Pipeline Components

### Content Download
- Platform-specific downloaders using `yt-dlp` base classes
- Quality parameter support for video/audio optimization
- Metadata extraction (title, description, duration, etc.)
- Error handling with `StepResult` dataclass

### Analysis Pipeline
- **Transcript segmentation** - Chunks content using `analysis.segmenter`
- **Topic extraction** - Identifies key topics with `analysis.topics`  
- **Claim extraction** - Extracts factual claims for verification
- **Sentiment analysis** - Analyzes emotional tone

### Vector Storage
- Tenant-aware namespacing in Qdrant
- Hybrid storage with SQLite metadata
- Retention policy enforcement
- Embedding generation and indexing

### Error Handling and Fallbacks
- Transcript fetch failures: the pipeline falls back to Whisper transcription. In tests, this path is stubbed to avoid heavy dependencies.
- Missing creator or episode id: creator defaults to `"unknown"`; episode id falls back to a stable hash of the URL and is used consistently in payloads and provenance.
- `published_at` normalization: accepts strings, datetimes, or `None`. Naive datetimes are treated as UTC and emitted as ISO8601.

#### Strict Mode (Optional)

Enable `ENABLE_INGEST_STRICT=1` to fail fast when required metadata is missing:

- Missing creator (channel/streamer) → error
- Missing episode id → error (instead of using URL-hash fallback)

Use in canary/staging to surface upstream provider regressions early.

## Operations Runbook

### Strict‑Mode Triage
- Symptom: Ingest fails with "ingest strict mode violation".
- Immediate steps:
  1. Check provider health and recent API changes.
  2. Inspect logs for missing fields (creator/id) and the affected URLs.
  3. If this is an upstream regression, disable strict mode temporarily:
     `unset ENABLE_INGEST_STRICT` (or set to `0`) and redeploy.
  4. File an issue to track normalisation fixes or provider adapter updates.

### Fallback Spike Triage
- Symptom: Sudden increase in transcript/id fallbacks.
- Immediate steps:
  1. Open Grafana: Ingest Fallbacks dashboard; filter by source.
  2. Check `/metrics` for `ingest_transcript_fallbacks_total` and `ingest_missing_id_fallbacks_total` deltas.
  3. Sample a few recent URLs; verify captions/metadata availability.
  4. If widespread, pause non‑essential ingest; create a provider incident and track status. Re‑enable after upstream recovery.

## Configuration

The pipeline reads configuration from `config/ingest.yaml`:

```yaml
platforms:
  youtube:
    quality: best              # Video quality preference
    extract_subtitles: true    # Download captions
    max_duration: 7200         # 2 hours max
    
  twitch:
    quality: source           # Source quality preferred
    extract_chat: true        # Include chat messages
    max_clips: 50            # Clip limit per stream
    
  tiktok:
    quality: best
    extract_audio: true       # Audio for transcription
    
processing:
  chunk_size: 800             # Characters per chunk
  chunk_overlap: 200          # Overlap between chunks
  enable_transcription: true  # Audio-to-text
```

Environment variables for external services are required:
- `OPENAI_API_KEY` or `OPENROUTER_API_KEY` - For transcription and processing
- `QDRANT_URL` - Vector database connection
- Platform-specific API keys when needed

## Advanced Features

### Scheduled Ingestion
Configure recurring ingestion via the scheduler:

```python
from scheduler import Scheduler, PriorityQueue
from ingest.sources.youtube import YouTubeConnector

sched.add_watch(
    tenant='default', 
    workspace='main', 
    source_type='youtube', 
    handle='channel_id'
)
```

### Quality Control
- Content verification before storage
- Duplicate detection and deduplication  
- Policy compliance checking
- Error recovery and retries

### Performance Optimization
- Parallel processing for multiple URLs
- Caching of processed content
- Incremental updates for channels/playlists
- Resource usage monitoring

#### Concurrent Metadata + Transcript Fetch (Experimental)

An optional feature flag `ENABLE_INGEST_CONCURRENT` enables concurrent fetching of
video metadata and its transcript for supported platforms (currently YouTube
and Twitch). When set (any non-empty value), the ingestion pipeline spawns a
small thread pool (max 2 workers) to issue both network calls in parallel,
reducing end-to-end latency particularly for sources with non-trivial caption
latency.

Behavior:
* Default: flag unset -> sequential (baseline, deterministic ordering)
* Enabled: concurrent; on unexpected executor errors the code transparently
  falls back to the sequential path
* Transcript errors are isolated: a transcript fetch failure downgrades to
  `None` and the pipeline triggers the Whisper fallback transcription path.

Operational Guidance:
* Enable incrementally in staging before production wide rollout
* Pair with observability (tracing + a latency histogram) for before/after
  comparisons (future enhancement)
* Safe to disable at any time; only affects the metadata + transcript phase

Example (bash):
```bash
export ENABLE_INGEST_CONCURRENT=1
python -m ingest https://youtu.be/dummy --tenant default --workspace main
```

## Console Script (Optional)

Installing the project also exposes a console entry point named `ingest`:

```bash
ingest https://youtu.be/dummy --tenant default --workspace main
```

Notes:
* Your virtual environment's `bin` directory must be on `PATH` (activate it with `source venv/bin/activate` or use the absolute path: `./venv/bin/ingest`).
* The console script is functionally equivalent to `python -m ingest` and simply dispatches to `ingest.__main__:main`.
* Documentation examples keep `python -m ingest` because it works even if the console script is not on `PATH`.
* After modifying `pyproject.toml` you must reinstall (`pip install -e .`) for entry point changes to take effect.
