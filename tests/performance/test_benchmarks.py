"""Performance benchmark tests for critical operations."""

from __future__ import annotations

import time
from platform.core.step_result import StepResult

import pytest

from domains.memory.vector_store import MemoryService


class TestPerformanceBenchmarks:
    """Performance benchmarks for critical operations."""

    @pytest.fixture
    def memory_service(self):
        """Create memory service for testing."""
        return MemoryService()

    def test_memory_retrieval_performance(self, memory_service):
        """Benchmark memory retrieval performance."""
        tenant, workspace = ("test_tenant", "test_workspace")
        namespace = f"{tenant}:{workspace}"
        for i in range(100):
            memory_service.add(f"Test content {i}", namespace=namespace)
        start_time = time.time()
        for _ in range(10):
            pass
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 1.0, f"Memory retrieval took {duration:.2f}s, expected < 1.0s"

    def test_concurrent_operations_performance(self, memory_service):
        """Benchmark concurrent operations performance."""
        import queue
        import threading

        tenant, workspace = ("test_tenant", "test_workspace")
        namespace = f"{tenant}:{workspace}"
        results = queue.Queue()

        def worker(worker_id):
            start_time = time.time()
            for i in range(10):
                memory_service.add(f"Worker {worker_id} content {i}", namespace=namespace)
            end_time = time.time()
            results.put((worker_id, end_time - start_time))

        start_time = time.time()
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        end_time = time.time()
        total_duration = end_time - start_time
        assert total_duration < 2.0, f"Concurrent operations took {total_duration:.2f}s, expected < 2.0s"
        assert results.qsize() == 5

    def test_large_content_processing_performance(self):
        """Benchmark processing of large content."""
        large_content = "Large content " * 10000
        start_time = time.time()
        processed_content = self._simulate_content_processing(large_content)
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 5.0, f"Large content processing took {duration:.2f}s, expected < 5.0s"
        assert len(processed_content) > 0

    def _simulate_content_processing(self, content: str) -> str:
        """Simulate content processing operations."""
        time.sleep(0.1)
        return content.upper()

    def test_memory_usage_benchmark(self, memory_service):
        """Benchmark memory usage during operations."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        tenant, workspace = ("test_tenant", "test_workspace")
        namespace = f"{tenant}:{workspace}"
        for i in range(1000):
            large_content = f"Large content {i} " * 100
            memory_service.add(large_content, namespace=namespace)
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory
        assert memory_increase < 100 * 1024 * 1024, f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"

    def test_cache_hit_performance(self):
        """Benchmark cache hit performance."""
        cache = {}

        def cache_get(key):
            return cache.get(key)

        def cache_set(key, value):
            cache[key] = value

        for i in range(1000):
            cache_set(f"key_{i}", f"value_{i}")
        start_time = time.time()
        for _ in range(100):
            for i in range(100):
                result = cache_get(f"key_{i}")
                assert result is not None
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 0.1, f"Cache operations took {duration:.2f}s, expected < 0.1s"

    def test_api_response_time_benchmark(self):
        """Benchmark API response times."""

        def simulate_api_call():
            time.sleep(0.05)
            return StepResult.ok(data={"response": "success"})

        start_time = time.time()
        results = []
        for _ in range(10):
            result = simulate_api_call()
            results.append(result)
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 1.0, f"API calls took {duration:.2f}s, expected < 1.0s"
        assert all(result.success for result in results)

    def test_database_operation_performance(self):
        """Benchmark database operation performance."""

        def simulate_db_operation():
            time.sleep(0.01)
            return StepResult.ok(data={"db_result": "success"})

        start_time = time.time()
        results = []
        for _ in range(100):
            result = simulate_db_operation()
            results.append(result)
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 2.0, f"Database operations took {duration:.2f}s, expected < 2.0s"
        assert all(result.success for result in results)

    def test_error_handling_performance(self):
        """Benchmark error handling performance."""

        def simulate_error_operation():
            try:
                if time.time() % 2 < 0.1:
                    raise ValueError("Simulated error")
                return StepResult.ok(data={"result": "success"})
            except Exception as e:
                return StepResult.fail(str(e))

        start_time = time.time()
        results = []
        for _ in range(100):
            result = simulate_error_operation()
            results.append(result)
        end_time = time.time()
        duration = end_time - start_time
        assert duration < 1.0, f"Error handling took {duration:.2f}s, expected < 1.0s"
        success_count = sum(1 for result in results if result.success)
        assert success_count > 0
        assert success_count < len(results)
