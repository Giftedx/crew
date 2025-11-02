# Troubleshooting Guide - Repository Restructure

This guide helps troubleshoot common issues after the repository restructure from a partially migrated state to a clean 3-layer architecture.

## Common Issues and Solutions

### 1. Import Errors After Restructure

**Symptom**: `ModuleNotFoundError` or `ImportError` after restructure

**Possible Causes**:
- Legacy import paths still in code
- Missing `__init__.py` files
- Incorrect import paths

**Solutions**:

1. **Check for Legacy Imports**:
```bash
# Find legacy imports
grep -r "from core\." src/ | grep -v __pycache__
grep -r "from ai\." src/ | grep -v __pycache__
grep -r "from obs\." src/ | grep -v __pycache__
grep -r "from ingest\." src/ | grep -v __pycache__
grep -r "from analysis\." src/ | grep -v __pycache__
grep -r "from memory\." src/ | grep -v "__pycache__\|domains.memory"
```

Should return zero results. If not, migrate remaining imports:
```bash
python scripts/migrate_imports.py --file <file_path>
```

2. **Verify Import Paths**:
   - Platform layer: `from platform.* import ...`
   - Domain layer: `from domains.* import ...`
   - App layer: `from app.* import ...`

3. **Check `__init__.py` Files**:
   - Ensure all package directories have `__init__.py`
   - Verify exports are correct

4. **Python Path Issues**:
   - Ensure `src/` is in `PYTHONPATH` or use `python -m` syntax
   - Check `pyproject.toml` package configuration

### 2. Module Resolution Errors

**Symptom**: `ModuleNotFoundError: No module named 'platform.core'`

**Possible Causes**:
- Python treating `platform` as standard library module
- Incorrect PYTHONPATH
- Missing `src/` in path

**Solutions**:

1. **Use Explicit Source Path**:
```python
# Instead of: from platform.core.step_result import StepResult
# Use explicit path:
from src.platform.core.step_result import StepResult
```

2. **Set PYTHONPATH**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

3. **Use `python -m` Syntax**:
```bash
# Instead of: python app/main.py
python -m app.main
```

4. **Install in Development Mode**:
```bash
pip install -e .
```

### 3. Test Failures After Migration

**Symptom**: Tests failing with import errors or missing modules

**Solutions**:

1. **Update Test Imports**:
   - Change test imports to use new paths
   - Example: `from ultimate_discord_intelligence_bot.tools.*` → `from domains.*.tools.*`

2. **Check Test Configuration**:
   - Verify `pytest.ini` or `pyproject.toml` has correct paths
   - Ensure `src/` is in Python path for tests

3. **Update Test Fixtures**:
   - Update fixtures that reference old paths
   - Update mocks for moved modules

4. **Run Tests from Repository Root**:
```bash
# Always run from repository root
cd /path/to/repo
python -m pytest tests/
```

### 4. Missing Tool Registrations

**Symptom**: Tools not found or registered incorrectly

**Possible Causes**:
- MAPPING dictionary not updated
- Tool imports incorrect
- Lazy loading broken

**Solutions**:

1. **Verify Tool MAPPING**:
   - Check `src/ultimate_discord_intelligence_bot/tools/__init__.py`
   - Verify MAPPING points to correct `domains/` locations

2. **Check Tool Imports**:
   - Verify tools use correct import paths
   - Check `__getattr__` function in `tools/__init__.py`

3. **Verify Tool Registration**:
```python
# Check if tool is registered
from ultimate_discord_intelligence_bot.tools import MyTool
```

### 5. Application Startup Errors

**Symptom**: Application fails to start with import errors

**Solutions**:

1. **Check Entry Point**:
   - Verify `app/main.py` exists and is correct
   - Check `pyproject.toml` entry point configuration

2. **Verify Configuration**:
   - Check `app/config/settings.py` exists
   - Verify configuration paths are correct

3. **Check Dependencies**:
   - Verify all dependencies installed
   - Check for missing packages

4. **Use Correct Import Syntax**:
```bash
# Correct way to start application
python -m app.main
```

### 6. Missing Files After Restructure

**Symptom**: File not found errors

**Possible Causes**:
- File moved during restructure
- File deleted as duplicate
- Incorrect file path

**Solutions**:

1. **Search for File**:
```bash
find src/ -name "<filename>" -type f
```

2. **Check Migration Logs**:
   - Review phase completion documents in `docs/restructure/`
   - Check what happened to specific files

3. **Verify File Was Moved**:
   - Check if file exists in new location
   - Verify import path matches new location

### 7. Framework Integration Issues

**Symptom**: CrewAI, Qdrant, DSPy, or other framework integration broken

**Solutions**:

1. **Verify Framework Location**:
   - CrewAI: `domains/orchestration/crewai/`
   - Qdrant: `domains/memory/vector/qdrant/`
   - DSPy: `platform/prompts/dspy/`
   - LlamaIndex: `platform/rag/llamaindex/`
   - Mem0: `domains/memory/continual/mem0/`
   - HippoRAG: `domains/memory/continual/hipporag/`

2. **Check Framework Imports**:
   - Verify imports use new paths
   - Check for legacy import paths

3. **Verify Integration Points**:
   - Check framework configuration files
   - Verify connection to framework-specific directories

### 8. Circular Import Errors

**Symptom**: `ImportError: cannot import name 'X' from partially initialized module`

**Solutions**:

1. **Identify Circular Dependency**:
   - Use import tracing
   - Check import graph

2. **Refactor Imports**:
   - Move imports inside functions
   - Use lazy imports
   - Restructure module dependencies

3. **Use Type Checking Imports**:
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from platform.core.step_result import StepResult
```

### 9. Documentation Out of Date

**Symptom**: Documentation references old paths or structure

**Solutions**:

1. **Update Documentation**:
   - Update README.md
   - Update architecture docs
   - Update developer guides
   - Update Cursor rules

2. **Verify Documentation Accuracy**:
   - Check all file paths in docs
   - Verify import examples
   - Update directory structure diagrams

### 10. Performance Issues

**Symptom**: Slower performance after restructure

**Possible Causes**:
- Import path changes affecting import speed
- Missing caching
- Circular dependencies

**Solutions**:

1. **Profile Imports**:
```bash
python -X importtime -m app.main 2>&1 | head -20
```

2. **Check for Circular Dependencies**:
   - Use import graph analysis
   - Refactor to break cycles

3. **Optimize Import Paths**:
   - Use shorter import paths where possible
   - Avoid deep import chains

## Verification Commands

### Check for Legacy Imports
```bash
# Should return zero results
grep -rE "from (core|ai|obs|ingest|analysis|memory)\." src/ | grep -v __pycache__ | wc -l
```

### Verify Directory Structure
```bash
# Should not exist
ls src/core/ src/ai/ src/obs/ src/ingest/ src/analysis/ src/memory/ 2>&1 | grep "No such file"
```

### Check Import Resolution
```bash
python scripts/verify_imports.py
```

### Verify No Duplicates
```bash
python scripts/verify_duplicates.py --source src/ultimate_discord_intelligence_bot/tools --target src/domains
```

### Run Tests
```bash
make test
# or
python -m pytest tests/
```

## Getting Help

1. **Check Documentation**:
   - `docs/restructure/MIGRATION_COMPLETE.md`
   - `docs/restructure/LESSONS_LEARNED.md`
   - `docs/architecture/overview.md`

2. **Review Migration Logs**:
   - Phase completion documents in `docs/restructure/`
   - Git commit history

3. **Use Verification Scripts**:
   - `scripts/verify_imports.py`
   - `scripts/verify_duplicates.py`
   - `scripts/analyze_imports.py`

4. **Check Test Suite**:
   - Run tests to identify specific failures
   - Review test output for detailed error messages

## Prevention

To prevent issues:

1. ✅ Always use new import paths (`platform.*`, `domains.*`, `app.*`)
2. ✅ Run tests after any changes
3. ✅ Verify imports resolve correctly
4. ✅ Update documentation when making changes
5. ✅ Use verification scripts before committing
6. ✅ Follow 3-layer architecture principles

## Rollback Procedure

If issues are severe, rollback to pre-restructure baseline:

1. **Identify Baseline Tag**:
```bash
git tag -l "*restructure*"
```

2. **Checkout Baseline**:
```bash
git checkout pre-restructure-baseline-YYYYMMDD
```

3. **Create New Branch**:
```bash
git checkout -b rollback-YYYYMMDD
```

4. **Apply Fixes**:
   - Fix specific issues
   - Test thoroughly
   - Commit fixes

Note: Rollback should be last resort. Most issues can be fixed with import path corrections.
