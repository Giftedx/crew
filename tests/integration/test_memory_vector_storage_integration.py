"""Integration tests for memory and vector storage with Qdrant."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from domains.memory.vector_store import MemoryService
from ultimate_discord_intelligence_bot.tenancy.context import TenantContext


class TestMemoryVectorStorageIntegration:
    """Integration tests for memory and vector storage."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Create a mock Qdrant client."""
        client = MagicMock()
        client.upsert = AsyncMock(return_value={"status": "ok"})
        client.search = AsyncMock(
            return_value={
                "result": [
                    {
                        "id": "test_id_1",
                        "score": 0.95,
                        "payload": {
                            "text": "Test content about artificial intelligence",
                            "metadata": {"source": "test", "timestamp": 1234567890},
                        },
                    }
                ]
            }
        )
        client.delete = AsyncMock(return_value={"status": "ok"})
        client.get_collection = AsyncMock(return_value={"status": "ok"})
        return client

    @pytest.fixture
    def memory_service(self, mock_qdrant_client):
        """Create a MemoryService instance with mocked Qdrant client."""
        with patch("ultimate_discord_intelligence_bot.services.memory_service.QdrantClient") as mock_qdrant:
            mock_qdrant.return_value = mock_qdrant_client
            service = MemoryService()
            service.client = mock_qdrant_client
            return service

    @pytest.fixture
    def test_tenant_context(self):
        """Create a test tenant context."""
        return TenantContext(tenant="test_tenant", workspace="test_workspace")

    @pytest.mark.asyncio
    async def test_memory_storage_and_retrieval(self, memory_service, test_tenant_context):
        """Test storing and retrieving content from memory."""
        content = "This is a test document about machine learning and artificial intelligence."
        metadata = {"source": "test", "timestamp": 1234567890, "tags": ["AI", "ML", "technology"]}
        store_result = await memory_service.store_content(
            content=content,
            metadata=metadata,
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        assert store_result.success
        assert "memory_id" in store_result.data
        retrieve_result = await memory_service.retrieve_content(
            query="machine learning artificial intelligence",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
            limit=5,
        )
        assert retrieve_result.success
        assert len(retrieve_result.data["results"]) > 0

    @pytest.mark.asyncio
    async def test_memory_storage_with_embeddings(self, memory_service, test_tenant_context):
        """Test memory storage with custom embeddings."""
        content = "Advanced neural network architectures for deep learning applications."
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5] * 100
        with patch.object(memory_service, "_generate_embeddings", return_value=mock_embeddings):
            result = await memory_service.store_content(
                content=content, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
            )
        assert result.success
        assert "memory_id" in result.data

    @pytest.mark.asyncio
    async def test_memory_search_with_filters(self, memory_service, test_tenant_context):
        """Test memory search with metadata filters."""
        documents = [
            {
                "content": "Machine learning algorithms for classification",
                "metadata": {"category": "ML", "difficulty": "beginner"},
            },
            {
                "content": "Deep learning neural networks for image recognition",
                "metadata": {"category": "DL", "difficulty": "advanced"},
            },
            {
                "content": "Natural language processing techniques",
                "metadata": {"category": "NLP", "difficulty": "intermediate"},
            },
        ]
        for doc in documents:
            await memory_service.store_content(
                content=doc["content"],
                metadata=doc["metadata"],
                tenant=test_tenant_context.tenant,
                workspace=test_tenant_context.workspace,
            )
        search_result = await memory_service.retrieve_content(
            query="machine learning",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
            filters={"category": "ML"},
            limit=10,
        )
        assert search_result.success
        assert len(search_result.data["results"]) > 0

    @pytest.mark.asyncio
    async def test_memory_batch_operations(self, memory_service, test_tenant_context):
        """Test batch memory operations."""
        documents = [
            "Document 1 about artificial intelligence",
            "Document 2 about machine learning",
            "Document 3 about deep learning",
            "Document 4 about neural networks",
            "Document 5 about computer vision",
        ]
        batch_result = await memory_service.store_batch(
            contents=documents, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert batch_result.success
        assert len(batch_result.data["stored_ids"]) == len(documents)
        search_result = await memory_service.search_batch(
            queries=["artificial intelligence", "machine learning"],
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        assert search_result.success
        assert len(search_result.data["results"]) > 0

    @pytest.mark.asyncio
    async def test_memory_tenant_isolation(self, memory_service):
        """Test that memory storage respects tenant isolation."""
        tenant1 = "tenant_1"
        tenant2 = "tenant_2"
        workspace = "test_workspace"
        await memory_service.store_content(content="Tenant 1 content", tenant=tenant1, workspace=workspace)
        await memory_service.store_content(content="Tenant 2 content", tenant=tenant2, workspace=workspace)
        result1 = await memory_service.retrieve_content(query="content", tenant=tenant1, workspace=workspace)
        result2 = await memory_service.retrieve_content(query="content", tenant=tenant2, workspace=workspace)
        assert result1.success
        assert result2.success
        assert result1.data["results"] != result2.data["results"]

    @pytest.mark.asyncio
    async def test_memory_workspace_isolation(self, memory_service):
        """Test that memory storage respects workspace isolation."""
        tenant = "test_tenant"
        workspace1 = "workspace_1"
        workspace2 = "workspace_2"
        await memory_service.store_content(content="Workspace 1 content", tenant=tenant, workspace=workspace1)
        await memory_service.store_content(content="Workspace 2 content", tenant=tenant, workspace=workspace2)
        result1 = await memory_service.retrieve_content(query="content", tenant=tenant, workspace=workspace1)
        result2 = await memory_service.retrieve_content(query="content", tenant=tenant, workspace=workspace2)
        assert result1.success
        assert result2.success
        assert result1.data["results"] != result2.data["results"]

    @pytest.mark.asyncio
    async def test_memory_deletion(self, memory_service, test_tenant_context):
        """Test memory content deletion."""
        store_result = await memory_service.store_content(
            content="Content to be deleted", tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        memory_id = store_result.data["memory_id"]
        delete_result = await memory_service.delete_content(
            memory_id=memory_id, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert delete_result.success
        search_result = await memory_service.retrieve_content(
            query="deleted", tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert search_result.success
        assert len(search_result.data["results"]) == 0

    @pytest.mark.asyncio
    async def test_memory_update_operations(self, memory_service, test_tenant_context):
        """Test memory content updates."""
        store_result = await memory_service.store_content(
            content="Original content",
            metadata={"version": 1},
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        memory_id = store_result.data["memory_id"]
        update_result = await memory_service.update_content(
            memory_id=memory_id,
            content="Updated content",
            metadata={"version": 2},
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        assert update_result.success
        search_result = await memory_service.retrieve_content(
            query="Updated content", tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert search_result.success
        assert len(search_result.data["results"]) > 0

    @pytest.mark.asyncio
    async def test_memory_semantic_search(self, memory_service, test_tenant_context):
        """Test semantic search capabilities."""
        documents = [
            "The quick brown fox jumps over the lazy dog",
            "Artificial intelligence is transforming industries",
            "Machine learning algorithms process large datasets",
            "Deep learning neural networks mimic brain functions",
            "Computer vision enables machines to see and understand",
        ]
        for doc in documents:
            await memory_service.store_content(
                content=doc, tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
            )
        search_result = await memory_service.retrieve_content(
            query="AI technology and algorithms",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
            limit=5,
        )
        assert search_result.success
        assert len(search_result.data["results"]) > 0
        results = search_result.data["results"]
        ai_related = [r for r in results if "artificial" in r["content"].lower() or "machine" in r["content"].lower()]
        assert len(ai_related) > 0

    @pytest.mark.asyncio
    async def test_memory_performance_metrics(self, memory_service, test_tenant_context):
        """Test memory performance metrics collection."""
        start_time = asyncio.get_event_loop().time()
        await memory_service.store_content(
            content="Performance test content",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        store_time = asyncio.get_event_loop().time() - start_time
        start_time = asyncio.get_event_loop().time()
        await memory_service.retrieve_content(
            query="performance test", tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        search_time = asyncio.get_event_loop().time() - start_time
        assert store_time < 1.0
        assert search_time < 1.0

    @pytest.mark.asyncio
    async def test_memory_error_handling(self, memory_service, test_tenant_context):
        """Test memory error handling and recovery."""
        result = await memory_service.store_content(
            content="Test content", tenant="", workspace=test_tenant_context.workspace
        )
        assert not result.success
        assert "error" in result.data
        result = await memory_service.store_content(
            content="Test content", tenant=test_tenant_context.tenant, workspace=""
        )
        assert not result.success
        assert "error" in result.data

    @pytest.mark.asyncio
    async def test_memory_concurrent_operations(self, memory_service, test_tenant_context):
        """Test concurrent memory operations."""
        tasks = []
        for i in range(10):
            task = memory_service.store_content(
                content=f"Concurrent test content {i}",
                tenant=test_tenant_context.tenant,
                workspace=test_tenant_context.workspace,
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        for result in results:
            assert result.success
        search_result = await memory_service.retrieve_content(
            query="Concurrent test", tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert search_result.success
        assert len(search_result.data["results"]) >= 10

    @pytest.mark.asyncio
    async def test_memory_collection_management(self, memory_service, test_tenant_context):
        """Test memory collection management."""
        create_result = await memory_service.create_collection(
            collection_name="test_collection",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        assert create_result.success
        list_result = await memory_service.list_collections(
            tenant=test_tenant_context.tenant, workspace=test_tenant_context.workspace
        )
        assert list_result.success
        assert "test_collection" in list_result.data["collections"]
        delete_result = await memory_service.delete_collection(
            collection_name="test_collection",
            tenant=test_tenant_context.tenant,
            workspace=test_tenant_context.workspace,
        )
        assert delete_result.success
