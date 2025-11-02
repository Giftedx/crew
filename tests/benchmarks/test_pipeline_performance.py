"""
Performance benchmarks for the content processing pipeline.

This module benchmarks full pipeline processing time, memory usage,
and concurrent request handling capacity.
"""

import asyncio
import statistics
import time
from platform.core.step_result import StepResult
from unittest.mock import patch

import psutil
import pytest

from ultimate_discord_intelligence_bot.pipeline_components.orchestrator import ContentPipeline


class TestPipelinePerformance:
    """Performance benchmarks for the content processing pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return ContentPipeline()

    @pytest.fixture
    def sample_urls(self):
        """Sample URLs for performance testing."""
        return [
            "https://example.com/video1",
            "https://example.com/video2",
            "https://example.com/video3",
            "https://example.com/video4",
            "https://example.com/video5",
        ]

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for performance testing."""
        return {
            "max_retries": 3,
            "timeout": 30,
            "enable_rollback": True,
            "enable_monitoring": True,
            "concurrency_limit": 10,
        }

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context for performance testing."""
        return {"tenant": "perf_test_tenant", "workspace": "perf_test_workspace"}

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_single_pipeline_processing_time(self, pipeline, mock_config, sample_tenant_context):
        """Benchmark single pipeline processing time."""
        sample_url = "https://example.com/test-video"
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            start_time = time.time()
            result = await pipeline.process_content(
                url=sample_url,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
                config=mock_config,
            )
            end_time = time.time()
            processing_time = end_time - start_time
            assert result.success
            assert processing_time < 5.0
            print(f"Single pipeline processing time: {processing_time:.3f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_memory_usage(self, pipeline, mock_config, sample_tenant_context):
        """Benchmark pipeline memory usage during processing."""
        sample_url = "https://example.com/test-video"
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            result = await pipeline.process_content(
                url=sample_url,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
                config=mock_config,
            )
            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = peak_memory - initial_memory
            assert result.success
            assert memory_increase < 100
            print(f"Memory usage increase: {memory_increase:.2f} MB")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_processing(self, pipeline, mock_config, sample_tenant_context, sample_urls):
        """Benchmark concurrent pipeline processing capacity."""
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            start_time = time.time()
            tasks = [
                pipeline.process_content(
                    url=url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=mock_config,
                )
                for url in sample_urls
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            total_time = end_time - start_time
            assert all(result.success for result in results)
            assert total_time < 10.0
            print(f"Concurrent processing time for {len(sample_urls)} URLs: {total_time:.3f} seconds")
            print(f"Average time per URL: {total_time / len(sample_urls):.3f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_processing_memory_usage(self, pipeline, mock_config, sample_tenant_context, sample_urls):
        """Benchmark memory usage during concurrent processing."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            tasks = [
                pipeline.process_content(
                    url=url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=mock_config,
                )
                for url in sample_urls
            ]
            results = await asyncio.gather(*tasks)
            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = peak_memory - initial_memory
            assert all(result.success for result in results)
            assert memory_increase < 200
            print(f"Concurrent memory usage increase: {memory_increase:.2f} MB")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_throughput_benchmark(self, pipeline, mock_config, sample_tenant_context):
        """Benchmark pipeline throughput over multiple iterations."""
        iterations = 10
        processing_times = []
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            for i in range(iterations):
                sample_url = f"https://example.com/test-video-{i}"
                start_time = time.time()
                result = await pipeline.process_content(
                    url=sample_url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=mock_config,
                )
                end_time = time.time()
                processing_times.append(end_time - start_time)
                assert result.success
            avg_processing_time = statistics.mean(processing_times)
            min_processing_time = min(processing_times)
            max_processing_time = max(processing_times)
            std_dev = statistics.stdev(processing_times) if len(processing_times) > 1 else 0
            throughput = 1.0 / avg_processing_time
            assert avg_processing_time < 3.0
            assert throughput > 0.3
            print(f"Average processing time: {avg_processing_time:.3f} seconds")
            print(f"Min processing time: {min_processing_time:.3f} seconds")
            print(f"Max processing time: {max_processing_time:.3f} seconds")
            print(f"Standard deviation: {std_dev:.3f} seconds")
            print(f"Throughput: {throughput:.3f} URLs/second")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_stress_test(self, pipeline, mock_config, sample_tenant_context):
        """Stress test pipeline with high concurrent load."""
        concurrent_requests = 20
        sample_urls = [f"https://example.com/stress-test-{i}" for i in range(concurrent_requests)]
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            start_time = time.time()
            tasks = [
                pipeline.process_content(
                    url=url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=mock_config,
                )
                for url in sample_urls
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            total_time = end_time - start_time
            successful_results = [r for r in results if isinstance(r, StepResult) and r.success]
            failed_results = [r for r in results if not isinstance(r, StepResult) or not r.success]
            success_rate = len(successful_results) / len(results)
            assert success_rate >= 0.95
            assert total_time < 30.0
            print(f"Stress test with {concurrent_requests} concurrent requests:")
            print(f"Total time: {total_time:.3f} seconds")
            print(f"Success rate: {success_rate:.2%}")
            print(f"Successful requests: {len(successful_results)}")
            print(f"Failed requests: {len(failed_results)}")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_memory_leak_detection(self, pipeline, mock_config, sample_tenant_context):
        """Test for memory leaks during repeated pipeline processing."""
        iterations = 50
        memory_measurements = []
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            process = psutil.Process()
            for i in range(iterations):
                sample_url = f"https://example.com/memory-test-{i}"
                result = await pipeline.process_content(
                    url=sample_url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=mock_config,
                )
                memory_usage = process.memory_info().rss / 1024 / 1024
                memory_measurements.append(memory_usage)
                assert result.success
            initial_memory = memory_measurements[0]
            final_memory = memory_measurements[-1]
            memory_increase = final_memory - initial_memory
            memory_trend = statistics.mean(memory_measurements[-10:]) - statistics.mean(memory_measurements[:10])
            assert memory_increase < 50
            assert memory_trend < 20
            print(f"Memory leak test over {iterations} iterations:")
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Final memory: {final_memory:.2f} MB")
            print(f"Memory increase: {memory_increase:.2f} MB")
            print(f"Memory trend: {memory_trend:.2f} MB")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_error_recovery_performance(self, pipeline, mock_config, sample_tenant_context):
        """Benchmark pipeline error recovery performance."""
        sample_url = "https://example.com/error-recovery-test"
        call_count = 0

        async def mock_failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary failure")
            return StepResult.ok(data={"content": "test"})

        with (
            patch.object(pipeline, "_download_phase", side_effect=mock_failing_then_success),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            start_time = time.time()
            result = await pipeline.process_content(
                url=sample_url,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
                config=mock_config,
            )
            end_time = time.time()
            recovery_time = end_time - start_time
            assert result.success
            assert call_count == 3
            assert recovery_time < 8.0
            print(f"Error recovery time: {recovery_time:.3f} seconds")
            print(f"Number of retries: {call_count - 1}")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_pipeline_configuration_performance_impact(self, pipeline, sample_tenant_context):
        """Test performance impact of different pipeline configurations."""
        sample_url = "https://example.com/config-test"
        configs = [
            {"timeout": 10, "max_retries": 1},
            {"timeout": 30, "max_retries": 3},
            {"timeout": 60, "max_retries": 5},
        ]
        config_results = []
        with (
            patch.object(pipeline, "_download_phase", return_value=StepResult.ok(data={"content": "test"})),
            patch.object(
                pipeline, "_transcription_phase", return_value=StepResult.ok(data={"transcript": "test transcript"})
            ),
            patch.object(pipeline, "_analysis_phase", return_value=StepResult.ok(data={"analysis": "test analysis"})),
            patch.object(pipeline, "_memory_storage_phase", return_value=StepResult.ok()),
        ):
            for config in configs:
                start_time = time.time()
                result = await pipeline.process_content(
                    url=sample_url,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                    config=config,
                )
                end_time = time.time()
                processing_time = end_time - start_time
                config_results.append({"config": config, "time": processing_time, "success": result.success})
                assert result.success
        for result in config_results:
            print(f"Config {result['config']}: {result['time']:.3f} seconds")
        assert all(result["success"] for result in config_results)
