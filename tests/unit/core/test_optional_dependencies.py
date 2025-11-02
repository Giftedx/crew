from unittest.mock import patch
import pytest
from platform.core.optional_dependencies import DependencyManager, HashEmbeddingModel, InMemoryCache, InMemoryVectorStore, MockDiarization, MockTranscription, OptionalDependency, get_cache, get_dependency_manager, get_embedding_model, get_vector_store, is_redis_available, is_sentence_transformers_available

class TestOptionalDependency:
    """Test the OptionalDependency class."""

    def test_available_module(self):
        """Test with available module."""
        dependency = OptionalDependency('os')
        assert dependency.is_available is True
        module = dependency.get_or_fallback()
        assert module is not None

    def test_unavailable_module_with_fallback(self):
        """Test with unavailable module but fallback."""

        def fallback():
            return 'fallback_result'
        dependency = OptionalDependency('nonexistent_module', fallback_fn=fallback)
        assert dependency.is_available is False
        result = dependency.get_or_fallback()
        assert result == 'fallback_result'

    def test_unavailable_module_without_fallback(self):
        """Test with unavailable module and no fallback."""
        dependency = OptionalDependency('nonexistent_module')
        assert dependency.is_available is False
        with pytest.raises(ImportError):
            dependency.get_or_fallback()

class TestDependencyManager:
    """Test the DependencyManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = DependencyManager()

    def test_initialization(self):
        """Test manager initialization."""
        assert 'redis' in self.manager._dependencies
        assert 'sentence_transformers' in self.manager._dependencies
        assert 'qdrant_client' in self.manager._dependencies

    def test_register_dependency(self):
        """Test registering a new dependency."""

        def test_fallback():
            return 'test'
        self.manager.register_dependency('test_dep', 'test_module', fallback_fn=test_fallback)
        assert 'test_dep' in self.manager._dependencies

    def test_set_feature_flag(self):
        """Test setting feature flags."""
        self.manager.set_feature_flag('TEST_FLAG', True)
        assert self.manager._feature_flags['TEST_FLAG'] is True

    def test_get_dependency_with_feature_flag_disabled(self):
        """Test getting dependency with disabled feature flag."""

        def test_fallback():
            return 'test_fallback'
        self.manager.register_dependency('test_dep', 'test_module', fallback_fn=test_fallback, feature_flag='TEST_FLAG')
        result = self.manager.get_dependency('test_dep')
        assert result == 'test_fallback'
        self.manager.set_feature_flag('TEST_FLAG', True)
        result = self.manager.get_dependency('test_dep')
        assert result == 'test_fallback'

    def test_get_dependency_unknown(self):
        """Test getting unknown dependency."""
        with pytest.raises(ValueError):
            self.manager.get_dependency('unknown_dependency')

    def test_is_available(self):
        """Test availability checking."""
        assert 'redis' in self.manager._dependencies
        assert self.manager.is_available('nonexistent') is False

    def test_get_stats(self):
        """Test getting dependency statistics."""
        stats = self.manager.get_stats()
        assert 'redis' in stats
        assert 'sentence_transformers' in stats
        assert 'available' in stats['redis']
        assert 'feature_flag' in stats['redis']

class TestInMemoryCache:
    """Test the InMemoryCache fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = InMemoryCache()

    def test_basic_operations(self):
        """Test basic cache operations."""
        self.cache.set('key1', 'value1')
        assert self.cache.get('key1') == 'value1'
        assert self.cache.get('nonexistent') is None
        self.cache.set('key2', 'value2')
        assert self.cache.get('key2') == 'value2'
        self.cache.delete('key2')
        assert self.cache.get('key2') is None

    def test_ttl_functionality(self):
        """Test TTL functionality."""
        import time
        self.cache.set('ttl_key', 'ttl_value', ex=1)
        assert self.cache.get('ttl_key') == 'ttl_value'
        time.sleep(1.1)
        assert self.cache.get('ttl_key') is None

    def test_clear(self):
        """Test cache clearing."""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        assert self.cache.get('key1') == 'value1'
        assert self.cache.get('key2') == 'value2'
        self.cache.clear()
        assert self.cache.get('key1') is None
        assert self.cache.get('key2') is None

class TestHashEmbeddingModel:
    """Test the HashEmbeddingModel fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        self.model = HashEmbeddingModel(embedding_dim=384)

    def test_encode_batch(self):
        """Test batch encoding."""
        texts = ['Hello world', 'Test text', 'Another text']
        embeddings = self.model.encode(texts)
        assert len(embeddings) == 3
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384
        assert len(embeddings[2]) == 384
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]

    def test_encode_single(self):
        """Test single text encoding."""
        text = 'Hello world'
        embedding = self.model.encode_single(text)
        assert len(embedding) == 384
        assert all((isinstance(x, float) for x in embedding))

    def test_deterministic_encoding(self):
        """Test that encoding is deterministic."""
        text = 'Test text'
        embedding1 = self.model.encode_single(text)
        embedding2 = self.model.encode_single(text)
        assert embedding1 == embedding2

    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        text1 = 'Text one'
        text2 = 'Text two'
        embedding1 = self.model.encode_single(text1)
        embedding2 = self.model.encode_single(text2)
        assert embedding1 != embedding2

class TestInMemoryVectorStore:
    """Test the InMemoryVectorStore fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        self.store = InMemoryVectorStore()

    def test_upsert_and_search(self):
        """Test upsert and search operations."""
        collection_name = 'test_collection'
        points = [{'id': 'vec1', 'vector': [1.0, 0.0, 0.0], 'payload': {'text': 'first'}}, {'id': 'vec2', 'vector': [0.0, 1.0, 0.0], 'payload': {'text': 'second'}}, {'id': 'vec3', 'vector': [0.0, 0.0, 1.0], 'payload': {'text': 'third'}}]
        self.store.upsert(collection_name, points)
        query_vector = [1.0, 0.0, 0.0]
        results = self.store.search(collection_name, query_vector, limit=2)
        assert len(results) == 2
        assert results[0]['id'] == 'vec1'
        assert results[0]['payload']['text'] == 'first'
        assert results[0]['score'] > results[1]['score']

    def test_delete(self):
        """Test vector deletion."""
        collection_name = 'test_collection'
        self.store.upsert(collection_name, [{'id': 'vec1', 'vector': [1.0, 0.0, 0.0]}])
        results = self.store.search(collection_name, [1.0, 0.0, 0.0])
        assert len(results) == 1
        self.store.delete(collection_name, ['vec1'])
        results = self.store.search(collection_name, [1.0, 0.0, 0.0])
        assert len(results) == 0

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        sim1 = self.store._cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
        assert sim1 == 1.0
        sim2 = self.store._cosine_similarity([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        assert sim2 == 0.0
        sim3 = self.store._cosine_similarity([1.0, 0.0, 0.0], [-1.0, 0.0, 0.0])
        assert sim3 == -1.0

class TestMockDiarization:
    """Test the MockDiarization fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        self.diarizer = MockDiarization()

    def test_call_method(self):
        """Test diarization call."""
        result = self.diarizer('/path/to/audio.wav')
        assert 'segments' in result
        assert len(result['segments']) > 0
        segment = result['segments'][0]
        assert 'start' in segment
        assert 'end' in segment
        assert 'speaker' in segment

class TestMockTranscription:
    """Test the MockTranscription fallback."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transcriber = MockTranscription()

    def test_transcribe_method(self):
        """Test transcription."""
        result = self.transcriber.transcribe('/path/to/audio.wav')
        assert 'text' in result
        assert 'segments' in result
        assert len(result['segments']) > 0
        assert result['text'] == 'This is a mock transcription of the audio content.'

    def test_call_method(self):
        """Test call method."""
        result = self.transcriber('/path/to/audio.wav')
        assert 'text' in result
        assert result['text'] == 'This is a mock transcription of the audio content.'

class TestGlobalFunctions:
    """Test global utility functions."""

    def test_get_dependency_manager(self):
        """Test getting global dependency manager."""
        manager = get_dependency_manager()
        assert isinstance(manager, DependencyManager)

    def test_get_cache(self):
        """Test getting cache implementation."""
        cache = get_cache()
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')

    def test_get_embedding_model(self):
        """Test getting embedding model."""
        model = get_embedding_model()
        assert hasattr(model, 'encode')
        assert hasattr(model, 'encode_single')

    def test_get_vector_store(self):
        """Test getting vector store."""
        store = get_vector_store()
        assert hasattr(store, 'upsert')
        assert hasattr(store, 'search')

    def test_availability_checks(self):
        """Test availability check functions."""
        redis_available = is_redis_available()
        st_available = is_sentence_transformers_available()
        assert isinstance(redis_available, bool)
        assert isinstance(st_available, bool)

class TestIntegration:
    """Integration tests for the dependency framework."""

    def test_fallback_behavior(self):
        """Test that fallbacks work when main dependencies are unavailable."""
        manager = DependencyManager()
        with patch.dict('sys.modules', {'redis': None, 'sentence_transformers': None}):
            cache = manager.get_dependency('redis')
            assert isinstance(cache, InMemoryCache)
            embedding_model = manager.get_dependency('sentence_transformers')
            assert isinstance(embedding_model, HashEmbeddingModel)

    def test_feature_flag_control(self):
        """Test feature flag control of dependencies."""
        manager = DependencyManager()

        def test_fallback():
            return 'fallback'
        manager.register_dependency('test_dep', 'test_module', fallback_fn=test_fallback, feature_flag='TEST_FLAG')
        result = manager.get_dependency('test_dep')
        assert result == 'fallback'
        manager.set_feature_flag('TEST_FLAG', True)
        result = manager.get_dependency('test_dep')
        assert result == 'fallback'

    def test_performance_comparison(self):
        """Test performance characteristics of fallbacks."""
        import time
        cache = InMemoryCache()
        start_time = time.time()
        for i in range(1000):
            cache.set(f'key_{i}', f'value_{i}')
            cache.get(f'key_{i}')
        cache_time = time.time() - start_time
        assert cache_time < 1.0
        model = HashEmbeddingModel()
        start_time = time.time()
        texts = [f'test text {i}' for i in range(100)]
        embeddings = model.encode(texts)
        embedding_time = time.time() - start_time
        assert embedding_time < 1.0
        assert len(embeddings) == 100
        assert len(embeddings[0]) == 384