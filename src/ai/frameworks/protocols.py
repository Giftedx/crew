"""Universal framework adapter protocol for multi-framework AI agent support.

This module defines the FrameworkAdapter protocol that all framework implementations
must conform to. It provides a unified interface for executing agent workflows across
different frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex).

Design Principles:
- **Framework Agnostic**: Interface independent of underlying framework
- **StepResult Contract**: All methods return StepResult for consistent error handling
- **Progressive Feature Support**: Frameworks can declare what features they support
- **State Management**: Support for persisting and restoring workflow state
- **Tool Interoperability**: Universal tool system works across frameworks
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewTask
from ultimate_discord_intelligence_bot.step_result import StepResult


class FrameworkFeature(Enum):
    """Features that frameworks may support.

    Not all frameworks support all features. Frameworks declare their capabilities
    via the supports_feature() method.
    """

    # Core execution features
    SEQUENTIAL_EXECUTION = "sequential_execution"
    PARALLEL_EXECUTION = "parallel_execution"
    HIERARCHICAL_EXECUTION = "hierarchical_execution"

    # State management features
    STATE_PERSISTENCE = "state_persistence"
    STATE_CHECKPOINTING = "state_checkpointing"
    STATE_BRANCHING = "state_branching"

    # Agent features
    DYNAMIC_AGENT_CREATION = "dynamic_agent_creation"
    AGENT_MEMORY = "agent_memory"
    MULTI_AGENT_COLLABORATION = "multi_agent_collaboration"

    # Tool features
    CUSTOM_TOOLS = "custom_tools"
    TOOL_CHAINING = "tool_chaining"
    TOOL_RETRY = "tool_retry"

    # Advanced features
    STREAMING = "streaming"
    ASYNC_EXECUTION = "async_execution"
    DISTRIBUTED_EXECUTION = "distributed_execution"
    HUMAN_IN_LOOP = "human_in_loop"

    # Observability features
    TELEMETRY = "telemetry"
    DEBUGGING = "debugging"
    PERFORMANCE_PROFILING = "performance_profiling"


@dataclass
class AgentRole:
    """Definition of an agent's role and capabilities."""

    role_name: str
    """Name/identifier of the role (e.g., 'researcher', 'analyst', 'writer')."""

    goal: str
    """High-level goal this agent should accomplish."""

    backstory: str | None = None
    """Optional background context for the agent's persona."""

    capabilities: list[str] | None = None
    """List of required capabilities/tools for this role."""

    delegation_allowed: bool = True
    """Whether this agent can delegate tasks to other agents."""

    verbose: bool = False
    """Whether to enable verbose logging for this agent."""

    metadata: dict[str, Any] | None = None
    """Additional framework-specific metadata."""


@dataclass
class ExecutionResult:
    """Result of framework execution with standardized metrics."""

    success: bool
    """Whether execution completed successfully."""

    output: Any
    """Primary output/result from the execution."""

    agent_outputs: dict[str, Any] | None = None
    """Individual outputs from each agent (if multi-agent)."""

    execution_time_ms: float | None = None
    """Total execution time in milliseconds."""

    token_usage: dict[str, int] | None = None
    """Token usage breakdown (prompt_tokens, completion_tokens, total_tokens)."""

    cost_usd: float | None = None
    """Estimated cost in USD."""

    state_checkpoint: str | None = None
    """ID of state checkpoint (if state persistence enabled)."""

    metadata: dict[str, Any] | None = None
    """Additional execution metadata."""


class FrameworkAdapter(Protocol):
    """Universal interface for AI agent framework adapters.

    All framework implementations (CrewAI, LangGraph, AutoGen, LlamaIndex) must
    implement this protocol to enable framework-agnostic workflow execution.

    Example:
        ```python
        # Get adapter for any framework
        adapter = get_framework_adapter("langgraph")  # or "crewai", "autogen", etc.

        # Execute task using the framework
        task = CrewTask(
            task_id="research_task",
            task_type="research",
            description="Research AI agent frameworks",
            inputs={"topic": "agent frameworks"}
        )
        config = CrewConfig(tenant_id="default", timeout_seconds=300)

        result = await adapter.execute_task(task, config)
        if result.success:
            print(f"Result: {result.data['output']}")
        ```
    """

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Get the name of the framework.

        Returns:
            Framework name (e.g., "crewai", "langgraph", "autogen", "llamaindex")
        """
        ...

    @property
    @abstractmethod
    def framework_version(self) -> str:
        """Get the version of the framework.

        Returns:
            Version string (e.g., "0.1.0")
        """
        ...

    @abstractmethod
    async def execute_task(
        self,
        task: CrewTask,
        config: CrewConfig,
    ) -> StepResult[ExecutionResult]:
        """Execute a task using this framework.

        Args:
            task: Task definition with inputs and requirements
            config: Execution configuration (tenant, timeouts, flags, etc.)

        Returns:
            StepResult containing ExecutionResult with outputs and metrics

        Example:
            ```python
            task = CrewTask(
                task_id="summarize",
                task_type="content_processing",
                description="Summarize the article",
                inputs={"article_text": "..."}
            )
            config = CrewConfig(tenant_id="acme_corp", timeout_seconds=60)

            result = await adapter.execute_task(task, config)
            if result.success:
                summary = result.data.output
            ```
        """
        ...

    @abstractmethod
    async def create_agent(
        self,
        role: AgentRole,
        tools: list[Any] | None = None,
    ) -> StepResult[Any]:
        """Create an agent with the specified role and tools.

        Args:
            role: Agent role definition
            tools: List of tools available to the agent

        Returns:
            StepResult containing framework-specific agent instance

        Example:
            ```python
            role = AgentRole(
                role_name="researcher",
                goal="Find and analyze information",
                capabilities=["web_search", "document_analysis"]
            )
            result = await adapter.create_agent(role, tools=[search_tool, analysis_tool])
            if result.success:
                agent = result.data
            ```
        """
        ...

    @abstractmethod
    def supports_feature(self, feature: FrameworkFeature) -> bool:
        """Check if this framework supports a specific feature.

        Args:
            feature: Feature to check support for

        Returns:
            True if feature is supported, False otherwise

        Example:
            ```python
            if adapter.supports_feature(FrameworkFeature.STATE_PERSISTENCE):
                # Enable checkpointing
                config.enable_checkpointing = True
            ```
        """
        ...

    @abstractmethod
    async def save_state(
        self,
        state: dict[str, Any],
        checkpoint_id: str | None = None,
    ) -> StepResult[str]:
        """Save workflow state for later restoration.

        Args:
            state: State data to persist
            checkpoint_id: Optional checkpoint identifier

        Returns:
            StepResult containing checkpoint ID

        Raises:
            NotImplementedError: If framework doesn't support state persistence
        """
        ...

    @abstractmethod
    async def restore_state(
        self,
        checkpoint_id: str,
    ) -> StepResult[dict[str, Any]]:
        """Restore previously saved workflow state.

        Args:
            checkpoint_id: Identifier of the checkpoint to restore

        Returns:
            StepResult containing restored state data

        Raises:
            NotImplementedError: If framework doesn't support state persistence
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Get detailed information about framework capabilities.

        Returns:
            Dictionary with capability information:
            - supported_features: List of FrameworkFeature values
            - max_agents: Maximum number of concurrent agents (or None)
            - supports_streaming: Whether streaming is available
            - supports_async: Whether async execution is available
            - state_backends: List of supported state persistence backends
            - limitations: List of known limitations
            - metadata: Additional capability metadata
        """
        ...


class BaseFrameworkAdapter(ABC):
    """Base implementation of FrameworkAdapter with common functionality.

    Framework implementations should extend this class rather than implementing
    FrameworkAdapter directly. This provides:
    - Common error handling patterns
    - StepResult construction helpers
    - Feature detection helpers
    - Logging and telemetry hooks
    """

    def __init__(self) -> None:
        """Initialize the framework adapter."""
        self._supported_features: set[FrameworkFeature] = set()

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Get the name of the framework."""
        ...

    @property
    @abstractmethod
    def framework_version(self) -> str:
        """Get the version of the framework."""
        ...

    def supports_feature(self, feature: FrameworkFeature) -> bool:
        """Check if this framework supports a specific feature."""
        return feature in self._supported_features

    def _register_feature(self, feature: FrameworkFeature) -> None:
        """Register a supported feature.

        Args:
            feature: Feature to register as supported
        """
        self._supported_features.add(feature)

    def _register_features(self, features: list[FrameworkFeature]) -> None:
        """Register multiple supported features.

        Args:
            features: List of features to register
        """
        self._supported_features.update(features)

    async def save_state(
        self,
        state: dict[str, Any],
        checkpoint_id: str | None = None,
    ) -> StepResult[str]:
        """Save workflow state (default: not supported).

        Subclasses should override this if they support state persistence.
        """
        return StepResult.fail(
            error=f"{self.framework_name} does not support state persistence",
            error_category="unsupported_feature",
        )

    async def restore_state(
        self,
        checkpoint_id: str,
    ) -> StepResult[dict[str, Any]]:
        """Restore workflow state (default: not supported).

        Subclasses should override this if they support state persistence.
        """
        return StepResult.fail(
            error=f"{self.framework_name} does not support state restoration",
            error_category="unsupported_feature",
        )
