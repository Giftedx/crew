"""Core interfaces for unified crew system.

This module defines the protocols and data classes that form the foundation
of the crew execution system. All implementations must conform to these interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.step_result import StepResult


class CrewExecutionMode(Enum):
    """Execution modes for crew tasks."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


class CrewPriority(Enum):
    """Priority levels for crew tasks."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class CrewConfig:
    """Configuration for crew execution.

    This dataclass encapsulates all configuration needed for crew execution,
    including tenant context, performance budgets, and feature flags.
    """

    tenant_id: str
    "Tenant identifier for multi-tenant isolation."
    enable_cache: bool = True
    "Whether to enable caching for this execution."
    enable_telemetry: bool = True
    "Whether to emit telemetry and metrics."
    timeout_seconds: int = 300
    "Maximum execution time in seconds."
    max_retries: int = 3
    "Maximum number of retry attempts on failure."
    quality_threshold: float = 0.7
    "Minimum quality score threshold (0.0-1.0)."
    execution_mode: CrewExecutionMode = CrewExecutionMode.SEQUENTIAL
    "Execution mode for agent coordination."
    enable_early_exit: bool = True
    "Whether to enable early exit optimizations."
    enable_fallback: bool = True
    "Whether to enable fallback strategies on failure."
    metadata: dict[str, Any] = field(default_factory=dict)
    "Additional metadata for the execution."


@dataclass
class CrewTask:
    """A task to be executed by the crew.

    This dataclass represents a single unit of work that will be
    processed by the crew execution system.
    """

    task_id: str
    "Unique identifier for this task."
    task_type: str
    "Type/category of the task (e.g., 'content_analysis', 'research')."
    description: str
    "Human-readable description of what the task should accomplish."
    inputs: dict[str, Any]
    "Input data and parameters for the task."
    agent_requirements: list[str] = field(default_factory=list)
    "List of required agent roles/types."
    tool_requirements: list[str] = field(default_factory=list)
    "List of required tool names."
    priority: CrewPriority = CrewPriority.NORMAL
    "Priority level for execution ordering."
    expected_output_schema: dict[str, Any] | None = None
    "Optional schema for expected output validation."
    context: dict[str, Any] = field(default_factory=dict)
    "Additional context and metadata."

    def __post_init__(self) -> None:
        """Validate task after initialization."""
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if not self.task_type:
            raise ValueError("task_type cannot be empty")
        if not self.description:
            raise ValueError("description cannot be empty")


@dataclass
class CrewExecutionResult:
    """Result of a crew execution.

    This wraps StepResult with additional crew-specific metadata.
    """

    step_result: StepResult
    "The underlying StepResult from execution."
    task_id: str
    "ID of the task that was executed."
    execution_time_seconds: float
    "Total execution time in seconds."
    agents_used: list[str] = field(default_factory=list)
    "List of agents that participated in execution."
    tools_used: list[str] = field(default_factory=list)
    "List of tools that were invoked."
    cache_hits: int = 0
    "Number of cache hits during execution."
    retry_count: int = 0
    "Number of retries that were attempted."
    metadata: dict[str, Any] = field(default_factory=dict)
    "Additional execution metadata."


class CrewExecutor(ABC):
    """Abstract base for crew executors.

    This protocol defines the interface that all crew executors must implement.
    Implementations should handle the orchestration of agents and tools to
    complete tasks while maintaining observability and reliability.
    """

    @abstractmethod
    async def execute(self, task: CrewTask, config: CrewConfig) -> CrewExecutionResult:
        """Execute a crew task.

        Args:
            task: The task to execute
            config: Configuration for execution

        Returns:
            CrewExecutionResult containing the outcome and metadata
        """
        ...

    @abstractmethod
    async def validate_task(self, task: CrewTask) -> StepResult:
        """Validate task before execution.

        Args:
            task: The task to validate

        Returns:
            StepResult indicating whether the task is valid
        """
        ...

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources after execution.

        This should be called after execution completes, whether successful or not.
        """
        ...


class CrewFactory(ABC):
    """Abstract factory for creating crews.

    This factory pattern allows for different crew executor implementations
    to be created based on task requirements or configuration.
    """

    @abstractmethod
    def create_executor(self, executor_type: str, config: CrewConfig) -> CrewExecutor:
        """Create a crew executor.

        Args:
            executor_type: Type of executor to create (e.g., 'unified', 'legacy')
            config: Configuration for the executor

        Returns:
            A CrewExecutor instance

        Raises:
            ValueError: If executor_type is not supported
        """
        ...

    @abstractmethod
    def get_available_executors(self) -> list[str]:
        """Get list of available executor types.

        Returns:
            List of supported executor type names
        """
        ...
