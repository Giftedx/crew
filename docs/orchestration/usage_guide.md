# Orchestration Framework - Usage Guide

**Version**: 1.0  
**Last Updated**: October 31, 2025  
**Phase**: 1.2 Complete ✅  
**Status**: Production Ready

---

## 🚀 Quick Navigation

**New to orchestration?** → Start with [Quick Start](#quick-start)  
**Migrating an orchestrator?** → Jump to [Migration Patterns](#migration-patterns)  
**Need API reference?** → See [API Reference](#api-reference)  
**Stuck on an error?** → Check [Troubleshooting](#troubleshooting)  
**Want to understand layers?** → Read [Layer Assignment Guide](#layer-assignment-guide)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Layer Assignment Guide](#layer-assignment-guide)
4. [Migration Patterns](#migration-patterns)
   - [Domain Pattern](#domain-pattern-stateless-business-logic)
   - [Infrastructure Pattern](#infrastructure-pattern-background-tasks--lifecycle)
   - [Application Pattern](#application-pattern-lazy-dependencies--coordination)
5. [Best Practices](#best-practices)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Examples & Resources](#examples--resources)

---

## Introduction

### What is the Orchestration Framework?

The orchestration framework is a unified, hierarchical system for managing complex coordination logic across the Discord Intelligence Bot. It consolidates 16+ scattered orchestrator classes into a clean, three-layer architecture.

### Why Was It Created?

**Problem**: Orchestrators were scattered across the codebase with:

- No clear hierarchy or organization
- Overlapping responsibilities
- Inconsistent patterns
- Difficult to discover and maintain

**Solution**: Unified orchestration framework with:

- Three clear layers (domain, application, infrastructure)
- Consistent patterns and protocols
- Centralized discovery and lifecycle management
- Production-ready observability

### Key Benefits

✅ **Consistency** - All orchestrators follow same patterns  
✅ **Discoverability** - Centralized registration and lookup  
✅ **Observability** - Built-in structured logging and metrics  
✅ **Lifecycle Management** - Proper initialization and cleanup  
✅ **Type Safety** - Protocol-based design with type hints  
✅ **Testability** - Clean separation of concerns

---

## Quick Start

### 5-Minute Path to Your First Orchestrator

#### Step 1: Choose Your Layer

Ask yourself: What does my orchestrator do?

- **Business logic/workflow** → `DOMAIN` layer
- **Cross-component coordination** → `APPLICATION` layer
- **Infrastructure concerns** → `INFRASTRUCTURE` layer

See [Layer Assignment Guide](#layer-assignment-guide) for details.

#### Step 2: Create Your Orchestrator

```python
from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

class MyOrchestrator(BaseOrchestrator):
    """My awesome orchestrator."""
    
    def __init__(self):
        super().__init__(
            layer=OrchestrationLayer.DOMAIN,  # Choose appropriate layer
            name="my_orchestrator",  # Unique name
            orchestration_type=OrchestrationType.SEQUENTIAL,  # Choose type
        )
        # Your initialization here
    
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs,
    ) -> StepResult:
        """Execute orchestration logic."""
        self._log_orchestration_start(context, **kwargs)
        
        # Your orchestration logic here
        result_data = {"status": "success", "message": "Hello, World!"}
        
        result = StepResult.ok(result=result_data)
        self._log_orchestration_end(context, result)
        return result
    
    async def cleanup(self) -> None:
        """Clean up resources (optional)."""
        pass
```

#### Step 3: Register and Use

```python
from core.orchestration import get_orchestration_facade

# Create instance
orchestrator = MyOrchestrator()

# Register with facade
facade = get_orchestration_facade()
facade.register(orchestrator)

# Use it
context = OrchestrationContext(
    tenant_id="my-tenant",
    request_id="req-123",
    metadata={"source": "discord"},
)

result = await facade.orchestrate("my_orchestrator", context)
print(f"Result: {result.data}")
```

**That's it!** You've created a production-ready orchestrator.

---

## Layer Assignment Guide

### Decision Tree

```
┌─────────────────────────────────────────────────────┐
│ What does your orchestrator primarily manage?       │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  Infrastructure?  Coordination?  Business Logic?
        │               │               │
        ▼               ▼               ▼
  INFRASTRUCTURE   APPLICATION      DOMAIN
        │               │               │
        ▼               ▼               ▼
   Resilience      Feedback Hub    Workflows
   Monitoring      State Mgmt      Analysis
   Health          Multi-comp      Task Execution
   Telemetry       Routing         Fallback Logic
```

### Layer Definitions

#### DOMAIN Layer

**Purpose**: Business logic and workflow orchestration

**Use When**:

- Orchestrating business workflows
- Coordinating task execution
- Implementing fallback strategies
- Managing analysis pipelines

**Characteristics**:

- Often stateless
- Focused on "what to do" not "how to do it"
- Business domain concepts
- Relatively simple lifecycle

**Examples**:

- `FallbackAutonomousOrchestrator` - Fallback analysis workflow
- `EnhancedAutonomousOrchestrator` - Enhanced autonomous features
- `HierarchicalOrchestrator` - Hierarchical task coordination

**Pattern**: [Domain Pattern](#domain-pattern-stateless-business-logic)

#### APPLICATION Layer

**Purpose**: Cross-component coordination and state management

**Use When**:

- Coordinating multiple subsystems
- Managing feedback loops across components
- Routing signals between systems
- Maintaining application-wide state

**Characteristics**:

- Manages component interactions
- Often has lazy-loaded dependencies
- Coordination-focused
- May run background coordination tasks

**Examples**:

- `UnifiedFeedbackOrchestrator` - Central RL feedback hub (6 component queues, 9 dependencies)
- `AdvancedBanditsOrchestrator` - Contextual bandits routing
- `RealTimeMonitoringOrchestrator` - Cross-system monitoring

**Pattern**: [Application Pattern](#application-pattern-lazy-dependencies--coordination)

#### INFRASTRUCTURE Layer

**Purpose**: Infrastructure concerns (resilience, monitoring, lifecycle)

**Use When**:

- Managing infrastructure resilience
- Health monitoring
- Telemetry collection
- Circuit breakers and retries
- Resource lifecycle management

**Characteristics**:

- Runs background infrastructure tasks
- Manages system health
- Infrastructure-level concerns
- Complex lifecycle (start/stop/cleanup)

**Examples**:

- `ResilienceOrchestrator` - Circuit breakers, retries, adaptive routing
- `TelemetryOrchestrator` - Metrics and telemetry collection
- `SecurityOrchestrator` - Security monitoring

**Pattern**: [Infrastructure Pattern](#infrastructure-pattern-background-tasks--lifecycle)

### Orchestration Types

Available types in `OrchestrationType`:

- **SEQUENTIAL** - Execute steps in sequence
- **PARALLEL** - Execute steps in parallel
- **HIERARCHICAL** - Hierarchical coordination
- **ADAPTIVE** - Adaptive execution based on conditions
- **FEEDBACK** - Feedback-driven orchestration
- **MONITORING** - Monitoring and observability
- **COORDINATION** - Cross-component coordination (application layer)
- **LIFECYCLE** - Lifecycle management (infrastructure layer)
- **BUSINESS_LOGIC** - Business logic execution (domain layer)

---

## Migration Patterns

### Overview

We have three proven patterns from successful migrations:

1. **Domain Pattern** - Stateless business logic (FallbackAutonomousOrchestrator, 269 lines)
2. **Infrastructure Pattern** - Background tasks & lifecycle (ResilienceOrchestrator, 432 lines)
3. **Application Pattern** - Lazy dependencies & coordination (UnifiedFeedbackOrchestrator, 1,059 lines)

Each pattern is production-tested with comprehensive validation.

---

### Domain Pattern: Stateless Business Logic

**Use For**: Business workflows, task coordination, analysis pipelines

**Reference Migration**: [ORCHESTRATOR_MIGRATION_1_FALLBACK.md](../../ORCHESTRATOR_MIGRATION_1_FALLBACK.md)

#### Characteristics

- ✅ Stateless (no background tasks)
- ✅ Simple lifecycle (no cleanup needed)
- ✅ Direct parameter mapping to kwargs
- ✅ Straightforward orchestrate() implementation

#### Migration Checklist

- [ ] Identify original orchestrator file and size
- [ ] Determine caller locations
- [ ] Create new file in `src/core/orchestration/domain/`
- [ ] Inherit from `BaseOrchestrator`
- [ ] Set layer=`DOMAIN`, choose appropriate type
- [ ] Map original method to `orchestrate(context, **kwargs)`
- [ ] Extract parameters from kwargs
- [ ] Convert return value to `StepResult`
- [ ] Update callers (import changes only)
- [ ] Test import, instantiation, execution
- [ ] Mark old file as `.DEPRECATED`
- [ ] Document migration

#### Code Template

**Before** (original):

```python
class MyWorkflowOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def execute_workflow(
        self,
        interaction: Any,
        content_url: str,
        depth: str = "standard"
    ) -> None:
        """Execute the workflow."""
        # Business logic here
        result = await self._analyze(content_url, depth)
        await interaction.send(f"Analysis: {result}")
```

**After** (migrated):

```python
from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

class MyWorkflowOrchestrator(BaseOrchestrator):
    """My workflow orchestrator."""
    
    def __init__(self):
        super().__init__(
            layer=OrchestrationLayer.DOMAIN,
            name="my_workflow",
            orchestration_type=OrchestrationType.SEQUENTIAL,
        )
    
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs,
    ) -> StepResult:
        """Execute orchestration logic."""
        self._log_orchestration_start(context, **kwargs)
        
        # Extract parameters from kwargs
        interaction = kwargs.get("interaction")
        content_url = kwargs.get("content_url")
        depth = kwargs.get("depth", "standard")
        
        # Business logic (unchanged)
        result = await self._analyze(content_url, depth)
        
        # Send Discord message (unchanged)
        if interaction:
            await interaction.send(f"Analysis: {result}")
        
        # Return StepResult
        result = StepResult.ok(
            result={
                "analysis": result,
                "url": content_url,
                "depth": depth,
            }
        )
        self._log_orchestration_end(context, result)
        return result
```

**Caller Update**:

```python
# Before
from my_app.my_workflow_orchestrator import MyWorkflowOrchestrator
orch = MyWorkflowOrchestrator()
await orch.execute_workflow(interaction, url, depth="deep")

# After
from core.orchestration import get_orchestration_facade, OrchestrationContext
context = OrchestrationContext(
    tenant_id="discord",
    request_id=str(interaction.id),
    metadata={"channel": interaction.channel.id},
)
facade = get_orchestration_facade()
result = await facade.orchestrate(
    "my_workflow",
    context,
    interaction=interaction,
    content_url=url,
    depth="deep",
)
```

#### Common Pitfalls

❌ **Logging kwargs conflict**:

```python
# WRONG - 'depth' conflicts with structlog's internal 'depth' parameter
self._log_orchestration_start(context, **kwargs)  # if kwargs has 'depth'
```

✅ **Solution**: BaseOrchestrator already filters kwargs automatically (fixed in protocols.py)

---

### Infrastructure Pattern: Background Tasks & Lifecycle

**Use For**: Resilience, monitoring, health checks, telemetry

**Reference Migration**: [ORCHESTRATOR_MIGRATION_2_RESILIENCE.md](../../ORCHESTRATOR_MIGRATION_2_RESILIENCE.md)

#### Characteristics

- ✅ Runs background async tasks
- ✅ Complex lifecycle (start/stop/cleanup)
- ✅ Uses `asyncio.Event` for graceful shutdown
- ✅ Lazy task initialization (not in `__init__`)
- ✅ Timeout protection in cleanup

#### Migration Checklist

- [ ] Identify background tasks in original orchestrator
- [ ] Create new file in `src/core/orchestration/infrastructure/`
- [ ] Inherit from `BaseOrchestrator`
- [ ] Set layer=`INFRASTRUCTURE`, choose appropriate type
- [ ] Add `_shutdown_event = asyncio.Event()`
- [ ] Create lazy task initialization helper
- [ ] Implement background task loops with shutdown checks
- [ ] Implement proper cleanup with timeout
- [ ] Update `orchestrate()` to start tasks lazily
- [ ] Update callers
- [ ] Test lifecycle (start → orchestrate → cleanup)
- [ ] Mark old file as `.DEPRECATED`
- [ ] Document migration

#### Code Template

**Before** (original):

```python
class MyMonitoringOrchestrator:
    def __init__(self):
        self._health_data = {}
        # START TASKS IN __init__ - WRONG!
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """Background monitoring task."""
        while True:  # Infinite loop - no shutdown mechanism!
            await self._check_health()
            await asyncio.sleep(60)
    
    async def execute_with_monitoring(self, func, *args):
        """Execute with monitoring."""
        return await func(*args)
```

**After** (migrated):

```python
from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult
import asyncio

class MyMonitoringOrchestrator(BaseOrchestrator):
    """My monitoring orchestrator."""
    
    def __init__(self):
        super().__init__(
            layer=OrchestrationLayer.INFRASTRUCTURE,
            name="my_monitoring",
            orchestration_type=OrchestrationType.MONITORING,
        )
        self._health_data = {}
        self._shutdown_event = asyncio.Event()
        self._monitoring_task = None
        self._monitoring_started = False
    
    def _start_monitoring(self) -> None:
        """Start background monitoring (lazy initialization)."""
        if self._monitoring_started:
            return
        
        try:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._monitoring_started = True
        except RuntimeError:
            # No event loop yet - will start on first orchestrate() call
            pass
    
    async def _monitoring_loop(self):
        """Background monitoring task with graceful shutdown."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_health()
                # Wait with timeout to check shutdown frequently
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=60.0,
                )
            except asyncio.TimeoutError:
                continue  # Normal - just continue monitoring
            except Exception as e:
                self.logger.error("monitoring_error", error=str(e))
    
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs,
    ) -> StepResult:
        """Execute with monitoring."""
        # Start monitoring on first call
        if not self._monitoring_started:
            self._start_monitoring()
        
        self._log_orchestration_start(context, **kwargs)
        
        operation = kwargs.get("operation", "execute")
        
        if operation == "execute":
            func = kwargs.get("func")
            args = kwargs.get("args", ())
            result_value = await func(*args)
            result = StepResult.ok(result={"value": result_value})
        elif operation == "get_health":
            result = StepResult.ok(result=self._health_data)
        else:
            result = StepResult.fail(
                f"Unknown operation: {operation}",
                error_category=ErrorCategory.VALIDATION,
            )
        
        self._log_orchestration_end(context, result)
        return result
    
    async def cleanup(self) -> None:
        """Clean shutdown with timeout protection."""
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for task to complete (with timeout)
        if self._monitoring_task and not self._monitoring_task.done():
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
```

#### Common Pitfalls

❌ **Starting tasks in `__init__`**:

```python
def __init__(self):
    asyncio.create_task(self._background_loop())  # RuntimeError: no event loop!
```

✅ **Solution**: Lazy initialization in `orchestrate()` or create helper

❌ **No shutdown mechanism**:

```python
async def _background_loop(self):
    while True:  # Infinite loop!
        await self._work()
```

✅ **Solution**: Use `asyncio.Event` and check `while not self._shutdown_event.is_set()`

❌ **No cleanup timeout**:

```python
async def cleanup(self):
    await self._task  # Could hang forever!
```

✅ **Solution**: Use `asyncio.wait_for(self._task, timeout=5.0)` with cancel fallback

---

### Application Pattern: Lazy Dependencies & Coordination

**Use For**: Cross-component coordination, feedback routing, state management

**Reference Migration**: [ORCHESTRATOR_MIGRATION_3_UNIFIED_FEEDBACK.md](../../ORCHESTRATOR_MIGRATION_3_UNIFIED_FEEDBACK.md)

#### Characteristics

- ✅ Coordinates multiple components/subsystems
- ✅ Lazy-loaded dependencies (9+ dependencies common)
- ✅ Background coordination tasks
- ✅ Operation routing through single `orchestrate()` method
- ✅ Queue-based or event-based coordination
- ✅ Backward compatibility via aliases and dual-access

#### Migration Checklist

- [ ] Identify all dependencies (routers, managers, coordinators)
- [ ] Map component interactions and queues
- [ ] Create new file in `src/core/orchestration/application/`
- [ ] Inherit from `BaseOrchestrator`
- [ ] Set layer=`APPLICATION`, type=`COORDINATION`
- [ ] Initialize dependencies as `None` (lazy load)
- [ ] Create lazy getter methods for each dependency
- [ ] Implement operation routing in `orchestrate()`
- [ ] Preserve backward compatibility (aliases, singleton accessor)
- [ ] Update callers (minimal changes)
- [ ] Test all operations
- [ ] Mark old file as `.DEPRECATED`
- [ ] Document migration

#### Code Template

**Before** (original):

```python
class MyCoordinationOrchestrator:
    def __init__(self, router_a=None, router_b=None, manager=None):
        # Dependencies injected or loaded immediately
        from my_app.router_a import get_router_a
        from my_app.router_b import get_router_b
        from my_app.manager import get_manager
        
        self._router_a = router_a or get_router_a()
        self._router_b = router_b or get_router_b()
        self._manager = manager or get_manager()
        
        self._queues = {"a": deque(), "b": deque()}
        
        # Global singleton
        global _instance
        _instance = self
    
    def start(self):
        """Start background tasks."""
        asyncio.create_task(self._processing_loop())
    
    def submit_signal(self, component, data):
        """Submit a signal."""
        self._queues[component].append(data)
    
    def get_metrics(self):
        """Get metrics."""
        return {"signals": len(self._queues["a"]) + len(self._queues["b"])}

# Global singleton accessor
def get_orchestrator():
    return _instance
```

**After** (migrated):

```python
from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)
from ultimate_discord_intelligence_bot.step_result import StepResult
from collections import deque
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from my_app.router_a import RouterA
    from my_app.router_b import RouterB
    from my_app.manager import Manager

class MyCoordinationOrchestrator(BaseOrchestrator):
    """My coordination orchestrator."""
    
    def __init__(
        self,
        router_a: "RouterA | None" = None,
        router_b: "RouterB | None" = None,
        manager: "Manager | None" = None,
    ):
        super().__init__(
            layer=OrchestrationLayer.APPLICATION,
            name="my_coordination",
            orchestration_type=OrchestrationType.COORDINATION,
        )
        
        # Lazy-loaded dependencies (stored as None)
        self._router_a = router_a
        self._router_b = router_b
        self._manager = manager
        
        self._queues = {"a": deque(), "b": deque()}
        self._shutdown_event = asyncio.Event()
        self._tasks_started = False
    
    # Lazy getters for dependencies
    @property
    def router_a(self) -> "RouterA":
        if self._router_a is None:
            from my_app.router_a import get_router_a
            self._router_a = get_router_a()
        return self._router_a
    
    @property
    def router_b(self) -> "RouterB":
        if self._router_b is None:
            from my_app.router_b import get_router_b
            self._router_b = get_router_b()
        return self._router_b
    
    @property
    def manager(self) -> "Manager":
        if self._manager is None:
            from my_app.manager import get_manager
            self._manager = get_manager()
        return self._manager
    
    def _start_background_tasks(self) -> None:
        """Start background processing tasks (lazy initialization)."""
        if self._tasks_started:
            return
        try:
            asyncio.create_task(self._processing_loop())
            self._tasks_started = True
        except RuntimeError:
            pass  # Will start on first orchestrate() call
    
    async def _processing_loop(self):
        """Background processing with shutdown support."""
        while not self._shutdown_event.is_set():
            # Process queues
            for component, queue in self._queues.items():
                while queue:
                    signal = queue.popleft()
                    await self._process_signal(component, signal)
            
            await asyncio.sleep(1)
    
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs,
    ) -> StepResult:
        """Unified entry point with operation routing."""
        # Start background tasks on first call
        if not self._tasks_started:
            self._start_background_tasks()
        
        self._log_orchestration_start(context, **kwargs)
        
        # Operation routing
        operation = kwargs.get("operation", "submit_signal")
        
        if operation == "submit_signal":
            component = kwargs.get("component")
            data = kwargs.get("data")
            self._queues[component].append(data)
            result = StepResult.ok(result={"queued": True})
        
        elif operation == "get_metrics":
            metrics = {
                "signals": sum(len(q) for q in self._queues.values()),
                "queue_a": len(self._queues["a"]),
                "queue_b": len(self._queues["b"]),
            }
            result = StepResult.ok(result=metrics)
        
        elif operation == "start":
            self._start_background_tasks()
            result = StepResult.ok(result={"status": "started"})
        
        elif operation == "stop":
            self._shutdown_event.set()
            result = StepResult.ok(result={"status": "stopped"})
        
        else:
            result = StepResult.fail(
                f"Unknown operation: {operation}",
                error_category=ErrorCategory.VALIDATION,
            )
        
        self._log_orchestration_end(context, result)
        return result
    
    async def cleanup(self) -> None:
        """Clean shutdown."""
        self._shutdown_event.set()
        # Wait for tasks with timeout (similar to infrastructure pattern)

# Backward compatibility: singleton accessor
_global_orchestrator: MyCoordinationOrchestrator | None = None

def get_orchestrator(auto_create: bool = False) -> MyCoordinationOrchestrator | None:
    """Get global orchestrator instance (backward compatibility)."""
    global _global_orchestrator
    if _global_orchestrator is None and auto_create:
        _global_orchestrator = MyCoordinationOrchestrator()
    return _global_orchestrator

def set_orchestrator(orchestrator: MyCoordinationOrchestrator) -> None:
    """Set global orchestrator instance (backward compatibility)."""
    global _global_orchestrator
    _global_orchestrator = orchestrator
```

**Caller Update** (minimal changes):

```python
# Before
from my_app.my_coordination import get_orchestrator
orch = get_orchestrator()
orch.start()
orch.submit_signal("a", {"value": 42})
metrics = orch.get_metrics()

# After (Option 1: Backward compatible - just update import)
from core.orchestration.application import get_orchestrator
orch = get_orchestrator(auto_create=True)
orch.start()  # Still works!
orch.submit_signal("a", {"value": 42})  # Still works!
metrics = orch.get_metrics()  # Still works!

# After (Option 2: Use facade - recommended for new code)
from core.orchestration import get_orchestration_facade, OrchestrationContext
facade = get_orchestration_facade()
context = OrchestrationContext(tenant_id="app", request_id="req-1", metadata={})

await facade.orchestrate("my_coordination", context, operation="start")
await facade.orchestrate("my_coordination", context, operation="submit_signal", component="a", data={"value": 42})
metrics_result = await facade.orchestrate("my_coordination", context, operation="get_metrics")
metrics = metrics_result.data
```

#### Common Pitfalls

❌ **Eager dependency loading**:

```python
def __init__(self):
    from heavy_module import HeavyRouter  # Loads immediately!
    self._router = HeavyRouter()
```

✅ **Solution**: Lazy load via property or getter method

❌ **No operation routing**:

```python
# Multiple methods instead of unified orchestrate()
async def submit_signal(self, ...): ...
async def get_metrics(self): ...
async def start(self): ...
```

✅ **Solution**: Single `orchestrate()` with `operation` parameter routing

❌ **Breaking backward compatibility**:

```python
# Removing old methods completely
# Old code: orch.submit_signal("a", data)
# New code: No equivalent!
```

✅ **Solution**: Keep old methods as wrappers or maintain singleton accessor pattern

---

## Best Practices

### From 3 Production Migrations

#### 1. Lazy Initialization for Async Tasks

**Principle**: Never call `asyncio.create_task()` in `__init__`

```python
class MyOrchestrator(BaseOrchestrator):
    def __init__(self):
        super().__init__(...)
        self._task_started = False
    
    def _start_task(self) -> None:
        if self._task_started:
            return
        try:
            asyncio.create_task(self._background_loop())
            self._task_started = True
        except RuntimeError:
            pass  # Will start on first orchestrate() call
    
    async def orchestrate(self, context, **kwargs):
        if not self._task_started:
            self._start_task()
        # ... rest of logic
```

#### 2. Graceful Shutdown with Events

**Principle**: Use `asyncio.Event` for coordinated shutdown

```python
class MyOrchestrator(BaseOrchestrator):
    def __init__(self):
        super().__init__(...)
        self._shutdown_event = asyncio.Event()
    
    async def _background_loop(self):
        while not self._shutdown_event.is_set():
            # Do work
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                continue
    
    async def cleanup(self):
        self._shutdown_event.set()
        # Wait for tasks with timeout
```

#### 3. Cleanup with Timeout Protection

**Principle**: Always add timeout when waiting for task cleanup

```python
async def cleanup(self) -> None:
    self._shutdown_event.set()
    
    if self._task and not self._task.done():
        try:
            await asyncio.wait_for(self._task, timeout=5.0)
        except asyncio.TimeoutError:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
```

#### 4. Backward Compatibility Strategies

**Principle**: Preserve existing APIs during migration

**Strategy A**: Keep old methods as wrappers

```python
async def orchestrate(self, context, **kwargs):
    operation = kwargs.get("operation")
    # New unified logic
    ...

# Backward compatibility wrapper
async def execute_workflow(self, url, depth="standard"):
    """Legacy method for backward compatibility."""
    context = OrchestrationContext(
        tenant_id="legacy",
        request_id=str(uuid.uuid4()),
        metadata={},
    )
    return await self.orchestrate(
        context,
        operation="execute_workflow",
        url=url,
        depth=depth,
    )
```

**Strategy B**: Singleton accessor pattern

```python
# In module
_global_instance = None

def get_orchestrator():
    return _global_instance

# Old code still works
from my_module import get_orchestrator
orch = get_orchestrator()
```

#### 5. Operation Routing Pattern

**Principle**: Single `orchestrate()` method routes to multiple operations

```python
async def orchestrate(self, context, **kwargs):
    operation = kwargs.get("operation", "default")
    
    if operation == "execute":
        return await self._execute(context, **kwargs)
    elif operation == "get_status":
        return await self._get_status(context, **kwargs)
    elif operation == "start":
        return await self._start(context, **kwargs)
    else:
        return StepResult.fail(
            f"Unknown operation: {operation}",
            error_category=ErrorCategory.VALIDATION,
        )
```

#### 6. Lazy Dependency Injection

**Principle**: Accept dependencies as optional, load on-demand

```python
def __init__(self, router=None, manager=None):
    super().__init__(...)
    self._router = router  # May be None
    self._manager = manager  # May be None

@property
def router(self):
    if self._router is None:
        from my_app.router import get_router
        self._router = get_router()
    return self._router
```

#### 7. Structured Logging Best Practices

**Principle**: Let BaseOrchestrator handle logging, avoid kwargs conflicts

```python
async def orchestrate(self, context, **kwargs):
    # BaseOrchestrator automatically filters conflicting kwargs
    self._log_orchestration_start(context, **kwargs)
    
    # Your logic
    result = StepResult.ok(result={...})
    
    self._log_orchestration_end(context, result)
    return result
```

#### 8. Testing Strategy

**Principle**: Test in layers: import → instantiate → register → execute → cleanup

```python
# Test 1: Import
from core.orchestration.domain import MyOrchestrator
print("✅ Import successful")

# Test 2: Instantiate
orch = MyOrchestrator()
print(f"✅ Instantiated: {orch.name}, {orch.layer}")

# Test 3: Register
facade = get_orchestration_facade()
facade.register(orch)
print("✅ Registered with facade")

# Test 4: Execute
context = OrchestrationContext(tenant_id="test", request_id="test-1", metadata={})
result = await facade.orchestrate("my_orchestrator", context)
print(f"✅ Executed: {result.success}")

# Test 5: Cleanup
await orch.cleanup()
print("✅ Cleanup successful")
```

---

## API Reference

### BaseOrchestrator

Base class for all orchestrators.

```python
class BaseOrchestrator(ABC):
    def __init__(
        self,
        layer: OrchestrationLayer,
        name: str,
        orchestration_type: OrchestrationType,
    ):
        """Initialize orchestrator.
        
        Args:
            layer: Orchestration layer (DOMAIN, APPLICATION, INFRASTRUCTURE)
            name: Unique orchestrator name
            orchestration_type: Type of orchestration
        """
    
    @property
    def layer(self) -> OrchestrationLayer:
        """Get orchestration layer."""
    
    @property
    def name(self) -> str:
        """Get orchestrator name."""
    
    @property
    def orchestration_type(self) -> OrchestrationType:
        """Get orchestration type."""
    
    @abstractmethod
    async def orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs: Any,
    ) -> StepResult:
        """Execute orchestration logic.
        
        Args:
            context: Orchestration context
            **kwargs: Operation-specific parameters
            
        Returns:
            StepResult with execution outcome
        """
    
    async def can_orchestrate(
        self,
        context: OrchestrationContext,
        **kwargs: Any,
    ) -> bool:
        """Check if can orchestrate (optional override).
        
        Returns:
            True if can orchestrate, False otherwise
        """
    
    async def cleanup(self) -> None:
        """Clean up resources (optional override)."""
    
    def _log_orchestration_start(
        self,
        context: OrchestrationContext,
        **kwargs: Any,
    ) -> None:
        """Log orchestration start (use in orchestrate())."""
    
    def _log_orchestration_end(
        self,
        context: OrchestrationContext,
        result: StepResult,
    ) -> None:
        """Log orchestration end (use in orchestrate())."""
```

### OrchestrationContext

Shared context for orchestration execution.

```python
@dataclass
class OrchestrationContext:
    tenant_id: str  # Tenant identifier
    request_id: str  # Request identifier
    metadata: dict[str, Any]  # Additional metadata
    trace_id: str | None = None  # Trace ID for distributed tracing
    parent_orchestrator: str | None = None  # Parent orchestrator name
    orchestration_depth: int = 0  # Depth in hierarchy
    
    def create_child_context(self, parent_name: str) -> "OrchestrationContext":
        """Create child context for nested orchestration.
        
        Args:
            parent_name: Parent orchestrator name
            
        Returns:
            New context with incremented depth
        """
```

### OrchestrationFacade

Unified entry point for all orchestration.

```python
class OrchestrationFacade:
    def register(self, orchestrator: OrchestratorProtocol) -> None:
        """Register an orchestrator.
        
        Args:
            orchestrator: Orchestrator instance
            
        Raises:
            ValueError: If orchestrator with same name already registered
        """
    
    def unregister(self, name: str) -> None:
        """Unregister an orchestrator.
        
        Args:
            name: Orchestrator name
            
        Raises:
            ValueError: If orchestrator not found
        """
    
    def get(self, name: str) -> OrchestratorProtocol | None:
        """Get orchestrator by name.
        
        Args:
            name: Orchestrator name
            
        Returns:
            Orchestrator instance or None if not found
        """
    
    def get_by_layer(
        self,
        layer: OrchestrationLayer,
    ) -> Sequence[OrchestratorProtocol]:
        """Get all orchestrators in a layer.
        
        Args:
            layer: Orchestration layer
            
        Returns:
            List of orchestrators in layer
        """
    
    async def orchestrate(
        self,
        orchestrator_name: str,
        context: OrchestrationContext,
        **kwargs: Any,
    ) -> StepResult:
        """Execute orchestration via facade.
        
        Args:
            orchestrator_name: Name of orchestrator to execute
            context: Orchestration context
            **kwargs: Operation-specific parameters
            
        Returns:
            StepResult from orchestration
        """
    
    def list_orchestrators(self) -> dict[str, dict]:
        """List all registered orchestrators.
        
        Returns:
            Dict mapping name to orchestrator info
        """

# Global facade instance
def get_orchestration_facade() -> OrchestrationFacade:
    """Get the global orchestration facade."""
```

### Enums

```python
class OrchestrationLayer(Enum):
    """Orchestration layers."""
    DOMAIN = "domain"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"

class OrchestrationType(Enum):
    """Orchestration types."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"
    FEEDBACK = "feedback"
    MONITORING = "monitoring"
    COORDINATION = "coordination"
    LIFECYCLE = "lifecycle"
    BUSINESS_LOGIC = "business_logic"
```

---

## Troubleshooting

### Common Errors & Solutions

#### RuntimeError: no running event loop

**Error**:

```
RuntimeError: no running event loop
RuntimeWarning: coroutine 'MyOrchestrator._background_loop' was never awaited
```

**Cause**: Trying to create async tasks in `__init__` when no event loop is running

**Solution**: Use lazy initialization pattern

```python
def __init__(self):
    super().__init__(...)
    self._task_started = False

def _start_task(self):
    if self._task_started:
        return
    try:
        asyncio.create_task(self._background_loop())
        self._task_started = True
    except RuntimeError:
        pass  # Will start on first orchestrate() call

async def orchestrate(self, context, **kwargs):
    if not self._task_started:
        self._start_task()
    # ...
```

#### TypeError: got multiple values for keyword argument

**Error**:

```
TypeError: got multiple values for keyword argument 'depth'
```

**Cause**: Parameter name in kwargs conflicts with structlog's internal parameters (depth, event, level, etc.)

**Solution**: BaseOrchestrator automatically filters conflicting kwargs in logging. This should not occur with current implementation. If it does, update to latest protocols.py.

#### AttributeError: 'OrchestrationType' has no attribute 'XXX'

**Error**:

```
AttributeError: 'OrchestrationType' has no attribute 'COORDINATION'
```

**Cause**: Using orchestration type that doesn't exist in enum

**Solution**: Check available types in `OrchestrationType` enum or add new type if needed:

```python
# In src/core/orchestration/protocols.py
class OrchestrationType(Enum):
    # ... existing types
    YOUR_NEW_TYPE = "your_new_type"
```

#### ValueError: Orchestrator 'XXX' not found

**Error**:

```
ValueError: Orchestrator 'my_orchestrator' not found in facade
```

**Cause**: Orchestrator not registered with facade before use

**Solution**: Register orchestrator before calling it

```python
orch = MyOrchestrator()
facade = get_orchestration_facade()
facade.register(orch)  # Don't forget this!
await facade.orchestrate("my_orchestrator", context)
```

#### Tasks Never Complete / Memory Leaks

**Symptom**: Background tasks continue running after orchestrator should stop

**Cause**: No graceful shutdown mechanism

**Solution**: Implement proper cleanup with shutdown event

```python
def __init__(self):
    self._shutdown_event = asyncio.Event()

async def _background_loop(self):
    while not self._shutdown_event.is_set():
        # Work
        try:
            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            continue

async def cleanup(self):
    self._shutdown_event.set()
    # Wait with timeout
```

---

## Examples & Resources

### Live Examples

All migration patterns are documented with real production examples:

1. **Domain Pattern** - [ORCHESTRATOR_MIGRATION_1_FALLBACK.md](../../ORCHESTRATOR_MIGRATION_1_FALLBACK.md)
   - FallbackAutonomousOrchestrator (269 lines)
   - Stateless workflow orchestration
   - Before/after code comparison
   - Complete validation results

2. **Infrastructure Pattern** - [ORCHESTRATOR_MIGRATION_2_RESILIENCE.md](../../ORCHESTRATOR_MIGRATION_2_RESILIENCE.md)
   - ResilienceOrchestrator (432 lines)
   - Background tasks and lifecycle management
   - Circuit breakers and health monitoring
   - Graceful shutdown implementation

3. **Application Pattern** - [ORCHESTRATOR_MIGRATION_3_UNIFIED_FEEDBACK.md](../../ORCHESTRATOR_MIGRATION_3_UNIFIED_FEEDBACK.md)
   - UnifiedFeedbackOrchestrator (1,059 lines)
   - Lazy dependency injection (9 dependencies)
   - Multi-component coordination (6 queues)
   - Operation routing pattern
   - Backward compatibility strategies

### Code Examples

**Example 1: Simple Domain Orchestrator**

```python
# See ORCHESTRATOR_MIGRATION_1_FALLBACK.md for complete working example
from core.orchestration import BaseOrchestrator, OrchestrationLayer
# ... implementation
```

**Example 2: Infrastructure Orchestrator with Background Tasks**

```python
# See ORCHESTRATOR_MIGRATION_2_RESILIENCE.md for complete working example
from core.orchestration import BaseOrchestrator, OrchestrationLayer
# ... implementation with health monitoring loop
```

**Example 3: Application Coordinator with Lazy Dependencies**

```python
# See ORCHESTRATOR_MIGRATION_3_UNIFIED_FEEDBACK.md for complete working example
from core.orchestration import BaseOrchestrator, OrchestrationLayer
# ... implementation with lazy-loaded routers and managers
```

### Test Examples

See `tests/test_core/test_orchestration/test_orchestration_core.py` for comprehensive test patterns:

- Context creation and hierarchy
- Orchestrator initialization
- Facade registration and discovery
- Execution and cleanup

### Progress Tracking

See [PHASE1_2_ORCHESTRATION_PROGRESS.md](../../PHASE1_2_ORCHESTRATION_PROGRESS.md) for:

- Overall progress (80% complete)
- Completed migrations (3/16+)
- Remaining orchestrators (13+)
- Lessons learned
- Next steps

---

## Quick Reference Card

### Layer Decision

- **DOMAIN** = Business workflows, task execution
- **APPLICATION** = Cross-component coordination
- **INFRASTRUCTURE** = Resilience, monitoring, health

### Pattern Selection

- **Simple stateless** → Domain Pattern
- **Background tasks** → Infrastructure Pattern
- **Multi-component coordination** → Application Pattern

### Migration Steps

1. Choose layer (domain/application/infrastructure)
2. Inherit from `BaseOrchestrator`
3. Map original method → `orchestrate(context, **kwargs)`
4. Implement cleanup if needed
5. Update callers (import changes)
6. Test: import → instantiate → register → execute
7. Mark old file `.DEPRECATED`
8. Document migration

### Common Imports

```python
from core.orchestration import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
    get_orchestration_facade,
)
from ultimate_discord_intelligence_bot.step_result import StepResult, ErrorCategory
```

### Testing Template

```python
# 1. Import
from core.orchestration.{layer} import MyOrchestrator

# 2. Instantiate
orch = MyOrchestrator()

# 3. Register
facade = get_orchestration_facade()
facade.register(orch)

# 4. Execute
context = OrchestrationContext(tenant_id="test", request_id="test-1", metadata={})
result = await facade.orchestrate("my_orchestrator", context, **params)

# 5. Cleanup
await orch.cleanup()
```

---

## Version History

- **v1.0** (2024-10-31) - Initial release after Phase 1.2 completion
  - 3 production migrations validated
  - All 3 layer patterns established
  - 15/16 tests passing
  - Zero production impact

---

## Need Help?

- **Architecture questions** → See [NEXT_GENERATION_ARCHITECTURE_VISION.md](../../NEXT_GENERATION_ARCHITECTURE_VISION.md)
- **Strategic context** → See [STRATEGIC_REFACTORING_PLAN_2025.md](../../STRATEGIC_REFACTORING_PLAN_2025.md)
- **Migration examples** → See individual migration reports (ORCHESTRATOR_MIGRATION_*.md)
- **Test patterns** → See `tests/test_core/test_orchestration/`
- **Progress tracking** → See [PHASE1_2_ORCHESTRATION_PROGRESS.md](../../PHASE1_2_ORCHESTRATION_PROGRESS.md)

**Remember**: With the patterns established in this guide, migrating the remaining 13+ orchestrators should be straightforward. The framework is production-ready and waiting for your orchestrators! 🚀
