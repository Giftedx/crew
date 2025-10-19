# MyPy Usage Guide

## Running MyPy

### Correct Method (Avoids Duplicate Module Errors)

Run MyPy from within the `src` directory to avoid duplicate module path issues:

```bash
cd src
../.venv/bin/python -m mypy <target_files> --ignore-missing-imports
```

### Full Codebase Check

```bash
cd src
../.venv/bin/python -m mypy . --ignore-missing-imports
```

### Check Specific Module

```bash
cd src
../.venv/bin/python -m mypy core/llm_router.py --ignore-missing-imports
```

## Current Status

**Total Errors Found**: 921 (when checking from src directory)

This is significantly higher than the 120 baseline mentioned in documentation, indicating:

1. The baseline may have been for a subset of files
2. The configuration in `pyproject.toml` limits MyPy to specific files only
3. Many errors are in third-party library stub issues

## Error Categories

Based on initial scan, errors include:

- Missing type parameters for generic types
- Missing type annotations on functions
- Unreachable code
- Missing variable annotations
- Unused type ignore comments
- Third-party library type issues (OpenTelemetry, discord.py)

## Configuration

The project uses configuration in `pyproject.toml` which:

- Limits checking to specific files (see `files =` section)
- Excludes tests and scripts
- Uses incremental adoption approach
- Sets `ignore_missing_imports = true` globally

## Recommended Workflow

1. **Run from src directory** to avoid module path conflicts
2. **Check specific modules** rather than full codebase
3. **Focus on critical paths** first (pipeline, memory, routing)
4. **Gradually expand** type coverage

## Known Issues

- **Duplicate Module Discovery**: Running MyPy from project root causes `core.settings` vs `src.core.settings` conflict
- **Solution**: Always run from `src` directory or update PYTHONPATH explicitly
