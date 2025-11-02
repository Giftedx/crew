"""CrewAI framework adapter implementation.

This adapter wraps the existing UnifiedCrewExecutor from crew_core to provide
a FrameworkAdapter-compliant interface for CrewAI-based workflow execution.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog

from ai.frameworks.protocols import (
    AgentRole,
    BaseFrameworkAdapter,
    ExecutionResult,
    FrameworkFeature,
)
from ultimate_discord_intelligence_bot.crew_core.executor import UnifiedCrewExecutor
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewTask


logger = structlog.get_logger(__name__)


class CrewAIFrameworkAdapter(BaseFrameworkAdapter):
    """FrameworkAdapter implementation for CrewAI.

    This adapter wraps the existing crew_core.UnifiedCrewExecutor to provide
    framework-agnostic access to CrewAI functionality. It maintains full backward
    compatibility while enabling multi-framework workflows.

    Features:
    - Sequential, parallel, and hierarchical execution modes
    - Full observability via metrics and structured logging
    - Tool integration via CrewAI's tool system
    - Retry logic with exponential backoff
    - Multi-tenant support

    Example:
        ```python
        from ai.frameworks import get_framework_adapter

        adapter = get_framework_adapter("crewai")
        task = CrewTask(
            task_id="research",
            task_type="research",
            description="Research AI frameworks",
            inputs={"topic": "LangChain vs CrewAI"}
        )
        config = CrewConfig(tenant_id="default")
        result = await adapter.execute_task(task, config)
        ```
    """

    def __init__(self) -> None:
        """Initialize the CrewAI framework adapter."""
        super().__init__()

        # Register supported features
        self._register_features(
            [
                FrameworkFeature.SEQUENTIAL_EXECUTION,
                FrameworkFeature.PARALLEL_EXECUTION,
                FrameworkFeature.HIERARCHICAL_EXECUTION,
                FrameworkFeature.DYNAMIC_AGENT_CREATION,
                FrameworkFeature.AGENT_MEMORY,
                FrameworkFeature.MULTI_AGENT_COLLABORATION,
                FrameworkFeature.CUSTOM_TOOLS,
                FrameworkFeature.TOOL_CHAINING,
                FrameworkFeature.TOOL_RETRY,
                FrameworkFeature.ASYNC_EXECUTION,
                FrameworkFeature.TELEMETRY,
                FrameworkFeature.DEBUGGING,
            ]
        )

        logger.info("crewai_adapter_initialized")

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "crewai"

    @property
    def framework_version(self) -> str:
        """Get the framework version."""
        # Import here to avoid circular dependencies
        try:
            import crewai

            return crewai.__version__
        except (ImportError, AttributeError):
            return "unknown"

    async def execute_task(
        self,
        task: CrewTask,
        config: CrewConfig,
    ) -> StepResult[ExecutionResult]:
        """Execute a task using CrewAI via UnifiedCrewExecutor.

        Args:
            task: Task definition with inputs and requirements
            config: Execution configuration

        Returns:
            StepResult containing ExecutionResult with outputs and metrics
        """
        start_time = time.time()

        try:
            # Create UnifiedCrewExecutor with the config
            executor = UnifiedCrewExecutor(config)

            # Execute the task
            crew_result = await executor.execute(task, config)

            # Convert CrewExecutionResult to ExecutionResult
            execution_time_ms = (time.time() - start_time) * 1000

            execution_result = ExecutionResult(
                success=crew_result.step_result.success,
                output=crew_result.step_result.data if crew_result.step_result.success else None,
                agent_outputs=crew_result.agents_used,
                execution_time_ms=execution_time_ms,
                token_usage=crew_result.metadata.get("token_usage") if crew_result.metadata else None,
                cost_usd=crew_result.metadata.get("cost_usd") if crew_result.metadata else None,
                metadata={
                    "task_id": crew_result.task_id,
                    "tools_used": crew_result.tools_used,
                    "cache_hits": crew_result.cache_hits,
                    "retry_count": crew_result.retry_count,
                    "execution_time_seconds": crew_result.execution_time_seconds,
                },
            )

            return StepResult.ok(
                result=execution_result,
                metadata={
                    "framework": "crewai",
                    "task_id": task.task_id,
                    "execution_mode": config.execution_mode.value,
                },
            )

        except Exception as e:
            logger.error(
                "crewai_task_execution_failed",
                task_id=task.task_id,
                error=str(e),
                exc_info=True,
            )

            execution_time_ms = (time.time() - start_time) * 1000

            execution_result = ExecutionResult(
                success=False,
                output=None,
                execution_time_ms=execution_time_ms,
                metadata={"error": str(e)},
            )

            return StepResult.fail(
                error=str(e),
                error_category="execution_error",
                data=execution_result,
            )

    async def create_agent(
        self,
        role: AgentRole,
        tools: list[Any] | None = None,
    ) -> StepResult[Any]:
        """Create a CrewAI agent with the specified role.

        Args:
            role: Agent role definition
            tools: List of tools available to the agent

        Returns:
            StepResult containing CrewAI Agent instance
        """
        try:
            from crewai import Agent

            # Convert our AgentRole to CrewAI Agent parameters
            agent_params = {
                "role": role.role_name,
                "goal": role.goal,
                "verbose": role.verbose,
                "allow_delegation": role.delegation_allowed,
            }

            if role.backstory:
                agent_params["backstory"] = role.backstory

            if tools:
                agent_params["tools"] = tools

            # Create the agent
            agent = Agent(**agent_params)

            logger.info(
                "crewai_agent_created",
                role=role.role_name,
                tools_count=len(tools) if tools else 0,
            )

            return StepResult.ok(
                result=agent,
                metadata={
                    "framework": "crewai",
                    "role": role.role_name,
                    "tools_count": len(tools) if tools else 0,
                },
            )

        except ImportError:
            return StepResult.fail(
                error="CrewAI not installed",
                error_category="dependency_missing",
            )
        except Exception as e:
            logger.error(
                "crewai_agent_creation_failed",
                role=role.role_name,
                error=str(e),
                exc_info=True,
            )
            return StepResult.fail(
                error=f"Failed to create CrewAI agent: {e}",
                error_category="agent_creation_error",
            )

    def get_capabilities(self) -> dict[str, Any]:
        """Get detailed CrewAI capabilities.

        Returns:
            Dictionary with capability information
        """
        return {
            "supported_features": [f.value for f in self._supported_features],
            "max_agents": None,  # No hard limit
            "supports_streaming": False,
            "supports_async": True,
            "state_backends": [],  # CrewAI doesn't have built-in state persistence
            "limitations": [
                "No built-in state persistence",
                "No streaming support",
                "Limited distributed execution",
            ],
            "metadata": {
                "framework": "crewai",
                "version": self.framework_version,
                "execution_modes": ["sequential", "parallel", "hierarchical"],
            },
        }
