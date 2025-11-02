"""Mem0 memory plugin for long-term episodic memory and user preferences.

Integrates Mem0's persistent memory layer for cross-session learning,
user preference tracking, and adaptive behavior.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from ultimate_discord_intelligence_bot.services.mem0_service import Mem0MemoryService
from platform.core.step_result import StepResult
if TYPE_CHECKING:
    from collections.abc import Sequence
logger = logging.getLogger(__name__)

class Mem0Plugin:
    """Memory plugin for Mem0 episodic memory backend.

    Provides long-term memory with:
    - User preference learning
    - Cross-session context retention
    - Semantic memory retrieval
    - Adaptive user modeling
    """

    def __init__(self):
        """Initialize Mem0 plugin."""
        try:
            self._service = Mem0MemoryService()
            logger.info('Mem0Plugin initialized successfully')
        except Exception as exc:
            logger.warning(f'Mem0Plugin initialization failed: {exc}')
            self._service = None

    async def store(self, namespace: str, records: Sequence[dict[str, Any]]) -> StepResult:
        """Store records in Mem0 episodic memory.

        Args:
            namespace: Tenant-scoped namespace (format: tenant:workspace:creator)
            records: Records to store, each with 'content' and optional 'metadata'

        Returns:
            StepResult with storage outcome
        """
        if self._service is None:
            return StepResult.fail('Mem0 service unavailable')
        try:
            parts = namespace.split(':')
            if len(parts) < 2:
                return StepResult.fail(f'Invalid namespace format: {namespace}')
            user_id = f'{parts[0]}:{parts[1]}'
            stored_count = 0
            for record in records:
                content = record.get('content')
                if not content:
                    logger.warning('Skipping record without content')
                    continue
                metadata = record.get('metadata', {})
                metadata.update({'namespace': namespace, 'tenant': parts[0], 'workspace': parts[1]})
                result = self._service.remember(content, user_id, metadata)
                if result.success:
                    stored_count += 1
                else:
                    logger.warning(f'Failed to store record: {result.error}')
            if stored_count == 0:
                return StepResult.fail('No records stored successfully', namespace=namespace)
            return StepResult.ok(stored=stored_count, namespace=namespace, user_id=user_id, backend='mem0')
        except Exception as exc:
            return StepResult.fail(f'Mem0 storage failed: {exc}', namespace=namespace, step='mem0_store')

    async def retrieve(self, namespace: str, query: str, limit: int) -> StepResult:
        """Retrieve records from Mem0 episodic memory.

        Args:
            namespace: Tenant-scoped namespace
            query: Query string for semantic search
            limit: Maximum number of results

        Returns:
            StepResult with retrieved records
        """
        if self._service is None:
            return StepResult.fail('Mem0 service unavailable')
        try:
            parts = namespace.split(':')
            if len(parts) < 2:
                return StepResult.fail(f'Invalid namespace format: {namespace}')
            user_id = f'{parts[0]}:{parts[1]}'
            result = self._service.recall(query, user_id, limit=limit)
            if not result.success:
                return StepResult.fail(f'Mem0 recall failed: {result.error}', namespace=namespace, step='mem0_retrieve')
            memories = result.data or []
            formatted_results = []
            for memory in memories:
                formatted_results.append({'id': memory.get('id'), 'content': memory.get('memory', ''), 'score': memory.get('score', 0.0), 'metadata': memory.get('metadata', {}), 'created_at': memory.get('created_at'), 'updated_at': memory.get('updated_at')})
            return StepResult.ok(results=formatted_results, count=len(formatted_results), namespace=namespace, user_id=user_id, backend='mem0')
        except Exception as exc:
            return StepResult.fail(f'Mem0 retrieval failed: {exc}', namespace=namespace, step='mem0_retrieve')
__all__ = ['Mem0Plugin']