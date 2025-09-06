---
title: Agents & Project Structure
origin: migrated_from_root
status: active
last_moved: 2025-09-02
replaces:
  - AGENTS.md
---

## Repository Structure & Agents

This document migrates the content of the former root `AGENTS.md` and aligns it with the new documentation taxonomy.

## Project Structure

- **Source**: `src/` — core app modules under domain subpackages.
- **Tests**: `tests/` (files named `test_*.py`).
- **Docs**: `docs/` (start with `docs/GETTING_STARTED.md` and `docs/setup_cli.md`).
- **Config**: `.env` at repo root; templates: `.env.example`, `.env.production.example`.
- **Data & Tenants**: `data/` and `tenants/<slug>/` for tenant artifacts.

## Build, Test & Development Commands

Prefer Make (delegates to `scripts/dev.sh`):

| Task | Command |
|------|---------|
| Initial setup | `make install` |
| Run tests | `make test` |
| Lint check | `make lint` |
| Format (auto-fix) | `make format` |
| Type check (full) | `make type` |
| Type check (changed) | `make type-changed` |
| Eval (golden) | `make eval` |

For more granular script usage see `docs/dev_assistants.md`.

## Agents Overview (Placeholder)

Detailed agent reference is maintained in `docs/agent_reference.md`.
