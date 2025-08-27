# Discord CDN Archiver

The archiver stores project artifacts in Discord and keeps enough metadata to
re‑fetch them when CDN links expire. Discord’s default per‑attachment upload
limit is roughly **10 MiB** unless a server’s boost tier raises it. Because CDN
links are temporary and signed, the manifest records the message ID and all
attachment IDs instead of raw URLs. Compression parameters are persisted so
future re‑uploads can avoid double re‑encoding.

## Limit Detection and Policy

`limits.detect` reads environment overrides (e.g.
`DISCORD_UPLOAD_LIMIT_BYTES`) and falls back to 10 MiB when no guild‑specific
limit is known. Files pass through `policy.check` which enforces allowlists,
size ceilings and EXIF stripping before any data leaves the machine.

## Compression and Routing

`compress.fit_to_limit` transcodes media to meet the detected limit—downscaling
images or adjusting ffmpeg parameters for audio/video. Files are routed through
`router.pick_channel` using `config/archive_routes.yaml`; a SHA‑256 hash avoids
duplicate uploads.

## Usage

```python
from archive.discord_store import archive_file
archive_file("example.png", {"kind": "images", "visibility": "public"})
```

## Rehydration

`rehydrate.fetch_attachment` resolves a fresh signed URL by refetching the
message and attachment via the Discord API, ensuring long‑term access even as
CDN links expire.

## REST API and CLI

- `POST /api/archive` — multipart upload with metadata.
- `GET /api/archive/{hash}` — return a fresh temporary URL.
- `GET /api/archive/search?tag=foo` — search by tag.
- `python -m archive.discord_store.uploader <path>` — one‑shot CLI uploader.

URLs returned by the API are always fetched via message/attachment IDs; the
`media.discordapp.net` proxy is never used for persistence.

## Environment

- `DISCORD_BOT_TOKEN`
- `ENABLE_DISCORD_ARCHIVER` (default `1`)
- `ARCHIVER_ALLOW_WEBHOOK_FALLBACK` (default `0`)
- `ARCHIVE_DB_PATH` (optional manifest location)
- `ARCHIVE_API_TOKEN` (auth token for REST API)
