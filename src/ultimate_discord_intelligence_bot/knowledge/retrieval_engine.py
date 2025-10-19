"""Unified Retrieval Engine - Multi-source retrieval with ranking and de-duplication

This engine provides sophisticated retrieval capabilities that combine results
from multiple memory backends, rank them by relevance, and provide intelligent
de-duplication and context building.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant

logger = logging.getLogger(__name__)


@dataclass
class RetrievalQuery:
    """Structured query for retrieval operations"""

    text: str
    intent: str = "general"  # general, fact_check, debate_analysis, creator_intel
    context: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    min_confidence: float = 0.5
    include_metadata: bool = True


@dataclass
class RankedResult:
    """Result with ranking information"""

    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    confidence: float = 1.0
    relevance_score: float = 1.0
    rank: int = 0
    tenant_id: str = "default"
    workspace_id: str = "main"

    @property
    def combined_score(self) -> float:
        """Combined score for ranking"""
        return (self.confidence * 0.6) + (self.relevance_score * 0.4)


@dataclass
class RetrievalConfig:
    """Configuration for retrieval engine"""

    enable_semantic_ranking: bool = True
    enable_content_deduplication: bool = True
    enable_metadata_fusion: bool = True
    similarity_threshold: float = 0.7
    max_results_per_source: int = 50
    fusion_strategy: str = "weighted_average"  # weighted_average, best_of_each, hybrid


class UnifiedRetrievalEngine:
    """Advanced retrieval engine with multi-source ranking and fusion"""

    def __init__(self, config: Optional[RetrievalConfig] = None):
        self.config = config or RetrievalConfig()
        self.query_cache = {}  # Simple query result cache
        self.ranking_weights = {
            "semantic_similarity": 0.4,
            "confidence": 0.3,
            "recency": 0.2,
            "source_authority": 0.1,
        }

    async def retrieve(
        self,
        query: RetrievalQuery,
        unified_memory_service,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> StepResult:
        """Perform sophisticated multi-source retrieval with ranking"""
        try:
            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            # Check query cache first
            cache_key = self._get_cache_key(query, tenant_id, workspace_id)
            if cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                logger.debug(f"Retrieved from cache: {cache_key}")
                return cached_result

            # Perform retrieval from unified memory service
            memory_result = await unified_memory_service.retrieve(
                query=query.text,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                filters=query.filters,
                limit=query.limit * 3,  # Get more for ranking
            )

            if not memory_result.success:
                return StepResult.fail(
                    f"Memory retrieval failed: {memory_result.error}"
                )

            # Convert to RankedResult objects
            raw_results = memory_result.data.get("results", [])
            ranked_results = []

            for i, result in enumerate(raw_results):
                ranked_result = RankedResult(
                    content=result.content,
                    metadata=result.metadata,
                    source=result.source,
                    confidence=result.confidence,
                    tenant_id=tenant_id,
                    workspace_id=workspace_id,
                )
                ranked_results.append(ranked_result)

            # Apply ranking and fusion
            final_results = await self._rank_and_fuse_results(
                ranked_results, query, tenant_id, workspace_id
            )

            # Apply deduplication if enabled
            if self.config.enable_content_deduplication:
                final_results = self._deduplicate_results(final_results, query)

            # Limit results
            final_results = final_results[: query.limit]

            # Build response
            response_data = {
                "results": final_results,
                "query": {
                    "text": query.text,
                    "intent": query.intent,
                    "filters": query.filters,
                },
                "metadata": {
                    "total_sources": len(set(r.source for r in final_results)),
                    "avg_confidence": sum(r.confidence for r in final_results)
                    / len(final_results)
                    if final_results
                    else 0,
                    "avg_relevance": sum(r.relevance_score for r in final_results)
                    / len(final_results)
                    if final_results
                    else 0,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                },
            }

            result = StepResult.ok(data=response_data)

            # Cache the result
            self.query_cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Error in unified retrieval: {e}", exc_info=True)
            return StepResult.fail(f"Retrieval engine failed: {str(e)}")

    async def _rank_and_fuse_results(
        self,
        results: List[RankedResult],
        query: RetrievalQuery,
        tenant_id: str,
        workspace_id: str,
    ) -> List[RankedResult]:
        """Rank and fuse results from multiple sources"""
        try:
            # Calculate relevance scores
            for result in results:
                result.relevance_score = await self._calculate_relevance(result, query)

            # Group by source for fusion
            source_groups = {}
            for result in results:
                if result.source not in source_groups:
                    source_groups[result.source] = []
                source_groups[result.source].append(result)

            # Apply fusion strategy
            fused_results = []
            if self.config.fusion_strategy == "weighted_average":
                fused_results = self._weighted_average_fusion(source_groups)
            elif self.config.fusion_strategy == "best_of_each":
                fused_results = self._best_of_each_fusion(source_groups)
            elif self.config.fusion_strategy == "hybrid":
                fused_results = self._hybrid_fusion(source_groups)
            else:
                # Default: just rank all results together
                fused_results = results

            # Sort by combined score
            fused_results.sort(key=lambda x: x.combined_score, reverse=True)

            # Assign final ranks
            for i, result in enumerate(fused_results):
                result.rank = i + 1

            return fused_results

        except Exception as e:
            logger.warning(f"Ranking and fusion failed: {e}")
            # Fallback: simple ranking by confidence
            results.sort(key=lambda x: x.confidence, reverse=True)
            for i, result in enumerate(results):
                result.rank = i + 1
            return results

    async def _calculate_relevance(
        self, result: RankedResult, query: RetrievalQuery
    ) -> float:
        """Calculate relevance score for a result"""
        try:
            relevance_score = 0.0

            # Semantic similarity (if we have embeddings)
            if hasattr(result, "embedding") and hasattr(query, "embedding"):
                # This would use cosine similarity in a real implementation
                relevance_score += 0.3

            # Text overlap
            text_overlap = self._calculate_text_overlap(query.text, result.content)
            relevance_score += text_overlap * 0.3

            # Intent matching
            if query.intent in result.metadata.get("intent", ""):
                relevance_score += 0.2

            # Context matching
            if query.context and result.metadata:
                context_overlap = self._calculate_context_overlap(
                    query.context, result.metadata
                )
                relevance_score += context_overlap * 0.2

            return min(1.0, relevance_score)

        except Exception as e:
            logger.debug(f"Relevance calculation failed: {e}")
            return 0.5  # Default relevance

    def _calculate_text_overlap(self, query: str, content: str) -> float:
        """Calculate text overlap between query and content"""
        try:
            query_words = set(re.findall(r"\w+", query.lower()))
            content_words = set(re.findall(r"\w+", content.lower()))

            if not query_words:
                return 0.0

            overlap = len(query_words.intersection(content_words))
            return overlap / len(query_words)

        except Exception:
            return 0.0

    def _calculate_context_overlap(
        self, query_context: Dict[str, Any], result_metadata: Dict[str, Any]
    ) -> float:
        """Calculate context overlap between query and result metadata"""
        try:
            overlap_score = 0.0
            total_fields = 0

            for key, value in query_context.items():
                if key in result_metadata:
                    total_fields += 1
                    if result_metadata[key] == value:
                        overlap_score += 1.0
                    elif isinstance(value, str) and isinstance(
                        result_metadata[key], str
                    ):
                        # Partial string match
                        if value.lower() in result_metadata[key].lower():
                            overlap_score += 0.5

            return overlap_score / total_fields if total_fields > 0 else 0.0

        except Exception:
            return 0.0

    def _weighted_average_fusion(
        self, source_groups: Dict[str, List[RankedResult]]
    ) -> List[RankedResult]:
        """Fuse results using weighted average by source"""
        fused_results = []

        for source, results in source_groups.items():
            if not results:
                continue

            # Sort by confidence within source
            results.sort(key=lambda x: x.confidence, reverse=True)

            # Take top results from each source
            top_results = results[: self.config.max_results_per_source]

            # Adjust confidence based on source authority
            source_authority = self._get_source_authority(source)
            for result in top_results:
                result.confidence *= source_authority

            fused_results.extend(top_results)

        return fused_results

    def _best_of_each_fusion(
        self, source_groups: Dict[str, List[RankedResult]]
    ) -> List[RankedResult]:
        """Take the best result from each source"""
        fused_results = []

        for source, results in source_groups.items():
            if not results:
                continue

            # Take the best result from each source
            best_result = max(results, key=lambda x: x.confidence)
            fused_results.append(best_result)

        return fused_results

    def _hybrid_fusion(
        self, source_groups: Dict[str, List[RankedResult]]
    ) -> List[RankedResult]:
        """Hybrid fusion strategy combining weighted average and best of each"""
        # Get best of each source
        best_results = self._best_of_each_fusion(source_groups)

        # Get weighted average results
        weighted_results = self._weighted_average_fusion(source_groups)

        # Combine and deduplicate
        all_results = best_results + weighted_results
        seen_content = set()
        unique_results = []

        for result in all_results:
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)

        return unique_results

    def _deduplicate_results(
        self, results: List[RankedResult], query: RetrievalQuery
    ) -> List[RankedResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return results

        unique_results = []
        seen_content = set()

        for result in results:
            # Simple deduplication by content hash
            content_hash = hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
            else:
                # If duplicate, keep the one with higher confidence
                for i, existing in enumerate(unique_results):
                    if hash(existing.content) == content_hash:
                        if result.confidence > existing.confidence:
                            unique_results[i] = result
                        break

        return unique_results

    def _get_source_authority(self, source: str) -> float:
        """Get authority weight for a source"""
        authority_weights = {
            "vector": 1.0,  # Vector search is most authoritative
            "semantic": 0.9,  # Semantic cache is highly reliable
            "sqlite": 0.8,  # SQLite is reliable but less sophisticated
            "mem0": 0.7,  # External knowledge graph
        }
        return authority_weights.get(source, 0.5)

    def _get_cache_key(
        self, query: RetrievalQuery, tenant_id: str, workspace_id: str
    ) -> str:
        """Generate cache key for query"""
        return f"{tenant_id}:{workspace_id}:{hash(query.text)}:{query.intent}:{query.limit}"

    def clear_cache(self) -> None:
        """Clear the query cache"""
        self.query_cache.clear()
        logger.info("Retrieval engine cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.query_cache),
            "cache_keys": list(self.query_cache.keys()),
        }
