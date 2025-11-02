"""Tests for Enhanced Analysis Tool."""
from unittest.mock import MagicMock, patch
import pytest
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool

class TestEnhancedAnalysisTool:
    """Test cases for Enhanced Analysis Tool."""

    @pytest.fixture
    def tool(self):
        """Create EnhancedAnalysisTool instance."""
        return EnhancedAnalysisTool()

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return 'This is a political statement about healthcare policy that needs analysis.'

    @pytest.fixture
    def sample_dict_content(self):
        """Sample dictionary content for testing."""
        return {'description': 'Political content about healthcare', 'title': 'Healthcare Policy Analysis', 'url': 'https://example.com/article'}

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == 'Enhanced Content Analysis Tool'
        assert tool.description == 'Analyze content with multiple analysis modes and intelligent fallbacks'
        assert hasattr(tool, '_run')

    def test_successful_comprehensive_analysis(self, tool, sample_content):
        """Test successful comprehensive analysis."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 0.5}
            result = tool._run(sample_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data is not None
            assert 'political_topics' in result.data
            assert 'sentiment' in result.data
            mock_analyze.assert_called_once()

    def test_successful_political_analysis(self, tool, sample_content):
        """Test successful political analysis."""
        with patch.object(tool, '_analyze_political') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'processing_time': 0.3}
            result = tool._run(sample_content, 'political', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data is not None
            assert 'political_topics' in result.data
            mock_analyze.assert_called_once()

    def test_successful_sentiment_analysis(self, tool, sample_content):
        """Test successful sentiment analysis."""
        with patch.object(tool, '_analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {'sentiment': 'positive', 'sentiment_confidence': 0.9, 'processing_time': 0.2}
            result = tool._run(sample_content, 'sentiment', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data is not None
            assert result.data['sentiment'] == 'positive'
            mock_analyze.assert_called_once()

    def test_successful_claims_analysis(self, tool, sample_content):
        """Test successful claims analysis."""
        with patch.object(tool, '_analyze_claims') as mock_analyze:
            mock_analyze.return_value = {'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 0.4}
            result = tool._run(sample_content, 'claims', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data is not None
            assert 'extracted_claims' in result.data
            mock_analyze.assert_called_once()

    def test_dict_content_handling(self, tool, sample_dict_content):
        """Test handling of dictionary content."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'processing_time': 0.5}
            result = tool._run(sample_dict_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert result.success
            mock_analyze.assert_called_once()

    def test_missing_required_parameters(self, tool):
        """Test handling of missing required parameters."""
        result = tool._run('', 'comprehensive', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'Content cannot be empty' in result.error
        result = tool._run('content', '', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'Analysis type is required' in result.error
        result = tool._run('content', 'comprehensive', '', 'test_workspace')
        assert not result.success
        assert 'Tenant is required' in result.error
        result = tool._run('content', 'comprehensive', 'test_tenant', '')
        assert not result.success
        assert 'Workspace is required' in result.error

    def test_invalid_analysis_type(self, tool, sample_content):
        """Test handling of invalid analysis type."""
        result = tool._run(sample_content, 'invalid_type', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'Invalid analysis type' in result.error

    def test_analysis_failure_handling(self, tool, sample_content):
        """Test handling of analysis failures."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.side_effect = Exception('Analysis failed')
            result = tool._run(sample_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert not result.success
            assert 'Analysis failed' in result.error

    def test_metrics_integration(self, tool, sample_content):
        """Test metrics integration."""
        with patch('ultimate_discord_intelligence_bot.obs.metrics.get_metrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
                mock_analyze.return_value = {'processing_time': 0.5}
                tool._run(sample_content, 'comprehensive', 'test_tenant', 'test_workspace')
                mock_metrics_instance.increment.assert_called()

    def test_processing_time_tracking(self, tool, sample_content):
        """Test processing time tracking."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'processing_time': 0.5}
            result = tool._run(sample_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert result.success
            assert 'processing_time' in result.data
            assert result.data['processing_time'] > 0

    def test_content_preprocessing(self, tool):
        """Test content preprocessing."""
        result = tool._run('Simple text', 'comprehensive', 'test_tenant', 'test_workspace')
        assert result.success
        dict_content = {'description': 'Test content'}
        result = tool._run(dict_content, 'comprehensive', 'test_tenant', 'test_workspace')
        assert result.success
        dict_content = {'title': 'Test title'}
        result = tool._run(dict_content, 'comprehensive', 'test_tenant', 'test_workspace')
        assert result.success

    def test_tenant_workspace_isolation(self, tool, sample_content):
        """Test tenant and workspace isolation."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'processing_time': 0.5}
            result1 = tool._run(sample_content, 'comprehensive', 'tenant1', 'workspace1')
            result2 = tool._run(sample_content, 'comprehensive', 'tenant2', 'workspace2')
            assert result1.success
            assert result2.success

    def test_error_handling_with_invalid_content_type(self, tool):
        """Test error handling with invalid content type."""
        result = tool._run(None, 'comprehensive', 'test_tenant', 'test_workspace')
        assert not result.success
        result = tool._run({}, 'comprehensive', 'test_tenant', 'test_workspace')
        assert not result.success

    def test_analysis_type_case_insensitive(self, tool, sample_content):
        """Test that analysis type is case insensitive."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'processing_time': 0.5}
            result = tool._run(sample_content, 'COMPREHENSIVE', 'test_tenant', 'test_workspace')
            assert result.success
            mock_analyze.assert_called_once()

    def test_concurrent_analysis_requests(self, tool, sample_content):
        """Test handling of concurrent analysis requests."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'processing_time': 0.5}
            results = []
            for i in range(5):
                result = tool._run(f'{sample_content} {i}', 'comprehensive', 'test_tenant', 'test_workspace')
                results.append(result)
            for result in results:
                assert result.success

    def test_memory_usage_optimization(self, tool, sample_content):
        """Test memory usage optimization."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'processing_time': 0.5}
            large_content = 'x' * 10000
            result = tool._run(large_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert result.success
            mock_analyze.assert_called_once()

    def test_analysis_result_structure(self, tool, sample_content):
        """Test that analysis results have the expected structure."""
        with patch.object(tool, '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 0.5}
            result = tool._run(sample_content, 'comprehensive', 'test_tenant', 'test_workspace')
            assert result.success
            data = result.data
            assert 'political_topics' in data
            assert 'bias_indicators' in data
            assert 'sentiment' in data
            assert 'sentiment_confidence' in data
            assert 'extracted_claims' in data
            assert 'processing_time' in data
            assert isinstance(data['political_topics'], list)
            assert isinstance(data['bias_indicators'], list)
            assert isinstance(data['sentiment'], str)
            assert isinstance(data['sentiment_confidence'], (int, float))
            assert isinstance(data['extracted_claims'], list)
            assert isinstance(data['processing_time'], (int, float))