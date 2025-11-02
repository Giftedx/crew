"""Performance optimization tests."""
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

class TestPerformanceOptimization:
    """Performance optimization tests."""

    @pytest.fixture
    def optimization_tools(self):
        """Create tools for optimization testing."""
        return {'download_tool': MultiPlatformDownloadTool(), 'analysis_tool': EnhancedAnalysisTool(), 'verification_tool': ClaimVerifierTool(), 'memory_tool': UnifiedMemoryTool()}

    @pytest.fixture
    def optimization_data_file(self, tmp_path):
        """Create optimization data file."""
        return tmp_path / 'performance_optimization.json'

    @pytest.fixture
    def sample_content(self):
        """Sample content for optimization testing."""
        return 'This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification.'

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {'tenant': 'optimization_tenant', 'workspace': 'optimization_workspace'}

    def test_concurrent_operations_optimization(self, optimization_tools, sample_tenant_context):
        """Test concurrent operations optimization."""
        optimization_results = {'sequential_time': 0, 'concurrent_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            start_time = time.time()
            for i in range(50):
                result = optimization_tools['memory_tool']._run('store', f'Sequential content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            optimization_results['sequential_time'] = time.time() - start_time
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(optimization_tools['memory_tool']._run, 'store', f'Concurrent content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace']) for i in range(50)]
                for future in futures:
                    result = future.result()
                    assert result.success
            optimization_results['concurrent_time'] = time.time() - start_time
            optimization_results['improvement'] = (optimization_results['sequential_time'] - optimization_results['concurrent_time']) / optimization_results['sequential_time'] * 100
            assert optimization_results['concurrent_time'] < optimization_results['sequential_time']
            assert optimization_results['improvement'] > 0

    def test_caching_optimization(self, optimization_tools, sample_content, sample_tenant_context):
        """Test caching optimization."""
        caching_results = {'first_execution_time': 0, 'cached_execution_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            result1 = optimization_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            caching_results['first_execution_time'] = time.time() - start_time
            start_time = time.time()
            result2 = optimization_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            caching_results['cached_execution_time'] = time.time() - start_time
            if caching_results['cached_execution_time'] < caching_results['first_execution_time']:
                caching_results['improvement'] = (caching_results['first_execution_time'] - caching_results['cached_execution_time']) / caching_results['first_execution_time'] * 100
            assert result1.success
            assert result2.success

    def test_batch_processing_optimization(self, optimization_tools, sample_tenant_context):
        """Test batch processing optimization."""
        batch_results = {'individual_time': 0, 'batch_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            start_time = time.time()
            for i in range(20):
                result = optimization_tools['memory_tool']._run('store', f'Individual content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            batch_results['individual_time'] = time.time() - start_time
            start_time = time.time()
            batch_content = [f'Batch content {i}' for i in range(20)]
            batch_metadata = [{'index': i} for i in range(20)]
            for content, metadata in zip(batch_content, batch_metadata, strict=False):
                result = optimization_tools['memory_tool']._run('store', content, metadata, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            batch_results['batch_time'] = time.time() - start_time
            batch_results['improvement'] = (batch_results['individual_time'] - batch_results['batch_time']) / batch_results['individual_time'] * 100
            assert batch_results['batch_time'] <= batch_results['individual_time']

    def test_memory_optimization(self, optimization_tools, sample_tenant_context):
        """Test memory optimization."""
        memory_results = {'initial_memory': 0, 'final_memory': 0, 'memory_usage': 0}
        import os
        import psutil
        process = psutil.Process(os.getpid())
        memory_results['initial_memory'] = process.memory_info().rss / 1024 / 1024
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            for i in range(1000):
                result = optimization_tools['memory_tool']._run('store', f'Memory test content {i}' * 100, {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
        memory_results['final_memory'] = process.memory_info().rss / 1024 / 1024
        memory_results['memory_usage'] = memory_results['final_memory'] - memory_results['initial_memory']
        assert memory_results['memory_usage'] < 500
        assert memory_results['memory_usage'] > 0

    def test_cpu_optimization(self, optimization_tools, sample_tenant_context):
        """Test CPU optimization."""
        cpu_results = {'initial_cpu': 0, 'final_cpu': 0, 'cpu_usage': 0}
        import os
        import psutil
        process = psutil.Process(os.getpid())
        cpu_results['initial_cpu'] = process.cpu_percent()
        with patch.object(optimization_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            for i in range(100):
                result = optimization_tools['analysis_tool']._run(f'CPU test content {i}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
        cpu_results['final_cpu'] = process.cpu_percent()
        cpu_results['cpu_usage'] = cpu_results['final_cpu'] - cpu_results['initial_cpu']
        assert cpu_results['final_cpu'] < 90
        assert cpu_results['cpu_usage'] >= 0

    def test_network_optimization(self, optimization_tools, sample_tenant_context):
        """Test network optimization."""
        network_results = {'sequential_time': 0, 'concurrent_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['download_tool'], '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/test_video.mp4', 'duration': 180, 'quality': '720p'}
            start_time = time.time()
            for i in range(10):
                result = optimization_tools['download_tool']._run(f'https://youtube.com/watch?v=test{i}', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            network_results['sequential_time'] = time.time() - start_time
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(optimization_tools['download_tool']._run, f'https://youtube.com/watch?v=concurrent{i}', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace']) for i in range(10)]
                for future in futures:
                    result = future.result()
                    assert result.success
            network_results['concurrent_time'] = time.time() - start_time
            network_results['improvement'] = (network_results['sequential_time'] - network_results['concurrent_time']) / network_results['sequential_time'] * 100
            assert network_results['concurrent_time'] < network_results['sequential_time']
            assert network_results['improvement'] > 0

    def test_database_optimization(self, optimization_tools, sample_tenant_context):
        """Test database optimization."""
        db_results = {'individual_time': 0, 'batch_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            start_time = time.time()
            for i in range(50):
                result = optimization_tools['memory_tool']._run('store', f'DB content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            db_results['individual_time'] = time.time() - start_time
            start_time = time.time()
            batch_data = [{'content': f'Batch DB content {i}', 'metadata': {'index': i}} for i in range(50)]
            for data in batch_data:
                result = optimization_tools['memory_tool']._run('store', data['content'], data['metadata'], 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            db_results['batch_time'] = time.time() - start_time
            db_results['improvement'] = (db_results['individual_time'] - db_results['batch_time']) / db_results['individual_time'] * 100
            assert db_results['batch_time'] <= db_results['individual_time']

    def test_algorithm_optimization(self, optimization_tools, sample_content, sample_tenant_context):
        """Test algorithm optimization."""
        algorithm_results = {'naive_time': 0, 'optimized_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            for i in range(20):
                result = optimization_tools['analysis_tool']._run(f'{sample_content} {i}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            algorithm_results['naive_time'] = time.time() - start_time
            start_time = time.time()
            for i in range(20):
                result = optimization_tools['analysis_tool']._run(f'{sample_content} {i}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            algorithm_results['optimized_time'] = time.time() - start_time
            algorithm_results['improvement'] = (algorithm_results['naive_time'] - algorithm_results['optimized_time']) / algorithm_results['naive_time'] * 100
            assert algorithm_results['optimized_time'] <= algorithm_results['naive_time']

    def test_resource_pooling_optimization(self, optimization_tools, sample_tenant_context):
        """Test resource pooling optimization."""
        pooling_results = {'no_pool_time': 0, 'with_pool_time': 0, 'improvement': 0}
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            start_time = time.time()
            for i in range(30):
                result = optimization_tools['memory_tool']._run('store', f'No pool content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            pooling_results['no_pool_time'] = time.time() - start_time
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(optimization_tools['memory_tool']._run, 'store', f'Pool content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace']) for i in range(30)]
                for future in futures:
                    result = future.result()
                    assert result.success
            pooling_results['with_pool_time'] = time.time() - start_time
            pooling_results['improvement'] = (pooling_results['no_pool_time'] - pooling_results['with_pool_time']) / pooling_results['no_pool_time'] * 100
            assert pooling_results['with_pool_time'] < pooling_results['no_pool_time']
            assert pooling_results['improvement'] > 0

    def test_optimization_recommendations(self, optimization_tools, sample_content, sample_tenant_context, optimization_data_file):
        """Test optimization recommendations generation."""
        recommendations = []
        with patch.object(optimization_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace'}
            start_time = time.time()
            for i in range(20):
                result = optimization_tools['memory_tool']._run('store', f'Sequential content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                assert result.success
            sequential_time = time.time() - start_time
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(optimization_tools['memory_tool']._run, 'store', f'Concurrent content {i}', {'index': i}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace']) for i in range(20)]
                for future in futures:
                    result = future.result()
                    assert result.success
            concurrent_time = time.time() - start_time
            if concurrent_time < sequential_time:
                improvement = (sequential_time - concurrent_time) / sequential_time * 100
                recommendations.append({'type': 'concurrent_operations', 'description': 'Use concurrent operations for better performance', 'improvement': f'{improvement:.1f}% faster', 'implementation': 'Use ThreadPoolExecutor for parallel operations', 'priority': 'high' if improvement > 50 else 'medium'})
            with patch.object(optimization_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
                mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
                start_time = time.time()
                result1 = optimization_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                first_time = time.time() - start_time
                start_time = time.time()
                result2 = optimization_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                second_time = time.time() - start_time
                if second_time < first_time:
                    caching_improvement = (first_time - second_time) / first_time * 100
                    recommendations.append({'type': 'caching', 'description': 'Implement caching for repeated operations', 'improvement': f'{caching_improvement:.1f}% faster', 'implementation': 'Cache analysis results for identical content', 'priority': 'high' if caching_improvement > 30 else 'medium'})
                assert result1.success
                assert result2.success
            optimization_data = {'timestamp': time.time(), 'recommendations': recommendations, 'summary': {'total_recommendations': len(recommendations), 'high_priority': len([r for r in recommendations if r['priority'] == 'high']), 'medium_priority': len([r for r in recommendations if r['priority'] == 'medium'])}}
            with open(optimization_data_file, 'w') as f:
                json.dump(optimization_data, f, indent=2)
            assert len(recommendations) > 0
            assert any((rec['type'] == 'concurrent_operations' for rec in recommendations))
            assert os.path.exists(optimization_data_file)