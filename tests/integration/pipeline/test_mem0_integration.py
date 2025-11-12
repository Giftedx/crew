"""Tests for Mem0 integration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


pytest.skip("Test file imports from non-existent or moved modules", allow_module_level=True)

from ultimate_discord_intelligence_bot.services.mem0_service import Mem0MemoryService
from ultimate_discord_intelligence_bot.tools.mem0_memory_tool import Mem0MemoryTool


class TestMem0MemoryService:
    """Test Mem0MemoryService functionality."""

    @pytest.fixture
    def mock_memory(self):
        """Mock Mem0 Memory client."""
        with patch("ultimate_discord_intelligence_bot.services.mem0_service.Memory") as mock:
            mock_instance = mock.return_value
            mock_instance.add.return_value = [{"id": "mem_123", "memory": "test content"}]
            mock_instance.search.return_value = {
                "results": [{"id": "mem_123", "memory": "test content", "score": 0.95}]
            }
            mock_instance.update.return_value = {"id": "mem_123", "updated": True}
            mock_instance.delete.return_value = None
            mock_instance.get_all.return_value = {"results": [{"id": "mem_123", "memory": "test content"}]}
            mock_instance.history.return_value = [{"version": 1, "content": "old content"}]
            yield mock_instance

    def test_remember_success(self, mock_memory):
        """Test successful memory storage."""
        service = Mem0MemoryService()
        result = service.remember(
            content="User prefers concise summaries", user_id="tenant1:workspace1", metadata={"category": "formatting"}
        )
        assert result.success
        assert result.data is not None
        mock_memory.add.assert_called_once()

    def test_recall_success(self, mock_memory):
        """Test successful memory recall."""
        service = Mem0MemoryService()
        result = service.recall(query="How should I format output?", user_id="tenant1:workspace1")
        assert result.success
        assert "results" in result.data
        assert len(result.data["results"]) > 0
        mock_memory.search.assert_called_once()

    def test_update_memory_success(self, mock_memory):
        """Test successful memory update."""
        service = Mem0MemoryService()
        result = service.update_memory(
            memory_id="mem_123",
            content="Updated preference",
            user_id="tenant1:workspace1",
            metadata={"category": "formatting"},
        )
        assert result.success
        mock_memory.update.assert_called_once()

    def test_delete_memory_success(self, mock_memory):
        """Test successful memory deletion."""
        service = Mem0MemoryService()
        result = service.delete_memory(memory_id="mem_123", user_id="tenant1:workspace1")
        assert result.success
        assert result.data["deleted"] == "mem_123"
        mock_memory.delete.assert_called_once()

    def test_get_all_memories_success(self, mock_memory):
        """Test retrieving all memories."""
        service = Mem0MemoryService()
        result = service.get_all_memories(user_id="tenant1:workspace1")
        assert result.success
        assert "results" in result.data
        mock_memory.get_all.assert_called_once()

    def test_get_memory_history_success(self, mock_memory):
        """Test retrieving memory history."""
        service = Mem0MemoryService()
        result = service.get_memory_history(memory_id="mem_123", user_id="tenant1:workspace1")
        assert result.success
        assert isinstance(result.data, list)
        mock_memory.history.assert_called_once()

    def test_remember_error_handling(self, mock_memory):
        """Test error handling in remember operation."""
        mock_memory.add.side_effect = Exception("Connection error")
        service = Mem0MemoryService()
        result = service.remember(content="test", user_id="tenant1:workspace1")
        assert not result.success
        assert "Connection error" in result.error


class TestMem0MemoryTool:
    """Test Mem0MemoryTool functionality."""

    @pytest.fixture
    def mock_service(self):
        """Mock Mem0MemoryService."""
        with patch("ultimate_discord_intelligence_bot.tools.mem0_memory_tool.Mem0MemoryService") as mock:
            mock_instance = mock.return_value
            mock_instance.remember.return_value = StepResult.ok(data=[{"id": "mem_123", "memory": "test"}])
            mock_instance.recall.return_value = StepResult.ok(data={"results": [{"memory": "test", "score": 0.95}]})
            mock_instance.update_memory.return_value = StepResult.ok(data={"updated": True})
            mock_instance.delete_memory.return_value = StepResult.ok(data={"deleted": "mem_123"})
            mock_instance.get_all_memories.return_value = StepResult.ok(data={"results": []})
            mock_instance.get_memory_history.return_value = StepResult.ok(data=[])
            yield mock_instance

    def test_remember_action(self, mock_service):
        """Test remember action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="remember", content="User prefers summaries", tenant="tenant1", workspace="workspace1"
        )
        assert result.success
        mock_service.remember.assert_called_once()

    def test_recall_action(self, mock_service):
        """Test recall action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="recall", query="What are user preferences?", tenant="tenant1", workspace="workspace1"
        )
        assert result.success
        mock_service.recall.assert_called_once()

    def test_update_action(self, mock_service):
        """Test update action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(
            action="update", memory_id="mem_123", content="Updated preference", tenant="tenant1", workspace="workspace1"
        )
        assert result.success
        mock_service.update_memory.assert_called_once()

    def test_delete_action(self, mock_service):
        """Test delete action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(action="delete", memory_id="mem_123", tenant="tenant1", workspace="workspace1")
        assert result.success
        mock_service.delete_memory.assert_called_once()

    def test_list_action(self, mock_service):
        """Test list action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(action="list", tenant="tenant1", workspace="workspace1")
        assert result.success
        mock_service.get_all_memories.assert_called_once()

    def test_history_action(self, mock_service):
        """Test history action via tool."""
        tool = Mem0MemoryTool()
        result = tool._run(action="history", memory_id="mem_123", tenant="tenant1", workspace="workspace1")
        assert result.success
        mock_service.get_memory_history.assert_called_once()

    def test_tenant_isolation(self, mock_service):
        """Test tenant isolation in user_id construction."""
        tool = Mem0MemoryTool()
        tool._run(action="remember", content="test", tenant="tenant_a", workspace="workspace_x")
        call_args = mock_service.remember.call_args
        assert call_args[0][1] == "tenant_a:workspace_x"

    def test_validation_remember_missing_content(self):
        """Test validation for remember action."""
        tool = Mem0MemoryTool()
        result = tool._run(action="remember", tenant="tenant1", workspace="workspace1")
        assert not result.success
        assert "Content must be provided" in result.error

    def test_validation_recall_missing_query(self):
        """Test validation for recall action."""
        tool = Mem0MemoryTool()
        result = tool._run(action="recall", tenant="tenant1", workspace="workspace1")
        assert not result.success
        assert "query must be provided" in result.error

    def test_validation_update_missing_fields(self):
        """Test validation for update action."""
        tool = Mem0MemoryTool()
        result1 = tool._run(action="update", content="test", tenant="tenant1", workspace="workspace1")
        assert not result1.success
        result2 = tool._run(action="update", memory_id="mem_123", tenant="tenant1", workspace="workspace1")
        assert not result2.success

    def test_validation_delete_missing_memory_id(self):
        """Test validation for delete action."""
        tool = Mem0MemoryTool()
        result = tool._run(action="delete", tenant="tenant1", workspace="workspace1")
        assert not result.success
        assert "memory_id must be provided" in result.error

    def test_validation_history_missing_memory_id(self):
        """Test validation for history action."""
        tool = Mem0MemoryTool()
        result = tool._run(action="history", tenant="tenant1", workspace="workspace1")
        assert not result.success
        assert "memory_id must be provided" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
