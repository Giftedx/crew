from __future__ import annotations

import importlib
import logging
import time
from collections.abc import Callable
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    def get(self, key: str) -> Any:
        """Get value from cache."""
        ...

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        """Set value in cache with optional expiration."""
        ...

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        ...

    def clear(self) -> None:
        """Clear all cache entries."""
        ...


class EmbeddingProtocol(Protocol):
    """Protocol for embedding implementations."""

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts into embeddings."""
        ...

    def encode_single(self, text: str) -> list[float]:
        """Encode single text into embedding."""
        ...


class DependencyManager:
    """Manages optional dependencies with graceful fallbacks."""

    def __init__(self):
        self._dependencies: dict[str, OptionalDependency] = {}
        self._feature_flags: dict[str, bool] = {}
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize default optional dependencies."""

        # Redis cache fallback
        self._dependencies["redis"] = OptionalDependency(
            module_name="redis", fallback_fn=self._create_redis_fallback, feature_flag="ENABLE_REDIS_CACHE"
        )

        # Sentence transformers fallback
        self._dependencies["sentence_transformers"] = OptionalDependency(
            module_name="sentence_transformers",
            fallback_fn=self._create_sentence_transformers_fallback,
            feature_flag="ENABLE_SENTENCE_TRANSFORMERS",
        )

        # Qdrant client fallback
        self._dependencies["qdrant_client"] = OptionalDependency(
            module_name="qdrant_client",
            fallback_fn=self._create_qdrant_fallback,
            feature_flag="ENABLE_QDRANT_VECTOR_STORE",
        )

        # Pyannote audio fallback
        self._dependencies["pyannote_audio"] = OptionalDependency(
            module_name="pyannote.audio",
            fallback_fn=self._create_pyannote_fallback,
            feature_flag="ENABLE_SPEAKER_DIARIZATION",
        )

        # Whisper fallback
        self._dependencies["whisper"] = OptionalDependency(
            module_name="whisper",
            fallback_fn=self._create_whisper_fallback,
            feature_flag="ENABLE_WHISPER_TRANSCRIPTION",
        )

        # Faster-whisper fallback
        self._dependencies["faster_whisper"] = OptionalDependency(
            module_name="faster_whisper",
            fallback_fn=self._create_faster_whisper_fallback,
            feature_flag="ENABLE_FAST_WHISPER",
        )

    def _create_redis_fallback(self) -> Any:
        """Create Redis fallback implementation."""
        return InMemoryCache()

    def _create_sentence_transformers_fallback(self) -> Any:
        """Create sentence transformers fallback implementation."""
        return HashEmbeddingModel()

    def _create_qdrant_fallback(self) -> Any:
        """Create Qdrant fallback implementation."""
        return InMemoryVectorStore()

    def _create_pyannote_fallback(self) -> Any:
        """Create Pyannote fallback implementation."""
        return MockDiarization()

    def _create_whisper_fallback(self) -> Any:
        """Create Whisper fallback implementation."""
        return MockTranscription()

    def _create_faster_whisper_fallback(self) -> Any:
        """Create Faster-whisper fallback implementation."""
        return MockTranscription()

    def register_dependency(
        self, name: str, module_name: str, fallback_fn: Callable | None = None, feature_flag: str | None = None
    ) -> None:
        """Register an optional dependency."""
        self._dependencies[name] = OptionalDependency(
            module_name=module_name, fallback_fn=fallback_fn, feature_flag=feature_flag
        )

    def set_feature_flag(self, flag_name: str, enabled: bool) -> None:
        """Set feature flag for optional dependency."""
        self._feature_flags[flag_name] = enabled

    def get_dependency(self, name: str) -> Any:
        """Get dependency or fallback implementation."""
        if name not in self._dependencies:
            raise ValueError(f"Unknown dependency: {name}")

        dependency = self._dependencies[name]

        # Check feature flag first
        if dependency.feature_flag and not self._feature_flags.get(dependency.feature_flag, False):
            logger.info(f"Feature flag '{dependency.feature_flag}' disabled, using fallback for '{name}'")
            if dependency.fallback_fn:
                return dependency.fallback_fn()
            else:
                raise ImportError(f"Dependency '{name}' not available and no fallback provided")

        # Try to get the actual module
        try:
            return dependency.get_or_fallback()
        except ImportError as e:
            logger.warning(f"Failed to import '{dependency.module_name}': {e}")
            if dependency.fallback_fn:
                logger.info(f"Using fallback implementation for '{name}'")
                return dependency.fallback_fn()
            else:
                raise

    def is_available(self, name: str) -> bool:
        """Check if dependency is available (including fallback)."""
        if name not in self._dependencies:
            return False

        dependency = self._dependencies[name]

        # Check feature flag first
        if dependency.feature_flag and not self._feature_flags.get(dependency.feature_flag, False):
            # Feature disabled, check if fallback is available
            return dependency.fallback_fn is not None

        # Check if actual module is available
        return dependency.is_available or dependency.fallback_fn is not None

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about dependency availability."""
        stats = {}
        for name, dependency in self._dependencies.items():
            stats[name] = {
                "available": dependency.is_available,
                "feature_flag": dependency.feature_flag,
                "feature_enabled": self._feature_flags.get(dependency.feature_flag, False)
                if dependency.feature_flag
                else None,
                "using_fallback": not dependency.is_available and dependency.fallback_fn is not None,
            }
        return stats


class OptionalDependency:
    """Wrapper for optional dependencies with fallbacks."""

    def __init__(self, module_name: str, fallback_fn: Callable | None = None, feature_flag: str | None = None):
        self.module_name = module_name
        self.fallback_fn = fallback_fn
        self.feature_flag = feature_flag
        self._module = None
        self._available = None

    @property
    def is_available(self) -> bool:
        """Check if dependency is available."""
        if self._available is None:
            try:
                self._module = importlib.import_module(self.module_name)
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    def get_or_fallback(self) -> Any:
        """Get module or fallback implementation."""
        if self.is_available:
            return self._module
        elif self.fallback_fn:
            return self.fallback_fn()
        else:
            raise ImportError(f"Required dependency '{self.module_name}' not available and no fallback provided")


# Global dependency manager instance
_dependency_manager = DependencyManager()


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager."""
    return _dependency_manager


def get_cache() -> CacheProtocol:
    """Get cache implementation (Redis or in-memory)."""
    return _dependency_manager.get_dependency("redis")


def get_embedding_model() -> EmbeddingProtocol:
    """Get embedding model (sentence-transformers or hash-based)."""
    return _dependency_manager.get_dependency("sentence_transformers")


def get_vector_store() -> Any:
    """Get vector store (Qdrant or in-memory)."""
    return _dependency_manager.get_dependency("qdrant_client")


def get_diarization_model() -> Any:
    """Get diarization model (Pyannote or mock)."""
    return _dependency_manager.get_dependency("pyannote_audio")


def get_transcription_model() -> Any:
    """Get transcription model (Whisper or mock)."""
    return _dependency_manager.get_dependency("whisper")


def get_fast_transcription_model() -> Any:
    """Get fast transcription model (Faster-whisper or mock)."""
    return _dependency_manager.get_dependency("faster_whisper")


# Fallback Implementations


class InMemoryCache:
    """In-memory cache fallback for Redis."""

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._ttl_cache: dict[str, float] = {}

    def get(self, key: str) -> Any:
        """Get value from cache."""
        if key in self._cache:
            # Check TTL
            if key in self._ttl_cache:
                if time.time() > self._ttl_cache[key]:
                    del self._cache[key]
                    del self._ttl_cache[key]
                    return None
            return self._cache[key].get("value")
        return None

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        """Set value in cache with optional expiration."""
        self._cache[key] = {"value": value}
        if ex is not None:
            self._ttl_cache[key] = time.time() + ex

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)
        self._ttl_cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._ttl_cache.clear()


class HashEmbeddingModel:
    """Hash-based embedding fallback for sentence-transformers."""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Generate hash-based embeddings."""
        import hashlib

        embeddings = []
        for text in texts:
            # Create deterministic hash from text
            hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

            # Create embedding vector
            embedding = [float((hash_val + i) % 1000) / 1000.0 for i in range(self.embedding_dim)]
            embeddings.append(embedding)

        return embeddings

    def encode_single(self, text: str) -> list[float]:
        """Encode single text into embedding."""
        embeddings = self.encode([text])
        return embeddings[0]


class InMemoryVectorStore:
    """In-memory vector store fallback for Qdrant."""

    def __init__(self):
        self._vectors: dict[str, list[float]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    def upsert(self, collection_name: str, points: list[dict[str, Any]]) -> None:
        """Upsert vectors to collection."""
        for point in points:
            vector_id = point["id"]
            vector = point["vector"]
            metadata = point.get("payload", {})

            self._vectors[vector_id] = vector
            self._metadata[vector_id] = metadata

    def search(
        self, collection_name: str, query_vector: list[float], limit: int = 10, **kwargs
    ) -> list[dict[str, Any]]:
        """Search for similar vectors."""
        results = []

        for vector_id, vector in self._vectors.items():
            # Simple cosine similarity (mock implementation)
            similarity = self._cosine_similarity(query_vector, vector)

            results.append({"id": vector_id, "score": similarity, "payload": self._metadata.get(vector_id, {})})

        # Sort by similarity and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def delete(self, collection_name: str, point_ids: list[str]) -> None:
        """Delete vectors from collection."""
        for point_id in point_ids:
            self._vectors.pop(point_id, None)
            self._metadata.pop(point_id, None)

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


class MockDiarization:
    """Mock diarization for Pyannote fallback."""

    def __init__(self):
        pass

    def __call__(self, audio_path: str, **kwargs) -> dict[str, Any]:
        """Mock diarization call."""
        return {
            "segments": [
                {"start": 0.0, "end": 60.0, "speaker": "SPEAKER_01"},
                {"start": 60.0, "end": 120.0, "speaker": "SPEAKER_02"},
            ]
        }


class MockTranscription:
    """Mock transcription for Whisper fallback."""

    def __init__(self):
        pass

    def transcribe(self, audio_path: str, **kwargs) -> dict[str, Any]:
        """Mock transcription call."""
        return {
            "text": "This is a mock transcription of the audio content.",
            "segments": [
                {"start": 0.0, "end": 10.0, "text": "This is a mock transcription"},
                {"start": 10.0, "end": 20.0, "text": "of the audio content."},
            ],
        }

    def __call__(self, audio_path: str, **kwargs) -> dict[str, Any]:
        """Mock call method."""
        return self.transcribe(audio_path, **kwargs)


# Utility functions for checking dependency availability


def is_redis_available() -> bool:
    """Check if Redis is available."""
    return _dependency_manager.is_available("redis")


def is_sentence_transformers_available() -> bool:
    """Check if sentence-transformers is available."""
    return _dependency_manager.is_available("sentence_transformers")


def is_qdrant_available() -> bool:
    """Check if Qdrant is available."""
    return _dependency_manager.is_available("qdrant_client")


def is_pyannote_available() -> bool:
    """Check if Pyannote is available."""
    return _dependency_manager.is_available("pyannote_audio")


def is_whisper_available() -> bool:
    """Check if Whisper is available."""
    return _dependency_manager.is_available("whisper")


def is_faster_whisper_available() -> bool:
    """Check if Faster-whisper is available."""
    return _dependency_manager.is_available("faster_whisper")


def get_dependency_stats() -> dict[str, Any]:
    """Get statistics about all dependencies."""
    return _dependency_manager.get_stats()
