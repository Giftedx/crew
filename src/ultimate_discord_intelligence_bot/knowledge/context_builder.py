"""Unified Context Builder - Comprehensive context aggregation for agents

This module provides intelligent context building that combines information
from multiple sources to create comprehensive, relevant context for agent
decision-making and response generation.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from platform.core.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant
logger = logging.getLogger(__name__)

@dataclass
class ContextRequest:
    """Request for context building"""
    agent_id: str
    task_type: str = 'general'
    query: str | None = None
    current_context: dict[str, Any] | None = None
    max_context_length: int = 4000
    include_history: bool = True
    include_related_content: bool = True
    include_creator_intelligence: bool = True
    include_fact_checking: bool = True
    priority_sources: list[str] | None = None

@dataclass
class ContextSegment:
    """A segment of context with metadata"""
    content: str
    source: str
    relevance_score: float = 1.0
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    segment_type: str = 'general'

@dataclass
class UnifiedContext:
    """Unified context for agent consumption"""
    agent_id: str
    task_type: str
    primary_context: str
    supporting_contexts: list[ContextSegment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    relevance_score: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class ContextConfig:
    """Configuration for context building"""
    enable_semantic_grouping: bool = True
    enable_temporal_ordering: bool = True
    enable_relevance_filtering: bool = True
    max_segments: int = 20
    min_relevance_threshold: float = 0.3
    context_compression_enabled: bool = True

class UnifiedContextBuilder:
    """Intelligent context builder for comprehensive agent context"""

    def __init__(self, config: ContextConfig | None=None):
        self.config = config or ContextConfig()
        self.context_cache = {}
        self.agent_context_history = {}

    async def build_context(self, request: ContextRequest, unified_memory_service, retrieval_engine, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Build comprehensive context for an agent"""
        try:
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, 'tenant_id', 'default') if ctx else 'default'
            if workspace_id is None:
                workspace_id = getattr(ctx, 'workspace_id', 'main') if ctx else 'main'
            cache_key = self._get_cache_key(request, tenant_id, workspace_id)
            if cache_key in self.context_cache:
                cached_context = self.context_cache[cache_key]
                logger.debug(f'Retrieved context from cache: {cache_key}')
                return StepResult.ok(data=cached_context)
            context_segments = []
            if request.query:
                primary_segment = await self._build_primary_context(request, unified_memory_service, retrieval_engine)
                if primary_segment:
                    context_segments.append(primary_segment)
            if request.include_history:
                historical_segments = await self._build_historical_context(request, unified_memory_service, retrieval_engine)
                context_segments.extend(historical_segments)
            if request.include_related_content:
                related_segments = await self._build_related_context(request, unified_memory_service, retrieval_engine)
                context_segments.extend(related_segments)
            if request.include_creator_intelligence:
                creator_segments = await self._build_creator_intelligence_context(request, unified_memory_service, retrieval_engine)
                context_segments.extend(creator_segments)
            if request.include_fact_checking:
                fact_check_segments = await self._build_fact_checking_context(request, unified_memory_service, retrieval_engine)
                context_segments.extend(fact_check_segments)
            filtered_segments = self._filter_and_rank_segments(context_segments, request)
            unified_context = await self._build_unified_context(request, filtered_segments, tenant_id, workspace_id)
            self.context_cache[cache_key] = unified_context
            self._update_agent_history(request.agent_id, unified_context)
            return StepResult.ok(data=unified_context)
        except Exception as e:
            logger.error(f'Error in context building: {e}', exc_info=True)
            return StepResult.fail(f'Context building failed: {e!s}')

    async def _build_primary_context(self, request: ContextRequest, unified_memory_service, retrieval_engine) -> ContextSegment | None:
        """Build primary context from the main query"""
        try:
            if not request.query:
                return None
            from .retrieval_engine import RetrievalQuery
            retrieval_query = RetrievalQuery(text=request.query, intent=request.task_type, context=request.current_context, limit=5)
            result = await retrieval_engine.retrieve(retrieval_query, unified_memory_service)
            if not result.success:
                logger.warning(f'Primary context retrieval failed: {result.error}')
                return None
            results = result.data.get('results', [])
            if not results:
                return None
            primary_content = []
            for i, ranked_result in enumerate(results[:3]):
                primary_content.append(f'[Source {i + 1}: {ranked_result.source}]')
                primary_content.append(ranked_result.content)
                primary_content.append('')
            return ContextSegment(content='\n'.join(primary_content), source='unified_retrieval', relevance_score=1.0, segment_type='primary', metadata={'query': request.query, 'task_type': request.task_type, 'results_count': len(results)})
        except Exception as e:
            logger.warning(f'Primary context building failed: {e}')
            return None

    async def _build_historical_context(self, request: ContextRequest, unified_memory_service, retrieval_engine) -> list[ContextSegment]:
        """Build historical context for the agent"""
        try:
            segments = []
            agent_history = self.agent_context_history.get(request.agent_id, [])
            if agent_history:
                recent_contexts = agent_history[-3:]
                for i, context in enumerate(recent_contexts):
                    segment = ContextSegment(content=f'[Previous Context {i + 1}] {context.primary_context[:500]}...', source='agent_history', relevance_score=0.7 - i * 0.1, segment_type='historical', timestamp=context.timestamp, metadata={'task_type': context.task_type, 'agent_id': request.agent_id})
                    segments.append(segment)
            if request.query:
                from .retrieval_engine import RetrievalQuery
                historical_query = RetrievalQuery(text=f'historical context {request.query}', intent='historical_reference', limit=3)
                result = await retrieval_engine.retrieve(historical_query, unified_memory_service)
                if result.success:
                    results = result.data.get('results', [])
                    for ranked_result in results:
                        if ranked_result.metadata.get('timestamp'):
                            segment = ContextSegment(content=ranked_result.content, source=ranked_result.source, relevance_score=ranked_result.confidence * 0.8, segment_type='historical', metadata=ranked_result.metadata)
                            segments.append(segment)
            return segments
        except Exception as e:
            logger.warning(f'Historical context building failed: {e}')
            return []

    async def _build_related_content_context(self, request: ContextRequest, unified_memory_service, retrieval_engine) -> list[ContextSegment]:
        """Build context from related content"""
        try:
            segments = []
            if not request.query:
                return segments
            related_intents = ['related_content', 'similar_topics', 'contextual_info']
            for intent in related_intents:
                from .retrieval_engine import RetrievalQuery
                related_query = RetrievalQuery(text=request.query, intent=intent, limit=2)
                result = await retrieval_engine.retrieve(related_query, unified_memory_service)
                if result.success:
                    results = result.data.get('results', [])
                    for ranked_result in results:
                        segment = ContextSegment(content=ranked_result.content, source=ranked_result.source, relevance_score=ranked_result.confidence * 0.6, segment_type='related', metadata=ranked_result.metadata)
                        segments.append(segment)
            return segments
        except Exception as e:
            logger.warning(f'Related content context building failed: {e}')
            return []

    async def _build_creator_intelligence_context(self, request: ContextRequest, unified_memory_service, retrieval_engine) -> list[ContextSegment]:
        """Build context from creator intelligence data"""
        try:
            segments = []
            if request.query:
                from .retrieval_engine import RetrievalQuery
                creator_query = RetrievalQuery(text=request.query, intent='creator_intelligence', filters={'content_type': 'creator_intel'}, limit=3)
                result = await retrieval_engine.retrieve(creator_query, unified_memory_service)
                if result.success:
                    results = result.data.get('results', [])
                    for ranked_result in results:
                        segment = ContextSegment(content=ranked_result.content, source=ranked_result.source, relevance_score=ranked_result.confidence, segment_type='creator_intel', metadata=ranked_result.metadata)
                        segments.append(segment)
            return segments
        except Exception as e:
            logger.warning(f'Creator intelligence context building failed: {e}')
            return []

    async def _build_fact_checking_context(self, request: ContextRequest, unified_memory_service, retrieval_engine) -> list[ContextSegment]:
        """Build context from fact-checking data"""
        try:
            segments = []
            if request.query:
                from .retrieval_engine import RetrievalQuery
                fact_query = RetrievalQuery(text=request.query, intent='fact_checking', filters={'content_type': 'fact_check'}, limit=2)
                result = await retrieval_engine.retrieve(fact_query, unified_memory_service)
                if result.success:
                    results = result.data.get('results', [])
                    for ranked_result in results:
                        segment = ContextSegment(content=ranked_result.content, source=ranked_result.source, relevance_score=ranked_result.confidence, segment_type='fact_check', metadata=ranked_result.metadata)
                        segments.append(segment)
            return segments
        except Exception as e:
            logger.warning(f'Fact-checking context building failed: {e}')
            return []

    def _filter_and_rank_segments(self, segments: list[ContextSegment], request: ContextRequest) -> list[ContextSegment]:
        """Filter and rank context segments"""
        try:
            if self.config.enable_relevance_filtering:
                segments = [seg for seg in segments if seg.relevance_score >= self.config.min_relevance_threshold]
            segments.sort(key=lambda x: x.relevance_score, reverse=True)
            segments = segments[:self.config.max_segments]
            return segments
        except Exception as e:
            logger.warning(f'Segment filtering failed: {e}')
            return segments

    async def _build_unified_context(self, request: ContextRequest, segments: list[ContextSegment], tenant_id: str, workspace_id: str) -> UnifiedContext:
        """Build the final unified context"""
        try:
            primary_segments = [seg for seg in segments if seg.segment_type == 'primary']
            supporting_segments = [seg for seg in segments if seg.segment_type != 'primary']
            if primary_segments:
                primary_context = primary_segments[0].content
            elif request.current_context and 'primary_context' in request.current_context:
                primary_context = request.current_context['primary_context']
            else:
                primary_context = request.query or ''
            if self.config.context_compression_enabled:
                primary_context = self._compress_context(primary_context, request.max_context_length)
            total_tokens = len(primary_context.split()) + sum((len(seg.content.split()) for seg in supporting_segments))
            relevance_score = sum((seg.relevance_score for seg in segments)) / len(segments) if segments else 0.0
            return UnifiedContext(agent_id=request.agent_id, task_type=request.task_type, primary_context=primary_context, supporting_contexts=supporting_segments, metadata={'tenant_id': tenant_id, 'workspace_id': workspace_id, 'segments_count': len(segments), 'primary_segments': len(primary_segments), 'supporting_segments': len(supporting_segments), 'build_timestamp': datetime.now(timezone.utc).isoformat()}, total_tokens=total_tokens, relevance_score=relevance_score)
        except Exception as e:
            logger.error(f'Unified context building failed: {e}')
            return UnifiedContext(agent_id=request.agent_id, task_type=request.task_type, primary_context=request.query or '', metadata={'error': str(e)})

    def _compress_context(self, context: str, max_length: int) -> str:
        """Compress context to fit within token limits"""
        try:
            if len(context) <= max_length:
                return context
            half_length = max_length // 2
            compressed = context[:half_length] + '\n... [context compressed] ...\n' + context[-half_length:]
            return compressed
        except Exception as e:
            logger.warning(f'Context compression failed: {e}')
            return context[:max_length] if len(context) > max_length else context

    def _update_agent_history(self, agent_id: str, context: UnifiedContext) -> None:
        """Update agent context history"""
        try:
            if agent_id not in self.agent_context_history:
                self.agent_context_history[agent_id] = []
            self.agent_context_history[agent_id].append(context)
            self.agent_context_history[agent_id] = self.agent_context_history[agent_id][-10:]
        except Exception as e:
            logger.warning(f'Agent history update failed: {e}')

    def _get_cache_key(self, request: ContextRequest, tenant_id: str, workspace_id: str) -> str:
        """Generate cache key for context request"""
        return f'{tenant_id}:{workspace_id}:{request.agent_id}:{request.task_type}:{hash(request.query or '')}'

    def clear_cache(self) -> None:
        """Clear the context cache"""
        self.context_cache.clear()
        self.agent_context_history.clear()
        logger.info('Context builder cache cleared')

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {'context_cache_size': len(self.context_cache), 'agent_history_size': sum((len(history) for history in self.agent_context_history.values())), 'agents_with_history': len(self.agent_context_history)}