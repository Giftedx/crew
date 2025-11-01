"""State management protocols for framework-agnostic workflow state.

This module defines the core data structures and protocols for managing workflow
state that can be converted between different AI frameworks (CrewAI, LangGraph,
AutoGen, LlamaIndex).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class Message:
    """Universal message format compatible with all frameworks.

    Attributes:
        role: The role of the message sender (system, user, assistant, function, tool)
        content: The text content of the message
        name: Optional name of the function/tool that generated this message
        function_call: Optional function call data for assistant messages
        metadata: Additional framework-specific metadata
        timestamp: When the message was created
    """

    role: MessageRole
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "role": self.role.value,
            "content": self.content,
            "name": self.name,
            "function_call": self.function_call,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            name=data.get("name"),
            function_call=data.get("function_call"),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class Checkpoint:
    """Workflow checkpoint for state recovery.

    Attributes:
        id: Unique identifier for this checkpoint
        name: Human-readable name for the checkpoint
        state_snapshot: Serialized state at this point
        framework: Framework that was active at this checkpoint
        created_at: When this checkpoint was created
        metadata: Additional checkpoint metadata
    """

    id: str
    name: str
    state_snapshot: dict[str, Any]
    framework: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "state_snapshot": self.state_snapshot,
            "framework": self.framework,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Create checkpoint from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            state_snapshot=data["state_snapshot"],
            framework=data.get("framework"),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StateMetadata:
    """Metadata about the workflow state.

    Attributes:
        workflow_id: Unique identifier for the workflow
        current_framework: Currently active framework
        created_at: When the state was created
        updated_at: When the state was last updated
        version: State schema version
        tags: Tags for categorizing/searching states
        custom: Additional custom metadata
    """

    workflow_id: str
    current_framework: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "current_framework": self.current_framework,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": self.tags,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateMetadata":
        """Create metadata from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            current_framework=data.get("current_framework"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            custom=data.get("custom", {}),
        )


@runtime_checkable
class StatePersistence(Protocol):
    """Protocol for state persistence backends."""

    async def save(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Save state to persistent storage.

        Args:
            workflow_id: Unique identifier for the workflow
            state: Serialized state dictionary
        """
        ...

    async def load(self, workflow_id: str) -> dict[str, Any] | None:
        """Load state from persistent storage.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Serialized state dictionary or None if not found
        """
        ...

    async def delete(self, workflow_id: str) -> bool:
        """Delete state from persistent storage.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            True if deleted, False if not found
        """
        ...

    async def list_workflows(self) -> list[str]:
        """List all workflow IDs in storage.

        Returns:
            List of workflow IDs
        """
        ...


@runtime_checkable
class StateConverter(Protocol):
    """Protocol for converting state between frameworks."""

    def to_framework_state(self, unified_state: Any) -> Any:
        """Convert unified state to framework-specific format.

        Args:
            unified_state: UnifiedWorkflowState instance

        Returns:
            Framework-specific state object
        """
        ...

    def from_framework_state(self, framework_state: Any) -> Any:
        """Convert framework-specific state to unified format.

        Args:
            framework_state: Framework-specific state object

        Returns:
            UnifiedWorkflowState instance
        """
        ...
