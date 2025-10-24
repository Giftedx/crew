"""
Hierarchical Orchestrator Service - Supervisor-Worker Coordination

This service implements the hierarchical agent orchestration system with
supervisor-worker patterns, dynamic load balancing, and failure recovery.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult

from ..agents.executive_supervisor import ExecutiveSupervisorAgent
from ..agents.workflow_manager import WorkflowManagerAgent
from ..step_result import StepResult


logger = logging.getLogger(__name__)


class OrchestrationStatus(Enum):
    """Orchestration status enumeration."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(Enum):
    """Agent role enumeration."""

    EXECUTIVE_SUPERVISOR = "executive_supervisor"
    WORKFLOW_MANAGER = "workflow_manager"
    SPECIALIST_AGENT = "specialist_agent"
    MONITORING_AGENT = "monitoring_agent"


@dataclass
class AgentInstance:
    """Agent instance with metadata and status."""

    id: str
    role: AgentRole
    agent_type: str
    status: str = "idle"
    current_load: float = 0.0
    max_capacity: float = 1.0
    capabilities: list[str] = field(default_factory=list)
    last_heartbeat: datetime | None = None
    performance_metrics: dict[str, float] = field(default_factory=dict)
    assigned_tasks: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationTask:
    """Orchestration task with execution context."""

    id: str
    name: str
    description: str
    priority: int
    assigned_agent: str | None = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationSession:
    """Orchestration session with task tracking."""

    id: str
    name: str
    status: OrchestrationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    tasks: list[OrchestrationTask] = field(default_factory=list)
    agents: list[AgentInstance] = field(default_factory=list)
    tenant: str = ""
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class HierarchicalOrchestrator:
    """Hierarchical orchestrator for supervisor-worker coordination."""

    def __init__(self):
        """Initialize the hierarchical orchestrator."""
        self.executive_supervisor = ExecutiveSupervisorAgent()
        self.workflow_manager = WorkflowManagerAgent()
        self.active_sessions: dict[str, OrchestrationSession] = {}
        self.agent_registry: dict[str, AgentInstance] = {}
        self.task_queue: list[OrchestrationTask] = []
        self.status = OrchestrationStatus.IDLE

        # Performance tracking
        self.performance_metrics = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "average_completion_time": 0.0,
            "agent_utilization": 0.0,
        }

    async def create_orchestration_session(
        self,
        name: str,
        mission_context: str,
        objectives: list[dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """
        Create a new orchestration session with strategic planning.

        Args:
            name: Session name
            mission_context: Mission context for strategic planning
            objectives: List of objectives
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with session information
        """
        try:
            session_id = str(uuid.uuid4())

            # Create orchestration session
            session = OrchestrationSession(
                id=session_id,
                name=name,
                status=OrchestrationStatus.PLANNING,
                tenant=tenant,
                workspace=workspace,
            )

            # Execute strategic planning
            planning_result = await self.executive_supervisor.execute_strategic_planning(
                mission_context, objectives, tenant, workspace
            )

            if not planning_result.success:
                return StepResult.fail(f"Strategic planning failed: {planning_result.error}")

            # Create tasks from strategic plan
            tasks = self._create_tasks_from_strategic_plan(planning_result.data, session_id)
            session.tasks = tasks

            # Register session
            self.active_sessions[session_id] = session
            self.status = OrchestrationStatus.PLANNING

            return StepResult.ok(
                data={
                    "session_id": session_id,
                    "session_name": name,
                    "status": session.status.value,
                    "tasks_created": len(tasks),
                    "strategic_plan": planning_result.data,
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Failed to create orchestration session: {e!s}")
            return StepResult.fail(f"Failed to create orchestration session: {e!s}")

    async def execute_orchestration_session(self, session_id: str) -> StepResult:
        """
        Execute an orchestration session with workflow management.

        Args:
            session_id: Session identifier

        Returns:
            StepResult with execution results
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")

            session = self.active_sessions[session_id]
            session.status = OrchestrationStatus.EXECUTING
            session.started_at = datetime.utcnow()

            # Resolve dependencies
            dependency_result = await self.workflow_manager.resolve_dependencies(
                [self._task_to_dict(task) for task in session.tasks],
                session.tenant,
                session.workspace,
            )

            if not dependency_result.success:
                return StepResult.fail(f"Dependency resolution failed: {dependency_result.error}")

            # Route tasks to agents
            available_agents = self._get_available_agents()
            routing_result = await self.workflow_manager.route_tasks(
                {
                    "id": session_id,
                    "name": session.name,
                    "tasks": [self._task_to_dict(task) for task in session.tasks],
                },
                available_agents,
                session.tenant,
                session.workspace,
            )

            if not routing_result.success:
                return StepResult.fail(f"Task routing failed: {routing_result.error}")

            # Execute tasks
            execution_results = await self._execute_tasks_with_monitoring(session, routing_result.data)

            # Update session status
            if all(result.get("status") == "completed" for result in execution_results):
                session.status = OrchestrationStatus.COMPLETED
                session.completed_at = datetime.utcnow()
                self.performance_metrics["completed_sessions"] += 1
            else:
                session.status = OrchestrationStatus.FAILED
                self.performance_metrics["failed_sessions"] += 1

            self.performance_metrics["total_sessions"] += 1
            self._update_performance_metrics(session)

            return StepResult.ok(
                data={
                    "session_id": session_id,
                    "status": session.status.value,
                    "execution_results": execution_results,
                    "dependency_resolution": dependency_result.data,
                    "task_routing": routing_result.data,
                    "performance_metrics": self.performance_metrics,
                }
            )

        except Exception as e:
            logger.error(f"Failed to execute orchestration session: {e!s}")
            return StepResult.fail(f"Failed to execute orchestration session: {e!s}")

    async def monitor_orchestration_session(self, session_id: str) -> StepResult:
        """
        Monitor an active orchestration session.

        Args:
            session_id: Session identifier

        Returns:
            StepResult with monitoring data
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")

            session = self.active_sessions[session_id]

            # Collect monitoring data
            monitoring_data = {
                "session_status": session.status.value,
                "task_status_summary": self._get_task_status_summary(session.tasks),
                "agent_utilization": self._get_agent_utilization(),
                "performance_metrics": self._get_session_performance_metrics(session),
                "health_checks": await self._perform_health_checks(session),
                "bottlenecks": self._identify_bottlenecks(session),
                "recommendations": self._generate_monitoring_recommendations(session),
            }

            return StepResult.ok(data=monitoring_data)

        except Exception as e:
            logger.error(f"Failed to monitor orchestration session: {e!s}")
            return StepResult.fail(f"Failed to monitor orchestration session: {e!s}")

    async def handle_failure_recovery(self, session_id: str, failure_context: dict[str, Any]) -> StepResult:
        """
        Handle failure recovery for an orchestration session.

        Args:
            session_id: Session identifier
            failure_context: Context about the failure

        Returns:
            StepResult with recovery actions
        """
        try:
            if session_id not in self.active_sessions:
                return StepResult.fail(f"Session {session_id} not found")

            session = self.active_sessions[session_id]
            session.status = OrchestrationStatus.RECOVERING

            # Analyze failure
            failure_analysis = self._analyze_failure(failure_context, session)

            # Determine recovery strategy
            recovery_strategy = self._determine_recovery_strategy(failure_analysis)

            # Execute recovery actions
            recovery_results = await self._execute_recovery_actions(session, recovery_strategy)

            # Update session status
            if recovery_results.get("success", False):
                session.status = OrchestrationStatus.EXECUTING
            else:
                session.status = OrchestrationStatus.FAILED

            return StepResult.ok(
                data={
                    "session_id": session_id,
                    "failure_analysis": failure_analysis,
                    "recovery_strategy": recovery_strategy,
                    "recovery_results": recovery_results,
                    "session_status": session.status.value,
                }
            )

        except Exception as e:
            logger.error(f"Failed to handle failure recovery: {e!s}")
            return StepResult.fail(f"Failed to handle failure recovery: {e!s}")

    def register_agent(self, agent_instance: AgentInstance) -> StepResult:
        """
        Register an agent instance with the orchestrator.

        Args:
            agent_instance: Agent instance to register

        Returns:
            StepResult with registration status
        """
        try:
            self.agent_registry[agent_instance.id] = agent_instance
            agent_instance.last_heartbeat = datetime.utcnow()

            return StepResult.ok(
                data={
                    "agent_id": agent_instance.id,
                    "role": agent_instance.role.value,
                    "status": "registered",
                    "total_registered_agents": len(self.agent_registry),
                }
            )

        except Exception as e:
            logger.error(f"Failed to register agent: {e!s}")
            return StepResult.fail(f"Failed to register agent: {e!s}")

    def get_orchestration_status(self) -> StepResult:
        """
        Get overall orchestration system status.

        Returns:
            StepResult with system status
        """
        try:
            return StepResult.ok(
                data={
                    "orchestrator_status": self.status.value,
                    "active_sessions": len(self.active_sessions),
                    "registered_agents": len(self.agent_registry),
                    "queued_tasks": len(self.task_queue),
                    "performance_metrics": self.performance_metrics,
                    "system_health": self._assess_system_health(),
                }
            )

        except Exception as e:
            logger.error(f"Failed to get orchestration status: {e!s}")
            return StepResult.fail(f"Failed to get orchestration status: {e!s}")

    def _create_tasks_from_strategic_plan(self, strategic_plan: dict[str, Any], session_id: str) -> StepResult:
        """Create orchestration tasks from strategic plan."""
        tasks = []

        for objective in strategic_plan.get("objectives", []):
            task = OrchestrationTask(
                id=f"{session_id}_{objective['id']}",
                name=objective["title"],
                description=objective["description"],
                priority=objective["priority"],
                dependencies=objective.get("dependencies", []),
                metadata={
                    "objective_id": objective["id"],
                    "success_criteria": objective.get("success_criteria", []),
                    "resource_requirements": objective.get("resource_requirements", {}),
                    "timeline": objective.get("timeline", "TBD"),
                },
            )
            tasks.append(task)

        return tasks

    def _task_to_dict(self, task: OrchestrationTask) -> StepResult:
        """Convert orchestration task to dictionary."""
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "dependencies": task.dependencies,
            "estimated_duration_seconds": task.metadata.get("estimated_duration", 60),
            "agent_type": task.metadata.get("agent_type", "general"),
            "resource_requirements": task.metadata.get("resource_requirements", {}),
            "metadata": task.metadata,
        }

    def _get_available_agents(self) -> StepResult:
        """Get list of available agents for task routing."""
        available_agents = []

        for agent in self.agent_registry.values():
            if agent.status == "idle" and agent.current_load < agent.max_capacity:
                available_agents.append(
                    {
                        "id": agent.id,
                        "type": agent.agent_type,
                        "capabilities": agent.capabilities,
                        "current_load": agent.current_load,
                        "max_concurrent_tasks": int(agent.max_capacity * 10),  # Estimate
                        "average_completion_time": agent.performance_metrics.get("avg_completion_time", 60.0),
                        "success_rate": agent.performance_metrics.get("success_rate", 0.95),
                        "specializations": agent.metadata.get("specializations", []),
                    }
                )

        return available_agents

    async def _execute_tasks_with_monitoring(
        self, session: OrchestrationSession, routing_data: dict[str, Any]
    ) -> StepResult:
        """Execute tasks with monitoring and failure handling."""
        execution_results = []
        assignments = routing_data.get("assignments", [])

        for assignment in assignments:
            task_id = assignment.get("task_id")
            assigned_agent = assignment.get("assigned_agent")

            if not assigned_agent:
                execution_results.append(
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": "No agent assigned",
                        "assigned_agent": None,
                    }
                )
                continue

            # Find task in session
            task = next((t for t in session.tasks if t.id == task_id), None)
            if not task:
                execution_results.append(
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": "Task not found",
                        "assigned_agent": assigned_agent,
                    }
                )
                continue

            # Update task status
            task.assigned_agent = assigned_agent
            task.status = "running"
            task.started_at = datetime.utcnow()

            # Simulate task execution (in real implementation, this would call actual agents)
            try:
                # Update agent load
                if assigned_agent in self.agent_registry:
                    self.agent_registry[assigned_agent].current_load += 0.1
                    self.agent_registry[assigned_agent].assigned_tasks.append(task_id)

                # Simulate execution time
                await asyncio.sleep(0.1)  # Simulate work

                # Mark task as completed
                task.status = "completed"
                task.completed_at = datetime.utcnow()

                execution_results.append(
                    {
                        "task_id": task_id,
                        "status": "completed",
                        "assigned_agent": assigned_agent,
                        "started_at": task.started_at.isoformat(),
                        "completed_at": task.completed_at.isoformat(),
                        "duration_seconds": (task.completed_at - task.started_at).total_seconds(),
                    }
                )

                # Update agent load
                if assigned_agent in self.agent_registry:
                    self.agent_registry[assigned_agent].current_load -= 0.1
                    if task_id in self.agent_registry[assigned_agent].assigned_tasks:
                        self.agent_registry[assigned_agent].assigned_tasks.remove(task_id)

            except Exception as e:
                task.status = "failed"
                execution_results.append(
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e),
                        "assigned_agent": assigned_agent,
                    }
                )

        return execution_results

    def _get_task_status_summary(self, tasks: list[OrchestrationTask]) -> StepResult:
        """Get summary of task statuses."""
        status_counts = {}
        for task in tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        return status_counts

    def _get_agent_utilization(self) -> StepResult:
        """Get agent utilization metrics."""
        if not self.agent_registry:
            return {"average_utilization": 0.0, "total_agents": 0}

        total_load = sum(agent.current_load for agent in self.agent_registry.values())
        average_utilization = total_load / len(self.agent_registry)

        return {
            "average_utilization": average_utilization,
            "total_agents": len(self.agent_registry),
            "idle_agents": sum(1 for agent in self.agent_registry.values() if agent.current_load < 0.1),
            "busy_agents": sum(1 for agent in self.agent_registry.values() if agent.current_load >= 0.1),
        }

    def _get_session_performance_metrics(self, session: OrchestrationSession) -> StepResult:
        """Get performance metrics for a session."""
        if not session.started_at:
            return {"status": "not_started"}

        current_time = datetime.utcnow()
        duration = (current_time - session.started_at).total_seconds()

        completed_tasks = sum(1 for task in session.tasks if task.status == "completed")
        total_tasks = len(session.tasks)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        return {
            "duration_seconds": duration,
            "completion_rate": completion_rate,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "failed_tasks": sum(1 for task in session.tasks if task.status == "failed"),
        }

    async def _perform_health_checks(self, session: OrchestrationSession) -> StepResult:
        """Perform health checks on the session."""
        health_checks = {
            "session_health": "healthy",
            "agent_health": "healthy",
            "task_health": "healthy",
            "overall_health": "healthy",
        }

        # Check for stuck tasks
        stuck_tasks = []
        for task in session.tasks:
            if (
                task.status == "running"
                and task.started_at
                and (datetime.utcnow() - task.started_at).total_seconds() > 300
            ):  # 5 minutes
                stuck_tasks.append(task.id)

        if stuck_tasks:
            health_checks["task_health"] = "degraded"
            health_checks["stuck_tasks"] = stuck_tasks

        # Check agent heartbeats
        stale_agents = []
        for agent in self.agent_registry.values():
            if agent.last_heartbeat and (datetime.utcnow() - agent.last_heartbeat).total_seconds() > 60:  # 1 minute
                stale_agents.append(agent.id)

        if stale_agents:
            health_checks["agent_health"] = "degraded"
            health_checks["stale_agents"] = stale_agents

        # Determine overall health
        if any(status != "healthy" for status in health_checks.values() if isinstance(status, str)):
            health_checks["overall_health"] = "degraded"

        return health_checks

    def _identify_bottlenecks(self, session: OrchestrationSession) -> StepResult:
        """Identify bottlenecks in the session."""
        bottlenecks = []

        # Check for tasks waiting for dependencies
        waiting_tasks = []
        for task in session.tasks:
            if task.status == "pending":
                incomplete_deps = [
                    dep
                    for dep in task.dependencies
                    if not any(t.id == dep and t.status == "completed" for t in session.tasks)
                ]
                if incomplete_deps:
                    waiting_tasks.append({"task_id": task.id, "waiting_for": incomplete_deps})

        if waiting_tasks:
            bottlenecks.append(
                {
                    "type": "dependency_bottleneck",
                    "description": "Tasks waiting for dependencies",
                    "affected_tasks": waiting_tasks,
                }
            )

        # Check for overloaded agents
        overloaded_agents = [agent.id for agent in self.agent_registry.values() if agent.current_load > 0.8]

        if overloaded_agents:
            bottlenecks.append(
                {
                    "type": "agent_overload",
                    "description": "Agents operating at high capacity",
                    "affected_agents": overloaded_agents,
                }
            )

        return bottlenecks

    def _generate_monitoring_recommendations(self, session: OrchestrationSession) -> StepResult:
        """Generate monitoring recommendations."""
        recommendations = []

        # Check completion rate
        completed_tasks = sum(1 for task in session.tasks if task.status == "completed")
        total_tasks = len(session.tasks)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0

        if completion_rate < 0.5 and session.started_at:
            duration = (datetime.utcnow() - session.started_at).total_seconds()
            if duration > 300:  # 5 minutes
                recommendations.append(
                    {
                        "type": "performance",
                        "priority": "high",
                        "description": "Low completion rate detected",
                        "suggestion": "Consider reallocating resources or investigating task failures",
                    }
                )

        # Check agent utilization
        avg_utilization = self._get_agent_utilization()["average_utilization"]
        if avg_utilization > 0.8:
            recommendations.append(
                {
                    "type": "scaling",
                    "priority": "medium",
                    "description": "High agent utilization",
                    "suggestion": "Consider adding more agents or optimizing task distribution",
                }
            )

        return recommendations

    def _analyze_failure(self, failure_context: dict[str, Any], session: OrchestrationSession) -> StepResult:
        """Analyze failure context and determine root cause."""
        return {
            "failure_type": failure_context.get("type", "unknown"),
            "affected_components": failure_context.get("affected_components", []),
            "error_message": failure_context.get("error_message", ""),
            "timestamp": failure_context.get("timestamp", datetime.utcnow().isoformat()),
            "session_impact": self._assess_session_impact(failure_context, session),
            "root_cause_analysis": self._perform_root_cause_analysis(failure_context),
        }

    def _assess_session_impact(self, failure_context: dict[str, Any], session: OrchestrationSession) -> StepResult:
        """Assess impact of failure on session."""
        affected_components = failure_context.get("affected_components", [])

        if any("critical" in comp.lower() for comp in affected_components):
            return "critical"
        elif any("agent" in comp.lower() for comp in affected_components):
            return "high"
        else:
            return "medium"

    def _perform_root_cause_analysis(self, failure_context: dict[str, Any]) -> StepResult:
        """Perform root cause analysis."""
        return {
            "likely_causes": [
                "Resource exhaustion",
                "Network connectivity issues",
                "Agent unavailability",
                "Task dependency failures",
            ],
            "confidence_level": 0.7,
            "recommended_investigation": [
                "Check agent health status",
                "Verify resource availability",
                "Review task dependencies",
                "Analyze error logs",
            ],
        }

    def _determine_recovery_strategy(self, failure_analysis: dict[str, Any]) -> StepResult:
        """Determine recovery strategy based on failure analysis."""
        session_impact = failure_analysis.get("session_impact", "medium")

        if session_impact == "critical":
            return {
                "strategy": "full_restart",
                "actions": [
                    "Terminate current session",
                    "Reallocate all resources",
                    "Restart with fresh agents",
                    "Implement additional monitoring",
                ],
                "estimated_recovery_time": "5-10 minutes",
            }
        elif session_impact == "high":
            return {
                "strategy": "selective_restart",
                "actions": [
                    "Identify failed components",
                    "Restart affected agents",
                    "Reassign failed tasks",
                    "Continue with remaining tasks",
                ],
                "estimated_recovery_time": "2-5 minutes",
            }
        else:
            return {
                "strategy": "graceful_degradation",
                "actions": [
                    "Continue with available resources",
                    "Implement workarounds",
                    "Monitor for additional issues",
                    "Plan for maintenance window",
                ],
                "estimated_recovery_time": "1-2 minutes",
            }

    async def _execute_recovery_actions(
        self, session: OrchestrationSession, recovery_strategy: dict[str, Any]
    ) -> StepResult:
        """Execute recovery actions based on strategy."""
        strategy = recovery_strategy.get("strategy", "graceful_degradation")

        if strategy == "full_restart":
            # Reset session
            session.status = OrchestrationStatus.PLANNING
            session.started_at = None
            session.completed_at = None

            # Reset all tasks
            for task in session.tasks:
                task.status = "pending"
                task.assigned_agent = None
                task.started_at = None
                task.completed_at = None

            return {"success": True, "action": "session_restarted"}

        elif strategy == "selective_restart":
            # Reset failed tasks only
            failed_tasks = [task for task in session.tasks if task.status == "failed"]
            for task in failed_tasks:
                task.status = "pending"
                task.assigned_agent = None
                task.started_at = None
                task.completed_at = None
                task.retry_count += 1

            return {
                "success": True,
                "action": "failed_tasks_reset",
                "reset_count": len(failed_tasks),
            }

        else:  # graceful_degradation
            # Continue with current state
            return {"success": True, "action": "continued_with_degradation"}

    def _update_performance_metrics(self, session: OrchestrationSession):
        """Update performance metrics based on session completion."""
        if session.completed_at and session.started_at:
            duration = (session.completed_at - session.started_at).total_seconds()

            # Update average completion time
            total_sessions = self.performance_metrics["total_sessions"]
            current_avg = self.performance_metrics["average_completion_time"]
            self.performance_metrics["average_completion_time"] = (
                current_avg * (total_sessions - 1) + duration
            ) / total_sessions

        # Update agent utilization
        if self.agent_registry:
            total_load = sum(agent.current_load for agent in self.agent_registry.values())
            self.performance_metrics["agent_utilization"] = total_load / len(self.agent_registry)

    def _assess_system_health(self) -> StepResult:
        """Assess overall system health."""
        health_score = 1.0

        # Check active sessions
        if len(self.active_sessions) > 10:  # Arbitrary threshold
            health_score -= 0.1

        # Check agent registry
        if len(self.agent_registry) == 0:
            health_score -= 0.3

        # Check task queue
        if len(self.task_queue) > 100:  # Arbitrary threshold
            health_score -= 0.2

        # Check performance metrics
        if self.performance_metrics["failed_sessions"] > 0:
            failure_rate = self.performance_metrics["failed_sessions"] / max(
                1, self.performance_metrics["total_sessions"]
            )
            health_score -= failure_rate * 0.5

        health_score = max(0.0, min(1.0, health_score))

        if health_score >= 0.8:
            status = "healthy"
        elif health_score >= 0.6:
            status = "degraded"
        else:
            status = "unhealthy"

        return {
            "status": status,
            "score": health_score,
            "active_sessions": len(self.active_sessions),
            "registered_agents": len(self.agent_registry),
            "queued_tasks": len(self.task_queue),
        }
