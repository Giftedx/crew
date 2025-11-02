"""Integration tests for error handling and tenant isolation."""
from unittest.mock import Mock, patch
from platform.core.step_result import StepResult

class TestErrorHandlingIntegration:
    """Test error handling across critical workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tenant = 'test_tenant'
        self.workspace = 'test_workspace'

    def test_tenant_isolation_memory_storage(self):
        """Test tenant isolation in memory storage operations."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool
        tool = MemoryStorageTool()
        with patch('ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client') as mock_client:
            mock_client.return_value.upsert.return_value = Mock()
            result = tool._run('test content', self.tenant, self.workspace)
            assert result.success
            assert self.tenant in str(result.data)

    def test_tenant_isolation_memory_retrieval(self):
        """Test tenant isolation in memory retrieval operations."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool
        tool = MemoryStorageTool()
        with patch('ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client') as mock_client:
            mock_client.return_value.search.return_value = Mock()
            result = tool._run('test query', self.tenant, self.workspace)
            assert isinstance(result, StepResult)

    def test_error_handling_network_failures(self):
        """Test error handling for network failures."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
        tool = FactCheckTool()
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Network error')
            result = tool._run('test claim', self.tenant, self.workspace)
            assert not result.success
            assert 'Network error' in result.error

    def test_error_handling_invalid_input(self):
        """Test error handling for invalid input."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
        tool = FactCheckTool()
        result = tool._run('', self.tenant, self.workspace)
        assert not result.success
        assert 'claim cannot be empty' in result.error

    def test_error_handling_missing_tenant(self):
        """Test error handling for missing tenant context."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool
        tool = MemoryStorageTool()
        result = tool._run('test content', '', self.workspace)
        assert not result.success
        assert 'tenant is required' in result.error

    def test_error_handling_missing_workspace(self):
        """Test error handling for missing workspace context."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool
        tool = MemoryStorageTool()
        result = tool._run('test content', self.tenant, '')
        assert not result.success
        assert 'workspace is required' in result.error

    def test_error_recovery_mechanisms(self):
        """Test error recovery mechanisms."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
        tool = FactCheckTool()
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [Exception('Backend 1 failed'), Mock(json=lambda: {'results': []})]
            result = tool._run('test claim', self.tenant, self.workspace)
            assert result.success

    def test_tenant_context_propagation(self):
        """Test tenant context propagation through tool chain."""
        from ultimate_discord_intelligence_bot.tools.memory_storage_tool import MemoryStorageTool
        tool = MemoryStorageTool()
        with patch('ultimate_discord_intelligence_bot.tools.memory_storage_tool.get_qdrant_client') as mock_client:
            mock_client.return_value.upsert.return_value = Mock()
            result = tool._run('test content', self.tenant, self.workspace)
            assert result.success
            mock_client.return_value.upsert.assert_called_once()
            call_args = mock_client.return_value.upsert.call_args
            assert self.tenant in str(call_args)

    def test_error_categorization(self):
        """Test proper error categorization."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
        tool = FactCheckTool()
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception('Connection timeout')
            result = tool._run('test claim', self.tenant, self.workspace)
            assert not result.success
            assert result.error_category == 'NETWORK_ERROR'

    def test_retry_mechanisms(self):
        """Test retry mechanisms for transient failures."""
        from ultimate_discord_intelligence_bot.tools.fact_check_tool import FactCheckTool
        tool = FactCheckTool()
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [Exception('Temporary failure'), Exception('Temporary failure'), Mock(json=lambda: {'results': []})]
            result = tool._run('test claim', self.tenant, self.workspace)
            assert result.success