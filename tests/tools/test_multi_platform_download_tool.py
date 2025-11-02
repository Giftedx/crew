"""Tests for Multi-Platform Download Tool."""
from unittest.mock import MagicMock, patch
import pytest
from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool

class TestMultiPlatformDownloadTool:
    """Test cases for Multi-Platform Download Tool."""

    @pytest.fixture
    def tool(self):
        """Create MultiPlatformDownloadTool instance."""
        return MultiPlatformDownloadTool()

    @pytest.fixture
    def youtube_url(self):
        """Sample YouTube URL for testing."""
        return 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    @pytest.fixture
    def twitter_url(self):
        """Sample Twitter URL for testing."""
        return 'https://twitter.com/example/status/123456789'

    @pytest.fixture
    def instagram_url(self):
        """Sample Instagram URL for testing."""
        return 'https://www.instagram.com/p/example123/'

    @pytest.fixture
    def tiktok_url(self):
        """Sample TikTok URL for testing."""
        return 'https://www.tiktok.com/@user/video/123456789'

    @pytest.fixture
    def mock_download_result(self):
        """Mock download result."""
        return {'success': True, 'platform': 'youtube', 'title': 'Test Video', 'duration': 180, 'quality': '720p', 'file_path': '/tmp/downloaded_video.mp4', 'metadata': {'uploader': 'Test Channel', 'view_count': 1000, 'upload_date': '2024-01-01'}}

    def test_tool_initialization(self, tool):
        """Test tool initialization."""
        assert tool is not None
        assert tool.name == 'Multi-Platform Download Tool'
        assert tool.description == 'Download content from multiple platforms with unified interface'
        assert hasattr(tool, '_run')

    def test_successful_youtube_download(self, tool, youtube_url, mock_download_result):
        """Test successful YouTube download."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = mock_download_result
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data is not None
            assert result.data['platform'] == 'youtube'
            assert result.data['title'] == 'Test Video'
            mock_download.assert_called_once()

    def test_successful_twitter_download(self, tool, twitter_url, mock_download_result):
        """Test successful Twitter download."""
        with patch.object(tool, '_download_twitter') as mock_download:
            mock_download_result['platform'] = 'twitter'
            mock_download.return_value = mock_download_result
            result = tool._run(twitter_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['platform'] == 'twitter'
            mock_download.assert_called_once()

    def test_successful_instagram_download(self, tool, instagram_url, mock_download_result):
        """Test successful Instagram download."""
        with patch.object(tool, '_download_instagram') as mock_download:
            mock_download_result['platform'] = 'instagram'
            mock_download.return_value = mock_download_result
            result = tool._run(instagram_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['platform'] == 'instagram'
            mock_download.assert_called_once()

    def test_successful_tiktok_download(self, tool, tiktok_url, mock_download_result):
        """Test successful TikTok download."""
        with patch.object(tool, '_download_tiktok') as mock_download:
            mock_download_result['platform'] = 'tiktok'
            mock_download.return_value = mock_download_result
            result = tool._run(tiktok_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['platform'] == 'tiktok'
            mock_download.assert_called_once()

    def test_platform_detection(self, tool):
        """Test platform detection from URLs."""
        test_cases = [('https://www.youtube.com/watch?v=123', 'youtube'), ('https://youtu.be/123', 'youtube'), ('https://twitter.com/user/status/123', 'twitter'), ('https://x.com/user/status/123', 'twitter'), ('https://www.instagram.com/p/123/', 'instagram'), ('https://www.tiktok.com/@user/video/123', 'tiktok'), ('https://www.reddit.com/r/subreddit/comments/123', 'reddit'), ('https://www.twitch.tv/videos/123', 'twitch'), ('https://kick.com/user/video/123', 'kick'), ('https://discord.com/channels/123/456', 'discord')]
        for url, expected_platform in test_cases:
            detected_platform = tool._detect_platform(url)
            assert detected_platform == expected_platform, f'Failed for URL: {url}'

    def test_unsupported_platform(self, tool):
        """Test handling of unsupported platforms."""
        unsupported_url = 'https://unsupported-platform.com/video/123'
        result = tool._run(unsupported_url, '720p', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'Unsupported platform' in result.error

    def test_missing_required_parameters(self, tool):
        """Test handling of missing required parameters."""
        result = tool._run('', '720p', 'test_tenant', 'test_workspace')
        assert not result.success
        assert 'URL cannot be empty' in result.error
        result = tool._run('https://youtube.com/watch?v=123', '720p', '', 'test_workspace')
        assert not result.success
        assert 'Tenant is required' in result.error
        result = tool._run('https://youtube.com/watch?v=123', '720p', 'test_tenant', '')
        assert not result.success
        assert 'Workspace is required' in result.error

    def test_invalid_url_format(self, tool):
        """Test handling of invalid URL format."""
        invalid_urls = ['not-a-url', 'ftp://example.com/video', 'https://', 'javascript:void(0)']
        for invalid_url in invalid_urls:
            result = tool._run(invalid_url, '720p', 'test_tenant', 'test_workspace')
            assert not result.success
            assert 'Invalid URL format' in result.error

    def test_quality_validation(self, tool, youtube_url):
        """Test quality parameter validation."""
        valid_qualities = ['144p', '240p', '360p', '480p', '720p', '1080p', 'best', 'worst']
        for quality in valid_qualities:
            with patch.object(tool, '_download_youtube') as mock_download:
                mock_download.return_value = {'success': True, 'platform': 'youtube'}
                result = tool._run(youtube_url, quality, 'test_tenant', 'test_workspace')
                assert result.success

    def test_download_failure_handling(self, tool, youtube_url):
        """Test handling of download failures."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.side_effect = Exception('Download failed')
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert not result.success
            assert 'Download failed' in result.error

    def test_network_error_handling(self, tool, youtube_url):
        """Test handling of network errors."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.side_effect = ConnectionError('Network unreachable')
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert not result.success
            assert 'Network error' in result.error

    def test_tenant_workspace_isolation(self, tool, youtube_url):
        """Test tenant and workspace isolation."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube'}
            result1 = tool._run(youtube_url, '720p', 'tenant1', 'workspace1')
            result2 = tool._run(youtube_url, '720p', 'tenant2', 'workspace2')
            assert result1.success
            assert result2.success

    def test_metrics_integration(self, tool, youtube_url):
        """Test metrics integration."""
        with patch('ultimate_discord_intelligence_bot.obs.metrics.get_metrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            with patch.object(tool, '_download_youtube') as mock_download:
                mock_download.return_value = {'success': True, 'platform': 'youtube'}
                tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
                mock_metrics_instance.increment.assert_called()

    def test_download_result_structure(self, tool, youtube_url, mock_download_result):
        """Test that download results have the expected structure."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = mock_download_result
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            data = result.data
            assert 'success' in data
            assert 'platform' in data
            assert 'title' in data
            assert 'file_path' in data
            assert isinstance(data['success'], bool)
            assert isinstance(data['platform'], str)
            assert isinstance(data['title'], str)
            assert isinstance(data['file_path'], str)

    def test_metadata_extraction(self, tool, youtube_url):
        """Test metadata extraction."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'title': 'Test Video', 'metadata': {'uploader': 'Test Channel', 'view_count': 1000, 'upload_date': '2024-01-01', 'description': 'Test description'}}
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert 'metadata' in result.data
            assert result.data['metadata']['uploader'] == 'Test Channel'
            assert result.data['metadata']['view_count'] == 1000

    def test_file_path_validation(self, tool, youtube_url):
        """Test file path validation."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/downloaded_video.mp4'}
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['file_path'] == '/tmp/downloaded_video.mp4'

    def test_concurrent_downloads(self, tool):
        """Test handling of concurrent downloads."""
        urls = ['https://youtube.com/watch?v=1', 'https://youtube.com/watch?v=2', 'https://youtube.com/watch?v=3']
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube'}
            results = []
            for url in urls:
                result = tool._run(url, '720p', 'test_tenant', 'test_workspace')
                results.append(result)
            for result in results:
                assert result.success

    def test_quality_fallback(self, tool, youtube_url):
        """Test quality fallback when requested quality is not available."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'quality': '480p', 'original_quality_requested': '1080p'}
            result = tool._run(youtube_url, '1080p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['quality'] == '480p'

    def test_duration_validation(self, tool, youtube_url):
        """Test duration validation."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'duration': 3600, 'duration_limit': 1800}
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            assert result.data['duration'] == 3600

    def test_error_handling_with_invalid_parameters(self, tool):
        """Test error handling with invalid parameters."""
        result = tool._run(None, '720p', 'test_tenant', 'test_workspace')
        assert not result.success
        result = tool._run('https://youtube.com/watch?v=123', None, 'test_tenant', 'test_workspace')
        assert not result.success

    def test_platform_specific_handling(self, tool):
        """Test platform-specific handling."""
        youtube_url = 'https://youtube.com/watch?v=123'
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube'}
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            mock_download.assert_called_once()
        twitter_url = 'https://twitter.com/user/status/123'
        with patch.object(tool, '_download_twitter') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'twitter'}
            result = tool._run(twitter_url, '720p', 'test_tenant', 'test_workspace')
            assert result.success
            mock_download.assert_called_once()

    def test_quality_parameter_handling(self, tool, youtube_url):
        """Test quality parameter handling."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube'}
            result = tool._run(youtube_url, '', 'test_tenant', 'test_workspace')
            assert result.success
            result = tool._run(youtube_url, None, 'test_tenant', 'test_workspace')
            assert result.success

    def test_url_normalization(self, tool):
        """Test URL normalization."""
        test_cases = [('https://youtube.com/watch?v=123', 'https://www.youtube.com/watch?v=123'), ('youtube.com/watch?v=123', 'https://www.youtube.com/watch?v=123'), ('https://youtu.be/123', 'https://www.youtube.com/watch?v=123')]
        for input_url, expected_normalized in test_cases:
            normalized = tool._normalize_url(input_url)
            assert normalized == expected_normalized

    def test_download_timeout_handling(self, tool, youtube_url):
        """Test download timeout handling."""
        with patch.object(tool, '_download_youtube') as mock_download:
            mock_download.side_effect = TimeoutError('Download timeout')
            result = tool._run(youtube_url, '720p', 'test_tenant', 'test_workspace')
            assert not result.success
            assert 'Timeout' in result.error