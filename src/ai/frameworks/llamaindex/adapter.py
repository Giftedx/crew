"""LlamaIndex framework adapter implementation.

This adapter provides integration with LlamaIndex's query engine and agent workflows,
enabling RAG-powered task execution with flexible data connectors.
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
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from llama_index.core.agent import AgentRunner

    from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewTask


logger = structlog.get_logger(__name__)


class LlamaIndexFrameworkAdapter(BaseFrameworkAdapter):
    """FrameworkAdapter implementation for LlamaIndex.

    LlamaIndex provides query engines and agents for RAG (Retrieval Augmented Generation)
    workflows. This adapter maps CrewTask executions to LlamaIndex query/agent operations.

    Features:
    - Query engine-based task execution
    - Agent workflows with tool integration
    - RAG capabilities with flexible data loaders
    - Streaming support for incremental responses
    - Multi-step reasoning via ReAct agents

    Example:
        ```python
        from ai.frameworks import get_framework_adapter

        adapter = get_framework_adapter("llamaindex")
        task = CrewTask(
            task_id="query",
            task_type="query",
            description="What are the key features of LlamaIndex?",
            inputs={"context": "..."}
        )
        config = CrewConfig(tenant_id="default")
        result = await adapter.execute_task(task, config)
        ```
    """

    def __init__(self) -> None:
        """Initialize the LlamaIndex framework adapter."""
        super().__init__()

        # Register supported features
        self._register_features(
            [
                FrameworkFeature.SEQUENTIAL_EXECUTION,
                FrameworkFeature.ASYNC_EXECUTION,
                FrameworkFeature.CUSTOM_TOOLS,
                FrameworkFeature.TOOL_CHAINING,
                FrameworkFeature.STREAMING,
                FrameworkFeature.TELEMETRY,
                FrameworkFeature.DEBUGGING,
            ]
        )

        logger.info("llamaindex_adapter_initialized")

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "llamaindex"

    @property
    def framework_version(self) -> str:
        """Get the framework version."""
        try:
            import llama_index

            return llama_index.__version__
        except (ImportError, AttributeError):
            return "unknown"

    async def execute_task(
        self,
        task: CrewTask,
        config: CrewConfig,
    ) -> StepResult[ExecutionResult]:
        """Execute a task using LlamaIndex query engine or agent.

        Args:
            task: Task definition with inputs and requirements
            config: Execution configuration

        Returns:
            StepResult containing ExecutionResult with outputs and metrics
        """
        start_time = time.time()

        try:
            from llama_index.core import Settings, VectorStoreIndex
            from llama_index.core.schema import Document
            from llama_index.llms.openai import OpenAI

            # Configure LLM
            Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.7)

            # Create simple in-memory index for task context
            documents = []

            # Add task description as document
            documents.append(Document(text=task.description))

            # Add task inputs as documents
            if task.inputs:
                for key, value in task.inputs.items():
                    if isinstance(value, str):
                        documents.append(Document(text=f"{key}: {value}"))

            # Create vector index
            index = VectorStoreIndex.from_documents(documents)

            # Create query engine
            query_engine = index.as_query_engine()

            # Execute query
            query = task.description
            response = await query_engine.aquery(query)

            # Extract output
            output = str(response)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Build execution result
            execution_result = ExecutionResult(
                success=True,
                output=output,
                agent_outputs={"query_engine": output},
                execution_time_ms=execution_time_ms,
                metadata={
                    "task_id": task.task_id,
                    "query": query,
                    "source_nodes": len(response.source_nodes) if hasattr(response, "source_nodes") else 0,
                },
            )

            logger.info(
                "llamaindex_task_execution_success",
                task_id=task.task_id,
                execution_time_ms=execution_time_ms,
            )

            return StepResult.ok(
                result=execution_result,
                metadata={
                    "framework": "llamaindex",
                    "task_id": task.task_id,
                    "execution_mode": "query_engine",
                },
            )

        except Exception as e:
            logger.error(
                "llamaindex_task_execution_failed",
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
    ) -> StepResult[AgentRunner]:
        """Create a LlamaIndex agent with the specified role.

        Args:
            role: Agent role definition
            tools: List of LlamaIndex tools (optional)

        Returns:
            StepResult containing LlamaIndex AgentRunner instance
        """
        try:
            from llama_index.core.agent import ReActAgent
            from llama_index.llms.openai import OpenAI

            # Create LLM
            llm = OpenAI(model="gpt-4o-mini", temperature=0.7)

            # Build system prompt from role
            system_prompt = f"You are {role.role_name}."
            if role.backstory:
                system_prompt += f" {role.backstory}"
            system_prompt += f"\n\nYour goal: {role.goal}"

            # Create agent
            if tools:
                # Create ReAct agent with tools
                agent = ReActAgent.from_tools(
                    tools=tools,
                    llm=llm,
                    verbose=role.verbose,
                    system_prompt=system_prompt,
                )
            else:
                # Create simple agent without tools
                agent = ReActAgent.from_tools(
                    tools=[],
                    llm=llm,
                    verbose=role.verbose,
                    system_prompt=system_prompt,
                )

            logger.info(
                "llamaindex_agent_created",
                role=role.role_name,
                tools_count=len(tools) if tools else 0,
            )

            return StepResult.ok(
                result=agent,
                metadata={
                    "framework": "llamaindex",
                    "role": role.role_name,
                    "tools_count": len(tools) if tools else 0,
                },
            )

        except ImportError:
            return StepResult.fail(
                error="LlamaIndex not installed",
                error_category="dependency_missing",
            )
        except Exception as e:
            logger.error(
                "llamaindex_agent_creation_failed",
                role=role.role_name,
                error=str(e),
                exc_info=True,
            )
            return StepResult.fail(
                error=f"Failed to create LlamaIndex agent: {e}",
                error_category="agent_creation_error",
            )

    async def save_state(
        self,
        state: dict[str, Any],
        checkpoint_id: str | None = None,
    ) -> StepResult[str]:
        """Save workflow state (not supported).

        LlamaIndex doesn't have built-in state persistence for workflows.

        Args:
            state: State data to persist
            checkpoint_id: Optional checkpoint identifier

        Returns:
            StepResult with error indicating feature not supported
        """
        logger.warning("llamaindex_save_state_not_supported")

        return StepResult.fail(
            error="LlamaIndex does not support workflow state persistence",
            error_category="unsupported_feature",
        )

    async def restore_state(
        self,
        checkpoint_id: str,
    ) -> StepResult[dict[str, Any]]:
        """Restore workflow state (not supported).

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            StepResult with error indicating feature not supported
        """
        logger.warning("llamaindex_restore_state_not_supported", checkpoint_id=checkpoint_id)

        return StepResult.fail(
            error="LlamaIndex does not support workflow state restoration",
            error_category="unsupported_feature",
        )

    def get_capabilities(self) -> dict[str, Any]:
        """Get detailed LlamaIndex capabilities.

        Returns:
            Dictionary with capability information
        """
        return {
            "supported_features": [f.value for f in self._supported_features],
            "max_agents": None,
            "supports_streaming": True,
            "supports_async": True,
            "state_backends": [],  # No built-in state persistence
            "limitations": [
                "No built-in workflow state persistence",
                "Limited multi-agent orchestration",
                "Primarily designed for RAG use cases",
                "Tools must be in LlamaIndex format",
            ],
            "metadata": {
                "framework": "llamaindex",
                "version": self.framework_version,
                "execution_modes": ["query_engine", "agent", "workflow"],
                "rag_support": True,
                "data_connectors": True,
            },
        }
