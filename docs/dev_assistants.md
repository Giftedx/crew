---
title: Developer Assistant Guidance
origin: root_consolidation
status: active
last_moved: 2025-09-02
replaces:
  - docs/dev_assistants/CLAUDE.md
  - docs/dev_assistants/GEMINI.md
related:
  - docs/conventions.md
---

## Developer Assistant Guidance

This consolidated guide replaces the former `docs/dev_assistants/CLAUDE.md` and `docs/dev_assistants/GEMINI.md` files. It provides context and guard‑rails for any AI/code assistant operating on this repository.

## Project Overview (Unified)

Ultimate Discord Intelligence Bot (aka Giftedx Crew) is a tenant‑aware Discord intelligence and ingestion platform. It ingests public media, applies grounded analysis, and serves answers through cost‑guarded model routing with reliability, provenance and privacy controls.

## Core Principles for Automated Changes

1. Minimize Root Clutter – prefer adding/altering files under `src/`, `docs/`, or `scripts/`.
1. Respect Incremental Quality Gates – keep Ruff, mypy, and pytest green; only relax via per‑file ignores with justification.
1. Preserve Feature Flags – never remove or repurpose an existing flag without deprecation metadata.
1. Immutable History Docs – files under `docs/history/` are archival; append, do not rewrite.
1. Deterministic Dependencies – modify `pyproject.toml` first, then regenerate `requirements.lock` (authoritative) via `uv` process.

## Common Development Commands

Use the Make targets (delegating to `scripts/dev.sh`):

| Task | Make | Direct Script |
|------|------|---------------|
| Install deps | `make install` | `scripts/dev.sh install` |
| Lint (check) | `make lint` | `scripts/dev.sh lint` |
| Format (fix) | `make format` | `scripts/dev.sh format` |
| Type (full) | `make type` | `scripts/dev.sh type` |
| Type (changed) | `make type-changed` | `scripts/dev.sh type-changed` |
| Tests | `make test` | `scripts/dev.sh test` |
| Eval (golden) | `make eval` | `scripts/dev.sh eval` |
| Hooks setup | `make hooks` | `scripts/dev.sh hooks` |

## When Adding New Docs

Add YAML front matter:

```yaml
---
title: Descriptive Title
origin: new
status: draft # or active / deprecated / historical
last_moved: 2025-09-02
related:
  - docs/architecture/architecture.md
---
```

## AI Assistant Boundaries

Do NOT:

- Commit secrets or sample real tokens – use obvious placeholders.
- Delete historical docs in `docs/history/`.
- Introduce new top‑level directories without rationale.

Prefer to:

- Refactor large modules into focused tools.
- Add tests alongside new behavior.
- Update docs and changelog for user‑visible changes.

## Deprecation Lifecycle

1. Mark doc/code as deprecated (front matter `status: deprecated`).
1. Provide replacement path via `replaces` / `supersedes` fields.
1. After grace period, move file to `docs/history/` with status `historical`.

## References

- `docs/conventions.md` – overarching repository conventions.
- `docs/security/README.md` – security posture & secret handling.
- `docs/architecture/` – architectural overviews & sync reports.

## MCP (Model Context Protocol) usage with assistants

This repo provides an optional FastMCP server that exposes safe tools (memory/router/obs/kg/ingest/http/a2a). See `docs/mcp.md` for details.

### Claude Desktop configuration

Add to `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "crew": { "command": "crew_mcp" }
  }
}
```

Then launch the stdio server locally (after installing extras):

```bash
pip install -e '.[mcp]'
crew_mcp
```

Enable servers via env flags before launch, e.g.:

```bash
export ENABLE_MCP_MEMORY=1 ENABLE_MCP_ROUTER=1 ENABLE_MCP_OBS=1 ENABLE_MCP_KG=1 ENABLE_MCP_INGEST=1 ENABLE_MCP_HTTP=1 ENABLE_MCP_A2A=1
export MCP_HTTP_ALLOWLIST="api.github.com,raw.githubusercontent.com"
crew_mcp
```

### Using MCP tools inside Crew (no transport)

Set `ENABLE_MCP_CALL_TOOL=1` to inject an in-process tool that calls MCP module functions directly. See `src/ultimate_discord_intelligence_bot/tools/mcp_call_tool.py` and usage examples in `docs/mcp.md`.

---
_This file supersedes `docs/dev_assistants/CLAUDE.md` and `docs/dev_assistants/GEMINI.md` (moved from the repository root to reduce clutter)._
