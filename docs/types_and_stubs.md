# Type Checking & Stub Guidance

This project uses mypy for gradual typing. A recent snapshot (see `reports/mypy_snapshot.txt`) shows existing technical debt; this guide explains how to reduce it safely.

## Goals

1. Prevent new untyped regressions in core logic.
1. Incrementally reduce legacy errors without blocking feature velocity.
1. Provide a clear policy for handling third‑party libraries lacking stubs.

## Quick Commands

```bash
make type          # Run mypy (non-failing locally)
make lint          # Ruff (import/order + style)
make test          # Pytest
```

## Installing Stubs

Install available type stubs first:

```bash
pip install types-psutil types-jsonschema
```

Run (interactive acceptance suppressed):

```bash
mypy --install-types --non-interactive || true
```

Add any new stub packages to `pyproject.toml` `optional-dependencies[dev]`.

## When Stubs Don’t Exist

For libraries like `whisper`, `faster_whisper`, `transformers`, `yt_dlp`, `crewai`, `vllm`, `gptcache`, create minimal placeholders:

```text
stubs/
  transformers/__init__.pyi
  whisper/__init__.pyi
  ...
```

Inside each `.pyi`, add only the symbols actually imported (keep surface area small). Prefer `Protocol` for callable factories when interfaces are stable.

If you cannot create a stub yet, add a single targeted ignore:

```python
import transformers  # type: ignore[import-not-found]  # TODO: add stub
```

Avoid wide `ignore-errors` at module level unless the file is explicitly quarantined.

## Avoiding Common Error Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| Reassigning imported class/object to `None` | “Cannot assign to a type” | Optional alias: `_DistributedLLMCache: type[DistributedLLMCache] \| None` |
| Redefining cached functions | Incompatible redefinition | Separate pure impl + decorated wrapper: `wrapped = lru_cache(...)(impl)` |
| Divergent subclass method signature | Override error | Match base signature; add adapter wrapper if new params needed |
| Dynamic fallback via reassignment | Obscures types | Encapsulate in a factory returning a `Protocol` instance |

## Introducing New Typed Surfaces

Add TypedDicts or Protocols for structured data boundaries, e.g.:

```python
from typing import TypedDict

class LLMRouteResult(TypedDict, total=False):
    status: str
    cached: bool
    cache_type: str
    model: str
```

Use these for function returns instead of loose `dict[str, Any]`.

## Phased Adoption (Condensed)

1. Stubs & ignores: eliminate import errors.
1. Structural dedup (settings / secure_config).
1. Signature alignment (LearningEngine, middleware).
1. Typed domain objects (cache hits, route results, StepResult serialization).
1. Tighten config: `--warn-unused-ignores`, then selective `--disallow-incomplete-defs`.

## Baseline Strategy

If adopting a strict CI gate, persist a JSON snapshot of error counts and block increases. Only decrease counts after a remediation change. This avoids “big bang” PRs.

### Future CI Gating (Planned)

Proposed incremental enforcement steps (do not enable all at once):

1. Error Count Guard: Script runs `mypy` and parses total errors; fails if count > snapshot.
1. New-File Guard: Any new `.py` file with >0 errors fails regardless of baseline.
1. Unused Ignore Guard: Enable `--warn-unused-ignores` in CI only; require cleanup before merge.
1. Definition Strictness: For selected packages (`core/`, `analysis/`), add `per-module options` with `disallow-incomplete-defs = True` after they reach 0 errors.
1. Full Strict Pilot: Trial `strict = True` in an isolated subpackage (e.g. `core/cache/`) to validate assumptions before broader rollout.

Baseline snapshot workflow (implemented):

```bash
# Guard (fails only if errors increased)
make type-guard

# After intentional reduction (records new lower count)
make type-guard-update
```

First run (no snapshot) will create `reports/mypy_snapshot.json` automatically.

CI usage:

```bash
make ci-type-guard            # (in pipeline) fails if increased
make ci-type-guard ARGS="--json"  # machine readable status
```

JSON mode example output:

```json
{"status": "stable", "baseline_total": 69, "current_total": 69, "delta": 0, "baseline_path": "reports/mypy_snapshot.json"}
```

Advanced JSON + breakdown:

```bash
make type-guard-json               # JSON status only
BREAKDOWN=1 make type-guard-json   # JSON + per top-level package counts
```

Sample breakdown output:

```json
{
  "status": "stable",
  "baseline_total": 69,
  "current_total": 69,
  "delta": 0,
  "baseline_path": "reports/mypy_snapshot.json",
  "breakdown": {"core": 12, "analysis": 8, "memory": 5}
}
```

## py.typed

If any internal package is intended for external reuse, add a `py.typed` file to mark inline types as authoritative.

## Pre-Commit Hook (Optional)

Run mypy only on changed Python files:

```bash
changed=$(git diff --name-only --diff-filter=ACMRT HEAD | grep -E '\\.py$' || true)
if [ -n "$changed" ]; then
  mypy $changed || true
fi
```

## Decision Matrix for New Code

| Situation | Action |
|-----------|--------|
| New core feature | Fully type public functions + return type |
| Experimental / prototype | Allow Any internally; add TODO for typing before GA |
| Third-party dynamic wrapper | Provide minimal Protocol interface |

## FAQ

**Q:** Should we silence every existing error?  \
**A:** No—only isolate low-value legacy areas; prioritize surfaces that propagate into widely used modules.

**Q:** When to add `# type: ignore` vs stub?  \
**A:** Prefer stub if library is stable and used in >1 module; ignore only for transient or soon-to-be-replaced code.

**Q:** How to handle generated code?  \
**A:** Put it in a `generated/` folder and exclude or apply `ignore-errors` there, never in hand-written logic.

---

This guide will evolve as the remediation plan progresses. Update alongside each phase completion.
