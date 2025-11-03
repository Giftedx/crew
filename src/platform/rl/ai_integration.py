"""
Advanced AI integration module for the Ultimate Discord Intelligence Bot.

Combines DSPy optimization framework with advanced agent planning patterns
to provide sophisticated AI capabilities with automated optimization and coordination.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .agent_planner import AgentPlanner, PlanningContext, PlanningStrategy
from .dspy_optimizer import (
    DSPyOptimizer,
    OptimizationConfig,
    PromptTemplate,
    PromptType,
)


logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """AI integration modes."""

    OPTIMIZATION_FIRST = "optimization_first"  # Optimize prompts before planning
    PLANNING_FIRST = "planning_first"  # Plan tasks before optimizing
    PARALLEL = "parallel"  # Run optimization and planning in parallel
    ADAPTIVE = "adaptive"  # Adapt based on context


class AICapability(Enum):
    """AI capability types."""

    PROMPT_OPTIMIZATION = "prompt_optimization"
    TASK_PLANNING = "task_planning"
    AGENT_COORDINATION = "agent_coordination"
    PERFORMANCE_MONITORING = "performance_monitoring"
    ADAPTIVE_LEARNING = "adaptive_learning"
    RESOURCE_MANAGEMENT = "resource_management"


@dataclass
class AIWorkflow:
    """AI workflow definition."""

    workflow_id: str
    name: str
    description: str
    required_capabilities: set[AICapability]
    optimization_config: OptimizationConfig
    planning_strategy: PlanningStrategy
    integration_mode: IntegrationMode
    expected_duration: float
    quality_threshold: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complex(self) -> bool:
        """Check if workflow is complex."""
        return len(self.required_capabilities) > 3 or self.expected_duration > 3600

    @property
    def requires_optimization(self) -> bool:
        """Check if workflow requires optimization."""
        return AICapability.PROMPT_OPTIMIZATION in self.required_capabilities

    @property
    def requires_planning(self) -> bool:
        """Check if workflow requires planning."""
        return AICapability.TASK_PLANNING in self.required_capabilities


@dataclass
class WorkflowResult:
    """Result of AI workflow execution."""

    workflow_id: str
    success: bool
    execution_time: float
    optimization_results: dict[str, Any] | None = None
    planning_results: dict[str, Any] | None = None
    performance_metrics: dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_quality(self) -> bool:
        """Check if result is high quality."""
        return self.quality_score >= 0.8

    @property
    def is_efficient(self) -> bool:
        """Check if execution was efficient."""
        return self.execution_time < 300  # Less than 5 minutes


@dataclass
class AIResource:
    """AI resource definition."""

    resource_id: str
    resource_type: str
    capacity: float
    current_usage: float = 0.0
    performance_score: float = 1.0
    availability: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available_capacity(self) -> float:
        """Get available capacity."""
        return max(0.0, self.capacity - self.current_usage)

    @property
    def utilization_rate(self) -> float:
        """Get utilization rate."""
        if self.capacity == 0:
            return 0.0
        return self.current_usage / self.capacity


class AIIntegration:
    """
    Advanced AI integration system combining DSPy optimization and agent planning.

    Provides sophisticated AI capabilities with automated optimization,
    intelligent task planning, and adaptive coordination.
    """

    def __init__(self, integration_mode: IntegrationMode = IntegrationMode.ADAPTIVE):
        """Initialize AI integration system."""
        self.integration_mode = integration_mode
        self.dspy_optimizer: DSPyOptimizer | None = None
        self.agent_planner: AgentPlanner | None = None
        self.workflows: dict[str, AIWorkflow] = {}
        self.workflow_history: list[WorkflowResult] = []
        self.ai_resources: dict[str, AIResource] = {}

        # Performance tracking
        self.performance_metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "average_execution_time": 0.0,
            "average_quality_score": 0.0,
            "optimization_success_rate": 0.0,
            "planning_success_rate": 0.0,
        }

        # Integration state
        self.is_initialized = False
        self.current_workflows: set[str] = set()

        logger.info(f"AI integration system initialized with mode: {integration_mode.value}")

    async def initialize(
        self,
        optimization_config: OptimizationConfig | None = None,
        planning_strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE,
    ) -> bool:
        """Initialize the AI integration system."""
        try:
            # Initialize DSPy optimizer
            opt_config = optimization_config or OptimizationConfig()
            self.dspy_optimizer = DSPyOptimizer(opt_config)

            # Initialize agent planner
            self.agent_planner = AgentPlanner(planning_strategy)

            # Initialize AI resources
            await self._initialize_resources()

            self.is_initialized = True
            logger.info("AI integration system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"AI integration initialization failed: {e}")
            return False

    async def _initialize_resources(self) -> None:
        """Initialize AI resources."""
        try:
            # CPU resource
            cpu_resource = AIResource(
                resource_id="cpu",
                resource_type="computational",
                capacity=100.0,
                performance_score=1.0,
            )
            self.ai_resources["cpu"] = cpu_resource

            # Memory resource
            memory_resource = AIResource(
                resource_id="memory",
                resource_type="storage",
                capacity=1000.0,  # GB
                performance_score=1.0,
            )
            self.ai_resources["memory"] = memory_resource

            # GPU resource (if available)
            gpu_resource = AIResource(
                resource_id="gpu",
                resource_type="computational",
                capacity=50.0,
                performance_score=1.0,
            )
            self.ai_resources["gpu"] = gpu_resource

            logger.info("AI resources initialized")

        except Exception as e:
            logger.error(f"Resource initialization failed: {e}")

    async def register_workflow(self, workflow: AIWorkflow) -> bool:
        """Register an AI workflow."""
        try:
            if not self.is_initialized:
                logger.error("AI integration system not initialized")
                return False

            if workflow.workflow_id in self.workflows:
                logger.warning(f"Workflow {workflow.workflow_id} already registered")
                return False

            self.workflows[workflow.workflow_id] = workflow
            logger.info(f"Registered workflow: {workflow.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.workflow_id}: {e}")
            return False

    async def execute_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any] | None = None,
    ) -> WorkflowResult | None:
        """Execute an AI workflow."""
        start_time = time.time()

        try:
            if not self.is_initialized:
                logger.error("AI integration system not initialized")
                return None

            if workflow_id not in self.workflows:
                logger.error(f"Workflow {workflow_id} not found")
                return None

            if workflow_id in self.current_workflows:
                logger.warning(f"Workflow {workflow_id} already running")
                return None

            workflow = self.workflows[workflow_id]
            self.current_workflows.add(workflow_id)

            logger.info(f"Starting workflow execution: {workflow.name}")

            # Execute workflow based on integration mode
            result = await self._execute_workflow_by_mode(workflow, context or {})

            execution_time = time.time() - start_time
            result.execution_time = execution_time

            # Update tracking
            self.workflow_history.append(result)
            self._update_performance_metrics(result)

            self.current_workflows.discard(workflow_id)

            logger.info(f"Workflow completed: {workflow.name}, success={result.success}, time={execution_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.current_workflows.discard(workflow_id)
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                execution_time=time.time() - start_time,
                error_message=str(e),
            )

    async def _execute_workflow_by_mode(self, workflow: AIWorkflow, context: dict[str, Any]) -> WorkflowResult:
        """Execute workflow based on integration mode."""
        try:
            if workflow.integration_mode == IntegrationMode.OPTIMIZATION_FIRST:
                return await self._execute_optimization_first(workflow, context)
            elif workflow.integration_mode == IntegrationMode.PLANNING_FIRST:
                return await self._execute_planning_first(workflow, context)
            elif workflow.integration_mode == IntegrationMode.PARALLEL:
                return await self._execute_parallel(workflow, context)
            else:  # ADAPTIVE
                return await self._execute_adaptive(workflow, context)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                execution_time=0.0,
                error_message=str(e),
            )

    async def _execute_optimization_first(self, workflow: AIWorkflow, context: dict[str, Any]) -> WorkflowResult:
        """Execute workflow with optimization first."""
        optimization_results = None
        planning_results = None
        success = True
        quality_score = 0.0

        try:
            # Step 1: Optimization
            if workflow.requires_optimization and self.dspy_optimizer:
                optimization_results = await self._run_optimization_phase(workflow, context)
                if optimization_results:
                    quality_score += 0.5
                else:
                    success = False

            # Step 2: Planning
            if workflow.requires_planning and self.agent_planner and success:
                planning_results = await self._run_planning_phase(workflow, context)
                if planning_results:
                    quality_score += 0.5
                else:
                    success = False

            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=success,
                execution_time=0.0,  # Will be set by caller
                optimization_results=optimization_results,
                planning_results=planning_results,
                quality_score=quality_score,
            )

        except Exception as e:
            logger.error(f"Optimization-first execution failed: {e}")
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                execution_time=0.0,
                error_message=str(e),
            )

    async def _execute_planning_first(self, workflow: AIWorkflow, context: dict[str, Any]) -> WorkflowResult:
        """Execute workflow with planning first."""
        optimization_results = None
        planning_results = None
        success = True
        quality_score = 0.0

        try:
            # Step 1: Planning
            if workflow.requires_planning and self.agent_planner:
                planning_results = await self._run_planning_phase(workflow, context)
                if planning_results:
                    quality_score += 0.5
                else:
                    success = False

            # Step 2: Optimization
            if workflow.requires_optimization and self.dspy_optimizer and success:
                optimization_results = await self._run_optimization_phase(workflow, context)
                if optimization_results:
                    quality_score += 0.5
                else:
                    success = False

            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=success,
                execution_time=0.0,
                optimization_results=optimization_results,
                planning_results=planning_results,
                quality_score=quality_score,
            )

        except Exception as e:
            logger.error(f"Planning-first execution failed: {e}")
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                execution_time=0.0,
                error_message=str(e),
            )

    async def _execute_parallel(self, workflow: AIWorkflow, context: dict[str, Any]) -> WorkflowResult:
        """Execute workflow with parallel optimization and planning."""
        try:
            # Run optimization and planning in parallel
            tasks = []

            if workflow.requires_optimization and self.dspy_optimizer:
                tasks.append(self._run_optimization_phase(workflow, context))

            if workflow.requires_planning and self.agent_planner:
                tasks.append(self._run_planning_phase(workflow, context))

            if not tasks:
                return WorkflowResult(
                    workflow_id=workflow.workflow_id,
                    success=True,
                    execution_time=0.0,
                    quality_score=1.0,
                )

            # Execute tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            optimization_results = None
            planning_results = None
            quality_score = 0.0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Parallel task {i} failed: {result}")
                    continue

                if i == 0 and workflow.requires_optimization:
                    optimization_results = result
                    if result:
                        quality_score += 0.5
                elif i == 1 and workflow.requires_planning:
                    planning_results = result
                    if result:
                        quality_score += 0.5

            success = quality_score > 0

            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=success,
                execution_time=0.0,
                optimization_results=optimization_results,
                planning_results=planning_results,
                quality_score=quality_score,
            )

        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                execution_time=0.0,
                error_message=str(e),
            )

    async def _execute_adaptive(self, workflow: AIWorkflow, context: dict[str, Any]) -> WorkflowResult:
        """Execute workflow with adaptive strategy."""
        try:
            # Analyze context and workflow complexity
            system_load = self._calculate_system_load()
            workflow_complexity = workflow.is_complex

            # Choose execution strategy based on context
            if system_load > 0.8 or workflow_complexity:
                # High load or complex workflow - use optimization first
                return await self._execute_optimization_first(workflow, context)
            elif system_load < 0.3 and not workflow_complexity:
                # Low load and simple workflow - use parallel
                return await self._execute_parallel(workflow, context)
            else:
                # Default to planning first
                return await self._execute_planning_first(workflow, context)

        except Exception as e:
            logger.error(f"Adaptive execution failed: {e}")
            return WorkflowResult(
                workflow_id=workflow.workflow_id,
                success=False,
                execution_time=0.0,
                error_message=str(e),
            )

    async def _run_optimization_phase(self, workflow: AIWorkflow, context: dict[str, Any]) -> dict[str, Any] | None:
        """Run optimization phase."""
        try:
            if not self.dspy_optimizer:
                return None

            # Create sample prompt template for optimization
            template = PromptTemplate(
                template_id=f"workflow_{workflow.workflow_id}",
                prompt_type=PromptType.ANALYSIS,
                base_template="Analyze the following content: {content}",
                variables=["content"],
            )

            # Register template
            await self.dspy_optimizer.register_template(template)

            # Create sample evaluation dataset
            from .dspy_optimizer import EvaluationDataset, OptimizationMetric

            dataset = EvaluationDataset(
                dataset_id=f"dataset_{workflow.workflow_id}",
                examples=[{"content": "Sample content"}],
                ground_truth=["Sample analysis"],
                evaluation_metrics=[OptimizationMetric.ACCURACY],
            )

            await self.dspy_optimizer.register_evaluation_dataset(dataset)

            # Run optimization
            result = await self.dspy_optimizer.optimize_template(
                template.template_id,
                dataset.dataset_id,
                workflow.optimization_config,
            )

            if result and result.is_successful:
                return {
                    "optimized_template": result.optimized_template,
                    "performance_metrics": result.performance_metrics,
                    "optimization_time": result.optimization_time,
                }

            return None

        except Exception as e:
            logger.error(f"Optimization phase failed: {e}")
            return None

    async def _run_planning_phase(self, workflow: AIWorkflow, context: dict[str, Any]) -> dict[str, Any] | None:
        """Run planning phase."""
        try:
            if not self.agent_planner:
                return None

            # Create sample tasks for planning
            from .agent_planner import AgentCapability, Task, TaskPriority

            tasks = [
                Task(
                    task_id=f"task_{i}",
                    task_type="analysis",
                    description=f"Task {i} for workflow {workflow.workflow_id}",
                    priority=TaskPriority.NORMAL,
                    required_capabilities={AgentCapability.CONTENT_ANALYSIS},
                    estimated_duration=60.0,
                )
                for i in range(3)
            ]

            # Create planning context
            planning_context = PlanningContext(
                available_agents=list(self.agent_planner.agents.values()),
                system_load=0.5,
            )

            # Create execution plan
            plan = await self.agent_planner.create_execution_plan(
                tasks, planning_context, f"plan_{workflow.workflow_id}"
            )

            if plan and plan.is_valid:
                return {
                    "plan_id": plan.plan_id,
                    "tasks_count": len(plan.tasks),
                    "estimated_completion_time": plan.estimated_completion_time,
                    "coordination_pattern": plan.coordination_pattern.value,
                }

            return None

        except Exception as e:
            logger.error(f"Planning phase failed: {e}")
            return None

    def _calculate_system_load(self) -> float:
        """Calculate current system load."""
        try:
            if not self.ai_resources:
                return 0.0

            total_utilization = sum(resource.utilization_rate for resource in self.ai_resources.values())
            return total_utilization / len(self.ai_resources)

        except Exception as e:
            logger.error(f"System load calculation failed: {e}")
            return 0.0

    def _update_performance_metrics(self, result: WorkflowResult) -> None:
        """Update performance metrics."""
        try:
            self.performance_metrics["total_workflows"] += 1

            if result.success:
                self.performance_metrics["successful_workflows"] += 1

            # Update averages
            total = self.performance_metrics["total_workflows"]
            successful = self.performance_metrics["successful_workflows"]

            # Average execution time
            current_avg_time = self.performance_metrics["average_execution_time"]
            new_avg_time = (current_avg_time * (total - 1) + result.execution_time) / total
            self.performance_metrics["average_execution_time"] = new_avg_time

            # Average quality score
            if result.success:
                current_avg_quality = self.performance_metrics["average_quality_score"]
                new_avg_quality = (current_avg_quality * (successful - 1) + result.quality_score) / successful
                self.performance_metrics["average_quality_score"] = new_avg_quality

            # Success rates
            self.performance_metrics["optimization_success_rate"] = (
                sum(1 for r in self.workflow_history if r.optimization_results) / total
            )
            self.performance_metrics["planning_success_rate"] = (
                sum(1 for r in self.workflow_history if r.planning_results) / total
            )

        except Exception as e:
            logger.error(f"Performance metrics update failed: {e}")

    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get performance metrics."""
        return self.performance_metrics.copy()

    async def get_workflow_history(self, limit: int | None = None) -> list[WorkflowResult]:
        """Get workflow execution history."""
        history = self.workflow_history.copy()
        if limit:
            history = history[-limit:]
        return history

    async def clear_cache(self) -> None:
        """Clear all caches."""
        try:
            if self.dspy_optimizer:
                await self.dspy_optimizer.clear_cache()

            if self.agent_planner:
                await self.agent_planner.clear_cache()

            logger.info("AI integration cache cleared")

        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")

    async def __aenter__(self) -> "AIIntegration":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.clear_cache()
