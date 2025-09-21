# Mypy Remediation Plan

## Snapshot

See `reports/mypy_snapshot.txt` for the full current output (69 errors / 27 files).

## Categorized Issues

| Category | Approx Count | Representative Examples |
|----------|--------------|-------------------------|
| Missing / Unstubbed Third-Party Imports | ~20 | `transformers`, `whisper`, `faster_whisper`, `gptcache`, `crewai`, `vllm`, `yt_dlp`, `nltk`, `instructor`, `faiss` |
| Missing Stubs but Available (`types-*`) | ~5 | `psutil`, `jsonschema` |
| Redefinition / Duplicate Symbols | 6 | `core/secure_config.py` (`BaseSettings`, `AliasChoices`), repeated wrappers shadowing cached functions |
| Incompatible Overrides / Signatures | 4 | `learning_engine.recommend`, middleware `dispatch` signatures |
| Assignment to Type / Module Objects | 10 | `openrouter_service.py` assigning `None` to imported class names; cache modules assigning to lru-wrapped callables |
| Incompatible Redefinition of Cached Functions | 5 | `prompt_engine.py`, `vector_store.py`, `openrouter_service.py` |
| Argument Type Mismatch | 1 | `debate_command_tool.py` passing `StepResult` where dict expected |
| LSP Violations (middleware) | 1 | `server/rate_limit.py` dispatch override incompatibility (still reported despite lint fix) |
| Untyped Dynamic Patterns | 6 | Tenancy helpers, HTTP utils conditional redefinitions |
| Misc (Return/value assignment mismatch) | 11 | Various `assignment` category errors in snapshot tail |

## Phased Remediation

### Phase 0: Environment & Stubs (Fast Wins)

- Install available stub packages: `types-psutil`, `types-jsonschema`.
- Add a short script/Make target: `make types-install` running `mypy --install-types --non-interactive || true`.
- For libraries lacking stubs, create `stubs/` shim package with minimal `.pyi` or add `# type: ignore[import-not-found]` plus TODO tag.

### Phase 1: Structural Hygiene

- Deduplicate symbol declarations in `core/secure_config.py` & `core/settings.py` (single source of BaseSettings / AliasChoices logic).
- Introduce internal helper modules for dynamic import fallbacks instead of redefining names in-place.
- Replace direct reassignment of imported class names with alternative sentinel variables (e.g., `_DistributedLLMCache: type[DistributedLLMCache] | None`).

### Phase 2: Interface Alignment

- Conform `ultimate_discord_intelligence_bot/services/learning_engine.py` recommend signature to base `LearningEngine` (see also `src/core/learning_engine.py`) or provide adapter wrapper.
- Normalize middleware `dispatch` signature to match Starlette exactly (return type `Response` or `StreamingResponse`).
- Encapsulate dynamic monkeypatch fallback logic into small functions returning typed Protocol instances.

### Phase 3: Domain Typing Enhancements

- Introduce TypedDict / Protocols:
  - `SemanticCacheHit` / `SemanticCacheResponse`.
  - `LLMRouteResult` for OpenRouter output.
  - `StepResultDict` for serialization boundary.
- Add `py.typed` file for any distributable internal packages.

### Phase 4: Safe Refactors & Baseline Tightening

- Refactor cached function wrappers: separate pure function from decorated alias to avoid redefinition errors.
- Replace assignments to lru-wrapped functions with wrapper factory patterns.
- After each sub-phase, re-run mypy and update a shrinking baseline; fail CI on new regressions.

### Phase 5: Optional Strictness

- Enable `--disallow-incomplete-defs` and `--warn-redundant-casts` gradually per module.
- Turn on `--no-implicit-reexport` for `core/` once duplicates removed.

## Prioritized Ticket Breakdown

| Ticket | Scope | Effort | Risk | Outcome |
|--------|-------|--------|------|---------|
| T1 | Stub installation & ignores | XS | Low | Immediate error count drop (~25%) |
| T2 | Secure config dedup | S | Med | Eliminates redefinition noise |
| T3 | LearningEngine signature alignment | S | Low | Removes override error, clarifies API |
| T4 | Middleware dispatch typing | XS | Low | Removes LSP violation |
| T5 | Cached function refactor (prompt/vector/openrouter) | M | Med | Reduces misc redefinition & assignment errors |
| T6 | TypedDict introduction for cache & results | M | Low | Improves downstream reliability |
| T7 | Baseline tightening & CI gate | S | Low | Prevents regression |

## Suggested CI Additions

- New make target: `make type-ci` running mypy with `--warn-unused-ignores`.
- Enforce no increase in total error count (persist last snapshot number in `reports/mypy_snapshot.txt`).

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Over-correction breaking dynamic fallback | Introduce thin adapter functions, keep original names exporting typed wrappers |
| Stub drift (3rd-party updates) | Nightly `mypy --install-types` in optional job; pin stub versions in lockfile |
| Developer friction | Provide quick-start doc section (Phase 0) plus pre-commit hook for touched modules only |

## Immediate Next Steps (if approved)

1. Implement T1 & T4 together (fastest cleanup).
1. Open parallel PR for T2 (isolated refactor) while T3 branch adjusts LearningEngine.
1. After merge, regenerate snapshot and recalc categories.

## Exit Criteria

- Error count reduced by ≥50% after Phases 0–2.
- No override/redefinition errors remain after Phase 3.
- CI blocks newly introduced untyped imports.

---

Generated automatically; adjust counts if snapshot changes before remediation starts.
