"""Comprehensive tests for GraphMemoryTool covering knowledge graph operations."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ultimate_discord_intelligence_bot.tools.memory.graph_memory_tool import (
    GraphMemorySchema,
    GraphMemoryTool,
)


@pytest.fixture
def mock_graph_service():
    """Create a mock graph service for testing."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.graph_memory_tool.GraphMemoryService") as mock_class:
        service_instance = Mock()
        mock_class.return_value = service_instance

        # Mock successful operations
        service_instance.add_entity = Mock(return_value={"entity_id": "ent_123", "status": "created"})
        service_instance.add_relation = Mock(return_value={"relation_id": "rel_456", "status": "created"})
        service_instance.query_graph = Mock(
            return_value={
                "entities": [{"id": "ent_123", "name": "Python", "type": "language"}],
                "relations": [{"source": "ent_123", "target": "ent_456", "type": "uses"}],
            }
        )
        service_instance.get_entity = Mock(return_value={"id": "ent_123", "name": "Python", "type": "language"})
        service_instance.delete_entity = Mock(return_value={"status": "deleted"})
        service_instance.update_entity = Mock(return_value={"entity_id": "ent_123", "status": "updated"})

        yield service_instance


@pytest.fixture
def mock_metrics():
    """Create a mock metrics instance."""
    with patch("ultimate_discord_intelligence_bot.tools.memory.graph_memory_tool.get_metrics") as mock_get_metrics:
        metrics_instance = Mock()
        mock_get_metrics.return_value = metrics_instance
        metrics_instance.counter.return_value = Mock()
        metrics_instance.histogram.return_value = Mock()
        yield metrics_instance


class TestGraphMemorySchema:
    """Test suite for GraphMemorySchema validation."""

    def test_schema_valid_add_entity_action(self):
        """Test schema validation for add_entity action."""
        schema = GraphMemorySchema(
            action="add_entity",
            entity_name="Python",
            entity_type="language",
        )
        assert schema.action == "add_entity"
        assert schema.entity_name == "Python"
        assert schema.entity_type == "language"

    def test_schema_valid_add_relation_action(self):
        """Test schema validation for add_relation action."""
        schema = GraphMemorySchema(
            action="add_relation",
            source_entity="ent_123",
            target_entity="ent_456",
            relation_type="uses",
        )
        assert schema.action == "add_relation"
        assert schema.source_entity == "ent_123"
        assert schema.target_entity == "ent_456"
        assert schema.relation_type == "uses"

    def test_schema_valid_query_action(self):
        """Test schema validation for query action."""
        schema = GraphMemorySchema(
            action="query",
            query="MATCH (n:language) RETURN n",
        )
        assert schema.action == "query"
        assert schema.query == "MATCH (n:language) RETURN n"

    def test_schema_valid_get_entity_action(self):
        """Test schema validation for get_entity action."""
        schema = GraphMemorySchema(
            action="get_entity",
            entity_id="ent_123",
        )
        assert schema.action == "get_entity"
        assert schema.entity_id == "ent_123"

    def test_schema_valid_delete_entity_action(self):
        """Test schema validation for delete_entity action."""
        schema = GraphMemorySchema(
            action="delete_entity",
            entity_id="ent_123",
        )
        assert schema.action == "delete_entity"
        assert schema.entity_id == "ent_123"

    def test_schema_valid_update_entity_action(self):
        """Test schema validation for update_entity action."""
        schema = GraphMemorySchema(
            action="update_entity",
            entity_id="ent_123",
            entity_name="Python 3.12",
        )
        assert schema.action == "update_entity"
        assert schema.entity_id == "ent_123"
        assert schema.entity_name == "Python 3.12"


class TestGraphMemoryTool:
    """Test suite for GraphMemoryTool operations."""

    def test_tool_metadata(self):
        """Test tool has correct metadata."""
        tool = GraphMemoryTool()
        assert tool.name == "graph_memory_tool"
        assert "knowledge graph" in tool.description.lower()
        assert tool.args_schema == GraphMemorySchema

    def test_add_entity_success(self, mock_graph_service, mock_metrics):
        """Test successful add_entity operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name="Python",
            entity_type="language",
            properties={"version": "3.12"},
        )

        assert result.success
        assert result.data["entity_id"] == "ent_123"
        assert result.data["status"] == "created"

        # Verify service called correctly
        mock_graph_service.add_entity.assert_called_once_with(
            entity_name="Python",
            entity_type="language",
            properties={"version": "3.12"},
            tenant="test_tenant",
            workspace="test_workspace",
        )

        # Verify metrics
        mock_metrics.counter.assert_called()
        mock_metrics.histogram.assert_called()

    def test_add_entity_missing_name(self, mock_graph_service, mock_metrics):
        """Test add_entity fails without entity_name."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name=None,
            entity_type="language",
        )

        assert not result.success
        assert "Entity name must be provided" in result.error
        mock_graph_service.add_entity.assert_not_called()

    def test_add_entity_missing_type(self, mock_graph_service, mock_metrics):
        """Test add_entity fails without entity_type."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name="Python",
            entity_type=None,
        )

        assert not result.success
        assert "Entity type must be provided" in result.error
        mock_graph_service.add_entity.assert_not_called()

    def test_add_relation_success(self, mock_graph_service, mock_metrics):
        """Test successful add_relation operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_relation",
            tenant="test_tenant",
            workspace="test_workspace",
            source_entity="ent_123",
            target_entity="ent_456",
            relation_type="uses",
            properties={"frequency": "high"},
        )

        assert result.success
        assert result.data["relation_id"] == "rel_456"
        assert result.data["status"] == "created"

        # Verify service called correctly
        mock_graph_service.add_relation.assert_called_once_with(
            source_entity="ent_123",
            target_entity="ent_456",
            relation_type="uses",
            properties={"frequency": "high"},
            tenant="test_tenant",
            workspace="test_workspace",
        )

    def test_add_relation_missing_source(self, mock_graph_service, mock_metrics):
        """Test add_relation fails without source_entity."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_relation",
            tenant="test_tenant",
            workspace="test_workspace",
            source_entity=None,
            target_entity="ent_456",
            relation_type="uses",
        )

        assert not result.success
        assert "Source entity must be provided" in result.error
        mock_graph_service.add_relation.assert_not_called()

    def test_add_relation_missing_target(self, mock_graph_service, mock_metrics):
        """Test add_relation fails without target_entity."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_relation",
            tenant="test_tenant",
            workspace="test_workspace",
            source_entity="ent_123",
            target_entity=None,
            relation_type="uses",
        )

        assert not result.success
        assert "Target entity must be provided" in result.error
        mock_graph_service.add_relation.assert_not_called()

    def test_add_relation_missing_type(self, mock_graph_service, mock_metrics):
        """Test add_relation fails without relation_type."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="add_relation",
            tenant="test_tenant",
            workspace="test_workspace",
            source_entity="ent_123",
            target_entity="ent_456",
            relation_type=None,
        )

        assert not result.success
        assert "Relation type must be provided" in result.error
        mock_graph_service.add_relation.assert_not_called()

    def test_query_success(self, mock_graph_service, mock_metrics):
        """Test successful query operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="query",
            tenant="test_tenant",
            workspace="test_workspace",
            query="MATCH (n:language) RETURN n",
        )

        assert result.success
        assert "entities" in result.data
        assert "relations" in result.data
        assert len(result.data["entities"]) == 1
        assert result.data["entities"][0]["name"] == "Python"

        # Verify service called correctly
        mock_graph_service.query_graph.assert_called_once_with(
            query="MATCH (n:language) RETURN n",
            tenant="test_tenant",
            workspace="test_workspace",
        )

    def test_query_missing_query_string(self, mock_graph_service, mock_metrics):
        """Test query fails without query string."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="query",
            tenant="test_tenant",
            workspace="test_workspace",
            query=None,
        )

        assert not result.success
        assert "Query must be provided" in result.error
        mock_graph_service.query_graph.assert_not_called()

    def test_get_entity_success(self, mock_graph_service, mock_metrics):
        """Test successful get_entity operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="get_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id="ent_123",
        )

        assert result.success
        assert result.data["id"] == "ent_123"
        assert result.data["name"] == "Python"

        # Verify service called correctly
        mock_graph_service.get_entity.assert_called_once_with(
            entity_id="ent_123",
            tenant="test_tenant",
            workspace="test_workspace",
        )

    def test_get_entity_missing_id(self, mock_graph_service, mock_metrics):
        """Test get_entity fails without entity_id."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="get_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id=None,
        )

        assert not result.success
        assert "Entity ID must be provided" in result.error
        mock_graph_service.get_entity.assert_not_called()

    def test_delete_entity_success(self, mock_graph_service, mock_metrics):
        """Test successful delete_entity operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="delete_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id="ent_123",
        )

        assert result.success
        assert result.data["status"] == "deleted"

        # Verify service called correctly
        mock_graph_service.delete_entity.assert_called_once_with(
            entity_id="ent_123",
            tenant="test_tenant",
            workspace="test_workspace",
        )

    def test_delete_entity_missing_id(self, mock_graph_service, mock_metrics):
        """Test delete_entity fails without entity_id."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="delete_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id=None,
        )

        assert not result.success
        assert "Entity ID must be provided" in result.error
        mock_graph_service.delete_entity.assert_not_called()

    def test_update_entity_success(self, mock_graph_service, mock_metrics):
        """Test successful update_entity operation."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="update_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id="ent_123",
            entity_name="Python 3.12",
            properties={"stable": True},
        )

        assert result.success
        assert result.data["entity_id"] == "ent_123"
        assert result.data["status"] == "updated"

        # Verify service called correctly
        mock_graph_service.update_entity.assert_called_once_with(
            entity_id="ent_123",
            entity_name="Python 3.12",
            properties={"stable": True},
            tenant="test_tenant",
            workspace="test_workspace",
        )

    def test_update_entity_missing_id(self, mock_graph_service, mock_metrics):
        """Test update_entity fails without entity_id."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="update_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_id=None,
            entity_name="Python 3.12",
        )

        assert not result.success
        assert "Entity ID must be provided" in result.error
        mock_graph_service.update_entity.assert_not_called()

    def test_unknown_action(self, mock_graph_service, mock_metrics):
        """Test handling of unknown action."""
        tool = GraphMemoryTool()

        result = tool._run(
            action="invalid_action",  # type: ignore
            tenant="test_tenant",
            workspace="test_workspace",
        )

        assert not result.success
        assert "Unknown action" in result.error

    def test_exception_handling(self, mock_graph_service, mock_metrics):
        """Test exception handling in tool operations."""
        mock_graph_service.add_entity.side_effect = Exception("Graph database unavailable")

        tool = GraphMemoryTool()
        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name="Python",
            entity_type="language",
        )

        assert not result.success
        assert "Graph memory operation failed" in result.error
        assert "Graph database unavailable" in result.error

    def test_tenant_workspace_passed_to_service(self, mock_graph_service, mock_metrics):
        """Test tenant and workspace are passed to all service methods."""
        tool = GraphMemoryTool()

        # Test add_entity
        tool._run(
            action="add_entity",
            tenant="tenant_a",
            workspace="workspace_b",
            entity_name="Test",
            entity_type="test",
        )

        call_args = mock_graph_service.add_entity.call_args[1]
        assert call_args["tenant"] == "tenant_a"
        assert call_args["workspace"] == "workspace_b"

    def test_optional_properties_handling(self, mock_graph_service, mock_metrics):
        """Test that optional properties are handled correctly."""
        tool = GraphMemoryTool()

        # Test with properties
        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name="Python",
            entity_type="language",
            properties={"version": "3.12"},
        )

        assert result.success
        call_args = mock_graph_service.add_entity.call_args[1]
        assert call_args["properties"] == {"version": "3.12"}

        # Test without properties
        mock_graph_service.add_entity.reset_mock()
        result = tool._run(
            action="add_entity",
            tenant="test_tenant",
            workspace="test_workspace",
            entity_name="Python",
            entity_type="language",
        )

        assert result.success
        call_args = mock_graph_service.add_entity.call_args[1]
        assert call_args["properties"] is None
