"""Unified Orchestration Service - Single hierarchical orchestrator

This service provides a unified orchestration system that consolidates all
existing orchestrators into a single, intelligent hierarchical system with
advanced task management, dependency resolution, and performance optimization.
"""

from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

try:
    from ultimate_discord_intelligence_bot.services.hierarchical_orchestrator import HierarchicalOrchestrator
except ImportError:
    HierarchicalOrchestrator = None
try:
    from ultimate_discord_intelligence_bot.enhanced_crew_integration import EnhancedCrewExecutor
except ImportError:
    EnhancedCrewExecutor = None
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskRequest:
    """Request for task execution"""

    task_id: str
    task_type: str
    payload: dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: list[str] = field(default_factory=list)
    tenant_id: str | None = None
    workspace_id: str | None = None
    timeout: int | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result from task execution"""

    task_id: str
    status: TaskStatus
    result_data: Any | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationMetrics:
    """Orchestration performance metrics"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 0.0
    active_tasks: int = 0
    queued_tasks: int = 0
    last_reset: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedOrchestrationConfig:
    """Configuration for unified orchestration service"""

    enable_hierarchical_orchestrator: bool = True
    enable_enhanced_crew_executor: bool = True
    enable_task_scheduling: bool = True
    enable_dependency_resolution: bool = True
    enable_performance_monitoring: bool = True
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    retry_delay: int = 5
    max_retries: int = 3
    metrics_collection_interval: int = 60
    task_cleanup_interval: int = 3600
    max_task_history: int = 1000


class UnifiedOrchestrationService:
    """Unified orchestration service consolidating all orchestrators"""

    def __init__(self, config: UnifiedOrchestrationConfig | None = None):
        self.config = config or UnifiedOrchestrationConfig()
        self._initialized = False
        self._hierarchical_orchestrator: Any | None = None
        self._enhanced_crew_executor: Any | None = None
        self._task_queue: dict[str, TaskRequest] = {}
        self._running_tasks: dict[str, TaskRequest] = {}
        self._completed_tasks: dict[str, TaskResult] = {}
        self._failed_tasks: dict[str, TaskResult] = {}
        self._metrics: dict[str, OrchestrationMetrics] = {}
        self._task_dependencies: dict[str, set[str]] = {}
        self._task_dependents: dict[str, set[str]] = {}
        self._background_tasks: set[asyncio.Task[Any]] = set()
        self._initialize_orchestration_components()

    def _initialize_orchestration_components(self) -> None:
        """Initialize all orchestration components"""
        try:
            if self.config.enable_hierarchical_orchestrator and HierarchicalOrchestrator:
                try:
                    self._hierarchical_orchestrator = HierarchicalOrchestrator()
                    logger.info("Hierarchical Orchestrator initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Hierarchical Orchestrator: {e}")
                    self._hierarchical_orchestrator = None
            if self.config.enable_enhanced_crew_executor and EnhancedCrewExecutor:
                try:
                    self._enhanced_crew_executor = EnhancedCrewExecutor()
                    logger.info("Enhanced Crew Executor initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Enhanced Crew Executor: {e}")
                    self._enhanced_crew_executor = None
            self._initialized = True
            logger.info(f"Unified orchestration service initialized with {self._get_active_components()} components")
        except Exception as e:
            logger.error(f"Failed to initialize unified orchestration service: {e}")
            self._initialized = False

    def _get_active_components(self) -> int:
        """Get count of active orchestration components"""
        count = 0
        if self._hierarchical_orchestrator is not None:
            count += 1
        if self._enhanced_crew_executor is not None:
            count += 1
        return count

    async def execute_task(
        self, task_request: TaskRequest, tenant_id: str | None = None, workspace_id: str | None = None
    ) -> StepResult:
        """Execute a task through the unified orchestration system"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified orchestration service not initialized")
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"
            task_request.tenant_id = tenant_id
            task_request.workspace_id = workspace_id
            if not await self._check_dependencies(task_request):
                self._task_queue[task_request.task_id] = task_request
                return StepResult.ok(
                    data={"status": "queued", "reason": "dependencies_not_satisfied", "task_id": task_request.task_id}
                )
            if len(self._running_tasks) >= self.config.max_concurrent_tasks:
                self._task_queue[task_request.task_id] = task_request
                return StepResult.ok(
                    data={
                        "status": "queued",
                        "reason": "concurrent_task_limit_reached",
                        "task_id": task_request.task_id,
                    }
                )
            result = await self._execute_task_internal(task_request)
            await self._update_task_dependencies(task_request, result)
            await self._process_queued_tasks(tenant_id, workspace_id)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f"Error in task execution: {e}", exc_info=True)
            return StepResult.fail(f"Task execution failed: {e!s}")

    async def _execute_task_internal(self, task_request: TaskRequest) -> TaskResult:
        """Internal task execution logic"""
        task_id = task_request.task_id
        start_time = datetime.now(timezone.utc)
        self._running_tasks[task_id] = task_request
        try:
            if task_request.task_type in ["crew_execution", "agent_task", "workflow"]:
                result = await self._execute_via_crew_executor(task_request)
            elif task_request.task_type in ["hierarchical", "supervisor", "worker"]:
                result = await self._execute_via_hierarchical_orchestrator(task_request)
            else:
                result = await self._execute_generic_task(task_request)
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds() * 1000
            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                result_data=result.data if result.success else None,
                error_message=result.error if not result.success else None,
                execution_time_ms=execution_time,
                started_at=start_time,
                completed_at=end_time,
                retry_count=task_request.retry_count,
                metadata={
                    "task_type": task_request.task_type,
                    "tenant_id": task_request.tenant_id,
                    "workspace_id": task_request.workspace_id,
                    "orchestrator_used": self._get_orchestrator_used(task_request),
                },
            )
            if result.success:
                self._completed_tasks[task_id] = task_result
            else:
                self._failed_tasks[task_id] = task_result
                if task_request.retry_count < task_request.max_retries:
                    await self._schedule_retry(task_request)
            return task_result
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            execution_time = (end_time - start_time).total_seconds() * 1000
            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time_ms=execution_time,
                started_at=start_time,
                completed_at=end_time,
                retry_count=task_request.retry_count,
                metadata={"error_type": type(e).__name__, "task_type": task_request.task_type},
            )
            self._failed_tasks[task_id] = task_result
            if task_request.retry_count < task_request.max_retries:
                await self._schedule_retry(task_request)
            return task_result
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            self._update_metrics(task_request.tenant_id, task_request.workspace_id, task_result)

    async def _execute_via_crew_executor(self, task_request: TaskRequest) -> StepResult:
        """Execute task via Enhanced Crew Executor"""
        try:
            if not self._enhanced_crew_executor:
                return StepResult.fail("Enhanced Crew Executor not available")
            result = await self._enhanced_crew_executor.execute_with_comprehensive_monitoring(
                inputs=task_request.payload, tenant_id=task_request.tenant_id, workspace_id=task_request.workspace_id
            )
            return result
        except Exception as e:
            return StepResult.fail(f"Crew executor execution failed: {e!s}")

    async def _execute_via_hierarchical_orchestrator(self, task_request: TaskRequest) -> StepResult:
        """Execute task via Hierarchical Orchestrator"""
        try:
            if not self._hierarchical_orchestrator:
                return StepResult.fail("Hierarchical Orchestrator not available")
            result = await self._hierarchical_orchestrator.execute_task(
                task_type=task_request.task_type,
                payload=task_request.payload,
                tenant_id=task_request.tenant_id,
                workspace_id=task_request.workspace_id,
            )
            return result
        except Exception as e:
            return StepResult.fail(f"Hierarchical orchestrator execution failed: {e!s}")

    async def _execute_generic_task(self, task_request: TaskRequest) -> StepResult:
        """Execute generic task"""
        try:
            await asyncio.sleep(0.1)
            return StepResult.ok(
                data={
                    "task_id": task_request.task_id,
                    "task_type": task_request.task_type,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "payload": task_request.payload,
                }
            )
        except Exception as e:
            return StepResult.fail(f"Generic task execution failed: {e!s}")

    async def _check_dependencies(self, task_request: TaskRequest) -> bool:
        """Check if task dependencies are satisfied"""
        try:
            if not task_request.dependencies:
                return True
            for dep_id in task_request.dependencies:
                if dep_id not in self._completed_tasks:
                    return False
                if self._completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False

    async def _update_task_dependencies(self, task_request: TaskRequest, task_result: TaskResult) -> None:
        """Update task dependencies after execution"""
        try:
            task_id = task_request.task_id
            for dep_id in task_request.dependencies:
                if dep_id not in self._task_dependents:
                    self._task_dependents[dep_id] = set()
                self._task_dependents[dep_id].add(task_id)
            if task_id in self._task_dependents:
                for dependent_id in self._task_dependents[task_id]:
                    if dependent_id in self._task_queue:
                        dependent_task = self._task_queue[dependent_id]
                        if await self._check_dependencies(dependent_task):
                            del self._task_queue[dependent_id]
                            await self._execute_task_internal(dependent_task)
        except Exception as e:
            logger.error(f"Error updating task dependencies: {e}")

    async def _process_queued_tasks(self, tenant_id: str, workspace_id: str) -> None:
        """Process queued tasks that can now be executed"""
        try:
            tasks_to_execute = []
            for task_id, task_request in list(self._task_queue.items()):
                if (
                    await self._check_dependencies(task_request)
                    and len(self._running_tasks) < self.config.max_concurrent_tasks
                ):
                    tasks_to_execute.append(task_id)
            for task_id in tasks_to_execute:
                task_request = self._task_queue.pop(task_id)
                task = asyncio.create_task(self._execute_task_internal(task_request))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
        except Exception as e:
            logger.error(f"Error processing queued tasks: {e}")

    async def _schedule_retry(self, task_request: TaskRequest) -> None:
        """Schedule task retry"""
        try:
            task_request.retry_count += 1
            await asyncio.sleep(self.config.retry_delay)
            self._task_queue[task_request.task_id] = task_request
        except Exception as e:
            logger.error(f"Error scheduling retry: {e}")

    def _get_orchestrator_used(self, task_request: TaskRequest) -> str:
        """Get the orchestrator used for task execution"""
        if task_request.task_type in ["crew_execution", "agent_task", "workflow"]:
            return "enhanced_crew_executor"
        elif task_request.task_type in ["hierarchical", "supervisor", "worker"]:
            return "hierarchical_orchestrator"
        else:
            return "generic_executor"

    def _update_metrics(self, tenant_id: str, workspace_id: str, task_result: TaskResult) -> None:
        """Update orchestration metrics"""
        try:
            key = f"{tenant_id}:{workspace_id}"
            if key not in self._metrics:
                self._metrics[key] = OrchestrationMetrics()
            metrics = self._metrics[key]
            metrics.total_tasks += 1
            if task_result.status == TaskStatus.COMPLETED:
                metrics.completed_tasks += 1
            elif task_result.status == TaskStatus.FAILED:
                metrics.failed_tasks += 1
            if metrics.total_tasks > 0:
                metrics.success_rate = metrics.completed_tasks / metrics.total_tasks
            total_time = metrics.avg_execution_time_ms * (metrics.total_tasks - 1) + task_result.execution_time_ms
            metrics.avg_execution_time_ms = total_time / metrics.total_tasks
            metrics.active_tasks = len(self._running_tasks)
            metrics.queued_tasks = len(self._task_queue)
        except Exception as e:
            logger.warning(f"Failed to update metrics: {e}")

    def get_task_status(self, task_id: str) -> StepResult:
        """Get status of a specific task"""
        try:
            if task_id in self._running_tasks:
                return StepResult.ok(
                    data={
                        "task_id": task_id,
                        "status": TaskStatus.RUNNING.value,
                        "started_at": self._running_tasks[task_id].metadata.get("started_at"),
                    }
                )
            if task_id in self._completed_tasks:
                result = self._completed_tasks[task_id]
                return StepResult.ok(
                    data={
                        "task_id": task_id,
                        "status": result.status.value,
                        "result_data": result.result_data,
                        "execution_time_ms": result.execution_time_ms,
                        "started_at": result.started_at.isoformat() if result.started_at else None,
                        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                        "metadata": result.metadata,
                    }
                )
            if task_id in self._failed_tasks:
                result = self._failed_tasks[task_id]
                return StepResult.ok(
                    data={
                        "task_id": task_id,
                        "status": result.status.value,
                        "error_message": result.error_message,
                        "execution_time_ms": result.execution_time_ms,
                        "started_at": result.started_at.isoformat() if result.started_at else None,
                        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                        "retry_count": result.retry_count,
                        "metadata": result.metadata,
                    }
                )
            if task_id in self._task_queue:
                return StepResult.ok(
                    data={
                        "task_id": task_id,
                        "status": TaskStatus.PENDING.value,
                        "dependencies": self._task_queue[task_id].dependencies,
                        "priority": self._task_queue[task_id].priority.value,
                    }
                )
            return StepResult.fail(f"Task {task_id} not found")
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return StepResult.fail(f"Task status retrieval failed: {e!s}")

    def get_orchestration_metrics(
        self, tenant_id: str | None = None, workspace_id: str | None = None
    ) -> dict[str, Any]:
        """Get orchestration performance metrics"""
        try:
            if tenant_id and workspace_id:
                key = f"{tenant_id}:{workspace_id}"
                metrics = self._metrics.get(key, OrchestrationMetrics())
            else:
                metrics = OrchestrationMetrics()
                for key_metrics in self._metrics.values():
                    metrics.total_tasks += key_metrics.total_tasks
                    metrics.completed_tasks += key_metrics.completed_tasks
                    metrics.failed_tasks += key_metrics.failed_tasks
                    metrics.active_tasks += key_metrics.active_tasks
                    metrics.queued_tasks += key_metrics.queued_tasks
                if self._metrics:
                    total_execution_time = sum(
                        (m.avg_execution_time_ms * m.total_tasks for m in self._metrics.values())
                    )
                    total_tasks = sum((m.total_tasks for m in self._metrics.values()))
                    metrics.avg_execution_time_ms = total_execution_time / max(total_tasks, 1)
                    if total_tasks > 0:
                        metrics.success_rate = sum((m.completed_tasks for m in self._metrics.values())) / total_tasks
            return {
                "total_tasks": metrics.total_tasks,
                "completed_tasks": metrics.completed_tasks,
                "failed_tasks": metrics.failed_tasks,
                "success_rate": metrics.success_rate,
                "avg_execution_time_ms": metrics.avg_execution_time_ms,
                "active_tasks": metrics.active_tasks,
                "queued_tasks": metrics.queued_tasks,
                "last_reset": metrics.last_reset.isoformat(),
                "active_components": self._get_active_components(),
            }
        except Exception as e:
            logger.error(f"Failed to get orchestration metrics: {e}")
            return {"error": str(e)}

    def cancel_task(self, task_id: str) -> StepResult:
        """Cancel a running or queued task"""
        try:
            if task_id in self._running_tasks:
                task_result = TaskResult(
                    task_id=task_id, status=TaskStatus.CANCELLED, completed_at=datetime.now(timezone.utc)
                )
                self._failed_tasks[task_id] = task_result
                del self._running_tasks[task_id]
                return StepResult.ok(data={"cancelled": True, "task_id": task_id})
            if task_id in self._task_queue:
                del self._task_queue[task_id]
                return StepResult.ok(data={"cancelled": True, "task_id": task_id})
            return StepResult.fail(f"Task {task_id} not found or already completed")
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return StepResult.fail(f"Task cancellation failed: {e!s}")

    def get_orchestration_status(self) -> dict[str, Any]:
        """Get overall orchestration system status"""
        return {
            "initialized": self._initialized,
            "active_components": self._get_active_components(),
            "running_tasks": len(self._running_tasks),
            "queued_tasks": len(self._task_queue),
            "completed_tasks": len(self._completed_tasks),
            "failed_tasks": len(self._failed_tasks),
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "hierarchical_orchestrator": self._hierarchical_orchestrator is not None,
            "enhanced_crew_executor": self._enhanced_crew_executor is not None,
        }
