"""Graph memory plugin for knowledge graph operations and relationship traversal.

Integrates GraphMemoryTool for lightweight knowledge graph construction,
storage, and relationship-based retrieval.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tools.graph_memory_tool import GraphMemoryTool
if TYPE_CHECKING:
    from collections.abc import Sequence
logger = logging.getLogger(__name__)

class GraphPlugin:
    """Memory plugin for knowledge graph backend.

    Provides graph-based memory with:
    - Entity and relationship extraction
    - Knowledge graph construction
    - Relationship traversal
    - Keyword-based graph search
    """

    def __init__(self, storage_dir: str | None=None):
        """Initialize Graph plugin.

        Args:
            storage_dir: Optional storage directory override
        """
        try:
            self._tool = GraphMemoryTool(storage_dir=storage_dir)
            logger.info('GraphPlugin initialized successfully')
        except Exception as exc:
            logger.warning(f'GraphPlugin initialization failed: {exc}')
            self._tool = None

    async def store(self, namespace: str, records: Sequence[dict[str, Any]]) -> StepResult:
        """Store records as knowledge graphs.

        Args:
            namespace: Tenant-scoped namespace (format: tenant:workspace:creator)
            records: Records to store, each with 'content' and optional 'metadata'

        Returns:
            StepResult with storage outcome
        """
        if self._tool is None:
            return StepResult.fail('Graph tool unavailable')
        try:
            parts = namespace.split(':')
            index = parts[-1] if len(parts) > 3 else 'graph'
            stored_count = 0
            graph_ids = []
            for record in records:
                content = record.get('content')
                if not content:
                    logger.warning('Skipping record without content')
                    continue
                metadata = record.get('metadata', {})
                metadata.update({'namespace': namespace})
                tags = metadata.pop('tags', None)
                result = self._tool.run(text=content, index=index, metadata=metadata, tags=tags)
                if result.success:
                    stored_count += 1
                    graph_id = result.data.get('graph_id')
                    if graph_id:
                        graph_ids.append(graph_id)
                else:
                    logger.warning(f'Failed to store graph: {result.error}')
            if stored_count == 0:
                return StepResult.fail('No graphs stored successfully', namespace=namespace)
            return StepResult.ok(stored=stored_count, graph_ids=graph_ids, namespace=namespace, index=index, backend='graph')
        except Exception as exc:
            return StepResult.fail(f'Graph storage failed: {exc}', namespace=namespace, step='graph_store')

    async def retrieve(self, namespace: str, query: str, limit: int) -> StepResult:
        """Retrieve graphs using keyword search.

        Args:
            namespace: Tenant-scoped namespace
            query: Query string for keyword matching
            limit: Maximum number of results

        Returns:
            StepResult with retrieved graphs
        """
        if self._tool is None:
            return StepResult.fail('Graph tool unavailable')
        try:
            parts = namespace.split(':')
            index = parts[-1] if len(parts) > 3 else 'graph'
            result = self._tool.search_graphs(query=query, namespace=index, tags=None, limit=limit)
            if not result.success:
                return StepResult.fail(f'Graph search failed: {result.error}', namespace=namespace, step='graph_retrieve')
            graphs = result.data.get('graphs', [])
            formatted_results = []
            for graph_meta in graphs:
                graph_id = graph_meta.get('graph_id')
                formatted_results.append({'graph_id': graph_id, 'score': graph_meta.get('score', 0.0), 'keywords': graph_meta.get('keywords', []), 'tags': graph_meta.get('tags', []), 'node_count': graph_meta.get('node_count', 0), 'edge_count': graph_meta.get('edge_count', 0), 'metadata': {'tenant_scoped': graph_meta.get('tenant_scoped', False), 'namespace': namespace}})
            return StepResult.ok(results=formatted_results, count=len(formatted_results), namespace=namespace, index=index, backend='graph')
        except Exception as exc:
            return StepResult.fail(f'Graph retrieval failed: {exc}', namespace=namespace, step='graph_retrieve')
__all__ = ['GraphPlugin']