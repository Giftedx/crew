"""Unified Orchestration System - Phase 4 Implementation

This module provides a unified orchestration system that consolidates all
existing orchestrators into a single, intelligent hierarchical system with
advanced task management, dependency resolution, and performance optimization.

See ADR-0004 for architectural consolidation decisions.
"""

from .facade import (
    OrchestrationFacade,
    OrchestrationStrategy,
    get_orchestrator,
)
from .task_manager import (
    TaskDependencyResolver,
    TaskManager,
    TaskManagerConfig,
    TaskScheduler,
)
from .unified_orchestrator import (
    OrchestrationMetrics,
    TaskPriority,
    TaskRequest,
    TaskResult,
    TaskStatus,
    UnifiedOrchestrationConfig,
    UnifiedOrchestrationService,
)


__all__ = [
    # ADR-0004 Facade (recommended entry point)
    "OrchestrationFacade",
    "OrchestrationMetrics",
    "OrchestrationStrategy",
    "TaskDependencyResolver",
    # Task management
    "TaskManager",
    "TaskManagerConfig",
    "TaskPriority",
    "TaskRequest",
    "TaskResult",
    "TaskScheduler",
    "TaskStatus",
    "UnifiedOrchestrationConfig",
    # Legacy orchestration service
    "UnifiedOrchestrationService",
    "get_orchestrator",
]
