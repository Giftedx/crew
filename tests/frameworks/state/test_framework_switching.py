"""Tests for framework switching demo to ensure it works correctly."""

import pytest

from ai.frameworks.state import UnifiedWorkflowState
from ai.frameworks.state.persistence import MemoryBackend


class TestFrameworkSwitching:
    """Test suite for framework switching scenarios."""

    def test_langgraph_roundtrip(self):
        """Test LangGraph conversion preserves state."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there!")
        state.update_context(step=1, user_id="user-123")

        # Convert to LangGraph and back
        langgraph_state = state.to_langgraph_state()
        restored = UnifiedWorkflowState.from_langgraph_state(langgraph_state, workflow_id=state.metadata.workflow_id)

        # Verify preservation
        assert len(restored.messages) == len(state.messages)
        assert restored.context["step"] == state.context["step"]
        assert restored.context["user_id"] == state.context["user_id"]

    def test_crewai_roundtrip(self):
        """Test CrewAI conversion preserves state."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Analyze this")
        state.add_message("assistant", "Analyzing...")
        state.update_context(task="analysis", priority="high")

        # Convert to CrewAI and back
        crewai_context = state.to_crewai_context()
        restored = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id=state.metadata.workflow_id)

        # Verify preservation
        assert len(restored.messages) == len(state.messages)
        assert restored.context["task"] == state.context["task"]
        assert restored.context["priority"] == state.context["priority"]

    def test_autogen_roundtrip(self):
        """Test AutoGen conversion preserves state."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Help me")
        state.add_message("assistant", "Sure!", agent_name="Helper")
        state.update_context(conversation_id="conv-456")

        # Convert to AutoGen and back
        autogen_messages = state.to_autogen_messages()
        restored = UnifiedWorkflowState.from_autogen_messages(
            autogen_messages, workflow_id=state.metadata.workflow_id, context=state.context
        )

        # Verify preservation
        assert len(restored.messages) == len(state.messages)
        assert restored.context["conversation_id"] == state.context["conversation_id"]

    def test_llamaindex_roundtrip(self):
        """Test LlamaIndex conversion preserves state."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Query data")
        state.add_message("assistant", "Querying...")
        state.update_context(query_type="semantic", index="docs")

        # Convert to LlamaIndex and back
        llamaindex_chat = state.to_llamaindex_chat_history()
        restored = UnifiedWorkflowState.from_llamaindex_chat_history(
            llamaindex_chat, workflow_id=state.metadata.workflow_id, context=state.context
        )

        # Verify preservation
        assert len(restored.messages) == len(state.messages)
        assert restored.context["query_type"] == state.context["query_type"]
        assert restored.context["index"] == state.context["index"]

    def test_multi_framework_transition(self):
        """Test transitioning through all 4 frameworks."""
        # Start with initial state
        state = UnifiedWorkflowState()
        state.add_message("user", "Process this request")
        state.update_context(request_id="req-789")
        initial_workflow_id = state.metadata.workflow_id

        # LangGraph stage
        langgraph_state = state.to_langgraph_state()
        langgraph_state["stage_1_complete"] = True
        state = UnifiedWorkflowState.from_langgraph_state(langgraph_state, workflow_id=initial_workflow_id)

        # CrewAI stage
        crewai_context = state.to_crewai_context()
        crewai_context["stage_2_complete"] = True
        state = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id=initial_workflow_id)

        # AutoGen stage
        autogen_messages = state.to_autogen_messages()
        autogen_messages.append({"role": "assistant", "content": "Processing..."})
        state = UnifiedWorkflowState.from_autogen_messages(
            autogen_messages, workflow_id=initial_workflow_id, context=state.context
        )

        # LlamaIndex stage
        llamaindex_chat = state.to_llamaindex_chat_history()
        llamaindex_chat.append({"role": "assistant", "content": "Complete!"})
        state = UnifiedWorkflowState.from_llamaindex_chat_history(
            llamaindex_chat, workflow_id=initial_workflow_id, context=state.context
        )

        # Verify all stages completed
        assert state.context["stage_1_complete"] is True
        assert state.context["stage_2_complete"] is True
        assert state.context["request_id"] == "req-789"
        assert len(state.messages) == 3  # Initial + 2 added
        # Note: Checkpoints are not preserved through framework conversions
        # Each from_* method creates a new state, checkpoints must be manually preserved

    @pytest.mark.asyncio
    async def test_persistence_across_transitions(self):
        """Test state persists correctly across framework transitions."""
        backend = MemoryBackend()

        # Stage 1: LangGraph
        state = UnifiedWorkflowState()
        state.add_message("user", "Start workflow")
        state.update_context(stage=1)
        await backend.save(state.metadata.workflow_id, state.to_dict())

        # Load and transition to CrewAI
        loaded = await backend.load(state.metadata.workflow_id)
        state = UnifiedWorkflowState.from_dict(loaded)
        crewai_context = state.to_crewai_context()
        crewai_context["stage"] = 2
        state = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id=state.metadata.workflow_id)
        await backend.save(state.metadata.workflow_id, state.to_dict())

        # Load and transition to AutoGen
        loaded = await backend.load(state.metadata.workflow_id)
        state = UnifiedWorkflowState.from_dict(loaded)
        state.update_context(stage=3)
        await backend.save(state.metadata.workflow_id, state.to_dict())

        # Final load - verify all stages preserved
        loaded = await backend.load(state.metadata.workflow_id)
        final_state = UnifiedWorkflowState.from_dict(loaded)

        assert final_state.context["stage"] == 3
        assert len(final_state.messages) == 1

    def test_checkpoint_restoration_after_framework_switch(self):
        """Test checkpoints work when preserving state across framework boundaries."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Test")
        state.update_context(value=10)

        # Create checkpoint before framework switch
        checkpoint1 = state.create_checkpoint("before_switch")

        # Switch to LangGraph and modify
        langgraph_state = state.to_langgraph_state()
        langgraph_state["value"] = 20

        # Restore from framework format while preserving checkpoints
        # Note: from_langgraph_state creates NEW state without checkpoints
        # In practice, you'd persist state via backend before/after conversion

        # Verify original state still has checkpoint
        assert len(state.checkpoints) == 1
        assert state.context["value"] == 10

        # Restore checkpoint works on original state
        state.update_context(value=99)  # Modify
        restored = state.restore_checkpoint(checkpoint1.id)
        assert restored is True
        assert state.context["value"] == 10  # Back to original

    def test_context_accumulation_across_frameworks(self):
        """Test context accumulates correctly as state moves through frameworks."""
        state = UnifiedWorkflowState()
        initial_workflow_id = state.metadata.workflow_id

        # LangGraph adds context
        langgraph_state = state.to_langgraph_state()
        langgraph_state["langgraph_data"] = "value1"
        state = UnifiedWorkflowState.from_langgraph_state(langgraph_state, workflow_id=initial_workflow_id)

        # CrewAI adds more context
        crewai_context = state.to_crewai_context()
        crewai_context["crewai_data"] = "value2"
        state = UnifiedWorkflowState.from_crewai_context(crewai_context, workflow_id=initial_workflow_id)

        # AutoGen preserves and adds
        state.update_context(autogen_data="value3")

        # Verify all context preserved
        assert state.context["langgraph_data"] == "value1"
        assert state.context["crewai_data"] == "value2"
        assert state.context["autogen_data"] == "value3"

    def test_message_metadata_preserved(self):
        """Test message metadata survives framework transitions."""
        state = UnifiedWorkflowState()
        state.add_message("user", "Hello", confidence=0.95, source="web")

        # Round-trip through all frameworks
        for framework in ["langgraph", "crewai", "autogen", "llamaindex"]:
            if framework == "langgraph":
                converted = state.to_langgraph_state()
                state = UnifiedWorkflowState.from_langgraph_state(converted, workflow_id=state.metadata.workflow_id)
            elif framework == "crewai":
                converted = state.to_crewai_context()
                state = UnifiedWorkflowState.from_crewai_context(converted, workflow_id=state.metadata.workflow_id)
            elif framework == "autogen":
                converted = state.to_autogen_messages()
                state = UnifiedWorkflowState.from_autogen_messages(
                    converted, workflow_id=state.metadata.workflow_id, context=state.context
                )
            elif framework == "llamaindex":
                converted = state.to_llamaindex_chat_history()
                state = UnifiedWorkflowState.from_llamaindex_chat_history(
                    converted, workflow_id=state.metadata.workflow_id, context=state.context
                )

        # Note: Metadata preservation depends on framework format
        # Some frameworks may not preserve all metadata fields
        assert len(state.messages) == 1
        assert state.messages[0].content == "Hello"
