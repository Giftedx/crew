---
title: Contributing Guide
origin: CONTRIBUTING.md (root)
status: migrated
last_moved: 2025-09-02
---

Thanks for your interest in improving the project! This guide summarizes the local workflow, quality gates, and incremental improvement policies (lint & typing) so changes stay fast and safe.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pre-commit install --install-hooks
./scripts/dev.sh test
```

## Common Commands

| Task | Command |
|------|---------|
| Lint (check) | `./scripts/dev.sh lint` |
| Lint + Format | `./scripts/dev.sh format` |
| Type check (full, non-fatal locally) | `./scripts/dev.sh type` |
| Type check (changed files) | `./scripts/dev.sh type-changed` |
| Mypy baseline check | `./scripts/dev.sh type-baseline` |
| Update mypy baseline (only when improving) | `./scripts/dev.sh type-baseline-update` |
| Tests | `./scripts/dev.sh test` |
| Golden eval (optional) | `./scripts/dev.sh eval` |

## Linting Policy

We use Ruff for lint + (optionally) format. The lint baseline is being improved incrementally. Avoid introducing new E/F class errors; prefer fixing violations you touch.

## Typing Policy

Mypy runs in a moderately strict mode. A baseline error count is tracked in `mypy_baseline.json`. CI should fail if the count increases.

Guidelines:

1. Do not add new `# type: ignore` without a trailing reason comment.
2. Remove an unused ignore if you touch the line.
3. When creating new modules, fully type public function signatures.
4. Prefer TypedDict or dataclasses for structured dict payloads that cross module boundaries.

## Updating the Mypy Baseline

Only update the baseline when the current error count is less than or equal to the existing value (preferably strictly lower):

```bash
./scripts/dev.sh type-baseline-update
```

If you must intentionally raise it (rare), document rationale in the PR description.

## Tests

All tests must pass (`pytest -q`). Add focused tests for new behavior. Keep tests fast; use existing fixtures before creating new heavy ones.

## Feature Flags

Add any new flag to docs (`docs/feature_flags.md`) and ensure a default-off posture unless clearly safe.

## Deprecations

For deprecated modules or functions:

1. Add a clear docstring with planned removal version/date.
2. Emit a `DeprecationWarning` at import or first call (where practical).
3. Remove after at least one minor release cycle or when usage telemetry is zero.

Optional local guard: install the deprecation pre-commit hook to block commits
containing past-deadline or removed symbol references:

```bash
bash scripts/install_deprecation_hook.sh
```

Skip temporarily (e.g., during a multi-step refactor):

```bash
SKIP_DEPRECATION_HOOK=1 git commit -m "refactor: adjust legacy flag usage"
```

## Pull Request Checklist

- [ ] Tests added/updated & passing
- [ ] Lint clean for changed files
- [ ] No increase in mypy error count (baseline check passes)
- [ ] Feature flags documented (if applicable)
- [ ] Docs updated (if behavior or config changed)
- [ ] No stray debug prints / large commented blocks

## Commit Style

Follow Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, etc.

## Security & Privacy

Validate external inputs; never trust user-provided URLs or paths. Reuse existing helpers (see `security/` and `policy/`). Run through privacy filter where user content leaves the system.

## Observability

Emit metrics or traces using existing helpers; avoid ad-hoc prints. Extend enums consistently.

## Packaging Notes

- The internal `src/discord` shim exists to support local tests without the heavy `discord.py` import.
- The shim is excluded from wheels to avoid clashing with the real `discord` package on PyPI. Runtime code should rely on `discord.py`; tests can import the shim from the repository source layout.

## Questions

Open a draft PR early or file an issue describing your approach. Collaboration > large opaque diffs.

Happy hacking!
