"""Comprehensive tests for MemoryStorageTool covering storage operations."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.memory.memory_storage_tool import (
    MemoryStorageSchema,
    MemoryStorageTool,
)


@pytest.fixture
def mock_qdrant_client():
    """Create a mock Qdrant client for testing."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.memory_storage_tool.get_qdrant_client") as mock_get:
        client_instance = Mock()
        mock_get.return_value = client_instance

        # Mock successful operations
        client_instance.upsert = Mock(return_value=Mock(status="completed"))
        client_instance.search = Mock(return_value=[Mock(id="vec_1", payload={"content": "test memory"}, score=0.95)])
        client_instance.retrieve = Mock(return_value=[Mock(id="vec_1", payload={"content": "retrieved memory"})])
        client_instance.delete = Mock(return_value=Mock(status="completed"))
        client_instance.scroll = Mock(return_value=([Mock(id="vec_1", payload={"content": "mem1"})], None))

        yield client_instance


@pytest.fixture
def mock_embedding_fn():
    """Create a mock embedding function."""
    return Mock(return_value=[0.1, 0.2, 0.3, 0.4])


@pytest.fixture
def mock_metrics():
    """Create a mock metrics instance."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.memory_storage_tool.get_metrics") as mock_get_metrics:
        metrics_instance = Mock()
        mock_get_metrics.return_value = metrics_instance
        metrics_instance.counter.return_value = Mock()
        metrics_instance.histogram.return_value = Mock()
        yield metrics_instance


class TestMemoryStorageSchema:
    """Test suite for MemoryStorageSchema validation."""

    def test_schema_valid_store_action(self):
        """Test schema validation for store action."""
        schema = MemoryStorageSchema(
            action="store",
            content="This is a memory to store",
        )
        assert schema.action == "store"
        assert schema.content == "This is a memory to store"

    def test_schema_valid_search_action(self):
        """Test schema validation for search action."""
        schema = MemoryStorageSchema(
            action="search",
            query="search term",
            limit=5,
        )
        assert schema.action == "search"
        assert schema.query == "search term"
        assert schema.limit == 5

    def test_schema_valid_retrieve_action(self):
        """Test schema validation for retrieve action."""
        schema = MemoryStorageSchema(
            action="retrieve",
            memory_id="vec_123",
        )
        assert schema.action == "retrieve"
        assert schema.memory_id == "vec_123"

    def test_schema_valid_delete_action(self):
        """Test schema validation for delete action."""
        schema = MemoryStorageSchema(
            action="delete",
            memory_id="vec_456",
        )
        assert schema.action == "delete"
        assert schema.memory_id == "vec_456"

    def test_schema_default_limit(self):
        """Test default limit value."""
        schema = MemoryStorageSchema(action="list")
        assert schema.limit == 10


class TestMemoryStorageTool:
    """Test suite for MemoryStorageTool operations."""

    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        embedding_fn = Mock()
        tool = MemoryStorageTool(embedding_fn=embedding_fn)
        assert tool.name == "memory_storage_tool"
        assert "vector store" in tool.description.lower()
        assert tool.args_schema == MemoryStorageSchema

    def test_store_success(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test successful store operation."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="store",
            tenant="test_tenant",
            workspace="test_workspace",
            content="User prefers Python over JavaScript",
        )

        assert result.success
        assert "memory_id" in result.data

        # Verify embedding function called
        mock_embedding_fn.assert_called_once_with("User prefers Python over JavaScript")

        # Verify Qdrant upsert called
        mock_qdrant_client.upsert.assert_called_once()

        # Verify metrics
        mock_metrics.counter.assert_called()
        mock_metrics.histogram.assert_called()

    def test_store_missing_content(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test store operation fails without content."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="store",
            tenant="test_tenant",
            workspace="test_workspace",
            content=None,
        )

        assert not result.success
        assert "Content must be provided" in result.error
        mock_embedding_fn.assert_not_called()
        mock_qdrant_client.upsert.assert_not_called()

    def test_search_success(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test successful search operation."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="search",
            tenant="test_tenant",
            workspace="test_workspace",
            query="Python preferences",
            limit=5,
        )

        assert result.success
        assert len(result.data["memories"]) == 1
        assert result.data["memories"][0]["content"] == "test memory"
        assert result.data["memories"][0]["score"] == 0.95

        # Verify embedding and search called
        mock_embedding_fn.assert_called_once_with("Python preferences")
        mock_qdrant_client.search.assert_called_once()

    def test_search_missing_query(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test search operation fails without query."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="search",
            tenant="test_tenant",
            workspace="test_workspace",
            query=None,
        )

        assert not result.success
        assert "Query must be provided" in result.error
        mock_embedding_fn.assert_not_called()
        mock_qdrant_client.search.assert_not_called()

    def test_retrieve_success(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test successful retrieve operation."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="retrieve",
            tenant="test_tenant",
            workspace="test_workspace",
            memory_id="vec_123",
        )

        assert result.success
        assert result.data["content"] == "retrieved memory"

        # Verify Qdrant retrieve called
        mock_qdrant_client.retrieve.assert_called_once()

    def test_retrieve_missing_memory_id(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test retrieve operation fails without memory_id."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="retrieve",
            tenant="test_tenant",
            workspace="test_workspace",
            memory_id=None,
        )

        assert not result.success
        assert "Memory ID must be provided" in result.error
        mock_qdrant_client.retrieve.assert_not_called()

    def test_delete_success(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test successful delete operation."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="delete",
            tenant="test_tenant",
            workspace="test_workspace",
            memory_id="vec_123",
        )

        assert result.success

        # Verify Qdrant delete called
        mock_qdrant_client.delete.assert_called_once()

    def test_delete_missing_memory_id(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test delete operation fails without memory_id."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="delete",
            tenant="test_tenant",
            workspace="test_workspace",
            memory_id=None,
        )

        assert not result.success
        assert "Memory ID must be provided" in result.error
        mock_qdrant_client.delete.assert_not_called()

    def test_list_success(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test successful list operation."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="list",
            tenant="test_tenant",
            workspace="test_workspace",
            limit=20,
        )

        assert result.success
        assert len(result.data["memories"]) == 1

        # Verify Qdrant scroll called
        mock_qdrant_client.scroll.assert_called_once()

    def test_unknown_action(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test handling of unknown action."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        result = tool._run(
            action="invalid_action",  # type: ignore
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert not result.success
        assert "Unknown action" in result.error

    def test_exception_handling(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test exception handling in tool operations."""
        mock_qdrant_client.upsert.side_effect = Exception("Vector store unavailable")

        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)
        result = tool._run(
            action="store",
            tenant="test_tenant",
            workspace="test_workspace",
            content="test content",
        )

        assert not result.success
        assert "Memory storage operation failed" in result.error
        assert "Vector store unavailable" in result.error

    def test_collection_name_formatting(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test collection name includes tenant and workspace."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        tool._run(
            action="store",
            tenant="tenant_a",
            workspace="workspace_b",
            content="test",
        )

        call_args = mock_qdrant_client.upsert.call_args
        collection_name = call_args[1]["collection_name"]
        assert "tenant_a" in collection_name
        assert "workspace_b" in collection_name

    def test_metadata_includes_tenant_workspace(self, mock_qdrant_client, mock_embedding_fn, mock_metrics):
        """Test stored payload includes tenant and workspace metadata."""
        tool = MemoryStorageTool(embedding_fn=mock_embedding_fn)

        tool._run(
            action="store",
            tenant="test_tenant",
            workspace="test_workspace",
            content="test content",
        )

        call_args = mock_qdrant_client.upsert.call_args
        points = call_args[1]["points"]
        payload = points[0].payload

        assert payload["tenant"] == "test_tenant"
        assert payload["workspace"] == "test_workspace"
        assert payload["content"] == "test content"
