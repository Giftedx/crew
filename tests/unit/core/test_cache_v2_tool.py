"""Tests for Cache V2 Tool."""
from unittest.mock import AsyncMock, Mock, patch
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.cache_v2_tool import CacheV2Tool

class TestCacheV2Tool:
    """Test suite for CacheV2Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = CacheV2Tool()

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', False)
    def test_disabled_feature_flag(self):
        """Test tool behavior when ENABLE_CACHE_V2 is disabled."""
        result = self.tool._run(operation='get', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert 'ENABLE_CACHE_V2 is disabled' in result_obj.error

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_cache_namespace')
    def test_get_operation_success(self, mock_namespace, mock_cache_factory):
        """Test successful get operation."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = StepResult.ok(value='test_value', hit=True)
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()
        result = self.tool._run(operation='get', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert result_obj.data['value'] == 'test_value'
        assert result_obj.data['hit'] is True

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_cache_namespace')
    def test_get_operation_miss(self, mock_namespace, mock_cache_factory):
        """Test get operation with cache miss."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = StepResult.ok(value=None, hit=False)
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()
        result = self.tool._run(operation='get', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert result_obj.data['value'] is None
        assert result_obj.data['hit'] is False

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_cache_namespace')
    def test_set_operation_success(self, mock_namespace, mock_cache_factory):
        """Test successful set operation."""
        mock_cache = AsyncMock()
        mock_cache.set.return_value = StepResult.ok()
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()
        result = self.tool._run(operation='set', cache_name='test', key='test_key', value='test_value', dependencies=['dep1', 'dep2'], tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert result_obj.success

    def test_set_operation_missing_value(self):
        """Test set operation with missing value."""
        result = self.tool._run(operation='set', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert 'Value required for set operation' in result_obj.error

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_cache_namespace')
    def test_delete_operation(self, mock_namespace, mock_cache_factory):
        """Test delete operation."""
        mock_cache = AsyncMock()
        mock_cache.set.return_value = StepResult.ok()
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()
        result = self.tool._run(operation='delete', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert result_obj.success

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_cache_namespace')
    def test_get_stats_operation(self, mock_namespace, mock_cache_factory):
        """Test get_stats operation."""
        mock_cache_instance = AsyncMock()
        mock_cache_instance.get_stats.return_value = {'hits': 10, 'misses': 5}
        mock_cache = Mock()
        mock_cache.get_cache.return_value = mock_cache_instance
        mock_cache_factory.return_value = mock_cache
        mock_namespace.return_value = Mock()
        result = self.tool._run(operation='get_stats', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert result_obj.success
        assert result_obj.data['hits'] == 10
        assert result_obj.data['misses'] == 5

    def test_unknown_operation(self):
        """Test unknown operation."""
        result = self.tool._run(operation='unknown', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert 'Unknown operation: unknown' in result_obj.error

    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.ENABLE_CACHE_V2', True)
    @patch('ultimate_discord_intelligence_bot.tools.cache_v2_tool.get_unified_cache')
    def test_cache_exception_handling(self, mock_cache_factory):
        """Test exception handling during cache operations."""
        mock_cache_factory.side_effect = Exception('Cache connection failed')
        result = self.tool._run(operation='get', cache_name='test', key='test_key', tenant='test_tenant', workspace='test_workspace')
        result_obj = StepResult.from_json(result)
        assert not result_obj.success
        assert 'Cache operation failed' in result_obj.error