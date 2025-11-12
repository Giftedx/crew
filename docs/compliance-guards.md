# Compliance Guards Documentation

## Overview

Compliance guards are automated validation scripts that enforce architectural contracts, code quality standards, and platform conventions across the Ultimate Discord Intelligence Bot codebase. They prevent violations from entering the codebase through CI enforcement and pre-commit hooks.

## Guard Categories

### 1. HTTP Wrapper Usage Guard (`validate_http_wrappers_usage.py`)

**Purpose**: Ensures all HTTP requests use sanctioned wrapper functions instead of direct `requests.*` calls.

**Contract Enforced**:

- All HTTP calls must use `resilient_get`, `resilient_post`, or `retrying_*` functions from `platform.http.http_utils`
- Direct `requests.get`, `requests.post`, `session.get`, `client.get` calls are forbidden outside approved modules
- Exceptions: wrapper modules themselves, compatibility shims, tests

**Why**:

- Ensures circuit breakers, retries, timeouts, and tenant context propagation are applied consistently
- Provides centralized observability for all HTTP operations
- Enables automatic failure recovery and resilience

**Common Violations**:

```python
# ❌ VIOLATION
import requests
response = requests.get(url)

# ✅ CORRECT
from platform.http.http_utils import resilient_get
response = resilient_get(url, timeout_seconds=10.0)
```

**Fix Strategy**:

1. Replace `import requests` with `from platform.http.http_utils import resilient_get, resilient_post`
2. Change `requests.get(...)` to `resilient_get(...)`
3. Add `timeout_seconds` parameter (required)
4. Handle StepResult return type if using advanced wrappers

### 2. Tools Exports Guard (`validate_tools_exports.py`)

**Purpose**: Validates that all tool classes are properly exported in `__all__` and importable.

**Contract Enforced**:

- Every tool class in `src/ultimate_discord_intelligence_bot/tools/` must be listed in `tools/__init__.py::__all__`
- Tool classes must be importable without raising exceptions
- Tool stubs (for optional dependencies) are allowed

**Why**:

- Prevents tools from being written but not registered
- Ensures CrewAI can discover and use all available tools
- Catches import errors and dependency issues early

**Common Violations**:

```python
# In src/ultimate_discord_intelligence_bot/tools/my_new_tool.py
class MyNewTool(BaseTool):  # ✅ Implemented
    ...

# ❌ VIOLATION: Missing from tools/__init__.py::__all__
```

**Fix Strategy**:

1. Add tool class name to `src/ultimate_discord_intelligence_bot/tools/__init__.py::__all__`
2. Import tool class in `__init__.py`
3. Run `make guards` to verify

### 3. Metrics Instrumentation Guard (`metrics_instrumentation_guard.py`)

**Purpose**: Ensures metrics follow naming conventions and are properly instrumented.

**Contract Enforced**:

- Metrics must follow `{domain}_{component}_{metric}_{unit}` naming pattern
- Counter names must end in `_total`
- Histogram/summary names must end in duration unit (`_seconds`, `_ms`, `_bytes`)
- Required labels: `tenant_id` (for multi-tenant metrics)

**Why**:

- Enables Prometheus/Grafana dashboards to work correctly
- Prevents metric cardinality explosions
- Ensures consistent observability across the platform

**Common Violations**:

```python
# ❌ VIOLATION: Missing _total suffix
counter = metrics.counter("tool_runs", labels={"tool": tool_name})

# ✅ CORRECT
counter = metrics.counter("tool_runs_total", labels={"tool": tool_name, "tenant_id": tenant_id})
```

**Fix Strategy**:

1. Add `_total` suffix to counter metrics
2. Add `_seconds` suffix to duration histograms
3. Include `tenant_id` in labels for tenant-scoped metrics
4. Use `get_metrics()` helper for standard metric access

### 4. Deprecated Directories Guard (`deprecated_directories_guard.py`)

**Purpose**: Prevents new modules from being added to directories marked as deprecated per architecture decision records (ADRs).

**Contract Enforced**:

- No new files in `src/core/routing/` (migrated to `src/platform/llm/`)
- No new files in `src/ai/routing/` (migrated to `src/platform/llm/`)
- No new files in `src/performance/` (migrated to platform components)

**Why**:

- Enforces 3-layer architecture migration
- Prevents regression to deprecated patterns
- Keeps codebase maintainable

**Common Violations**:

```bash
# ❌ VIOLATION: Adding file to deprecated directory
git add src/core/routing/new_router.py

# ✅ CORRECT: Use new architecture
git add src/platform/llm/routers/new_router.py
```

**Fix Strategy**:

1. Move new code to correct platform/domains/app layer
2. Follow 3-layer architecture documented in README
3. Update imports to reference new locations

### 5. Dispatcher Usage Guard (`validate_dispatcher_usage.py`)

**Purpose**: Ensures async task dispatch uses approved patterns with proper tenant context propagation.

**Contract Enforced**:

- Use `run_with_tenant_context` wrapper for ThreadPoolExecutor submissions
- No direct `DispatcherPoolExecutor` instantiation without context wrapping

**Why**:

- Prevents cross-tenant data leaks
- Ensures tenant context propagates across async boundaries
- Maintains observability in multi-threaded scenarios

**Common Violations**:

```python
# ❌ VIOLATION: Context lost
with ThreadPoolExecutor() as pool:
    future = pool.submit(task_func, args)

# ✅ CORRECT: Context preserved
from ultimate_discord_intelligence_bot.tenancy.context import run_with_tenant_context
with ThreadPoolExecutor() as pool:
    future = pool.submit(run_with_tenant_context(task_func), args)
```

## CI Integration

### Continuous Integration

Guards run automatically on every pull request via `.github/workflows/guards-ci.yml`:

```yaml
on:
  pull_request:
  push:
    branches: [ main, master, develop ]
```

**Workflow Steps**:

1. Checkout code with full git history
2. Set up Python 3.12 environment
3. Cache pip dependencies for faster runs
4. Install project with dev dependencies
5. Run `make guards` and capture output
6. Generate structured violation report
7. Upload artifacts (logs + JSON report)
8. Comment on PR if violations found (includes fix instructions)
9. Fail workflow if guards failed (blocks merge)

**Viewing Results**:

- Check workflow status in GitHub Actions tab
- Download `guard-violations-report` artifact for detailed JSON
- Read PR comment for violation summary and fix instructions

### Pre-Commit Hooks

Guards run locally before each commit via `.githooks/pre-commit`:

**Installation**:

```bash
make setup-hooks  # Installs pre-commit hook
```

**Behavior**:

- Runs all 5 guards before allowing commit
- Provides colored output for each guard
- Shows pass/fail status in real-time
- Blocks commit if any guard fails
- Can be bypassed in emergencies: `git commit --no-verify`

**Example Output**:

```
🔒 Running compliance guards pre-commit hook...
Running guards validation...
  → Checking HTTP wrapper usage...
    ✓ HTTP wrapper guard passed
  → Checking tools exports...
    ✓ Tools export guard passed
  → Checking metrics instrumentation...
    ✓ Metrics instrumentation guard passed
  → Checking deprecated directories...
    ✓ Deprecated directories guard passed
  → Checking dispatcher usage...
    ✓ Dispatcher usage guard passed

✅ All compliance guards passed!
```

## Running Guards Manually

### All Guards

```bash
make guards  # Run all compliance guards
```

### Individual Guards

```bash
# HTTP wrapper validation
python scripts/validate_http_wrappers_usage.py

# Tools exports validation
python scripts/validate_tools_exports.py

# Metrics instrumentation validation
python scripts/metrics_instrumentation_guard.py

# Deprecated directories validation
python scripts/guards/deprecated_directories_guard.py

# Dispatcher usage validation
python scripts/validate_dispatcher_usage.py
```

### Guard Reports

Generate structured JSON report from guard execution:

```bash
# Run guards and capture output
make guards 2>&1 | tee guards_output.log

# Generate report
python scripts/generate_guard_report.py \
  --input guards_output.log \
  --output reports/guard_violations.json \
  --pretty
```

**Report Structure**:

```json
{
  "timestamp": "2025-11-12T10:30:00Z",
  "total_guards": 5,
  "passed_guards": 4,
  "failed_guards": 1,
  "total_violations": 3,
  "guards": [
    {
      "guard_name": "validate_http_wrappers_usage",
      "status": "failed",
      "violations": [
        {
          "guard_name": "validate_http_wrappers_usage",
          "severity": "error",
          "file_path": "src/domains/intelligence/analysis/youtube_tool.py",
          "line_number": 45,
          "message": "Direct requests.get usage detected",
          "suggestion": "Use resilient_get from platform.http.http_utils"
        }
      ]
    }
  ],
  "summary": "Total Guards: 5\nPassed: 4, Failed: 1\nTotal Violations: 3"
}
```

## Fixing Violations

### General Workflow

1. **Run guards locally**:

   ```bash
   make guards
   ```

2. **Review violations**: Read output to identify files and line numbers

3. **Fix violations**: Apply corrections per guard-specific fix strategy (see above)

4. **Verify fix**:

   ```bash
   make guards  # Should pass
   ```

5. **Commit**:

   ```bash
   git add <fixed-files>
   git commit -m "fix: resolve compliance guard violations"
   # Pre-commit hook runs automatically and verifies fix
   ```

### Emergency Bypass

**Only use in genuine emergencies** (production incident, security hotfix):

```bash
git commit --no-verify -m "hotfix: critical security patch"
```

**Post-emergency**:

1. Create follow-up PR to fix violations
2. Document bypass reason in commit message
3. Add guard violations to tech debt backlog

## Adding New Guards

1. **Create guard script**:

   ```bash
   # Example: scripts/guards/new_compliance_guard.py
   ```

2. **Follow template**:

   ```python
   #!/usr/bin/env python3
   """Guard description."""
   import sys

   def main() -> int:
       violations = []
       # ... validation logic ...
       if violations:
           for v in violations:
               print(f"VIOLATION: {v}")
           return 1
       return 0

   if __name__ == "__main__":
       sys.exit(main())
   ```

3. **Add to Makefile**:

   ```makefile
   guards:
       $(PYTHON) scripts/guards/new_compliance_guard.py && ...
   ```

4. **Update pre-commit hook**: Add guard to `.githooks/pre-commit`

5. **Document**: Add section to this guide

## Best Practices

### For Developers

- Run `make guards` before pushing
- Install pre-commit hooks: `make setup-hooks`
- Read violation messages carefully (contain fix instructions)
- Fix violations immediately (don't accumulate technical debt)
- Ask for help if violation seems incorrect

### For Reviewers

- Check CI guard status before approving PRs
- Require violations to be fixed (don't approve with failing guards)
- Verify fixes address root cause (not just suppress symptoms)
- Suggest guard improvements if patterns emerge

### For Maintainers

- Keep guards up to date with architecture changes
- Add new guards when new patterns need enforcement
- Review guard reports monthly to identify systemic issues
- Update documentation when guards change

## Troubleshooting

### Guard Fails but Code Looks Correct

**Symptom**: Guard reports violation but code follows conventions

**Solutions**:

1. Check if file is in allowlist (some files legitimately exempt)
2. Verify pattern matching isn't catching false positive
3. Check for whitespace/formatting differences
4. File bug report with guard output and file content

### Pre-Commit Hook Not Running

**Symptom**: Can commit without seeing guard output

**Solutions**:

```bash
# Reinstall hooks
make setup-hooks

# Verify hook is executable
ls -la .git/hooks/pre-commit

# Check hook content
cat .git/hooks/pre-commit
```

### CI Guard Passes but Local Fails (or vice versa)

**Symptom**: Different results between CI and local

**Solutions**:

1. Ensure same Python version (3.12 in CI)
2. Install same dependencies: `pip install -e .[dev]`
3. Check for uncommitted changes affecting guard
4. Compare git diff between local and CI

## Metrics & Observability

Guards emit metrics when run in production:

```prometheus
# Guard execution duration
guard_execution_duration_seconds{guard="validate_http_wrappers_usage"} 0.234

# Compliance violations detected
compliance_violations_total{guard="tools_exports",severity="error"} 3

# Guard execution results
guard_execution_total{guard="deprecated_directories",status="passed"} 1
```

**Dashboards**:

- Grafana: "Compliance Guards" dashboard
- Alerts: PagerDuty on repeated CI failures

## References

- **Architecture Decision Records**: `docs/adr/` (ADR-0001 through ADR-0005)
- **3-Layer Architecture**: `README.md` (Architecture section)
- **StepResult Pattern**: `src/platform/core/step_result.py`
- **HTTP Utilities**: `src/platform/http/http_utils.py`
- **Metrics Standards**: `docs/observability.md`
- **Tenancy Context**: `src/ultimate_discord_intelligence_bot/tenancy/context.py`

## Support

**Questions**: Ask in #eng-platform Slack channel
**Bug Reports**: File issue with `compliance-guards` label
**Improvements**: Submit PR with guard enhancement

---

**Last Updated**: 2025-11-12
**Maintainer**: Platform Team
**Related**: F011/F014 Polishv2 Implementation
