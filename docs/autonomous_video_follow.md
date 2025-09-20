# Autonomous Video Follow & Backfill

Goal: After a user submits a video (Discord or API), the system processes it end-to-end and then automatically follows the uploader/channel. It enumerates all videos from the last 12 months and enqueues them for processing. This feature is opt-in via flags and reuses existing scheduler, ingest, and pipeline seams.

## High-level flow

1) User invokes a command (e.g., /analyze) with a video URL.
1) ContentPipeline downloads, transcribes, analyzes, persists memory, posts to Discord.
1) Post-processing hook calls `trigger_auto_follow(download_result, queue, tenant, workspace)`.
1) Auto-follow checks flags; if enabled and platform is YouTube, builds a BackfillPlan.
1) Backfill enumerates uploader's recent videos (yt-dlp extract_flat) since 12 months ago and enqueues ingest jobs.
1) Scheduler picks jobs and runs `ingest.pipeline.run`, which builds transcripts, topics, and memory entries.

## New modules

- `src/ingest/backfill.py`
  - `BackfillPlan`: parameters for backfill (source_type, uploader_handle, tenant/workspace, since_iso, limit)
  - `enumerate_youtube_recent_videos(handle_or_url, since_iso, limit)`: returns `[ {external_id, url}, ... ]` using yt-dlp in flat mode. Guarded by `ENABLE_UPLOADER_BACKFILL=1`.
  - `enqueue_backfill(plan, queue)`: composes `IngestJob`s and calls `queue.enqueue_bulk`.

- `src/ultimate_discord_intelligence_bot/auto_follow.py`
  - `trigger_auto_follow(download_result, queue, tenant, workspace)`: reads `platform` and `uploader` from the download step and enqueues a 12-month backfill if `ENABLE_AUTO_FOLLOW_UPLOADER=1`.

## Discord integration points

- The `PipelineTool` and `ContentPipeline` already coordinate download/transcription/analysis. Call `trigger_auto_follow` after a successful download to auto-enqueue backfill.
- Add a user-facing toggle command later (e.g., `/follow_uploader on|off`) to set the flag at runtime or per-guild.

## Feature flags

- `ENABLE_AUTO_FOLLOW_UPLOADER=1` – turn on auto-follow behavior after downloads.
- `ENABLE_UPLOADER_BACKFILL=1` – allow yt-dlp channel enumeration and enqueueing.
- `AUTO_FOLLOW_MAX_VIDEOS=200` – cap backfill size.

## Data contracts

- Ingest job: existing `ingest.pipeline.IngestJob` (source, external_id, url, tenant, workspace, tags, visibility)
- Queue: existing `scheduler.PriorityQueue` (supports `enqueue_bulk`)

## Edge cases

- yt-dlp missing: backfill returns 0 (no-op).
- Private/deleted videos: filtered out by yt-dlp or fail during pipeline; scheduler dedupe prevents thrash.
- Non-YouTube sources: ignored by current backfill implementation.
- Missing uploader name: skip auto-follow.

## Acceptance criteria

- With flags enabled, submitting a YouTube video results in N>=0 additional jobs enqueued for same tenant/workspace.
- With flags disabled, no change in behavior.
- No network calls made during tests unless explicitly enabled by flags; backfill gracefully degrades.
