# Test Migration Guide

## Current State

- 620 test files in mixed legacy structure
- Imports use old paths (migrated in Phase 1)
- Tests may fail due to moved modules
- Test structure ready: unit/platform/, unit/domains/, integration/, e2e/

## Migration Plan

### Phase 1: Import Updates (COMPLETED)

All source imports have been migrated to new structure:
- `ultimate_discord_intelligence_bot.step_result` → `platform.core.step_result`
- `ultimate_discord_intelligence_bot.services.*` → `platform.*` or `domains.*`
- `core.*` → `platform.core.*`
- `obs.*` → `platform.observability.*`
- `src.ai.*` → `platform.rl.*`

### Phase 2: Test File Migration (DEFERRED)

**Strategy**: Update test imports using same AST tool, then move files to mirror src/ structure

**Execution Steps**:

1. **Update test imports**:
   ```bash
   python scripts/migrate_imports.py tests/ --execute
   ```

2. **Move unit tests** to mirror src/ structure:
   - `tests/unit/platform/http/` ← `tests/unit/core/` (HTTP tests)
   - `tests/unit/platform/llm/` ← `tests/unit/ai/` (LLM tests)
   - `tests/unit/domains/intelligence/` ← `tests/unit/tools/verification/` (verification tests)
   - Continue mapping for all test directories

3. **Integration tests**: Keep in `tests/integration/`, update imports only

4. **E2E tests**: Keep in `tests/e2e/`, update imports only

### Phase 3: Test Execution Priority

**Critical Path** (fix first):
1. Platform core tests (StepResult, HTTP, cache)
2. Domain intelligence tests (analysis, verification tools)
3. Memory system tests (vector store, embeddings)
4. Orchestration tests (crew, agents)

**Low Priority**:
- Archive tests (already moved to `.archive/`)
- Legacy test stubs
- Deprecated feature tests

### Known Issues

**Import Conflicts**:
- `platform` module shadows Python stdlib `platform`
- Solution: Use explicit imports or `from import` syntax
- Example: `from platform.core.step_result import StepResult` (not `import platform`)

**Missing Imports**:
- Some tests may fail due to circular dependencies
- Solution: Refactor test setup to avoid circular imports

### Validation Steps

After migrating test imports:

```bash
# Verify no import errors
python -m pytest tests/unit/platform/core --collect-only

# Run critical path tests
pytest tests/unit/platform/core tests/unit/domains/intelligence

# Check coverage
pytest --cov=src/platform --cov=src/domains
```

### Rollback Plan

If migration breaks critical tests:

```bash
# Revert test imports
git checkout tests/

# Run tests with old imports (may fail)
pytest tests/unit/platform/core --tb=short
```

## Current Work

- [x] Phase 1: Migrate source imports (573 files)
- [ ] Phase 2: Migrate test imports
- [ ] Phase 3: Reorganize test structure
- [ ] Phase 4: Update pytest config
- [ ] Phase 5: Verify test coverage

## Next Steps

1. Run import migration on tests/
2. Fix any test-specific import issues
3. Reorganize test files to mirror src/
4. Update pyproject.toml test paths
5. Run full test suite

