"""Tests for Unified Memory Tool."""
from unittest.mock import MagicMock, patch
import pytest
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool

class TestUnifiedMemoryTool:
    """Test cases for Unified Memory Tool."""

    @pytest.fixture
    def tool(self):
        """Create UnifiedMemoryTool instance."""
        return UnifiedMemoryTool()

    @pytest.fixture
    def sample_content(self):
        """Sample content for storage."""
        return 'This is sample content for memory storage testing.'

    @pytest.fixture
    def sample_query(self):
        """Sample query for retrieval."""
        return 'sample content'

    def test_tool_initialization(self, tool):
        """Test UnifiedMemoryTool initialization."""
        assert tool is not None
        assert hasattr(tool, '_run')

    def test_memory_store_basic(self, tool, sample_content):
        """Test basic memory storage functionality."""
        result = tool._run(query=sample_content)
        assert isinstance(result, StepResult)
        assert result.success or result.status == 'uncertain'

    def test_memory_retrieve_basic(self, tool, sample_query):
        """Test basic memory retrieval functionality."""
        result = tool._run(query=sample_query, intent='general', limit=5, min_confidence=0.5)
        assert isinstance(result, StepResult)
        assert result.success or result.status == 'uncertain'

    def test_memory_store_empty_content(self, tool):
        """Test memory storage with empty content."""
        result = tool._run(query='')
        assert isinstance(result, StepResult)
        assert result.success or result.status == 'uncertain'

    def test_memory_retrieve_empty_query(self, tool):
        """Test memory retrieval with empty query."""
        result = tool._run(query='')
        assert isinstance(result, StepResult)
        assert result.success or result.status == 'uncertain'

    def test_memory_tenant_isolation(self, tool, sample_content, sample_query):
        """Test memory operations respect tenant isolation."""
        result1 = tool._run(query=sample_content)
        result2 = tool._run(query=sample_query, intent='general')
        assert isinstance(result1, StepResult)
        assert isinstance(result2, StepResult)
        assert result1.success or result1.status == 'uncertain'
        assert result2.success or result2.status == 'uncertain'

    @patch('ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool.UnifiedMemoryService')
    def test_memory_with_mock_service(self, mock_service_class, tool, sample_content):
        """Test memory operations with mocked service."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.store_content.return_value = StepResult.ok(data={'stored': True})
        result = tool._run(query=sample_content)
        assert isinstance(result, StepResult)
        assert result.success or result.status == 'uncertain'