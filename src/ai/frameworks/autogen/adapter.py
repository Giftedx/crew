"""AutoGen framework adapter implementation.

This adapter provides integration with AutoGen's multi-agent conversation framework,
enabling conversational task solving through agent collaboration and debate.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any

import structlog

from ai.frameworks.protocols import (
    AgentRole,
    BaseFrameworkAdapter,
    ExecutionResult,
    FrameworkFeature,
)
from ultimate_discord_intelligence_bot.crew_core.interfaces import CrewConfig, CrewTask
from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from autogen import AssistantAgent, ConversableAgent


logger = structlog.get_logger(__name__)


class AutoGenFrameworkAdapter(BaseFrameworkAdapter):
    """FrameworkAdapter implementation for AutoGen.

    AutoGen provides multi-agent conversation-based workflows where agents
    collaborate through message passing to solve tasks. This adapter maps
    CrewTask executions to AutoGen agent conversations.

    Features:
    - Conversational task solving via agent message exchange
    - Multi-agent collaboration through GroupChat
    - Human-in-the-loop support via UserProxyAgent
    - Function calling for tool integration
    - Autonomous agent behavior with termination conditions

    Limitations:
    - No built-in state persistence (conversation history only)
    - Sequential turn-taking (no true parallel execution)
    - Limited hierarchical organization

    Example:
        ```python
        from ai.frameworks import get_framework_adapter

        adapter = get_framework_adapter("autogen")
        task = CrewTask(
            task_id="analysis",
            task_type="analysis",
            description="Analyze the sentiment of customer reviews",
            inputs={"reviews": [...]}
        )
        config = CrewConfig(tenant_id="default")
        result = await adapter.execute_task(task, config)
        ```
    """

    def __init__(self) -> None:
        """Initialize the AutoGen framework adapter."""
        super().__init__()

        # Register supported features
        self._register_features(
            [
                FrameworkFeature.SEQUENTIAL_EXECUTION,
                FrameworkFeature.MULTI_AGENT_COLLABORATION,
                FrameworkFeature.HUMAN_IN_LOOP,
                FrameworkFeature.ASYNC_EXECUTION,
                FrameworkFeature.CUSTOM_TOOLS,
                FrameworkFeature.TELEMETRY,
                FrameworkFeature.DEBUGGING,
            ]
        )

        logger.info("autogen_adapter_initialized")

    @property
    def framework_name(self) -> str:
        """Get the framework name."""
        return "autogen"

    @property
    def framework_version(self) -> str:
        """Get the framework version."""
        try:
            import autogen

            return autogen.__version__
        except (ImportError, AttributeError):
            return "unknown"

    def _create_llm_config(self, model: str = "gpt-4o-mini", temperature: float = 0.7) -> dict[str, Any]:
        """Create LLM configuration for AutoGen agents.

        Args:
            model: Model name
            temperature: Sampling temperature

        Returns:
            LLM config dictionary
        """
        return {
            "model": model,
            "temperature": temperature,
            "timeout": 120,
        }

    async def execute_task(
        self,
        task: CrewTask,
        config: CrewConfig,
    ) -> StepResult[ExecutionResult]:
        """Execute a task using AutoGen multi-agent conversation.

        Args:
            task: Task definition with inputs and requirements
            config: Execution configuration

        Returns:
            StepResult containing ExecutionResult with outputs and metrics
        """
        start_time = time.time()

        try:
            from autogen import AssistantAgent, UserProxyAgent

            # Create LLM config
            llm_config = self._create_llm_config()

            # Create assistant agent to solve the task
            assistant = AssistantAgent(
                name="task_executor",
                system_message=(
                    f"You are an expert at {task.task_type}. "
                    f"Your task: {task.description}\n\n"
                    f"Provide a clear, concise solution."
                ),
                llm_config=llm_config,
            )

            # Create user proxy for autonomous execution
            user_proxy = UserProxyAgent(
                name="user_proxy",
                human_input_mode="NEVER",  # Fully autonomous
                max_consecutive_auto_reply=10,
                is_termination_msg=lambda x: x.get("content", "").strip().endswith("TERMINATE"),
                code_execution_config=False,  # Disable code execution for safety
            )

            # Format task inputs as context
            context = f"Task: {task.description}\n"
            if task.inputs:
                context += f"\nInputs:\n{json.dumps(task.inputs, indent=2)}"

            # Initiate conversation
            await user_proxy.a_initiate_chat(
                assistant,
                message=context,
            )

            # Extract conversation results
            messages = user_proxy.chat_messages.get(assistant, [])

            # Get final output (last assistant message)
            output = None
            agent_outputs: dict[str, Any] = {}

            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    output = msg.get("content", "")
                    agent_outputs["task_executor"] = output
                    break

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Build execution result
            execution_result = ExecutionResult(
                success=True,
                output=output,
                agent_outputs=agent_outputs,
                execution_time_ms=execution_time_ms,
                metadata={
                    "task_id": task.task_id,
                    "conversation_length": len(messages),
                    "messages": messages,
                },
            )

            logger.info(
                "autogen_task_execution_success",
                task_id=task.task_id,
                execution_time_ms=execution_time_ms,
                message_count=len(messages),
            )

            return StepResult.ok(
                result=execution_result,
                metadata={
                    "framework": "autogen",
                    "task_id": task.task_id,
                    "conversation_turns": len(messages),
                },
            )

        except Exception as e:
            logger.error(
                "autogen_task_execution_failed",
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
    ) -> StepResult[ConversableAgent]:
        """Create an AutoGen agent with the specified role.

        Args:
            role: Agent role definition
            tools: List of AutoGen-compatible functions (optional)

        Returns:
            StepResult containing AutoGen AssistantAgent instance
        """
        try:
            from autogen import AssistantAgent

            # Build system message from role
            system_message = f"You are {role.role_name}."
            if role.backstory:
                system_message += f" {role.backstory}"
            system_message += f"\n\nYour goal: {role.goal}"

            # Create LLM config
            llm_config = self._create_llm_config()

            # Add function calling for tools if provided
            if tools:
                # AutoGen expects tools in OpenAI function calling format
                # For now, assume tools are already in correct format
                # (Full conversion will be in Week 3 universal tools)
                llm_config["functions"] = tools

            # Create agent
            agent = AssistantAgent(
                name=role.role_name.replace(" ", "_").lower(),
                system_message=system_message,
                llm_config=llm_config,
            )

            logger.info(
                "autogen_agent_created",
                role=role.role_name,
                tools_count=len(tools) if tools else 0,
            )

            return StepResult.ok(
                result=agent,
                metadata={
                    "framework": "autogen",
                    "role": role.role_name,
                    "tools_count": len(tools) if tools else 0,
                },
            )

        except ImportError:
            return StepResult.fail(
                error="AutoGen not installed",
                error_category="dependency_missing",
            )
        except Exception as e:
            logger.error(
                "autogen_agent_creation_failed",
                role=role.role_name,
                error=str(e),
                exc_info=True,
            )
            return StepResult.fail(
                error=f"Failed to create AutoGen agent: {e}",
                error_category="agent_creation_error",
            )

    async def save_state(
        self,
        state: dict[str, Any],
        checkpoint_id: str | None = None,
    ) -> StepResult[str]:
        """Save conversation state (limited support).

        AutoGen doesn't have built-in state persistence. This method
        returns the state as JSON for external storage.

        Args:
            state: State data to persist (typically conversation history)
            checkpoint_id: Optional checkpoint identifier

        Returns:
            StepResult containing checkpoint ID
        """
        try:
            # Generate checkpoint_id if not provided
            if not checkpoint_id:
                import uuid

                checkpoint_id = f"autogen_checkpoint_{uuid.uuid4().hex[:8]}"

            # Convert state to JSON for external storage
            state_json = json.dumps(state)

            logger.info(
                "autogen_state_saved",
                checkpoint_id=checkpoint_id,
                state_size=len(state_json),
            )

            return StepResult.ok(
                result=checkpoint_id,
                metadata={
                    "framework": "autogen",
                    "state_json": state_json,
                    "warning": "AutoGen state persistence is limited - conversation history only",
                },
            )

        except Exception as e:
            logger.error("autogen_save_state_failed", error=str(e), exc_info=True)
            return StepResult.fail(
                error=f"Failed to save state: {e}",
                error_category="state_persistence_error",
            )

    async def restore_state(
        self,
        checkpoint_id: str,
    ) -> StepResult[dict[str, Any]]:
        """Restore conversation state (not supported).

        AutoGen doesn't support restoring conversation state without
        replaying the entire conversation.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            StepResult with error indicating feature not supported
        """
        logger.warning("autogen_restore_state_not_supported", checkpoint_id=checkpoint_id)

        return StepResult.fail(
            error="AutoGen does not support state restoration without replaying entire conversation",
            error_category="unsupported_feature",
        )

    def get_capabilities(self) -> dict[str, Any]:
        """Get detailed AutoGen capabilities.

        Returns:
            Dictionary with capability information
        """
        return {
            "supported_features": [f.value for f in self._supported_features],
            "max_agents": None,  # No hard limit on conversation participants
            "supports_streaming": False,
            "supports_async": True,
            "state_backends": [],  # No built-in state persistence
            "limitations": [
                "No built-in state persistence (conversation history only)",
                "Sequential turn-taking (no true parallel execution)",
                "State restoration not supported",
                "Tools must be in AutoGen/OpenAI function calling format",
            ],
            "metadata": {
                "framework": "autogen",
                "version": self.framework_version,
                "execution_modes": ["conversation", "group_chat"],
                "human_in_loop": True,
                "code_execution": True,
            },
        }
