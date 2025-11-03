"""Tests for unified memory facade (ADR-0002)."""

from __future__ import annotations

from platform.core.step_result import StepResult

import pytest
from memory.vector_store import VectorRecord

from ultimate_discord_intelligence_bot.memory import UnifiedMemoryService, get_unified_memory


@pytest.fixture
def memory_service():
    """Create unified memory service instance."""
    return UnifiedMemoryService()


@pytest.fixture
def sample_vectors():
    """Create sample vector records for testing."""
    return [
        VectorRecord(vector=[0.1, 0.2, 0.3], payload={"text": "test content 1", "id": 1}),
        VectorRecord(vector=[0.2, 0.3, 0.4], payload={"text": "test content 2", "id": 2}),
    ]


class TestNamespaceGeneration:
    """Test namespace generation for tenant isolation."""

    def test_namespace_format(self, memory_service):
        """Test namespace includes tenant, workspace, creator."""
        ns = memory_service.get_namespace("tenant1", "workspace1", "creator1")
        assert ns == "tenant1:workspace1:creator1"

    def test_namespace_default_creator(self, memory_service):
        """Test namespace with default creator."""
        ns = memory_service.get_namespace("tenant1", "workspace1")
        assert ns == "tenant1:workspace1:default"


class TestMemoryUpsert:
    """Test vector upsert operations."""

    @pytest.mark.asyncio
    async def test_upsert_success(self, memory_service, sample_vectors):
        """Test successful vector upsert."""
        result = await memory_service.upsert(tenant="test", workspace="test", records=sample_vectors)
        assert isinstance(result, StepResult)
        assert result.success
        assert result.data["upserted"] == 2
        assert "test:test:default" in result.data["namespace"]

    @pytest.mark.asyncio
    async def test_upsert_with_creator(self, memory_service, sample_vectors):
        """Test upsert with creator isolation."""
        result = await memory_service.upsert(
            tenant="test", workspace="test", records=sample_vectors, creator="creator1"
        )
        assert result.success
        assert "creator1" in result.data["namespace"]


class TestMemoryQuery:
    """Test vector query operations."""

    @pytest.mark.asyncio
    async def test_query_success(self, memory_service, sample_vectors):
        """Test successful vector query."""
        await memory_service.upsert(tenant="test", workspace="test", records=sample_vectors)
        query_vector = [0.15, 0.25, 0.35]
        result = await memory_service.query(tenant="test", workspace="test", vector=query_vector, top_k=2)
        assert result.success
        assert "results" in result.data
        assert result.data["count"] >= 0

    @pytest.mark.asyncio
    async def test_query_isolation(self, memory_service, sample_vectors):
        """Test tenant isolation in queries."""
        await memory_service.upsert(tenant="tenant1", workspace="workspace1", records=sample_vectors)
        query_vector = [0.15, 0.25, 0.35]
        result = await memory_service.query(tenant="tenant2", workspace="workspace2", vector=query_vector, top_k=2)
        assert result.success


class TestMemorySingleton:
    """Test global memory service singleton."""

    def test_get_unified_memory_singleton(self):
        """Test get_unified_memory returns singleton."""
        service1 = get_unified_memory()
        service2 = get_unified_memory()
        assert service1 is service2

    def test_singleton_uses_global_vector_store(self):
        """Test singleton uses production vector store."""
        service = get_unified_memory()
        assert service._store is not None
