"""Unified Memory Tool - CrewAI tool for accessing unified knowledge layer

This tool provides CrewAI agents with access to the unified knowledge layer,
enabling them to store and retrieve information from all memory backends
through a single, coherent interface.
"""

from __future__ import annotations

import logging
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ultimate_discord_intelligence_bot.knowledge import (
    ContextConfig,
    ContextRequest,
    RetrievalConfig,
    RetrievalQuery,
    UnifiedContextBuilder,
    UnifiedMemoryConfig,
    UnifiedMemoryService,
    UnifiedRetrievalEngine,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


class UnifiedMemoryStoreInput(BaseModel):
    """Input for unified memory store operation"""

    content: str = Field(description="Content to store in unified memory")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata for the content")
    namespace: str | None = Field(default=None, description="Optional namespace for the content")


class UnifiedMemoryRetrieveInput(BaseModel):
    """Input for unified memory retrieve operation"""

    query: str = Field(description="Query to search for in unified memory")
    intent: str = Field(
        default="general",
        description="Intent of the query (general, fact_check, debate_analysis, creator_intel)",
    )
    filters: dict[str, Any] | None = Field(default=None, description="Optional filters for the search")
    limit: int = Field(default=10, description="Maximum number of results to return")
    min_confidence: float = Field(default=0.5, description="Minimum confidence threshold for results")


class UnifiedContextBuildInput(BaseModel):
    """Input for unified context build operation"""

    agent_id: str = Field(description="ID of the agent requesting context")
    task_type: str = Field(description="Type of task the agent is performing")
    query: str | None = Field(default=None, description="Query for context building")
    current_context: dict[str, Any] | None = Field(default=None, description="Current context to build upon")
    max_context_length: int = Field(default=4000, description="Maximum context length in tokens")
    include_history: bool = Field(default=True, description="Include historical context")
    include_related_content: bool = Field(default=True, description="Include related content")
    include_creator_intelligence: bool = Field(default=True, description="Include creator intelligence")
    include_fact_checking: bool = Field(default=True, description="Include fact-checking information")


class UnifiedMemoryTool(BaseTool):
    """Unified memory tool for CrewAI agents"""

    name: str = "unified_memory_tool"
    description: str = (
        "Provides access to the unified knowledge layer for storing and retrieving information. "
        "This tool integrates vector storage, SQLite, semantic cache, and mem0 into a single "
        "coherent interface for comprehensive knowledge management."
    )
    args_schema: type[BaseModel] = UnifiedMemoryRetrieveInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize unified services
        memory_config = UnifiedMemoryConfig(
            enable_vector_store=True,
            enable_sqlite_store=True,
            enable_semantic_cache=True,
            enable_mem0=False,  # Disable by default, can be enabled via config
        )

        retrieval_config = RetrievalConfig(
            enable_semantic_ranking=True,
            enable_content_deduplication=True,
            enable_metadata_fusion=True,
        )

        context_config = ContextConfig(
            enable_semantic_grouping=True,
            enable_temporal_ordering=True,
            enable_relevance_filtering=True,
        )

        try:
            self._memory_service = UnifiedMemoryService(memory_config)
            self._retrieval_engine = UnifiedRetrievalEngine(retrieval_config)
            self._context_builder = UnifiedContextBuilder(context_config)
            logger.info("Unified memory tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize unified memory tool: {e}")
            self._memory_service = None
            self._retrieval_engine = None
            self._context_builder = None

    def _run(
        self,
        query: str,
        intent: str = "general",
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        min_confidence: float = 0.5,
        **kwargs: Any,
    ) -> StepResult:
        """Execute unified memory retrieval"""
        try:
            if not self._memory_service or not self._retrieval_engine:
                return StepResult.fail("Unified memory services not initialized")

            # Create retrieval query
            retrieval_query = RetrievalQuery(
                text=query,
                intent=intent,
                filters=filters,
                limit=limit,
                min_confidence=min_confidence,
            )

            # Perform retrieval (sync wrapper for async operation)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(self._retrieval_engine.retrieve(retrieval_query, self._memory_service))

            if not result.success:
                return StepResult.fail(f"Retrieval failed: {result.error}")

            # Format results for agent consumption
            data = result.data
            results = data.get("results", [])

            if not results:
                return StepResult.ok(data={"message": f"No relevant information found for query: '{query}'"})

            # Build response
            response_parts = []
            response_parts.append(f"Found {len(results)} relevant results for query: '{query}'")
            response_parts.append("")

            for i, ranked_result in enumerate(results, 1):
                response_parts.append(
                    f"Result {i} (Confidence: {ranked_result.confidence:.2f}, Source: {ranked_result.source}):"
                )
                response_parts.append(ranked_result.content)
                if ranked_result.metadata:
                    response_parts.append(f"Metadata: {ranked_result.metadata}")
                response_parts.append("")

            # Add summary metadata
            metadata = data.get("metadata", {})
            if metadata:
                response_parts.append("Summary:")
                response_parts.append(f"- Sources queried: {metadata.get('total_sources', 'unknown')}")
                response_parts.append(f"- Average confidence: {metadata.get('avg_confidence', 0):.2f}")
                response_parts.append(f"- Average relevance: {metadata.get('avg_relevance', 0):.2f}")

            return StepResult.ok(
                data={"results": "\n".join(response_parts), "count": len(results), "metadata": metadata}
            )

        except Exception as e:
            logger.error(f"Error in unified memory retrieval: {e}", exc_info=True)
            return StepResult.fail(f"Error during retrieval: {e!s}")


class UnifiedMemoryStoreTool(BaseTool):
    """Tool for storing information in unified memory"""

    name: str = "unified_memory_store_tool"
    description: str = (
        "Stores information in the unified knowledge layer across all configured backends. "
        "Information stored through this tool becomes available to all agents and services."
    )
    args_schema: type[BaseModel] = UnifiedMemoryStoreInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize memory service
        memory_config = UnifiedMemoryConfig()
        try:
            self._memory_service = UnifiedMemoryService(memory_config)
            logger.info("Unified memory store tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize unified memory store tool: {e}")
            self._memory_service = None

    def _run(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        namespace: str | None = None,
        **kwargs: Any,
    ) -> StepResult:
        """Execute unified memory storage"""
        try:
            if not self._memory_service:
                return StepResult.fail("Unified memory service not initialized")

            # Perform storage (sync wrapper for async operation)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self._memory_service.store(content=content, metadata=metadata, namespace=namespace)
            )

            if not result.success:
                return StepResult.fail(f"Storage failed: {result.error}")

            # Format response
            data = result.data
            stored_backends = data.get("stored_backends", [])
            total_backends = data.get("total_backends", 0)

            response_data = {
                "message": f"Successfully stored information in {len(stored_backends)}/{total_backends} backends",
                "stored_backends": stored_backends,
                "total_backends": total_backends,
                "namespace": data.get("namespace", "default"),
                "metadata": metadata,
            }

            return StepResult.ok(data=response_data)

        except Exception as e:
            logger.error(f"Error in unified memory storage: {e}", exc_info=True)
            return StepResult.fail(f"Error during storage: {e!s}")


class UnifiedContextTool(BaseTool):
    """Tool for building comprehensive context for agents"""

    name: str = "unified_context_tool"
    description: str = (
        "Builds comprehensive context for agent decision-making by combining information "
        "from multiple sources including historical data, related content, creator intelligence, "
        "and fact-checking information."
    )
    args_schema: type[BaseModel] = UnifiedContextBuildInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize services
        memory_config = UnifiedMemoryConfig()
        context_config = ContextConfig()

        try:
            self._memory_service = UnifiedMemoryService(memory_config)
            self._context_builder = UnifiedContextBuilder(context_config)
            logger.info("Unified context tool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize unified context tool: {e}")
            self._memory_service = None
            self._context_builder = None

    def _run(
        self,
        agent_id: str,
        task_type: str,
        query: str | None = None,
        current_context: dict[str, Any] | None = None,
        max_context_length: int = 4000,
        include_history: bool = True,
        include_related_content: bool = True,
        include_creator_intelligence: bool = True,
        include_fact_checking: bool = True,
        **kwargs: Any,
    ) -> StepResult:
        """Execute unified context building"""
        try:
            if not self._memory_service or not self._context_builder:
                return StepResult.fail("Unified context services not initialized")

            # Create context request
            context_request = ContextRequest(
                agent_id=agent_id,
                task_type=task_type,
                query=query,
                current_context=current_context,
                max_context_length=max_context_length,
                include_history=include_history,
                include_related_content=include_related_content,
                include_creator_intelligence=include_creator_intelligence,
                include_fact_checking=include_fact_checking,
            )

            # Build context (sync wrapper for async operation)
            import asyncio

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self._context_builder.build_context(
                    context_request,
                    self._memory_service,
                    None,  # retrieval_engine not needed for context building
                )
            )

            if not result.success:
                return StepResult.fail(f"Context building failed: {result.error}")

            # Format unified context for agent consumption
            unified_context = result.data

            response_parts = []
            response_parts.append(f"Comprehensive context built for {agent_id} (Task: {task_type})")
            response_parts.append("")
            response_parts.append("PRIMARY CONTEXT:")
            response_parts.append(unified_context.primary_context)
            response_parts.append("")

            if unified_context.supporting_contexts:
                response_parts.append("SUPPORTING CONTEXTS:")
                for i, segment in enumerate(unified_context.supporting_contexts, 1):
                    response_parts.append(
                        f"{i}. [{segment.segment_type.upper()}] (Relevance: {segment.relevance_score:.2f})"
                    )
                    response_parts.append(f"   Source: {segment.source}")
                    response_parts.append(f"   Content: {segment.content[:200]}...")
                    response_parts.append("")

            # Add metadata
            metadata = unified_context.metadata
            response_parts.append("CONTEXT METADATA:")
            response_parts.append(f"- Total segments: {metadata.get('segments_count', 0)}")
            response_parts.append(f"- Total tokens: {unified_context.total_tokens}")
            response_parts.append(f"- Overall relevance: {unified_context.relevance_score:.2f}")
            response_parts.append(f"- Build timestamp: {unified_context.timestamp}")

            return StepResult.ok(
                data={
                    "context": "\n".join(response_parts),
                    "agent_id": agent_id,
                    "task_type": task_type,
                    "total_tokens": unified_context.total_tokens,
                    "relevance_score": unified_context.relevance_score,
                    "segments_count": metadata.get("segments_count", 0),
                }
            )

        except Exception as e:
            logger.error(f"Error in unified context building: {e}", exc_info=True)
            return StepResult.fail(f"Error during context building: {e!s}")
