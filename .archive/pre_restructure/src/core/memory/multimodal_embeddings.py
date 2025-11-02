"""
Multi-modal embeddings system for enhanced content understanding.

This module provides comprehensive multi-modal embedding capabilities for text,
visual, and audio content, enabling cross-modal similarity and retrieval.
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


logger = logging.getLogger(__name__)


class EmbeddingType(Enum):
    """Types of embeddings supported."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class EmbeddingModel(Enum):
    """Embedding models available."""

    # Text models
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"

    # Image models
    CLIP_VIT_BASE_PATCH32 = "clip-vit-base-patch32"
    CLIP_VIT_LARGE_PATCH14 = "clip-vit-large-patch14"
    RESNET_50 = "resnet-50"

    # Audio models
    WHISPER_EMBEDDINGS = "whisper-embeddings"
    WAV2VEC2 = "wav2vec2"
    AUDIO_CLIP = "audio-clip"

    # Multi-modal models
    CLIP_MULTIMODAL = "clip-multimodal"
    BLIP2 = "blip2"
    LLAVA = "llava"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    # Model selection
    text_model: EmbeddingModel = EmbeddingModel.TEXT_EMBEDDING_3_SMALL
    image_model: EmbeddingModel = EmbeddingModel.CLIP_VIT_BASE_PATCH32
    audio_model: EmbeddingModel = EmbeddingModel.WHISPER_EMBEDDINGS

    # Embedding parameters
    embedding_dimension: int = 1536  # OpenAI ada-002 dimension
    max_text_length: int = 8192
    max_audio_duration: float = 30.0  # seconds
    image_size: tuple[int, int] = (224, 224)

    # Performance settings
    batch_size: int = 32
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600 * 24  # 24 hours

    # Cross-modal settings
    enable_cross_modal: bool = True
    cross_modal_threshold: float = 0.7
    enable_multimodal_fusion: bool = True

    # Quality settings
    normalize_embeddings: bool = True
    enable_quantization: bool = False
    quantization_bits: int = 8


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embedding: np.ndarray
    embedding_type: EmbeddingType
    model_used: EmbeddingModel
    content_hash: str
    metadata: dict[str, Any]
    processing_time: float
    confidence_score: float = 1.0

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return len(self.embedding)

    @property
    def normalized_embedding(self) -> np.ndarray:
        """Get normalized embedding."""
        norm = np.linalg.norm(self.embedding)
        if norm == 0:
            return self.embedding
        return self.embedding / norm


@dataclass
class MultiModalEmbedding:
    """Multi-modal embedding combining multiple modalities."""

    text_embedding: EmbeddingResult | None = None
    image_embedding: EmbeddingResult | None = None
    audio_embedding: EmbeddingResult | None = None

    # Fused embedding
    fused_embedding: np.ndarray | None = None
    fusion_method: str = "weighted_average"

    # Metadata
    content_id: str = ""
    timestamp: float = 0.0
    confidence_scores: dict[str, float] = None

    def __post_init__(self):
        if self.confidence_scores is None:
            self.confidence_scores = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    @property
    def has_text(self) -> bool:
        """Check if text embedding is available."""
        return self.text_embedding is not None

    @property
    def has_image(self) -> bool:
        """Check if image embedding is available."""
        return self.image_embedding is not None

    @property
    def has_audio(self) -> bool:
        """Check if audio embedding is available."""
        return self.audio_embedding is not None

    @property
    def modality_count(self) -> int:
        """Get number of modalities present."""
        return sum([self.has_text, self.has_image, self.has_audio])

    def get_primary_embedding(self) -> np.ndarray | None:
        """Get the primary embedding (fused if available, otherwise best single modality)."""
        if self.fused_embedding is not None:
            return self.fused_embedding

        # Return highest confidence single modality
        embeddings = []
        if self.text_embedding:
            embeddings.append((self.text_embedding.confidence_score, self.text_embedding.embedding))
        if self.image_embedding:
            embeddings.append((self.image_embedding.confidence_score, self.image_embedding.embedding))
        if self.audio_embedding:
            embeddings.append((self.audio_embedding.confidence_score, self.audio_embedding.embedding))

        if embeddings:
            # Sort by confidence and return highest
            embeddings.sort(key=lambda x: x[0], reverse=True)
            return embeddings[0][1]

        return None


class MultiModalEmbeddingGenerator:
    """
    Multi-modal embedding generator with support for text, image, and audio content.

    Provides unified interface for generating embeddings across different modalities
    with cross-modal similarity and fusion capabilities.
    """

    def __init__(self, config: EmbeddingConfig | None = None):
        """Initialize multi-modal embedding generator."""
        self.config = config or EmbeddingConfig()
        self._cache: dict[str, EmbeddingResult] = {}
        self._model_cache: dict[EmbeddingModel, Any] = {}

        # Initialize models
        self._initialize_models()

        logger.info(f"Multi-modal embedding generator initialized with config: {self.config}")

    def _initialize_models(self) -> None:
        """Initialize embedding models."""
        try:
            # Initialize text embedding model
            self._load_text_model()

            # Initialize image embedding model
            self._load_image_model()

            # Initialize audio embedding model
            self._load_audio_model()

        except Exception as e:
            logger.warning(f"Some embedding models failed to load: {e}")

    def _load_text_model(self) -> None:
        """Load text embedding model."""
        try:
            # For now, we'll use a placeholder for the actual model loading
            # In production, this would load the actual embedding model
            self._model_cache[self.config.text_model] = "text_model_loaded"
            logger.info(f"Text model {self.config.text_model.value} loaded")
        except Exception as e:
            logger.error(f"Failed to load text model: {e}")

    def _load_image_model(self) -> None:
        """Load image embedding model."""
        try:
            # Placeholder for image model loading
            self._model_cache[self.config.image_model] = "image_model_loaded"
            logger.info(f"Image model {self.config.image_model.value} loaded")
        except Exception as e:
            logger.error(f"Failed to load image model: {e}")

    def _load_audio_model(self) -> None:
        """Load audio embedding model."""
        try:
            # Placeholder for audio model loading
            self._model_cache[self.config.audio_model] = "audio_model_loaded"
            logger.info(f"Audio model {self.config.audio_model.value} loaded")
        except Exception as e:
            logger.error(f"Failed to load audio model: {e}")

    async def generate_text_embedding(self, text: str, model: EmbeddingModel | None = None) -> EmbeddingResult:
        """Generate embedding for text content."""
        start_time = time.time()

        # Check cache
        content_hash = self._hash_content(text, EmbeddingType.TEXT)
        if self.config.enable_caching and content_hash in self._cache:
            cached_result = self._cache[content_hash]
            if self._is_cache_valid(cached_result):
                return cached_result

        # Validate input
        if len(text) > self.config.max_text_length:
            text = text[: self.config.max_text_length]

        # Generate embedding
        try:
            # Placeholder for actual embedding generation
            embedding = await self._generate_text_embedding_impl(text, model)

            result = EmbeddingResult(
                embedding=embedding,
                embedding_type=EmbeddingType.TEXT,
                model_used=model or self.config.text_model,
                content_hash=content_hash,
                metadata={
                    "text_length": len(text),
                    "truncated": len(text) > self.config.max_text_length,
                },
                processing_time=time.time() - start_time,
                confidence_score=1.0,
            )

            # Cache result
            if self.config.enable_caching:
                self._cache[content_hash] = result

            return result

        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise

    async def generate_image_embedding(
        self,
        image_data: str | bytes | Image.Image | Path,
        model: EmbeddingModel | None = None,
    ) -> EmbeddingResult:
        """Generate embedding for image content."""
        start_time = time.time()

        # Process image data
        image = await self._process_image_data(image_data)

        # Check cache
        content_hash = self._hash_image(image)
        if self.config.enable_caching and content_hash in self._cache:
            cached_result = self._cache[content_hash]
            if self._is_cache_valid(cached_result):
                return cached_result

        # Generate embedding
        try:
            # Placeholder for actual embedding generation
            embedding = await self._generate_image_embedding_impl(image, model)

            result = EmbeddingResult(
                embedding=embedding,
                embedding_type=EmbeddingType.IMAGE,
                model_used=model or self.config.image_model,
                content_hash=content_hash,
                metadata={"image_size": image.size, "image_mode": image.mode},
                processing_time=time.time() - start_time,
                confidence_score=1.0,
            )

            # Cache result
            if self.config.enable_caching:
                self._cache[content_hash] = result

            return result

        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            raise

    async def generate_audio_embedding(
        self, audio_data: str | bytes | Path, model: EmbeddingModel | None = None
    ) -> EmbeddingResult:
        """Generate embedding for audio content."""
        start_time = time.time()

        # Process audio data
        audio_array = await self._process_audio_data(audio_data)

        # Check cache
        content_hash = self._hash_audio(audio_array)
        if self.config.enable_caching and content_hash in self._cache:
            cached_result = self._cache[content_hash]
            if self._is_cache_valid(cached_result):
                return cached_result

        # Generate embedding
        try:
            # Placeholder for actual embedding generation
            embedding = await self._generate_audio_embedding_impl(audio_array, model)

            result = EmbeddingResult(
                embedding=embedding,
                embedding_type=EmbeddingType.AUDIO,
                model_used=model or self.config.audio_model,
                content_hash=content_hash,
                metadata={"audio_length": len(audio_array), "sample_rate": 16000},
                processing_time=time.time() - start_time,
                confidence_score=1.0,
            )

            # Cache result
            if self.config.enable_caching:
                self._cache[content_hash] = result

            return result

        except Exception as e:
            logger.error(f"Failed to generate audio embedding: {e}")
            raise

    async def generate_multimodal_embedding(
        self,
        text: str | None = None,
        image_data: str | bytes | Image.Image | Path | None = None,
        audio_data: str | bytes | Path | None = None,
        content_id: str = "",
    ) -> MultiModalEmbedding:
        """Generate multi-modal embedding combining multiple modalities."""
        start_time = time.time()

        # Generate individual embeddings
        text_embedding = None
        image_embedding = None
        audio_embedding = None

        if text:
            text_embedding = await self.generate_text_embedding(text)

        if image_data:
            image_embedding = await self.generate_image_embedding(image_data)

        if audio_data:
            audio_embedding = await self.generate_audio_embedding(audio_data)

        # Create multi-modal embedding
        multimodal = MultiModalEmbedding(
            text_embedding=text_embedding,
            image_embedding=image_embedding,
            audio_embedding=audio_embedding,
            content_id=content_id or self._generate_content_id(text, image_data, audio_data),
            timestamp=time.time(),
            confidence_scores={
                "text": text_embedding.confidence_score if text_embedding else 0.0,
                "image": image_embedding.confidence_score if image_embedding else 0.0,
                "audio": audio_embedding.confidence_score if audio_embedding else 0.0,
            },
        )

        # Generate fused embedding if multiple modalities present
        if multimodal.modality_count > 1 and self.config.enable_multimodal_fusion:
            multimodal.fused_embedding = await self._fuse_embeddings(multimodal)
            multimodal.fusion_method = "weighted_average"

        processing_time = time.time() - start_time
        logger.info(
            f"Generated multi-modal embedding with {multimodal.modality_count} modalities in {processing_time:.3f}s"
        )

        return multimodal

    async def _generate_text_embedding_impl(self, text: str, model: EmbeddingModel | None = None) -> np.ndarray:
        """Implementation of text embedding generation."""
        # Placeholder implementation - in production this would call the actual model
        # For now, generate a random embedding of the correct dimension
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.normal(0, 1, self.config.embedding_dimension).astype(np.float32)

        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)

        return embedding

    async def _generate_image_embedding_impl(
        self, image: Image.Image, model: EmbeddingModel | None = None
    ) -> np.ndarray:
        """Implementation of image embedding generation."""
        # Placeholder implementation
        np.random.seed(hash(image.tobytes()) % 2**32)
        embedding = np.random.normal(0, 1, self.config.embedding_dimension).astype(np.float32)

        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)

        return embedding

    async def _generate_audio_embedding_impl(
        self, audio_array: np.ndarray, model: EmbeddingModel | None = None
    ) -> np.ndarray:
        """Implementation of audio embedding generation."""
        # Placeholder implementation
        np.random.seed(hash(audio_array.tobytes()) % 2**32)
        embedding = np.random.normal(0, 1, self.config.embedding_dimension).astype(np.float32)

        if self.config.normalize_embeddings:
            embedding = embedding / np.linalg.norm(embedding)

        return embedding

    async def _process_image_data(self, image_data: str | bytes | Image.Image | Path) -> Image.Image:
        """Process various image data formats into PIL Image."""
        if isinstance(image_data, Image.Image):
            return image_data

        if isinstance(image_data, (str, Path)):
            # Load from file
            return Image.open(image_data)

        if isinstance(image_data, bytes):
            # Load from bytes
            return Image.open(io.BytesIO(image_data))

        raise ValueError(f"Unsupported image data type: {type(image_data)}")

    async def _process_audio_data(self, audio_data: str | bytes | Path) -> np.ndarray:
        """Process various audio data formats into numpy array."""
        # Placeholder implementation - in production this would use librosa or similar
        # For now, return a random audio array
        duration = min(self.config.max_audio_duration, 10.0)  # Default 10 seconds
        sample_rate = 16000
        length = int(duration * sample_rate)

        np.random.seed(hash(str(audio_data)) % 2**32)
        return np.random.normal(0, 0.1, length).astype(np.float32)

    async def _fuse_embeddings(self, multimodal: MultiModalEmbedding) -> np.ndarray:
        """Fuse multiple modality embeddings into a single embedding."""
        embeddings = []
        weights = []

        if multimodal.text_embedding:
            embeddings.append(multimodal.text_embedding.embedding)
            weights.append(multimodal.confidence_scores.get("text", 1.0))

        if multimodal.image_embedding:
            embeddings.append(multimodal.image_embedding.embedding)
            weights.append(multimodal.confidence_scores.get("image", 1.0))

        if multimodal.audio_embedding:
            embeddings.append(multimodal.audio_embedding.embedding)
            weights.append(multimodal.confidence_scores.get("audio", 1.0))

        if not embeddings:
            raise ValueError("No embeddings to fuse")

        # Weighted average fusion
        embeddings = np.array(embeddings)
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # Normalize weights

        fused = np.average(embeddings, axis=0, weights=weights)

        if self.config.normalize_embeddings:
            fused = fused / np.linalg.norm(fused)

        return fused

    def _hash_content(self, content: str, content_type: EmbeddingType) -> str:
        """Generate hash for content caching."""
        return hashlib.sha256(f"{content_type.value}:{content}".encode()).hexdigest()

    def _hash_image(self, image: Image.Image) -> str:
        """Generate hash for image caching."""
        return hashlib.sha256(image.tobytes()).hexdigest()

    def _hash_audio(self, audio_array: np.ndarray) -> str:
        """Generate hash for audio caching."""
        return hashlib.sha256(audio_array.tobytes()).hexdigest()

    def _generate_content_id(
        self,
        text: str | None = None,
        image_data: Any | None = None,
        audio_data: Any | None = None,
    ) -> str:
        """Generate unique content ID."""
        content_parts = []
        if text:
            content_parts.append(f"text:{hash(text)}")
        if image_data:
            content_parts.append(f"image:{hash(str(image_data))}")
        if audio_data:
            content_parts.append(f"audio:{hash(str(audio_data))}")

        return hashlib.md5("|".join(content_parts).encode(), usedforsecurity=False).hexdigest()  # nosec B324 - content fingerprint only

    def _is_cache_valid(self, result: EmbeddingResult) -> bool:
        """Check if cached result is still valid."""
        return time.time() - result.metadata.get("cached_at", 0) < self.config.cache_ttl_seconds

    def calculate_similarity(
        self,
        embedding1: EmbeddingResult | MultiModalEmbedding,
        embedding2: EmbeddingResult | MultiModalEmbedding,
    ) -> float:
        """Calculate cosine similarity between embeddings."""
        # Get primary embeddings
        emb1 = self._get_embedding_array(embedding1)
        emb2 = self._get_embedding_array(embedding2)

        if emb1 is None or emb2 is None:
            return 0.0

        # Ensure embeddings are normalized
        if self.config.normalize_embeddings:
            emb1 = emb1 / np.linalg.norm(emb1)
            emb2 = emb2 / np.linalg.norm(emb2)

        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2)
        return float(similarity)

    def _get_embedding_array(self, embedding: EmbeddingResult | MultiModalEmbedding) -> np.ndarray | None:
        """Extract embedding array from various embedding types."""
        if isinstance(embedding, EmbeddingResult):
            return embedding.embedding

        if isinstance(embedding, MultiModalEmbedding):
            return embedding.get_primary_embedding()

        return None

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        text_entries = sum(1 for result in self._cache.values() if result.embedding_type == EmbeddingType.TEXT)
        image_entries = sum(1 for result in self._cache.values() if result.embedding_type == EmbeddingType.IMAGE)
        audio_entries = sum(1 for result in self._cache.values() if result.embedding_type == EmbeddingType.AUDIO)

        return {
            "total_entries": total_entries,
            "text_entries": text_entries,
            "image_entries": image_entries,
            "audio_entries": audio_entries,
            "cache_hit_rate": getattr(self, "_cache_hits", 0) / max(1, getattr(self, "_cache_requests", 1)),
        }

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
