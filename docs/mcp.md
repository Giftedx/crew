# FastMCP server (optional)

This repository now includes an optional Model Context Protocol (MCP) server powered by FastMCP.

What you get (modular, feature-flagged):

- Core tools: `health_check()`, `echo(message, uppercase=False)`, `get_config_flag(name, default=None)`
- Core resource: `settings://service_name`
- Optional servers (enable with env flags):
  - memory (ENABLE_MCP_MEMORY=1): vector search/list/sample
  - router (ENABLE_MCP_ROUTER=1): cost estimates and advisory routing
  - obs (ENABLE_MCP_OBS=1): health/counters; full metrics resource gated by ENABLE_MCP_OBS_PROM_RESOURCE=1
  - kg (ENABLE_MCP_KG=1): KG subgraph/timeline; policy and grounding resources
  - ingest (ENABLE_MCP_INGEST=1): safe YouTube/Twitch metadata, local transcript
  - http (ENABLE_MCP_HTTP=1): allowlisted HTTPS GET with optional cache (set MCP_HTTP_ALLOWLIST)
  - a2a (ENABLE_MCP_A2A=1): bridge to selected A2A tools (`tools.*`) via a single `a2a_call` tool

## Install

Use the optional dependency group:

```bash
# using uv (recommended)
uv pip install .[mcp]

# or with pip
pip install ".[mcp]"
```

## Run locally

- Stdio (works with Claude Desktop):

```bash
crew_mcp
```

- HTTP transport (optional):

```bash
python -c 'from mcp_server.server import mcp; mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")'
```

Alternatively, use Makefile helpers:

```bash
# stdio transport (honors env flags)
make run-mcp

# run only MCP tests when fastmcp is installed
make test-mcp
```

## Configure MCP client

Example `~/.claude/config.json` snippet:

```json
{
  "mcpServers": {
    "crew": { "command": "crew_mcp" }
  }
}
```

Gemini / GitHub MCP actions already exist in `.github/workflows/*` with examples of `mcpServers` usage.

## Notes

- The server name is derived from `core.settings.Settings.service_name` when available.
- Import safety: If the FastMCP extra is not installed, MCP modules still import successfully. They expose a lightweight
  stub object with `.tool`/`.resource` decorators so other frameworks/scaffolds don’t crash. Attempting to run a stub
  server raises a clear error instructing to install `.[mcp]`.
- Enable optional servers with environment variables before launching, for example:

```bash
ENABLE_MCP_MEMORY=1 ENABLE_MCP_ROUTER=1 ENABLE_MCP_OBS=1 ENABLE_MCP_KG=1 ENABLE_MCP_INGEST=1 ENABLE_MCP_HTTP=1 \
ENABLE_MCP_A2A=1 \
MCP_HTTP_ALLOWLIST="api.github.com,raw.githubusercontent.com" \
crew_mcp
```

- Extend by adding new modules under `src/mcp_server/` and mounting them in `src/mcp_server/server.py` behind feature flags.

## MCP tools quick reference

| Server (flag) | Tools | Resources |
| --- | --- | --- |
| core (always) | health_check, echo, get_config_flag | settings://service_name |
| memory (ENABLE_MCP_MEMORY) | vs_search, vs_list_namespaces, vs_samples | memory://<ns>/stats |
| router (ENABLE_MCP_ROUTER) | estimate_cost, route_completion, choose_embedding_model | — |
| obs (ENABLE_MCP_OBS) | summarize_health, get_counters, recent_degradations | metrics://prom (if ENABLE_MCP_OBS_PROM_RESOURCE); degradations://recent |
| kg (ENABLE_MCP_KG) | kg_query, kg_timeline, policy_keys | policy://{key}, grounding://profiles |
| ingest (ENABLE_MCP_INGEST) | extract_metadata, list_channel_videos, fetch_transcript_local, summarize_subtitles | ingest://providers |
| http (ENABLE_MCP_HTTP) | http_get, http_json_get | httpcfg://allowlist, httpcfg://example-header |
| a2a (ENABLE_MCP_A2A) | a2a_call | a2a://skills, a2a://skills_full |

Tip: To discover resources in a client, request them by URI (many return JSON-like text).

### A2A Bridge quick usage

When `ENABLE_MCP_A2A=1` is set, the A2A Bridge mounts under the `a2a` prefix and exposes:

- Tool: `a2a_call(method, params)` — only `tools.*` methods are permitted.
- Resources: `a2a://skills` (names), `a2a://skills_full` (with schemas when available).

Example call via an MCP client:

```json
tool: a2a.a2a_call
params: {"method": "tools.text_analyze", "params": {"text": "hello world"}}
```

### Using MCP tools inside Crew (no transport)

You can call the same MCP server tools directly from Crew agents using a lightweight bridge tool that imports the MCP modules in-process.

- Flag: set `ENABLE_MCP_CALL_TOOL=1` to inject an "MCP Call Tool" into all agents.
- Location: `src/ultimate_discord_intelligence_bot/tools/mcp_call_tool.py`
- Contract:
  - Inputs: `namespace` (e.g., "http"), `name` (e.g., "http_json_get"), `params` (dict)
  - Output: StepResult.ok with `result` payload (dict), or StepResult.fail with error message

Example Crew usage (pseudocode):

```python
tool = MCPCallTool()
res = tool.run("http", "http_json_get", {"url": "https://example.com/data.json"})
assert res.ok and "result" in res
```

Security: only a curated allowlist per namespace is exposed; adding new functions requires changing the registry in `mcp_call_tool.py`.

## CI smoke test

A lightweight GitHub Actions workflow runs on push/PR to ensure all MCP modules remain import-safe across Python versions (3.10–3.13) without installing optional extras:

- Location: `.github/workflows/mcp-smoke.yml`
- What it does: installs only `pytest`, sets `PYTHONPATH=src`, and runs `tests/test_mcp_imports.py`.

Run locally:

```bash
make test-mcp-smoke
```

If you add a new MCP module under `src/mcp_server/`, update `tests/test_mcp_imports.py` to include it so the smoke test guards against regressions.
