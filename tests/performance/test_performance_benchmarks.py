"""Performance tests and benchmarks for the Ultimate Discord Intelligence Bot."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest

from ultimate_discord_intelligence_bot.tools.acquisition.multi_platform_download_tool import MultiPlatformDownloadTool
from ultimate_discord_intelligence_bot.tools.analysis.enhanced_analysis_tool import EnhancedAnalysisTool
from ultimate_discord_intelligence_bot.tools.memory.unified_memory_tool import UnifiedMemoryTool
from ultimate_discord_intelligence_bot.tools.verification.claim_verifier_tool import ClaimVerifierTool


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

            # Measure performance
            start_time = time.time()
            result = performance_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()

            execution_time = end_time - start_time

            assert result.success
            assert execution_time < 5.0  # Should complete within 5 seconds
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

            # Measure performance for multiple downloads
            start_time = time.time()
            results = []
            for url in test_urls:
                result = performance_tools["download_tool"]._run(
                    url, "720p", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                results.append(result)
            end_time = time.time()

            execution_time = end_time - start_time

            # All should succeed
            for result in results:
                assert result.success

            # Should complete within reasonable time
            assert execution_time < 10.0  # 10 seconds for 3 downloads
            assert execution_time / len(test_urls) < 5.0  # Average per download

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

            # Measure performance for multiple verifications
            start_time = time.time()
            results = []
            for claim in test_claims:
                result = performance_tools["verification_tool"]._run(
                    claim, "Test context", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                results.append(result)
            end_time = time.time()

            execution_time = end_time - start_time

            # All should succeed
            for result in results:
                assert result.success

            # Should complete within reasonable time
            assert execution_time < 15.0  # 15 seconds for 3 verifications
            assert execution_time / len(test_claims) < 8.0  # Average per verification

    def test_memory_tool_performance(self, performance_tools, sample_tenant_context):
        """Test memory tool performance benchmarks."""
        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {
                "success": True,
                "content_id": "test_123",
                "namespace": "test_namespace",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            # Measure performance for multiple storage operations
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

            # All should succeed
            for result in results:
                assert result.success

            # Should complete within reasonable time
            assert execution_time < 5.0  # 5 seconds for 10 operations
            assert execution_time / 10 < 1.0  # Average per operation

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

        # Test concurrent analysis operations
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

        # All should succeed
        for result in results:
            assert result.success

        # Should complete within reasonable time
        assert execution_time < 10.0  # 10 seconds for 10 concurrent operations
        assert execution_time / 10 < 2.0  # Average per operation

    def test_memory_usage_performance(self, performance_tools, sample_tenant_context):
        """Test memory usage performance."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

            # Perform multiple memory operations
            for i in range(100):
                result = performance_tools["memory_tool"]._run(
                    "store",
                    f"Test content {i}" * 100,  # Large content
                    {"index": i},
                    "test_namespace",
                    sample_tenant_context["tenant"],
                    sample_tenant_context["workspace"],
                )
                assert result.success

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase

    def test_response_time_benchmarks(self, performance_tools, sample_content, sample_tenant_context):
        """Test response time benchmarks for different operations."""
        benchmarks = {}

        # Analysis tool benchmark
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

        # Memory tool benchmark
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

        # Verify benchmarks are within acceptable limits
        assert benchmarks["analysis"] < 2.0  # Analysis should complete within 2 seconds
        assert benchmarks["memory"] < 1.0  # Memory operations should complete within 1 second

    def test_throughput_benchmarks(self, performance_tools, sample_tenant_context):
        """Test throughput benchmarks for high-volume operations."""
        # Test high-volume memory operations
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
            throughput = successful_operations / total_time  # Operations per second

            assert successful_operations == 1000  # All operations should succeed
            assert throughput > 100  # Should handle at least 100 operations per second

    def test_error_handling_performance(self, performance_tools, sample_tenant_context):
        """Test error handling performance."""
        # Test with failing operations
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

            assert error_count == 100  # All operations should fail
            assert execution_time < 5.0  # Error handling should be fast

    def test_scalability_benchmarks(self, performance_tools, sample_tenant_context):
        """Test scalability benchmarks."""
        # Test with increasing load
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

            # Verify scalability (execution time should not increase linearly)
            for i in range(1, len(execution_times)):
                time_per_operation = execution_times[i] / load_sizes[i]
                prev_time_per_operation = execution_times[i - 1] / load_sizes[i - 1]

                # Time per operation should not increase significantly
                assert time_per_operation <= prev_time_per_operation * 1.5

    def test_resource_usage_benchmarks(self, performance_tools, sample_tenant_context):
        """Test resource usage benchmarks."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Get initial resource usage
        process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch.object(performance_tools["memory_tool"], "_store_content") as mock_store:
            mock_store.return_value = {"success": True, "content_id": "test_123", "namespace": "test_namespace"}

            # Perform operations
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

        # Get final resource usage
        final_cpu = process.cpu_percent()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Resource usage should be reasonable
        assert final_memory - initial_memory < 200  # Less than 200MB increase
        assert final_cpu < 80  # CPU usage should be reasonable

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

                # Simulate async operation
                await asyncio.sleep(0.1)
                return performance_tools["analysis_tool"]._run(content, "comprehensive", tenant, workspace)

        async def run_async_tests():
            start_time = time.time()

            # Run multiple async operations
            tasks = [
                run_async_analysis(
                    f"{sample_content} {i}", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
                )
                for i in range(10)
            ]

            results = await asyncio.gather(*tasks)
            end_time = time.time()

            execution_time = end_time - start_time

            # All should succeed
            for result in results:
                assert result.success

            # Async operations should be faster than sequential
            assert execution_time < 5.0  # Should complete within 5 seconds

            return execution_time

        # Run async test
        execution_time = asyncio.run(run_async_tests())
        assert execution_time > 0

    def test_performance_regression(self, performance_tools, sample_content, sample_tenant_context):
        """Test for performance regressions."""
        # Baseline performance measurement
        with patch.object(performance_tools["analysis_tool"], "_analyze_comprehensive") as mock_analyze:
            mock_analyze.return_value = {
                "political_topics": ["healthcare"],
                "sentiment": "neutral",
                "sentiment_confidence": 0.8,
                "extracted_claims": ["Healthcare is important"],
                "processing_time": 1.0,
            }

            # Measure baseline
            start_time = time.time()
            result = performance_tools["analysis_tool"]._run(
                sample_content, "comprehensive", sample_tenant_context["tenant"], sample_tenant_context["workspace"]
            )
            end_time = time.time()

            baseline_time = end_time - start_time
            assert result.success

            # Verify performance is within acceptable limits
            assert baseline_time < 3.0  # Should complete within 3 seconds

            # Store baseline for future regression testing
            # In a real scenario, this would be stored in a performance database
            assert baseline_time > 0
