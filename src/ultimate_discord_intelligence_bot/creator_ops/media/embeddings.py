"""
Embeddings generation and vector storage for semantic search.

This module provides comprehensive embeddings generation with Qdrant storage,
cross-platform retrieval, and semantic search capabilities.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None
from memory.qdrant_provider import get_qdrant_client
from ultimate_discord_intelligence_bot.creator_ops.config import CreatorOpsConfig
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.creator_ops.media.alignment import AlignedTranscript
    from ultimate_discord_intelligence_bot.creator_ops.media.nlp import NLPResult
logger = logging.getLogger(__name__)

@dataclass
class Embedding:
    """Embedding with metadata."""
    vector: list[float]
    text: str
    metadata: dict[str, Any]
    created_at: datetime

@dataclass
class EmbeddingResult:
    """Complete embedding generation result."""
    embeddings: list[Embedding]
    model_name: str
    vector_dimension: int
    processing_time: float
    created_at: datetime

@dataclass
class SearchResult:
    """Semantic search result."""
    text: str
    score: float
    metadata: dict[str, Any]
    start_time: float | None = None
    end_time: float | None = None
    speaker: str | None = None

class EmbeddingsGenerator:
    """
    Embeddings generation with Qdrant storage and semantic search.

    Features:
    - Generate embeddings for transcript segments, clips, posts
    - Store in Qdrant with metadata
    - Cross-platform retrieval
    - Semantic search with similarity scoring
    - Batch processing with progress tracking
    """

    def __init__(self, model_name: str='text-embedding-3-large', config: CreatorOpsConfig | None=None, device: str | None=None) -> None:
        """Initialize embeddings generator."""
        self.config = config or CreatorOpsConfig()
        self.model_name = model_name
        self.device = device or self._get_optimal_device()
        self.model = None
        self.qdrant_client = None
        self._initialize_model()
        self._initialize_qdrant()

    def _get_optimal_device(self) -> str:
        """Get optimal device for embeddings generation."""
        if torch is not None and self.config.use_gpu and torch.cuda.is_available():
            return 'cuda'
        return 'cpu'

    def _initialize_model(self) -> None:
        """Initialize embedding model."""
        if SentenceTransformer is None:
            raise ImportError('sentence-transformers not available. Install ML dependencies: pip install sentence-transformers torch')
        try:
            if self.model_name == 'text-embedding-3-large':
                model_name = 'sentence-transformers/all-MiniLM-L6-v2'
            else:
                model_name = self.model_name
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info(f'Loaded embedding model {model_name} on {self.device}')
        except Exception as e:
            logger.error(f'Failed to initialize embedding model: {e!s}')
            raise

    def _initialize_qdrant(self) -> None:
        """Initialize Qdrant client."""
        try:
            self.qdrant_client = get_qdrant_client()
            collections = self.qdrant_client.get_collections()
            logger.info(f'Connected to Qdrant. Found {len(collections.collections)} collections')
        except Exception as e:
            logger.error(f'Failed to initialize Qdrant client: {e!s}')
            raise

    def generate_embeddings(self, texts: list[str], metadata_list: list[dict[str, Any]] | None=None, batch_size: int=32) -> StepResult:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of texts to embed
            metadata_list: List of metadata for each text
            batch_size: Batch size for processing

        Returns:
            StepResult with EmbeddingResult
        """
        start_time = datetime.utcnow()
        try:
            if not texts:
                return StepResult.fail('No texts provided for embedding generation')
            if metadata_list is None:
                metadata_list = [{} for _ in texts]
            if len(metadata_list) != len(texts):
                return StepResult.fail('Metadata list length must match texts length')
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_metadata = metadata_list[i:i + batch_size]
                batch_embeddings = self.model.encode(batch_texts, convert_to_tensor=False, show_progress_bar=True)
                for _j, (text, metadata, embedding) in enumerate(zip(batch_texts, batch_metadata, batch_embeddings, strict=False)):
                    embedding_obj = Embedding(vector=embedding.tolist(), text=text, metadata=metadata, created_at=datetime.utcnow())
                    all_embeddings.append(embedding_obj)
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result = EmbeddingResult(embeddings=all_embeddings, model_name=self.model_name, vector_dimension=len(all_embeddings[0].vector) if all_embeddings else 0, processing_time=processing_time, created_at=start_time)
            return StepResult.ok(data=result)
        except Exception as e:
            logger.error(f'Embedding generation failed: {e!s}')
            return StepResult.fail(f'Embedding generation failed: {e!s}')

    def generate_transcript_embeddings(self, aligned_transcript: AlignedTranscript, nlp_result: NLPResult | None=None, collection_name: str='creator_ops_transcripts') -> StepResult:
        """
        Generate embeddings for transcript segments and store in Qdrant.

        Args:
            aligned_transcript: Aligned transcript to process
            nlp_result: NLP analysis result (optional)
            collection_name: Qdrant collection name

        Returns:
            StepResult with stored embedding IDs
        """
        try:
            texts = []
            metadata_list = []
            for i, segment in enumerate(aligned_transcript.segments):
                texts.append(segment.text)
                metadata = {'segment_index': i, 'start_time': segment.start_time, 'end_time': segment.end_time, 'speaker': segment.speaker, 'is_overlap': segment.is_overlap, 'confidence': segment.confidence, 'language': segment.language, 'transcript_id': f'transcript_{aligned_transcript.created_at.timestamp()}', 'created_at': aligned_transcript.created_at.isoformat()}
                if nlp_result:
                    sentiment = next((s for s in nlp_result.sentiment_analysis if s.start_time == segment.start_time), None)
                    if sentiment:
                        metadata['sentiment'] = sentiment.label
                        metadata['sentiment_score'] = sentiment.score
                    safety = next((s for s in nlp_result.content_safety if s.start_time == segment.start_time), None)
                    if safety:
                        metadata['toxicity_score'] = safety.toxicity_score
                        metadata['brand_suitability'] = safety.brand_suitability_score
                        metadata['risk_level'] = safety.risk_level
                metadata_list.append(metadata)
            embedding_result = self.generate_embeddings(texts, metadata_list)
            if not embedding_result.success:
                return embedding_result
            stored_ids = self._store_embeddings_in_qdrant(embedding_result.data.embeddings, collection_name)
            return StepResult.ok(data={'stored_ids': stored_ids, 'collection_name': collection_name, 'embedding_count': len(stored_ids)})
        except Exception as e:
            logger.error(f'Transcript embedding generation failed: {e!s}')
            return StepResult.fail(f'Transcript embedding generation failed: {e!s}')

    def _store_embeddings_in_qdrant(self, embeddings: list[Embedding], collection_name: str) -> list[str]:
        """Store embeddings in Qdrant collection."""
        try:
            try:
                self.qdrant_client.get_collection(collection_name)
            except Exception:
                vec_size = len(embeddings[0].vector) if embeddings else 384
                try:
                    from qdrant_client.http import models as _qmodels
                    vec_cfg = _qmodels.VectorParams(size=vec_size, distance=_qmodels.Distance.COSINE)
                except Exception:
                    try:
                        from qdrant_client import models as _legacy_models
                        vec_cfg = _legacy_models.VectorParams(size=vec_size, distance=getattr(_legacy_models.Distance, 'COSINE', 'Cosine'))
                    except Exception:
                        vec_cfg = {'size': vec_size, 'distance': 'Cosine'}
                try:
                    self.qdrant_client.create_collection(collection_name=collection_name, vectors_config=vec_cfg)
                except TypeError:
                    self.qdrant_client.create_collection(collection_name, vectors_config=vec_cfg)
                logger.info(f'Created Qdrant collection: {collection_name}')
            points = []
            for i, embedding in enumerate(embeddings):
                point_id = f'{collection_name}_{i}_{datetime.utcnow().timestamp()}'
                try:
                    from qdrant_client.http import models as _qmodels
                    point = _qmodels.PointStruct(id=point_id, vector=embedding.vector, payload={'text': embedding.text, 'metadata': embedding.metadata, 'created_at': embedding.created_at.isoformat()})
                except Exception:
                    try:
                        from qdrant_client import models as _legacy_models
                        point = _legacy_models.PointStruct(id=point_id, vector=embedding.vector, payload={'text': embedding.text, 'metadata': embedding.metadata, 'created_at': embedding.created_at.isoformat()})
                    except Exception:
                        point = {'id': point_id, 'vector': embedding.vector, 'payload': {'text': embedding.text, 'metadata': embedding.metadata, 'created_at': embedding.created_at.isoformat()}}
                points.append(point)
            self.qdrant_client.upsert(collection_name=collection_name, points=points)
            logger.info(f'Stored {len(points)} embeddings in collection {collection_name}')
            return [point.id for point in points]
        except Exception as e:
            logger.error(f'Failed to store embeddings in Qdrant: {e!s}')
            raise

    def search_similar_content(self, query: str, collection_name: str='creator_ops_transcripts', limit: int=10, score_threshold: float=0.7) -> StepResult:
        """
        Search for similar content using semantic search.

        Args:
            query: Search query
            collection_name: Qdrant collection name
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            StepResult with search results
        """
        try:
            query_embedding = self.model.encode([query], convert_to_tensor=False)[0]
            search_results = self.qdrant_client.search(collection_name=collection_name, query_vector=query_embedding.tolist(), limit=limit, score_threshold=score_threshold)
            results = []
            for result in search_results:
                payload = result.payload
                search_result = SearchResult(text=payload['text'], score=result.score, metadata=payload['metadata'], start_time=payload['metadata'].get('start_time'), end_time=payload['metadata'].get('end_time'), speaker=payload['metadata'].get('speaker'))
                results.append(search_result)
            return StepResult.ok(data={'results': results, 'query': query, 'total_results': len(results), 'collection_name': collection_name})
        except Exception as e:
            logger.error(f'Semantic search failed: {e!s}')
            return StepResult.fail(f'Semantic search failed: {e!s}')

    def get_collection_info(self, collection_name: str) -> StepResult:
        """Get information about a Qdrant collection."""
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            return StepResult.ok(data={'name': collection_name, 'vectors_count': collection_info.vectors_count, 'indexed_vectors_count': collection_info.indexed_vectors_count, 'points_count': collection_info.points_count, 'status': collection_info.status, 'optimizer_status': collection_info.optimizer_status})
        except Exception as e:
            logger.error(f'Failed to get collection info: {e!s}')
            return StepResult.fail(f'Failed to get collection info: {e!s}')

    def delete_collection(self, collection_name: str) -> StepResult:
        """Delete a Qdrant collection."""
        try:
            self.qdrant_client.delete_collection(collection_name)
            logger.info(f'Deleted Qdrant collection: {collection_name}')
            return StepResult.ok(data={'deleted': True, 'collection_name': collection_name})
        except Exception as e:
            logger.error(f'Failed to delete collection: {e!s}')
            return StepResult.fail(f'Failed to delete collection: {e!s}')

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
        return {'model_name': self.model_name, 'device': self.device, 'has_gpu': torch.cuda.is_available() if torch is not None else False, 'vector_dimension': self.model.get_sentence_embedding_dimension() if self.model else 0, 'qdrant_connected': self.qdrant_client is not None}

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.model:
            del self.model
            self.model = None
        if self.qdrant_client:
            pass
        if torch is not None and self.device == 'cuda' and torch.cuda.is_available():
            torch.cuda.empty_cache()