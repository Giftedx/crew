"""Unified workflow state management across AI frameworks.

This module provides a framework-agnostic state representation that can be
converted to and from CrewAI, LangGraph, AutoGen, and LlamaIndex formats.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from .protocols import Checkpoint, Message, MessageRole, StateMetadata


logger = structlog.get_logger(__name__)


@dataclass
class UnifiedWorkflowState:
    """Framework-agnostic workflow state.

    This class represents workflow state in a universal format that can be
    converted to any supported AI framework format. It maintains conversation
    history, context, checkpoints, and metadata in a way that preserves
    information across framework transitions.

    Attributes:
        messages: Conversation history with role-based messages
        context: Arbitrary context data for the workflow
        checkpoints: State snapshots for recovery/rollback
        metadata: Metadata about the workflow and state
    """

    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    metadata: StateMetadata = field(default_factory=lambda: StateMetadata(workflow_id=str(uuid.uuid4())))

    def add_message(
        self,
        role: MessageRole | str,
        content: str,
        name: str | None = None,
        function_call: dict[str, Any] | None = None,
        **metadata: Any,
    ) -> None:
        """Add a message to the conversation history.

        Args:
            role: Role of the message sender
            content: Message content
            name: Optional name of function/tool
            function_call: Optional function call data
            **metadata: Additional metadata for the message
        """
        if isinstance(role, str):
            role = MessageRole(role)

        message = Message(
            role=role,
            content=content,
            name=name,
            function_call=function_call,
            metadata=metadata,
        )
        self.messages.append(message)
        self.metadata.updated_at = datetime.now()

        logger.info(
            "message_added",
            role=role.value,
            content_length=len(content),
            workflow_id=self.metadata.workflow_id,
        )

    def update_context(self, **kwargs: Any) -> None:
        """Update workflow context with new key-value pairs.

        Args:
            **kwargs: Context key-value pairs to update
        """
        self.context.update(kwargs)
        self.metadata.updated_at = datetime.now()

        logger.info(
            "context_updated",
            keys=list(kwargs.keys()),
            workflow_id=self.metadata.workflow_id,
        )

    def create_checkpoint(self, name: str, **metadata: Any) -> Checkpoint:
        """Create a checkpoint of the current state.

        Args:
            name: Human-readable name for the checkpoint
            **metadata: Additional checkpoint metadata

        Returns:
            The created Checkpoint instance
        """
        # Create snapshot without checkpoints to avoid recursion
        # Use copy to avoid reference issues
        snapshot = {
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context.copy(),
            "checkpoints": [],  # Don't include checkpoints in snapshot
            "metadata": self.metadata.to_dict(),
        }

        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            name=name,
            state_snapshot=snapshot,
            framework=self.metadata.current_framework,
            metadata=metadata,
        )
        self.checkpoints.append(checkpoint)
        self.metadata.updated_at = datetime.now()

        logger.info(
            "checkpoint_created",
            checkpoint_name=name,
            checkpoint_id=checkpoint.id,
            workflow_id=self.metadata.workflow_id,
        )

        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore state from a checkpoint.

        Args:
            checkpoint_id: ID of the checkpoint to restore

        Returns:
            True if restored successfully, False if checkpoint not found
        """
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                restored_state = UnifiedWorkflowState.from_dict(checkpoint.state_snapshot)
                self.messages = restored_state.messages
                self.context = restored_state.context.copy()  # Create a copy to avoid reference issues
                # Don't restore metadata or checkpoints - keep current ones
                self.metadata.updated_at = datetime.now()

                logger.info(
                    "checkpoint_restored",
                    checkpoint_id=checkpoint_id,
                    checkpoint_name=checkpoint.name,
                    workflow_id=self.metadata.workflow_id,
                )
                return True

        logger.warning(
            "checkpoint_not_found",
            checkpoint_id=checkpoint_id,
            workflow_id=self.metadata.workflow_id,
        )
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary for persistence.

        Returns:
            Dictionary representation of the state
        """
        return {
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "checkpoints": [cp.to_dict() for cp in self.checkpoints],
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UnifiedWorkflowState":
        """Deserialize state from dictionary.

        Args:
            data: Dictionary representation of the state

        Returns:
            UnifiedWorkflowState instance
        """
        return cls(
            messages=[Message.from_dict(msg) for msg in data.get("messages", [])],
            context=data.get("context", {}),
            checkpoints=[Checkpoint.from_dict(cp) for cp in data.get("checkpoints", [])],
            metadata=StateMetadata.from_dict(data["metadata"]),
        )

    # Framework conversion methods

    def to_langgraph_state(self) -> dict[str, Any]:
        """Convert to LangGraph state format.

        LangGraph uses a dictionary-based state with messages as a key.

        Returns:
            LangGraph-compatible state dictionary
        """
        langgraph_messages = []
        for msg in self.messages:
            lg_msg = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                lg_msg["name"] = msg.name
            if msg.function_call:
                lg_msg["function_call"] = msg.function_call
            langgraph_messages.append(lg_msg)

        state = {
            "messages": langgraph_messages,
            **self.context,  # Flatten context into state
        }

        logger.debug(
            "converted_to_langgraph",
            message_count=len(langgraph_messages),
            workflow_id=self.metadata.workflow_id,
        )

        return state

    def to_crewai_context(self) -> dict[str, Any]:
        """Convert to CrewAI context format.

        CrewAI uses a context dictionary passed to agents and tasks.

        Returns:
            CrewAI-compatible context dictionary
        """
        # Build conversation history as string for CrewAI
        conversation = []
        for msg in self.messages:
            prefix = f"{msg.role.value.upper()}"
            if msg.name:
                prefix += f" ({msg.name})"
            conversation.append(f"{prefix}: {msg.content}")

        context = {
            "conversation_history": "\n".join(conversation),
            "workflow_id": self.metadata.workflow_id,
            **self.context,  # Include all context data
        }

        logger.debug(
            "converted_to_crewai",
            message_count=len(self.messages),
            workflow_id=self.metadata.workflow_id,
        )

        return context

    def to_autogen_messages(self) -> list[dict[str, Any]]:
        """Convert to AutoGen message format.

        AutoGen uses a list of messages with role and content.

        Returns:
            List of AutoGen-compatible message dictionaries
        """
        autogen_messages = []
        for msg in self.messages:
            ag_msg = {
                "role": msg.role.value,
                "content": msg.content,
            }
            if msg.name:
                ag_msg["name"] = msg.name
            if msg.function_call:
                ag_msg["function_call"] = msg.function_call
            autogen_messages.append(ag_msg)

        logger.debug(
            "converted_to_autogen",
            message_count=len(autogen_messages),
            workflow_id=self.metadata.workflow_id,
        )

        return autogen_messages

    def to_llamaindex_chat_history(self) -> list[dict[str, str]]:
        """Convert to LlamaIndex chat history format.

        LlamaIndex uses a simplified message list with role and content.

        Returns:
            List of LlamaIndex-compatible chat messages
        """
        chat_history = []
        for msg in self.messages:
            # LlamaIndex primarily uses user/assistant roles
            role = msg.role.value
            if role == "function" or role == "tool":
                role = "assistant"  # Map function/tool to assistant

            chat_history.append(
                {
                    "role": role,
                    "content": msg.content,
                }
            )

        logger.debug(
            "converted_to_llamaindex",
            message_count=len(chat_history),
            workflow_id=self.metadata.workflow_id,
        )

        return chat_history

    @classmethod
    def from_langgraph_state(cls, state: dict[str, Any], workflow_id: str | None = None) -> "UnifiedWorkflowState":
        """Create unified state from LangGraph state.

        Args:
            state: LangGraph state dictionary
            workflow_id: Optional workflow ID (generates new if not provided)

        Returns:
            UnifiedWorkflowState instance
        """
        messages = []
        for msg_data in state.get("messages", []):
            messages.append(
                Message(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    name=msg_data.get("name"),
                    function_call=msg_data.get("function_call"),
                )
            )

        # Extract context (everything except messages)
        context = {k: v for k, v in state.items() if k != "messages"}

        metadata = StateMetadata(
            workflow_id=workflow_id or str(uuid.uuid4()),
            current_framework="langgraph",
        )

        return cls(messages=messages, context=context, metadata=metadata)

    @classmethod
    def from_crewai_context(cls, context: dict[str, Any], workflow_id: str | None = None) -> "UnifiedWorkflowState":
        """Create unified state from CrewAI context.

        Args:
            context: CrewAI context dictionary
            workflow_id: Optional workflow ID (generates new if not provided)

        Returns:
            UnifiedWorkflowState instance
        """
        messages = []

        # Parse conversation history if present
        if "conversation_history" in context:
            history = context["conversation_history"]
            for line in history.split("\n"):
                if ":" not in line:
                    continue
                prefix, content = line.split(":", 1)
                role_str = prefix.split("(")[0].strip().lower()
                try:
                    role = MessageRole(role_str)
                    messages.append(Message(role=role, content=content.strip()))
                except ValueError:
                    continue

        # Extract context (everything except conversation_history and workflow_id)
        state_context = {k: v for k, v in context.items() if k not in ("conversation_history", "workflow_id")}

        metadata = StateMetadata(
            workflow_id=context.get("workflow_id", workflow_id or str(uuid.uuid4())),
            current_framework="crewai",
        )

        return cls(messages=messages, context=state_context, metadata=metadata)

    @classmethod
    def from_autogen_messages(
        cls, messages: list[dict[str, Any]], workflow_id: str | None = None, context: dict[str, Any] | None = None
    ) -> "UnifiedWorkflowState":
        """Create unified state from AutoGen messages.

        Args:
            messages: List of AutoGen message dictionaries
            workflow_id: Optional workflow ID (generates new if not provided)
            context: Optional context data

        Returns:
            UnifiedWorkflowState instance
        """
        unified_messages = []
        for msg_data in messages:
            unified_messages.append(
                Message(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    name=msg_data.get("name"),
                    function_call=msg_data.get("function_call"),
                )
            )

        metadata = StateMetadata(
            workflow_id=workflow_id or str(uuid.uuid4()),
            current_framework="autogen",
        )

        return cls(
            messages=unified_messages,
            context=context or {},
            metadata=metadata,
        )

    @classmethod
    def from_llamaindex_chat_history(
        cls, chat_history: list[dict[str, str]], workflow_id: str | None = None, context: dict[str, Any] | None = None
    ) -> "UnifiedWorkflowState":
        """Create unified state from LlamaIndex chat history.

        Args:
            chat_history: List of LlamaIndex chat message dictionaries
            workflow_id: Optional workflow ID (generates new if not provided)
            context: Optional context data

        Returns:
            UnifiedWorkflowState instance
        """
        messages = []
        for msg_data in chat_history:
            messages.append(
                Message(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                )
            )

        metadata = StateMetadata(
            workflow_id=workflow_id or str(uuid.uuid4()),
            current_framework="llamaindex",
        )

        return cls(messages=messages, context=context or {}, metadata=metadata)

    def __repr__(self) -> str:
        """String representation of the state."""
        return (
            f"UnifiedWorkflowState("
            f"workflow_id={self.metadata.workflow_id!r}, "
            f"messages={len(self.messages)}, "
            f"context_keys={list(self.context.keys())}, "
            f"checkpoints={len(self.checkpoints)}, "
            f"framework={self.metadata.current_framework!r})"
        )
