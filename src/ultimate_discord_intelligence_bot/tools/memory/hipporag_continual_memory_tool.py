"""HippoRAG 2 Continual Memory Tool.

Implements neurobiologically-inspired continual memory using the HippoRAG 2 framework.
Provides advanced memory consolidation, associativity, and sense-making capabilities
that complement the existing GraphMemoryTool with hippocampal-inspired dynamics.
"""
from __future__ import annotations
import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4
from platform.config.configuration import get_config
from platform.observability.metrics import get_metrics
from platform.core.step_result import StepResult
from ._base import BaseTool
try:
    from hipporag import HippoRAG
    HIPPORAG_AVAILABLE = True
except ImportError:
    HIPPORAG_AVAILABLE = False
    HippoRAG = None

def _is_feature_enabled() -> bool:
    """Check if HippoRAG continual memory is enabled via feature flag."""
    config = get_config()
    env_enabled = any((bool(os.getenv(flag)) for flag in ('ENABLE_HIPPORAG_MEMORY', 'ENABLE_HIPPORAG_CONTINUAL_MEMORY')))
    cfg_enabled = bool(getattr(config, 'enable_hipporag_memory', False) or getattr(config, 'enable_hipporag_continual_memory', False))
    return env_enabled or cfg_enabled

def _get_model_config() -> tuple[str, str, str | None, str | None]:
    """Get LLM and embedding model configuration from environment/config."""
    config = get_config()
    llm_model = os.getenv('HIPPORAG_LLM_MODEL') or getattr(config, 'hipporag_llm_model', 'gpt-4o-mini')
    llm_base_url = os.getenv('HIPPORAG_LLM_BASE_URL') or getattr(config, 'hipporag_llm_base_url', None)
    embedding_model = os.getenv('HIPPORAG_EMBEDDING_MODEL') or getattr(config, 'hipporag_embedding_model', 'nvidia/NV-Embed-v2')
    embedding_base_url = os.getenv('HIPPORAG_EMBEDDING_BASE_URL') or getattr(config, 'hipporag_embedding_base_url', None)
    return (llm_model, embedding_model, llm_base_url, embedding_base_url)

class HippoRagContinualMemoryTool(BaseTool[StepResult]):
    """Neurobiologically-inspired continual memory using HippoRAG 2.

    This tool implements advanced memory consolidation patterns inspired by
    hippocampal memory formation. It provides three key capabilities:

    1. Factual Memory: Long-term retention of factual information
    2. Sense-Making: Integration of complex, interconnected contexts
    3. Associativity: Multi-hop retrieval across memory networks

    When HippoRAG is unavailable, gracefully falls back to lightweight
    graph-based memory to maintain system functionality.
    """
    name: str = 'HippoRAG Continual Memory Tool'
    description: str = 'Store and consolidate memories using neurobiologically-inspired continual learning.'

    def __init__(self, storage_dir: str | os.PathLike[str] | None=None) -> None:
        super().__init__()
        base_dir = storage_dir or os.getenv('HIPPORAG_STORAGE', 'crew_data/Processing/hipporag_memory')
        self._base_path = Path(base_dir)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._metrics = get_metrics()
        self._hipporag_instances: dict[str, Any] = {}

    @staticmethod
    def _physical_namespace(namespace: str) -> str:
        """Convert logical namespace to filesystem-safe physical namespace."""
        safe = namespace.replace(':', '__').replace('/', '_')
        return safe.replace(' ', '_')

    def _namespace_path(self, namespace: str) -> Path:
        """Get storage path for a namespace."""
        physical = self._physical_namespace(namespace)
        path = self._base_path / physical
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _resolve_namespace(self, index: str) -> tuple[str, bool]:
        """Resolve tenant-aware namespace using mem_ns pattern."""
        with contextlib.suppress(Exception):
            from ultimate_discord_intelligence_bot.tenancy.context import current_tenant, mem_ns
            ctx = current_tenant()
            if ctx is not None:
                return (mem_ns(ctx, index), True)
        return (index, False)

    def _get_hipporag_instance(self, namespace: str) -> Any | None:
        """Get or create HippoRAG instance for namespace."""
        if not HIPPORAG_AVAILABLE or not _is_feature_enabled():
            return None
        if namespace in self._hipporag_instances:
            return self._hipporag_instances[namespace]
        try:
            llm_model, embedding_model, llm_base_url, embedding_base_url = _get_model_config()
            save_dir = self._namespace_path(namespace)
            kwargs = {'save_dir': str(save_dir), 'llm_model_name': llm_model, 'embedding_model_name': embedding_model}
            if llm_base_url:
                kwargs['llm_base_url'] = llm_base_url
            if embedding_base_url:
                kwargs['embedding_base_url'] = embedding_base_url
            hipporag = HippoRAG(**kwargs)
            self._hipporag_instances[namespace] = hipporag
            return hipporag
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter('hipporag_init_failures', labels={'namespace': namespace, 'error': type(exc).__name__}).inc()
            return None

    def _fallback_memory_store(self, text: str, namespace: str, metadata: dict[str, Any] | None=None, tags: list[str] | None=None) -> dict[str, Any]:
        """Fallback to simple memory storage when HippoRAG unavailable."""
        memory_id = uuid4().hex
        memory_record = {'id': memory_id, 'text': text, 'namespace': namespace, 'metadata': metadata or {}, 'tags': tags or [], 'timestamp': time.time(), 'type': 'fallback_memory', 'backend': 'lightweight'}
        ns_path = self._namespace_path(namespace)
        memory_file = ns_path / f'{memory_id}.json'
        with memory_file.open('w', encoding='utf-8') as f:
            json.dump(memory_record, f, ensure_ascii=False, indent=2)
        return {'memory_id': memory_id, 'storage_path': str(memory_file), 'backend': 'fallback', 'capabilities': ['basic_storage']}

    def run(self, *, text: str, index: str='continual_memory', metadata: dict[str, Any] | None=None, tags: list[str] | None=None, consolidate: bool=True) -> StepResult:
        """Store text in continual memory with hippocampal-inspired consolidation.

        Args:
            text: Text content to store in memory
            index: Memory index/namespace identifier
            metadata: Additional metadata to store with the memory
            tags: Tags for memory organization and retrieval
            consolidate: Whether to trigger memory consolidation

        Returns:
            StepResult with memory storage details and capabilities
        """
        if not isinstance(text, str) or not text.strip():
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'hipporag_continual_memory', 'outcome': 'skipped'}).inc()
            return StepResult.skip(reason='empty_text')
        namespace, tenant_scoped = self._resolve_namespace(index)
        if not _is_feature_enabled():
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'hipporag_continual_memory', 'outcome': 'disabled'}).inc()
            return StepResult.skip(reason='feature_disabled', namespace=namespace)
        try:
            hipporag = self._get_hipporag_instance(namespace)
            if hipporag is None:
                fallback_result = self._fallback_memory_store(text, namespace, metadata, tags)
                with contextlib.suppress(Exception):
                    self._metrics.counter('tool_runs_total', labels={'tool': 'hipporag_continual_memory', 'outcome': 'fallback'}).inc()
                return StepResult.ok(data=fallback_result, namespace=namespace, tenant_scoped=tenant_scoped, custom_status='fallback_used')
            docs = [text]
            doc_metadata = {'original_metadata': metadata or {}, 'tags': tags or [], 'timestamp': time.time(), 'namespace': namespace, 'tenant_scoped': tenant_scoped}
            hipporag.index(docs=docs)
            memory_id = uuid4().hex
            meta_path = self._namespace_path(namespace) / f'{memory_id}_meta.json'
            with meta_path.open('w', encoding='utf-8') as f:
                json.dump(doc_metadata, f, ensure_ascii=False, indent=2)
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'hipporag_continual_memory', 'outcome': 'success', 'tenant_scoped': str(tenant_scoped).lower()}).inc()
                self._metrics.counter('hipporag_memory_operations', labels={'operation': 'index', 'namespace': namespace}).inc()
            return StepResult.ok(data={'memory_id': memory_id, 'namespace': namespace, 'tenant_scoped': tenant_scoped, 'backend': 'hipporag', 'capabilities': ['factual_memory', 'sense_making', 'associativity', 'continual_learning'], 'consolidation_enabled': consolidate, 'metadata_path': str(meta_path)})
        except Exception as exc:
            with contextlib.suppress(Exception):
                self._metrics.counter('tool_runs_total', labels={'tool': 'hipporag_continual_memory', 'outcome': 'error'}).inc()
            return StepResult.fail(f'HippoRAG continual memory failed: {exc}', namespace=namespace, step='hipporag_index')

    def retrieve(self, *, query: str, index: str='continual_memory', num_to_retrieve: int=3, include_reasoning: bool=True) -> StepResult:
        """Retrieve memories using HippoRAG's advanced retrieval capabilities.

        Args:
            query: Query text for memory retrieval
            index: Memory index/namespace to search
            num_to_retrieve: Number of memories to retrieve
            include_reasoning: Whether to include reasoning in results

        Returns:
            StepResult with retrieved memories and reasoning
        """
        if not isinstance(query, str) or not query.strip():
            return StepResult.skip(reason='empty_query')
        namespace, tenant_scoped = self._resolve_namespace(index)
        if not _is_feature_enabled():
            return StepResult.skip(reason='feature_disabled', namespace=namespace)
        try:
            hipporag = self._get_hipporag_instance(namespace)
            if hipporag is None:
                return StepResult.skip(reason='hipporag_unavailable', namespace=namespace)
            queries = [query]
            retrieval_results = hipporag.retrieve(queries=queries, num_to_retrieve=num_to_retrieve)
            results = retrieval_results[0] if retrieval_results else []
            formatted_results = []
            for result in results:
                formatted_result = {'text': result.get('content', ''), 'score': result.get('score', 0.0), 'metadata': result.get('metadata', {})}
                if include_reasoning:
                    formatted_result['reasoning'] = result.get('reasoning', '')
                formatted_results.append(formatted_result)
            with contextlib.suppress(Exception):
                self._metrics.counter('hipporag_memory_operations', labels={'operation': 'retrieve', 'namespace': namespace}).inc()
            return StepResult.ok(data={'query': query, 'results': formatted_results, 'num_retrieved': len(formatted_results), 'namespace': namespace, 'tenant_scoped': tenant_scoped, 'backend': 'hipporag'})
        except Exception as exc:
            return StepResult.fail(f'HippoRAG retrieval failed: {exc}', namespace=namespace, step='hipporag_retrieve')
__all__ = ['HippoRagContinualMemoryTool']