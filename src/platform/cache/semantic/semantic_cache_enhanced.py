import hashlib
import logging
from typing import Any

from ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, with_tenant


logger = logging.getLogger(__name__)


class SemanticCacheEnhanced:
    """Enhanced semantic cache using vector similarity."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        # Lazy import to avoid circular dependency
        try:
            from sentence_transformers import SentenceTransformer

            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            logger.warning("Failed to import sentence transformer for semantic cache")
            self.encoder = None
        self.cache_collection = "semantic_cache"
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure cache collection exists."""
        # Lazy import to avoid circular dependency
        try:
            from qdrant_client.models import Distance, VectorParams

            from domains.memory.vector.client_factory import get_qdrant_client

            client = get_qdrant_client()
        except Exception:
            logger.warning("Failed to import qdrant client for semantic cache")
            return
        collections = client.get_collections().collections
        if not any(c.name == self.cache_collection for c in collections):
            client.create_collection(
                collection_name=self.cache_collection, vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )

    @with_tenant
    async def get(self, prompt: str, context: dict | None = None) -> StepResult | None:
        """Get cached response for similar prompt."""
        try:
            if self.encoder is None:
                logger.warning("Semantic cache encoder not available")
                return None
            tenant = current_tenant()
            # Lazy import to avoid circular dependency
            from domains.memory.vector.client_factory import get_qdrant_client

            client = get_qdrant_client()
            embedding = self.encoder.encode(prompt).tolist()
            results = client.search(
                collection_name=self.cache_collection,
                query_vector=embedding,
                limit=5,
                query_filter={"must": [{"key": "tenant_id", "match": {"value": tenant.id}}]},
            )
            if results and results[0].score >= self.similarity_threshold:
                logger.info(f"Semantic cache hit with score {results[0].score}")
                return StepResult.ok(
                    result=results[0].payload["response"],
                    metadata={"cache_hit": True, "similarity_score": results[0].score},
                )
            return None
        except Exception as e:
            logger.error(f"Semantic cache get failed: {e}")
            return None

    @with_tenant
    async def set(self, prompt: str, response: Any, context: dict | None = None) -> StepResult:
        """Cache a prompt-response pair."""
        try:
            if self.encoder is None:
                logger.warning("Semantic cache encoder not available")
                return StepResult.fail(error="Encoder not available", error_category=ErrorCategory.CACHE_ERROR)
            tenant = current_tenant()
            # Lazy import to avoid circular dependency
            from qdrant_client.models import PointStruct

            from domains.memory.vector.client_factory import get_qdrant_client

            client = get_qdrant_client()
            embedding = self.encoder.encode(prompt).tolist()
            prompt_hash = hashlib.md5(f"{tenant.id}:{prompt}".encode()).hexdigest()
            client.upsert(
                collection_name=self.cache_collection,
                points=[
                    PointStruct(
                        id=prompt_hash,
                        vector=embedding,
                        payload={
                            "tenant_id": tenant.id,
                            "prompt": prompt,
                            "response": response,
                            "context": context or {},
                        },
                    )
                ],
            )
            return StepResult.ok(result={"cached": True}, metadata={"cache_id": prompt_hash})
        except Exception as e:
            logger.error(f"Semantic cache set failed: {e}")
            return StepResult.fail(error=str(e), error_category=ErrorCategory.CACHE_ERROR)
