"""Task Manager - Advanced task scheduling and dependency management

This module provides advanced task scheduling, dependency resolution, and
task lifecycle management for the unified orchestration system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from heapq import heappop, heappush
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class TaskManagerConfig:
    """Configuration for task manager"""

    max_queue_size: int = 10000
    max_dependency_depth: int = 10
    enable_priority_scheduling: bool = True
    enable_dependency_optimization: bool = True
    task_cleanup_interval: int = 3600  # 1 hour
    max_task_history: int = 1000


@dataclass
class TaskNode:
    """Node in the task dependency graph"""

    task_id: str
    task_type: str
    priority: int
    dependencies: set[str]
    dependents: set[str]
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSchedule:
    """Task schedule information"""

    task_id: str
    scheduled_time: datetime
    priority: int
    estimated_duration: int = 0
    resource_requirements: dict[str, Any] = field(default_factory=dict)


class TaskDependencyResolver:
    """Resolves task dependencies and detects cycles"""

    def __init__(self):
        self._dependency_graph: dict[str, set[str]] = {}
        self._reverse_dependency_graph: dict[str, set[str]] = {}

    def add_task_dependencies(self, task_id: str, dependencies: list[str]) -> StepResult:
        """Add task dependencies to the graph"""
        try:
            # Validate dependencies
            for dep in dependencies:
                if dep == task_id:
                    return StepResult.fail(f"Task {task_id} cannot depend on itself")

            # Add to dependency graph
            self._dependency_graph[task_id] = set(dependencies)

            # Update reverse dependency graph
            for dep in dependencies:
                if dep not in self._reverse_dependency_graph:
                    self._reverse_dependency_graph[dep] = set()
                self._reverse_dependency_graph[dep].add(task_id)

            # Check for cycles
            cycle = self._detect_cycle(task_id)
            if cycle:
                return StepResult.fail(f"Cycle detected in dependencies: {' -> '.join(cycle)}")

            return StepResult.ok(data={"dependencies_added": len(dependencies)})

        except Exception as e:
            logger.error(f"Error adding task dependencies: {e}")
            return StepResult.fail(f"Dependency addition failed: {e!s}")

    def remove_task(self, task_id: str) -> StepResult:
        """Remove task from dependency graph"""
        try:
            # Remove from dependency graph
            if task_id in self._dependency_graph:
                dependencies = self._dependency_graph.pop(task_id)

                # Update reverse dependency graph
                for dep in dependencies:
                    if dep in self._reverse_dependency_graph:
                        self._reverse_dependency_graph[dep].discard(task_id)
                        if not self._reverse_dependency_graph[dep]:
                            del self._reverse_dependency_graph[dep]

            # Remove from reverse dependency graph
            if task_id in self._reverse_dependency_graph:
                dependents = self._reverse_dependency_graph.pop(task_id)

                # Update dependency graph
                for dependent in dependents:
                    if dependent in self._dependency_graph:
                        self._dependency_graph[dependent].discard(task_id)

            return StepResult.ok(data={"task_removed": True})

        except Exception as e:
            logger.error(f"Error removing task: {e}")
            return StepResult.fail(f"Task removal failed: {e!s}")

    def get_ready_tasks(self, completed_tasks: set[str]) -> list[str]:
        """Get tasks that are ready to execute (dependencies satisfied)"""
        try:
            ready_tasks = []

            for task_id, dependencies in self._dependency_graph.items():
                if task_id not in completed_tasks:
                    # Check if all dependencies are completed
                    if dependencies.issubset(completed_tasks):
                        ready_tasks.append(task_id)

            return ready_tasks

        except Exception as e:
            logger.error(f"Error getting ready tasks: {e}")
            return []

    def get_dependents(self, task_id: str) -> list[str]:
        """Get all tasks that depend on the given task"""
        try:
            return list(self._reverse_dependency_graph.get(task_id, set()))
        except Exception as e:
            logger.error(f"Error getting dependents: {e}")
            return []

    def _detect_cycle(self, start_task: str) -> list[str] | None:
        """Detect cycles in the dependency graph using DFS"""
        try:
            visited = set()
            rec_stack = set()
            path = []

            def dfs(task_id: str) -> bool:
                visited.add(task_id)
                rec_stack.add(task_id)
                path.append(task_id)

                # Check dependencies
                for dep in self._dependency_graph.get(task_id, set()):
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        # Cycle detected
                        path.index(dep)
                        return True

                rec_stack.remove(task_id)
                path.pop()
                return False

            if dfs(start_task):
                # Find the cycle
                cycle_start = path.index(path[-1])
                return path[cycle_start:]

            return None

        except Exception as e:
            logger.error(f"Error detecting cycle: {e}")
            return None


class TaskScheduler:
    """Priority-based task scheduler with resource management"""

    def __init__(self, config: TaskManagerConfig | None = None):
        self.config = config or TaskManagerConfig()
        self._priority_queue: list[tuple[int, datetime, str]] = []  # (priority, time, task_id)
        self._scheduled_tasks: dict[str, TaskSchedule] = {}
        self._resource_usage: dict[str, int] = {}
        self._max_resources: dict[str, int] = {"cpu": 100, "memory": 100, "io": 100}

    def schedule_task(
        self,
        task_id: str,
        priority: int,
        estimated_duration: int = 0,
        resource_requirements: dict[str, Any] | None = None,
        scheduled_time: datetime | None = None,
    ) -> StepResult:
        """Schedule a task for execution"""
        try:
            if scheduled_time is None:
                scheduled_time = datetime.now(timezone.utc)

            # Check resource availability
            if resource_requirements:
                if not self._check_resources_available(resource_requirements):
                    return StepResult.fail("Insufficient resources available")

                # Reserve resources
                self._reserve_resources(resource_requirements)

            # Create task schedule
            task_schedule = TaskSchedule(
                task_id=task_id,
                scheduled_time=scheduled_time,
                priority=priority,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements or {},
            )

            # Add to priority queue
            heappush(self._priority_queue, (-priority, scheduled_time, task_id))
            self._scheduled_tasks[task_id] = task_schedule

            return StepResult.ok(data={"scheduled": True, "task_id": task_id})

        except Exception as e:
            logger.error(f"Error scheduling task: {e}")
            return StepResult.fail(f"Task scheduling failed: {e!s}")

    def get_next_task(self) -> str | None:
        """Get the next task to execute based on priority and schedule"""
        try:
            if not self._priority_queue:
                return None

            # Get highest priority task that's ready
            while self._priority_queue:
                priority, scheduled_time, task_id = heappop(self._priority_queue)

                # Check if task is ready to execute
                if scheduled_time <= datetime.now(timezone.utc) and task_id in self._scheduled_tasks:
                    return task_id

                # Put back if not ready
                heappush(self._priority_queue, (priority, scheduled_time, task_id))
                break

            return None

        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            return None

    def complete_task(self, task_id: str) -> StepResult:
        """Mark task as completed and release resources"""
        try:
            if task_id in self._scheduled_tasks:
                task_schedule = self._scheduled_tasks.pop(task_id)

                # Release resources
                if task_schedule.resource_requirements:
                    self._release_resources(task_schedule.resource_requirements)

                return StepResult.ok(data={"completed": True, "task_id": task_id})

            return StepResult.fail(f"Task {task_id} not found in scheduler")

        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return StepResult.fail(f"Task completion failed: {e!s}")

    def cancel_task(self, task_id: str) -> StepResult:
        """Cancel a scheduled task"""
        try:
            if task_id in self._scheduled_tasks:
                task_schedule = self._scheduled_tasks.pop(task_id)

                # Release resources
                if task_schedule.resource_requirements:
                    self._release_resources(task_schedule.resource_requirements)

                # Remove from priority queue
                self._priority_queue = [(p, t, tid) for p, t, tid in self._priority_queue if tid != task_id]

                return StepResult.ok(data={"cancelled": True, "task_id": task_id})

            return StepResult.fail(f"Task {task_id} not found in scheduler")

        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return StepResult.fail(f"Task cancellation failed: {e!s}")

    def _check_resources_available(self, requirements: dict[str, Any]) -> bool:
        """Check if required resources are available"""
        try:
            for resource, amount in requirements.items():
                if resource in self._max_resources:
                    current_usage = self._resource_usage.get(resource, 0)
                    if current_usage + amount > self._max_resources[resource]:
                        return False
            return True
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            return False

    def _reserve_resources(self, requirements: dict[str, Any]) -> None:
        """Reserve resources for a task"""
        try:
            for resource, amount in requirements.items():
                if resource in self._max_resources:
                    self._resource_usage[resource] = self._resource_usage.get(resource, 0) + amount
        except Exception as e:
            logger.error(f"Error reserving resources: {e}")

    def _release_resources(self, requirements: dict[str, Any]) -> None:
        """Release resources for a task"""
        try:
            for resource, amount in requirements.items():
                if resource in self._resource_usage:
                    self._resource_usage[resource] = max(0, self._resource_usage[resource] - amount)
        except Exception as e:
            logger.error(f"Error releasing resources: {e}")

    def get_scheduler_status(self) -> dict[str, Any]:
        """Get scheduler status and metrics"""
        try:
            return {
                "queued_tasks": len(self._priority_queue),
                "scheduled_tasks": len(self._scheduled_tasks),
                "resource_usage": self._resource_usage.copy(),
                "max_resources": self._max_resources.copy(),
                "next_task": self._priority_queue[0][2] if self._priority_queue else None,
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {"error": str(e)}


class TaskManager:
    """Unified task manager coordinating dependencies and scheduling"""

    def __init__(self, config: TaskManagerConfig | None = None):
        self.config = config or TaskManagerConfig()
        self._dependency_resolver = TaskDependencyResolver()
        self._task_scheduler = TaskScheduler(config)
        self._task_nodes: dict[str, TaskNode] = {}
        self._completed_tasks: set[str] = set()
        self._running_tasks: set[str] = set()

    def add_task(
        self,
        task_id: str,
        task_type: str,
        priority: int = 2,
        dependencies: list[str] | None = None,
        estimated_duration: int = 0,
        resource_requirements: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Add a task to the manager"""
        try:
            # Create task node
            task_node = TaskNode(
                task_id=task_id,
                task_type=task_type,
                priority=priority,
                dependencies=set(dependencies or []),
                dependents=set(),
                metadata=metadata or {},
            )

            # Add dependencies
            if dependencies:
                dep_result = self._dependency_resolver.add_task_dependencies(task_id, dependencies)
                if not dep_result.success:
                    return dep_result

            # Add to scheduler
            schedule_result = self._task_scheduler.schedule_task(
                task_id=task_id,
                priority=priority,
                estimated_duration=estimated_duration,
                resource_requirements=resource_requirements,
            )

            if not schedule_result.success:
                return schedule_result

            # Store task node
            self._task_nodes[task_id] = task_node

            return StepResult.ok(data={"task_added": True, "task_id": task_id})

        except Exception as e:
            logger.error(f"Error adding task: {e}")
            return StepResult.fail(f"Task addition failed: {e!s}")

    def get_ready_tasks(self) -> list[str]:
        """Get tasks that are ready to execute"""
        try:
            # Get tasks with satisfied dependencies
            ready_tasks = self._dependency_resolver.get_ready_tasks(self._completed_tasks)

            # Filter out running tasks
            ready_tasks = [tid for tid in ready_tasks if tid not in self._running_tasks]

            # Sort by priority
            ready_tasks.sort(
                key=lambda tid: self._task_nodes.get(tid, TaskNode("", "", 0)).priority,
                reverse=True,
            )

            return ready_tasks

        except Exception as e:
            logger.error(f"Error getting ready tasks: {e}")
            return []

    def start_task(self, task_id: str) -> StepResult:
        """Mark task as running"""
        try:
            if task_id not in self._task_nodes:
                return StepResult.fail(f"Task {task_id} not found")

            if task_id in self._running_tasks:
                return StepResult.fail(f"Task {task_id} is already running")

            self._running_tasks.add(task_id)
            self._task_nodes[task_id].status = "running"

            return StepResult.ok(data={"started": True, "task_id": task_id})

        except Exception as e:
            logger.error(f"Error starting task: {e}")
            return StepResult.fail(f"Task start failed: {e!s}")

    def complete_task(self, task_id: str, result_data: Any | None = None) -> StepResult:
        """Mark task as completed"""
        try:
            if task_id not in self._task_nodes:
                return StepResult.fail(f"Task {task_id} not found")

            # Remove from running tasks
            self._running_tasks.discard(task_id)

            # Add to completed tasks
            self._completed_tasks.add(task_id)

            # Update task status
            self._task_nodes[task_id].status = "completed"
            if result_data:
                self._task_nodes[task_id].metadata["result_data"] = result_data

            # Complete in scheduler
            self._task_scheduler.complete_task(task_id)

            return StepResult.ok(data={"completed": True, "task_id": task_id})

        except Exception as e:
            logger.error(f"Error completing task: {e}")
            return StepResult.fail(f"Task completion failed: {e!s}")

    def fail_task(self, task_id: str, error_message: str) -> StepResult:
        """Mark task as failed"""
        try:
            if task_id not in self._task_nodes:
                return StepResult.fail(f"Task {task_id} not found")

            # Remove from running tasks
            self._running_tasks.discard(task_id)

            # Update task status
            self._task_nodes[task_id].status = "failed"
            self._task_nodes[task_id].metadata["error_message"] = error_message

            # Cancel in scheduler
            self._task_scheduler.cancel_task(task_id)

            return StepResult.ok(data={"failed": True, "task_id": task_id})

        except Exception as e:
            logger.error(f"Error failing task: {e}")
            return StepResult.fail(f"Task failure handling failed: {e!s}")

    def get_task_status(self, task_id: str) -> StepResult:
        """Get status of a specific task"""
        try:
            if task_id not in self._task_nodes:
                return StepResult.fail(f"Task {task_id} not found")

            task_node = self._task_nodes[task_id]

            return StepResult.ok(
                data={
                    "task_id": task_id,
                    "task_type": task_node.task_type,
                    "status": task_node.status,
                    "priority": task_node.priority,
                    "dependencies": list(task_node.dependencies),
                    "dependents": list(task_node.dependents),
                    "created_at": task_node.created_at.isoformat(),
                    "metadata": task_node.metadata,
                }
            )

        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return StepResult.fail(f"Task status retrieval failed: {e!s}")

    def get_manager_metrics(self) -> dict[str, Any]:
        """Get task manager metrics"""
        try:
            scheduler_status = self._task_scheduler.get_scheduler_status()

            return {
                "total_tasks": len(self._task_nodes),
                "running_tasks": len(self._running_tasks),
                "completed_tasks": len(self._completed_tasks),
                "ready_tasks": len(self.get_ready_tasks()),
                "scheduler_status": scheduler_status,
                "dependency_graph_size": len(self._dependency_resolver._dependency_graph),
                "reverse_dependency_graph_size": len(self._dependency_resolver._reverse_dependency_graph),
            }

        except Exception as e:
            logger.error(f"Error getting manager metrics: {e}")
            return {"error": str(e)}
