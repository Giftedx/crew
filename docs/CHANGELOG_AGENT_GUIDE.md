# Agent Guide Changelog

Chronological record of updates to `.github/copilot-instructions.md` to help AI assistants & reviewers understand deltas affecting automation quality.

## 2025-09-11

- Refreshed architecture landmarks (added time utils, clarified segmentation modules, emphasized single observability init).
- Expanded StepResult contract (explicit metrics-before-return rule; clarified vector search raw output shape).
- Tightened tenancy guidance (no raw user text/URLs in metric labels or namespaces).
- Clarified feature flag + deprecation workflow (run `make docs` after touching deprecated surfaces; align with README replacements table).
- Added routing & RL flow phrasing (capability/cost filter + ε-greedy explore wording).
- Strengthened scheduler notes (do not rename existing metric labels; deterministic key format).
- Consolidated determinism/time guidance (hash URLs, guard experimental paths with flags).
- Rewrote HTTP & caching section to forbid direct `requests` usage and centralize retry YAML precedence.
- Observability: no `print` for runtime signaling; single-span rule reiterated.
- Memory layer: clarified archiver facade usage and retention/prune responsibilities.
- Testing & CI: enumerated bootstrap variants (`uv-bootstrap`), type guard snapshot discipline, compliance tasks (`make compliance[-fix]`).
- Added Gotchas & Migration Patterns (flags not set, LearningEngine deprecation, StepResult migration script, retry precedence order, mypy snapshot discipline, vector namespace composition, grounding citation monotonicity) with cross-file references.
- Added Discord & crew run commands plus quick ingest concurrency flag example.

## Format Philosophy

- Keep core guide ~50 lines; move rationale & history here.
- Each changelog bullet should enable safe diff comprehension for future automation tuning.
