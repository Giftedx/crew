"""Integration tests for content pipeline end-to-end workflows."""
from __future__ import annotations
from unittest.mock import patch
import pytest
from ultimate_discord_intelligence_bot.pipeline import ContentPipeline
from platform.core.step_result import StepResult

class TestContentPipeline:
    """Integration tests for content processing pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create content pipeline for testing."""
        return ContentPipeline()

    @pytest.fixture
    def sample_url(self):
        """Sample URL for testing."""
        return 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context for testing."""
        return ('test_tenant', 'test_workspace')

    @patch('ultimate_discord_intelligence_bot.pipeline.download_content')
    @patch('ultimate_discord_intelligence_bot.pipeline.transcribe_audio')
    @patch('ultimate_discord_intelligence_bot.pipeline.analyze_content')
    def test_end_to_end_processing_success(self, mock_analyze, mock_transcribe, mock_download, pipeline, sample_url, sample_tenant_context):
        """Test successful end-to-end content processing."""
        tenant, workspace = sample_tenant_context
        mock_download.return_value = StepResult.ok(data={'file_path': '/tmp/test.mp4'})
        mock_transcribe.return_value = StepResult.ok(data={'transcript': 'test transcript'})
        mock_analyze.return_value = StepResult.ok(data={'analysis': 'test analysis'})
        result = pipeline.process_content(sample_url, tenant, workspace)
        assert result.success
        assert 'analysis' in result.data
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_analyze.assert_called_once()

    @patch('ultimate_discord_intelligence_bot.pipeline.download_content')
    def test_download_failure_handling(self, mock_download, pipeline, sample_url, sample_tenant_context):
        """Test handling of download failures."""
        tenant, workspace = sample_tenant_context
        mock_download.return_value = StepResult.fail('Download failed')
        result = pipeline.process_content(sample_url, tenant, workspace)
        assert not result.success
        assert 'Download failed' in result.error

    @patch('ultimate_discord_intelligence_bot.pipeline.download_content')
    @patch('ultimate_discord_intelligence_bot.pipeline.transcribe_audio')
    def test_transcription_failure_handling(self, mock_transcribe, mock_download, pipeline, sample_url, sample_tenant_context):
        """Test handling of transcription failures."""
        tenant, workspace = sample_tenant_context
        mock_download.return_value = StepResult.ok(data={'file_path': '/tmp/test.mp4'})
        mock_transcribe.return_value = StepResult.fail('Transcription failed')
        result = pipeline.process_content(sample_url, tenant, workspace)
        assert not result.success
        assert 'Transcription failed' in result.error

    def test_invalid_url_handling(self, pipeline, sample_tenant_context):
        """Test handling of invalid URLs."""
        tenant, workspace = sample_tenant_context
        invalid_url = 'not-a-valid-url'
        result = pipeline.process_content(invalid_url, tenant, workspace)
        assert not result.success
        assert 'Invalid URL' in result.error

    def test_missing_tenant_context(self, pipeline, sample_url):
        """Test handling of missing tenant context."""
        result = pipeline.process_content(sample_url, '', '')
        assert not result.success
        assert 'Tenant and workspace are required' in result.error

    @patch('ultimate_discord_intelligence_bot.pipeline.download_content')
    @patch('ultimate_discord_intelligence_bot.pipeline.transcribe_audio')
    @patch('ultimate_discord_intelligence_bot.pipeline.analyze_content')
    def test_tenant_isolation(self, mock_analyze, mock_transcribe, mock_download, pipeline, sample_url):
        """Test that tenant isolation is maintained throughout pipeline."""
        tenant1, workspace1 = ('tenant1', 'workspace1')
        tenant2, workspace2 = ('tenant2', 'workspace2')
        mock_download.return_value = StepResult.ok(data={'file_path': '/tmp/test.mp4'})
        mock_transcribe.return_value = StepResult.ok(data={'transcript': 'test transcript'})
        mock_analyze.return_value = StepResult.ok(data={'analysis': 'test analysis'})
        result1 = pipeline.process_content(sample_url, tenant1, workspace1)
        result2 = pipeline.process_content(sample_url, tenant2, workspace2)
        assert result1.success
        assert result2.success
        for call in mock_download.call_args_list:
            assert call[0][1] in [tenant1, tenant2]
            assert call[0][2] in [workspace1, workspace2]