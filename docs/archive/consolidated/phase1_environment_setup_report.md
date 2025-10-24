# Phase 1 Environment Setup Report
Generated: 2025-10-18 02:57:11 UTC

## Environment Configuration
Status: healthy

### Required Variables
- DISCORD_BOT_TOKEN: ✅ Set
- OPENAI_API_KEY: ✅ Set
- QDRANT_URL: ✅ Set

### Optional Variables
- OPENROUTER_API_KEY: ✅ Set
- POSTGRES_URL: ✅ Set
- REDIS_URL: ✅ Set
- MINIO_URL: ✅ Set

## Service Health
Status: unhealthy

- qdrant: unhealthy
  Error: HTTPConnectionPool(host='localhost', port=6333): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7b63efca4090>: Failed to establish a new connection: [Errno 111] Connection refused'))
- postgres: unknown
- redis: unknown
- minio: unhealthy
  Error: HTTPConnectionPool(host='localhost', port=9000): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7b63efca6350>: Failed to establish a new connection: [Errno 111] Connection refused'))

## OAuth Configuration
Status: healthy

- youtube: configured
- twitch: configured
- tiktok: configured
- instagram: configured
- x: configured

## Doctor Check Results
Status: healthy

### Output
.venv/bin/python -m ultimate_discord_intelligence_bot.setup_cli doctor

Doctor
======
✅ ffmpeg: /usr/bin/ffmpeg
✅ yt-dlp: /home/crew/.venv/bin/yt-dlp
✅ Vector store (dummy) reachable: :memory:
✅ Basic env check passed
