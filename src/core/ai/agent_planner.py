"""
Advanced agent planning patterns for the Ultimate Discord Intelligence Bot.

Provides sophisticated planning capabilities including hierarchical task decomposition,
multi-agent coordination, dynamic replanning, and adaptive strategy selection.
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class PlanningStrategy(Enum):
    """Planning strategies for agent coordination."""

    HIERARCHICAL = "hierarchical"
    DECENTRALIZED = "decentralized"
    CENTRALIZED = "centralized"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = "critical"  # System-critical tasks
    HIGH = "high"  # Important user requests
    NORMAL = "normal"  # Standard operations
    LOW = "low"  # Background tasks
    MAINTENANCE = "maintenance"  # System maintenance


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class AgentCapability(Enum):
    """Agent capability types."""

    CONTENT_ANALYSIS = "content_analysis"
    FACT_CHECKING = "fact_checking"
    DEBATE_SCORING = "debate_scoring"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SUMMARIZATION = "summarization"
    TRANSCRIPTION = "transcription"
    MODERATION = "moderation"
    RESEARCH = "research"
    TRANSLATION = "translation"
    VISUAL_ANALYSIS = "visual_analysis"


class CoordinationPattern(Enum):
    """Agent coordination patterns."""

    SEQUENTIAL = "sequential"  # Tasks executed in sequence
    PARALLEL = "parallel"  # Tasks executed concurrently
    PIPELINE = "pipeline"  # Streaming pipeline processing
    HIERARCHICAL = "hierarchical"  # Hierarchical task decomposition
    COLLABORATIVE = "collaborative"  # Collaborative problem solving
    COMPETITIVE = "competitive"  # Competitive task assignment


@dataclass
class Task:
    """Task definition for agent planning."""

    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    required_capabilities: set[AgentCapability]
    estimated_duration: float  # in seconds
    dependencies: set[str] = field(default_factory=set)
    resources_required: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_ready(self) -> bool:
        """Check if task is ready for execution."""
        return len(self.dependencies) == 0

    @property
    def complexity_score(self) -> float:
        """Calculate task complexity score."""
        base_complexity = len(self.required_capabilities) * 0.1
        duration_factor = min(1.0, self.estimated_duration / 3600)  # Normalize to hours
        constraint_factor = len(self.constraints) * 0.05

        return min(1.0, base_complexity + duration_factor + constraint_factor)

    @property
    def urgency_score(self) -> float:
        """Calculate task urgency score."""
        priority_scores = {
            TaskPriority.CRITICAL: 1.0,
            TaskPriority.HIGH: 0.8,
            TaskPriority.NORMAL: 0.6,
            TaskPriority.LOW: 0.4,
            TaskPriority.MAINTENANCE: 0.2,
        }
        return priority_scores.get(self.priority, 0.5)


@dataclass
class Agent:
    """Agent definition for planning."""

    agent_id: str
    name: str
    capabilities: set[AgentCapability]
    current_load: float = 0.0
    max_capacity: float = 1.0
    performance_score: float = 1.0
    availability: bool = True
    current_tasks: set[str] = field(default_factory=set)
    specialization_areas: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available_capacity(self) -> float:
        """Get available capacity."""
        return max(0.0, self.max_capacity - self.current_load)

    @property
    def is_available(self) -> bool:
        """Check if agent is available."""
        return self.availability and self.available_capacity > 0.1

    def capability_match_score(self, required_capabilities: set[AgentCapability]) -> float:
        """Calculate capability match score."""
        if not required_capabilities:
            return 1.0

        intersection = required_capabilities.intersection(self.capabilities)
        return len(intersection) / len(required_capabilities)

    def can_handle_task(self, task: Task) -> bool:
        """Check if agent can handle a task."""
        if not self.is_available:
            return False

        capability_match = self.capability_match_score(task.required_capabilities)
        capacity_match = self.available_capacity >= task.complexity_score

        return capability_match >= 0.5 and capacity_match


@dataclass
class ExecutionPlan:
    """Execution plan for task coordination."""

    plan_id: str
    tasks: list[Task]
    task_assignments: dict[str, str]  # task_id -> agent_id
    execution_order: list[str]  # task_ids in execution order
    estimated_completion_time: float
    coordination_pattern: CoordinationPattern
    dependencies: dict[str, set[str]] = field(default_factory=dict)
    resource_allocation: dict[str, dict[str, Any]] = field(default_factory=dict)
    fallback_plans: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Check if plan is valid."""
        # Check if all tasks are assigned
        assigned_tasks = set(self.task_assignments.keys())
        plan_tasks = {task.task_id for task in self.tasks}

        if assigned_tasks != plan_tasks:
            return False

        # Check if execution order is valid
        task_ids = {task.task_id for task in self.tasks}
        return set(self.execution_order).issubset(task_ids)

    @property
    def total_complexity(self) -> float:
        """Calculate total plan complexity."""
        return sum(task.complexity_score for task in self.tasks)

    @property
    def critical_path_length(self) -> float:
        """Calculate critical path length."""
        # Simplified critical path calculation
        total_duration = 0.0
        for task_id in self.execution_order:
            task = next((t for t in self.tasks if t.task_id == task_id), None)
            if task:
                total_duration += task.estimated_duration

        return total_duration


@dataclass
class PlanningContext:
    """Context for planning decisions."""

    available_agents: list[Agent]
    system_load: float = 0.0
    resource_constraints: dict[str, Any] = field(default_factory=dict)
    time_constraints: dict[str, float] = field(default_factory=dict)
    quality_requirements: dict[str, float] = field(default_factory=dict)
    optimization_goals: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_capacity(self) -> float:
        """Get total system capacity."""
        return sum(agent.max_capacity for agent in self.available_agents)

    @property
    def available_capacity(self) -> float:
        """Get available system capacity."""
        return sum(agent.available_capacity for agent in self.available_agents)

    @property
    def capacity_utilization(self) -> float:
        """Get capacity utilization percentage."""
        if self.total_capacity == 0:
            return 0.0
        return (self.total_capacity - self.available_capacity) / self.total_capacity


class AgentPlanner:
    """
    Advanced agent planner for multi-agent coordination and task planning.

    Provides sophisticated planning capabilities including hierarchical decomposition,
    dynamic replanning, and adaptive strategy selection.
    """

    def __init__(self, strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE):
        """Initialize agent planner."""
        self.strategy = strategy
        self.agents: dict[str, Agent] = {}
        self.execution_plans: dict[str, ExecutionPlan] = {}
        self.task_queue: list[Task] = []
        self.completed_tasks: set[str] = set()
        self.failed_tasks: set[str] = set()

        # Planning statistics
        self.planning_stats = {
            "plans_created": 0,
            "tasks_assigned": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_planning_time": 0.0,
            "average_execution_time": 0.0,
        }

        # Planning cache
        self.planning_cache: dict[str, ExecutionPlan] = {}
        self.capability_cache: dict[str, set[AgentCapability]] = {}

        logger.info(f"Agent planner initialized with strategy: {strategy.value}")

    async def register_agent(self, agent: Agent) -> bool:
        """Register an agent with the planner."""
        try:
            if agent.agent_id in self.agents:
                logger.warning(f"Agent {agent.agent_id} already registered")
                return False

            self.agents[agent.agent_id] = agent
            self.capability_cache[agent.agent_id] = agent.capabilities.copy()

            logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False

    async def submit_task(self, task: Task) -> bool:
        """Submit a task for planning."""
        try:
            if task.task_id in [t.task_id for t in self.task_queue]:
                logger.warning(f"Task {task.task_id} already in queue")
                return False

            self.task_queue.append(task)
            logger.info(f"Submitted task: {task.task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False

    async def create_execution_plan(
        self,
        tasks: list[Task],
        context: PlanningContext,
        plan_id: str | None = None,
    ) -> ExecutionPlan | None:
        """Create an execution plan for tasks."""
        start_time = time.time()

        try:
            if not tasks:
                logger.warning("No tasks provided for planning")
                return None

            plan_id = plan_id or f"plan_{int(time.time())}"

            # Select planning strategy
            strategy = await self._select_planning_strategy(tasks, context)

            # Create plan based on strategy
            if strategy == PlanningStrategy.HIERARCHICAL:
                plan = await self._create_hierarchical_plan(tasks, context, plan_id)
            elif strategy == PlanningStrategy.DECENTRALIZED:
                plan = await self._create_decentralized_plan(tasks, context, plan_id)
            elif strategy == PlanningStrategy.CENTRALIZED:
                plan = await self._create_centralized_plan(tasks, context, plan_id)
            elif strategy == PlanningStrategy.HYBRID:
                plan = await self._create_hybrid_plan(tasks, context, plan_id)
            else:  # ADAPTIVE
                plan = await self._create_adaptive_plan(tasks, context, plan_id)

            if plan and plan.is_valid:
                self.execution_plans[plan_id] = plan
                self.planning_stats["plans_created"] += 1

                planning_time = time.time() - start_time
                self._update_planning_stats(planning_time)

                logger.info(f"Created execution plan: {plan_id}")
                return plan
            else:
                logger.error(f"Failed to create valid plan: {plan_id}")
                return None

        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            return None

    async def _select_planning_strategy(self, tasks: list[Task], context: PlanningContext) -> PlanningStrategy:
        """Select optimal planning strategy."""
        try:
            # Analyze task characteristics
            total_complexity = sum(task.complexity_score for task in tasks)
            avg_urgency = np.mean([task.urgency_score for task in tasks])
            dependency_count = sum(len(task.dependencies) for task in tasks)

            # Analyze system context
            capacity_utilization = context.capacity_utilization
            agent_count = len(context.available_agents)

            # Strategy selection logic
            if total_complexity > 0.8 and dependency_count > len(tasks) * 0.5:
                return PlanningStrategy.HIERARCHICAL
            elif agent_count > 5 and capacity_utilization < 0.7:
                return PlanningStrategy.DECENTRALIZED
            elif avg_urgency > 0.8 and agent_count <= 3:
                return PlanningStrategy.CENTRALIZED
            elif total_complexity > 0.5 and dependency_count > 0:
                return PlanningStrategy.HYBRID
            else:
                return PlanningStrategy.ADAPTIVE

        except Exception as e:
            logger.error(f"Strategy selection failed: {e}")
            return self.strategy

    async def _create_hierarchical_plan(
        self, tasks: list[Task], context: PlanningContext, plan_id: str
    ) -> ExecutionPlan | None:
        """Create hierarchical execution plan."""
        try:
            # Sort tasks by priority and dependencies
            sorted_tasks = await self._sort_tasks_hierarchically(tasks)

            # Assign tasks to agents hierarchically
            task_assignments = {}
            execution_order = []

            for task in sorted_tasks:
                # Find best agent for task
                best_agent = await self._find_best_agent(task, context.available_agents)
                if best_agent:
                    task_assignments[task.task_id] = best_agent.agent_id
                    execution_order.append(task.task_id)
                else:
                    logger.warning(f"No suitable agent found for task: {task.task_id}")
                    return None

            # Calculate execution time
            estimated_time = sum(task.estimated_duration for task in tasks)

            return ExecutionPlan(
                plan_id=plan_id,
                tasks=sorted_tasks,
                task_assignments=task_assignments,
                execution_order=execution_order,
                estimated_completion_time=estimated_time,
                coordination_pattern=CoordinationPattern.HIERARCHICAL,
                dependencies=await self._build_dependency_graph(tasks),
            )

        except Exception as e:
            logger.error(f"Hierarchical planning failed: {e}")
            return None

    async def _create_decentralized_plan(
        self, tasks: list[Task], context: PlanningContext, plan_id: str
    ) -> ExecutionPlan | None:
        """Create decentralized execution plan."""
        try:
            # Assign tasks based on agent capabilities and load
            task_assignments = {}
            execution_order = []

            # Sort tasks by urgency
            urgent_tasks = sorted(tasks, key=lambda t: t.urgency_score, reverse=True)

            for task in urgent_tasks:
                # Find available agent with best capability match
                available_agents = [a for a in context.available_agents if a.can_handle_task(task)]

                if available_agents:
                    # Select agent with best score (capability + availability)
                    best_agent = max(
                        available_agents,
                        key=lambda a: (
                            a.capability_match_score(task.required_capabilities) * 0.7 + a.available_capacity * 0.3
                        ),
                    )

                    task_assignments[task.task_id] = best_agent.agent_id
                    execution_order.append(task.task_id)
                else:
                    logger.warning(f"No available agent for task: {task.task_id}")
                    return None

            estimated_time = sum(task.estimated_duration for task in tasks)

            return ExecutionPlan(
                plan_id=plan_id,
                tasks=urgent_tasks,
                task_assignments=task_assignments,
                execution_order=execution_order,
                estimated_completion_time=estimated_time,
                coordination_pattern=CoordinationPattern.PARALLEL,
            )

        except Exception as e:
            logger.error(f"Decentralized planning failed: {e}")
            return None

    async def _create_centralized_plan(
        self, tasks: list[Task], context: PlanningContext, plan_id: str
    ) -> ExecutionPlan | None:
        """Create centralized execution plan."""
        try:
            # Central coordinator assigns all tasks
            task_assignments = {}
            execution_order = []

            # Sort tasks by priority
            priority_order = [
                TaskPriority.CRITICAL,
                TaskPriority.HIGH,
                TaskPriority.NORMAL,
                TaskPriority.LOW,
                TaskPriority.MAINTENANCE,
            ]

            sorted_tasks = []
            for priority in priority_order:
                priority_tasks = [t for t in tasks if t.priority == priority]
                sorted_tasks.extend(sorted(priority_tasks, key=lambda t: t.estimated_duration))

            for task in sorted_tasks:
                # Assign to most capable agent
                best_agent = await self._find_most_capable_agent(task, context.available_agents)
                if best_agent:
                    task_assignments[task.task_id] = best_agent.agent_id
                    execution_order.append(task.task_id)
                else:
                    logger.warning(f"No capable agent for task: {task.task_id}")
                    return None

            estimated_time = sum(task.estimated_duration for task in sorted_tasks)

            return ExecutionPlan(
                plan_id=plan_id,
                tasks=sorted_tasks,
                task_assignments=task_assignments,
                execution_order=execution_order,
                estimated_completion_time=estimated_time,
                coordination_pattern=CoordinationPattern.SEQUENTIAL,
            )

        except Exception as e:
            logger.error(f"Centralized planning failed: {e}")
            return None

    async def _create_hybrid_plan(
        self, tasks: list[Task], context: PlanningContext, plan_id: str
    ) -> ExecutionPlan | None:
        """Create hybrid execution plan."""
        try:
            # Combine hierarchical and decentralized approaches
            critical_tasks = [t for t in tasks if t.priority == TaskPriority.CRITICAL]
            other_tasks = [t for t in tasks if t.priority != TaskPriority.CRITICAL]

            # Use centralized for critical tasks
            critical_plan = None
            if critical_tasks:
                critical_plan = await self._create_centralized_plan(critical_tasks, context, f"{plan_id}_critical")

            # Use decentralized for other tasks
            other_plan = None
            if other_tasks:
                other_plan = await self._create_decentralized_plan(other_tasks, context, f"{plan_id}_other")

            # Merge plans
            if critical_plan and other_plan:
                merged_tasks = critical_plan.tasks + other_plan.tasks
                merged_assignments = {
                    **critical_plan.task_assignments,
                    **other_plan.task_assignments,
                }
                merged_order = critical_plan.execution_order + other_plan.execution_order
                merged_time = critical_plan.estimated_completion_time + other_plan.estimated_completion_time

                return ExecutionPlan(
                    plan_id=plan_id,
                    tasks=merged_tasks,
                    task_assignments=merged_assignments,
                    execution_order=merged_order,
                    estimated_completion_time=merged_time,
                    coordination_pattern=CoordinationPattern.HIERARCHICAL,
                )
            elif critical_plan:
                return critical_plan
            elif other_plan:
                return other_plan
            else:
                return None

        except Exception as e:
            logger.error(f"Hybrid planning failed: {e}")
            return None

    async def _create_adaptive_plan(
        self, tasks: list[Task], context: PlanningContext, plan_id: str
    ) -> ExecutionPlan | None:
        """Create adaptive execution plan."""
        try:
            # Dynamically adapt based on current conditions
            if context.capacity_utilization < 0.5:
                # Low load - use decentralized
                return await self._create_decentralized_plan(tasks, context, plan_id)
            elif len(tasks) > 10:
                # Many tasks - use hierarchical
                return await self._create_hierarchical_plan(tasks, context, plan_id)
            else:
                # Default to centralized
                return await self._create_centralized_plan(tasks, context, plan_id)

        except Exception as e:
            logger.error(f"Adaptive planning failed: {e}")
            return None

    async def _sort_tasks_hierarchically(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks in hierarchical order."""
        try:
            # Topological sort based on dependencies
            sorted_tasks = []
            remaining_tasks = tasks.copy()

            while remaining_tasks:
                # Find tasks with no unmet dependencies
                ready_tasks = [
                    task for task in remaining_tasks if all(dep in self.completed_tasks for dep in task.dependencies)
                ]

                if not ready_tasks:
                    # Circular dependency or missing dependency
                    logger.warning("Circular dependency detected, breaking with priority order")
                    ready_tasks = [min(remaining_tasks, key=lambda t: t.priority.value)]

                # Sort ready tasks by priority and urgency
                ready_tasks.sort(key=lambda t: (t.priority.value, -t.urgency_score))

                sorted_tasks.extend(ready_tasks)
                remaining_tasks = [t for t in remaining_tasks if t not in ready_tasks]

            return sorted_tasks

        except Exception as e:
            logger.error(f"Hierarchical sorting failed: {e}")
            return tasks

    async def _find_best_agent(self, task: Task, agents: list[Agent]) -> Agent | None:
        """Find best agent for a task."""
        try:
            suitable_agents = [a for a in agents if a.can_handle_task(task)]

            if not suitable_agents:
                return None

            # Score agents based on capability match and availability
            scored_agents = []
            for agent in suitable_agents:
                capability_score = agent.capability_match_score(task.required_capabilities)
                availability_score = agent.available_capacity
                performance_score = agent.performance_score

                total_score = capability_score * 0.5 + availability_score * 0.3 + performance_score * 0.2

                scored_agents.append((total_score, agent))

            # Return best agent
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            return scored_agents[0][1]

        except Exception as e:
            logger.error(f"Agent finding failed: {e}")
            return None

    async def _find_most_capable_agent(self, task: Task, agents: list[Agent]) -> Agent | None:
        """Find most capable agent for a task."""
        try:
            capable_agents = [a for a in agents if a.capability_match_score(task.required_capabilities) >= 0.8]

            if not capable_agents:
                return None

            # Return agent with highest capability match
            return max(
                capable_agents,
                key=lambda a: a.capability_match_score(task.required_capabilities),
            )

        except Exception as e:
            logger.error(f"Capable agent finding failed: {e}")
            return None

    async def _build_dependency_graph(self, tasks: list[Task]) -> dict[str, set[str]]:
        """Build dependency graph for tasks."""
        try:
            graph = {}
            for task in tasks:
                graph[task.task_id] = task.dependencies.copy()
            return graph

        except Exception as e:
            logger.error(f"Dependency graph building failed: {e}")
            return {}

    def _update_planning_stats(self, planning_time: float) -> None:
        """Update planning statistics."""
        try:
            total_plans = self.planning_stats["plans_created"]
            current_avg = self.planning_stats["average_planning_time"]

            # Update running average
            new_avg = (current_avg * (total_plans - 1) + planning_time) / total_plans
            self.planning_stats["average_planning_time"] = new_avg

        except Exception as e:
            logger.error(f"Planning stats update failed: {e}")

    async def get_planning_statistics(self) -> dict[str, Any]:
        """Get planning statistics."""
        return self.planning_stats.copy()

    async def clear_cache(self) -> None:
        """Clear planning cache."""
        self.planning_cache.clear()
        self.capability_cache.clear()
        logger.info("Planning cache cleared")

    async def __aenter__(self) -> "AgentPlanner":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.clear_cache()
