"""
Unified Pipeline for Multi-Agent RL Orchestration System.

This module provides the main orchestration pipeline that integrates
all components: vector memory, RL routing, MCP tools, prompt optimization,
and Discord publishing.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant
from .artifact_publisher import ArtifactMetadata, ArtifactPublisher, DiscordConfig
from .bandit_policy import BanditPolicy
from .context_service import ContextService
from .embedding_service import EmbeddingService
from .mcp_client import MCPClient
from .memory_service import MemoryService
from .observability_service import ObservabilityService
from .optimization_pipeline import OptimizationPipeline
from .prompt_compressor import CompressionConfig, PromptCompressor
from .prompt_engine import PromptEngine
from .routing_service import RoutingService


logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline."""

    # Vector Memory
    enable_vector_memory: bool = True
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # RL Routing
    enable_rl_routing: bool = True
    available_providers: list[str] | None = None
    bandit_alpha_prior: float = 1.0
    bandit_beta_prior: float = 1.0

    # MCP Tools
    enable_mcp_tools: bool = True
    mcp_base_url: str = "https://api.mcp.io"
    mcp_api_key: str | None = None

    # Prompt Optimization
    enable_prompt_optimization: bool = True
    target_compression_ratio: float = 0.5
    min_quality_threshold: float = 0.8

    # Discord Publishing
    enable_discord_publishing: bool = True
    discord_webhook_url: str | None = None
    discord_bot_token: str | None = None

    # Observability
    enable_observability: bool = True
    metrics_endpoint: str | None = None


class UnifiedPipeline:
    """Unified pipeline orchestrating all system components."""

    def __init__(self, config: PipelineConfig | None = None):
        """Initialize the unified pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        self.components: dict[str, Any] = {}
        self.initialized = False

        logger.info("Initialized UnifiedPipeline with config: %s", self.config)

    async def initialize(self) -> StepResult:
        """Initialize all pipeline components.

        Returns:
            StepResult indicating initialization success/failure
        """
        try:
            logger.info("Initializing unified pipeline components...")

            # Initialize observability first
            if self.config.enable_observability:
                self.components["observability"] = ObservabilityService()
                logger.info("Initialized observability service")

            # Initialize context service
            self.components["context"] = ContextService()
            logger.info("Initialized context service")

            # Initialize vector memory components
            if self.config.enable_vector_memory:
                await self._initialize_vector_memory()
                logger.info("Initialized vector memory components")

            # Initialize RL routing components
            if self.config.enable_rl_routing:
                await self._initialize_rl_routing()
                logger.info("Initialized RL routing components")

            # Initialize MCP tools
            if self.config.enable_mcp_tools:
                await self._initialize_mcp_tools()
                logger.info("Initialized MCP tools")

            # Initialize prompt optimization
            if self.config.enable_prompt_optimization:
                await self._initialize_prompt_optimization()
                logger.info("Initialized prompt optimization")

            # Initialize Discord publishing
            if self.config.enable_discord_publishing:
                await self._initialize_discord_publishing()
                logger.info("Initialized Discord publishing")

            self.initialized = True
            logger.info("Unified pipeline initialization completed successfully")

            return StepResult.ok(data={"initialized": True, "components": list(self.components.keys())})

        except Exception as e:
            logger.error("Pipeline initialization failed: %s", str(e))
            return StepResult.fail(f"Pipeline initialization failed: {e!s}")

    async def _initialize_vector_memory(self):
        """Initialize vector memory components."""
        # Initialize embedding service
        self.components["embedding"] = EmbeddingService()

        # Initialize memory service
        self.components["memory"] = MemoryService(
            qdrant_url=self.config.qdrant_url,
            qdrant_api_key=self.config.qdrant_api_key,
        )

    async def _initialize_rl_routing(self):
        """Initialize RL routing components."""
        if not self.config.available_providers:
            self.config.available_providers = ["openai", "anthropic", "cohere"]

        # Initialize bandit policy
        self.components["bandit_policy"] = BanditPolicy(
            context_service=self.components["context"],
            obs_service=self.components.get("observability"),
            arms=self.config.available_providers,
            alpha_prior=self.config.bandit_alpha_prior,
            beta_prior=self.config.bandit_beta_prior,
        )

        # Initialize routing service
        self.components["routing"] = RoutingService(
            context_service=self.components["context"],
            obs_service=self.components.get("observability"),
            available_providers=self.config.available_providers,
            bandit_alpha_prior=self.config.bandit_alpha_prior,
            bandit_beta_prior=self.config.bandit_beta_prior,
        )

    async def _initialize_mcp_tools(self):
        """Initialize MCP tools."""
        self.components["mcp_client"] = MCPClient(
            base_url=self.config.mcp_base_url,
            api_key=self.config.mcp_api_key,
        )

    async def _initialize_prompt_optimization(self):
        """Initialize prompt optimization components."""
        # Initialize prompt compressor
        compression_config = CompressionConfig(
            target_compression_ratio=self.config.target_compression_ratio,
            min_quality_threshold=self.config.min_quality_threshold,
        )
        self.components["compressor"] = PromptCompressor(compression_config)

        # Initialize optimization pipeline
        self.components["optimization"] = OptimizationPipeline(
            compressor=self.components["compressor"],
        )

        # Initialize prompt engine with optimization
        self.components["prompt_engine"] = PromptEngine()
        self.components["prompt_engine"].enable_optimization(
            compression_config=compression_config,
        )

    async def _initialize_discord_publishing(self):
        """Initialize Discord publishing components."""
        discord_config = DiscordConfig(
            webhook_url=self.config.discord_webhook_url,
            bot_token=self.config.discord_bot_token,
        )
        self.components["artifact_publisher"] = ArtifactPublisher(discord_config)

    @require_tenant(strict_flag_enabled=False)
    async def process_content(
        self,
        content: str,
        content_type: str = "analysis",
        tenant: str = "",
        workspace: str = "",
        **kwargs: Any,
    ) -> StepResult:
        """Process content through the unified pipeline.

        Args:
            content: Content to process
            content_type: Type of content
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional processing parameters

        Returns:
            StepResult with processing results
        """
        try:
            if not self.initialized:
                init_result = await self.initialize()
                if not init_result.success:
                    return init_result

            start_time = time.time()
            logger.info("Processing content through unified pipeline")

            # Step 1: Store in vector memory
            if "memory" in self.components:
                memory_result = await self.components["memory"].add(
                    text=content,
                    tenant=tenant,
                    workspace=workspace,
                )
                if not memory_result.success:
                    logger.warning("Failed to store in memory: %s", memory_result.error)

            # Step 2: Optimize prompt if enabled
            optimized_content = content
            if "prompt_engine" in self.components:
                optimization_result = await self.components["prompt_engine"].generate_optimized(
                    template=content,
                    variables={},
                    tenant=tenant,
                    workspace=workspace,
                )
                if optimization_result.success:
                    optimized_content = optimization_result.data["prompt"]

            # Step 3: Route through RL system
            routing_result = None
            if "routing" in self.components:
                routing_result = await self.components["routing"].select_llm_provider(
                    {
                        "tenant": tenant,
                        "workspace": workspace,
                        "content_type": content_type,
                    }
                )

            # Step 4: Process with MCP tools if available
            mcp_results = {}
            if "mcp_client" in self.components:
                # Example: Use web search tool
                search_result = await self.components["mcp_client"].execute_tool(
                    tool_name="web_search",
                    parameters={"query": content[:100]},  # Truncate for search
                    tenant=tenant,
                    workspace=workspace,
                )
                if search_result.success:
                    mcp_results["web_search"] = search_result.data

            # Step 5: Publish artifacts to Discord
            if "artifact_publisher" in self.components:
                artifact_data = {
                    "content": optimized_content,
                    "analysis": content,
                    "routing_info": routing_result.data if routing_result and routing_result.success else None,
                    "mcp_results": mcp_results,
                }

                metadata = ArtifactMetadata(
                    artifact_id=f"pipeline_{int(time.time())}",
                    title=f"{content_type.title()} Analysis",
                    description=f"Processed {content_type} through unified pipeline",
                    content_type=content_type,
                    tenant=tenant,
                    workspace=workspace,
                    created_at=time.time(),
                    tags=["pipeline", content_type],
                )

                publish_result = await self.components["artifact_publisher"].publish_artifact(
                    artifact_data=artifact_data,
                    metadata=metadata,
                    tenant=tenant,
                    workspace=workspace,
                )

                if publish_result.success:
                    logger.info("Published artifact to Discord: %s", metadata.artifact_id)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000

            # Record metrics
            if "observability" in self.components:
                self.components["observability"].metrics.increment_counter(
                    "pipeline_content_processed",
                    tags={"content_type": content_type, "tenant": tenant},
                )
                self.components["observability"].metrics.record_histogram(
                    "pipeline_processing_time_ms",
                    processing_time,
                    tags={"content_type": content_type, "tenant": tenant},
                )

            return StepResult.ok(
                data={
                    "processed_content": optimized_content,
                    "routing_result": routing_result.data if routing_result and routing_result.success else None,
                    "mcp_results": mcp_results,
                    "processing_time_ms": processing_time,
                    "components_used": list(self.components.keys()),
                }
            )

        except Exception as e:
            logger.error("Content processing failed: %s", str(e))
            return StepResult.fail(f"Content processing failed: {e!s}")

    async def get_pipeline_stats(self) -> StepResult:
        """Get comprehensive pipeline statistics.

        Returns:
            StepResult with pipeline statistics
        """
        try:
            stats = {
                "initialized": self.initialized,
                "components": list(self.components.keys()),
                "config": {
                    "vector_memory_enabled": self.config.enable_vector_memory,
                    "rl_routing_enabled": self.config.enable_rl_routing,
                    "mcp_tools_enabled": self.config.enable_mcp_tools,
                    "prompt_optimization_enabled": self.config.enable_prompt_optimization,
                    "discord_publishing_enabled": self.config.enable_discord_publishing,
                    "observability_enabled": self.config.enable_observability,
                },
            }

            # Get component-specific stats
            if "memory" in self.components:
                memory_stats = self.components["memory"].get_stats()
                if memory_stats.success:
                    stats["memory_stats"] = memory_stats.data

            if "optimization" in self.components:
                opt_stats = self.components["optimization"].get_optimization_stats()
                if opt_stats.success:
                    stats["optimization_stats"] = opt_stats.data

            if "artifact_publisher" in self.components:
                pub_stats = self.components["artifact_publisher"].get_publishing_stats()
                if pub_stats.success:
                    stats["publishing_stats"] = pub_stats.data

            if "routing" in self.components:
                routing_stats = self.components["routing"].get_provider_stats()
                if routing_stats.success:
                    stats["routing_stats"] = routing_stats.data

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error("Failed to get pipeline stats: %s", str(e))
            return StepResult.fail(f"Failed to get pipeline stats: {e!s}")

    async def health_check(self) -> StepResult:
        """Perform comprehensive health check on all components.

        Returns:
            StepResult with health status
        """
        try:
            health_status = {
                "overall_health": "healthy",
                "components": {},
                "timestamp": time.time(),
            }

            # Check each component
            for name, component in self.components.items():
                try:
                    if hasattr(component, "health_check"):
                        health_result = await component.health_check()
                        health_status["components"][name] = {
                            "status": "healthy" if health_result.success else "unhealthy",
                            "details": health_result.data if health_result.success else health_result.error,
                        }
                    else:
                        health_status["components"][name] = {
                            "status": "unknown",
                            "details": "No health check method available",
                        }
                except Exception as e:
                    health_status["components"][name] = {
                        "status": "error",
                        "details": str(e),
                    }

            # Determine overall health
            unhealthy_components = [
                name
                for name, status in health_status["components"].items()
                if status["status"] in ["unhealthy", "error"]
            ]

            if unhealthy_components:
                health_status["overall_health"] = "degraded"
                health_status["unhealthy_components"] = unhealthy_components

            return StepResult.ok(data=health_status)

        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return StepResult.fail(f"Health check failed: {e!s}")

    async def shutdown(self) -> StepResult:
        """Gracefully shutdown the pipeline.

        Returns:
            StepResult indicating shutdown success/failure
        """
        try:
            logger.info("Shutting down unified pipeline...")

            # Shutdown components that need cleanup
            for name, component in self.components.items():
                try:
                    if hasattr(component, "close_session"):
                        await component.close_session()
                    elif hasattr(component, "shutdown"):
                        await component.shutdown()
                except Exception as e:
                    logger.warning("Error shutting down component %s: %s", name, str(e))

            self.components.clear()
            self.initialized = False

            logger.info("Unified pipeline shutdown completed")
            return StepResult.ok(data={"shutdown": True})

        except Exception as e:
            logger.error("Pipeline shutdown failed: %s", str(e))
            return StepResult.fail(f"Pipeline shutdown failed: {e!s}")
