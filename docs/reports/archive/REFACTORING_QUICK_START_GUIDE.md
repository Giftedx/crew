# Refactoring Quick Start Guide

**Companion to**: `STRATEGIC_REFACTORING_PLAN_2025.md`
**Purpose**: Tactical guide for immediate implementation
**Last Updated**: October 31, 2025

---

## 🚀 Week 1 Action Items

### Day 1-2: Crew Component Consolidation Setup

#### Step 1: Create New Package Structure

```bash
# Create the new crew_core package
mkdir -p src/ultimate_discord_intelligence_bot/crew_core
touch src/ultimate_discord_intelligence_bot/crew_core/__init__.py
touch src/ultimate_discord_intelligence_bot/crew_core/interfaces.py
touch src/ultimate_discord_intelligence_bot/crew_core/executor.py
touch src/ultimate_discord_intelligence_bot/crew_core/factory.py
touch src/ultimate_discord_intelligence_bot/crew_core/error_handling.py
touch src/ultimate_discord_intelligence_bot/crew_core/insights.py
```

#### Step 2: Define Interfaces

**File**: `src/ultimate_discord_intelligence_bot/crew_core/interfaces.py`

```python
"""Core interfaces for unified crew system."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass
from ultimate_discord_intelligence_bot.step_result import StepResult

@dataclass
class CrewConfig:
    """Configuration for crew execution."""
    tenant_id: str
    enable_cache: bool = True
    enable_telemetry: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3
    quality_threshold: float = 0.7

@dataclass
class CrewTask:
    """A task to be executed by the crew."""
    task_id: str
    task_type: str
    description: str
    inputs: dict[str, Any]
    agent_requirements: list[str]
    tool_requirements: list[str]

class CrewExecutor(ABC):
    """Abstract base for crew executors."""

    @abstractmethod
    async def execute(
        self,
        task: CrewTask,
        config: CrewConfig
    ) -> StepResult:
        """Execute a crew task."""
        ...

    @abstractmethod
    async def validate_task(self, task: CrewTask) -> StepResult:
        """Validate task before execution."""
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution."""
        ...

class CrewFactory(ABC):
    """Abstract factory for creating crews."""

    @abstractmethod
    def create_executor(
        self,
        executor_type: str,
        config: CrewConfig
    ) -> CrewExecutor:
        """Create a crew executor."""
        ...

    @abstractmethod
    def get_available_executors(self) -> list[str]:
        """Get list of available executor types."""
        ...
```

#### Step 3: Implement Unified Executor

**File**: `src/ultimate_discord_intelligence_bot/crew_core/executor.py`

```python
"""Unified crew executor implementation."""

import asyncio
from typing import Any, Optional
from ultimate_discord_intelligence_bot.step_result import StepResult, ErrorCategory
from ultimate_discord_intelligence_bot.crew_core.interfaces import (
    CrewExecutor,
    CrewTask,
    CrewConfig
)
from obs.metrics import get_metrics
from core.http_utils import resilient_post
import structlog

logger = structlog.get_logger(__name__)

class UnifiedCrewExecutor(CrewExecutor):
    """Unified implementation consolidating all crew execution logic."""

    def __init__(self, config: CrewConfig):
        self.config = config
        self.metrics = get_metrics()

    async def execute(
        self,
        task: CrewTask,
        config: CrewConfig
    ) -> StepResult:
        """Execute a crew task with full observability."""

        logger.info(
            "crew_execution_started",
            task_id=task.task_id,
            task_type=task.task_type,
            tenant_id=config.tenant_id
        )

        # Validate task
        validation = await self.validate_task(task)
        if not validation.success:
            return validation

        # Execute with retries
        for attempt in range(config.max_retries):
            try:
                # Record attempt
                self.metrics.counter(
                    "crew_execution_attempts_total",
                    labels={
                        "task_type": task.task_type,
                        "attempt": str(attempt + 1)
                    }
                ).inc()

                # Execute task logic
                result = await self._execute_internal(task, config)

                if result.success:
                    logger.info(
                        "crew_execution_success",
                        task_id=task.task_id,
                        attempt=attempt + 1
                    )
                    return result

                # Check if retryable
                if not result.retryable:
                    return result

                # Wait before retry
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(
                    "crew_execution_error",
                    task_id=task.task_id,
                    error=str(e),
                    attempt=attempt + 1
                )

                if attempt == config.max_retries - 1:
                    return StepResult.fail(
                        f"Crew execution failed after {config.max_retries} attempts: {e}",
                        error_category=ErrorCategory.EXECUTION,
                        retryable=False
                    )

        return StepResult.fail(
            "Crew execution failed after max retries",
            error_category=ErrorCategory.EXECUTION,
            retryable=False
        )

    async def _execute_internal(
        self,
        task: CrewTask,
        config: CrewConfig
    ) -> StepResult:
        """Internal execution logic (to be migrated from existing crew.py)."""

        # TODO: Migrate execution logic from crew.py
        # This is where the actual CrewAI orchestration happens

        return StepResult.ok(
            result={"status": "completed"},
            metadata={"task_id": task.task_id}
        )

    async def validate_task(self, task: CrewTask) -> StepResult:
        """Validate task before execution."""

        if not task.task_id:
            return StepResult.fail(
                "Task ID is required",
                error_category=ErrorCategory.VALIDATION
            )

        if not task.description:
            return StepResult.fail(
                "Task description is required",
                error_category=ErrorCategory.VALIDATION
            )

        return StepResult.ok(result={"validated": True})

    async def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("crew_executor_cleanup", tenant_id=self.config.tenant_id)
```

#### Step 4: Create Migration Script

**File**: `scripts/migrate_crew_callers.py`

```python
"""Script to migrate crew callers to new unified API."""

import re
import os
from pathlib import Path

OLD_PATTERNS = [
    r"from ultimate_discord_intelligence_bot.crew import CrewRunner",
    r"from ultimate_discord_intelligence_bot.crew_new import",
    r"from ultimate_discord_intelligence_bot.crew_modular import",
]

NEW_IMPORT = "from ultimate_discord_intelligence_bot.crew_core import UnifiedCrewExecutor, CrewTask, CrewConfig"

def migrate_file(file_path: Path):
    """Migrate a single file."""
    content = file_path.read_text()
    modified = False

    for pattern in OLD_PATTERNS:
        if re.search(pattern, content):
            content = re.sub(pattern, NEW_IMPORT, content)
            modified = True

    if modified:
        file_path.write_text(content)
        print(f"✅ Migrated: {file_path}")

def main():
    """Migrate all Python files."""
    src_dir = Path("src")

    for py_file in src_dir.rglob("*.py"):
        if "crew_core" not in str(py_file):
            migrate_file(py_file)

if __name__ == "__main__":
    main()
```

---

### Day 3-4: Orchestrator Hierarchy Setup

#### Step 1: Create Orchestration Package

```bash
mkdir -p src/core/orchestration/{domain,application,infrastructure}
touch src/core/orchestration/__init__.py
touch src/core/orchestration/protocols.py
touch src/core/orchestration/facade.py
```

#### Step 2: Define Orchestration Protocols

**File**: `src/core/orchestration/protocols.py`

```python
"""Orchestration protocols and base classes."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol, runtime_checkable
from enum import Enum
from dataclasses import dataclass
from ultimate_discord_intelligence_bot.step_result import StepResult

class OrchestrationLayer(Enum):
    """Orchestration layers in the hierarchy."""
    DOMAIN = "domain"  # Business logic orchestration
    APPLICATION = "application"  # Application coordination
    INFRASTRUCTURE = "infrastructure"  # Infrastructure concerns

@dataclass
class OrchestrationContext:
    """Shared context for orchestration."""
    tenant_id: str
    request_id: str
    metadata: dict[str, Any]
    trace_id: Optional[str] = None

@runtime_checkable
class OrchestratorProtocol(Protocol):
    """Base protocol for all orchestrators."""

    @property
    def layer(self) -> OrchestrationLayer:
        """The orchestration layer this belongs to."""
        ...

    @property
    def name(self) -> str:
        """Orchestrator name."""
        ...

    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs
    ) -> StepResult:
        """Orchestrate a workflow or operation."""
        ...

class BaseOrchestrator(ABC):
    """Base class for orchestrators."""

    def __init__(self, layer: OrchestrationLayer, name: str):
        self._layer = layer
        self._name = name

    @property
    def layer(self) -> OrchestrationLayer:
        return self._layer

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs
    ) -> StepResult:
        """Orchestrate operation."""
        ...
```

#### Step 3: Create Orchestration Facade

**File**: `src/core/orchestration/facade.py`

```python
"""Unified facade for all orchestration."""

from typing import Optional
from ultimate_discord_intelligence_bot.step_result import StepResult
from core.orchestration.protocols import (
    OrchestrationContext,
    OrchestrationLayer,
    OrchestratorProtocol
)
import structlog

logger = structlog.get_logger(__name__)

class OrchestrationFacade:
    """Unified entry point for all orchestration."""

    def __init__(self):
        self._orchestrators: dict[str, OrchestratorProtocol] = {}

    def register(self, orchestrator: OrchestratorProtocol) -> None:
        """Register an orchestrator."""
        key = f"{orchestrator.layer.value}.{orchestrator.name}"
        self._orchestrators[key] = orchestrator
        logger.info(
            "orchestrator_registered",
            layer=orchestrator.layer.value,
            name=orchestrator.name
        )

    def get(
        self,
        layer: OrchestrationLayer,
        name: str
    ) -> Optional[OrchestratorProtocol]:
        """Get an orchestrator."""
        key = f"{layer.value}.{name}"
        return self._orchestrators.get(key)

    async def orchestrate(
        self,
        layer: OrchestrationLayer,
        name: str,
        context: OrchestrationContext,
        **kwargs
    ) -> StepResult:
        """Orchestrate via specific orchestrator."""

        orchestrator = self.get(layer, name)
        if not orchestrator:
            return StepResult.fail(
                f"Orchestrator not found: {layer.value}.{name}"
            )

        logger.info(
            "orchestration_started",
            layer=layer.value,
            name=name,
            tenant_id=context.tenant_id
        )

        result = await orchestrator.orchestrate(context, **kwargs)

        logger.info(
            "orchestration_completed",
            layer=layer.value,
            name=name,
            success=result.success
        )

        return result

# Global facade instance
_facade: Optional[OrchestrationFacade] = None

def get_orchestration_facade() -> OrchestrationFacade:
    """Get the global orchestration facade."""
    global _facade
    if _facade is None:
        _facade = OrchestrationFacade()
    return _facade
```

---

## 📦 Code Reuse Patterns

### Pattern 1: Universal Tool Decorator

```python
"""Universal tool decorator for automatic framework adaptation."""

from functools import wraps
from typing import Any, Callable
from ultimate_discord_intelligence_bot.step_result import StepResult

def universal_tool(
    name: str,
    category: str,
    description: str,
    input_schema: dict,
    output_schema: dict
):
    """Decorator to create framework-agnostic tools."""

    def decorator(func: Callable) -> Any:

        @wraps(func)
        class UniversalToolImpl:
            """Auto-generated universal tool."""

            def __init__(self):
                self.name = name
                self.category = category
                self.description = description
                self.input_schema = input_schema
                self.output_schema = output_schema

            async def execute(self, **kwargs) -> StepResult:
                """Execute the tool."""
                return await func(**kwargs)

            def to_crewai_tool(self):
                """Convert to CrewAI tool."""
                from crewai.tools import Tool
                return Tool(
                    name=self.name,
                    description=self.description,
                    func=lambda **kw: asyncio.run(self.execute(**kw))
                )

            def to_langgraph_tool(self):
                """Convert to LangGraph tool."""
                # Implementation here
                pass

            def to_autogen_function(self):
                """Convert to AutoGen function."""
                return {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.input_schema
                }

        return UniversalToolImpl()

    return decorator

# Usage example
@universal_tool(
    name="web_search",
    category="search",
    description="Search the web for information",
    input_schema={"query": "string", "max_results": "integer"},
    output_schema={"results": "array"}
)
async def web_search(query: str, max_results: int = 10) -> StepResult:
    """Actual search implementation."""
    # Implementation
    return StepResult.ok(result={"results": []})
```

### Pattern 2: Routing Strategy Factory

```python
"""Factory for creating routing strategies."""

from typing import Protocol, runtime_checkable
from enum import Enum

class RoutingStrategy(Enum):
    """Available routing strategies."""
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    BANDIT = "bandit"
    LEAST_LOADED = "least_loaded"
    COST_AWARE = "cost_aware"

@runtime_checkable
class Router(Protocol):
    """Router protocol."""

    async def select(self, context: dict) -> Any:
        """Select backend."""
        ...

class RouterFactory:
    """Factory for creating routers."""

    @staticmethod
    def create(
        strategy: RoutingStrategy,
        backends: list,
        **kwargs
    ) -> Router:
        """Create a router."""

        if strategy == RoutingStrategy.RANDOM:
            from core.routing.strategies.random import RandomRouter
            return RandomRouter(backends)

        elif strategy == RoutingStrategy.BANDIT:
            from core.routing.strategies.bandit import BanditRouter
            return BanditRouter(backends, **kwargs)

        # Add more strategies...

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

# Usage
router = RouterFactory.create(
    RoutingStrategy.BANDIT,
    backends=["gpt-4", "claude-3", "gemini-pro"],
    exploration_factor=0.1
)

selection = await router.select({"task_type": "analysis"})
```

### Pattern 3: Framework Adapter Registry

```python
"""Registry pattern for framework adapters."""

from typing import Optional
from core.singleton import Singleton

class FrameworkRegistry(metaclass=Singleton):
    """Global registry for framework adapters."""

    def __init__(self):
        self._adapters = {}

    def register(self, name: str, adapter):
        """Register a framework adapter."""
        self._adapters[name] = adapter

    def get(self, name: str) -> Optional[Any]:
        """Get a framework adapter."""
        return self._adapters.get(name)

    def list_frameworks(self) -> list[str]:
        """List registered frameworks."""
        return list(self._adapters.keys())

# Global instance
registry = FrameworkRegistry()

# Register frameworks at startup
def register_frameworks():
    """Register all framework adapters."""
    from ai.frameworks.crewai_adapter import CrewAIAdapter
    from ai.frameworks.langgraph_adapter import LangGraphAdapter
    from ai.frameworks.autogen_adapter import AutoGenAdapter

    registry.register("crewai", CrewAIAdapter())
    registry.register("langgraph", LangGraphAdapter())
    registry.register("autogen", AutoGenAdapter())

# Usage
framework = registry.get("crewai")
result = await framework.execute_task(task)
```

---

## 🔧 Migration Checklist

### Before Starting

- [ ] Create feature branch: `git checkout -b refactor/phase1-consolidation`
- [ ] Backup current state: `git tag backup-pre-refactor-$(date +%Y%m%d)`
- [ ] Run full test suite: `make test`
- [ ] Document baseline metrics: `make metrics-baseline`

### During Migration

- [ ] Update imports incrementally
- [ ] Run tests after each change
- [ ] Update documentation as you go
- [ ] Add deprecation warnings to old code
- [ ] Keep old code for rollback (mark as .DEPRECATED)

### After Migration

- [ ] Run full test suite
- [ ] Compare metrics to baseline
- [ ] Update all documentation
- [ ] Create migration guide
- [ ] Train team on new patterns

---

## 🧪 Testing Strategy

### Unit Tests

```python
"""Example unit test for unified crew executor."""

import pytest
from ultimate_discord_intelligence_bot.crew_core import (
    UnifiedCrewExecutor,
    CrewTask,
    CrewConfig
)

@pytest.mark.asyncio
async def test_crew_executor_validation():
    """Test task validation."""

    config = CrewConfig(tenant_id="test")
    executor = UnifiedCrewExecutor(config)

    # Invalid task (no ID)
    task = CrewTask(
        task_id="",
        task_type="analysis",
        description="Test",
        inputs={},
        agent_requirements=[],
        tool_requirements=[]
    )

    result = await executor.validate_task(task)
    assert not result.success

@pytest.mark.asyncio
async def test_crew_executor_execution():
    """Test task execution."""

    config = CrewConfig(tenant_id="test", max_retries=1)
    executor = UnifiedCrewExecutor(config)

    task = CrewTask(
        task_id="test-1",
        task_type="analysis",
        description="Test analysis",
        inputs={"content": "test"},
        agent_requirements=["analyst"],
        tool_requirements=["search"]
    )

    result = await executor.execute(task, config)
    # Add assertions based on expected behavior
```

### Integration Tests

```python
"""Integration test for orchestration facade."""

import pytest
from core.orchestration import (
    get_orchestration_facade,
    OrchestrationContext,
    OrchestrationLayer
)

@pytest.mark.asyncio
async def test_orchestration_facade_registration():
    """Test orchestrator registration."""

    facade = get_orchestration_facade()

    # Create mock orchestrator
    from core.orchestration.domain.content_orchestrator import ContentOrchestrator
    orchestrator = ContentOrchestrator()

    # Register
    facade.register(orchestrator)

    # Retrieve
    retrieved = facade.get(OrchestrationLayer.DOMAIN, "content")
    assert retrieved is not None

@pytest.mark.asyncio
async def test_orchestration_execution():
    """Test orchestration execution."""

    facade = get_orchestration_facade()
    context = OrchestrationContext(
        tenant_id="test",
        request_id="req-123",
        metadata={}
    )

    result = await facade.orchestrate(
        OrchestrationLayer.DOMAIN,
        "content",
        context,
        url="https://example.com/video"
    )

    assert result.success
```

---

## 📊 Metrics to Track

### Code Metrics

```python
# scripts/track_refactoring_metrics.py

import subprocess
from pathlib import Path

def count_files(pattern: str) -> int:
    """Count files matching pattern."""
    cmd = f"fd -e py {pattern} src/ | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def count_lines(pattern: str) -> int:
    """Count lines in files matching pattern."""
    cmd = f"fd -e py {pattern} src/ -x wc -l | tail -1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return int(result.stdout.strip().split()[0])

# Track metrics
metrics = {
    "crew_files": count_files("crew"),
    "orchestrator_classes": subprocess.run(
        "rg 'class.*Orchestrator' src/ -t py | wc -l",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip(),
    "routing_functions": subprocess.run(
        "rg 'def.*route' src/ -t py | wc -l",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip(),
    "total_python_files": count_files(""),
    "total_lines_of_code": count_lines("")
}

print("Refactoring Metrics:")
print(f"Crew files: {metrics['crew_files']}")
print(f"Orchestrator classes: {metrics['orchestrator_classes']}")
print(f"Routing functions: {metrics['routing_functions']}")
print(f"Total Python files: {metrics['total_python_files']}")
print(f"Total LOC: {metrics['total_lines_of_code']}")
```

---

## 🎯 Success Indicators

### Week 1 Success

- [ ] Crew core package created
- [ ] At least 2 crew files consolidated
- [ ] All tests passing
- [ ] <10% performance regression

### Week 2 Success

- [ ] Orchestration hierarchy established
- [ ] At least 3 orchestrators migrated
- [ ] Performance analytics moved
- [ ] Documentation updated

### Week 3 Success

- [ ] Phase 1 complete
- [ ] 30% reduction in files
- [ ] All tests passing
- [ ] Migration guide published

---

**Remember**:

- Make small, incremental changes
- Test continuously
- Document as you go
- Keep communication open with the team
- Don't be afraid to ask for help or feedback

**Next Steps**: See `STRATEGIC_REFACTORING_PLAN_2025.md` for full roadmap and Phase 2+ details.
