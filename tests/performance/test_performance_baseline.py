"""Performance baseline and monitoring tests."""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest

from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool


class TestPerformanceBaseline:
    """Performance baseline and monitoring tests."""

    @pytest.fixture
    def baseline_tools(self):
        """Create tools for baseline testing."""
        return {
            "download_tool": MultiPlatformDownloadTool(),
            "analysis_tool": EnhancedAnalysisTool(),
            "verification_tool": ClaimVerifierTool(),
            "memory_tool": UnifiedMemoryTool(),
        }

    @pytest.fixture
    def baseline_data_file(self, tmp_path):
        """Create baseline data file."""
        return tmp_path / "performance_baseline.json"

    @pytest.fixture
    def sample_content(self):
        """Sample content for baseline testing."""
        return "This is a comprehensive political statement about healthcare policy that requires detailed analysis and verification."

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "baseline_tenant", "workspace": "baseline_workspace"}

    def test_establish_performance_baseline(
        self, baseline_tools, sample_content, sample_tenant_context, baseline_data_file
    ):
        """Establish performance baseline for all tools."""
        baseline_data = {"timestamp": time.time(), "version": "1.0.0", "baselines": {}}
        with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare", "policy"],
                "bias_indicators": ["subjective_language"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare policy needs improvement"],
                "processing_time": 1.5,
            }
            start_time = time.time()
            result = baseline_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            baseline_data["baselines"]["analysis_tool"] = {
                "execution_time": end_time - start_time,
                "success": result.success,
                "processing_time": result.data.get("processing_time", 0) if result.success else 0,
            }
            assert result.success
        with patch.object(baseline_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {
                "success": True,
                "platform": "youtube",
                "file_path": "/tmp/test_video.mp4",
                "duration": 180,
                "quality": "720p",
            }
            start_time = time.time()
            result = baseline_tools["download_tool"]._run(
                "https://youtube.com/watch?v=test",
                "720p",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            end_time = time.time()
            baseline_data["baselines"]["download_tool"] = {
                "execution_time": end_time - start_time,
                "success": result.success,
                "file_size": 0,
            }
            assert result.success
        with patch.object(baseline_tools["verification_tool"], "_verify_claim") as mock_verify:
            mock_verify.return_value = {
                "claim_id": "claim_123",
                "claim_text": "Healthcare policy needs improvement",
                "overall_confidence": 0.9,
                "verification_status": "verified",
                "sources": [],
                "processing_time": 3.0,
                "backends_used": ["serply"],
                "error_message": None,
            }
            start_time = time.time()
            result = baseline_tools["verification_tool"]._run(
                "Healthcare policy needs improvement",
                "Test context",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            end_time = time.time()
            baseline_data["baselines"]["verification_tool"] = {
                "execution_time": end_time - start_time,
                "success": result.success,
                "processing_time": result.data.get("processing_time", 0) if result.success else 0,
            }
            assert result.success
        with patch.object(baseline_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {
                "success": True,
                "content_id": "test_123",
                "namespace": "test_namespace",
                "timestamp": "2024-01-01T00:00:00Z",
            }
            start_time = time.time()
            result = baseline_tools["memory_tool"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            end_time = time.time()
            baseline_data["baselines"]["memory_tool"] = {
                "execution_time": end_time - start_time,
                "success": result.success,
                "storage_size": len("Test content"),
            }
            assert result.success
        with open(baseline_data_file, "w") as f:
            json.dump(baseline_data, f, indent=2)
        assert os.path.exists(baseline_data_file)
        assert "analysis_tool" in baseline_data["baselines"]
        assert "download_tool" in baseline_data["baselines"]
        assert "verification_tool" in baseline_data["baselines"]
        assert "memory_tool" in baseline_data["baselines"]

    def test_performance_regression_detection(
        self, baseline_tools, sample_content, sample_tenant_context, baseline_data_file
    ):
        """Test performance regression detection."""
        with open(baseline_data_file) as f:
            baseline_data = json.load(f)
        with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare", "policy"],
                "bias_indicators": ["subjective_language"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare policy needs improvement"],
                "processing_time": 1.5,
            }
            start_time = time.time()
            result = baseline_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            current_time = end_time - start_time
            baseline_time = baseline_data["baselines"]["analysis_tool"]["execution_time"]
            regression_threshold = baseline_time * 1.2
            assert (
                current_time <= regression_threshold
            ), f"Performance regression detected: {current_time} > {regression_threshold}"
            assert result.success

    def test_performance_monitoring(self, baseline_tools, sample_content, sample_tenant_context):
        """Test performance monitoring and metrics collection."""
        metrics_data = {"timestamp": time.time(), "metrics": {}}
        with patch("ultimate_discord_intelligence_bot.obs.metrics.get_metrics") as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                mock_analyze.return_value = {
                    "political_topics": ["healthcare"],
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.8,
                    "extracted_claims": ["Healthcare is important"],
                    "processing_time": 1.0,
                }
                result = baseline_tools["analysis_tool"]._run(
                    sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                mock_metrics_instance.increment.assert_called()
                mock_metrics_instance.timing.assert_called()
                metrics_data["metrics"]["analysis_tool"] = {
                    "execution_count": 1,
                    "success_rate": 1.0,
                    "average_time": 1.0,
                }
                assert result.success

    def test_load_testing(self, baseline_tools, sample_tenant_context):
        """Test load testing capabilities."""
        load_sizes = [10, 50, 100]
        load_results = {}
        with patch.object(baseline_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for load_size in load_sizes:
                start_time = time.time()
                successful_operations = 0
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(
                            baseline_tools["memory_tool"]._run,
                            "store",
                            f"Test content {i}",
                            {"index": i},
                            "test_namespace",
                            sample_tenant_context["tenant"],
                            sample_tenant_context["workspace"],
                        )
                        for i in range(load_size)
                    ]
                    for future in futures:
                        result = future.result()
                        if result.success:
                            successful_operations += 1
                end_time = time.time()
                execution_time = end_time - start_time
                load_results[load_size] = {
                    "execution_time": execution_time,
                    "successful_operations": successful_operations,
                    "throughput": successful_operations / execution_time,
                    "success_rate": successful_operations / load_size,
                }
                assert successful_operations == load_size
                assert load_results[load_size]["success_rate"] == 1.0
                assert load_results[load_size]["throughput"] > 0

    def test_stress_testing(self, baseline_tools, sample_tenant_context):
        """Test stress testing capabilities."""
        stress_duration = 30
        start_time = time.time()
        operation_count = 0
        error_count = 0
        with patch.object(baseline_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            while time.time() - start_time < stress_duration:
                result = baseline_tools["memory_tool"]._run(
                    "store",
                    f"Stress test content {operation_count}",
                    {"index": operation_count},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                operation_count += 1
                if not result.success:
                    error_count += 1
            assert operation_count > 0
            assert error_count == 0
            assert operation_count / stress_duration > 10

    def test_memory_usage_monitoring(self, baseline_tools, sample_tenant_context):
        """Test memory usage monitoring."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        with patch.object(baseline_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for i in range(1000):
                result = baseline_tools["memory_tool"]._run(
                    "store",
                    f"Large content {i}" * 100,
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        assert memory_increase < 500
        assert memory_increase > 0

    def test_cpu_usage_monitoring(self, baseline_tools, sample_tenant_context):
        """Test CPU usage monitoring."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_cpu = process.cpu_percent()
        with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            for i in range(100):
                result = baseline_tools["analysis_tool"]._run(
                    f"Test content {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
        final_cpu = process.cpu_percent()
        assert final_cpu < 90
        assert final_cpu >= initial_cpu

    def test_performance_alerting(self, baseline_tools, sample_content, sample_tenant_context):
        """Test performance alerting mechanisms."""
        alert_thresholds = {"analysis_tool": 5.0, "download_tool": 10.0, "verification_tool": 15.0, "memory_tool": 2.0}
        alerts = []
        with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            start_time = time.time()
            result = baseline_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            execution_time = end_time - start_time
            if execution_time > alert_thresholds["analysis_tool"]:
                alerts.append(
                    f"Analysis tool performance alert: {execution_time}s > {alert_thresholds['analysis_tool']}s"
                )
            assert result.success
        assert len(alerts) == 0

    def test_performance_trending(self, baseline_tools, sample_content, sample_tenant_context):
        """Test performance trending analysis."""
        performance_data = []
        with patch.object(baseline_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            for i in range(10):
                start_time = time.time()
                result = baseline_tools["analysis_tool"]._run(
                    f"{sample_content} {i}",
                    "comprehensive",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                end_time = time.time()
                performance_data.append(
                    {"timestamp": time.time(), "execution_time": end_time - start_time, "success": result.success}
                )
                assert result.success
            execution_times = [data["execution_time"] for data in performance_data]
            average_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            assert average_time > 0
            assert max_time > 0
            assert min_time > 0
            assert max_time >= min_time
            time_variance = max_time - min_time
            assert time_variance < 2.0

    def test_performance_optimization(self, baseline_tools, sample_tenant_context):
        """Test performance optimization opportunities."""
        optimization_opportunities = []
        with patch.object(baseline_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            start_time = time.time()
            for i in range(10):
                result = baseline_tools["memory_tool"]._run(
                    "store",
                    f"Sequential content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
            sequential_time = time.time() - start_time
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(
                        baseline_tools["memory_tool"]._run,
                        "store",
                        f"Concurrent content {i}",
                        {"index": i},
                        "test_namespace",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    for i in range(10)
                ]
                for future in futures:
                    result = future.result()
                    assert result.success
            concurrent_time = time.time() - start_time
            if concurrent_time < sequential_time:
                optimization_opportunities.append(
                    {
                        "type": "concurrent_operations",
                        "improvement": (sequential_time - concurrent_time) / sequential_time * 100,
                    }
                )
            assert len(optimization_opportunities) > 0
