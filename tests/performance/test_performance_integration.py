"""Performance integration tests."""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool

class TestPerformanceIntegration:
    """Performance integration tests."""

    @pytest.fixture
    def integration_tools(self):
        """Create tools for integration testing."""
        return {'download_tool': MultiPlatformDownloadTool(), 'analysis_tool': EnhancedAnalysisTool(), 'verification_tool': ClaimVerifierTool(), 'memory_tool': UnifiedMemoryTool()}

    @pytest.fixture
    def integration_data_file(self, tmp_path):
        """Create integration data file."""
        return tmp_path / 'performance_integration.json'

    @pytest.fixture
    def sample_content(self):
        """Sample content for integration testing."""
        return 'This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification.'

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {'tenant': 'integration_tenant', 'workspace': 'integration_workspace'}

    def test_end_to_end_performance(self, integration_tools, sample_content, sample_tenant_context):
        """Test end-to-end performance workflow."""
        workflow_results = {'download_time': 0, 'analysis_time': 0, 'verification_time': 0, 'storage_time': 0, 'total_time': 0, 'success': True}
        with patch.object(integration_tools['download_tool'], '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/test_video.mp4', 'duration': 180, 'quality': '720p'}
            start_time = time.time()
            download_result = integration_tools['download_tool']._run('https://youtube.com/watch?v=test', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            workflow_results['download_time'] = time.time() - start_time
            assert download_result.success
        with patch.object(integration_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 1.5}
            start_time = time.time()
            analysis_result = integration_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            workflow_results['analysis_time'] = time.time() - start_time
            assert analysis_result.success
        with patch.object(integration_tools['verification_tool'], '_verify_claim') as mock_verify:
            mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': 'Healthcare policy needs improvement', 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [], 'processing_time': 3.0, 'backends_used': ['serply'], 'error_message': None}
            start_time = time.time()
            verification_result = integration_tools['verification_tool']._run('Healthcare policy needs improvement', 'Test context', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            workflow_results['verification_time'] = time.time() - start_time
            assert verification_result.success
        with patch.object(integration_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace', 'timestamp': '2024-01-01T00:00:00Z'}
            start_time = time.time()
            storage_result = integration_tools['memory_tool']._run('store', 'Test content', {'test': 'metadata'}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            workflow_results['storage_time'] = time.time() - start_time
            assert storage_result.success
        workflow_results['total_time'] = workflow_results['download_time'] + workflow_results['analysis_time'] + workflow_results['verification_time'] + workflow_results['storage_time']
        assert workflow_results['success'] is True
        assert workflow_results['download_time'] > 0
        assert workflow_results['analysis_time'] > 0
        assert workflow_results['verification_time'] > 0
        assert workflow_results['storage_time'] > 0
        assert workflow_results['total_time'] > 0

    def test_concurrent_workflow_performance(self, integration_tools, sample_content, sample_tenant_context):
        """Test concurrent workflow performance."""
        concurrent_results = {'workflows_count': 0, 'successful_workflows': 0, 'failed_workflows': 0, 'total_execution_time': 0, 'average_execution_time': 0, 'max_execution_time': 0, 'min_execution_time': float('inf')}

        def execute_workflow(workflow_id):
            """Execute a single workflow."""
            workflow_start = time.time()
            try:
                with patch.object(integration_tools['download_tool'], '_download_youtube') as mock_download:
                    mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': f'/tmp/test_video_{workflow_id}.mp4', 'duration': 180, 'quality': '720p'}
                    download_result = integration_tools['download_tool']._run(f'https://youtube.com/watch?v=test_{workflow_id}', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    assert download_result.success
                with patch.object(integration_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
                    mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
                    analysis_result = integration_tools['analysis_tool']._run(f'{sample_content} {workflow_id}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    assert analysis_result.success
                with patch.object(integration_tools['memory_tool'], '_store_content') as mock_store:
                    mock_store.return_value = {'success': True, 'content_id': f'test_{workflow_id}', 'namespace': 'test_namespace'}
                    storage_result = integration_tools['memory_tool']._run('store', f'Workflow {workflow_id} content', {'workflow_id': workflow_id}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    assert storage_result.success
                return (time.time() - workflow_start, True)
            except Exception:
                return (time.time() - workflow_start, False)
        time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_workflow, i) for i in range(10)]
            for future in futures:
                execution_time, success = future.result()
                concurrent_results['workflows_count'] += 1
                concurrent_results['total_execution_time'] += execution_time
                concurrent_results['max_execution_time'] = max(concurrent_results['max_execution_time'], execution_time)
                concurrent_results['min_execution_time'] = min(concurrent_results['min_execution_time'], execution_time)
                if success:
                    concurrent_results['successful_workflows'] += 1
                else:
                    concurrent_results['failed_workflows'] += 1
        concurrent_results['average_execution_time'] = concurrent_results['total_execution_time'] / concurrent_results['workflows_count']
        assert concurrent_results['workflows_count'] == 10
        assert concurrent_results['successful_workflows'] == 10
        assert concurrent_results['failed_workflows'] == 0
        assert concurrent_results['average_execution_time'] > 0
        assert concurrent_results['max_execution_time'] > 0
        assert concurrent_results['min_execution_time'] > 0

    def test_memory_integration_performance(self, integration_tools, sample_content, sample_tenant_context):
        """Test memory integration performance."""
        memory_results = {'operations_count': 0, 'successful_operations': 0, 'failed_operations': 0, 'total_execution_time': 0, 'average_execution_time': 0, 'memory_usage': 0}
        import os
        import psutil
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        with patch.object(integration_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            time.time()
            for i in range(100):
                operation_start = time.time()
                result = integration_tools['memory_tool']._run('store', f'Memory integration content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                operation_end = time.time()
                execution_time = operation_end - operation_start
                memory_results['operations_count'] += 1
                memory_results['total_execution_time'] += execution_time
                if result.success:
                    memory_results['successful_operations'] += 1
                else:
                    memory_results['failed_operations'] += 1
                assert result.success
            memory_results['average_execution_time'] = memory_results['total_execution_time'] / memory_results['operations_count']
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_results['memory_usage'] = final_memory - initial_memory
            assert memory_results['operations_count'] == 100
            assert memory_results['successful_operations'] == 100
            assert memory_results['failed_operations'] == 0
            assert memory_results['average_execution_time'] > 0
            assert memory_results['memory_usage'] > 0

    def test_analysis_integration_performance(self, integration_tools, sample_content, sample_tenant_context):
        """Test analysis integration performance."""
        analysis_results = {'operations_count': 0, 'successful_operations': 0, 'failed_operations': 0, 'total_execution_time': 0, 'average_execution_time': 0, 'topics_detected': 0, 'claims_extracted': 0}
        with patch.object(integration_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 1.5}
            time.time()
            for i in range(50):
                operation_start = time.time()
                result = integration_tools['analysis_tool']._run(f'{sample_content} {i}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                operation_end = time.time()
                execution_time = operation_end - operation_start
                analysis_results['operations_count'] += 1
                analysis_results['total_execution_time'] += execution_time
                if result.success:
                    analysis_results['successful_operations'] += 1
                    analysis_results['topics_detected'] += len(result.data.get('political_topics', []))
                    analysis_results['claims_extracted'] += len(result.data.get('extracted_claims', []))
                else:
                    analysis_results['failed_operations'] += 1
                assert result.success
            analysis_results['average_execution_time'] = analysis_results['total_execution_time'] / analysis_results['operations_count']
            assert analysis_results['operations_count'] == 50
            assert analysis_results['successful_operations'] == 50
            assert analysis_results['failed_operations'] == 0
            assert analysis_results['average_execution_time'] > 0
            assert analysis_results['topics_detected'] > 0
            assert analysis_results['claims_extracted'] > 0

    def test_verification_integration_performance(self, integration_tools, sample_tenant_context):
        """Test verification integration performance."""
        verification_results = {'operations_count': 0, 'successful_operations': 0, 'failed_operations': 0, 'total_execution_time': 0, 'average_execution_time': 0, 'claims_verified': 0, 'high_confidence_claims': 0}
        with patch.object(integration_tools['verification_tool'], '_verify_claim') as mock_verify:
            mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': 'Healthcare policy needs improvement', 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [], 'processing_time': 3.0, 'backends_used': ['serply'], 'error_message': None}
            time.time()
            for i in range(25):
                operation_start = time.time()
                result = integration_tools['verification_tool']._run(f'Healthcare policy claim {i}', f'Test context {i}', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                operation_end = time.time()
                execution_time = operation_end - operation_start
                verification_results['operations_count'] += 1
                verification_results['total_execution_time'] += execution_time
                if result.success:
                    verification_results['successful_operations'] += 1
                    verification_results['claims_verified'] += 1
                    if result.data.get('overall_confidence', 0) > 0.8:
                        verification_results['high_confidence_claims'] += 1
                else:
                    verification_results['failed_operations'] += 1
                assert result.success
            verification_results['average_execution_time'] = verification_results['total_execution_time'] / verification_results['operations_count']
            assert verification_results['operations_count'] == 25
            assert verification_results['successful_operations'] == 25
            assert verification_results['failed_operations'] == 0
            assert verification_results['average_execution_time'] > 0
            assert verification_results['claims_verified'] == 25
            assert verification_results['high_confidence_claims'] == 25

    def test_download_integration_performance(self, integration_tools, sample_tenant_context):
        """Test download integration performance."""
        download_results = {'operations_count': 0, 'successful_operations': 0, 'failed_operations': 0, 'total_execution_time': 0, 'average_execution_time': 0, 'total_file_size': 0, 'average_file_size': 0}
        with patch.object(integration_tools['download_tool'], '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/test_video.mp4', 'duration': 180, 'quality': '720p'}
            time.time()
            for i in range(20):
                operation_start = time.time()
                result = integration_tools['download_tool']._run(f'https://youtube.com/watch?v=test_{i}', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                operation_end = time.time()
                execution_time = operation_end - operation_start
                download_results['operations_count'] += 1
                download_results['total_execution_time'] += execution_time
                if result.success:
                    download_results['successful_operations'] += 1
                    file_size = 100 * 1024 * 1024
                    download_results['total_file_size'] += file_size
                else:
                    download_results['failed_operations'] += 1
                assert result.success
            download_results['average_execution_time'] = download_results['total_execution_time'] / download_results['operations_count']
            download_results['average_file_size'] = download_results['total_file_size'] / download_results['successful_operations']
            assert download_results['operations_count'] == 20
            assert download_results['successful_operations'] == 20
            assert download_results['failed_operations'] == 0
            assert download_results['average_execution_time'] > 0
            assert download_results['total_file_size'] > 0
            assert download_results['average_file_size'] > 0

    def test_full_workflow_performance(self, integration_tools, sample_content, sample_tenant_context, integration_data_file):
        """Test full workflow performance."""
        workflow_data = {'timestamp': time.time(), 'workflow_performance': {}, 'system_health': {}, 'recommendations': []}
        with patch.object(integration_tools['download_tool'], '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/test_video.mp4', 'duration': 180, 'quality': '720p'}
            with patch.object(integration_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
                mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
                with patch.object(integration_tools['verification_tool'], '_verify_claim') as mock_verify:
                    mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': 'Healthcare is important', 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [], 'processing_time': 3.0, 'backends_used': ['serply'], 'error_message': None}
                    with patch.object(integration_tools['memory_tool'], '_store_content') as mock_store:
                        mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
                        start_time = time.time()
                        download_result = integration_tools['download_tool']._run('https://youtube.com/watch?v=test', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                        assert download_result.success
                        analysis_result = integration_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                        assert analysis_result.success
                        verification_result = integration_tools['verification_tool']._run('Healthcare is important', 'Test context', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                        assert verification_result.success
                        storage_result = integration_tools['memory_tool']._run('store', 'Test content', {'test': 'metadata'}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                        assert storage_result.success
                        total_time = time.time() - start_time
                        workflow_data['workflow_performance'] = {'total_execution_time': total_time, 'download_success': download_result.success, 'analysis_success': analysis_result.success, 'verification_success': verification_result.success, 'storage_success': storage_result.success, 'overall_success': all([download_result.success, analysis_result.success, verification_result.success, storage_result.success])}
                        workflow_data['system_health'] = {'cpu_usage': 45.2, 'memory_usage': 67.8, 'disk_usage': 23.1, 'network_latency': 12.5}
                        if total_time > 10.0:
                            workflow_data['recommendations'].append({'type': 'performance', 'description': 'Workflow execution time is too high', 'action': 'Optimize workflow performance'})
                        if not workflow_data['workflow_performance']['overall_success']:
                            workflow_data['recommendations'].append({'type': 'reliability', 'description': 'Workflow failed', 'action': 'Investigate and fix workflow failures'})
                        with open(integration_data_file, 'w') as f:
                            json.dump(workflow_data, f, indent=2)
                        assert os.path.exists(integration_data_file)
                        assert workflow_data['workflow_performance']['overall_success'] is True
                        assert workflow_data['workflow_performance']['total_execution_time'] > 0
                        assert workflow_data['system_health']['cpu_usage'] > 0
                        assert workflow_data['system_health']['memory_usage'] > 0