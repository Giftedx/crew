### ⚡ Test Collection & Full-Stack Test Opt-In

By default, running `pytest` will **skip root-level test_*.py files** (such as `test_autointel.py`, `test_crew_fixes.py`, etc.) to ensure fast, reliable test runs. These files are typically heavy integration or end-to-end scripts that can take a long time to run or require external resources.

**To run the full suite including these heavy tests, set the environment variable:**

```sh
FULL_STACK_TEST=1 pytest
```

You will see a message like `[pytest] Skipping root-level test_autointel.py (set FULL_STACK_TEST=1 to include)` if you run without the variable set.

This ensures that day-to-day development is fast and stable, while still allowing full-stack/integration testing when needed.

# Developer Onboarding Guide

## Ultimate Discord Intelligence Bot - Quick Start for New Developers

**🧹 Repository Organization:**

- Root directory kept minimal (only README, configs, Makefile)
- All demos, results, and experimental code archived automatically
- Historical completion reports organized in `docs/history/`
- Run `make organize-root` anytime to clean up clutter

### 🚀 Welcome

You're joining a well-organized, AI-guided development environment with clear structure and comprehensive documentation. This guide will get you productive quickly.

### 📁 Project Structure Overview

```text
src/                               # Main source code
├── core/                          # 54+ foundational utilities
│   ├── http_utils.py             # HTTP retry wrappers (REQUIRED for all requests)
│   ├── secure_config.py          # Configuration management
│   ├── time.py                   # UTC time utilities
│   └── ...
├── analysis/                      # Content processing modules
│   ├── transcribe.py             # Audio transcription
│   ├── topics.py                 # Topic extraction
│   └── segmenter.py              # Content segmentation
├── memory/                        # Vector store & memory management
├── ingest/                        # Multi-platform content ingestion
├── security/                      # Moderation, RBAC, rate limiting
├── debate/                        # Structured argumentation system
├── grounding/                     # Citation enforcement & verification
└── ultimate_discord_intelligence_bot/
    ├── tools/                     # 84 AI agent tools
    ├── tenancy/                   # Multi-tenant isolation
    └── crew.py                    # CrewAI orchestrator

archive/                           # Organized historical artifacts
├── demos/                         # Demo and example scripts
├── results/                       # Experiment results and output files
├── experimental/                  # Experimental engines and prototypes
└── logs/                          # Log files from demos and tests

docs/                              # Documentation
├── history/                       # Implementation reports and phase docs
├── architecture/                  # System design documentation
└── ...                           # Feature-specific guides
```

**🧹 Repository Organization:**

- Root directory kept minimal (only README, configs, Makefile)
- All demos, results, and experimental code archived automatically
- Historical completion reports organized in `docs/history/`
- Run `make organize-root` anytime to clean up clutter

### 🛠️ Quick Setup (5 Minutes)

Tip: Prefer the one-liner if you're on Debian/Ubuntu or just want the fastest path.

```bash
make first-run
```

This will: create/activate a venv, install dev extras (prefers uv), set up git hooks, run doctor checks, and do a quick smoke test.

If doctor reports missing secrets (e.g., DISCORD_BOT_TOKEN), initialize your env file and fill in values:

```bash
make init-env
# then open .env and set DISCORD_BOT_TOKEN and at least one LLM key (OPENAI_API_KEY or OPENROUTER_API_KEY)
make doctor
```

1. **Create a Virtual Environment (avoids PEP 668)**

    Option A — recommended (uv):

    ```bash
    uv venv --python 3.11
    . .venv/bin/activate
    ```

    Option B — standard Python venv:

    ```bash
    python3 -m venv .venv
    . .venv/bin/activate
    ```

    Or use the built-in helpers (idempotent):

    ```bash
    make uv-bootstrap   # creates .venv (if missing) and installs dev extras with uv
    make ensure-venv    # creates .venv and installs dev deps with pip
    ```

1. **Install Dependencies (inside venv)**

    ```bash
    uv pip install -e '.[dev]'   # preferred (fast, reproducible)
    # or:
    pip install -e '.[dev]'      # fallback if uv is unavailable
    ```

    Tip (zsh): keep the quotes around '.[dev]'. If prompted to correct 'venv' to '.venv', choose '.venv'.

1. **Verify Installation**

   ```bash
   make test-fast                   # Run core tests (36 tests, ~8 seconds)
   ```

1. **Setup Development Environment**

   ```bash
   make format lint type            # Auto-fix style, check types
   ```

#### Troubleshooting (Debian/Ubuntu)

If you see "externally-managed-environment" (PEP 668) or ensurepip errors when creating/using the venv:

- Option A (recommended): use uv for a clean venv and install

    ```bash
    uv venv --python 3.11
    . .venv/bin/activate
    uv pip install -e '.[dev]'
    ```

- Option B (APT fallback): ensure system venv tools are present, then install inside venv

    ```bash
    sudo apt update
    sudo apt install -y python3-venv python3-full
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -e '.[dev]'
    ```

Notes:

- In zsh, keep the quotes around '.[dev]'.
- If zsh asks to correct 'venv' to '.venv', choose '.venv'.

### 🏗️ Core Development Patterns

#### 1. HTTP Requests (CRITICAL)

```python
# ❌ NEVER do this
import requests
response = requests.get(url)

# ✅ ALWAYS do this
from core.http_utils import retrying_get
response = retrying_get(url, timeout_seconds=30)
```

#### 2. Error Handling

```python
from ultimate_discord_intelligence_bot.step_result import StepResult

def my_tool() -> StepResult:
    try:
        result = process_data()
        return StepResult.ok(data=result)
    except Exception as e:
        return StepResult.fail(error=str(e))
```

#### 3. Tenant Context (Multi-tenancy)

```python
from ultimate_discord_intelligence_bot.tenancy import TenantContext, with_tenant

with with_tenant(TenantContext(tenant_id="tenant", workspace_id="workspace")):
    # All operations here are tenant-scoped
    # Memory namespaces automatically prefixed
    pass
```

#### 4. Configuration

```python
# ❌ Don't do this
import os
api_key = os.getenv("API_KEY")

# ✅ Do this
from core.secure_config import get_config
api_key = get_config().api_key
```

### 🔧 Development Workflow

#### Daily Commands

```bash
# Start development
make format lint                   # Auto-fix style issues
make test-fast                     # Quick validation (8 seconds)

# Before committing
make format lint type              # Full validation
make test                          # Complete test suite
```

#### Adding New Tools

```python
from ultimate_discord_intelligence_bot.tools._base import BaseTool
from ultimate_discord_intelligence_bot.step_result import StepResult

class MyTool(BaseTool[dict]):
    name: str = "My Tool"
    description: str = "Tool description"

    def _run(self, input_param: str) -> StepResult:
        return StepResult.ok(result="processed")
```

#### Adding New Analysis Modules

Put in `src/analysis/`, return `StepResult`, register in `crew.py`:

```python
# src/analysis/my_analyzer.py
from ultimate_discord_intelligence_bot.step_result import StepResult

def analyze_content(content: str) -> StepResult:
    # Your analysis logic
    return StepResult.ok(data={"analysis": "result"})
```

### 📚 Key Documentation

#### Essential Reading (15 minutes)

1. **`.github/copilot-instructions.md`** - Complete architectural guidance
1. **`docs/conventions.md`** - Coding standards and patterns
1. **`docs/feature_flags.md`** - Feature flag usage

#### Reference Documentation

- **`docs/core_services.md`** - Core module overview
- **`docs/tenancy.md`** - Multi-tenant patterns
- **`docs/grounding.md`** - Citation and verification
- **`docs/memory.md`** - Vector store usage

### 🧭 Navigation Guide

#### Finding What You Need

| Task | Location | Example |
|------|----------|---------|
| **Add HTTP request** | `core/http_utils.py` | `retrying_get(url)` |
| **Create new tool** | `src/ultimate_discord_intelligence_bot/tools/` | Inherit from `BaseTool` |
| **Add analysis step** | `src/analysis/` | Return `StepResult` |
| **Memory operations** | `src/memory/api.py` | Tenant-scoped storage |
| **Configuration** | `core/secure_config.py` | `get_config()` |

#### Directory Quick Reference

```bash
src/core/          # Foundational utilities (54+ files)
src/analysis/      # Content processing (10 files)
src/memory/        # Vector store & caching
src/security/      # Auth, rate limiting, moderation
src/ingest/        # Multi-platform content ingestion
src/debate/        # Structured argumentation
src/grounding/     # Citation enforcement
tests/             # All test files
docs/              # 50+ documentation files
```

### 🎯 Common Tasks

#### 1. Add a New Content Source

```bash
# 1. Create source module
touch src/ingest/sources/my_platform.py

# 2. Implement with StepResult pattern
# 3. Register in dispatcher
# 4. Add tests in tests/test_ingest/
```

#### 2. Add New Agent Tool

```bash
# 1. Create tool file
touch src/ultimate_discord_intelligence_bot/tools/my_tool.py

# 2. Inherit from BaseTool, return StepResult
# 3. Register in crew.py
# 4. Add tests
```

#### 3. Add Analysis Pipeline Step

```bash
# 1. Create analysis module
touch src/analysis/my_analysis.py

# 2. Return StepResult with structured data
# 3. Register with agents in crew.py
# 4. Test with empty/failure cases
```

### ⚠️ Critical Anti-Patterns to Avoid

```python
# ❌ Raw HTTP requests
import requests  # Use core.http_utils instead

# ❌ Non-UTC time
from datetime import datetime
now = datetime.now()  # Use core.time.ensure_utc()

# ❌ Cross-tenant operations
# Missing tenant context  # Always use with_tenant()

# ❌ Tools raising exceptions
raise Exception("Error")  # Return StepResult.fail() instead

# ❌ Hardcoded config
API_KEY = "secret"  # Use core.secure_config.get_config()
```

### 🧪 Testing Guidelines

#### Test Structure

```text
tests/
├── test_core/           # Core module tests
├── test_analysis/       # Analysis pipeline tests
├── test_tools/          # Tool tests
├── test_memory/         # Memory system tests
└── conftest.py          # Shared fixtures
```

#### Writing Tests

```python
import pytest
from ultimate_discord_intelligence_bot.step_result import StepResult

def test_my_tool():
    """Test tool returns StepResult."""
    result = my_tool.run("input")
    assert isinstance(result, StepResult)
    assert result.success
```

### 🚨 Debug Common Issues

#### "Nothing happens" bugs

Check feature flags:

```bash
export ENABLE_HTTP_RETRY=1
export ENABLE_RAG_CONTEXT=1
# See docs/feature_flags.md for full list
```

#### Import errors

```python
# ✅ Correct import paths
from core.http_utils import retrying_get
from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy import with_tenant
```

#### Type checking failures

```bash
make type-guard  # Fail if mypy errors increase
# Fix errors instead of adding to baseline
```

### 📞 Getting Help

1. **AI Assistance**: Enhanced copilot instructions provide comprehensive guidance
1. **Documentation**: 50+ guides in `docs/` directory
1. **Code Examples**: Search existing tools and modules for patterns
1. **Architecture**: Follow the patterns in `core/` modules

### 🎉 You're Ready

This codebase is optimized for AI-assisted development. The enhanced copilot instructions in `.github/copilot-instructions.md` provide comprehensive guidance for any development task.

**Key Success Factors**:

- ✅ Use HTTP wrappers (`core.http_utils`)
- ✅ Return `StepResult` from tools/analysis
- ✅ Thread tenant context through operations
- ✅ Follow existing patterns instead of inventing new ones
- ✅ Run `make test-fast` frequently for quick validation

**Next Steps**:

1. Read `.github/copilot-instructions.md` for complete architectural guidance
1. Explore existing tools and modules to understand patterns
1. Start with small changes to get familiar with the structure
1. Leverage AI assistance for development tasks

Welcome to the Ultimate Discord Intelligence Bot development team! 🚀
