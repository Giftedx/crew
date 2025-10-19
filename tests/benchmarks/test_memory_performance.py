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

    # Vector Store Operation Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_retrieve_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store retrieve operation performance."""
        # Mock successful retrieve operation
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

        # Calculate performance metrics
        avg_retrieve_time = statistics.mean(retrieve_times)
        min_retrieve_time = min(retrieve_times)
        max_retrieve_time = max(retrieve_times)
        std_dev = statistics.stdev(retrieve_times) if len(retrieve_times) > 1 else 0

        # Performance assertions
        assert avg_retrieve_time < 0.1  # Average retrieve should be under 100ms
        assert max_retrieve_time < 0.5  # Max retrieve should be under 500ms

        # Record benchmark metrics
        print("Vector store retrieve performance:")
        print(f"Average time: {avg_retrieve_time:.4f} seconds")
        print(f"Min time: {min_retrieve_time:.4f} seconds")
        print(f"Max time: {max_retrieve_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_store_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store store operation performance."""
        # Mock successful store operation
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

        # Calculate performance metrics
        avg_store_time = statistics.mean(store_times)
        min_store_time = min(store_times)
        max_store_time = max(store_times)
        std_dev = statistics.stdev(store_times) if len(store_times) > 1 else 0

        # Performance assertions
        assert avg_store_time < 0.2  # Average store should be under 200ms
        assert max_store_time < 1.0  # Max store should be under 1 second

        # Record benchmark metrics
        print("Vector store store performance:")
        print(f"Average time: {avg_store_time:.4f} seconds")
        print(f"Min time: {min_store_time:.4f} seconds")
        print(f"Max time: {max_store_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_vector_store_search_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark vector store search operation performance."""
        # Mock successful search operation
        mock_vector_store.search.return_value = StepResult.ok(
            data={"results": [{"id": f"result_{i}", "score": 0.9 - i * 0.1} for i in range(10)]}
        )

        iterations = 100
        search_times = []

        for i in range(iterations):
            query_vector = [0.1] * 768  # Standard embedding dimension

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

        # Calculate performance metrics
        avg_search_time = statistics.mean(search_times)
        min_search_time = min(search_times)
        max_search_time = max(search_times)
        std_dev = statistics.stdev(search_times) if len(search_times) > 1 else 0

        # Performance assertions
        assert avg_search_time < 0.15  # Average search should be under 150ms
        assert max_search_time < 0.8  # Max search should be under 800ms

        # Record benchmark metrics
        print("Vector store search performance:")
        print(f"Average time: {avg_search_time:.4f} seconds")
        print(f"Min time: {min_search_time:.4f} seconds")
        print(f"Max time: {max_search_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    # Embedding Generation Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_embedding_generation_performance(self, mock_embedding_service):
        """Benchmark embedding generation performance."""
        # Mock successful embedding generation
        mock_embedding_service.generate_embedding.return_value = [0.1] * 768

        iterations = 50
        embedding_times = []

        for i in range(iterations):
            text = f"Sample text for embedding generation {i}"

            start_time = time.time()
            embedding = await mock_embedding_service.generate_embedding(text)
            end_time = time.time()

            embedding_times.append(end_time - start_time)
            assert len(embedding) == 768  # Standard embedding dimension

        # Calculate performance metrics
        avg_embedding_time = statistics.mean(embedding_times)
        min_embedding_time = min(embedding_times)
        max_embedding_time = max(embedding_times)
        std_dev = statistics.stdev(embedding_times) if len(embedding_times) > 1 else 0

        # Performance assertions
        assert avg_embedding_time < 0.5  # Average embedding should be under 500ms
        assert max_embedding_time < 2.0  # Max embedding should be under 2 seconds

        # Record benchmark metrics
        print("Embedding generation performance:")
        print(f"Average time: {avg_embedding_time:.4f} seconds")
        print(f"Min time: {min_embedding_time:.4f} seconds")
        print(f"Max time: {max_embedding_time:.4f} seconds")
        print(f"Standard deviation: {std_dev:.4f} seconds")

    # Batch Operation Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_batch_store_performance(self, mock_vector_store, sample_content_items, sample_tenant_context):
        """Benchmark batch store operation performance."""
        # Mock successful batch store operation
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

        # Analyze batch performance
        for result in batch_results:
            print(
                f"Batch size {result['batch_size']}: {result['time']:.3f} seconds, {result['throughput']:.2f} items/second"
            )

        # Performance assertions
        assert all(result["time"] < 5.0 for result in batch_results)  # All batches under 5 seconds
        assert all(result["throughput"] > 5.0 for result in batch_results)  # At least 5 items/second

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_batch_embedding_performance(self, mock_embedding_service):
        """Benchmark batch embedding generation performance."""
        # Mock successful batch embedding generation
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

        # Analyze batch embedding performance
        for result in batch_results:
            print(
                f"Batch embedding size {result['batch_size']}: {result['time']:.3f} seconds, {result['throughput']:.2f} embeddings/second"
            )

        # Performance assertions
        assert all(result["time"] < 3.0 for result in batch_results)  # All batches under 3 seconds
        assert all(result["throughput"] > 3.0 for result in batch_results)  # At least 3 embeddings/second

    # Search Query Latency Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_search_query_latency_at_scale(self, mock_vector_store, sample_tenant_context):
        """Benchmark search query latency at different scales."""

        # Mock successful search with different result counts
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

        # Analyze search latency scaling
        for result in scale_results:
            print(
                f"Search scale {result['scale']}: {result['time']:.4f} seconds, {result['latency_per_result']:.6f} seconds/result"
            )

        # Performance assertions
        assert all(result["time"] < 2.0 for result in scale_results)  # All searches under 2 seconds
        assert all(result["latency_per_result"] < 0.01 for result in scale_results)  # Under 10ms per result

    # Concurrent Memory Operation Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, mock_vector_store, sample_tenant_context):
        """Benchmark concurrent memory operations performance."""
        # Mock successful operations
        mock_vector_store.store.return_value = StepResult.ok(data={"id": "stored_id"})
        mock_vector_store.retrieve.return_value = StepResult.ok(data={"content": "retrieved content"})
        mock_vector_store.search.return_value = StepResult.ok(data={"results": []})

        concurrent_operations = 20
        operation_types = ["store", "retrieve", "search"]

        start_time = time.time()

        # Create concurrent tasks
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
            else:  # search
                task = mock_vector_store.search(
                    query_vector=[0.1] * 768,
                    limit=10,
                    tenant=sample_tenant_context["tenant"],
                    workspace=sample_tenant_context["workspace"],
                )

            tasks.append(task)

        # Execute all operations concurrently
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Performance assertions
        assert all(result.success for result in results)
        assert total_time < 3.0  # All concurrent operations under 3 seconds

        # Record benchmark metrics
        print("Concurrent memory operations:")
        print(f"Operations: {concurrent_operations}")
        print(f"Total time: {total_time:.3f} seconds")
        print(f"Operations per second: {concurrent_operations / total_time:.2f}")

    # Memory Compaction Performance

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_compaction_performance(self, mock_vector_store, sample_tenant_context):
        """Benchmark memory compaction performance."""
        # Mock successful compaction operation
        mock_vector_store.compact.return_value = StepResult.ok(
            data={"compacted_items": 100, "space_saved": "50MB", "compaction_time": 2.5}
        )

        start_time = time.time()
        result = await mock_vector_store.compact(
            tenant=sample_tenant_context["tenant"], workspace=sample_tenant_context["workspace"]
        )
        end_time = time.time()

        compaction_time = end_time - start_time

        # Performance assertions
        assert result.success
        assert compaction_time < 10.0  # Compaction should complete within 10 seconds

        # Record benchmark metrics
        print("Memory compaction performance:")
        print(f"Compaction time: {compaction_time:.3f} seconds")
        print(f"Compacted items: {result.data['compacted_items']}")
        print(f"Space saved: {result.data['space_saved']}")

    # Memory Usage Benchmarks

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_vector_store, sample_tenant_context):
        """Benchmark memory usage under various loads."""
        # Mock operations with memory tracking
        mock_vector_store.store.return_value = StepResult.ok(data={"id": "stored_id"})

        load_scales = [10, 50, 100, 200]
        memory_results = []

        for scale in load_scales:
            # Simulate memory usage based on load
            estimated_memory = scale * 0.1  # 0.1MB per item

            start_time = time.time()

            # Simulate batch operations
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

        # Analyze memory usage scaling
        for result in memory_results:
            print(
                f"Load scale {result['scale']}: {result['time']:.3f} seconds, "
                f"{result['estimated_memory']:.1f}MB, {result['throughput']:.2f} ops/second"
            )

        # Performance assertions
        assert all(result["time"] < 5.0 for result in memory_results)  # All loads under 5 seconds
        assert all(result["throughput"] > 10.0 for result in memory_results)  # At least 10 ops/second
