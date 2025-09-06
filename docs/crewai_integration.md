# CrewAI Integration Overview

This document explains how the repository integrates the CrewAI framework, the safeguards/flags we added, and how to extend or validate the setup. It complements the upstream CrewAI docs (see <https://docs.crewai.com>) and our internal conventions in `docs/conventions.md`.

## Goals

- Strong typing + early validation of YAML driven agents & tasks
- Environment‑driven configurability for the embedder
- Enhanced step‑level observability with optional raw output capture
- Low risk, backward compatible changes guarded by flags

## Key Components

- `src/ultimate_discord_intelligence_bot/crew.py`: Declarative assembly of agents/tasks → `Crew`.
- `src/ultimate_discord_intelligence_bot/config/agents.yaml` & `tasks.yaml`: Primary configuration sources (role, goal, backstory, reasoning, context, output destinations, etc.).
- `src/ultimate_discord_intelligence_bot/config_types.py`: `TypedDict` schemas (`AgentConfig`, `TaskConfig`) that mirror modern CrewAI YAML fields and give static analyzers (mypy/Pylance) precise shapes.
- `src/ultimate_discord_intelligence_bot/tools/_base.py`: Protocol shim for tools ensuring `name`, `description`, and `run()` are type‑checked even without importing heavy vendor classes at analysis time.

## Environment Flags

| Flag | Purpose | Default | Effect |
|------|---------|---------|--------|
| `ENABLE_CREW_CONFIG_VALIDATION` | Enforce structural + type validation of agent & task configs at crew construction | off | Raises `ValueError` on missing required fields or wrong types |
| `CREW_EMBEDDER_PROVIDER` | Override default embedder provider name | `openai` | Sets `crew.embedder['provider']` |
| `CREW_EMBEDDER_CONFIG_JSON` | Inject structured embedder config (merged) | none | Merges dict values into embedder config (e.g. `{ "config": {"dimension": 1024}}`) |
| `ENABLE_CREW_STEP_VERBOSE` | Emit truncated underlying raw step output | off | Prints `raw:` snippet (length capped) for each tool/think step |

### Example

```bash
export ENABLE_CREW_CONFIG_VALIDATION=1
export CREW_EMBEDDER_PROVIDER=vectorx
export CREW_EMBEDDER_CONFIG_JSON='{"config": {"api_key": "xyz", "dimension": 1536}}'
export ENABLE_CREW_STEP_VERBOSE=1
```

## Validation Logic

Located in `_validate_configs()` inside `crew.py` and executed only when `ENABLE_CREW_CONFIG_VALIDATION=1`.

Checks:

- Agents: required keys `{role, goal, backstory, allow_delegation, verbose, reasoning, inject_date, date_format}` and boolean/string type sanity.
- Tasks: each task must reference a defined agent; if `output_file` present ensures directory path exists (creates parent directories best‑effort).

This keeps runtime resilient (no validation by default) but offers a pre‑flight safety net in CI or controlled environments.

## Embedder Configuration

CrewAI initializes agent knowledge using `crew.embedder` during kickoff (per vendor docs). We expose a simple merge pattern:

1. Base: `{ "provider": <CREW_EMBEDDER_PROVIDER or 'openai'> }`
1. If `CREW_EMBEDDER_CONFIG_JSON` parses to a dict, update the base (shallow). This lets you attach provider‑specific nested keys like credentials, dimensions, batching hints.

## Step Observability

`_log_step(step)` uses duck typing (`_StepLike` Protocol) to avoid tight coupling. If `ENABLE_CREW_STEP_VERBOSE=1` and a `raw` attribute (or nested `output.raw`) is found, it prints a single line snippet truncated to `RAW_SNIPPET_MAX_LEN` (160 chars default) preventing terminal flood.

Sample output:

```text
🤖 Agent content_manager using PipelineTool
   ↳ raw: Summarized chunk 1 ...
🤖 Agent enhanced_fact_checker thinking...
```

## Typing Enhancements

- `AgentConfig` / `TaskConfig` provide shaped dictionaries for `agents_config` and `tasks_config` attributes installed by `@CrewBase` decorator.
- `list[BaseAgent]` annotation on `agents` to satisfy CrewAI’s internal expectation (avoids invariance complaints vs concrete `Agent`).
- `# type: ignore[call-arg]` on `Agent` / `Task` calls passing `config=` since runtime builder expands the config at object construction; static types do not model this factory pattern yet.

## Tests

File: `tests/test_crewai_enhancements.py`

| Test | Intent |
|------|--------|
| `test_validation_flag_detects_missing_field` | Ensures missing required agent field triggers `ValueError` when validation flag enabled |
| `test_embedder_env_override` | Verifies provider + merged JSON config populates `crew.embedder` |
| `test_verbose_step_logging_truncation` | Confirms raw step output is printed & truncated |

If `crewai` is not installed these tests are skipped (using `pytest.importorskip`). This keeps the broader suite functional in minimal environments.

## Extensibility Hooks (Future)

Possible low‑risk additions mirroring upstream features:

- Forward `max_reasoning_attempts` when present in YAML.
- Implement `@before_kickoff` / `@after_kickoff` hooks for input/result post‑processing.
- Add a feature flag for hierarchical process if managerial agent emerges.

## Operational Guidance

- For CI/regression safety run with validation enabled: `ENABLE_CREW_CONFIG_VALIDATION=1 pytest -q`.
- To diagnose step anomalies set `ENABLE_CREW_STEP_VERBOSE=1` (avoid in high‑volume production logs).
- Provide secret embedder fields via `CREW_EMBEDDER_CONFIG_JSON` (ensure secrets redaction in logs—current code never prints embedder dict).

## Alignment with Vendor Docs

- Decorator pattern (`@CrewBase`, `@agent`, `@task`, `@crew`) matches canonical examples.
- Config‑driven Agent/Task instantiation via `config=` consistent with quickstart patterns.
- Use of `process=Process.sequential` and `verbose=True`, plus memory/cache/planning flags aligns with modern feature set in documentation.
- Embedder merge matches knowledge initialization snippet (agents call `agent.set_knowledge(crew_embedder=...)` during kickoff — we just pre‑shape that dict).

## Troubleshooting

| Symptom | Cause | Action |
|---------|-------|--------|
| ValueError about missing agent fields | Validation flag on & YAML drift | Add missing keys to YAML or disable flag temporarily |
| Embedder dict empty | No env vars provided | Set `CREW_EMBEDDER_PROVIDER` or JSON override |
| Step raw not showing | Flag off or no raw attribute in object | Enable flag / confirm underlying object exposes `raw` |
| Type checker call-arg errors | Intentional due to dynamic config expansion | Retain `# type: ignore[call-arg]` comments |

## FAQ

**Why not always enforce validation?** – To keep local experimentation frictionless; misconfigurations are rare and caught in CI when the flag is enabled.

**Why shallow merge for embedder config?** – Simplicity; deep merge was unnecessary for current keys. Can extend if nested structures proliferate.

**Why Protocol + duck typing for step logging?** – Avoids importing internal CrewAI classes (stability & speed) and keeps compatibility if upstream refactors step structures.

---
Maintainers: Update this document when adding new flags, altering required config fields, or integrating hierarchical processes.
