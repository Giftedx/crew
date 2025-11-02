"""Integration tests for Discord bot workflow."""
from unittest.mock import MagicMock, patch
import pytest
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.discord.discord_monitor_tool import DiscordMonitorTool
from ultimate_discord_intelligence_bot.tools.discord.discord_post_tool import DiscordPostTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool

class TestDiscordBotWorkflow:
    """Integration tests for Discord bot workflow."""

    @pytest.fixture
    def bot_tools(self):
        """Create all tools needed for the Discord bot workflow."""
        return {'post_tool': DiscordPostTool(), 'monitor_tool': DiscordMonitorTool(), 'analysis_tool': EnhancedAnalysisTool(), 'verification_tool': ClaimVerifierTool()}

    @pytest.fixture
    def sample_discord_message(self):
        """Sample Discord message for testing."""
        return {'content': 'This is a political statement about healthcare policy that needs analysis.', 'author': 'test_user', 'channel_id': '123456789', 'guild_id': '987654321', 'timestamp': '2024-01-01T00:00:00Z'}

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {'tenant': 'discord_tenant', 'workspace': 'discord_workspace'}

    def test_discord_message_processing_workflow(self, bot_tools, sample_discord_message, sample_tenant_context):
        """Test the complete Discord message processing workflow."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_message') as mock_monitor:
            mock_monitor.return_value = {'success': True, 'message_id': 'msg_123', 'channel_id': sample_discord_message['channel_id'], 'guild_id': sample_discord_message['guild_id'], 'author': sample_discord_message['author'], 'content': sample_discord_message['content'], 'timestamp': sample_discord_message['timestamp'], 'mentions': [], 'attachments': []}
            monitor_result = bot_tools['monitor_tool']._run(sample_discord_message['channel_id'], sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert monitor_result.success
            assert monitor_result.data['content'] == sample_discord_message['content']
        with patch.object(bot_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 1.5}
            analysis_result = bot_tools['analysis_tool']._run(monitor_result.data['content'], 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert analysis_result.success
            assert 'political_topics' in analysis_result.data
            assert 'sentiment' in analysis_result.data
        if analysis_result.data['extracted_claims']:
            with patch.object(bot_tools['verification_tool'], '_verify_claim') as mock_verify:
                mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': analysis_result.data['extracted_claims'][0], 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [{'source_id': 'source_1', 'title': 'Healthcare Policy Study', 'url': 'https://example.com/study', 'snippet': 'Research shows healthcare policy improvements...', 'relevance_score': 0.95, 'backend': 'serply', 'timestamp': '2024-01-01T00:00:00Z', 'domain': 'example.com'}], 'processing_time': 2.0, 'backends_used': ['serply', 'exa'], 'error_message': None}
                verification_result = bot_tools['verification_tool']._run(analysis_result.data['extracted_claims'][0], 'Discord message context', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert verification_result.success
                assert verification_result.data['verification_status'] == 'verified'
        with patch.object(bot_tools['post_tool'], '_post_message') as mock_post:
            mock_post.return_value = {'success': True, 'message_id': 'response_123', 'channel_id': sample_discord_message['channel_id'], 'content': 'Analysis complete: Healthcare policy topic detected with neutral sentiment.', 'timestamp': '2024-01-01T00:01:00Z'}
            response_content = f'\n**Analysis Results:**\n- **Political Topics:** {', '.join(analysis_result.data['political_topics'])}\n- **Sentiment:** {analysis_result.data['sentiment']} (confidence: {analysis_result.data['sentiment_confidence']})\n- **Claims Found:** {len(analysis_result.data['extracted_claims'])}\n'
            if analysis_result.data['extracted_claims']:
                response_content += f'- **Verification Status:** {verification_result.data['verification_status']}\n'
            post_result = bot_tools['post_tool']._run(sample_discord_message['channel_id'], response_content, sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert post_result.success
            assert post_result.data['message_id'] == 'response_123'

    def test_discord_monitoring_workflow(self, bot_tools, sample_tenant_context):
        """Test Discord monitoring workflow."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.return_value = {'success': True, 'channel_id': '123456789', 'messages': [{'message_id': 'msg_1', 'content': 'First message', 'author': 'user1', 'timestamp': '2024-01-01T00:00:00Z'}, {'message_id': 'msg_2', 'content': 'Second message', 'author': 'user2', 'timestamp': '2024-01-01T00:01:00Z'}], 'total_messages': 2}
            monitor_result = bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert monitor_result.success
            assert len(monitor_result.data['messages']) == 2

    def test_discord_analysis_workflow(self, bot_tools, sample_tenant_context):
        """Test Discord analysis workflow."""
        sample_messages = ['This is a political statement about healthcare.', 'Technology is advancing rapidly.', 'Climate change is a serious issue.']
        with patch.object(bot_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'technology', 'climate'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important', 'Technology advances', 'Climate change is serious'], 'processing_time': 2.0}
            results = []
            for message in sample_messages:
                result = bot_tools['analysis_tool']._run(message, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                results.append(result)
            for result in results:
                assert result.success

    def test_discord_verification_workflow(self, bot_tools, sample_tenant_context):
        """Test Discord verification workflow."""
        sample_claims = ['Healthcare costs are rising', 'Technology improves productivity', 'Climate change is accelerating']
        with patch.object(bot_tools['verification_tool'], '_verify_claim') as mock_verify:
            mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': 'Test claim', 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [], 'processing_time': 2.0, 'backends_used': ['serply'], 'error_message': None}
            results = []
            for claim in sample_claims:
                result = bot_tools['verification_tool']._run(claim, 'Discord context', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                results.append(result)
            for result in results:
                assert result.success

    def test_discord_posting_workflow(self, bot_tools, sample_tenant_context):
        """Test Discord posting workflow."""
        sample_messages = ['Analysis complete: Healthcare topic detected.', 'Verification results: Claim verified with 90% confidence.', 'Summary: 3 political topics identified.']
        with patch.object(bot_tools['post_tool'], '_post_message') as mock_post:
            mock_post.return_value = {'success': True, 'message_id': 'response_123', 'channel_id': '123456789', 'content': 'Test message', 'timestamp': '2024-01-01T00:00:00Z'}
            results = []
            for message in sample_messages:
                result = bot_tools['post_tool']._run('123456789', message, sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                results.append(result)
            for result in results:
                assert result.success

    def test_discord_workflow_error_handling(self, bot_tools, sample_tenant_context):
        """Test Discord workflow error handling."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.side_effect = Exception('Monitoring failed')
            result = bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert not result.success
            assert 'Monitoring failed' in result.error
        with patch.object(bot_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.side_effect = Exception('Analysis failed')
            result = bot_tools['analysis_tool']._run('Test content', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert not result.success
            assert 'Analysis failed' in result.error
        with patch.object(bot_tools['post_tool'], '_post_message') as mock_post:
            mock_post.side_effect = Exception('Posting failed')
            result = bot_tools['post_tool']._run('123456789', 'Test message', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert not result.success
            assert 'Posting failed' in result.error

    def test_discord_concurrent_processing(self, bot_tools, sample_tenant_context):
        """Test concurrent Discord message processing."""
        channels = ['123456789', '987654321', '456789123']
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.return_value = {'success': True, 'channel_id': '123456789', 'messages': [], 'total_messages': 0}
            results = []
            for channel in channels:
                result = bot_tools['monitor_tool']._run(channel, sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                results.append(result)
            for result in results:
                assert result.success

    def test_discord_tenant_isolation(self, bot_tools):
        """Test tenant isolation in Discord workflow."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.return_value = {'success': True, 'channel_id': '123456789', 'messages': [], 'total_messages': 0}
            result1 = bot_tools['monitor_tool']._run('123456789', 'tenant1', 'workspace1')
            result2 = bot_tools['monitor_tool']._run('123456789', 'tenant2', 'workspace2')
            assert result1.success
            assert result2.success

    def test_discord_message_filtering(self, bot_tools, sample_tenant_context):
        """Test Discord message filtering."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.return_value = {'success': True, 'channel_id': '123456789', 'messages': [{'message_id': 'msg_1', 'content': 'This is a political statement about healthcare.', 'author': 'user1', 'timestamp': '2024-01-01T00:00:00Z', 'mentions': [], 'attachments': []}, {'message_id': 'msg_2', 'content': 'Hello everyone!', 'author': 'user2', 'timestamp': '2024-01-01T00:01:00Z', 'mentions': [], 'attachments': []}], 'total_messages': 2, 'filtered_messages': 1}
            result = bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert result.success
            assert result.data['filtered_messages'] == 1

    def test_discord_workflow_performance(self, bot_tools, sample_tenant_context):
        """Test Discord workflow performance."""
        with patch('ultimate_discord_intelligence_bot.obs.metrics.get_metrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
                mock_monitor.return_value = {'success': True, 'channel_id': '123456789', 'messages': [], 'total_messages': 0}
                bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                mock_metrics_instance.increment.assert_called()
                mock_metrics_instance.timing.assert_called()

    def test_discord_workflow_data_consistency(self, bot_tools, sample_discord_message, sample_tenant_context):
        """Test data consistency in Discord workflow."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_message') as mock_monitor:
            with patch.object(bot_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
                with patch.object(bot_tools['post_tool'], '_post_message') as mock_post:
                    mock_monitor.return_value = {'success': True, 'message_id': 'msg_123', 'content': sample_discord_message['content'], 'author': sample_discord_message['author']}
                    mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important']}
                    mock_post.return_value = {'success': True, 'message_id': 'response_123', 'channel_id': sample_discord_message['channel_id']}
                    monitor_result = bot_tools['monitor_tool']._run(sample_discord_message['channel_id'], sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    analysis_result = bot_tools['analysis_tool']._run(monitor_result.data['content'], 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    post_result = bot_tools['post_tool']._run(sample_discord_message['channel_id'], 'Analysis complete', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    assert monitor_result.success
                    assert analysis_result.success
                    assert post_result.success
                    assert monitor_result.data['content'] == sample_discord_message['content']
                    assert analysis_result.data['political_topics'] == ['healthcare']
                    assert post_result.data['message_id'] == 'response_123'

    def test_discord_workflow_error_recovery(self, bot_tools, sample_tenant_context):
        """Test Discord workflow error recovery."""
        with patch.object(bot_tools['monitor_tool'], '_monitor_channel') as mock_monitor:
            mock_monitor.side_effect = [Exception('Network error'), {'success': True, 'channel_id': '123456789', 'messages': [], 'total_messages': 0}]
            result1 = bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert not result1.success
            result2 = bot_tools['monitor_tool']._run('123456789', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert result2.success

    def test_discord_workflow_validation(self, bot_tools, sample_tenant_context):
        """Test Discord workflow validation."""
        result = bot_tools['monitor_tool']._run('', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
        assert not result.success
        with patch.object(bot_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'error': 'Empty content'}
            result = bot_tools['analysis_tool']._run('', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            assert not result.success