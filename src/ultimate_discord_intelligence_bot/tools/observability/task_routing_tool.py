from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import Any
from crewai.tools import BaseTool
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """Represents an agent's capabilities and current state."""

    agent_id: str
    name: str
    capabilities: list[str]
    current_load: float
    max_concurrent_tasks: int
    average_task_duration_minutes: float
    success_rate: float
    cost_per_task: float
    latency_ms: float
    last_updated: float


@dataclass
class TaskRequirement:
    """Represents task requirements for routing decisions."""

    task_id: str
    name: str
    required_capabilities: list[str]
    priority: int
    estimated_duration_minutes: int
    complexity_score: float
    deadline_minutes: int | None = None
    resource_requirements: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskAssignment:
    """Represents a task assignment to an agent."""

    assignment_id: str
    task_id: str
    agent_id: str
    assigned_at: float
    estimated_start_time: float
    estimated_completion_time: float
    priority: int
    status: str = "assigned"
    routing_confidence: float = 0.0
    routing_reason: str = ""


class TaskRoutingTool(BaseTool):
    """
    Task routing tool for intelligent task distribution with capability matching.
    Routes tasks to optimal agents based on capabilities, current load, performance
    history, and priority levels with comprehensive load balancing.
    """

    name: str = "task_routing_tool"
    description: str = "Intelligent task distribution with capability matching and load balancing. Routes tasks to optimal agents based on capabilities, current load, performance history, and priority levels."

    def _run(
        self, workflow_execution: dict[str, Any], available_agents: list[dict[str, Any]], tenant: str, workspace: str
    ) -> StepResult:
        """
        Route tasks to optimal agents based on capabilities and load balancing.

        Args:
            workflow_execution: Workflow execution data with tasks and execution order
            available_agents: List of available agents with their capabilities
            tenant: Tenant identifier for data isolation
            workspace: Workspace identifier for organization

        Returns:
            StepResult with task routing data
        """
        metrics = get_metrics()
        start_time = time.time()
        try:
            logger.info(f"Routing tasks for tenant '{tenant}', workspace '{workspace}'")
            logger.debug(f"Workflow Execution: {workflow_execution}")
            logger.debug(f"Available Agents: {available_agents}")
            if not workflow_execution or not available_agents:
                return StepResult.fail("Workflow execution and available agents are required")
            if not tenant or not workspace:
                return StepResult.fail("Tenant and workspace are required")
            tasks = self._parse_workflow_tasks(workflow_execution)
            execution_order = workflow_execution.get("execution_order", [])
            agent_capabilities = self._create_agent_capabilities(available_agents)
            assignments = self._route_tasks_intelligently(tasks, agent_capabilities, execution_order)
            routing_metrics = self._calculate_routing_metrics(assignments, agent_capabilities)
            routing_report = {
                "routing_id": f"routing_{int(time.time())}_{tenant}_{workspace}",
                "workflow_id": workflow_execution.get("id", "unknown"),
                "assignments": [assignment.__dict__ for assignment in assignments],
                "routing_metrics": routing_metrics,
                "agent_utilization": self._calculate_agent_utilization(assignments, agent_capabilities),
                "load_balancing_score": self._calculate_load_balancing_score(assignments, agent_capabilities),
                "created_at": self._get_current_timestamp(),
                "tenant": tenant,
                "workspace": workspace,
                "status": "routed",
                "version": "1.0",
            }
            logger.info("Task routing completed successfully")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "success"})
            return StepResult.success(routing_report)
        except Exception as e:
            logger.error(f"Task routing failed: {e!s}")
            metrics.counter("tool_runs_total", labels={"tool": self.__class__.__name__, "outcome": "error"})
            return StepResult.fail(f"Task routing failed: {e!s}")
        finally:
            metrics.histogram("tool_run_seconds", time.time() - start_time, labels={"tool": self.__class__.__name__})

    def _parse_workflow_tasks(self, workflow_execution: dict[str, Any]) -> list[TaskRequirement]:
        """Parse workflow execution to extract task requirements."""
        tasks = []
        workflow_tasks = workflow_execution.get("tasks", [])
        for task_data in workflow_tasks:
            task = TaskRequirement(
                task_id=task_data.get("id", f"task_{len(tasks)}"),
                name=task_data.get("name", "Untitled Task"),
                required_capabilities=task_data.get("required_capabilities", []),
                priority=task_data.get("priority", 1),
                estimated_duration_minutes=task_data.get("estimated_duration_minutes", 60),
                complexity_score=task_data.get("complexity_score", 0.5),
                deadline_minutes=task_data.get("deadline_minutes"),
                resource_requirements=task_data.get("resource_requirements", {}),
            )
            tasks.append(task)
        return tasks

    def _create_agent_capabilities(self, available_agents: list[dict[str, Any]]) -> list[AgentCapability]:
        """Create agent capability objects from available agents data."""
        capabilities = []
        current_time = self._get_current_timestamp()
        for agent_data in available_agents:
            capability = AgentCapability(
                agent_id=agent_data.get("id", f"agent_{len(capabilities)}"),
                name=agent_data.get("name", "Unknown Agent"),
                capabilities=agent_data.get("capabilities", []),
                current_load=agent_data.get("current_load", 0.0),
                max_concurrent_tasks=agent_data.get("max_concurrent_tasks", 5),
                average_task_duration_minutes=agent_data.get("average_task_duration_minutes", 60),
                success_rate=agent_data.get("success_rate", 0.9),
                cost_per_task=agent_data.get("cost_per_task", 0.1),
                latency_ms=agent_data.get("latency_ms", 1000),
                last_updated=current_time,
            )
            capabilities.append(capability)
        return capabilities

    def _route_tasks_intelligently(
        self, tasks: list[TaskRequirement], agent_capabilities: list[AgentCapability], execution_order: list[str]
    ) -> list[TaskAssignment]:
        """Route tasks to agents using intelligent assignment algorithm."""
        assignments = []
        current_time = self._get_current_timestamp()
        if execution_order:
            task_map = {task.task_id: task for task in tasks}
            ordered_tasks = [task_map.get(task_id) for task_id in execution_order if task_id in task_map]
            ordered_tasks.extend([task for task in tasks if task.task_id not in execution_order])
            tasks = ordered_tasks
        tasks.sort(key=lambda x: x.priority, reverse=True)
        for task in tasks:
            suitable_agents = self._find_suitable_agents(task, agent_capabilities)
            if suitable_agents:
                best_agent = self._select_best_agent(task, suitable_agents)
                assignment = TaskAssignment(
                    assignment_id=f"assign_{task.task_id}_{int(current_time)}",
                    task_id=task.task_id,
                    agent_id=best_agent.agent_id,
                    assigned_at=current_time,
                    estimated_start_time=current_time + best_agent.current_load * 60,
                    estimated_completion_time=current_time
                    + best_agent.current_load * 60
                    + task.estimated_duration_minutes * 60,
                    priority=task.priority,
                    routing_confidence=self._calculate_routing_confidence(task, best_agent),
                    routing_reason=self._generate_routing_reason(task, best_agent),
                )
                assignments.append(assignment)
                self._update_agent_load(best_agent, task)
            else:
                logger.warning(f"No suitable agent found for task {task.task_id}")
        return assignments

    def _find_suitable_agents(
        self, task: TaskRequirement, agent_capabilities: list[AgentCapability]
    ) -> list[AgentCapability]:
        """Find agents that can handle the task requirements."""
        suitable_agents = []
        for agent in agent_capabilities:
            if self._agent_has_capabilities(agent, task.required_capabilities) and agent.current_load < 0.9:
                suitable_agents.append(agent)
        return suitable_agents

    def _agent_has_capabilities(self, agent: AgentCapability, required_capabilities: list[str]) -> bool:
        """Check if agent has all required capabilities."""
        return all((capability in agent.capabilities for capability in required_capabilities))

    def _select_best_agent(self, task: TaskRequirement, suitable_agents: list[AgentCapability]) -> AgentCapability:
        """Select the best agent using scoring algorithm."""
        best_agent = None
        best_score = -1.0
        for agent in suitable_agents:
            score = self._calculate_agent_score(task, agent)
            if score > best_score:
                best_score = score
                best_agent = agent
        return best_agent or suitable_agents[0]

    def _calculate_agent_score(self, task: TaskRequirement, agent: AgentCapability) -> float:
        """Calculate agent suitability score for a task."""
        load_factor = 1.0 - agent.current_load
        success_factor = agent.success_rate
        latency_factor = max(0.1, 1.0 - agent.latency_ms / 10000.0)
        cost_factor = max(0.1, 1.0 - agent.cost_per_task / 1.0)
        capability_factor = len(set(task.required_capabilities) & set(agent.capabilities)) / len(
            task.required_capabilities
        )
        priority_factor = 0.5 + task.priority * 0.1
        score = (
            load_factor * 0.3
            + success_factor * 0.25
            + latency_factor * 0.2
            + cost_factor * 0.15
            + capability_factor * 0.1
        ) * priority_factor
        return score

    def _calculate_routing_confidence(self, task: TaskRequirement, agent: AgentCapability) -> float:
        """Calculate confidence in the routing decision."""
        capability_match = len(set(task.required_capabilities) & set(agent.capabilities)) / len(
            task.required_capabilities
        )
        confidence = agent.success_rate * 0.7 + capability_match * 0.3
        return min(1.0, confidence)

    def _generate_routing_reason(self, task: TaskRequirement, agent: AgentCapability) -> str:
        """Generate human-readable reason for routing decision."""
        reasons = []
        if agent.current_load < 0.3:
            reasons.append("low current load")
        elif agent.current_load < 0.6:
            reasons.append("moderate current load")
        if agent.success_rate > 0.95:
            reasons.append("high success rate")
        elif agent.success_rate > 0.9:
            reasons.append("good success rate")
        if agent.latency_ms < 500:
            reasons.append("low latency")
        elif agent.latency_ms < 1000:
            reasons.append("acceptable latency")
        capability_match = len(set(task.required_capabilities) & set(agent.capabilities))
        if capability_match == len(task.required_capabilities):
            reasons.append("perfect capability match")
        elif capability_match > len(task.required_capabilities) * 0.8:
            reasons.append("good capability match")
        return f"Selected based on: {', '.join(reasons)}" if reasons else "Selected as best available option"

    def _update_agent_load(self, agent: AgentCapability, task: TaskRequirement):
        """Update agent load after task assignment."""
        load_increase = task.complexity_score * 0.1 + task.estimated_duration_minutes / 600.0
        agent.current_load = min(1.0, agent.current_load + load_increase)

    def _calculate_routing_metrics(
        self, assignments: list[TaskAssignment], agent_capabilities: list[AgentCapability]
    ) -> dict[str, Any]:
        """Calculate routing performance metrics."""
        if not assignments:
            return {"total_assignments": 0, "average_confidence": 0.0, "routing_efficiency": 0.0}
        total_assignments = len(assignments)
        average_confidence = sum((assignment.routing_confidence for assignment in assignments)) / total_assignments
        agent_utilization = self._calculate_agent_utilization(assignments, agent_capabilities)
        routing_efficiency = sum(agent_utilization.values()) / len(agent_utilization) if agent_utilization else 0.0
        return {
            "total_assignments": total_assignments,
            "average_confidence": average_confidence,
            "routing_efficiency": routing_efficiency,
            "high_confidence_assignments": sum((1 for a in assignments if a.routing_confidence > 0.8)),
            "low_confidence_assignments": sum((1 for a in assignments if a.routing_confidence < 0.6)),
        }

    def _calculate_agent_utilization(
        self, assignments: list[TaskAssignment], agent_capabilities: list[AgentCapability]
    ) -> dict[str, float]:
        """Calculate utilization for each agent."""
        agent_tasks = {}
        for assignment in assignments:
            agent_tasks[assignment.agent_id] = agent_tasks.get(assignment.agent_id, 0) + 1
        utilization = {}
        for agent in agent_capabilities:
            task_count = agent_tasks.get(agent.agent_id, 0)
            max_tasks = agent.max_concurrent_tasks
            utilization[agent.agent_id] = min(1.0, task_count / max_tasks) if max_tasks > 0 else 0.0
        return utilization

    def _calculate_load_balancing_score(
        self, assignments: list[TaskAssignment], agent_capabilities: list[AgentCapability]
    ) -> float:
        """Calculate load balancing score (1.0 = perfectly balanced, 0.0 = completely unbalanced)."""
        if not assignments or not agent_capabilities:
            return 1.0
        agent_utilization = self._calculate_agent_utilization(assignments, agent_capabilities)
        utilizations = list(agent_utilization.values())
        if not utilizations:
            return 1.0
        mean_util = sum(utilizations) / len(utilizations)
        if mean_util == 0:
            return 1.0
        variance = sum(((util - mean_util) ** 2 for util in utilizations)) / len(utilizations)
        std_dev = variance**0.5
        coefficient_of_variation = std_dev / mean_util
        balance_score = max(0.0, 1.0 - coefficient_of_variation)
        return balance_score

    def _get_current_timestamp(self) -> float:
        """Returns the current UTC timestamp."""
        return time.time()
