import hashlib
import logging
from typing import Any

from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer
from src.memory.qdrant_provider import get_qdrant_client

from src.ultimate_discord_intelligence_bot.step_result import ErrorCategory, StepResult
from src.ultimate_discord_intelligence_bot.tenancy.context import current_tenant, with_tenant


logger = logging.getLogger(__name__)


class SemanticCacheEnhanced:
    """Enhanced semantic cache using vector similarity."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.cache_collection = "semantic_cache"
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure cache collection exists."""
        client = get_qdrant_client()
        collections = client.get_collections().collections

        if not any(c.name == self.cache_collection for c in collections):
            client.create_collection(
                collection_name=self.cache_collection,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE,
                ),
            )

    @with_tenant
    async def get(self, prompt: str, context: dict | None = None) -> StepResult | None:
        """Get cached response for similar prompt."""
        try:
            tenant = current_tenant()
            client = get_qdrant_client()

            # Generate embedding
            embedding = self.encoder.encode(prompt).tolist()

            # Search for similar prompts
            results = client.search(
                collection_name=self.cache_collection,
                query_vector=embedding,
                limit=5,
                query_filter={"must": [{"key": "tenant_id", "match": {"value": tenant.id}}]},
            )

            # Check if we have a good match
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
            tenant = current_tenant()
            client = get_qdrant_client()

            # Generate embedding and ID
            embedding = self.encoder.encode(prompt).tolist()
            prompt_hash = hashlib.md5(f"{tenant.id}:{prompt}".encode()).hexdigest()

            # Store in Qdrant
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
