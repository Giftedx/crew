# Getting Started

This guide provides a concise, one-path setup and run flow.

## Quick Start

- Setup: `python -m ultimate_discord_intelligence_bot.setup_cli`
- Doctor: `python -m ultimate_discord_intelligence_bot.setup_cli doctor`
- Run bot: `python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- Run crew: `python -m ultimate_discord_intelligence_bot.setup_cli run crew`

Make shortcuts: `make setup`, `make doctor`, `make run-discord`, `make run-crew`.

## What the Wizard Configures

- Tokens: Discord, OpenAI/OpenRouter, Exa, Perplexity
- Vector DB: Qdrant URL/API key
- Paths: downloads/config/logs/processing, yt-dlp directory
- Feature flags: ingestion, RAG/vector/grounding, caching, RL, Discord features, privacy/moderation, tracing/metrics
- HTTP & retries: timeouts and retry attempts
- Tenants: scaffolds `tenants/<slug>/` files (routing, budgets, policy overrides)
- Optional: ingest DB path and Discord upload limits

See details in `docs/setup_cli.md`.

## Common Discord Commands

- `!analyze <url>`: full analysis pipeline
- `!factcheck <claim>`: verdict with sources
- `!fallacy <text>`: logical fallacy detection
- `!status`: system status

## Troubleshooting

- Verify env: `python -m ultimate_discord_intelligence_bot.setup_cli doctor`
- Check logs: `tail -f logs/bot.log` (if logging configured)
- Restart: `pkill -f discord && python -m ultimate_discord_intelligence_bot.setup_cli run discord`
- Network/services: ensure Qdrant is reachable (`QDRANT_URL`) and ffmpeg is installed
- Drive optionality: If Google Drive credentials aren’t set, the pipeline uses a
  bypass implementation and marks the Drive step as skipped (no failure).
- Analyzer fallback: If NLTK data aren’t available, the analyzer falls back to a
  degraded stub. Install NLTK corpora later to enable full sentiment/keywords.

## Tips

- Keep feature flags minimal at first; enable advanced ones as needed
- Prefer `OPENROUTER_API_KEY` or `OPENAI_API_KEY` (either works)
- Use tenants to keep workspaces isolated per team/project
- Strict ingest checks (optional): enable `ENABLE_INGEST_STRICT=1` in staging to catch missing provider metadata early; see `docs/ingestion.md` runbook.

## Local Activities Development (Optional)

Discord Activities (Embedded Apps) can be tested locally alongside this API:

- Health probe for local Activity: `GET /activities/health` (returns `{ "status": "ok", "component": "activities" }`)
- Optional echo endpoint for debugging client wiring: enable with `ENABLE_ACTIVITIES_ECHO=1` and call `/activities/echo?q=ping`
- Follow Discord's local dev guide for URL mapping and launching from the client.
- See the curated references in [resources_index.md](resources_index.md) under "Discord Activities (Embedded Apps)".
- Quick local guide: [activities_local_dev.md](activities_local_dev.md)

Behavior notes:

- Activities endpoints are excluded from API response caching to ensure real-time responses while you iterate:
  - `/activities/health`
  - `/activities/echo` (enable with `ENABLE_ACTIVITIES_ECHO=1`)
- The example app includes a "Ping /activities/echo" button to visualize request info when echo is enabled.

Setup wizard toggles to help local Activities dev:

- Enable CORS for local web clients (Vite dev server origins)
- Enable the Activities echo endpoint for debugging

You can also export envs directly:

- `ENABLE_CORS=1` with `CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
- `ENABLE_ACTIVITIES_ECHO=1`

## Contributing

- Main pipeline orchestrator lives at `src/ultimate_discord_intelligence_bot/pipeline.py` (class `ContentPipeline`).

## Next: Type Safety (Optional)

When contributing new modules, see `docs/types_and_stubs.md` for the phased typing & stub strategy to avoid introducing fresh mypy debt.
