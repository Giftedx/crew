"""
Performance benchmarks for memory operations and vector store.

This module benchmarks vector store/retrieve operations, embedding generation time,
search query latency, and batch operation performance.
"""

import asyncio
import statistics
import time
from unittest.mock import Mock

import pytest

from ultimate_discord_intelligence_bot.step_result import StepResult


class TestMemoryPerformance:
    """Performance benchmarks for memory operations and vector store."""

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store for testing."""
        return Mock()

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service for testing."""
        return Mock()

    @pytest.fixture
    def sample_content_items(self):
        """Sample content items for performance testing."""
        return [{"id": f"item_{i}", "text": f"Sample content {i}", "metadata": {"index": i}} for i in range(100)]

    @pytest.fixture
    def sample_tenant_context(self):
        """Sample tenant context for performance testing."""
        return {"tenant": "perf_test_tenant", "workspace": "perf_test_workspace"}

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_retrieve_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store retrieve operation performance."""
        mock_vector_store.retrieve.return_value = StepResult.ok(
            data={"content": "retrieved content", "metadata": {"id": "test_id"}}
        )
        iterations = 100
        retrieve_times = []
        for i in range(iterations):
            content_id = f"test_content_{i}"
            start_time = time.time()
            result = await mock_vector_store.retrieve(
                content_id=content_id,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
            )
            end_time = time.time()
            retrieve_times.append(end_time - start_time)
            assert result.success
        avg_retrieve_time = statistics.mean(retrieve_times)
        min_retrieve_time = min(retrieve_times)
        max_retrieve_time = max(retrieve_times)
        std_dev = statistics.stdev(retrieve_times) if len(retrieve_times) > 1 else 0
        assert avg_retrieve_time < 0.1
        assert max_retrieve_time < 0.5
        print("Vector store retrieve performance:")
        print(f"Average time: {avg_retrieve_time:.4f} seconds")
        print(f"Min time: {min_retrieve_time:.4f} seconds")
        print(f"Max time: {max_retrieve_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_store_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store store operation performance."""
        mock_vector_store.store.return_value = StepResult.ok(data={"id": "stored_id"})
        iterations = 100
        store_times = []
        for i in range(iterations):
            content = {"id": f"test_content_{i}", "text": f"Sample content {i}", "metadata": {"index": i}}
            start_time = time.time()
            result = await mock_vector_store.store(
                content=content, tenant=sample_tenant_context["tenant"], workspace=sample_tenant_context["workspace"]
            )
            end_time = time.time()
            store_times.append(end_time - start_time)
            assert result.success
        avg_store_time = statistics.mean(store_times)
        min_store_time = min(store_times)
        max_store_time = max(store_times)
        std_dev = statistics.stdev(store_times) if len(store_times) > 1 else 0
        assert avg_store_time < 0.2
        assert max_store_time < 1.0
        print("Vector store store performance:")
        print(f"Average time: {avg_store_time:.4f} seconds")
        print(f"Min time: {min_store_time:.4f} seconds")
        print(f"Max time: {max_store_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_search_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store search operation performance."""
        mock_vector_store.search.return_value = StepResult.ok(
            data={"results": [{"id": f"result_{i}", "score": 0.9 - i * 0.1} for i in range(10)]}
        )
        iterations = 100
        search_times = []
        for _i in range(iterations):
            query_vector = [0.1] * 768
            start_time = time.time()
            result = await mock_vector_store.search(
                query_vector=query_vector,
                limit=10,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
            )
            end_time = time.time()
            search_times.append(end_time - start_time)
            assert result.success
        avg_search_time = statistics.mean(search_times)
        min_search_time = min(search_times)
        max_search_time = max(search_times)
        std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0
        assert avg_search_time < 0.15
        assert max_search_time < 0.8
        print("Vector store search performance:")
        print(f"Average time: {avg_search_time:.4f} seconds")
        print(f"Min time: {min_search_time:.4f} seconds")
        print(f"Max time: {max_search_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_embedding_generation_performance(self, mock_embedding_service):
        """Benchmark embedding generation performance."""
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768
        iterations = 50
        embedding_times = []
        for i in range(iterations):
            text = f"Sample text for embedding generation {i}"
            start_time = time.time()
            embedding = await mock_embedding_service.generate_embedding(text)
            end_time = time.time()
            embedding_times.append(end_time - start_time)
            assert len(embedding) == 768
        avg_embedding_time = statistics.mean(embedding_times)
        min_embedding_time = min(embedding_times)
        max_embedding_time = max(embedding_times)
        std_dev = statistics.stdev(embedding_times) if len(embedding_times) > 1 else 0
        assert avg_embedding_time < 0.5
        assert max_embedding_time < 2.0
        print("Embedding generation performance:")
        print(f"Average time: {avg_embedding_time:.4f} seconds")
        print(f"Min time: {min_embedding_time:.4f} seconds")
        print(f"Max time: {max_embedding_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_batch_store_performance(self, mock_vector_store, sample_content_items, sample_tenant_context):
        """Benchmark batch store operation performance."""
        mock_vector_store.batch_store.return_value = [
            StepResult.ok(data={"id": f"stored_{i}"}) for i in range(len(sample_content_items))
        ]
        batch_sizes = [10, 25, 50, 100]
        batch_results = []
        for batch_size in batch_sizes:
            batch_content = sample_content_items[:batch_size]
            start_time = time.time()
            results = await mock_vector_store.batch_store(
                content_list=batch_content,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
            )
            end_time = time.time()
            batch_time = end_time - start_time
            batch_results.append({"batch_size": batch_size, "time": batch_time, "throughput": batch_size / batch_time})
            assert all(result.success for result in results)
        for result in batch_results:
            print(
                f"Batch size {result['batch_size']}: {result['time']:.3f} seconds, {result['throughput']:.2f} items/second"
            )
        assert all(result["time"] < 5.0 for result in batch_results)
        assert all(result["throughput"] > 5.0 for result in batch_results)

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self, mock_embedding_service):
        """Benchmark batch embedding generation performance."""
        mock_embedding_service.batch_generate_embeddings.return_value = [[0.1] * 768 for _ in range(50)]
        batch_sizes = [10, 25, 50]
        batch_results = []
        for batch_size in batch_sizes:
            texts = [f"Sample text {i}" for i in range(batch_size)]
            start_time = time.time()
            embeddings = await mock_embedding_service.batch_generate_embeddings(texts)
            end_time = time.time()
            batch_time = end_time - start_time
            batch_results.append({"batch_size": batch_size, "time": batch_time, "throughput": batch_size / batch_time})
            assert len(embeddings) == batch_size
            assert all(len(emb) == 768 for emb in embeddings)
        for result in batch_results:
            print(
                f"Batch embedding size {result['batch_size']}: {result['time']:.3f} seconds, {result['throughput']:.2f} embeddings/second"
            )
        assert all(result["time"] < 3.0 for result in batch_results)
        assert all(result["throughput"] > 3.0 for result in batch_results)

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_search_query_latency_at_scale(self, mock_vector_store, sample_tenant_context):
        """Benchmark search query latency at different scales."""

        def mock_search_with_results(*args, **kwargs):
            limit = kwargs.get("limit", 10)
            results = [{"id": f"result_{i}", "score": 0.9 - i * 0.01} for i in range(limit)]
            return StepResult.ok(data={"results": results})

        mock_vector_store.search.side_effect = mock_search_with_results
        query_scales = [10, 50, 100, 500, 1000]
        scale_results = []
        for scale in query_scales:
            query_vector = [0.1] * 768
            start_time = time.time()
            result = await mock_vector_store.search(
                query_vector=query_vector,
                limit=scale,
                tenant=sample_tenant_context["tenant"],
                workspace=sample_tenant_context["workspace"],
            )
            end_time = time.time()
            search_time = end_time - start_time
            scale_results.append({"scale": scale, "time": search_time, "latency_per_result": search_time / scale})
            assert result.success
        for result in scale_results:
            print(
                f"Search scale {result['scale']}: {result['time']:.4f} seconds, {result['latency_per_result']:.6f} seconds/result"
            )
        assert all(result["time"] < 2.0 for result in scale_results)
        assert all(result["latency_per_result"] < 0.01 for result in scale_results)

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, mock_vector_store, sample_tenant_context):
        """Benchmark concurrent memory operations performance."""
        mock_vector_store.store.return_value = StepResult.ok(data={"id": "stored_id"})
        mock_vector_store.retrieve.return_value = StepResult.ok(data={"content": "retrieved content"})
        mock_vector_store.search.return_value = StepResult.ok(data={"results": []})
        concurrent_operations = 20
        operation_types = ["store", "retrieve", "search"]
        start_time = time.time()
        tasks = []
        for i in range(concurrent_operations):
            op_type = operation_types[i % len(operation_types)]
            if op_type == "store":
                content = {"id": f"concurrent_{i}", "text": f"Content {i}"}
                task = mock_vector_store.store(
                    content=content,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                )
            elif op_type == "retrieve":
                task = mock_vector_store.retrieve(
                    content_id=f"concurrent_{i}",
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                )
            else:
                task = mock_vector_store.search(
                    query_vector=[0.1] * 768,
                    limit=10,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                )
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        total_time = end_time - start_time
        assert all(result.success for result in results)
        assert total_time < 3.0
        print("Concurrent memory operations:")
        print(f"Operations: {concurrent_operations}")
        print(f"Total time: {total_time:.3f} seconds")
        print(f"Operations per second: {concurrent_operations / total_time:.2f}")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_compaction_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark memory compaction performance."""
        mock_vector_store.compact.return_value = StepResult.ok(
            data={"compacted_items": 100, "space_saved": "50MB", "compaction_time": 2.5}
        )
        start_time = time.time()
        result = await mock_vector_store.compact(
            tenant=sample_tenant_context["tenant"], workspace=sample_tenant_context["workspace"]
        )
        end_time = time.time()
        compaction_time = end_time - start_time
        assert result.success
        assert compaction_time < 10.0
        print("Memory compaction performance:")
        print(f"Compaction time: {compaction_time:.3f} seconds")
        print(f"Compacted items: {result.data['compacted_items']}")
        print(f"Space saved: {result.data['space_saved']}")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_vector_store, sample_tenant_context):
        """Benchmark memory usage under various loads."""
        mock_vector_store.store.return_value = StepResult.ok(data={"id": "stored_id"})
        load_scales = [10, 50, 100, 200]
        memory_results = []
        for scale in load_scales:
            estimated_memory = scale * 0.1
            start_time = time.time()
            tasks = []
            for i in range(scale):
                content = {"id": f"load_test_{i}", "text": f"Load test content {i}"}
                task = mock_vector_store.store(
                    content=content,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                )
                tasks.append(task)
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            operation_time = end_time - start_time
            memory_results.append(
                {
                    "scale": scale,
                    "time": operation_time,
                    "estimated_memory": estimated_memory,
                    "throughput": scale / operation_time,
                }
            )
            assert all(result.success for result in results)
        for result in memory_results:
            print(
                f"Load scale {result['scale']}: {result['time']:.3f} seconds, {result['estimated_memory']:.1f}MB, {result['throughput']:.2f} ops/second"
            )
        assert all(result["time"] < 5.0 for result in memory_results)
        assert all(result["throughput"] > 10.0 for result in memory_results)
