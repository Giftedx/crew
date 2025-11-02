"""Comprehensive tests for Mem0MemoryTool covering 60%+ of the codebase."""

from __future__ import annotations

from platform.core.step_result import StepResult
from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.memory.mem0_memory_tool import Mem0MemorySchema, Mem0MemoryTool


@pytest.fixture
def mock_mem0_service():
    """Create a mock Mem0MemoryService for testing."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.mem0_memory_tool.Mem0MemoryService") as mock_service:
        service_instance = Mock()
        mock_service.return_value = service_instance
        service_instance.remember.return_value = StepResult.ok(memory_id="mem_123", content="stored")
        service_instance.recall.return_value = StepResult.ok(memories=[{"id": "mem_123", "content": "recalled"}])
        service_instance.update_memory.return_value = StepResult.ok(memory_id="mem_123", content="updated")
        service_instance.delete_memory.return_value = StepResult.ok(deleted=True)
        service_instance.get_all_memories.return_value = StepResult.ok(memories=["mem1", "mem2"])
        service_instance.get_memory_history.return_value = StepResult.ok(history=[{"action": "created"}])
        yield service_instance


@pytest.fixture
def mock_metrics():
    """Create a mock metrics instance."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.mem0_memory_tool.get_metrics") as mock_get_metrics:
        metrics_instance = Mock()
        mock_get_metrics.return_value = metrics_instance
        metrics_instance.counter.return_value = Mock()
        metrics_instance.histogram.return_value = Mock()
        yield metrics_instance


class TestMem0MemorySchema:
    """Test suite for Mem0MemorySchema validation."""

    def test_schema_valid_remember_action(self):
        """Test schema validation for remember action."""
        schema = Mem0MemorySchema(action="remember", content="This is a test memory")
        assert schema.action == "remember"
        assert schema.content == "This is a test memory"
        assert schema.limit == 10

    def test_schema_valid_recall_action(self):
        """Test schema validation for recall action."""
        schema = Mem0MemorySchema(action="recall", query="search term", limit=5)
        assert schema.action == "recall"
        assert schema.query == "search term"
        assert schema.limit == 5

    def test_schema_valid_update_action(self):
        """Test schema validation for update action."""
        schema = Mem0MemorySchema(action="update", memory_id="mem_123", content="updated content")
        assert schema.action == "update"
        assert schema.memory_id == "mem_123"
        assert schema.content == "updated content"

    def test_schema_valid_delete_action(self):
        """Test schema validation for delete action."""
        schema = Mem0MemorySchema(action="delete", memory_id="mem_456")
        assert schema.action == "delete"
        assert schema.memory_id == "mem_456"

    def test_schema_valid_list_action(self):
        """Test schema validation for list action."""
        schema = Mem0MemorySchema(action="list")
        assert schema.action == "list"

    def test_schema_valid_history_action(self):
        """Test schema validation for history action."""
        schema = Mem0MemorySchema(action="history", memory_id="mem_789")
        assert schema.action == "history"
        assert schema.memory_id == "mem_789"

    def test_schema_default_limit(self):
        """Test default limit value."""
        schema = Mem0MemorySchema(action="list")
        assert schema.limit == 10


class TestMem0MemoryTool:
    """Test suite for Mem0MemoryTool operations."""

    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = Mem0MemoryTool()
        assert tool.name == "mem0_memory_tool"
        assert "persistent user preferences" in tool.description.lower()
        assert tool.args_schema == Mem0MemorySchema

    def test_remember_success(self, mock_mem0_service, mock_metrics):
        """Test successful remember operation."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="remember", tenant="test_tenant", workspace="test_workspace", content="User prefers dark mode"
        )
        assert result.success
        assert result.data["memory_id"] == "mem_123"
        mock_mem0_service.remember.assert_called_once()
        call_args = mock_mem0_service.remember.call_args
        assert call_args[0][0] == "User prefers dark mode"
        assert call_args[0][1] == "test_tenant:test_workspace"
        assert call_args[0][2]["tenant"] == "test_tenant"
        assert call_args[0][2]["workspace"] == "test_workspace"
        mock_metrics.counter.assert_called()
        mock_metrics.histogram.assert_called()

    def test_remember_missing_content(self, mock_mem0_service, mock_metrics):
        """Test remember operation fails without content."""
        tool = Mem0MemoryTool()
        result = tool._run(action="remember", tenant="test_tenant", workspace="test_workspace", content=None)
        assert not result.success
        assert "Content must be provided" in result.error
        mock_mem0_service.remember.assert_not_called()

    def test_recall_success(self, mock_mem0_service, mock_metrics):
        """Test successful recall operation."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="recall", tenant="test_tenant", workspace="test_workspace", query="dark mode preferences", limit=5
        )
        assert result.success
        assert len(result.data["memories"]) == 1
        mock_mem0_service.recall.assert_called_once()
        call_args = mock_mem0_service.recall.call_args
        assert call_args[0][0] == "dark mode preferences"
        assert call_args[0][1] == "test_tenant:test_workspace"
        assert call_args[1]["limit"] == 5

    def test_recall_missing_query(self, mock_mem0_service, mock_metrics):
        """Test recall operation fails without query."""
        tool = Mem0MemoryTool()
        result = tool._run(action="recall", tenant="test_tenant", workspace="test_workspace", query=None)
        assert not result.success
        assert "query must be provided" in result.error
        mock_mem0_service.recall.assert_not_called()

    def test_recall_default_limit(self, mock_mem0_service, mock_metrics):
        """Test recall uses default limit when not specified."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="recall", tenant="test_tenant", workspace="test_workspace", query="test query", limit=None
        )
        assert result.success
        call_args = mock_mem0_service.recall.call_args
        assert call_args[1]["limit"] == 10

    def test_update_success(self, mock_mem0_service, mock_metrics):
        """Test successful update operation."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="update",
            tenant="test_tenant",
            workspace="test_workspace",
            memory_id="mem_123",
            content="Updated preference: light mode",
        )
        assert result.success
        mock_mem0_service.update_memory.assert_called_once()
        call_args = mock_mem0_service.update_memory.call_args
        assert call_args[0][0] == "mem_123"
        assert call_args[0][1] == "Updated preference: light mode"
        assert call_args[0][2] == "test_tenant:test_workspace"

    def test_update_missing_memory_id(self, mock_mem0_service, mock_metrics):
        """Test update operation fails without memory_id."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="update", tenant="test_tenant", workspace="test_workspace", memory_id=None, content="updated content"
        )
        assert not result.success
        assert "memory_id and content must be provided" in result.error
        mock_mem0_service.update_memory.assert_not_called()

    def test_update_missing_content(self, mock_mem0_service, mock_metrics):
        """Test update operation fails without content."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="update", tenant="test_tenant", workspace="test_workspace", memory_id="mem_123", content=None
        )
        assert not result.success
        assert "memory_id and content must be provided" in result.error
        mock_mem0_service.update_memory.assert_not_called()

    def test_delete_success(self, mock_mem0_service, mock_metrics):
        """Test successful delete operation."""
        tool = Mem0MemoryTool()
        result = tool._run(action="delete", tenant="test_tenant", workspace="test_workspace", memory_id="mem_123")
        assert result.success
        mock_mem0_service.delete_memory.assert_called_once()
        call_args = mock_mem0_service.delete_memory.call_args
        assert call_args[0][0] == "mem_123"
        assert call_args[0][1] == "test_tenant:test_workspace"

    def test_delete_missing_memory_id(self, mock_mem0_service, mock_metrics):
        """Test delete operation fails without memory_id."""
        tool = Mem0MemoryTool()
        result = tool._run(action="delete", tenant="test_tenant", workspace="test_workspace", memory_id=None)
        assert not result.success
        assert "memory_id must be provided" in result.error
        mock_mem0_service.delete_memory.assert_not_called()

    def test_list_success(self, mock_mem0_service, mock_metrics):
        """Test successful list operation."""
        tool = Mem0MemoryTool()
        result = tool._run(action="list", tenant="test_tenant", workspace="test_workspace")
        assert result.success
        assert result.data["memories"] == ["mem1", "mem2"]
        mock_mem0_service.get_all_memories.assert_called_once()
        call_args = mock_mem0_service.get_all_memories.call_args
        assert call_args[0][0] == "test_tenant:test_workspace"

    def test_history_success(self, mock_mem0_service, mock_metrics):
        """Test successful history operation."""
        tool = Mem0MemoryTool()
        result = tool._run(action="history", tenant="test_tenant", workspace="test_workspace", memory_id="mem_123")
        assert result.success
        assert len(result.data["history"]) == 1
        mock_mem0_service.get_memory_history.assert_called_once()
        call_args = mock_mem0_service.get_memory_history.call_args
        assert call_args[0][0] == "mem_123"
        assert call_args[0][1] == "test_tenant:test_workspace"

    def test_history_missing_memory_id(self, mock_mem0_service, mock_metrics):
        """Test history operation fails without memory_id."""
        tool = Mem0MemoryTool()
        result = tool._run(action="history", tenant="test_tenant", workspace="test_workspace", memory_id=None)
        assert not result.success
        assert "memory_id must be provided" in result.error
        mock_mem0_service.get_memory_history.assert_not_called()

    def test_unknown_action(self, mock_mem0_service, mock_metrics):
        """Test handling of unknown action."""
        tool = Mem0MemoryTool()
        result = tool._run(action="invalid_action", tenant="test_tenant", workspace="test_workspace")
        assert not result.success
        assert "Unknown action" in result.error

    def test_exception_handling(self, mock_mem0_service, mock_metrics):
        """Test exception handling in tool operations."""
        mock_mem0_service.remember.side_effect = Exception("Service unavailable")
        tool = Mem0MemoryTool()
        result = tool._run(action="remember", tenant="test_tenant", workspace="test_workspace", content="test content")
        assert not result.success
        assert "Mem0 memory operation failed" in result.error
        assert "Service unavailable" in result.error
        mock_metrics.counter.assert_called()
        mock_metrics.histogram.assert_called()

    def test_service_failure_response(self, mock_mem0_service, mock_metrics):
        """Test handling of service failures returned as StepResult."""
        mock_mem0_service.remember.return_value = StepResult.fail("Database connection failed")
        tool = Mem0MemoryTool()
        result = tool._run(action="remember", tenant="test_tenant", workspace="test_workspace", content="test content")
        assert not result.success
        assert "Database connection failed" in result.error

    def test_tenant_workspace_formatting(self, mock_mem0_service, mock_metrics):
        """Test user_id formatting with tenant and workspace."""
        tool = Mem0MemoryTool()
        tool._run(action="remember", tenant="my_tenant", workspace="my_workspace", content="test")
        call_args = mock_mem0_service.remember.call_args
        user_id = call_args[0][1]
        assert user_id == "my_tenant:my_workspace"

    def test_metadata_includes_tenant_workspace(self, mock_mem0_service, mock_metrics):
        """Test metadata includes tenant and workspace information."""
        tool = Mem0MemoryTool()
        tool._run(action="remember", tenant="tenant_a", workspace="workspace_b", content="test content")
        call_args = mock_mem0_service.remember.call_args
        metadata = call_args[0][2]
        assert metadata["tenant"] == "tenant_a"
        assert metadata["workspace"] == "workspace_b"
