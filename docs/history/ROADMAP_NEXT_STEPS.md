# Roadmap & Next Steps (Rolling)

Last updated: 2025-08-31

## 1. Recently Completed Infrastructure Fixes

| Area | Change | Rationale | Status |
|------|--------|-----------|--------|
| Test Env | Forced pytest to use project venv explicitly | Eliminated false missing dependency errors | ✅ |
| Settings | Added `extra="ignore"` to pydantic `Settings` | Prevent explosion when unrelated env vars present | ✅ |
| Qdrant | Made `get_qdrant_client` fetch settings lazily | Monkeypatch-friendly & deterministic dummy fallback | ✅ |
| Archive | Added lazy import proxy in `archive/__init__.py` | Avoid heavy FastAPI import chain in lightweight tests | ✅ |
| Discord Bot | Added graceful discord.py fallback & shim | Tests can import `start_full_bot` without discord dependency | ✅ |
| Targeted Tests | Validated memory + lightweight + command helper tests | Proved foundational layers function correctly | ✅ |

## 2. Outstanding Technical Debt / Refactors

| Priority | Item | Issue | Proposed Action |
|----------|------|------|-----------------|
| High | Oversized `_render_analysis_result` | Excess branches & statements (lint complaints) | Extract sub-render functions |
| High | Oversized `_load_tools` | Large procedural block | Split into composable helpers |
| Medium | Magic numbers in analysis rendering | Length truncations, thresholds | Centralize constants |
| Low | Vector/dummy client coverage | Only basic dummy tests | Add more behavioral tests |

## 3. Testing Strategy Evolution

- Phase 1 (Done): Enable minimal subset under venv.
- Phase 2 (Next): Full suite; capture failure matrix.
- Phase 3: Introduce `@pytest.mark.fullstack`, `@pytest.mark.discord`.
- Phase 4: Parallelize once isolation clarified.

## 4. Proposed Upcoming Work Items

1. Refactor loaders and rendering into helpers.
2. Extract UI constants (done) and expand coverage.
3. Add dummy qdrant tests for recreate/reset.
4. Add shim tests for discord lightweight mode.
5. Document lightweight architecture.

## 5. Risk & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Hidden heavy imports | Slow imports / test flakiness | Medium | Scan for unconditional imports |
| Env drift | Validation errors | Low | Settings guard + explicit modeling |
| Test suite time | Slow feedback | Medium | Split markers & fast path CI |
