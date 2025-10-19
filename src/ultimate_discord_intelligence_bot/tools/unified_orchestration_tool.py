"""Unified Orchestration Tool - CrewAI tool for unified orchestration system

This tool provides CrewAI agents with access to the unified orchestration system,
enabling advanced task management, dependency resolution, and performance monitoring
across all orchestration components.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from crewai.tools import BaseTool  # type: ignore
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.orchestration import (
    TaskManager,
    TaskManagerConfig,
    TaskPriority,
    TaskRequest,
    UnifiedOrchestrationConfig,
    UnifiedOrchestrationService,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class TaskExecutionInput(BaseModel):
    """Input schema for task execution"""

    operation: str = Field(
        ..., description="Operation: execute_task, get_status, cancel_task, get_metrics"
    )
    task_id: str = Field(..., description="Task identifier")
    task_type: str = Field(default="generic", description="Type of task to execute")
    payload: Optional[Dict[str, Any]] = Field(
        default=None, description="Task payload data"
    )
    priority: str = Field(
        default="normal", description="Task priority: low, normal, high, critical"
    )
    dependencies: Optional[List[str]] = Field(
        default=None, description="Task dependencies"
    )
    tenant_id: str = Field(default="default", description="Tenant identifier")
    workspace_id: str = Field(default="main", description="Workspace identifier")
    timeout: Optional[int] = Field(default=None, description="Task timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class TaskManagementInput(BaseModel):
    """Input schema for task management"""

    operation: str = Field(
        ...,
        description="Operation: add_task, start_task, complete_task, fail_task, get_ready_tasks",
    )
    task_id: str = Field(..., description="Task identifier")
    task_type: str = Field(default="generic", description="Type of task")
    priority: int = Field(default=2, description="Task priority (1-4)")
    dependencies: Optional[List[str]] = Field(
        default=None, description="Task dependencies"
    )
    estimated_duration: int = Field(
        default=0, description="Estimated duration in seconds"
    )
    resource_requirements: Optional[Dict[str, Any]] = Field(
        default=None, description="Resource requirements"
    )
    result_data: Optional[Any] = Field(
        default=None, description="Result data (for completion)"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message (for failure)"
    )


class UnifiedOrchestrationTool(BaseTool):
    """Unified orchestration tool for CrewAI agents"""

    name: str = "unified_orchestration_tool"
    description: str = (
        "Provides unified orchestration capabilities including task execution, dependency resolution, "
        "and performance monitoring. Consolidates all orchestration systems into a single intelligent "
        "hierarchical system with advanced task management and optimization."
    )
    args_schema: Type[BaseModel] = TaskExecutionInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize unified orchestration service
        try:
            orchestration_config = UnifiedOrchestrationConfig(
                enable_hierarchical_orchestrator=True,
                enable_enhanced_crew_executor=True,
                enable_task_scheduling=True,
                enable_dependency_resolution=True,
                enable_performance_monitoring=True,
                max_concurrent_tasks=10,
                task_timeout=300,
                retry_delay=5,
                max_retries=3,
            )

            self._orchestration_service = UnifiedOrchestrationService(
                orchestration_config
            )
            logger.info("Unified orchestration tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize unified orchestration tool: {e}")
            self._orchestration_service = None

    def _run(
        self,
        operation: str,
        task_id: str,
        task_type: str = "generic",
        payload: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        dependencies: Optional[List[str]] = None,
        tenant_id: str = "default",
        workspace_id: str = "main",
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ) -> str:
        """Execute orchestration operation"""
        try:
            if not self._orchestration_service:
                return StepResult.fail(
                    "Unified orchestration service not initialized"
                ).to_json()

            if operation == "execute_task":
                return self._execute_task(
                    task_id,
                    task_type,
                    payload,
                    priority,
                    dependencies,
                    tenant_id,
                    workspace_id,
                    timeout,
                    max_retries,
                ).to_json()

            elif operation == "get_status":
                return self._get_task_status(task_id).to_json()

            elif operation == "cancel_task":
                return self._cancel_task(task_id).to_json()

            elif operation == "get_metrics":
                return self._get_orchestration_metrics(
                    tenant_id, workspace_id
                ).to_json()

            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_json()

        except Exception as e:
            logger.error(f"Error in unified orchestration tool: {e}", exc_info=True)
            return StepResult.fail(
                f"Orchestration operation failed: {str(e)}"
            ).to_json()

    def _execute_task(
        self,
        task_id: str,
        task_type: str,
        payload: Optional[Dict[str, Any]],
        priority: str,
        dependencies: Optional[List[str]],
        tenant_id: str,
        workspace_id: str,
        timeout: Optional[int],
        max_retries: int,
    ) -> StepResult:
        """Execute a task through the orchestration system"""
        try:
            # Convert priority string to enum
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "critical": TaskPriority.CRITICAL,
            }
            task_priority = priority_map.get(priority.lower(), TaskPriority.NORMAL)

            # Create task request
            task_request = TaskRequest(
                task_id=task_id,
                task_type=task_type,
                payload=payload or {},
                priority=task_priority,
                dependencies=dependencies or [],
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                timeout=timeout,
                max_retries=max_retries,
            )

            # Execute task
            import asyncio

            result = asyncio.run(
                self._orchestration_service.execute_task(
                    task_request, tenant_id, workspace_id
                )
            )

            if not result.success:
                return result

            return StepResult.ok(
                data={
                    "task_id": task_id,
                    "status": result.data.status.value
                    if hasattr(result.data, "status")
                    else str(result.data.get("status", "unknown")),
                    "result_data": result.data.result_data
                    if hasattr(result.data, "result_data")
                    else result.data.get("result_data"),
                    "execution_time_ms": result.data.execution_time_ms
                    if hasattr(result.data, "execution_time_ms")
                    else result.data.get("execution_time_ms", 0),
                    "started_at": result.data.started_at.isoformat()
                    if hasattr(result.data, "started_at") and result.data.started_at
                    else None,
                    "completed_at": result.data.completed_at.isoformat()
                    if hasattr(result.data, "completed_at") and result.data.completed_at
                    else None,
                    "metadata": result.data.metadata
                    if hasattr(result.data, "metadata")
                    else result.data.get("metadata", {}),
                }
            )

        except Exception as e:
            return StepResult.fail(f"Task execution failed: {str(e)}")

    def _get_task_status(self, task_id: str) -> StepResult:
        """Get status of a specific task"""
        try:
            result = self._orchestration_service.get_task_status(task_id)

            if not result.success:
                return result

            return StepResult.ok(data=result.data)

        except Exception as e:
            return StepResult.fail(f"Task status retrieval failed: {str(e)}")

    def _cancel_task(self, task_id: str) -> StepResult:
        """Cancel a task"""
        try:
            result = self._orchestration_service.cancel_task(task_id)

            if not result.success:
                return result

            return StepResult.ok(data=result.data)

        except Exception as e:
            return StepResult.fail(f"Task cancellation failed: {str(e)}")

    def _get_orchestration_metrics(
        self, tenant_id: str, workspace_id: str
    ) -> StepResult:
        """Get orchestration performance metrics"""
        try:
            metrics = self._orchestration_service.get_orchestration_metrics(
                tenant_id, workspace_id
            )

            return StepResult.ok(data=metrics)

        except Exception as e:
            return StepResult.fail(f"Metrics retrieval failed: {str(e)}")


class TaskManagementTool(BaseTool):
    """Task management tool for CrewAI agents"""

    name: str = "task_management_tool"
    description: str = (
        "Provides advanced task management capabilities including task scheduling, dependency resolution, "
        "and lifecycle management. Enables complex workflow orchestration with intelligent task ordering "
        "and resource optimization."
    )
    args_schema: Type[BaseModel] = TaskManagementInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize task manager
        try:
            manager_config = TaskManagerConfig(
                max_queue_size=10000,
                max_dependency_depth=10,
                enable_priority_scheduling=True,
                enable_dependency_optimization=True,
            )

            self._task_manager = TaskManager(manager_config)
            logger.info("Task management tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize task management tool: {e}")
            self._task_manager = None

    def _run(
        self,
        operation: str,
        task_id: str,
        task_type: str = "generic",
        priority: int = 2,
        dependencies: Optional[List[str]] = None,
        estimated_duration: int = 0,
        resource_requirements: Optional[Dict[str, Any]] = None,
        result_data: Optional[Any] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """Execute task management operation"""
        try:
            if not self._task_manager:
                return StepResult.fail("Task manager not initialized").to_json()

            if operation == "add_task":
                return self._add_task(
                    task_id,
                    task_type,
                    priority,
                    dependencies,
                    estimated_duration,
                    resource_requirements,
                ).to_json()

            elif operation == "start_task":
                return self._start_task(task_id).to_json()

            elif operation == "complete_task":
                return self._complete_task(task_id, result_data).to_json()

            elif operation == "fail_task":
                return self._fail_task(task_id, error_message).to_json()

            elif operation == "get_ready_tasks":
                return self._get_ready_tasks().to_json()

            else:
                return StepResult.fail(f"Unknown operation: {operation}").to_json()

        except Exception as e:
            logger.error(f"Error in task management tool: {e}", exc_info=True)
            return StepResult.fail(
                f"Task management operation failed: {str(e)}"
            ).to_json()

    def _add_task(
        self,
        task_id: str,
        task_type: str,
        priority: int,
        dependencies: Optional[List[str]],
        estimated_duration: int,
        resource_requirements: Optional[Dict[str, Any]],
    ) -> StepResult:
        """Add a task to the manager"""
        try:
            result = self._task_manager.add_task(
                task_id=task_id,
                task_type=task_type,
                priority=priority,
                dependencies=dependencies,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
            )

            return result

        except Exception as e:
            return StepResult.fail(f"Task addition failed: {str(e)}")

    def _start_task(self, task_id: str) -> StepResult:
        """Start a task"""
        try:
            result = self._task_manager.start_task(task_id)

            return result

        except Exception as e:
            return StepResult.fail(f"Task start failed: {str(e)}")

    def _complete_task(self, task_id: str, result_data: Optional[Any]) -> StepResult:
        """Complete a task"""
        try:
            result = self._task_manager.complete_task(task_id, result_data)

            return result

        except Exception as e:
            return StepResult.fail(f"Task completion failed: {str(e)}")

    def _fail_task(self, task_id: str, error_message: Optional[str]) -> StepResult:
        """Fail a task"""
        try:
            result = self._task_manager.fail_task(
                task_id, error_message or "Unknown error"
            )

            return result

        except Exception as e:
            return StepResult.fail(f"Task failure handling failed: {str(e)}")

    def _get_ready_tasks(self) -> StepResult:
        """Get tasks that are ready to execute"""
        try:
            ready_tasks = self._task_manager.get_ready_tasks()

            return StepResult.ok(
                data={"ready_tasks": ready_tasks, "count": len(ready_tasks)}
            )

        except Exception as e:
            return StepResult.fail(f"Ready tasks retrieval failed: {str(e)}")


class OrchestrationStatusTool(BaseTool):
    """Orchestration status tool for CrewAI agents"""

    name: str = "orchestration_status_tool"
    description: str = (
        "Provides status information about the unified orchestration system including "
        "active components, task queues, and system health."
    )
    args_schema: Type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize orchestration service for status checking
        try:
            orchestration_config = UnifiedOrchestrationConfig()
            self._orchestration_service = UnifiedOrchestrationService(
                orchestration_config
            )

            manager_config = TaskManagerConfig()
            self._task_manager = TaskManager(manager_config)

            logger.info("Orchestration status tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestration status tool: {e}")
            self._orchestration_service = None
            self._task_manager = None

    def _run(
        self,
        tenant_id: str = "default",
        workspace_id: str = "main",
    ) -> str:
        """Get orchestration system status"""
        try:
            status_info = {}

            # Get orchestration service status
            if self._orchestration_service:
                orchestration_status = (
                    self._orchestration_service.get_orchestration_status()
                )
                status_info["orchestration_status"] = orchestration_status

                # Get orchestration metrics
                orchestration_metrics = (
                    self._orchestration_service.get_orchestration_metrics(
                        tenant_id, workspace_id
                    )
                )
                status_info["orchestration_metrics"] = orchestration_metrics

            # Get task manager status
            if self._task_manager:
                manager_metrics = self._task_manager.get_manager_metrics()
                status_info["task_manager_metrics"] = manager_metrics

            return StepResult.ok(data=status_info).to_json()

        except Exception as e:
            logger.error(f"Error in orchestration status tool: {e}", exc_info=True)
            return StepResult.fail(f"Status retrieval failed: {str(e)}").to_json()
