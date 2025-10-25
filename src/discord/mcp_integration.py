"""
MCP server integration layer for Discord conversational AI.

This module provides a unified interface to all MCP servers for the Discord
conversational pipeline, handling feature flag gating and graceful degradation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.config.feature_flags import FeatureFlags


logger = logging.getLogger(__name__)


class MCPIntegrationLayer:
    """Unified integration layer for all MCP servers."""

    def __init__(self, feature_flags: FeatureFlags):
        self.feature_flags = feature_flags
        self._mcp_servers = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize MCP servers based on feature flags."""
        try:
            # Initialize servers based on feature flags
            if self.feature_flags.ENABLE_MCP_MEMORY:
                await self._init_memory_server()

            if self.feature_flags.ENABLE_MCP_KG:
                await self._init_kg_server()

            if self.feature_flags.ENABLE_MCP_CREWAI:
                await self._init_crewai_server()

            if self.feature_flags.ENABLE_MCP_ROUTER:
                await self._init_routing_server()

            if self.feature_flags.ENABLE_MCP_CREATOR_INTELLIGENCE:
                await self._init_creator_intelligence_server()

            self._initialized = True
            logger.info("MCP integration layer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP integration layer: {e}")
            # Continue with degraded functionality

    async def _init_memory_server(self) -> None:
        """Initialize memory MCP server."""
        try:
            from mcp_server.memory_server import MemoryServer

            self._mcp_servers["memory"] = MemoryServer()
            logger.info("Memory MCP server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize memory MCP server: {e}")

    async def _init_kg_server(self) -> None:
        """Initialize knowledge graph MCP server."""
        try:
            from mcp_server.kg_server import KGServer

            self._mcp_servers["kg"] = KGServer()
            logger.info("Knowledge Graph MCP server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize KG MCP server: {e}")

    async def _init_crewai_server(self) -> None:
        """Initialize CrewAI MCP server."""
        try:
            from mcp_server.crewai_server import CrewAIServer

            self._mcp_servers["crewai"] = CrewAIServer()
            logger.info("CrewAI MCP server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize CrewAI MCP server: {e}")

    async def _init_routing_server(self) -> None:
        """Initialize routing MCP server."""
        try:
            from mcp_server.routing_server import RoutingServer

            self._mcp_servers["routing"] = RoutingServer()
            logger.info("Routing MCP server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize routing MCP server: {e}")

    async def _init_creator_intelligence_server(self) -> None:
        """Initialize creator intelligence MCP server."""
        try:
            from mcp_server.creator_intelligence_server import CreatorIntelligenceServer

            self._mcp_servers["creator_intelligence"] = CreatorIntelligenceServer()
            logger.info("Creator Intelligence MCP server initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize creator intelligence MCP server: {e}")

    # Memory Server Integration
    async def search_memories(
        self, tenant: str, workspace: str, name: str, query: str, k: int = 5, min_score: float | None = None
    ) -> StepResult[dict[str, Any]]:
        """Search memories using vector similarity."""
        if not self.feature_flags.ENABLE_MCP_MEMORY:
            return StepResult.fail("Memory MCP server not enabled")

        memory_server = self._mcp_servers.get("memory")
        if not memory_server:
            return StepResult.fail("Memory MCP server not initialized")

        try:
            result = await memory_server.vs_search(tenant, workspace, name, query, k, min_score)
            return result
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return StepResult.fail(f"Memory search failed: {e!s}")

    async def list_memory_namespaces(self, tenant: str, workspace: str) -> StepResult[list[str]]:
        """List available memory namespaces."""
        if not self.feature_flags.ENABLE_MCP_MEMORY:
            return StepResult.fail("Memory MCP server not enabled")

        memory_server = self._mcp_servers.get("memory")
        if not memory_server:
            return StepResult.fail("Memory MCP server not initialized")

        try:
            result = await memory_server.vs_list_namespaces(tenant, workspace)
            return result
        except Exception as e:
            logger.error(f"List memory namespaces failed: {e}")
            return StepResult.fail(f"List memory namespaces failed: {e!s}")

    async def get_memory_samples(
        self, tenant: str, workspace: str, name: str, probe: str = "", n: int = 3
    ) -> StepResult[list[dict[str, Any]]]:
        """Get sample memories from a collection."""
        if not self.feature_flags.ENABLE_MCP_MEMORY:
            return StepResult.fail("Memory MCP server not enabled")

        memory_server = self._mcp_servers.get("memory")
        if not memory_server:
            return StepResult.fail("Memory MCP server not initialized")

        try:
            result = await memory_server.vs_samples(tenant, workspace, name, probe, n)
            return result
        except Exception as e:
            logger.error(f"Get memory samples failed: {e}")
            return StepResult.fail(f"Get memory samples failed: {e!s}")

    # Knowledge Graph Server Integration
    async def query_knowledge_graph(self, tenant: str, entity: str, depth: int = 1) -> StepResult[dict[str, Any]]:
        """Query the knowledge graph for entity relationships."""
        if not self.feature_flags.ENABLE_MCP_KG:
            return StepResult.fail("Knowledge Graph MCP server not enabled")

        kg_server = self._mcp_servers.get("kg")
        if not kg_server:
            return StepResult.fail("Knowledge Graph MCP server not initialized")

        try:
            result = await kg_server.kg_query(tenant, entity, depth)
            return result
        except Exception as e:
            logger.error(f"Knowledge graph query failed: {e}")
            return StepResult.fail(f"Knowledge graph query failed: {e!s}")

    async def get_entity_timeline(self, tenant: str, entity: str) -> StepResult[list[dict[str, Any]]]:
        """Get timeline events for an entity."""
        if not self.feature_flags.ENABLE_MCP_KG:
            return StepResult.fail("Knowledge Graph MCP server not enabled")

        kg_server = self._mcp_servers.get("kg")
        if not kg_server:
            return StepResult.fail("Knowledge Graph MCP server not initialized")

        try:
            result = await kg_server.kg_timeline(tenant, entity)
            return result
        except Exception as e:
            logger.error(f"Entity timeline query failed: {e}")
            return StepResult.fail(f"Entity timeline query failed: {e!s}")

    # CrewAI Server Integration
    async def execute_crew(self, inputs: dict[str, Any], crew_type: str = "default") -> StepResult[dict[str, Any]]:
        """Execute a CrewAI crew."""
        if not self.feature_flags.ENABLE_MCP_CREWAI:
            return StepResult.fail("CrewAI MCP server not enabled")

        crewai_server = self._mcp_servers.get("crewai")
        if not crewai_server:
            return StepResult.fail("CrewAI MCP server not initialized")

        try:
            result = await crewai_server.execute_crew(inputs, crew_type)
            return result
        except Exception as e:
            logger.error(f"CrewAI execution failed: {e}")
            return StepResult.fail(f"CrewAI execution failed: {e!s}")

    async def get_crew_status(self) -> StepResult[dict[str, Any]]:
        """Get current crew system status."""
        if not self.feature_flags.ENABLE_MCP_CREWAI:
            return StepResult.fail("CrewAI MCP server not enabled")

        crewai_server = self._mcp_servers.get("crewai")
        if not crewai_server:
            return StepResult.fail("CrewAI MCP server not initialized")

        try:
            result = await crewai_server.get_crew_status()
            return result
        except Exception as e:
            logger.error(f"Get crew status failed: {e}")
            return StepResult.fail(f"Get crew status failed: {e!s}")

    async def get_agent_performance(self, agent_name: str | None = None) -> StepResult[dict[str, Any]]:
        """Get agent performance metrics."""
        if not self.feature_flags.ENABLE_MCP_CREWAI:
            return StepResult.fail("CrewAI MCP server not enabled")

        crewai_server = self._mcp_servers.get("crewai")
        if not crewai_server:
            return StepResult.fail("CrewAI MCP server not initialized")

        try:
            result = await crewai_server.get_agent_performance(agent_name)
            return result
        except Exception as e:
            logger.error(f"Get agent performance failed: {e}")
            return StepResult.fail(f"Get agent performance failed: {e!s}")

    # Routing Server Integration
    async def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> StepResult[dict[str, Any]]:
        """Estimate cost for LLM call."""
        if not self.feature_flags.ENABLE_MCP_ROUTER:
            return StepResult.fail("Routing MCP server not enabled")

        routing_server = self._mcp_servers.get("routing")
        if not routing_server:
            return StepResult.fail("Routing MCP server not initialized")

        try:
            result = await routing_server.estimate_cost(model, input_tokens, output_tokens)
            return result
        except Exception as e:
            logger.error(f"Cost estimation failed: {e}")
            return StepResult.fail(f"Cost estimation failed: {e!s}")

    async def route_completion(self, task: str, tokens_hint: int | None = None) -> StepResult[dict[str, Any]]:
        """Get routing suggestion for task completion."""
        if not self.feature_flags.ENABLE_MCP_ROUTER:
            return StepResult.fail("Routing MCP server not enabled")

        routing_server = self._mcp_servers.get("routing")
        if not routing_server:
            return StepResult.fail("Routing MCP server not initialized")

        try:
            result = await routing_server.route_completion(task, tokens_hint)
            return result
        except Exception as e:
            logger.error(f"Routing suggestion failed: {e}")
            return StepResult.fail(f"Routing suggestion failed: {e!s}")

    async def choose_embedding_model(self, dimensions_required: int | None = None) -> StepResult[dict[str, Any]]:
        """Choose optimal embedding model."""
        if not self.feature_flags.ENABLE_MCP_ROUTER:
            return StepResult.fail("Routing MCP server not enabled")

        routing_server = self._mcp_servers.get("routing")
        if not routing_server:
            return StepResult.fail("Routing MCP server not initialized")

        try:
            result = await routing_server.choose_embedding_model(dimensions_required)
            return result
        except Exception as e:
            logger.error(f"Embedding model selection failed: {e}")
            return StepResult.fail(f"Embedding model selection failed: {e!s}")

    # Creator Intelligence Server Integration
    async def ingest_youtube_video(
        self, url: str, tenant: str, workspace: str, fetch_transcript: bool = True
    ) -> StepResult[dict[str, Any]]:
        """Ingest YouTube video content."""
        if not self.feature_flags.ENABLE_MCP_CREATOR_INTELLIGENCE:
            return StepResult.fail("Creator Intelligence MCP server not enabled")

        creator_server = self._mcp_servers.get("creator_intelligence")
        if not creator_server:
            return StepResult.fail("Creator Intelligence MCP server not initialized")

        try:
            result = await creator_server.ingest_youtube_video(url, tenant, workspace, fetch_transcript)
            return result
        except Exception as e:
            logger.error(f"YouTube ingestion failed: {e}")
            return StepResult.fail(f"YouTube ingestion failed: {e!s}")

    async def query_creator_content(
        self,
        query_text: str,
        collection_type: str,
        tenant: str,
        workspace: str,
        limit: int = 10,
        score_threshold: float = 0.7,
    ) -> StepResult[list[dict[str, Any]]]:
        """Query creator content using semantic search."""
        if not self.feature_flags.ENABLE_MCP_CREATOR_INTELLIGENCE:
            return StepResult.fail("Creator Intelligence MCP server not enabled")

        creator_server = self._mcp_servers.get("creator_intelligence")
        if not creator_server:
            return StepResult.fail("Creator Intelligence MCP server not initialized")

        try:
            result = await creator_server.query_creator_content(
                query_text, collection_type, tenant, workspace, limit, score_threshold
            )
            return result
        except Exception as e:
            logger.error(f"Creator content query failed: {e}")
            return StepResult.fail(f"Creator content query failed: {e!s}")

    async def get_collection_stats(
        self, collection_type: str, tenant: str, workspace: str
    ) -> StepResult[dict[str, Any]]:
        """Get collection statistics."""
        if not self.feature_flags.ENABLE_MCP_CREATOR_INTELLIGENCE:
            return StepResult.fail("Creator Intelligence MCP server not enabled")

        creator_server = self._mcp_servers.get("creator_intelligence")
        if not creator_server:
            return StepResult.fail("Creator Intelligence MCP server not initialized")

        try:
            result = await creator_server.get_collection_stats(collection_type, tenant, workspace)
            return result
        except Exception as e:
            logger.error(f"Get collection stats failed: {e}")
            return StepResult.fail(f"Get collection stats failed: {e!s}")

    async def get_integration_status(self) -> dict[str, Any]:
        """Get status of all MCP server integrations."""
        status = {
            "initialized": self._initialized,
            "servers": {},
        }

        # Check each server
        server_checks = {
            "memory": self.feature_flags.ENABLE_MCP_MEMORY,
            "kg": self.feature_flags.ENABLE_MCP_KG,
            "crewai": self.feature_flags.ENABLE_MCP_CREWAI,
            "routing": self.feature_flags.ENABLE_MCP_ROUTER,
            "creator_intelligence": self.feature_flags.ENABLE_MCP_CREATOR_INTELLIGENCE,
        }

        for server_name, enabled in server_checks.items():
            status["servers"][server_name] = {
                "enabled": enabled,
                "initialized": server_name in self._mcp_servers,
                "available": enabled and server_name in self._mcp_servers,
            }

        return status
