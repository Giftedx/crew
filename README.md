# Giftedx Crew

A tenant-aware Discord platform that ingests public media, builds grounded context, and answers questions through cost-guarded model routing and reinforcement learning.

## 📚 Documentation

**📖 [Complete Documentation Index](docs/ROOT_DOCS_INDEX.md)**

All detailed guides, architecture docs, and operational procedures have been organized under `docs/`. Use the documentation index above to find what you need.

**🚀 [Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md)** - Quick-start guide for new developers

## 🚀 Quick Start

[![CI (MCP)](https://github.com/Giftedx/crew/actions/workflows/ci-mcp.yml/badge.svg)](https://github.com/Giftedx/crew/actions/workflows/ci-mcp.yml)

1. **Install dependencies:**

   ```bash
   pip install -e '.[dev]'
   ```

   (Quote the extras in zsh to avoid glob expansion: without quotes zsh treats `[dev]` as a character class.)

1. **Run setup wizard:**

   ```bash
   python -m ultimate_discord_intelligence_bot.setup_cli
   ```

1. **Start the bot:**

   ```bash
   python -m ultimate_discord_intelligence_bot.setup_cli run discord
   ```

### Discord run tips

- Ensure `DISCORD_BOT_TOKEN` is set in your environment or `.env` before starting. The startup wizard will validate and fail fast if missing.
- For notifications, set `DISCORD_WEBHOOK` (and optionally `DISCORD_PRIVATE_WEBHOOK`); these names must match exactly (no `_URL` suffix).
- After first run, slash commands may take up to a minute to propagate globally; on dev servers they usually appear immediately.
- If you don’t see commands, confirm the bot has the following intents enabled in the Developer Portal: Message Content and Server Members.
- zsh tip: always quote extras during install, e.g., `pip install -e '.[dev]'`.

### Optional Extras

Install additional capability sets by combining extras (always quote in zsh):

```bash
# Development + metrics (Prometheus client)
pip install -e '.[dev,metrics]'

# Development + whisper reference model (may require Python 3.11 if numba/llvmlite issues on 3.12)
pip install -e '.[dev,whisper]'

# Development + vLLM local inference (GPU recommended)
pip install -e '.[dev,vllm]'

# Everything
pip install -e '.[dev,metrics,whisper,vllm]'
```

Notes:

- `whisper` extra adds `openai-whisper`; the project already includes `faster-whisper` by default.
- If `openai-whisper` fails to build on Python 3.12, create a Python 3.11 virtualenv for that extra.
- `vllm` pulls in large GPU-oriented dependencies (`torch`, `triton`, `xformers`); use only if you plan local model serving.
- You can layer extras after the initial install (e.g., `pip install '.[metrics]'`).

### MCP server (optional)

See `docs/mcp.md` for the full guide. Quickstart:

- Install extras: `pip install -e '.[mcp]'`
- Run stdio server: `crew_mcp` (works with Claude Desktop)
- Makefile helpers:
  - `make run-mcp` — run stdio server honoring env flags
  - `make test-mcp` — run MCP tests if `fastmcp` is installed; otherwise skip

Enable optional servers via env flags before launch, e.g.:

```bash
export ENABLE_MCP_MEMORY=1 ENABLE_MCP_ROUTER=1 ENABLE_MCP_OBS=1 ENABLE_MCP_KG=1 ENABLE_MCP_INGEST=1 ENABLE_MCP_HTTP=1 ENABLE_MCP_A2A=1
export MCP_HTTP_ALLOWLIST="api.github.com,raw.githubusercontent.com"
crew_mcp
```

#### Use MCP tools inside Crew (no transport)

Set `ENABLE_MCP_CALL_TOOL=1` to inject an in-process tool that calls MCP module functions directly from Crew agents.

Example (pseudocode):

```python
from ultimate_discord_intelligence_bot.tools.mcp_call_tool import MCPCallTool

tool = MCPCallTool()
res = tool.run("http", "http_json_get", {"url": "https://example.com/data.json"})
if res.success:
   print(res.data["result"])  # dict
```

## 🛠️ Development

```bash
make test     # Run tests
make lint     # Check code style
make format   # Auto-fix formatting
make type     # Type checking
make types-install  # Install common and suggested stub packages
make type-guard     # Fail if mypy errors increase vs snapshot
make type-guard-update  # Update snapshot after reducing errors
make ci-type-guard  # CI variant (use in pipeline), supports --json via ARGS
make type-guard-json  # Emit JSON (BREAKDOWN=1 for per-package counts)
```

### Testing tips

Fast sweep (subset):

- `make test-fast`

Fast sweep with clean env (avoids retry-precedence flakiness if `RETRY_MAX_ATTEMPTS` is set in your shell):

- `make test-fast-clean-env`

Notes:

- `.env` edits do not override variables already exported in your shell. If a value like `RETRY_MAX_ATTEMPTS` was exported earlier, tests that verify precedence may fail unexpectedly. Either use the clean-env target above or temporarily unset it for the test process.

See also: [Type Checking & Stub Guidance](docs/types_and_stubs.md) for the phased mypy remediation and stub strategy.

Optional Git hook:

```bash
ln -s ../../scripts/git_hooks/pre-push .git/hooks/pre-push  # adds type regression guard
```

### A2A JSON-RPC Quickstart

Expose the A2A adapter and call it locally:

- Set environment (in shell or `.env`):
  - `ENABLE_A2A_API=1`
  - Optional: `ENABLE_A2A_API_KEY=1` and `A2A_API_KEY="key1,key2"`
  - Optional tenancy: `A2A_TENANT_ID` and `A2A_WORKSPACE_ID`
- Start your API service (as in your usual run flow).
- Run the Python client demo:

```bash
make run-a2a-client-demo
```

- Run A2A-focused tests only:

```bash
make test-a2a
```

This target also validates the Postman/Insomnia collections JSON and required variables.

- Collections:
  - Postman: `docs/a2a_postman_collection.json`
  - Insomnia: `docs/a2a_insomnia_collection.json`
  - Configure variables: `A2A_BASE_URL`, `A2A_API_KEY` (if auth enabled), `A2A_TENANT_ID`, `A2A_WORKSPACE_ID` (optional)
  - Includes a ready-made "JSON-RPC: batch (auth)" example that uses optional API key and tenancy headers

### Activities local dev quick-start

Developing the example Activity (`examples/activities/hello-activity`)? Enable CORS and optional echo endpoint in the API for smooth local testing:

```bash
# in repo root (zsh compatible)
export ENABLE_CORS=1
export CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
export ENABLE_ACTIVITIES_ECHO=1  # optional: enables GET /activities/echo
```

Notes:

- Activities endpoints (`/activities/*`) are intentionally excluded from the API response cache for real-time behavior.
- The Hello Activity pings `/activities/health` on load and has a button to call `/activities/echo?q=ping` when echo is enabled.
- You can toggle these via the setup wizard too: `make setup`.

## 📁 Key Features

## � Optimization & Caching Enhancements

The platform includes advanced layers to control cost and latency:

These work alongside adaptive retrieval (dynamic k) and reinforcement learning–driven routing to minimize unnecessary token usage while preserving answer quality.

- [Getting Started Guide](docs/GETTING_STARTED.md)
- [Configuration Reference](docs/configuration.md)
- [Contributing Guidelines](docs/operations/CONTRIBUTING.md)
- [Security & Secrets](docs/security/SECURITY_SECRETS.md)
- [Architecture Overview](docs/architecture/architecture.md)

---

*For detailed documentation on any topic, see the [Documentation Index](docs/ROOT_DOCS_INDEX.md)*

## 🧠 Local Model Inference (Single 8GB GPU)

If you want to run local open models (Llama 3.1 8B, Qwen2.5 7B, Phi-3.5 Mini, etc.) on a constrained 8GB GPU:

1. Point Hugging Face caches to a larger mounted volume (edit `.env` or copy from `.env.example`):

   ```bash
   HF_HOME=/mnt/f/hf_cache
   TRANSFORMERS_CACHE=/mnt/f/hf_cache/transformers
   HF_DATASETS_CACHE=/mnt/f/hf_cache/datasets
   ```

1. Install vLLM extra (after base editable install):

   ```bash
   pip install -e '.[vllm]'
   ```

1. Download desired models (all or subset):

   ```bash
   ./scripts/download_models.sh all
   ```

1. Switch active model (exports `VLLM_MODEL_ID` for current shell):

   ```bash
   eval "$(python scripts/model_switcher.py --set primary)"
   ```

See: `docs/local_model_selection.md` for detailed rationale, VRAM strategies, and troubleshooting.

<!-- DEPRECATIONS:START -->
**Deprecations:** 2 active (<= 120 days window highlighted)  \
        Generated via `scripts/update_deprecation_badge.py`.

| Name | Stage | Remove After | Days Left | Occurrences | Violation | Replacement |
|------|-------|--------------|-----------|-------------|-----------|-------------|
| `ENABLE_ANALYSIS_HTTP_RETRY` | deprecated | 2025-12-31 | 101 | 1 | ✅ | ENABLE_HTTP_RETRY |
| `services.learning_engine.LearningEngine` | deprecated | 2025-12-31 | 101 | 28 | ✅ | core.learning_engine.LearningEngine |
<!-- DEPRECATIONS:END -->

## ▶️ Run on Replit

This repo includes minimal Replit configuration to run the FastAPI service and optionally the MCP server.

- Press Run to install dependencies and start the API at your Replit app URL.
- The API factory is `server.app:create_app`.
- Metrics endpoint is exposed at `/metrics` when enabled.

Optional: start the MCP server over HTTP on port 8001 in the Replit shell:

```bash
python -c 'from mcp_server.server import mcp; mcp.run(transport="http", host="0.0.0.0", port=8001, path="/mcp")'
```

For stdio-based MCP (e.g., for Claude Desktop), run locally and use the `crew_mcp` entrypoint after installing the `mcp` extra:

```bash
pip install -e '.[mcp]'
crew_mcp
```
