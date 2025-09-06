---
title: Repository Guidelines
origin: AGENTS.md (root)
status: migrated
last_moved: 2025-09-02
---

## Overview

Original root file `AGENTS.md` migrated during root cleanup. Provides high‑level contributor workflow, structure, and command references.

## Project Structure & Module Organization

- Source: `src/` — core app in `src/ultimate_discord_intelligence_bot/`; shared modules in `src/core`, `src/discord`, `src/ingest`, `src/analysis`.
- Tests: `tests/` (files named `test_*.py`).
- Docs: `docs/` (start with `docs/GETTING_STARTED.md` and `docs/setup_cli.md`).
- Config: `.env` at repo root; templates in `.env.example` and `src/ultimate_discord_intelligence_bot/config/`.
- Data & tenants: `data/` and `tenants/<slug>/` for tenant-specific artifacts.

## Build, Test, and Development Commands

- `make setup`: Launch setup wizard (`python -m ultimate_discord_intelligence_bot.setup_cli`).
- `make doctor`: Validate environment, binaries, and configuration.
- `make run-discord` / `make run-crew`: Run the Discord bot or the crew locally.
- `make test` (use `-k <pattern>` to filter): Run pytest.
- `make lint` / `make format` / `make type`: Ruff lint/format and mypy type checks.
- `make guards`: Run policy guardrails (HTTP wrappers, yt-dlp usage).
- `make ci-all`: Full local CI; `make eval` (optional) runs the golden eval harness.

## Coding Style & Naming Conventions

- Python 3.10+; 4-space indent; 120-char max line length; prefer double quotes.
- Use type hints for new/changed code; keep functions small and composable.
- Naming: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Networking: never call `requests.*` directly — use `core.http_utils` (`resilient_get`/`resilient_post`, retry helpers).
- Media downloads: use dispatchers/wrappers in `.../tools/*download_tool.py`; no raw `yt_dlp` or shell calls.

## Testing Guidelines

- Framework: pytest; name tests `tests/test_*.py`.
- Mock external network and I/O; isolate side effects.
- Add tests for new behavior and regressions; ensure `make test` passes locally.
- Focused runs: `make test -k "pattern"`.

## Commit & Pull Request Guidelines

- Conventional Commits (e.g., `feat(ingest): add YouTube channel parser`).
- PRs: clear description, linked issues, screenshots/logs for runtime changes, and note any config/deprecation impacts.
- Before opening: run `make format lint type test guards ci-all`; update docs and `.env.example` when config changes.

## Security & Configuration Tips

- Keep secrets in `.env`; never commit secrets. Validate with `make doctor`.
- Follow deprecation guidance in `docs/configuration.md`; do not bypass guard scripts.
- Use `tenants/<slug>/` for tenant data; keep per-tenant config isolated.

---
Generated 2025-09-02
