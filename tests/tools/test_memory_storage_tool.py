"""Tests for MemoryStorageTool."""
from unittest.mock import patch
import pytest
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.memory.memory_storage_tool import MemoryStorageTool

class TestMemoryStorageTool:
    """Test cases for MemoryStorageTool."""

    @pytest.fixture
    def tool(self):
        """Create MemoryStorageTool instance."""
        return MemoryStorageTool()

    def test_tool_initialization(self, tool):
        """Test tool initializes correctly."""
        assert tool.name == 'memory_storage'
        assert 'memory' in tool.description.lower()

    def test_run_with_valid_inputs(self, tool):
        """Test memory storage with valid inputs."""
        with patch.object(tool, '_store_memory') as mock_store:
            mock_store.return_value = StepResult.ok(data={'memory_id': 'mem_123', 'status': 'stored', 'namespace': 'test'})
            result = tool._run('Test content', 'test_namespace')
            assert result.success
            assert 'memory_id' in result.data
            mock_store.assert_called_once()

    def test_run_with_empty_content(self, tool):
        """Test memory storage with empty content."""
        result = tool._run('', 'test_namespace')
        assert not result.success
        assert 'empty' in result.error.lower()

    def test_run_with_missing_namespace(self, tool):
        """Test memory storage with missing namespace."""
        result = tool._run('Test content', '')
        assert not result.success
        assert 'namespace' in result.error.lower()

    def test_store_memory_success(self, tool):
        """Test successful memory storage."""
        content = 'Important information to store'
        namespace = 'test_namespace'
        with patch.object(tool, '_generate_embedding') as mock_embedding:
            with patch.object(tool, '_save_to_vector_db') as mock_save:
                mock_embedding.return_value = [0.1, 0.2, 0.3]
                mock_save.return_value = 'mem_123'
                result = tool._store_memory(content, namespace)
                assert result.success
                assert result.data['memory_id'] == 'mem_123'
                assert result.data['namespace'] == namespace

    def test_generate_embedding(self, tool):
        """Test embedding generation."""
        content = 'Test content for embedding'
        with patch.object(tool, '_get_embedding_model') as mock_model:
            mock_model.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
            embedding = tool._generate_embedding(content)
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all((isinstance(x, (int, float)) for x in embedding))

    def test_save_to_vector_db(self, tool):
        """Test saving to vector database."""
        content = 'Test content'
        embedding = [0.1, 0.2, 0.3]
        namespace = 'test'
        with patch.object(tool, '_get_vector_client') as mock_client:
            mock_client.return_value.upsert.return_value = {'ids': ['mem_123']}
            memory_id = tool._save_to_vector_db(content, embedding, namespace)
            assert memory_id == 'mem_123'
            mock_client.return_value.upsert.assert_called_once()

    def test_handle_storage_error(self, tool):
        """Test error handling in memory storage."""
        with patch.object(tool, '_generate_embedding') as mock_embedding:
            mock_embedding.side_effect = Exception('Embedding failed')
            result = tool._store_memory('test content', 'test_namespace')
            assert not result.success
            assert 'failed' in result.error.lower()

    def test_validate_inputs(self, tool):
        """Test input validation."""
        assert tool._validate_inputs('Valid content', 'valid_namespace') is True
        assert tool._validate_inputs('', 'valid_namespace') is False
        assert tool._validate_inputs('Valid content', '') is False
        assert tool._validate_inputs('', '') is False

    def test_retrieve_memory(self, tool):
        """Test memory retrieval."""
        query = 'test query'
        namespace = 'test_namespace'
        with patch.object(tool, '_search_vector_db') as mock_search:
            mock_search.return_value = [{'content': 'Relevant content', 'score': 0.95, 'id': 'mem_123'}]
            results = tool._retrieve_memory(query, namespace)
            assert isinstance(results, list)
            assert len(results) > 0
            assert results[0]['score'] == 0.95

    def test_search_vector_db(self, tool):
        """Test vector database search."""
        query = 'test query'
        namespace = 'test'
        with patch.object(tool, '_get_vector_client') as mock_client:
            with patch.object(tool, '_generate_embedding') as mock_embedding:
                mock_embedding.return_value = [0.1, 0.2, 0.3]
                mock_client.return_value.search.return_value = [{'content': 'Result 1', 'score': 0.9, 'id': 'mem_1'}]
                results = tool._search_vector_db(query, namespace)
                assert isinstance(results, list)
                assert len(results) > 0
                assert results[0]['score'] == 0.9

    def test_delete_memory(self, tool):
        """Test memory deletion."""
        memory_id = 'mem_123'
        namespace = 'test'
        with patch.object(tool, '_get_vector_client') as mock_client:
            mock_client.return_value.delete.return_value = {'status': 'deleted'}
            result = tool._delete_memory(memory_id, namespace)
            assert result.success
            assert result.data['status'] == 'deleted'

    def test_update_memory(self, tool):
        """Test memory update."""
        memory_id = 'mem_123'
        content = 'Updated content'
        namespace = 'test'
        with patch.object(tool, '_generate_embedding') as mock_embedding:
            with patch.object(tool, '_save_to_vector_db') as mock_save:
                mock_embedding.return_value = [0.1, 0.2, 0.3]
                mock_save.return_value = memory_id
                result = tool._update_memory(memory_id, content, namespace)
                assert result.success
                assert result.data['memory_id'] == memory_id