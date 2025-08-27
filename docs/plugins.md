# Plugin Architecture

This repository supports sandboxed plugins that can extend the system on a per-tenant basis.  Each plugin ships with a
`manifest.json` describing its capabilities, permissions, resource limits, and entrypoint.  Manifests are validated
against [`manifest.schema.json`](../src/ultimate_discord_intelligence_bot/plugins/manifest.schema.json).

Plugins are executed through the `PluginExecutor` which spawns the entrypoint in a separate process and injects a set of
**service adapters** (e.g. `svc_llm`, `svc_memory`).  The executor enforces basic permission checks and timeouts so that
plugins cannot exceed their granted capabilities.

See `plugins/example_summarizer` for a minimal example.

## Capability Tests

Every plugin must define a `tests` block in its `manifest.json` describing a self‑test entrypoint and a set of capability
scenarios.  The lightweight test runner located in `plugins/testkit` executes these scenarios with stubbed adapters and
verifies expectations such as required substrings via helpers like `must_include`, `forbidden`, or `status_ok`.  Developers can run

```bash
python -m ultimate_discord_intelligence_bot.plugins.testkit.cli --plugin ultimate_discord_intelligence_bot.plugins.example_summarizer
```

to verify a plugin before publishing or installing it.
