"""Tests for Memory V2 Tool."""

from unittest.mock import AsyncMock, Mock, patch

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.memory_v2_tool import MemoryV2Tool


class TestMemoryV2Tool:
    """Test suite for MemoryV2Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = MemoryV2Tool()

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_memory_namespace")
    def test_upsert_operation_success(self, mock_namespace, mock_memory_factory):
        """Test successful upsert operation."""
        # Setup mocks
        mock_memory = AsyncMock()
        mock_memory.upsert.return_value = StepResult.ok(upserted=1, namespace="test:main:default")
        mock_memory_factory.return_value = mock_memory
        mock_namespace.return_value = Mock()

        result = self.tool._run(
            operation="upsert",
            content="test content",
            metadata={"type": "test"},
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert result_obj.data["upserted"] == 1

    def test_upsert_operation_missing_content(self):
        """Test upsert operation with missing content."""
        result = self.tool._run(
            operation="upsert",
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert "Content required for upsert operation" in result_obj.error

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_memory_namespace")
    def test_query_operation_success(self, mock_namespace, mock_memory_factory):
        """Test successful query operation."""
        # Setup mocks
        mock_memory = AsyncMock()
        mock_memory.query.return_value = StepResult.ok(
            results=[{"content": "result1", "score": 0.9}],
            namespace="test:main:default",
            count=1,
        )
        mock_memory_factory.return_value = mock_memory
        mock_namespace.return_value = Mock()

        result = self.tool._run(
            operation="query",
            vector=[0.1, 0.2, 0.3],
            top_k=5,
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert len(result_obj.data["results"]) == 1
        assert result_obj.data["results"][0]["content"] == "result1"

    def test_query_operation_missing_vector(self):
        """Test query operation with missing vector."""
        result = self.tool._run(
            operation="query",
            top_k=5,
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert "Vector required for query operation" in result_obj.error

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    def test_delete_operation_not_supported(self, mock_memory_factory):
        """Test delete operation (not supported)."""
        result = self.tool._run(
            operation="delete",
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert "Delete operation not supported" in result_obj.error

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_memory_namespace")
    def test_get_stats_operation(self, mock_namespace, mock_memory_factory):
        """Test get_stats operation."""
        # Setup mocks
        mock_memory = AsyncMock()
        mock_memory.get_stats.return_value = {"total_records": 100, "namespaces": 5}
        mock_memory_factory.return_value = mock_memory
        mock_namespace.return_value = Mock()

        result = self.tool._run(
            operation="get_stats",
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert result_obj.data["total_records"] == 100
        assert result_obj.data["namespaces"] == 5

    def test_unknown_operation(self):
        """Test unknown operation."""
        result = self.tool._run(
            operation="unknown",
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert "Unknown operation: unknown" in result_obj.error

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    def test_memory_exception_handling(self, mock_memory_factory):
        """Test exception handling during memory operations."""
        # Setup mocks to raise exception
        mock_memory_factory.side_effect = Exception("Memory connection failed")

        result = self.tool._run(
            operation="upsert",
            content="test content",
            creator="test_creator",
            tenant="test_tenant",
            workspace="test_workspace",
        )

        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert "Memory operation failed" in result_obj.error

    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_unified_memory")
    @patch("ultimate_discord_intelligence_bot.tools.memory_v2_tool.get_memory_namespace")
    def test_default_creator_handling(self, mock_namespace, mock_memory_factory):
        """Test default creator handling when not provided."""
        # Setup mocks
        mock_memory = AsyncMock()
        mock_memory.upsert.return_value = StepResult.ok(upserted=1, namespace="test:main:default")
        mock_memory_factory.return_value = mock_memory
        mock_namespace.return_value = Mock()

        result = self.tool._run(
            operation="upsert",
            content="test content",
            tenant="test_tenant",
            workspace="test_workspace",
            # No creator provided, should default to "default"
        )

        result_obj = StepResult.from_json(result)
        assert result_obj.success

        # Verify that the memory.upsert was called with "default" as creator
        mock_memory.upsert.assert_called_once()
        call_args = mock_memory.upsert.call_args
        assert call_args[0][2] == "default"  # creator argument
