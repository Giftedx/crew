"""HippoRAG memory plugin for continual learning with neurobiological patterns.

Integrates HippoRAG's hippocampal-inspired memory consolidation for
factual memory, sense-making, and associative retrieval.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.hipporag_continual_memory_tool import HippoRagContinualMemoryTool
if TYPE_CHECKING:
    from collections.abc import Sequence
logger = logging.getLogger(__name__)

class HippoRAGPlugin:
    """Memory plugin for HippoRAG continual learning backend.

    Provides neurobiologically-inspired memory with:
    - Factual memory consolidation
    - Sense-making across contexts
    - Multi-hop associative retrieval
    - Continual learning without catastrophic forgetting
    """

    def __init__(self, storage_dir: str | None=None):
        """Initialize HippoRAG plugin.

        Args:
            storage_dir: Optional storage directory override
        """
        try:
            self._tool = HippoRagContinualMemoryTool(storage_dir=storage_dir)
            logger.info('HippoRAGPlugin initialized successfully')
        except Exception as exc:
            logger.warning(f'HippoRAGPlugin initialization failed: {exc}')
            self._tool = None

    async def store(self, namespace: str, records: Sequence[dict[str, Any]]) -> StepResult:
        """Store records in HippoRAG continual memory.

        Args:
            namespace: Tenant-scoped namespace (format: tenant:workspace:creator)
            records: Records to store, each with 'content' and optional 'metadata'

        Returns:
            StepResult with storage outcome
        """
        if self._tool is None:
            return StepResult.fail('HippoRAG tool unavailable')
        try:
            parts = namespace.split(':')
            index = parts[-1] if len(parts) > 3 else 'continual_memory'
            stored_count = 0
            memory_ids = []
            for record in records:
                content = record.get('content')
                if not content:
                    logger.warning('Skipping record without content')
                    continue
                metadata = record.get('metadata', {})
                metadata.update({'namespace': namespace})
                tags = metadata.pop('tags', [])
                result = self._tool.run(text=content, index=index, metadata=metadata, tags=tags, consolidate=True)
                if result.success:
                    stored_count += 1
                    memory_id = result.data.get('memory_id')
                    if memory_id:
                        memory_ids.append(memory_id)
                elif result.custom_status == 'fallback_used':
                    stored_count += 1
                    memory_id = result.data.get('id')
                    if memory_id:
                        memory_ids.append(memory_id)
                else:
                    logger.warning(f'Failed to store record in HippoRAG: {result.error}')
            if stored_count == 0:
                return StepResult.fail('No records stored successfully', namespace=namespace)
            return StepResult.ok(stored=stored_count, memory_ids=memory_ids, namespace=namespace, index=index, backend='hipporag', capabilities=['factual_memory', 'sense_making', 'associativity', 'continual_learning'])
        except Exception as exc:
            return StepResult.fail(f'HippoRAG storage failed: {exc}', namespace=namespace, step='hipporag_store')

    async def retrieve(self, namespace: str, query: str, limit: int) -> StepResult:
        """Retrieve records from HippoRAG continual memory.

        Args:
            namespace: Tenant-scoped namespace
            query: Query string for semantic search
            limit: Maximum number of results

        Returns:
            StepResult with retrieved records
        """
        if self._tool is None:
            return StepResult.fail('HippoRAG tool unavailable')
        try:
            parts = namespace.split(':')
            index = parts[-1] if len(parts) > 3 else 'continual_memory'
            result = self._tool.retrieve(query=query, index=index, num_to_retrieve=limit, include_reasoning=True)
            if not result.success:
                return StepResult.fail(f'HippoRAG retrieval failed: {result.error}', namespace=namespace, step='hipporag_retrieve')
            retrieval_data = result.data or {}
            results = retrieval_data.get('results', [])
            formatted_results = []
            for item in results:
                formatted_results.append({'content': item.get('text', ''), 'score': item.get('score', 0.0), 'metadata': item.get('metadata', {}), 'reasoning': item.get('reasoning', '')})
            return StepResult.ok(results=formatted_results, count=len(formatted_results), namespace=namespace, index=index, backend='hipporag', backend_status=retrieval_data.get('backend', 'unknown'))
        except Exception as exc:
            return StepResult.fail(f'HippoRAG retrieval failed: {exc}', namespace=namespace, step='hipporag_retrieve')
__all__ = ['HippoRAGPlugin']