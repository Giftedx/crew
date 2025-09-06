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

## Tips
- Keep feature flags minimal at first; enable advanced ones as needed
- Prefer `OPENROUTER_API_KEY` or `OPENAI_API_KEY` (either works)
- Use tenants to keep workspaces isolated per team/project
- Strict ingest checks (optional): enable `ENABLE_INGEST_STRICT=1` in staging to catch missing provider metadata early; see `docs/ingestion.md` runbook.
