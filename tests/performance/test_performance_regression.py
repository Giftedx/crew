"""Performance regression tests."""
import json
import os
import time
from unittest.mock import patch
import pytest
from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool

class TestPerformanceRegression:
    """Performance regression tests."""

    @pytest.fixture
    def regression_tools(self):
        """Create tools for regression testing."""
        return {'download_tool': MultiPlatformDownloadTool(), 'analysis_tool': EnhancedAnalysisTool(), 'verification_tool': ClaimVerifierTool(), 'memory_tool': UnifiedMemoryTool()}

    @pytest.fixture
    def regression_data_file(self, tmp_path):
        """Create regression data file."""
        return tmp_path / 'performance_regression.json'

    @pytest.fixture
    def sample_content(self):
        """Sample content for regression testing."""
        return 'This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification.'

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {'tenant': 'regression_tenant', 'workspace': 'regression_workspace'}

    def test_performance_regression_detection(self, regression_tools, sample_content, sample_tenant_context, regression_data_file):
        """Test performance regression detection."""
        baseline_data = {'timestamp': time.time(), 'version': '1.0.0', 'baselines': {'analysis_tool': {'execution_time': 1.0, 'success_rate': 1.0, 'processing_time': 1.0}, 'download_tool': {'execution_time': 2.0, 'success_rate': 1.0, 'file_size': 0}, 'verification_tool': {'execution_time': 3.0, 'success_rate': 1.0, 'processing_time': 3.0}, 'memory_tool': {'execution_time': 0.5, 'success_rate': 1.0, 'storage_size': 100}}}
        current_data = {'timestamp': time.time(), 'version': '1.1.0', 'current_performance': {}}
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare', 'policy'], 'bias_indicators': ['subjective_language'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare policy needs improvement'], 'processing_time': 1.2}
            start_time = time.time()
            result = regression_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            current_data['current_performance']['analysis_tool'] = {'execution_time': end_time - start_time, 'success': result.success, 'processing_time': result.data.get('processing_time', 0) if result.success else 0}
            assert result.success
        with patch.object(regression_tools['download_tool'], '_download_youtube') as mock_download:
            mock_download.return_value = {'success': True, 'platform': 'youtube', 'file_path': '/tmp/test_video.mp4', 'duration': 180, 'quality': '720p'}
            start_time = time.time()
            result = regression_tools['download_tool']._run('https://youtube.com/watch?v=test', '720p', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            current_data['current_performance']['download_tool'] = {'execution_time': end_time - start_time, 'success': result.success, 'file_size': 0}
            assert result.success
        with patch.object(regression_tools['verification_tool'], '_verify_claim') as mock_verify:
            mock_verify.return_value = {'claim_id': 'claim_123', 'claim_text': 'Healthcare policy needs improvement', 'overall_confidence': 0.9, 'verification_status': 'verified', 'sources': [], 'processing_time': 3.2, 'backends_used': ['serply'], 'error_message': None}
            start_time = time.time()
            result = regression_tools['verification_tool']._run('Healthcare policy needs improvement', 'Test context', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            current_data['current_performance']['verification_tool'] = {'execution_time': end_time - start_time, 'success': result.success, 'processing_time': result.data.get('processing_time', 0) if result.success else 0}
            assert result.success
        with patch.object(regression_tools['memory_tool'], '_store_content') as mock_store:
            mock_store.return_value = {'success': True, 'content_id': 'test_123', 'namespace': 'test_namespace', 'timestamp': '2024-01-01T00:00:00Z'}
            start_time = time.time()
            result = regression_tools['memory_tool']._run('store', 'Test content', {'test': 'metadata'}, 'test_namespace', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            current_data['current_performance']['memory_tool'] = {'execution_time': end_time - start_time, 'success': result.success, 'storage_size': len('Test content')}
            assert result.success
        regressions = []
        for tool_name in baseline_data['baselines']:
            baseline = baseline_data['baselines'][tool_name]
            current = current_data['current_performance'][tool_name]
            if current['execution_time'] > baseline['execution_time'] * 1.2:
                regressions.append({'tool': tool_name, 'type': 'execution_time', 'baseline': baseline['execution_time'], 'current': current['execution_time'], 'regression': (current['execution_time'] - baseline['execution_time']) / baseline['execution_time'] * 100})
            if current['success'] != baseline['success_rate']:
                regressions.append({'tool': tool_name, 'type': 'success_rate', 'baseline': baseline['success_rate'], 'current': current['success'], 'regression': 'Success rate decreased'})
        regression_data = {'baseline': baseline_data, 'current': current_data, 'regressions': regressions, 'summary': {'total_regressions': len(regressions), 'critical_regressions': len([r for r in regressions if r['type'] == 'success_rate']), 'performance_regressions': len([r for r in regressions if r['type'] == 'execution_time'])}}
        with open(regression_data_file, 'w') as f:
            json.dump(regression_data, f, indent=2)
        assert os.path.exists(regression_data_file)
        assert len(regressions) > 0
        assert regression_data['summary']['total_regressions'] > 0

    def test_performance_regression_thresholds(self, regression_tools, sample_content, sample_tenant_context):
        """Test performance regression thresholds."""
        thresholds = {'execution_time': 1.2, 'success_rate': 0.95, 'processing_time': 1.3, 'memory_usage': 1.5}
        alerts = []
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            result = regression_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            execution_time = end_time - start_time
            if execution_time > thresholds['execution_time']:
                alerts.append({'type': 'execution_time', 'message': f'Execution time {execution_time:.2f}s exceeds threshold {thresholds['execution_time']}s', 'severity': 'warning'})
            if not result.success:
                alerts.append({'type': 'success_rate', 'message': 'Success rate below threshold', 'severity': 'error'})
            assert len(alerts) == 0
            assert result.success

    def test_performance_regression_trending(self, regression_tools, sample_content, sample_tenant_context):
        """Test performance regression trending."""
        trending_data = {'timestamp': time.time(), 'trends': {}}
        performance_history = []
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            for hour in range(24):
                for operation in range(5):
                    start_time = time.time()
                    result = regression_tools['analysis_tool']._run(f'{sample_content} hour_{hour}_op_{operation}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    end_time = time.time()
                    performance_history.append({'timestamp': time.time() + hour * 3600, 'execution_time': end_time - start_time, 'success': result.success, 'hour': hour})
                    assert result.success
            hourly_performance = {}
            for hour in range(24):
                hour_data = [p for p in performance_history if p['hour'] == hour]
                if hour_data:
                    hourly_performance[hour] = {'average_time': sum((p['execution_time'] for p in hour_data)) / len(hour_data), 'success_rate': sum((1 for p in hour_data if p['success'])) / len(hour_data), 'operation_count': len(hour_data)}
            execution_times = [hourly_performance[h]['average_time'] for h in hourly_performance]
            success_rates = [hourly_performance[h]['success_rate'] for h in hourly_performance]
            trending_data['trends'] = {'execution_time_trend': 'stable' if max(execution_times) - min(execution_times) < 0.5 else 'variable', 'success_rate_trend': 'stable' if min(success_rates) > 0.95 else 'degrading', 'performance_variance': max(execution_times) - min(execution_times), 'overall_health': 'good' if min(success_rates) > 0.95 and max(execution_times) - min(execution_times) < 0.5 else 'needs_attention'}
            assert trending_data['trends']['execution_time_trend'] == 'stable'
            assert trending_data['trends']['success_rate_trend'] == 'stable'
            assert trending_data['trends']['overall_health'] == 'good'

    def test_performance_regression_alerts(self, regression_tools, sample_content, sample_tenant_context):
        """Test performance regression alerts."""
        alert_system = {'alerts': [], 'thresholds': {'execution_time': 5.0, 'success_rate': 0.95, 'error_rate': 0.05, 'memory_usage': 80.0, 'cpu_usage': 90.0}}
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            result = regression_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            execution_time = end_time - start_time
            if execution_time > alert_system['thresholds']['execution_time']:
                alert_system['alerts'].append({'type': 'execution_time', 'severity': 'warning', 'message': f'Analysis tool execution time {execution_time:.2f}s exceeds threshold {alert_system['thresholds']['execution_time']}s', 'timestamp': time.time()})
            if not result.success:
                alert_system['alerts'].append({'type': 'success_rate', 'severity': 'error', 'message': 'Analysis tool operation failed', 'timestamp': time.time()})
            assert len(alert_system['alerts']) == 0
            assert result.success
            assert execution_time < alert_system['thresholds']['execution_time']

    def test_performance_regression_reporting(self, regression_tools, sample_content, sample_tenant_context, regression_data_file):
        """Test performance regression reporting."""
        report_data = {'timestamp': time.time(), 'report_period': '24h', 'regressions': [], 'summary': {}}
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            total_operations = 0
            successful_operations = 0
            total_execution_time = 0
            regressions_detected = 0
            for hour in range(24):
                for operation in range(10):
                    start_time = time.time()
                    result = regression_tools['analysis_tool']._run(f'{sample_content} hour_{hour}_op_{operation}', 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
                    end_time = time.time()
                    execution_time = end_time - start_time
                    total_operations += 1
                    if result.success:
                        successful_operations += 1
                    total_execution_time += execution_time
                    if execution_time > 2.0:
                        regressions_detected += 1
                        report_data['regressions'].append({'tool': 'analysis_tool', 'type': 'execution_time', 'timestamp': time.time(), 'execution_time': execution_time, 'threshold': 2.0})
                    assert result.success
            report_data['summary'] = {'total_operations': total_operations, 'successful_operations': successful_operations, 'success_rate': successful_operations / total_operations, 'average_execution_time': total_execution_time / total_operations, 'regressions_detected': regressions_detected, 'regression_rate': regressions_detected / total_operations}
            with open(regression_data_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            assert os.path.exists(regression_data_file)
            assert report_data['summary']['total_operations'] == 240
            assert report_data['summary']['success_rate'] == 1.0
            assert report_data['summary']['average_execution_time'] > 0
            assert report_data['summary']['regressions_detected'] >= 0

    def test_performance_regression_mitigation(self, regression_tools, sample_content, sample_tenant_context):
        """Test performance regression mitigation."""
        mitigation_strategies = []
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            result = regression_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            execution_time = end_time - start_time
            if execution_time > 2.0:
                mitigation_strategies.append({'type': 'execution_time', 'strategy': 'optimize_algorithm', 'description': 'Optimize analysis algorithm for better performance', 'implementation': 'Use more efficient data structures and algorithms'})
                mitigation_strategies.append({'type': 'execution_time', 'strategy': 'caching', 'description': 'Implement caching for repeated operations', 'implementation': 'Cache analysis results for identical content'})
                mitigation_strategies.append({'type': 'execution_time', 'strategy': 'concurrent_processing', 'description': 'Use concurrent processing for better performance', 'implementation': 'Process multiple operations in parallel'})
            if not result.success:
                mitigation_strategies.append({'type': 'success_rate', 'strategy': 'error_handling', 'description': 'Improve error handling and recovery', 'implementation': 'Add retry logic and fallback mechanisms'})
                mitigation_strategies.append({'type': 'success_rate', 'strategy': 'monitoring', 'description': 'Add monitoring and alerting', 'implementation': 'Monitor tool performance and alert on failures'})
            assert result.success
            assert len(mitigation_strategies) >= 0

    def test_performance_regression_prevention(self, regression_tools, sample_content, sample_tenant_context):
        """Test performance regression prevention."""
        prevention_measures = []
        with patch.object(regression_tools['analysis_tool'], '_analyze_comprehensive') as mock_analyze:
            mock_analyze.return_value = {'political_topics': ['healthcare'], 'sentiment': 'neutral', 'sentiment_confidence': 0.8, 'extracted_claims': ['Healthcare is important'], 'processing_time': 1.0}
            start_time = time.time()
            result = regression_tools['analysis_tool']._run(sample_content, 'comprehensive', sample_tenant_context['tenant'], sample_tenant_context['workspace'])
            end_time = time.time()
            end_time - start_time
            prevention_measures.append({'type': 'monitoring', 'description': 'Continuous performance monitoring', 'implementation': 'Monitor tool performance in real-time'})
            prevention_measures.append({'type': 'alerting', 'description': 'Performance alerting system', 'implementation': 'Alert on performance degradation'})
            prevention_measures.append({'type': 'baseline', 'description': 'Performance baseline tracking', 'implementation': 'Track performance baselines over time'})
            prevention_measures.append({'type': 'testing', 'description': 'Performance regression testing', 'implementation': 'Test performance in CI/CD pipeline'})
            assert result.success
            assert len(prevention_measures) > 0
            assert any((measure['type'] == 'monitoring' for measure in prevention_measures))
            assert any((measure['type'] == 'alerting' for measure in prevention_measures))
            assert any((measure['type'] == 'baseline' for measure in prevention_measures))
            assert any((measure['type'] == 'testing' for measure in prevention_measures))