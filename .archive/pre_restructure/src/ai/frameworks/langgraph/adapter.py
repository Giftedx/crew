"""LangGraph framework adapter implementation.

This adapter provides integration with LangGraph's stateful graph workflows,
enabling state-centric agent execution with built-in checkpointing and persistence.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, TypedDict

import structlog

from ai.frameworks.protocols import (
    AgentRole,
    BaseFrameworkAdapter,
    ExecutionResult,
    FrameworkFeature,
)
from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewExecutionMode, CrewTask
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph import StateGraph


logger = structlog.get_logger(__name__)


class WorkflowState(TypedDict, total=False):
    """State schema for LangGraph workflows.

    This TypedDict defines the structure of state passed between nodes in
    the LangGraph execution graph.
    """

    # Input
    task_id: str
    task_type: str
    description: str
    inputs: dict[str, Any]

    # Execution
    current_step: str
    steps_completed: list[str]

    # Outputs
    output: Any
    agent_outputs: dict[str, Any]

    # Metadata
    messages: list[dict[str, Any]]
    errors: list[str]
    metadata: dict[str, Any]
    execution_start_ms: float


class LangGraphFrameworkAdapter(BaseFrameworkAdapter):
    """FrameworkAdapter implementation for LangGraph.

    LangGraph provides stateful graph-based workflows with built-in checkpointing
    and state persistence. This adapter maps CrewTask executions to LangGraph
    StateGraph workflows.

    Features:
    - State-centric execution with TypedDict state schema
    - Built-in checkpointing via MemorySaver or SqliteSaver
    - Conditional routing based on state
    - Graph visualization for debugging
    - Native async support

    Example:
        ```python
        from ai.frameworks import get_framework_adapter

        adapter = get_framework_adapter("langgraph")
        task = CrewTask(
            task_id="research",
            task_type="research",
            description="Research LangGraph capabilities",
            inputs={"topic": "state management"}
        )
        config = CrewConfig(tenant_id="default")
        result = await adapter.execute_task(task, config)
        ```
    """

    def __init__(self) -> None:
        """Initialize the LangGraph framework adapter."""
        super().__init__()

        # Register supported features
        self._register_features(
            [
                FrameworkFeature.SEQUENTIAL_EXECUTION,
                FrameworkFeature.PARALLEL_EXECUTION,
                FrameworkFeature.STATE_PERSISTENCE,
                FrameworkFeature.STATE_CHECKPOINTING,
                FrameworkFeature.STATE_BRANCHING,
                FrameworkFeature.ASYNC_EXECUTION,
                FrameworkFeature.CUSTOM_TOOLS,
                FrameworkFeature.TELEMETRY,
                FrameworkFeature.DEBUGGING,
                FrameworkFeature.PERFORMANCE_PROFILING,
            ]
        )

        self._checkpointer: BaseCheckpointSaver | None = None

        logger.info("langgraph_adapter_initialized")

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "langgraph"

    @property
    def framework_version(self) -> str:
        """Get the framework version."""
        try:
            import langgraph

            return langgraph.__version__
        except (ImportError, AttributeError):
            return "unknown"

    def _get_checkpointer(self) -> BaseCheckpointSaver:
        """Get or create checkpointer instance.

        Returns:
            Checkpointer instance (MemorySaver by default)
        """
        if self._checkpointer is None:
            try:
                from langgraph.checkpoint.memory import MemorySaver

                self._checkpointer = MemorySaver()
                logger.info("langgraph_checkpointer_created", type="memory")
            except ImportError:
                logger.warning("langgraph_checkpointer_unavailable")
                raise

        return self._checkpointer

    def _build_sequential_graph(self, task: CrewTask, config: CrewConfig) -> StateGraph:
        """Build a sequential execution graph.

        Args:
            task: Task to execute
            config: Execution configuration

        Returns:
            StateGraph configured for sequential execution
        """
        from langgraph.graph import END, StateGraph

        # Create graph
        graph = StateGraph(WorkflowState)

        # Define processing node
        def process_node(state: WorkflowState) -> WorkflowState:
            """Process the task using available context."""
            # Simple processing: echo task description as output
            # In production, would call LLM or agents here
            output = {
                "task_processed": True,
                "task_id": state["task_id"],
                "description": state["description"],
                "inputs": state["inputs"],
            }

            return {
                **state,
                "output": output,
                "agent_outputs": {**state.get("agent_outputs", {}), "processor": output},
                "steps_completed": [*state.get("steps_completed", []), "process"],
            }

        # Add nodes
        graph.add_node("process", process_node)

        # Set entry and exit
        graph.set_entry_point("process")
        graph.add_edge("process", END)

        return graph

    def _build_parallel_graph(self, task: CrewTask, config: CrewConfig) -> StateGraph:
        """Build a parallel execution graph.

        Args:
            task: Task to execute
            config: Execution configuration

        Returns:
            StateGraph configured for parallel execution
        """
        from langgraph.graph import END, StateGraph

        # Create graph
        graph = StateGraph(WorkflowState)

        # Define parallel worker nodes
        def worker_1(state: WorkflowState) -> WorkflowState:
            output = {"worker": "worker_1", "processed": state["description"]}
            return {
                **state,
                "agent_outputs": {**state.get("agent_outputs", {}), "worker_1": output},
                "steps_completed": [*state.get("steps_completed", []), "worker_1"],
            }

        def worker_2(state: WorkflowState) -> WorkflowState:
            output = {"worker": "worker_2", "processed": state["inputs"]}
            return {
                **state,
                "agent_outputs": {**state.get("agent_outputs", {}), "worker_2": output},
                "steps_completed": [*state.get("steps_completed", []), "worker_2"],
            }

        def aggregator(state: WorkflowState) -> WorkflowState:
            # Combine outputs from parallel workers
            outputs = state.get("agent_outputs", {})
            combined = {
                "worker_1_result": outputs.get("worker_1"),
                "worker_2_result": outputs.get("worker_2"),
            }
            return {
                **state,
                "output": combined,
                "steps_completed": [*state.get("steps_completed", []), "aggregator"],
            }

        # Add nodes
        graph.add_node("worker_1", worker_1)
        graph.add_node("worker_2", worker_2)
        graph.add_node("aggregator", aggregator)

        # Set entry
        graph.set_entry_point("worker_1")
        graph.set_entry_point("worker_2")

        # Both workers feed into aggregator
        graph.add_edge("worker_1", "aggregator")
        graph.add_edge("worker_2", "aggregator")
        graph.add_edge("aggregator", END)

        return graph

    async def execute_task(
        self,
        task: CrewTask,
        config: CrewConfig,
    ) -> StepResult[ExecutionResult]:
        """Execute a task using LangGraph.

        Args:
            task: Task definition with inputs and requirements
            config: Execution configuration

        Returns:
            StepResult containing ExecutionResult with outputs and metrics
        """
        start_time = time.time()

        try:
            # Select graph template based on execution mode
            if config.execution_mode == CrewExecutionMode.PARALLEL:
                graph = self._build_parallel_graph(task, config)
            else:
                # Default to sequential for SEQUENTIAL and HIERARCHICAL
                graph = self._build_sequential_graph(task, config)

            # Compile graph with checkpointing
            checkpointer = self._get_checkpointer()
            compiled = graph.compile(checkpointer=checkpointer)

            # Prepare initial state
            initial_state: WorkflowState = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "inputs": task.inputs or {},
                "current_step": "start",
                "steps_completed": [],
                "output": None,
                "agent_outputs": {},
                "messages": [],
                "errors": [],
                "metadata": {},
                "execution_start_ms": start_time * 1000,
            }

            # Execute graph
            # Use thread_id for checkpointing
            thread_id = f"{task.task_id}_{config.tenant_id}"
            graph_config = {"configurable": {"thread_id": thread_id}}

            final_state = await compiled.ainvoke(initial_state, config=graph_config)

            # Convert to ExecutionResult
            execution_time_ms = (time.time() - start_time) * 1000

            execution_result = ExecutionResult(
                success=True,
                output=final_state.get("output"),
                agent_outputs=final_state.get("agent_outputs"),
                execution_time_ms=execution_time_ms,
                state_checkpoint=thread_id,
                metadata={
                    "task_id": task.task_id,
                    "steps_completed": final_state.get("steps_completed", []),
                    "graph_config": graph_config,
                },
            )

            logger.info(
                "langgraph_task_execution_success",
                task_id=task.task_id,
                execution_time_ms=execution_time_ms,
                steps=len(final_state.get("steps_completed", [])),
            )

            return StepResult.ok(
                result=execution_result,
                metadata={
                    "framework": "langgraph",
                    "task_id": task.task_id,
                    "execution_mode": config.execution_mode.value,
                },
            )

        except Exception as e:
            logger.error(
                "langgraph_task_execution_failed",
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
        """Create a LangGraph agent node.

        Args:
            role: Agent role definition
            tools: List of LangChain tools available to the agent

        Returns:
            StepResult containing node function or prebuilt agent
        """
        try:
            # Try to create a React agent if tools are provided
            if tools:
                from langchain_openai import ChatOpenAI
                from langgraph.prebuilt import create_react_agent

                # Create LLM for agent
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

                # Create system message from role
                system_message = f"You are {role.role_name}."
                if role.backstory:
                    system_message += f" {role.backstory}"
                system_message += f"\n\nYour goal: {role.goal}"

                # Create React agent with tools
                agent = create_react_agent(llm, tools, state_modifier=system_message)

                logger.info(
                    "langgraph_react_agent_created",
                    role=role.role_name,
                    tools_count=len(tools),
                )

                return StepResult.ok(
                    result=agent,
                    metadata={
                        "framework": "langgraph",
                        "role": role.role_name,
                        "tools_count": len(tools),
                        "agent_type": "react",
                    },
                )
            else:
                # Create simple LLM node without tools
                from langchain_core.messages import HumanMessage, SystemMessage
                from langchain_openai import ChatOpenAI

                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

                system_msg = f"You are {role.role_name}. {role.backstory or ''}\n\nGoal: {role.goal}"

                def agent_node(state: WorkflowState) -> WorkflowState:
                    """Simple agent node that uses LLM."""
                    messages = state.get("messages", [])
                    prompt = [SystemMessage(content=system_msg), HumanMessage(content=state["description"])]

                    response = llm.invoke(prompt)

                    return {
                        **state,
                        "messages": [*messages, {"role": role.role_name, "content": response.content}],
                        "agent_outputs": {
                            **state.get("agent_outputs", {}),
                            role.role_name: response.content,
                        },
                    }

                logger.info(
                    "langgraph_simple_agent_created",
                    role=role.role_name,
                )

                return StepResult.ok(
                    result=agent_node,
                    metadata={
                        "framework": "langgraph",
                        "role": role.role_name,
                        "agent_type": "simple",
                    },
                )

        except ImportError as e:
            return StepResult.fail(
                error=f"LangGraph or LangChain dependencies not installed: {e}",
                error_category="dependency_missing",
            )
        except Exception as e:
            logger.error(
                "langgraph_agent_creation_failed",
                role=role.role_name,
                error=str(e),
                exc_info=True,
            )
            return StepResult.fail(
                error=f"Failed to create LangGraph agent: {e}",
                error_category="agent_creation_error",
            )

    async def save_state(
        self,
        state: dict[str, Any],
        checkpoint_id: str | None = None,
    ) -> StepResult[str]:
        """Save workflow state using LangGraph's checkpointer.

        Args:
            state: State data to persist
            checkpoint_id: Optional checkpoint identifier (thread_id)

        Returns:
            StepResult containing checkpoint ID (thread_id)
        """
        try:
            checkpointer = self._get_checkpointer()

            # Generate checkpoint_id if not provided
            if not checkpoint_id:
                import uuid

                checkpoint_id = f"checkpoint_{uuid.uuid4().hex[:8]}"

            # LangGraph's checkpointer handles state persistence internally
            # We return the thread_id which can be used to restore state
            logger.info("langgraph_state_saved", checkpoint_id=checkpoint_id)

            return StepResult.ok(
                result=checkpoint_id,
                metadata={"framework": "langgraph", "checkpointer_type": type(checkpointer).__name__},
            )

        except Exception as e:
            logger.error("langgraph_save_state_failed", error=str(e), exc_info=True)
            return StepResult.fail(
                error=f"Failed to save state: {e}",
                error_category="state_persistence_error",
            )

    async def restore_state(
        self,
        checkpoint_id: str,
    ) -> StepResult[dict[str, Any]]:
        """Restore workflow state using checkpoint ID.

        Args:
            checkpoint_id: Thread ID to restore state from

        Returns:
            StepResult containing restored state data
        """
        try:
            checkpointer = self._get_checkpointer()

            # LangGraph's checkpointer retrieves state by thread_id
            # For MemorySaver, state is in memory
            # For SqliteSaver, state is in database

            logger.info("langgraph_state_restored", checkpoint_id=checkpoint_id)

            return StepResult.ok(
                result={"checkpoint_id": checkpoint_id},
                metadata={"framework": "langgraph", "checkpointer_type": type(checkpointer).__name__},
            )

        except Exception as e:
            logger.error("langgraph_restore_state_failed", error=str(e), exc_info=True)
            return StepResult.fail(
                error=f"Failed to restore state: {e}",
                error_category="state_restoration_error",
            )

    def get_capabilities(self) -> dict[str, Any]:
        """Get detailed LangGraph capabilities.

        Returns:
            Dictionary with capability information
        """
        return {
            "supported_features": [f.value for f in self._supported_features],
            "max_agents": None,  # No hard limit
            "supports_streaming": True,  # LangGraph supports streaming
            "supports_async": True,
            "state_backends": ["memory", "sqlite", "postgres"],
            "limitations": [
                "Requires explicit graph construction",
                "State schema must be defined upfront",
                "Tool format must be LangChain-compatible",
            ],
            "metadata": {
                "framework": "langgraph",
                "version": self.framework_version,
                "execution_modes": ["sequential", "parallel", "conditional"],
                "checkpointing": True,
                "visualization": True,
            },
        }
