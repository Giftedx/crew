# Setup & Run Wizard

The unified setup wizard configures everything you need (core + advanced) and writes/merges your `.env`, creates folders, and optionally scaffolds tenant files.

## Quick Start

- Run the wizard: `python -m ultimate_discord_intelligence_bot.setup_cli`
- Check health: `python -m ultimate_discord_intelligence_bot.setup_cli doctor`
- Run bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- Run crew: `python -m ultimate_discord_intelligence_bot.setup_cli run crew`

Make shortcuts: `make setup`, `make doctor`, `make run-discord`, `make run-crew`.

## Prompts & Options

- Tokens: `DISCORD_BOT_TOKEN`, `DISCORD_WEBHOOK`, `DISCORD_PRIVATE_WEBHOOK`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `EXA_API_KEY`, `PERPLEXITY_API_KEY`.
  - Optional backends used by some tools: `SERPLY_API_KEY`, `WOLFRAM_ALPHA_APP_ID`.
- Vector DB: `QDRANT_URL` (default `http://localhost:6333`), `QDRANT_API_KEY`.
- Downloads: `DEFAULT_DOWNLOAD_QUALITY` (default `1080p`).
- Paths: `CREWAI_BASE_DIR`, `CREWAI_DOWNLOADS_DIR`, `CREWAI_CONFIG_DIR`, `CREWAI_LOGS_DIR`, `CREWAI_PROCESSING_DIR`, `CREWAI_YTDLP_DIR`.
- Google: `GOOGLE_CREDENTIALS` path.
- Feature flags: enable/disable ingestion (YouTube/Twitch/TikTok, `ENABLE_INGEST_CONCURRENT`), RAG/vector/grounding, caching, RL (global/routing/prompt/retrieval), Discord features, privacy/moderation/rate limiting, tracing/metrics/audit.
- HTTP & retries: `HTTP_TIMEOUT`, `ENABLE_HTTP_RETRY`, `RETRY_MAX_ATTEMPTS`.
- Tracing (optional): `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`.
- Tenant scaffolding: `TENANT_SLUG`, guild id, `tenants/<slug>/routing.yaml` allowed models, budgets (`daily_cap_usd`, `max_per_request`), policy overrides (allowed sources). Files are written to `tenants/<slug>/`.
- Ingest DB (optional): `INGEST_DB_PATH` for provenance/usage logs.
- Discord upload limits (optional): `DISCORD_UPLOAD_LIMIT_BYTES`, `DISCORD_UPLOAD_LIMIT_WEBHOOK_BYTES`, and per‑guild overrides via `guild:bytes` CSV.

## Doctor Checks

- Ensures required env (at minimum `DISCORD_BOT_TOKEN`) is present.
- Verifies `ffmpeg` is installed (required). Warns if `yt-dlp` is missing (optional).

The wizard is safe to re-run; it merges updates without discarding existing values.
