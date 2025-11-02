"""Performance tests and benchmarks for the Ultimate Discord Intelligence Bot."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest

from domains.ingestion.providers.multi_platform_download_tool import MultiPlatformDownloadTool
from domains.intelligence.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from domains.intelligence.verification.claim_verifier_tool import ClaimVerifierTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool


class TestPerformanceBenchmarks:
    """Performance tests and benchmarks."""

    @pytest.fixture
    def performance_tools(self):
        """Create tools for performance testing."""
        return {
            "download_tool": MultiPlatformDownloadTool(),
            "analysis_tool": EnhancedAnalysisTool(),
            "verification_tool": ClaimVerifierTool(),
            "memory_tool": UnifiedMemoryTool(),
        }

    @pytest.fixture
    def sample_content(self):
        """Sample content for performance testing."""
        return (
            "This is a political statement about healthcare policy that needs comprehensive analysis and verification."
        )

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context."""
        return {"tenant": "performance_tenant", "workspace": "performance_workspace"}

    def test_analysis_tool_performance(self, performance_tools, sample_content, sample_tenant_context):
        """Test analysis tool performance benchmarks."""
        with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare", "policy"],
                "bias_indicators": ["subjective_language"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare policy needs improvement"],
                "processing_time": 1.0,
            }
            start_time = time.time()
            result = performance_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            execution_time = end_time - start_time
            assert result.success
            assert execution_time < 5.0
            assert result.data["processing_time"] > 0

    def test_download_tool_performance(self, performance_tools, sample_tenant_context):
        """Test download tool performance benchmarks."""
        test_urls = ["https://youtube.com/watch?v=1", "https://youtube.com/watch?v=2", "https://youtube.com/watch?v=3"]
        with patch.object(performance_tools["download_tool"], "_download_youtube") as mock_download:
            mock_download.return_value = {
                "success": True,
                "platform": "youtube",
                "file_path": "/tmp/test_video.mp4",
                "duration": 180,
                "quality": "720p",
            }
            start_time = time.time()
            results = []
            for url in test_urls:
                result = performance_tools["download_tool"]._run(
                    url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                results.append(result)
            end_time = time.time()
            execution_time = end_time - start_time
            for result in results:
                assert result.success
            assert execution_time < 10.0
            assert execution_time / len(test_urls) < 5.0

    def test_verification_tool_performance(self, performance_tools, sample_tenant_context):
        """Test verification tool performance benchmarks."""
        test_claims = [
            "Healthcare costs are rising",
            "Technology improves productivity",
            "Climate change is accelerating",
        ]
        with patch.object(performance_tools["verification_tool"], "_verify_claim") as mock_verify:
            mock_verify.return_value = {
                "claim_id": "claim_123",
                "claim_text": "Test claim",
                "overall_confidence": 0.9,
                "verification_status": "verified",
                "sources": [],
                "processing_time": 2.0,
                "backends_used": ["serply"],
                "error_message": None,
            }
            start_time = time.time()
            results = []
            for claim in test_claims:
                result = performance_tools["verification_tool"]._run(
                    claim, "Test context", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                results.append(result)
            end_time = time.time()
            execution_time = end_time - start_time
            for result in results:
                assert result.success
            assert execution_time < 15.0
            assert execution_time / len(test_claims) < 8.0

    def test_memory_tool_performance(self, performance_tools, sample_tenant_context):
        """Test memory tool performance benchmarks."""
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {
                "success": True,
                "content_id": "test_123",
                "namespace": "test_namespace",
                "timestamp": "2024-01-01T00:00:00Z",
            }
            start_time = time.time()
            results = []
            for i in range(10):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                results.append(result)
            end_time = time.time()
            execution_time = end_time - start_time
            for result in results:
                assert result.success
            assert execution_time < 5.0
            assert execution_time / 10 < 1.0

    def test_concurrent_operations_performance(self, performance_tools, sample_content, sample_tenant_context):
        """Test concurrent operations performance."""

        def run_analysis(content, tenant, workspace):
            with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                mock_analyze.return_value = {
                    "political_topics": ["healthcare"],
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.8,
                    "extracted_claims": ["Healthcare is important"],
                    "processing_time": 1.0,
                }
                return performance_tools["analysis_tool"]._run(content, "comprehensive", tenant, workspace)

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    run_analysis,
                    f"{sample_content} {i}",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                for i in range(10)
            ]
            results = [future.result() for future in as_completed(futures)]
        end_time = time.time()
        execution_time = end_time - start_time
        for result in results:
            assert result.success
        assert execution_time < 10.0
        assert execution_time / 10 < 2.0

    def test_memory_usage_performance(self, performance_tools, sample_tenant_context):
        """Test memory usage performance."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for i in range(100):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}" * 100,
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        assert memory_increase < 100

    def test_response_time_benchmarks(self, performance_tools, sample_content, sample_tenant_context):
        """Test response time benchmarks for different operations."""
        benchmarks = {}
        with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            start_time = time.time()
            result = performance_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            benchmarks["analysis"] = end_time - start_time
            assert result.success
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            start_time = time.time()
            result = performance_tools["memory_tool"]._run(
                "store",
                "Test content",
                {"test": "metadata"},
                "test_namespace",
                sample_tenant_context["tenant"],
                sample_tenant_context["workspace"],
            )
            end_time = time.time()
            benchmarks["memory"] = end_time - start_time
            assert result.success
        assert benchmarks["analysis"] < 2.0
        assert benchmarks["memory"] < 1.0

    def test_throughput_benchmarks(self, performance_tools, sample_tenant_context):
        """Test throughput benchmarks for high-volume operations."""
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            start_time = time.time()
            successful_operations = 0
            for i in range(1000):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                if result.success:
                    successful_operations += 1
            end_time = time.time()
            total_time = end_time - start_time
            throughput = successful_operations / total_time
            assert successful_operations == 1000
            assert throughput > 100

    def test_error_handling_performance(self, performance_tools, sample_tenant_context):
        """Test error handling performance."""
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.side_effect = Exception("Storage failed")
            start_time = time.time()
            error_count = 0
            for i in range(100):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                if not result.success:
                    error_count += 1
            end_time = time.time()
            execution_time = end_time - start_time
            assert error_count == 100
            assert execution_time < 5.0

    def test_scalability_benchmarks(self, performance_tools, sample_tenant_context):
        """Test scalability benchmarks."""
        load_sizes = [10, 50, 100, 200]
        execution_times = []
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for load_size in load_sizes:
                start_time = time.time()
                for i in range(load_size):
                    result = performance_tools["memory_tool"]._run(
                        "store",
                        f"Test content {i}",
                        {"index": i},
                        "test_namespace",
                        sample_tenant_context["tenant"],
                        sample_tenant_context["workspace"],
                    )
                    assert result.success
                end_time = time.time()
                execution_times.append(end_time - start_time)
            for i in range(1, len(execution_times)):
                time_per_operation = execution_times[i] / load_sizes[i]
                prev_time_per_operation = execution_times[i - 1] / load_sizes[i - 1]
                assert time_per_operation <= prev_time_per_operation * 1.5

    def test_resource_usage_benchmarks(self, performance_tools, sample_tenant_context):
        """Test resource usage benchmarks."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}
            for i in range(1000):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}",
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success
        final_cpu = process.cpu_percent()
        final_memory = process.memory_info().rss / 1024 / 1024
        assert final_memory - initial_memory < 200
        assert final_cpu < 80

    def test_async_performance(self, performance_tools, sample_content, sample_tenant_context):
        """Test async performance benchmarks."""

        async def run_async_analysis(content, tenant, workspace):
            with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
                mock_analyze.return_value = {
                    "political_topics": ["healthcare"],
                    "sentiment": "neutral",
                    "sentiment_confidence": 0.8,
                    "extracted_claims": ["Healthcare is important"],
                    "processing_time": 1.0,
                }
                await asyncio.sleep(0.1)
                return performance_tools["analysis_tool"]._run(content, "comprehensive", tenant, workspace)

        async def run_async_tests():
            start_time = time.time()
            tasks = [
                run_async_analysis(
                    f"{sample_content} {i}", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                for i in range(10)
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            execution_time = end_time - start_time
            for result in results:
                assert result.success
            assert execution_time < 5.0
            return execution_time

        execution_time = asyncio.run(run_async_tests())
        assert execution_time > 0

    def test_performance_regression(self, performance_tools, sample_content, sample_tenant_context):
        """Test for performance regressions."""
        with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }
            start_time = time.time()
            result = performance_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()
            baseline_time = end_time - start_time
            assert result.success
            assert baseline_time < 3.0
            assert baseline_time > 0
