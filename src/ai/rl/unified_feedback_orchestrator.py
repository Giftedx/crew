"""Unified Feedback Loop Orchestrator

Central coordinator connecting:
- Trajectory evaluator → Bandit reward signals
- Routing updates → All tools/agents
- Memory consolidation triggers
- Shadow experiments
- Feature engineering pipeline
- Unified metrics and health monitoring
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from eval.trajectory_evaluator import AgentTrajectory
    from ultimate_discord_intelligence_bot.services.rl_model_router import RLModelRouter

logger = logging.getLogger(__name__)


class FeedbackSource(Enum):
    """Sources of feedback signals"""

    TRAJECTORY = "trajectory"
    RAG_RETRIEVAL = "rag_retrieval"
    TOOL_EXECUTION = "tool_execution"
    AGENT_TASK = "agent_task"
    GOVERNANCE = "governance"
    COST_BUDGET = "cost_budget"
    USER_EXPLICIT = "user_explicit"


class ComponentType(Enum):
    """Types of components that can receive feedback"""

    MODEL = "model"
    TOOL = "tool"
    AGENT = "agent"
    THRESHOLD = "threshold"
    PROMPT = "prompt"
    MEMORY = "memory"


@dataclass
class UnifiedFeedbackSignal:
    """Unified feedback signal from any source"""

    signal_id: str
    source: FeedbackSource
    component_type: ComponentType
    component_id: str
    reward: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class OrchestratorMetrics:
    """Metrics for orchestrator performance"""

    signals_processed: int = 0
    signals_by_source: dict[FeedbackSource, int] = field(default_factory=dict)
    signals_by_component: dict[ComponentType, int] = field(default_factory=dict)
    average_reward_by_component: dict[str, float] = field(default_factory=dict)
    consolidations_triggered: int = 0
    experiments_deployed: int = 0
    health_checks_performed: int = 0
    last_consolidation: float = 0.0
    uptime_seconds: float = 0.0


class UnifiedFeedbackOrchestrator:
    """
    Central orchestrator for all AI/ML/RL feedback loops.

    Responsibilities:
    1. Collect feedback from all sources (trajectories, tools, agents, RAG, etc.)
    2. Route feedback to appropriate bandit systems (models, tools, agents, thresholds)
    3. Trigger memory consolidation based on quality signals
    4. Coordinate shadow A/B experiments
    5. Manage feature engineering pipeline
    6. Monitor system health and auto-disable failing components
    7. Provide unified metrics and observability
    """

    def __init__(
        self,
        model_router: RLModelRouter | None = None,
        consolidation_interval_seconds: float = 3600.0,  # 1 hour
        health_check_interval_seconds: float = 300.0,  # 5 minutes
        max_queue_size: int = 10000,
    ):
        # Core dependencies (lazy loaded)
        self.model_router = model_router
        self._tool_router: Any = None
        self._agent_router: Any = None
        self._threshold_router: Any = None
        self._prompt_router: Any = None
        self._memory_consolidator: Any = None
        self._experiment_framework: Any = None
        self._health_monitor: Any = None
        self._feature_engineer: Any = None

        # Feedback queues by component type
        self.feedback_queues: dict[ComponentType, deque[UnifiedFeedbackSignal]] = {
            ct: deque(maxlen=max_queue_size) for ct in ComponentType
        }

        # Processing configuration
        self.consolidation_interval = consolidation_interval_seconds
        self.health_check_interval = health_check_interval_seconds
        self.max_queue_size = max_queue_size

        # Metrics
        self.metrics = OrchestratorMetrics()
        self.start_time = time.time()

        # Component health tracking
        self.component_health: dict[str, dict[str, Any]] = defaultdict(dict)
        self.disabled_components: set[str] = set()

        # Background tasks
        self._running = False
        self._tasks: list[asyncio.Task] = []

        logger.info("Unified Feedback Orchestrator initialized")

    async def start(self) -> StepResult:
        """Start background processing tasks"""
        if self._running:
            return StepResult.skip(reason="already_running")

        try:
            self._running = True

            # Start background processors
            self._tasks = [
                asyncio.create_task(self._process_feedback_loop()),
                asyncio.create_task(self._consolidation_loop()),
                asyncio.create_task(self._health_monitoring_loop()),
            ]

            logger.info("Orchestrator background tasks started")
            return StepResult.ok(message="Orchestrator started", tasks=len(self._tasks))

        except Exception as e:
            logger.error(f"Failed to start orchestrator: {e}")
            return StepResult.fail(f"Start failed: {e}")

    async def stop(self) -> StepResult:
        """Stop all background tasks"""
        if not self._running:
            return StepResult.skip(reason="not_running")

        try:
            self._running = False

            # Cancel all tasks
            for task in self._tasks:
                task.cancel()

            # Wait for cancellation
            await asyncio.gather(*self._tasks, return_exceptions=True)

            self._tasks.clear()

            logger.info("Orchestrator stopped")
            return StepResult.ok(message="Orchestrator stopped")

        except Exception as e:
            logger.error(f"Failed to stop orchestrator: {e}")
            return StepResult.fail(f"Stop failed: {e}")

    def submit_feedback(self, signal: UnifiedFeedbackSignal) -> StepResult:
        """Submit a feedback signal for processing"""
        try:
            # Validate signal
            if not 0.0 <= signal.reward <= 1.0:
                return StepResult.fail(f"Invalid reward value: {signal.reward}")

            if not 0.0 <= signal.confidence <= 1.0:
                return StepResult.fail(f"Invalid confidence value: {signal.confidence}")

            # Check if component is disabled
            if signal.component_id in self.disabled_components:
                return StepResult.skip(reason="component_disabled", component_id=signal.component_id)

            # Queue the signal
            self.feedback_queues[signal.component_type].append(signal)

            # Update metrics
            self.metrics.signals_processed += 1
            self.metrics.signals_by_source[signal.source] = self.metrics.signals_by_source.get(signal.source, 0) + 1
            self.metrics.signals_by_component[signal.component_type] = (
                self.metrics.signals_by_component.get(signal.component_type, 0) + 1
            )

            logger.debug(
                f"Feedback queued: {signal.source.value} → {signal.component_type.value}/{signal.component_id}"
            )

            return StepResult.ok(
                message="Feedback queued",
                queue_size=len(self.feedback_queues[signal.component_type]),
            )

        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            return StepResult.fail(f"Submit failed: {e}")

    def submit_trajectory_feedback(self, trajectory: AgentTrajectory, evaluation_result: dict[str, Any]) -> StepResult:
        """Submit feedback from trajectory evaluation"""
        try:
            # Extract model feedback
            model_id = self._extract_model_from_trajectory(trajectory)
            if model_id:
                model_signal = UnifiedFeedbackSignal(
                    signal_id=f"traj_{trajectory.session_id}_model",
                    source=FeedbackSource.TRAJECTORY,
                    component_type=ComponentType.MODEL,
                    component_id=model_id,
                    reward=evaluation_result.get("overall_score", 0.0),
                    confidence=evaluation_result.get("confidence", 0.8),
                    context={
                        "trajectory_id": trajectory.session_id,
                        "accuracy": evaluation_result.get("accuracy_score", 0.0),
                        "efficiency": evaluation_result.get("efficiency_score", 0.0),
                        "error_handling": evaluation_result.get("error_handling_score", 0.0),
                    },
                    metadata={"trajectory_length": len(trajectory.steps)},
                )
                self.submit_feedback(model_signal)

            # Extract tool feedback
            tool_performance = self._extract_tool_performance(trajectory, evaluation_result)
            for tool_id, performance in tool_performance.items():
                tool_signal = UnifiedFeedbackSignal(
                    signal_id=f"traj_{trajectory.session_id}_tool_{tool_id}",
                    source=FeedbackSource.TRAJECTORY,
                    component_type=ComponentType.TOOL,
                    component_id=tool_id,
                    reward=performance["reward"],
                    confidence=performance["confidence"],
                    context=performance.get("context", {}),
                    metadata=performance.get("metadata", {}),
                )
                self.submit_feedback(tool_signal)

            # Extract agent feedback
            agent_id = getattr(trajectory, "agent_id", None)
            if agent_id:
                agent_signal = UnifiedFeedbackSignal(
                    signal_id=f"traj_{trajectory.session_id}_agent",
                    source=FeedbackSource.TRAJECTORY,
                    component_type=ComponentType.AGENT,
                    component_id=agent_id,
                    reward=evaluation_result.get("overall_score", 0.0),
                    confidence=evaluation_result.get("confidence", 0.8),
                    context={
                        "success": trajectory.success,
                        "duration": trajectory.total_duration,
                    },
                )
                self.submit_feedback(agent_signal)

            # INTEGRATION: Extract prompt variant feedback if available
            prompt_variants = self._extract_prompt_variants(trajectory, evaluation_result)
            for variant_id, variant_performance in prompt_variants.items():
                prompt_signal = UnifiedFeedbackSignal(
                    signal_id=f"traj_{trajectory.session_id}_prompt_{variant_id}",
                    source=FeedbackSource.TRAJECTORY,
                    component_type=ComponentType.PROMPT,
                    component_id=variant_id,
                    reward=variant_performance["reward"],
                    confidence=variant_performance.get("confidence", 0.8),
                    context=variant_performance.get("context", {}),
                    metadata=variant_performance.get("metadata", {}),
                )
                self.submit_feedback(prompt_signal)

            return StepResult.ok(message="Trajectory feedback submitted")

        except Exception as e:
            logger.error(f"Failed to submit trajectory feedback: {e}")
            return StepResult.fail(f"Trajectory feedback failed: {e}")

    async def _process_feedback_loop(self) -> None:
        """Background task: Process queued feedback signals"""
        logger.info("Feedback processing loop started")

        while self._running:
            try:
                # Process model feedback
                if self.model_router and self.feedback_queues[ComponentType.MODEL]:
                    await self._process_model_feedback()

                # Process tool feedback
                if self._tool_router and self.feedback_queues[ComponentType.TOOL]:
                    await self._process_tool_feedback()

                # Process agent feedback
                if self._agent_router and self.feedback_queues[ComponentType.AGENT]:
                    await self._process_agent_feedback()

                # Process threshold feedback
                if self._threshold_router and self.feedback_queues[ComponentType.THRESHOLD]:
                    await self._process_threshold_feedback()

                # Process prompt feedback
                if self._prompt_router and self.feedback_queues[ComponentType.PROMPT]:
                    await self._process_prompt_feedback()

                # Sleep to avoid busy waiting
                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback processing loop: {e}")
                await asyncio.sleep(5.0)

        logger.info("Feedback processing loop stopped")

    async def _consolidation_loop(self) -> None:
        """Background task: Trigger memory consolidation periodically"""
        logger.info("Consolidation loop started")

        while self._running:
            try:
                await asyncio.sleep(self.consolidation_interval)

                # INTEGRATION: Check RAG quality signals for consolidation trigger
                should_consolidate, consolidation_reason = await self._check_rag_consolidation_trigger()

                if should_consolidate or self._memory_consolidator:
                    result = await self._trigger_memory_consolidation()
                    if result.success:
                        self.metrics.consolidations_triggered += 1
                        self.metrics.last_consolidation = time.time()
                        if consolidation_reason:
                            logger.info(f"RAG-triggered consolidation completed: {consolidation_reason}")
                        else:
                            logger.info("Scheduled memory consolidation completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in consolidation loop: {e}")
                await asyncio.sleep(60.0)

        logger.info("Consolidation loop stopped")

    async def _health_monitoring_loop(self) -> None:
        """Background task: Monitor component health"""
        logger.info("Health monitoring loop started")

        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)

                if self._health_monitor:
                    result = await self._check_component_health()
                    if result.success:
                        self.metrics.health_checks_performed += 1
                        logger.debug("Health check completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30.0)

        logger.info("Health monitoring loop stopped")

    async def _process_model_feedback(self) -> None:
        """Process queued model feedback"""
        queue = self.feedback_queues[ComponentType.MODEL]
        batch_size = min(10, len(queue))

        for _ in range(batch_size):
            if not queue:
                break

            signal = queue.popleft()

            try:
                # Update model router with feedback
                if self.model_router and hasattr(self.model_router, "bandit"):
                    context_vec = self._extract_context_vector(signal.context)
                    self.model_router.bandit.update(
                        arm_id=signal.component_id,
                        context=context_vec,
                        reward=signal.reward * signal.confidence,  # Confidence-weighted
                        trajectory_feedback=None,
                    )

                # Update average reward metric
                key = f"model/{signal.component_id}"
                current_avg = self.metrics.average_reward_by_component.get(key, signal.reward)
                self.metrics.average_reward_by_component[key] = 0.9 * current_avg + 0.1 * signal.reward  # EMA

            except Exception as e:
                logger.error(f"Failed to process model feedback: {e}")

    async def _process_tool_feedback(self) -> None:
        """Process queued tool feedback"""
        # Will be implemented when tool router is ready
        logger.debug("Tool feedback processing not yet implemented")

    async def _process_agent_feedback(self) -> None:
        """Process queued agent feedback"""
        # Will be implemented when agent router is ready
        logger.debug("Agent feedback processing not yet implemented")

    async def _process_threshold_feedback(self) -> None:
        """Process queued threshold feedback"""
        # Will be implemented when threshold router is ready
        logger.debug("Threshold feedback processing not yet implemented")

    async def _process_prompt_feedback(self) -> None:
        """Process queued prompt feedback"""
        # Will be implemented when prompt router is ready
        logger.debug("Prompt feedback processing not yet implemented")

    async def _trigger_memory_consolidation(self) -> StepResult:
        """Trigger memory consolidation based on quality signals"""
        try:
            # Gather quality signals from memory component feedback
            memory_signals = [
                s for s in self.feedback_queues[ComponentType.MEMORY] if s.source == FeedbackSource.RAG_RETRIEVAL
            ]

            if not memory_signals:
                return StepResult.skip(reason="no_memory_signals")

            # Calculate aggregate quality score
            avg_quality = np.mean([s.reward for s in memory_signals])

            # Trigger consolidation if quality is degrading
            if avg_quality < 0.7 or len(memory_signals) > 1000:
                # Call memory consolidator
                result = await self._memory_consolidator.consolidate()
                return result

            return StepResult.skip(reason="quality_acceptable")

        except Exception as e:
            logger.error(f"Memory consolidation failed: {e}")
            return StepResult.fail(f"Consolidation failed: {e}")

    async def _check_component_health(self) -> StepResult:
        """Check health of all components and auto-disable unhealthy ones"""
        try:
            unhealthy_components = []

            # Check each component type
            for component_type in ComponentType:
                components = self._get_components_by_type(component_type)

                for component_id in components:
                    health = self._calculate_component_health(component_id)

                    self.component_health[component_id] = health

                    # Auto-disable if unhealthy
                    if health["health_score"] < 0.3 and health["sample_size"] > 10:
                        self.disabled_components.add(component_id)
                        unhealthy_components.append(component_id)
                        logger.warning(f"Auto-disabled unhealthy component: {component_id}")

            return StepResult.ok(
                message="Health check completed",
                unhealthy_components=unhealthy_components,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return StepResult.fail(f"Health check failed: {e}")

    def _calculate_component_health(self, component_id: str) -> dict[str, Any]:
        """Calculate health metrics for a component"""
        # Get recent signals for this component
        recent_signals = []
        for queue in self.feedback_queues.values():
            recent_signals.extend([s for s in queue if s.component_id == component_id])

        if not recent_signals:
            return {
                "health_score": 1.0,
                "sample_size": 0,
                "avg_reward": None,
                "error_rate": 0.0,
            }

        # Calculate metrics
        rewards = [s.reward for s in recent_signals]
        avg_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        error_rate = sum(1 for r in rewards if r < 0.3) / len(rewards)

        # Health score combines reward quality and stability
        health_score = avg_reward * (1.0 - error_rate) * (1.0 - min(std_reward, 0.5))

        return {
            "health_score": health_score,
            "sample_size": len(recent_signals),
            "avg_reward": avg_reward,
            "error_rate": error_rate,
            "reward_std": std_reward,
        }

    def _get_components_by_type(self, component_type: ComponentType) -> list[str]:
        """Get all component IDs of a given type"""
        queue = self.feedback_queues[component_type]
        return list({s.component_id for s in queue})

    async def _check_rag_consolidation_trigger(self) -> tuple[bool, str]:
        """Check if RAG quality feedback indicates consolidation is needed.

        Returns:
            Tuple of (should_trigger, reason)
        """
        try:
            # Import RAG feedback system
            from ai.rag.rag_quality_feedback import get_rag_feedback

            rag_feedback = get_rag_feedback(auto_create=False)
            if rag_feedback is None:
                return False, ""

            # Check consolidation trigger
            should_trigger, reason = rag_feedback.should_trigger_consolidation()

            if should_trigger:
                logger.info(f"RAG quality trigger: {reason}")

                # Get pruning candidates
                candidates = rag_feedback.get_pruning_candidates(min_retrievals=5, limit=100)

                if candidates:
                    logger.info(f"Identified {len(candidates)} chunks for pruning")
                    # Store candidates for consolidation process
                    # TODO: Wire to actual memory pruning service when available

                return True, reason

            return False, ""

        except Exception as e:
            logger.warning(f"RAG consolidation check failed: {e}")
            return False, ""

    def _extract_context_vector(self, context: dict[str, Any]) -> np.ndarray:
        """Extract feature vector from context dictionary"""
        # Simple heuristic feature extraction
        features = []

        # Numeric features
        features.append(context.get("accuracy", 0.5))
        features.append(context.get("efficiency", 0.5))
        features.append(context.get("error_handling", 0.5))
        features.append(context.get("latency_ms", 1000.0) / 10000.0)  # Normalize
        features.append(context.get("cost_usd", 0.01) * 100.0)  # Normalize
        features.append(context.get("quality_score", 0.5))
        features.append(1.0 if context.get("success", False) else 0.0)
        features.append(context.get("trajectory_length", 5) / 20.0)  # Normalize
        features.append(context.get("token_count", 1000) / 10000.0)  # Normalize
        features.append(context.get("confidence", 0.5))

        return np.array(features[:10], dtype=float)

    def _extract_model_from_trajectory(self, trajectory: AgentTrajectory) -> str | None:
        """Extract model ID from trajectory"""
        # Try to find model_id in trajectory steps
        if trajectory.steps:
            for step in trajectory.steps:
                if hasattr(step, "tool_args") and step.tool_args:
                    model_id = step.tool_args.get("model_id")
                    if model_id:
                        return model_id

        # Try trajectory metadata
        return getattr(trajectory, "model_id", None)

    def _extract_tool_performance(
        self, trajectory: AgentTrajectory, evaluation_result: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Extract per-tool performance from trajectory"""
        tool_performance = {}

        if not trajectory.steps:
            return tool_performance

        # Calculate per-tool metrics
        for step in trajectory.steps:
            tool_name = step.tool_name or "unknown"

            if tool_name not in tool_performance:
                tool_performance[tool_name] = {
                    "reward": 0.0,
                    "confidence": 0.0,
                    "count": 0,
                    "context": {},
                    "metadata": {},
                }

            # Simple heuristic: success rate as reward
            success = 1.0 if step.result and hasattr(step.result, "success") and step.result.success else 0.0

            perf = tool_performance[tool_name]
            perf["count"] += 1
            perf["reward"] += success
            perf["confidence"] = 0.8  # Default confidence

        # Average rewards
        for tool_name in tool_performance:
            perf = tool_performance[tool_name]
            perf["reward"] /= max(perf["count"], 1)
            perf["context"]["usage_count"] = perf["count"]

        return tool_performance

    def _extract_prompt_variants(
        self, trajectory: AgentTrajectory, evaluation_result: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Extract per-prompt variant performance from trajectory.

        Returns:
            Dictionary mapping prompt_variant_id to performance metrics
        """
        prompt_performance = {}

        # Check if trajectory tracks prompt variants
        if not hasattr(trajectory, "prompt_variants"):
            return prompt_performance

        prompt_variants = getattr(trajectory, "prompt_variants", [])
        if not prompt_variants:
            return prompt_performance

        # Extract performance for each prompt variant used
        for variant in prompt_variants:
            variant_id = variant.get("variant_id") or variant.get("id")
            if not variant_id:
                continue

            # Calculate reward based on variant's contribution to overall quality
            quality_contribution = variant.get("quality_score", evaluation_result.get("overall_score", 0.0))
            latency = variant.get("latency_ms", 0.0)

            # Reward combines quality and efficiency
            reward = quality_contribution
            if latency > 0:
                # Penalty for high latency variants
                latency_penalty = min(0.2, latency / 10000.0)
                reward -= latency_penalty

            prompt_performance[variant_id] = {
                "reward": max(0.0, min(1.0, reward)),
                "confidence": 0.8,
                "context": {
                    "quality_contribution": quality_contribution,
                    "latency_ms": latency,
                    "prompt_type": variant.get("prompt_type", "unknown"),
                },
                "metadata": {
                    "trajectory_id": trajectory.session_id,
                    "variant_index": variant.get("index", 0),
                },
            }

        return prompt_performance

    def get_metrics(self) -> OrchestratorMetrics:
        """Get current orchestrator metrics"""
        self.metrics.uptime_seconds = time.time() - self.start_time
        return self.metrics

    def get_component_health_report(self) -> dict[str, Any]:
        """Get health report for all components"""
        return {
            "component_health": dict(self.component_health),
            "disabled_components": list(self.disabled_components),
            "total_components": sum(len(self._get_components_by_type(ct)) for ct in ComponentType),
        }


# Global singleton instance
_orchestrator: UnifiedFeedbackOrchestrator | None = None


def get_orchestrator(auto_create: bool = True) -> UnifiedFeedbackOrchestrator | None:
    """Get global orchestrator instance"""
    global _orchestrator

    if _orchestrator is None and auto_create:
        # Lazy load model router
        try:
            from ultimate_discord_intelligence_bot.services.rl_router_registry import (
                get_rl_model_router,
            )

            model_router = get_rl_model_router(create_if_missing=True)
            _orchestrator = UnifiedFeedbackOrchestrator(model_router=model_router)
        except Exception as e:
            logger.warning(f"Failed to create orchestrator: {e}")
            _orchestrator = UnifiedFeedbackOrchestrator()

    return _orchestrator


def set_orchestrator(orchestrator: UnifiedFeedbackOrchestrator) -> None:
    """Set global orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator


__all__ = [
    "ComponentType",
    "FeedbackSource",
    "OrchestratorMetrics",
    "UnifiedFeedbackOrchestrator",
    "UnifiedFeedbackSignal",
    "get_orchestrator",
    "set_orchestrator",
]
