"""AI/ML/RL Integration Layer

Wires all AI/ML/RL components together with unified configuration and metrics.
Central integration point for the entire enhanced AI system.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class AIMLRLConfig:
    """Unified configuration for AI/ML/RL system"""

    # Feature flags
    enable_unified_feedback: bool = True
    enable_tool_routing_bandit: bool = True
    enable_agent_routing_bandit: bool = True
    enable_rag_feedback: bool = True
    enable_prompt_ab: bool = True
    enable_threshold_tuning: bool = True
    enable_memory_consolidation: bool = True
    enable_health_monitoring: bool = True

    # Orchestrator settings
    feedback_processing_interval_s: float = 10.0
    consolidation_interval_s: float = 3600.0
    health_check_interval_s: float = 300.0

    # Bandit settings
    exploration_rate: float = 0.1
    learning_rate: float = 0.01
    context_dim: int = 15

    # Quality thresholds
    rag_pruning_threshold: float = 0.3
    rag_consolidation_threshold: float = 0.6
    tool_health_threshold: float = 0.4
    agent_health_threshold: float = 0.4

    # A/B testing
    min_samples_for_promotion: int = 50
    confidence_threshold: float = 0.95

    @classmethod
    def from_env(cls) -> AIMLRLConfig:
        """Create configuration from environment variables"""
        return cls(
            enable_unified_feedback=os.getenv("ENABLE_UNIFIED_FEEDBACK", "1") == "1",
            enable_tool_routing_bandit=os.getenv("ENABLE_TOOL_ROUTING_BANDIT", "1") == "1",
            enable_agent_routing_bandit=os.getenv("ENABLE_AGENT_ROUTING_BANDIT", "1") == "1",
            enable_rag_quality_feedback=os.getenv("ENABLE_RAG_QUALITY_FEEDBACK", "1") == "1",
            enable_prompt_ab_testing=os.getenv("ENABLE_PROMPT_AB_TESTING", "1") == "1",
            exploration_rate=float(os.getenv("BANDIT_EXPLORATION_RATE", "0.1")),
        )


class AIMLRLIntegration:
    """
    Central integration layer for AI/ML/RL system

    Responsibilities:
    1. Initialize all AI/ML/RL components
    2. Wire feedback loops between components
    3. Provide unified access API
    4. Manage background processing tasks
    5. Collect and expose aggregate metrics
    """

    def __init__(self, config: AIMLRLConfig | None = None):
        self.config = config or AIMLRLConfig.from_env()

        # Components (lazy loaded)
        self._orchestrator = None
        self._tool_router = None
        self._agent_router = None
        self._rag_feedback = None
        self._prompt_library = None
        self._threshold_tuner = None
        self._health_monitor = None

        # Background tasks
        self._running = False
        self._tasks: list[asyncio.Task] = []

        logger.info("AI/ML/RL Integration initialized")

    async def start(self) -> StepResult:
        """Start all AI/ML/RL components"""
        try:
            # Initialize components
            await self._initialize_components()

            # Start orchestrator
            if self._orchestrator and self.config.enable_unified_feedback:
                await self._orchestrator.start()

            # Start background tasks
            self._running = True
            self._tasks = [
                asyncio.create_task(self._feedback_processing_loop()),
                asyncio.create_task(self._metrics_collection_loop()),
            ]

            logger.info("AI/ML/RL system started successfully")
            return StepResult.ok(message="AI/ML/RL system started")

        except Exception as e:
            logger.error(f"Failed to start AI/ML/RL system: {e}")
            return StepResult.fail(f"Start failed: {e}")

    async def stop(self) -> StepResult:
        """Stop all components"""
        try:
            self._running = False

            # Cancel tasks
            for task in self._tasks:
                task.cancel()

            await asyncio.gather(*self._tasks, return_exceptions=True)

            # Stop orchestrator
            if self._orchestrator:
                await self._orchestrator.stop()

            logger.info("AI/ML/RL system stopped")
            return StepResult.ok(message="AI/ML/RL system stopped")

        except Exception as e:
            logger.error(f"Failed to stop AI/ML/RL system: {e}")
            return StepResult.fail(f"Stop failed: {e}")

    async def _initialize_components(self) -> None:
        """Initialize all AI/ML/RL components"""
        # Unified Feedback Orchestrator
        if self.config.enable_unified_feedback:
            from core.orchestration.application import get_orchestrator

            self._orchestrator = get_orchestrator(auto_create=True)

            # Connect to routers
            if self.config.enable_tool_routing_bandit:
                from ai.rl.tool_routing_bandit import get_tool_router

                self._tool_router = get_tool_router(auto_create=True)
                self._orchestrator._tool_router = self._tool_router

            if self.config.enable_agent_routing_bandit:
                from ai.rl.agent_routing_bandit import get_agent_router

                self._agent_router = get_agent_router(auto_create=True)
                self._orchestrator._agent_router = self._agent_router

            if self.config.enable_rag_quality_feedback:
                from ai.rag.rag_quality_feedback import get_rag_feedback

                self._rag_feedback = get_rag_feedback(auto_create=True)

            if self.config.enable_prompt_ab_testing:
                from ai.prompts.prompt_library_ab import get_prompt_library

                self._prompt_library = get_prompt_library(auto_create=True)
                self._orchestrator._prompt_router = self._prompt_library

            if self.config.enable_threshold_tuning:
                from ai.rl.threshold_tuning_bandit import get_threshold_bandit

                self._threshold_tuner = get_threshold_bandit(auto_create=True)

        logger.info("AI/ML/RL components initialized")

    async def _feedback_processing_loop(self) -> None:
        """Background task: Process feedback from all sources"""
        logger.info("Feedback processing loop started")

        while self._running:
            try:
                # Process tool feedback
                if self._tool_router:
                    await self._tool_router.process_feedback_batch(batch_size=20)

                # Process agent feedback
                if self._agent_router:
                    await self._agent_router.process_feedback_batch(batch_size=10)

                # Process prompt feedback
                if self._prompt_library:
                    await self._prompt_library.process_feedback_batch(batch_size=20)

                # Process threshold tuning feedback
                if self._threshold_tuner:
                    self._threshold_tuner.process_feedback_batch(batch_size=20)

                # Sleep
                await asyncio.sleep(self.config.feedback_processing_interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback processing loop: {e}")
                await asyncio.sleep(5.0)

        logger.info("Feedback processing loop stopped")

    async def _metrics_collection_loop(self) -> None:
        """Background task: Collect and expose metrics"""
        logger.info("Metrics collection loop started")

        while self._running:
            try:
                # Collect metrics from all components
                metrics = await self.get_aggregate_metrics()

                # Emit metrics (can be extended to push to Prometheus, etc.)
                logger.debug(f"Aggregate metrics: {metrics}")

                await asyncio.sleep(60.0)  # Collect every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(30.0)

        logger.info("Metrics collection loop stopped")

    async def get_aggregate_metrics(self) -> dict[str, Any]:
        """Get aggregate metrics from all components"""
        metrics = {
            "orchestrator": None,
            "tool_router": None,
            "agent_router": None,
            "rag_feedback": None,
            "prompt_library": None,
            "threshold_tuner": None,
        }

        try:
            if self._orchestrator:
                metrics["orchestrator"] = self._orchestrator.get_metrics().__dict__

            if self._tool_router:
                metrics["tool_router"] = self._tool_router.get_statistics()

            if self._agent_router:
                metrics["agent_router"] = self._agent_router.get_statistics()

            if self._rag_feedback:
                metrics["rag_feedback"] = self._rag_feedback.get_quality_report()

            if self._prompt_library:
                metrics["prompt_library"] = self._prompt_library.get_variant_statistics()

            if self._threshold_tuner:
                metrics["threshold_tuner"] = self._threshold_tuner.get_metrics()

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")

        return metrics

    # Public API methods

    async def route_tool(
        self, task_description: str, context: dict[str, Any], task_type: str = "general"
    ) -> StepResult:
        """Route a task to the best tool"""
        if not self._tool_router:
            return StepResult.fail("Tool routing not enabled")

        return await self._tool_router.route_tool_request(task_description, context, task_type)

    async def route_agent(
        self, task_description: str, context: dict[str, Any], task_type: str = "general"
    ) -> StepResult:
        """Route a task to the best agent"""
        if not self._agent_router:
            return StepResult.fail("Agent routing not enabled")

        return await self._agent_router.route_agent_task(task_description, context, task_type)

    async def select_prompt(
        self, prompt_type: str, context: dict[str, Any], optimization_target: str = "quality"
    ) -> StepResult:
        """Select best prompt variant"""
        if not self._prompt_library:
            return StepResult.fail("Prompt A/B testing not enabled")

        from ai.prompts.prompt_library_ab import PromptType

        try:
            pt = PromptType(prompt_type)
            return self._prompt_library.select_prompt(pt, context, optimization_target)
        except ValueError:
            return StepResult.fail(f"Invalid prompt type: {prompt_type}")

    def submit_trajectory_feedback(self, trajectory: Any, evaluation_result: dict[str, Any]) -> StepResult:
        """Submit feedback from trajectory evaluation"""
        if not self._orchestrator:
            return StepResult.fail("Orchestrator not enabled")

        return self._orchestrator.submit_trajectory_feedback(trajectory, evaluation_result)

    def submit_rag_feedback(
        self,
        query_id: str,
        query_text: str,
        retrieved_chunks: list[dict[str, Any]],
        relevance_scores: list[float],
    ) -> StepResult:
        """Submit RAG retrieval feedback"""
        if not self._rag_feedback:
            return StepResult.fail("RAG feedback not enabled")

        return self._rag_feedback.submit_retrieval_feedback(query_id, query_text, retrieved_chunks, relevance_scores)

    async def select_thresholds(
        self,
        content_type: str = "general",
        context: dict[str, Any] | None = None,
    ) -> StepResult:
        """Select optimal quality thresholds for content processing"""
        if not self._threshold_tuner:
            return StepResult.fail("Threshold tuning not enabled")

        return await self._threshold_tuner.select_thresholds(content_type, context or {})

    def submit_threshold_feedback(
        self,
        config_id: str,
        content_type: str,
        bypass_decision: bool,
        cost_saved_usd: float,
        quality_score: float,
        processing_time_saved_s: float = 0.0,
    ) -> StepResult:
        """Submit feedback for threshold decision"""
        if not self._threshold_tuner:
            return StepResult.fail("Threshold tuning not enabled")

        self._threshold_tuner.submit_threshold_feedback(
            config_id,
            content_type,
            bypass_decision,
            cost_saved_usd,
            quality_score,
            processing_time_saved_s,
        )
        return StepResult.ok(message="Threshold feedback submitted")


# Global singleton
_integration: AIMLRLIntegration | None = None


def get_ai_integration(auto_create: bool = True) -> AIMLRLIntegration | None:
    """Get global AI/ML/RL integration instance"""
    global _integration

    if _integration is None and auto_create:
        _integration = AIMLRLIntegration()

    return _integration


def set_ai_integration(integration: AIMLRLIntegration) -> None:
    """Set global AI/ML/RL integration instance"""
    global _integration
    _integration = integration


__all__ = [
    "AIMLRLConfig",
    "AIMLRLIntegration",
    "get_ai_integration",
    "set_ai_integration",
]
