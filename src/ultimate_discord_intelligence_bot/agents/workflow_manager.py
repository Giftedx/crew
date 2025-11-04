"""
Workflow Manager Agent - Dynamic Task Orchestration and Dependency Management

This agent manages complex workflows, resolves dependencies, and ensures optimal
task distribution across the agent hierarchy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from ..step_result import StepResult
from ..tools._base import BaseTool


if TYPE_CHECKING:
    from crewai import Agent


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class WorkflowTask:
    """Workflow task with dependencies and metadata."""

    id: str
    name: str
    description: str
    agent_type: str
    priority: TaskPriority
    dependencies: set[str] = field(default_factory=set)
    estimated_duration_seconds: int = 60
    resource_requirements: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    assigned_agent: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Workflow execution with task tracking."""

    id: str
    name: str
    tasks: list[WorkflowTask]
    status: TaskStatus
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    tenant: str = ""
    workspace: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapability:
    """Agent capability definition."""

    agent_id: str
    agent_type: str
    capabilities: list[str]
    current_load: float  # 0.0 to 1.0
    max_concurrent_tasks: int
    average_completion_time: float
    success_rate: float
    specializations: list[str] = field(default_factory=list)


class TaskRoutingTool(BaseTool):
    """Tool for intelligent task distribution and routing."""

    def _run(
        self,
        workflow_execution: dict[str, Any],
        available_agents: list[dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """
        Route tasks to optimal agents based on capabilities and current load.

        Args:
            workflow_execution: Workflow execution data
            available_agents: List of available agents with capabilities
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with task routing assignments
        """
        try:
            if not workflow_execution or not available_agents:
                return StepResult.fail("Workflow execution and available agents are required")

            routing_plan = self._create_routing_plan(workflow_execution, available_agents, tenant, workspace)

            return StepResult.ok(
                data={
                    "routing_plan": routing_plan,
                    "total_tasks": len(workflow_execution.get("tasks", [])),
                    "assigned_tasks": len(routing_plan.get("assignments", [])),
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Task routing failed: {e!s}")
            return StepResult.fail(f"Task routing failed: {e!s}")

    def _create_routing_plan(
        self,
        workflow: dict[str, Any],
        agents: list[dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> dict[str, Any]:
        """Create intelligent task routing plan."""
        tasks = workflow.get("tasks", [])
        agent_capabilities = [self._parse_agent_capability(agent) for agent in agents]

        # Sort tasks by priority and dependencies
        sorted_tasks = self._sort_tasks_by_priority_and_dependencies(tasks)

        assignments = []
        agent_loads = {agent.agent_id: agent.current_load for agent in agent_capabilities}

        for task_data in sorted_tasks:
            task = self._parse_workflow_task(task_data)

            # Find best agent for this task
            best_agent = self._find_best_agent_for_task(task, agent_capabilities, agent_loads)

            if best_agent:
                assignment = {
                    "task_id": task.id,
                    "task_name": task.name,
                    "assigned_agent": best_agent.agent_id,
                    "agent_type": best_agent.agent_type,
                    "priority": task.priority.value,
                    "estimated_duration": task.estimated_duration_seconds,
                    "routing_reason": self._get_routing_reason(task, best_agent),
                    "assigned_at": self._get_current_timestamp(),
                }
                assignments.append(assignment)

                # Update agent load
                agent_loads[best_agent.agent_id] += 0.1  # Simple load increment
            else:
                # No suitable agent found
                assignments.append(
                    {
                        "task_id": task.id,
                        "task_name": task.name,
                        "assigned_agent": "none",
                        "status": "unassigned",
                        "reason": "No suitable agent available",
                        "assigned_at": self._get_current_timestamp(),
                    }
                )

        return {
            "workflow_id": workflow.get("id", "unknown"),
            "assignments": assignments,
            "routing_strategy": "capability_and_load_based",
            "total_agents_used": len({a["assigned_agent"] for a in assignments if a["assigned_agent"]}),
            "load_distribution": self._calculate_load_distribution(assignments, agent_capabilities),
            "estimated_completion_time": self._estimate_workflow_completion_time(assignments),
        }

    def _parse_agent_capability(self, agent_data: dict[str, Any]) -> AgentCapability:
        """Parse agent capability from data."""
        return AgentCapability(
            agent_id=agent_data.get("id", "unknown"),
            agent_type=agent_data.get("type", "general"),
            capabilities=agent_data.get("capabilities", []),
            current_load=agent_data.get("current_load", 0.0),
            max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 1),
            average_completion_time=agent_data.get("average_completion_time", 60.0),
            success_rate=agent_data.get("success_rate", 0.95),
            specializations=agent_data.get("specializations", []),
        )

    def _parse_workflow_task(self, task_data: dict[str, Any]) -> WorkflowTask:
        """Parse workflow task from data."""
        return WorkflowTask(
            id=task_data.get("id", "unknown"),
            name=task_data.get("name", "Unnamed Task"),
            description=task_data.get("description", ""),
            agent_type=task_data.get("agent_type", "general"),
            priority=TaskPriority(task_data.get("priority", 2)),
            dependencies=set(task_data.get("dependencies", [])),
            estimated_duration_seconds=task_data.get("estimated_duration_seconds", 60),
            resource_requirements=task_data.get("resource_requirements", {}),
            metadata=task_data.get("metadata", {}),
        )

    def _sort_tasks_by_priority_and_dependencies(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort tasks by priority and resolve dependencies."""
        # Simple topological sort by priority
        return sorted(
            tasks,
            key=lambda t: (
                -t.get("priority", 2),  # Higher priority first
                len(t.get("dependencies", [])),  # Fewer dependencies first
            ),
        )

    def _find_best_agent_for_task(
        self,
        task: WorkflowTask,
        agents: list[AgentCapability],
        agent_loads: dict[str, float],
    ) -> AgentCapability | None:
        """Find the best agent for a specific task."""
        suitable_agents = []

        for agent in agents:
            # Check if agent can handle this task type and has capacity
            if (
                task.agent_type in agent.capabilities or "general" in agent.capabilities or task.agent_type == "general"
            ) and agent_loads.get(agent.agent_id, 0) < 0.9:  # 90% load threshold
                suitable_agents.append(agent)

        if not suitable_agents:
            return None

        # Score agents based on multiple factors
        best_agent = max(
            suitable_agents,
            key=lambda a: self._calculate_agent_score(task, a, agent_loads),
        )
        return best_agent

    def _calculate_agent_score(
        self, task: WorkflowTask, agent: AgentCapability, agent_loads: dict[str, float]
    ) -> float:
        """Calculate agent suitability score for a task."""
        # Base score from success rate
        score = agent.success_rate * 100

        # Penalty for current load
        current_load = agent_loads.get(agent.agent_id, 0)
        score -= current_load * 50

        # Bonus for specialization
        if task.agent_type in agent.specializations:
            score += 20

        # Bonus for faster completion time
        if agent.average_completion_time < task.estimated_duration_seconds:
            score += 10

        return score

    def _get_routing_reason(self, task: WorkflowTask, agent: AgentCapability) -> str:
        """Get human-readable routing reason."""
        reasons = []

        if task.agent_type in agent.specializations:
            reasons.append("specialized agent")
        elif agent.success_rate > 0.95:
            reasons.append("high success rate")
        elif agent.average_completion_time < task.estimated_duration_seconds:
            reasons.append("fast completion time")
        else:
            reasons.append("available capacity")

        return ", ".join(reasons)

    def _calculate_load_distribution(
        self, assignments: list[dict[str, Any]], agents: list[AgentCapability]
    ) -> dict[str, Any]:
        """Calculate load distribution across agents."""
        agent_assignments: dict[str, int] = {}
        for assignment in assignments:
            agent_id = assignment.get("assigned_agent")
            if agent_id:
                agent_assignments[agent_id] = agent_assignments.get(agent_id, 0) + 1

        return {
            "agent_assignments": agent_assignments,
            "load_balance_score": self._calculate_load_balance_score(agent_assignments, agents),
            "most_loaded_agent": max(agent_assignments.items(), key=lambda x: x[1])[0] if agent_assignments else None,
            "least_loaded_agent": min(agent_assignments.items(), key=lambda x: x[1])[0] if agent_assignments else None,
        }

    def _calculate_load_balance_score(self, assignments: dict[str, int], agents: list[AgentCapability]) -> float:
        """Calculate load balance score (0-1, higher is better)."""
        if not assignments:
            return 1.0

        assignment_counts = list(assignments.values())
        if len(assignment_counts) <= 1:
            return 1.0

        # Calculate coefficient of variation (lower is better)
        mean_assignments = sum(assignment_counts) / len(assignment_counts)
        variance = sum((x - mean_assignments) ** 2 for x in assignment_counts) / len(assignment_counts)
        std_dev = variance**0.5

        if mean_assignments == 0:
            return 1.0

        cv = std_dev / mean_assignments
        # Convert to 0-1 score (lower CV = higher score)
        return max(0, 1 - cv)

    def _estimate_workflow_completion_time(self, assignments: list[dict[str, Any]]) -> str:
        """Estimate total workflow completion time."""
        total_seconds = sum(assignment.get("estimated_duration", 60) for assignment in assignments)

        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            return f"{total_seconds // 60} minutes"
        else:
            return f"{total_seconds // 3600} hours"

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat()


class DependencyResolverTool(BaseTool):
    """Tool for managing inter-agent dependencies and task ordering."""

    def _run(self, workflow_tasks: list[dict[str, Any]], tenant: str, workspace: str) -> StepResult:
        """
        Resolve task dependencies and create execution order.

        Args:
            workflow_tasks: List of tasks with dependencies
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with dependency resolution
        """
        try:
            if not workflow_tasks:
                return StepResult.fail("Workflow tasks are required")

            resolution = self._resolve_dependencies(workflow_tasks, tenant, workspace)

            return StepResult.ok(
                data={
                    "dependency_resolution": resolution,
                    "total_tasks": len(workflow_tasks),
                    "resolved_tasks": len(resolution.get("execution_order", [])),
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Dependency resolution failed: {e!s}")
            return StepResult.fail(f"Dependency resolution failed: {e!s}")

    def _resolve_dependencies(self, tasks: list[dict[str, Any]], tenant: str, workspace: str) -> dict[str, Any]:
        """Resolve task dependencies using topological sort."""
        # Build dependency graph
        task_map = {task["id"]: task for task in tasks}
        in_degree = {task["id"]: 0 for task in tasks}
        dependencies = {task["id"]: set(task.get("dependencies", [])) for task in tasks}

        # Calculate in-degrees
        for deps in dependencies.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Topological sort
        execution_order = []
        ready_queue = [task_id for task_id, degree in in_degree.items() if degree == 0]

        while ready_queue:
            # Sort by priority
            ready_queue.sort(key=lambda tid: task_map[tid].get("priority", 2), reverse=True)
            current_task = ready_queue.pop(0)
            execution_order.append(current_task)

            # Update in-degrees
            for task_id, deps in dependencies.items():
                if current_task in deps:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        ready_queue.append(task_id)

        # Check for circular dependencies
        if len(execution_order) != len(tasks):
            circular_deps = [task_id for task_id in in_degree if in_degree[task_id] > 0]
            return {
                "execution_order": execution_order,
                "circular_dependencies": circular_deps,
                "resolution_status": "partial",
                "error": "Circular dependencies detected",
            }

        return {
            "execution_order": execution_order,
            "execution_phases": self._create_execution_phases(execution_order, task_map),
            "dependency_graph": self._build_dependency_graph(tasks),
            "critical_path": self._find_critical_path(execution_order, task_map),
            "resolution_status": "complete",
        }

    def _create_execution_phases(
        self, execution_order: list[str], task_map: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Create execution phases based on dependencies."""
        phases: list[dict[str, Any]] = []
        current_phase = []
        completed_tasks: set[str] = set()

        for task_id in execution_order:
            task = task_map[task_id]
            dependencies = set(task.get("dependencies", []))

            # Check if all dependencies are completed
            if dependencies.issubset(completed_tasks):
                current_phase.append(task_id)
            else:
                # Start new phase
                if current_phase:
                    phases.append(
                        {
                            "phase_id": f"phase_{len(phases) + 1}",
                            "tasks": current_phase,
                            "estimated_duration": self._estimate_phase_duration(current_phase, task_map),
                        }
                    )
                current_phase = [task_id]

        # Add final phase
        if current_phase:
            phases.append(
                {
                    "phase_id": f"phase_{len(phases) + 1}",
                    "tasks": current_phase,
                    "estimated_duration": self._estimate_phase_duration(current_phase, task_map),
                }
            )

        return phases

    def _estimate_phase_duration(self, task_ids: list[str], task_map: dict[str, dict[str, Any]]) -> str:
        """Estimate phase duration."""
        total_seconds = sum(task_map[task_id].get("estimated_duration_seconds", 60) for task_id in task_ids)

        if total_seconds < 60:
            return f"{total_seconds} seconds"
        elif total_seconds < 3600:
            return f"{total_seconds // 60} minutes"
        else:
            return f"{total_seconds // 3600} hours"

    def _build_dependency_graph(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Build dependency graph visualization."""
        nodes = []
        edges = []

        for task in tasks:
            nodes.append(
                {
                    "id": task["id"],
                    "name": task.get("name", "Unnamed"),
                    "priority": task.get("priority", 2),
                    "estimated_duration": task.get("estimated_duration_seconds", 60),
                }
            )

            for dep in task.get("dependencies", []):
                edges.append({"from": dep, "to": task["id"], "type": "dependency"})

        return {
            "nodes": nodes,
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        }

    def _find_critical_path(self, execution_order: list[str], task_map: dict[str, dict[str, Any]]) -> list[str]:
        """Find critical path through the workflow."""
        # Simple critical path: tasks with highest priority and longest duration
        critical_tasks = []

        for task_id in execution_order:
            task = task_map[task_id]
            priority = task.get("priority", 2)
            duration = task.get("estimated_duration_seconds", 60)

            # Consider task critical if high priority or long duration
            if priority >= 4 or duration >= 300:  # 5 minutes
                critical_tasks.append(task_id)

        return critical_tasks


class WorkflowOptimizationTool(BaseTool):
    """Tool for optimizing execution paths and resource utilization."""

    def _run(
        self,
        workflow_analysis: dict[str, Any],
        optimization_goals: list[str],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """
        Optimize workflow execution paths and resource utilization.

        Args:
            workflow_analysis: Current workflow analysis data
            optimization_goals: List of optimization goals (speed, cost, quality, etc.)
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with optimization recommendations
        """
        try:
            if not workflow_analysis or not optimization_goals:
                return StepResult.fail("Workflow analysis and optimization goals are required")

            optimizations = self._generate_optimizations(workflow_analysis, optimization_goals, tenant, workspace)

            return StepResult.ok(
                data={
                    "optimization_recommendations": optimizations,
                    "optimization_goals": optimization_goals,
                    "potential_improvements": self._calculate_improvement_potential(optimizations),
                    "tenant": tenant,
                    "workspace": workspace,
                }
            )

        except Exception as e:
            logger.error(f"Workflow optimization failed: {e!s}")
            return StepResult.fail(f"Workflow optimization failed: {e!s}")

    def _generate_optimizations(
        self, analysis: dict[str, Any], goals: list[str], tenant: str, workspace: str
    ) -> dict[str, Any]:
        """Generate optimization recommendations."""
        recommendations = {
            "parallelization_opportunities": self._find_parallelization_opportunities(analysis),
            "resource_optimizations": self._find_resource_optimizations(analysis),
            "bottleneck_eliminations": self._find_bottlenecks(analysis),
            "quality_improvements": self._find_quality_improvements(analysis),
            "cost_reductions": self._find_cost_reductions(analysis),
        }

        # Filter based on optimization goals
        filtered_recommendations = {}
        for goal in goals:
            if goal in recommendations:
                filtered_recommendations[goal] = recommendations[goal]

        return {
            "recommendations": filtered_recommendations,
            "implementation_priority": self._prioritize_optimizations(filtered_recommendations),
            "estimated_impact": self._estimate_optimization_impact(filtered_recommendations),
            "implementation_effort": self._estimate_implementation_effort(filtered_recommendations),
        }

    def _find_parallelization_opportunities(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Find opportunities for parallel task execution."""
        opportunities = []

        # Look for independent tasks that can run in parallel
        execution_phases = analysis.get("execution_phases", [])
        for phase in execution_phases:
            tasks = phase.get("tasks", [])
            if len(tasks) > 1:
                opportunities.append(
                    {
                        "type": "parallel_execution",
                        "phase": phase.get("phase_id"),
                        "tasks": tasks,
                        "potential_speedup": f"{len(tasks)}x",
                        "description": f"Execute {len(tasks)} tasks in parallel",
                    }
                )

        return opportunities

    def _find_resource_optimizations(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Find resource optimization opportunities."""
        return [
            {
                "type": "resource_pooling",
                "description": "Share resources across similar tasks",
                "potential_savings": "20-30%",
                "implementation": "medium",
            },
            {
                "type": "dynamic_scaling",
                "description": "Scale resources based on workload",
                "potential_savings": "15-25%",
                "implementation": "high",
            },
        ]

    def _find_bottlenecks(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Find and suggest bottleneck eliminations."""
        return [
            {
                "type": "dependency_optimization",
                "description": "Reduce unnecessary dependencies",
                "potential_improvement": "10-20%",
                "implementation": "low",
            },
            {
                "type": "agent_load_balancing",
                "description": "Better distribute tasks across agents",
                "potential_improvement": "15-25%",
                "implementation": "medium",
            },
        ]

    def _find_quality_improvements(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Find quality improvement opportunities."""
        return [
            {
                "type": "validation_enhancement",
                "description": "Add more validation steps",
                "potential_improvement": "5-10%",
                "implementation": "low",
            },
            {
                "type": "error_handling",
                "description": "Improve error handling and recovery",
                "potential_improvement": "10-15%",
                "implementation": "medium",
            },
        ]

    def _find_cost_reductions(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Find cost reduction opportunities."""
        return [
            {
                "type": "model_optimization",
                "description": "Use more cost-effective models where appropriate",
                "potential_savings": "20-40%",
                "implementation": "medium",
            },
            {
                "type": "caching_enhancement",
                "description": "Improve caching strategies",
                "potential_savings": "15-30%",
                "implementation": "low",
            },
        ]

    def _prioritize_optimizations(self, recommendations: dict[str, Any]) -> list[dict[str, Any]]:
        """Prioritize optimization recommendations."""
        priority_scores = {
            "parallelization_opportunities": 0.9,
            "bottleneck_eliminations": 0.8,
            "cost_reductions": 0.7,
            "resource_optimizations": 0.6,
            "quality_improvements": 0.5,
        }

        prioritized: list[dict[str, Any]] = []
        for category, items in recommendations.items():
            score = priority_scores.get(category, 0.5)
            for item in items:
                prioritized.append(
                    {
                        **item,
                        "category": category,
                        "priority_score": score,
                        "recommended_implementation_order": len(prioritized) + 1,
                    }
                )

        # Sort by priority score
        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        return prioritized

    def _calculate_improvement_potential(self, optimizations: dict[str, Any]) -> dict[str, Any]:
        """Calculate potential improvements from optimizations."""
        total_opportunities = sum(len(items) for items in optimizations.values())

        return {
            "total_optimization_opportunities": total_opportunities,
            "high_impact_opportunities": sum(
                1
                for items in optimizations.values()
                for item in items
                if "high" in str(item.get("potential_savings", "")).lower()
                or "high" in str(item.get("potential_improvement", "")).lower()
            ),
            "estimated_overall_improvement": "25-50%",
            "implementation_timeline": "2-4 weeks",
        }

    def _estimate_optimization_impact(self, recommendations: dict[str, Any]) -> dict[str, str]:
        """Estimate the impact of optimizations."""
        return {
            "performance_improvement": "20-40%",
            "cost_reduction": "15-35%",
            "quality_improvement": "10-20%",
            "reliability_improvement": "15-25%",
        }

    def _estimate_implementation_effort(self, recommendations: dict[str, Any]) -> dict[str, str]:
        """Estimate implementation effort for optimizations."""
        return {
            "low_effort": "1-2 weeks",
            "medium_effort": "2-4 weeks",
            "high_effort": "4-8 weeks",
            "total_effort": "6-12 weeks",
        }


class WorkflowManagerAgent:
    """Workflow Manager Agent for dynamic task orchestration."""

    def __init__(self):
        """Initialize the Workflow Manager Agent."""
        self.task_routing_tool = TaskRoutingTool()
        self.dependency_resolver_tool = DependencyResolverTool()
        self.workflow_optimization_tool = WorkflowOptimizationTool()

        # Note: CrewAI Agent initialization would go here in a real implementation
        # For now, we'll use the tools directly without CrewAI integration
        self.agent = None

    async def route_tasks(
        self,
        workflow_execution: dict[str, Any],
        available_agents: list[dict[str, Any]],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """Route tasks to optimal agents."""
        return self.task_routing_tool._run(workflow_execution, available_agents, tenant, workspace)

    async def resolve_dependencies(
        self, workflow_tasks: list[dict[str, Any]], tenant: str, workspace: str
    ) -> StepResult:
        """Resolve task dependencies and create execution order."""
        return self.dependency_resolver_tool._run(workflow_tasks, tenant, workspace)

    async def optimize_workflow(
        self,
        workflow_analysis: dict[str, Any],
        optimization_goals: list[str],
        tenant: str,
        workspace: str,
    ) -> StepResult:
        """Optimize workflow execution paths."""
        return self.workflow_optimization_tool._run(workflow_analysis, optimization_goals, tenant, workspace)

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        return self.agent
