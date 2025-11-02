"""Multi-agent collaboration framework for dynamic agent coordination.

This module provides patterns for agent collaboration including sequential,
parallel, and hierarchical execution patterns.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


logger = logging.getLogger(__name__)


class CollaborationPattern(Enum):
    """Available collaboration patterns for agent coordination."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent."""

    agent_id: str
    task_name: str
    inputs: dict[str, Any]
    dependencies: list[str] = None
    timeout: float | None = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class CollaborationResult:
    """Result of a collaboration execution."""

    pattern: CollaborationPattern
    results: dict[str, StepResult]
    execution_time: float
    success_count: int
    failure_count: int
    metadata: dict[str, Any] = None


class AgentCollaboration:
    """Framework for coordinating multiple agents in various collaboration patterns."""

    def __init__(self, feature_flags: FeatureFlags):
        """Initialize agent collaboration framework.

        Args:
            feature_flags: Feature flags configuration
        """
        self.feature_flags = feature_flags
        self.active_collaborations: dict[str, CollaborationResult] = {}

    def is_enabled(self) -> bool:
        """Check if agent collaboration is enabled."""
        return self.feature_flags.ENABLE_AGENT_COLLABORATION

    async def execute_sequential(
        self, tasks: list[AgentTask], collaboration_id: str | None = None
    ) -> CollaborationResult:
        """Execute tasks sequentially, passing results between agents.

        Args:
            tasks: List of agent tasks to execute
            collaboration_id: Optional ID for tracking this collaboration

        Returns:
            CollaborationResult: Results of the sequential execution
        """
        if not self.is_enabled():
            return CollaborationResult(
                pattern=CollaborationPattern.SEQUENTIAL,
                results={},
                execution_time=0.0,
                success_count=0,
                failure_count=len(tasks),
                metadata={"error": "Agent collaboration disabled"},
            )

        start_time = asyncio.get_event_loop().time()
        results = {}
        context = {}

        for task in tasks:
            try:
                # Add context from previous tasks
                task.inputs.update(context)

                # Execute task (simulated - would integrate with actual agent execution)
                result = await self._execute_agent_task(task)
                results[task.agent_id] = result

                # Update context for next task
                if result.success and result.data:
                    context.update(result.data)

            except Exception as e:
                logger.error(f"Sequential task failed for agent {task.agent_id}: {e}")
                results[task.agent_id] = StepResult.fail(f"Task execution failed: {e}")

        execution_time = asyncio.get_event_loop().time() - start_time
        success_count = sum(1 for r in results.values() if r.success)
        failure_count = len(results) - success_count

        result = CollaborationResult(
            pattern=CollaborationPattern.SEQUENTIAL,
            results=results,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count,
            metadata={"collaboration_id": collaboration_id},
        )

        if collaboration_id:
            self.active_collaborations[collaboration_id] = result

        return result

    async def execute_parallel(
        self, tasks: list[AgentTask], collaboration_id: str | None = None
    ) -> CollaborationResult:
        """Execute tasks in parallel with synchronization.

        Args:
            tasks: List of agent tasks to execute
            collaboration_id: Optional ID for tracking this collaboration

        Returns:
            CollaborationResult: Results of the parallel execution
        """
        if not self.is_enabled():
            return CollaborationResult(
                pattern=CollaborationPattern.PARALLEL,
                results={},
                execution_time=0.0,
                success_count=0,
                failure_count=len(tasks),
                metadata={"error": "Agent collaboration disabled"},
            )

        start_time = asyncio.get_event_loop().time()

        # Execute all tasks concurrently
        task_coroutines = [self._execute_agent_task(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Process results
        results = {}
        for task, result in zip(tasks, task_results, strict=False):
            if isinstance(result, Exception):
                results[task.agent_id] = StepResult.fail(f"Parallel execution failed: {result}")
            else:
                results[task.agent_id] = result

        execution_time = asyncio.get_event_loop().time() - start_time
        success_count = sum(1 for r in results.values() if r.success)
        failure_count = len(results) - success_count

        result = CollaborationResult(
            pattern=CollaborationPattern.PARALLEL,
            results=results,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count,
            metadata={"collaboration_id": collaboration_id},
        )

        if collaboration_id:
            self.active_collaborations[collaboration_id] = result

        return result

    async def execute_hierarchical(
        self, coordinator_task: AgentTask, subordinate_tasks: list[AgentTask], collaboration_id: str | None = None
    ) -> CollaborationResult:
        """Execute hierarchical pattern with coordinator and subordinates.

        Args:
            coordinator_task: Task for the coordinating agent
            subordinate_tasks: Tasks for subordinate agents
            collaboration_id: Optional ID for tracking this collaboration

        Returns:
            CollaborationResult: Results of the hierarchical execution
        """
        if not self.is_enabled():
            return CollaborationResult(
                pattern=CollaborationPattern.HIERARCHICAL,
                results={},
                execution_time=0.0,
                success_count=0,
                failure_count=len(subordinate_tasks) + 1,
                metadata={"error": "Agent collaboration disabled"},
            )

        start_time = asyncio.get_event_loop().time()
        results = {}

        # Execute coordinator first
        try:
            coordinator_result = await self._execute_agent_task(coordinator_task)
            results[coordinator_task.agent_id] = coordinator_result

            if coordinator_result.success:
                # Update subordinate tasks with coordinator context
                coordinator_context = coordinator_result.data or {}
                for task in subordinate_tasks:
                    task.inputs.update(coordinator_context)

                # Execute subordinates in parallel
                subordinate_coroutines = [self._execute_agent_task(task) for task in subordinate_tasks]
                subordinate_results = await asyncio.gather(*subordinate_coroutines, return_exceptions=True)

                for task, result in zip(subordinate_tasks, subordinate_results, strict=False):
                    if isinstance(result, Exception):
                        results[task.agent_id] = StepResult.fail(f"Subordinate execution failed: {result}")
                    else:
                        results[task.agent_id] = result
            else:
                # If coordinator fails, mark all subordinates as failed
                for task in subordinate_tasks:
                    results[task.agent_id] = StepResult.fail("Coordinator failed, skipping subordinate")

        except Exception as e:
            logger.error(f"Hierarchical execution failed: {e}")
            results[coordinator_task.agent_id] = StepResult.fail(f"Hierarchical execution failed: {e}")
            for task in subordinate_tasks:
                results[task.agent_id] = StepResult.fail("Execution failed")

        execution_time = asyncio.get_event_loop().time() - start_time
        success_count = sum(1 for r in results.values() if r.success)
        failure_count = len(results) - success_count

        result = CollaborationResult(
            pattern=CollaborationPattern.HIERARCHICAL,
            results=results,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count,
            metadata={"collaboration_id": collaboration_id},
        )

        if collaboration_id:
            self.active_collaborations[collaboration_id] = result

        return result

    async def execute_pipeline(
        self, pipeline_stages: list[list[AgentTask]], collaboration_id: str | None = None
    ) -> CollaborationResult:
        """Execute tasks in pipeline stages with data flow between stages.

        Args:
            pipeline_stages: List of stages, each containing tasks for that stage
            collaboration_id: Optional ID for tracking this collaboration

        Returns:
            CollaborationResult: Results of the pipeline execution
        """
        if not self.is_enabled():
            return CollaborationResult(
                pattern=CollaborationPattern.PIPELINE,
                results={},
                execution_time=0.0,
                success_count=0,
                failure_count=sum(len(stage) for stage in pipeline_stages),
                metadata={"error": "Agent collaboration disabled"},
            )

        start_time = asyncio.get_event_loop().time()
        results = {}
        pipeline_context = {}

        for stage_idx, stage_tasks in enumerate(pipeline_stages):
            logger.info(f"Executing pipeline stage {stage_idx + 1}/{len(pipeline_stages)}")

            # Update tasks with pipeline context
            for task in stage_tasks:
                task.inputs.update(pipeline_context)

            # Execute stage tasks in parallel
            stage_coroutines = [self._execute_agent_task(task) for task in stage_tasks]
            stage_results = await asyncio.gather(*stage_coroutines, return_exceptions=True)

            # Process stage results
            for task, result in zip(stage_tasks, stage_results, strict=False):
                if isinstance(result, Exception):
                    results[task.agent_id] = StepResult.fail(f"Pipeline stage failed: {result}")
                else:
                    results[task.agent_id] = result

                    # Update pipeline context with successful results
                    if result.success and result.data:
                        pipeline_context.update(result.data)

        execution_time = asyncio.get_event_loop().time() - start_time
        success_count = sum(1 for r in results.values() if r.success)
        failure_count = len(results) - success_count

        result = CollaborationResult(
            pattern=CollaborationPattern.PIPELINE,
            results=results,
            execution_time=execution_time,
            success_count=success_count,
            failure_count=failure_count,
            metadata={"collaboration_id": collaboration_id, "stages": len(pipeline_stages)},
        )

        if collaboration_id:
            self.active_collaborations[collaboration_id] = result

        return result

    async def _execute_agent_task(self, task: AgentTask) -> StepResult:
        """Execute a single agent task.

        Args:
            task: The agent task to execute

        Returns:
            StepResult: Result of the task execution
        """
        try:
            # Simulate task execution with timeout
            if task.timeout:
                result = await asyncio.wait_for(self._simulate_agent_execution(task), timeout=task.timeout)
            else:
                result = await self._simulate_agent_execution(task)

            return result

        except asyncio.TimeoutError:
            return StepResult.fail(f"Task timeout for agent {task.agent_id}")
        except Exception as e:
            return StepResult.fail(f"Task execution error: {e}")

    async def _simulate_agent_execution(self, task: AgentTask) -> StepResult:
        """Simulate agent task execution.

        In a real implementation, this would integrate with the actual
        agent execution system.

        Args:
            task: The task to simulate

        Returns:
            StepResult: Simulated execution result
        """
        # Simulate processing time
        await asyncio.sleep(0.1)

        # Simulate success/failure based on task complexity
        success_probability = 0.9 if task.retry_count == 0 else 0.7

        if hash(task.task_name) % 100 < success_probability * 100:
            return StepResult.ok(
                data={
                    "agent_id": task.agent_id,
                    "task": task.task_name,
                    "result": f"Processed {task.task_name}",
                    "inputs": task.inputs,
                }
            )
        else:
            return StepResult.fail(f"Simulated failure for {task.task_name}")

    def get_collaboration_status(self, collaboration_id: str) -> CollaborationResult | None:
        """Get the status of a specific collaboration.

        Args:
            collaboration_id: ID of the collaboration to check

        Returns:
            Optional[CollaborationResult]: Collaboration result if found
        """
        return self.active_collaborations.get(collaboration_id)

    def get_all_collaborations(self) -> dict[str, CollaborationResult]:
        """Get all active collaborations.

        Returns:
            Dict[str, CollaborationResult]: All active collaborations
        """
        return self.active_collaborations.copy()

    def clear_collaboration(self, collaboration_id: str) -> bool:
        """Clear a specific collaboration from memory.

        Args:
            collaboration_id: ID of the collaboration to clear

        Returns:
            bool: True if collaboration was found and cleared
        """
        if collaboration_id in self.active_collaborations:
            del self.active_collaborations[collaboration_id]
            return True
        return False
