#!/usr/bin/env python3
"""
Adaptive prioritization system for dynamic task management and resource allocation.

This system continuously evaluates task priorities based on system metrics, user feedback,
resource availability, and business impact to ensure optimal resource utilization.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()

# Constants for scoring thresholds
ERROR_RATE_THRESHOLD = 0.05
HIGH_LATENCY_THRESHOLD = 2000  # ms
CRITICAL_SCORE_THRESHOLD = 0.8
HIGH_SCORE_THRESHOLD = 0.6
MEDIUM_SCORE_THRESHOLD = 0.4
HISTORY_MAX_SIZE = 1000
HISTORY_TRIM_SIZE = 500


class TaskPriority(Enum):
    """Task priority levels with integer values for ordering.

    The previous implementation stored ``(int, description)`` tuples as enum
    values and reassigned ``self.value`` inside ``__init__`` which is not
    supported by :class:`Enum` (``.value`` is reserved). We now keep the enum
    values as plain integers (stable ordering) and maintain a separate mapping
    for descriptions.
    """

    P0_CRITICAL = 0
    P1_HIGH = 1
    P2_MEDIUM = 2
    P3_LOW = 3

    @property
    def description(self) -> str:  # convenience accessor
        return {
            TaskPriority.P0_CRITICAL: "System stability, security, or core functionality",
            TaskPriority.P1_HIGH: "Performance improvements, user experience",
            TaskPriority.P2_MEDIUM: "Feature enhancements, technical debt",
            TaskPriority.P3_LOW: "Documentation, optimization, future-proofing",
        }[self]


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Types of resources that can constrain task execution."""

    DEVELOPER_TIME = "developer_time"
    COMPUTE_RESOURCES = "compute_resources"
    API_BUDGET = "api_budget"
    EXTERNAL_DEPENDENCY = "external_dependency"


@dataclass
class TaskConstraint:
    """Represents a constraint affecting task execution."""

    resource_type: ResourceType
    required_amount: float
    available_amount: float

    @property
    def satisfaction_ratio(self) -> float:
        """Calculate how well this constraint is satisfied (0.0 to 1.0+)."""
        if self.required_amount == 0:
            return 1.0
        return self.available_amount / self.required_amount


@dataclass
class BusinessImpactMetrics:
    """Metrics for measuring business impact of tasks."""

    user_satisfaction_improvement: float = 0.0  # Expected improvement (0-1 scale)
    cost_reduction_dollars: float = 0.0  # Expected cost savings
    performance_improvement_percent: float = 0.0  # Expected performance gain
    risk_mitigation_score: float = 0.0  # Risk reduction (0-1 scale)
    strategic_alignment_score: float = 0.0  # Alignment with strategic goals (0-1 scale)

    def calculate_total_impact(self) -> float:
        """Calculate weighted total business impact score."""
        weights = {
            "user_satisfaction": 0.25,
            "cost_reduction": 0.20,
            "performance": 0.20,
            "risk_mitigation": 0.20,
            "strategic_alignment": 0.15,
        }

        # Normalize cost reduction to 0-1 scale (assuming $1000 max impact)
        normalized_cost = min(1.0, self.cost_reduction_dollars / 1000.0)

        # Normalize performance improvement (assuming 100% max improvement)
        normalized_performance = min(1.0, self.performance_improvement_percent / 100.0)

        return (
            weights["user_satisfaction"] * self.user_satisfaction_improvement
            + weights["cost_reduction"] * normalized_cost
            + weights["performance"] * normalized_performance
            + weights["risk_mitigation"] * self.risk_mitigation_score
            + weights["strategic_alignment"] * self.strategic_alignment_score
        )


@dataclass
class AdaptiveTask:
    """Task with adaptive prioritization metadata."""

    id: str
    name: str
    description: str
    base_priority: TaskPriority
    estimated_hours: float
    dependencies: list[str] = field(default_factory=list)
    constraints: list[TaskConstraint] = field(default_factory=list)
    business_impact: BusinessImpactMetrics = field(default_factory=BusinessImpactMetrics)

    # Dynamic properties
    current_priority: TaskPriority | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority_score: float = 0.0  # Calculated dynamic priority score

    # Tracking
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    last_priority_update: float = field(default_factory=time.time)

    # Feedback tracking
    user_feedback_score: float = 0.0  # User feedback on task importance
    urgency_multiplier: float = 1.0  # Urgency based on external factors

    def __post_init__(self):
        if self.current_priority is None:
            self.current_priority = self.base_priority

    def age_in_hours(self) -> float:
        """Calculate how long this task has been pending."""
        return (time.time() - self.created_at) / 3600.0

    def is_blocked(self) -> bool:
        """Check if task is blocked by resource constraints."""
        return any(constraint.satisfaction_ratio < 1.0 for constraint in self.constraints)

    def get_blocking_constraints(self) -> list[TaskConstraint]:
        """Get list of constraints that are blocking this task."""
        return [c for c in self.constraints if c.satisfaction_ratio < 1.0]


@dataclass
class SystemMetrics:
    """Current system metrics that influence prioritization."""

    error_rate: float = 0.0
    response_latency_p95: float = 0.0
    cost_per_interaction: float = 0.0
    user_satisfaction: float = 0.0
    system_load: float = 0.0
    available_budget: float = 0.0
    developer_availability: float = 1.0  # 0.0 to 1.0


@dataclass
class PrioritizationContext:
    """Context information for prioritization decisions."""

    current_metrics: SystemMetrics
    emergency_mode: bool = False
    budget_constraints: bool = False
    resource_constraints: dict[ResourceType, float] = field(default_factory=dict)
    strategic_focus: str = "stability"  # "stability", "growth", "cost_optimization"
    user_feedback: dict[str, float] = field(default_factory=dict)  # task_id -> feedback_score


class AdaptivePrioritizer:
    """Dynamic task prioritization system with context awareness."""

    def __init__(self):
        self.tasks: dict[str, AdaptiveTask] = {}
        self.prioritization_history: list[dict[str, Any]] = []

        # Prioritization weights (can be tuned)
        self.weights = {
            "base_priority": 0.30,
            "business_impact": 0.25,
            "urgency": 0.20,
            "resource_availability": 0.15,
            "user_feedback": 0.10,
        }

        # Context-specific multipliers
        self.context_multipliers = {
            "emergency": {"P0_CRITICAL": 2.0, "P1_HIGH": 0.5, "P2_MEDIUM": 0.1, "P3_LOW": 0.1},
            "budget_constrained": {"cost_reduction": 2.0, "performance": 1.5},
            "growth_focus": {"user_satisfaction": 1.8, "performance": 1.5, "strategic_alignment": 1.3},
        }

    def add_task(self, task: AdaptiveTask):
        """Add a new task to the prioritization system."""
        self.tasks[task.id] = task
        logger.info(f"Added task {task.id}: {task.name} (priority: {task.base_priority.name})")

    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            old_status = task.status
            task.status = status

            if status == TaskStatus.IN_PROGRESS and not task.started_at:
                task.started_at = time.time()
            elif status == TaskStatus.COMPLETED and not task.completed_at:
                task.completed_at = time.time()

            logger.info(f"Task {task_id} status: {old_status.value} -> {status.value}")

    def update_constraints(self, task_id: str, constraints: list[TaskConstraint]):
        """Update resource constraints for a task."""
        if task_id in self.tasks:
            self.tasks[task_id].constraints = constraints
            logger.info(f"Updated constraints for task {task_id}")

    def update_user_feedback(self, task_id: str, feedback_score: float):
        """Update user feedback for a task (0.0 to 1.0 scale)."""
        if task_id in self.tasks:
            self.tasks[task_id].user_feedback_score = feedback_score
            logger.info(f"Updated user feedback for task {task_id}: {feedback_score}")

    def calculate_priority_score(self, task: AdaptiveTask, context: PrioritizationContext) -> float:
        """Calculate dynamic priority score for a task."""
        # Base priority score (higher number = lower priority, so invert). Highest
        # priority (P0) should yield largest base score. With enum values 0..3 we
        # invert relative to max (3) and normalise to 0..1.
        base_score = (3 - task.base_priority.value) / 3.0

        # Business impact score
        impact_score = task.business_impact.calculate_total_impact()

        # Urgency score based on age and external factors
        age_factor = min(1.0, task.age_in_hours() / 168.0)  # Normalize to weeks
        urgency_score = age_factor * 0.5 + task.urgency_multiplier * 0.5

        # Resource availability score
        if task.constraints:
            resource_score = min(c.satisfaction_ratio for c in task.constraints)
            resource_score = min(1.0, resource_score)  # Cap at 1.0
        else:
            resource_score = 1.0

        # User feedback score (already 0-1 scale)
        feedback_score = task.user_feedback_score

        # Calculate weighted score
        weighted_score = (
            self.weights["base_priority"] * base_score
            + self.weights["business_impact"] * impact_score
            + self.weights["urgency"] * urgency_score
            + self.weights["resource_availability"] * resource_score
            + self.weights["user_feedback"] * feedback_score
        )

        # Apply context-specific multipliers
        if context.emergency_mode:
            priority_multiplier = self.context_multipliers["emergency"].get(task.base_priority.name, 1.0)
            weighted_score *= priority_multiplier

        if context.budget_constraints and task.business_impact.cost_reduction_dollars > 0:
            weighted_score *= self.context_multipliers["budget_constrained"]["cost_reduction"]

        if context.strategic_focus == "growth" and task.business_impact.user_satisfaction_improvement > 0:
            weighted_score *= self.context_multipliers["growth_focus"]["user_satisfaction"]

        # System health adjustments
        if context.current_metrics.error_rate > ERROR_RATE_THRESHOLD and task.base_priority == TaskPriority.P0_CRITICAL:
            weighted_score *= 1.5

        if (
            context.current_metrics.response_latency_p95 > HIGH_LATENCY_THRESHOLD
            and "performance" in task.description.lower()
        ):
            weighted_score *= 1.3

        return min(1.0, weighted_score)  # Cap at 1.0

    def recompute_priorities(self, context: PrioritizationContext) -> dict[str, float]:
        """Recompute priorities for all tasks based on current context."""

        updated_tasks = {}

        for task_id, task in self.tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                continue

            # Calculate new priority score
            new_score = self.calculate_priority_score(task, context)
            old_score = task.priority_score

            task.priority_score = new_score
            task.last_priority_update = time.time()

            # Determine new priority level based on score
            if new_score >= CRITICAL_SCORE_THRESHOLD:
                new_priority = TaskPriority.P0_CRITICAL
            elif new_score >= HIGH_SCORE_THRESHOLD:
                new_priority = TaskPriority.P1_HIGH
            elif new_score >= MEDIUM_SCORE_THRESHOLD:
                new_priority = TaskPriority.P2_MEDIUM
            else:
                new_priority = TaskPriority.P3_LOW

            # Update priority if it changed significantly
            if task.current_priority != new_priority:
                prev_name = task.current_priority.name if task.current_priority else "UNSET"
                logger.info(
                    f"Priority change for {task_id}: "
                    f"{prev_name} -> {new_priority.name} "
                    f"(score: {old_score:.3f} -> {new_score:.3f})"
                )
                task.current_priority = new_priority

            updated_tasks[task_id] = new_score

        # Record prioritization history
        self.prioritization_history.append(
            {"timestamp": time.time(), "context": asdict(context), "task_scores": updated_tasks.copy()}
        )

        # Limit history size
        if len(self.prioritization_history) > HISTORY_MAX_SIZE:
            self.prioritization_history = self.prioritization_history[-HISTORY_TRIM_SIZE:]

        return updated_tasks

    def get_prioritized_tasks(
        self, context: PrioritizationContext, statuses: list[TaskStatus] | None = None, limit: int | None = None
    ) -> list[AdaptiveTask]:
        """Get tasks ordered by current priority."""

        # Recompute priorities first
        self.recompute_priorities(context)

        # Filter by status if specified
        if statuses is None:
            statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]

        eligible_tasks = [task for task in self.tasks.values() if task.status in statuses]

        # Sort by priority score (descending)
        prioritized_tasks = sorted(eligible_tasks, key=lambda t: (t.priority_score, -t.age_in_hours()), reverse=True)

        # Apply limit if specified
        if limit:
            prioritized_tasks = prioritized_tasks[:limit]

        return prioritized_tasks

    def get_next_actionable_tasks(self, context: PrioritizationContext, max_tasks: int = 5) -> list[AdaptiveTask]:
        """Get the next actionable tasks that aren't blocked by constraints."""

        prioritized_tasks = self.get_prioritized_tasks(context, [TaskStatus.PENDING])

        # Filter out blocked tasks
        actionable_tasks = [task for task in prioritized_tasks if not task.is_blocked()]

        return actionable_tasks[:max_tasks]

    def identify_resource_bottlenecks(self) -> dict[ResourceType, list[str]]:
        """Identify resource bottlenecks affecting task execution."""
        bottlenecks: dict[ResourceType, list[str]] = {}

        for task in self.tasks.values():
            if task.status == TaskStatus.BLOCKED:
                blocking_constraints = task.get_blocking_constraints()
                for constraint in blocking_constraints:
                    if constraint.resource_type not in bottlenecks:
                        bottlenecks[constraint.resource_type] = []
                    bottlenecks[constraint.resource_type].append(task.id)

        return bottlenecks

    def suggest_resource_reallocation(self, context: PrioritizationContext) -> dict[str, Any]:
        """Suggest resource reallocation to optimize task completion."""

        bottlenecks = self.identify_resource_bottlenecks()
        high_priority_blocked = [
            task
            for task in self.tasks.values()
            if task.status == TaskStatus.BLOCKED and task.current_priority and task.current_priority.value <= 1
        ]

        recommendations: list[str] = []

        # Generate recommendations
        if ResourceType.DEVELOPER_TIME in bottlenecks:
            recommendations.append("Consider adding developer resources or deprioritizing lower-value tasks")

        if ResourceType.API_BUDGET in bottlenecks:
            cost_reduction_tasks = [
                task
                for task in self.tasks.values()
                if task.business_impact.cost_reduction_dollars > 0 and task.status == TaskStatus.PENDING
            ]
            if cost_reduction_tasks:
                recommendations.append(f"Prioritize cost reduction tasks: {[t.id for t in cost_reduction_tasks[:3]]}")

        if context.current_metrics.error_rate > ERROR_RATE_THRESHOLD:
            stability_tasks = [
                task
                for task in self.tasks.values()
                if task.current_priority == TaskPriority.P0_CRITICAL and task.status == TaskStatus.PENDING
            ]
            if stability_tasks:
                recommendations.append(f"Focus on critical stability tasks: {[t.id for t in stability_tasks[:3]]}")

        return {
            "bottlenecks": bottlenecks,
            "high_priority_blocked_count": len(high_priority_blocked),
            "recommendations": recommendations,
        }

    def get_prioritization_report(self, context: PrioritizationContext) -> dict[str, Any]:
        """Generate comprehensive prioritization report."""

        prioritized_tasks = self.get_prioritized_tasks(context)
        actionable_tasks = self.get_next_actionable_tasks(context)
        resource_suggestions = self.suggest_resource_reallocation(context)

        # Calculate summary statistics
        priority_distribution = {}
        for priority in TaskPriority:
            count = sum(1 for t in self.tasks.values() if t.current_priority == priority)
            priority_distribution[priority.name] = count

        status_distribution = {}
        for status in TaskStatus:
            count = sum(1 for t in self.tasks.values() if t.status == status)
            status_distribution[status.name] = count

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_tasks": len(self.tasks),
            "priority_distribution": priority_distribution,
            "status_distribution": status_distribution,
            "top_priority_tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "priority": task.current_priority.name if task.current_priority else "UNSET",
                    "score": task.priority_score,
                    "status": task.status.value,
                    "age_hours": task.age_in_hours(),
                }
                for task in prioritized_tasks[:10]
            ],
            "next_actionable": [
                {
                    "id": task.id,
                    "name": task.name,
                    "priority": task.current_priority.name if task.current_priority else "UNSET",
                    "score": task.priority_score,
                }
                for task in actionable_tasks
            ],
            "resource_analysis": resource_suggestions,
            "context": {
                "emergency_mode": context.emergency_mode,
                "budget_constraints": context.budget_constraints,
                "strategic_focus": context.strategic_focus,
                "system_health": {
                    "error_rate": context.current_metrics.error_rate,
                    "latency_p95": context.current_metrics.response_latency_p95,
                    "user_satisfaction": context.current_metrics.user_satisfaction,
                },
            },
        }


def create_example_tasks() -> list[AdaptiveTask]:
    """Create example tasks for demonstration."""

    tasks = [
        AdaptiveTask(
            id="PERF-001",
            name="Optimize LLM response caching",
            description="Implement semantic caching to reduce API costs",
            base_priority=TaskPriority.P1_HIGH,
            estimated_hours=16.0,
            business_impact=BusinessImpactMetrics(
                cost_reduction_dollars=500.0, performance_improvement_percent=30.0, user_satisfaction_improvement=0.2
            ),
            constraints=[
                TaskConstraint(ResourceType.DEVELOPER_TIME, 16.0, 20.0),
                TaskConstraint(ResourceType.API_BUDGET, 100.0, 150.0),
            ],
        ),
        AdaptiveTask(
            id="SEC-002",
            name="Fix authentication vulnerability",
            description="Critical security fix for user authentication",
            base_priority=TaskPriority.P0_CRITICAL,
            estimated_hours=8.0,
            business_impact=BusinessImpactMetrics(risk_mitigation_score=0.9, strategic_alignment_score=0.8),
            constraints=[TaskConstraint(ResourceType.DEVELOPER_TIME, 8.0, 20.0)],
        ),
        AdaptiveTask(
            id="FEAT-003",
            name="Add multimodal content processing",
            description="Support image and video processing in Discord bot",
            base_priority=TaskPriority.P2_MEDIUM,
            estimated_hours=40.0,
            business_impact=BusinessImpactMetrics(
                user_satisfaction_improvement=0.4, strategic_alignment_score=0.7, performance_improvement_percent=15.0
            ),
            constraints=[
                TaskConstraint(ResourceType.DEVELOPER_TIME, 40.0, 20.0),  # Over capacity
                TaskConstraint(ResourceType.COMPUTE_RESOURCES, 1.0, 0.6),  # Limited compute
            ],
        ),
        AdaptiveTask(
            id="DOC-004",
            name="Update API documentation",
            description="Comprehensive API documentation update",
            base_priority=TaskPriority.P3_LOW,
            estimated_hours=12.0,
            business_impact=BusinessImpactMetrics(user_satisfaction_improvement=0.1, strategic_alignment_score=0.3),
            constraints=[TaskConstraint(ResourceType.DEVELOPER_TIME, 12.0, 20.0)],
        ),
    ]

    return tasks


async def main():
    """Demonstration of adaptive prioritization system."""

    # Initialize prioritizer
    prioritizer = AdaptivePrioritizer()

    # Add example tasks
    for task in create_example_tasks():
        prioritizer.add_task(task)

    # Simulate different contexts
    contexts = [
        PrioritizationContext(
            current_metrics=SystemMetrics(
                error_rate=0.02,
                response_latency_p95=1200.0,
                cost_per_interaction=0.015,
                user_satisfaction=0.85,
                system_load=0.6,
                available_budget=500.0,
                developer_availability=1.0,
            ),
            strategic_focus="stability",
        ),
        PrioritizationContext(
            current_metrics=SystemMetrics(
                error_rate=0.08,  # High error rate!
                response_latency_p95=3000.0,
                cost_per_interaction=0.025,
                user_satisfaction=0.65,
                system_load=0.9,
                available_budget=100.0,  # Low budget
                developer_availability=0.7,
            ),
            emergency_mode=True,
            budget_constraints=True,
            strategic_focus="stability",
        ),
    ]

    print("🔄 ADAPTIVE PRIORITIZATION DEMONSTRATION\n")

    for i, context in enumerate(contexts, 1):
        print(f"📊 SCENARIO {i}: {'Emergency Mode' if context.emergency_mode else 'Normal Operations'}")
        print("-" * 60)

        # Generate prioritization report
        report = prioritizer.get_prioritization_report(context)

        print("System Health:")
        health = report["context"]["system_health"]
        print(f"  • Error Rate: {health['error_rate']:.1%}")
        print(f"  • Latency P95: {health['latency_p95']:.0f}ms")
        print(f"  • User Satisfaction: {health['user_satisfaction']:.1%}")

        print("\nTop Priority Tasks:")
        for task in report["top_priority_tasks"][:5]:
            print(f"  • {task['priority']}: {task['name']} (score: {task['score']:.3f})")

        print("\nNext Actionable Tasks:")
        for task in report["next_actionable"]:
            print(f"  • {task['name']} (priority: {task['priority']})")

        if report["resource_analysis"]["recommendations"]:
            print("\nRecommendations:")
            for rec in report["resource_analysis"]["recommendations"]:
                print(f"  • {rec}")

        print("\n" + "=" * 60 + "\n")

        # Update some task feedback for next iteration
        prioritizer.update_user_feedback("PERF-001", 0.8)
        prioritizer.update_task_status("SEC-002", TaskStatus.IN_PROGRESS)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
