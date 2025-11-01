"""Tests for UnifiedWorkflowState and state management protocols."""

from datetime import datetime

from ai.frameworks.state import (
    Checkpoint,
    Message,
    MessageRole,
    StateMetadata,
    UnifiedWorkflowState,
)


class TestMessage:
    """Tests for Message dataclass."""

    def test_message_creation(self):
        """Test creating a message with all fields."""
        msg = Message(
            role=MessageRole.USER,
            content="Hello, world!",
            name="test_user",
            function_call={"name": "test_func", "arguments": '{"arg": "value"}'},
            metadata={"key": "value"},
        )

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello, world!"
        assert msg.name == "test_user"
        assert msg.function_call["name"] == "test_func"
        assert msg.metadata["key"] == "value"
        assert isinstance(msg.timestamp, datetime)

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="Test response",
        )

        data = msg.to_dict()

        assert data["role"] == "assistant"
        assert data["content"] == "Test response"
        assert data["name"] is None
        assert data["function_call"] is None
        assert data["metadata"] == {}
        assert "timestamp" in data

    def test_message_from_dict(self):
        """Test message deserialization."""
        data = {
            "role": "system",
            "content": "You are a helpful assistant",
            "name": None,
            "function_call": None,
            "metadata": {},
            "timestamp": datetime.now().isoformat(),
        }

        msg = Message.from_dict(data)

        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant"
        assert isinstance(msg.timestamp, datetime)

    def test_message_roles(self):
        """Test all message role types."""
        roles = [
            MessageRole.SYSTEM,
            MessageRole.USER,
            MessageRole.ASSISTANT,
            MessageRole.FUNCTION,
            MessageRole.TOOL,
        ]

        for role in roles:
            msg = Message(role=role, content=f"Test {role.value}")
            assert msg.role == role
            assert msg.role.value in ["system", "user", "assistant", "function", "tool"]


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""

    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        state_snapshot = {
            "messages": [],
            "context": {"key": "value"},
            "metadata": {"workflow_id": "test-123"},
        }

        checkpoint = Checkpoint(
            id="cp-001",
            name="Initial State",
            state_snapshot=state_snapshot,
            framework="langgraph",
            metadata={"reason": "manual checkpoint"},
        )

        assert checkpoint.id == "cp-001"
        assert checkpoint.name == "Initial State"
        assert checkpoint.state_snapshot["context"]["key"] == "value"
        assert checkpoint.framework == "langgraph"
        assert checkpoint.metadata["reason"] == "manual checkpoint"
        assert isinstance(checkpoint.created_at, datetime)

    def test_checkpoint_to_dict(self):
        """Test checkpoint serialization."""
        checkpoint = Checkpoint(
            id="cp-002",
            name="Test Checkpoint",
            state_snapshot={"test": "data"},
        )

        data = checkpoint.to_dict()

        assert data["id"] == "cp-002"
        assert data["name"] == "Test Checkpoint"
        assert data["state_snapshot"] == {"test": "data"}
        assert "created_at" in data

    def test_checkpoint_from_dict(self):
        """Test checkpoint deserialization."""
        data = {
            "id": "cp-003",
            "name": "Restored Checkpoint",
            "state_snapshot": {"messages": []},
            "framework": "crewai",
            "created_at": datetime.now().isoformat(),
            "metadata": {},
        }

        checkpoint = Checkpoint.from_dict(data)

        assert checkpoint.id == "cp-003"
        assert checkpoint.name == "Restored Checkpoint"
        assert checkpoint.framework == "crewai"
        assert isinstance(checkpoint.created_at, datetime)


class TestStateMetadata:
    """Tests for StateMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating state metadata."""
        metadata = StateMetadata(
            workflow_id="wf-123",
            current_framework="langgraph",
            version="1.0.0",
            tags=["test", "demo"],
            custom={"priority": "high"},
        )

        assert metadata.workflow_id == "wf-123"
        assert metadata.current_framework == "langgraph"
        assert metadata.version == "1.0.0"
        assert "test" in metadata.tags
        assert metadata.custom["priority"] == "high"
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)

    def test_metadata_to_dict(self):
        """Test metadata serialization."""
        metadata = StateMetadata(workflow_id="wf-456")

        data = metadata.to_dict()

        assert data["workflow_id"] == "wf-456"
        assert data["version"] == "1.0.0"
        assert "created_at" in data
        assert "updated_at" in data

    def test_metadata_from_dict(self):
        """Test metadata deserialization."""
        data = {
            "workflow_id": "wf-789",
            "current_framework": "autogen",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "2.0.0",
            "tags": ["production"],
            "custom": {},
        }

        metadata = StateMetadata.from_dict(data)

        assert metadata.workflow_id == "wf-789"
        assert metadata.current_framework == "autogen"
        assert metadata.version == "2.0.0"
        assert isinstance(metadata.created_at, datetime)


class TestUnifiedWorkflowState:
    """Tests for UnifiedWorkflowState."""

    def test_state_creation(self):
        """Test creating an empty unified state."""
        state = UnifiedWorkflowState()

        assert len(state.messages) == 0
        assert len(state.context) == 0
        assert len(state.checkpoints) == 0
        assert state.metadata.workflow_id is not None
        assert state.metadata.version == "1.0.0"

    def test_add_message(self):
        """Test adding messages to state."""
        state = UnifiedWorkflowState()

        state.add_message(MessageRole.USER, "Hello!")
        state.add_message(MessageRole.ASSISTANT, "Hi there!", confidence=0.95)

        assert len(state.messages) == 2
        assert state.messages[0].role == MessageRole.USER
        assert state.messages[0].content == "Hello!"
        assert state.messages[1].metadata["confidence"] == 0.95

    def test_add_message_with_string_role(self):
        """Test adding message with string role."""
        state = UnifiedWorkflowState()

        state.add_message("user", "Test message")

        assert len(state.messages) == 1
        assert state.messages[0].role == MessageRole.USER

    def test_update_context(self):
        """Test updating workflow context."""
        state = UnifiedWorkflowState()

        state.update_context(task_id="task-123", priority="high")
        state.update_context(status="in_progress")

        assert state.context["task_id"] == "task-123"
        assert state.context["priority"] == "high"
        assert state.context["status"] == "in_progress"

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Test message")
        state.update_context(step=1)

        checkpoint = state.create_checkpoint("Before API call", reason="manual")

        assert len(state.checkpoints) == 1
        assert checkpoint.name == "Before API call"
        assert checkpoint.metadata["reason"] == "manual"
        assert len(checkpoint.state_snapshot["messages"]) == 1
        assert checkpoint.state_snapshot["context"]["step"] == 1

    def test_restore_checkpoint(self):
        """Test restoring from a checkpoint."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Message 1")
        state.update_context(step=1)

        checkpoint = state.create_checkpoint("Checkpoint 1")

        # Modify state after checkpoint
        state.add_message(MessageRole.ASSISTANT, "Message 2")
        state.update_context(step=2)

        assert len(state.messages) == 2
        assert state.context["step"] == 2

        # Restore checkpoint
        result = state.restore_checkpoint(checkpoint.id)

        assert result is True
        assert len(state.messages) == 1
        assert state.messages[0].content == "Message 1"
        assert state.context["step"] == 1

    def test_restore_nonexistent_checkpoint(self):
        """Test restoring from a nonexistent checkpoint."""
        state = UnifiedWorkflowState()

        result = state.restore_checkpoint("nonexistent-id")

        assert result is False

    def test_state_serialization(self):
        """Test state to_dict and from_dict."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Hello")
        state.update_context(key="value")
        state.create_checkpoint("Test")

        data = state.to_dict()

        assert len(data["messages"]) == 1
        assert data["context"]["key"] == "value"
        assert len(data["checkpoints"]) == 1
        assert "metadata" in data

        # Deserialize
        restored_state = UnifiedWorkflowState.from_dict(data)

        assert len(restored_state.messages) == 1
        assert restored_state.messages[0].content == "Hello"
        assert restored_state.context["key"] == "value"
        assert len(restored_state.checkpoints) == 1

    def test_to_langgraph_state(self):
        """Test conversion to LangGraph state format."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Hello")
        state.add_message(MessageRole.ASSISTANT, "Hi there")
        state.update_context(temperature=0.7, max_tokens=100)

        lg_state = state.to_langgraph_state()

        assert len(lg_state["messages"]) == 2
        assert lg_state["messages"][0]["role"] == "user"
        assert lg_state["messages"][0]["content"] == "Hello"
        assert lg_state["temperature"] == 0.7
        assert lg_state["max_tokens"] == 100

    def test_to_crewai_context(self):
        """Test conversion to CrewAI context format."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.SYSTEM, "You are helpful")
        state.add_message(MessageRole.USER, "Help me", name="john")
        state.update_context(task_id="task-123")

        crew_context = state.to_crewai_context()

        assert "conversation_history" in crew_context
        assert "SYSTEM: You are helpful" in crew_context["conversation_history"]
        assert "USER (john): Help me" in crew_context["conversation_history"]
        assert crew_context["task_id"] == "task-123"
        assert "workflow_id" in crew_context

    def test_to_autogen_messages(self):
        """Test conversion to AutoGen message format."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Test query")
        state.add_message(
            MessageRole.ASSISTANT,
            "Test response",
            function_call={"name": "test", "arguments": "{}"},
        )

        ag_messages = state.to_autogen_messages()

        assert len(ag_messages) == 2
        assert ag_messages[0]["role"] == "user"
        assert ag_messages[0]["content"] == "Test query"
        assert ag_messages[1]["function_call"]["name"] == "test"

    def test_to_llamaindex_chat_history(self):
        """Test conversion to LlamaIndex chat history format."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Question")
        state.add_message(MessageRole.ASSISTANT, "Answer")
        state.add_message(MessageRole.FUNCTION, "Function result")  # Should map to assistant

        li_history = state.to_llamaindex_chat_history()

        assert len(li_history) == 3
        assert li_history[0]["role"] == "user"
        assert li_history[1]["role"] == "assistant"
        assert li_history[2]["role"] == "assistant"  # Function mapped to assistant

    def test_from_langgraph_state(self):
        """Test creating unified state from LangGraph state."""
        lg_state = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
            "temperature": 0.8,
            "model": "gpt-4",
        }

        state = UnifiedWorkflowState.from_langgraph_state(lg_state, workflow_id="wf-lg-123")

        assert len(state.messages) == 2
        assert state.messages[0].role == MessageRole.USER
        assert state.context["temperature"] == 0.8
        assert state.context["model"] == "gpt-4"
        assert state.metadata.workflow_id == "wf-lg-123"
        assert state.metadata.current_framework == "langgraph"

    def test_from_crewai_context(self):
        """Test creating unified state from CrewAI context."""
        crew_context = {
            "conversation_history": "SYSTEM: Be helpful\nUSER: Help me\nASSISTANT: Sure!",
            "workflow_id": "wf-crew-456",
            "task_priority": "high",
        }

        state = UnifiedWorkflowState.from_crewai_context(crew_context)

        assert len(state.messages) == 3
        assert state.messages[0].role == MessageRole.SYSTEM
        assert state.messages[1].role == MessageRole.USER
        assert state.messages[2].role == MessageRole.ASSISTANT
        assert state.context["task_priority"] == "high"
        assert state.metadata.workflow_id == "wf-crew-456"
        assert state.metadata.current_framework == "crewai"

    def test_from_autogen_messages(self):
        """Test creating unified state from AutoGen messages."""
        ag_messages = [
            {"role": "user", "content": "Query"},
            {"role": "assistant", "content": "Response", "name": "assistant_1"},
        ]

        state = UnifiedWorkflowState.from_autogen_messages(
            ag_messages,
            workflow_id="wf-ag-789",
            context={"setting": "test"},
        )

        assert len(state.messages) == 2
        assert state.messages[1].name == "assistant_1"
        assert state.context["setting"] == "test"
        assert state.metadata.workflow_id == "wf-ag-789"
        assert state.metadata.current_framework == "autogen"

    def test_from_llamaindex_chat_history(self):
        """Test creating unified state from LlamaIndex chat history."""
        li_history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
        ]

        state = UnifiedWorkflowState.from_llamaindex_chat_history(
            li_history,
            workflow_id="wf-li-321",
            context={"index": "docs"},
        )

        assert len(state.messages) == 3
        assert state.messages[0].role == MessageRole.USER
        assert state.messages[1].role == MessageRole.ASSISTANT
        assert state.context["index"] == "docs"
        assert state.metadata.workflow_id == "wf-li-321"
        assert state.metadata.current_framework == "llamaindex"

    def test_state_repr(self):
        """Test state string representation."""
        state = UnifiedWorkflowState()
        state.add_message(MessageRole.USER, "Test")
        state.update_context(key="value")
        state.metadata.current_framework = "langgraph"

        repr_str = repr(state)

        assert "UnifiedWorkflowState" in repr_str
        assert "messages=1" in repr_str
        assert "checkpoints=0" in repr_str
        assert "langgraph" in repr_str

    def test_framework_conversion_roundtrip_langgraph(self):
        """Test LangGraph conversion roundtrip."""
        original = UnifiedWorkflowState()
        original.add_message(MessageRole.USER, "Test")
        original.update_context(param="value")

        lg_state = original.to_langgraph_state()
        restored = UnifiedWorkflowState.from_langgraph_state(lg_state)

        assert len(restored.messages) == 1
        assert restored.messages[0].content == "Test"
        assert restored.context["param"] == "value"

    def test_framework_conversion_roundtrip_autogen(self):
        """Test AutoGen conversion roundtrip."""
        original = UnifiedWorkflowState()
        original.add_message(MessageRole.USER, "Query")
        original.add_message(MessageRole.ASSISTANT, "Response")

        ag_messages = original.to_autogen_messages()
        restored = UnifiedWorkflowState.from_autogen_messages(ag_messages, context=original.context)

        assert len(restored.messages) == 2
        assert restored.messages[0].content == "Query"
        assert restored.messages[1].content == "Response"
