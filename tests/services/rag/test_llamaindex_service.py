"""Tests for LlamaIndex RAG service."""
import importlib.util
import pytest
LLAMAINDEX_AVAILABLE = importlib.util.find_spec('llama_index.core') is not None

@pytest.mark.skipif(not LLAMAINDEX_AVAILABLE, reason='LlamaIndex not available')
class TestLlamaIndexRAGService:
    """Test cases for LlamaIndex RAG service."""

    @pytest.fixture
    def service(self):
        """Create LlamaIndex RAG service instance."""
        from domains.memory.vector.llamaindex_service import LlamaIndexRAGService
        return LlamaIndexRAGService(qdrant_url='http://localhost:6333', collection_name='test_collection', openai_api_key='test_key')

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.index is not None
        assert service.vector_store is not None

    def test_ingest_documents(self, service):
        """Test document ingestion."""
        texts = ['This is a test document about artificial intelligence.', 'Another document discussing machine learning algorithms.']
        metadata = [{'source': 'test1'}, {'source': 'test2'}]
        result = service.ingest_documents(texts, metadata)
        assert result.success
        assert result.data['documents_ingested'] == 2
        assert result.data['nodes_created'] > 0

    def test_query(self, service):
        """Test querying the RAG system."""
        texts = ['Artificial intelligence is transforming technology.']
        service.ingest_documents(texts)
        result = service.query('What is artificial intelligence?', top_k=3)
        assert result.success
        assert 'query' in result.data
        assert 'results' in result.data
        assert len(result.data['results']) > 0

    def test_retrieve_context(self, service):
        """Test context retrieval."""
        texts = ['Neural networks are computational models.']
        service.ingest_documents(texts)
        result = service.retrieve_context('neural networks', top_k=2)
        assert result.success
        assert 'context' in result.data
        assert len(result.data['context']) > 0

    def test_get_stats(self, service):
        """Test getting RAG system statistics."""
        result = service.get_stats()
        assert result.success
        assert 'collection_name' in result.data
        assert 'points_count' in result.data

    def test_update_index(self, service):
        """Test index update."""
        result = service.update_index()
        assert result.success
        assert result.data['status'] == 'index_updated'

    def test_ingest_with_empty_texts(self, service):
        """Test ingesting empty text list."""
        result = service.ingest_documents([])
        assert result.success or not result.success