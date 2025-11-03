"""Unified Feedback Orchestrator - Application Layer.

Migrated from src/ai/rl/unified_feedback_orchestrator.py

Central orchestrator for all AI/ML/RL feedback loops. Coordinates feedback signals
from multiple sources (trajectories, tools, agents, RAG) and routes them to appropriate
bandit systems for continuous learning and optimization.

This is a critical piece of infrastructure that enables:
- Model routing bandit updates
- Tool routing optimization
- Agent performance feedback
- Cross-framework learning (Phase 3+)
- Memory consolidation triggers
"""

import asyncio
import contextlib
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from platform.core.step_result import ErrorCategory, StepResult
from platform.orchestration.protocols import (
    BaseOrchestrator,
    OrchestrationContext,
    OrchestrationLayer,
    OrchestrationType,
)
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog


if TYPE_CHECKING:
    from eval.trajectory_evaluator import AgentTrajectory
    from ultimate_discord_intelligence_bot.services.rl_model_router import RLModelRouter
logger = structlog.get_logger(__name__)


class FeedbackSource(Enum):
    """Sources of feedback signals."""

    TRAJECTORY = "trajectory"
    RAG_RETRIEVAL = "rag_retrieval"
    TOOL_EXECUTION = "tool_execution"
    AGENT_TASK = "agent_task"
    GOVERNANCE = "governance"
    COST_BUDGET = "cost_budget"
    USER_EXPLICIT = "user_explicit"


class ComponentType(Enum):
    """Types of components that can receive feedback."""

    MODEL = "model"
    TOOL = "tool"
    AGENT = "agent"
    THRESHOLD = "threshold"
    PROMPT = "prompt"
    MEMORY = "memory"


@dataclass
class UnifiedFeedbackSignal:
    """Unified feedback signal from any source."""

    signal_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source: FeedbackSource = FeedbackSource.TRAJECTORY
    component_type: ComponentType = ComponentType.MODEL
    component_id: str = ""
    reward: float = 0.5
    confidence: float = 0.8
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class FeedbackSignal:
    """Lightweight feedback signal wrapper for backward compatibility."""

    source: FeedbackSource
    component_type: ComponentType
    component_id: str
    reward: float
    confidence: float = 0.8
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    signal_id: str | None = None

    def to_unified(self) -> UnifiedFeedbackSignal:
        """Convert to UnifiedFeedbackSignal."""
        return UnifiedFeedbackSignal(
            signal_id=self.signal_id or uuid.uuid4().hex,
            source=self.source,
            component_type=self.component_type,
            component_id=self.component_id,
            reward=self.reward,
            confidence=self.confidence,
            context=self.context,
            metadata=self.metadata,
            timestamp=self.timestamp,
        )


@dataclass
class OrchestratorMetrics:
    """Metrics for orchestrator performance."""

    signals_processed: int = 0
    signals_by_source: dict[FeedbackSource, int] = field(default_factory=dict)
    signals_by_component: dict[ComponentType, int] = field(default_factory=dict)
    average_reward_by_component: dict[str, float] = field(default_factory=dict)
    consolidations_triggered: int = 0
    experiments_deployed: int = 0
    health_checks_performed: int = 0
    last_consolidation: float = 0.0
    uptime_seconds: float = 0.0


class UnifiedFeedbackOrchestrator(BaseOrchestrator):
    """Central orchestrator for all AI/ML/RL feedback loops.

    Migrated to application layer of hierarchical orchestration framework.
    Coordinates feedback from multiple sources and routes to appropriate
    bandit systems for continuous learning.

    Key responsibilities:
    - Collect feedback from trajectories, tools, agents, RAG
    - Route feedback to model/tool/agent routing bandits
    - Trigger memory consolidation based on quality signals
    - Monitor component health and auto-disable failures
    - Provide unified observability and metrics
    """

    def __init__(
        self,
        model_router: "RLModelRouter | None" = None,
        consolidation_interval_seconds: float = 3600.0,
        health_check_interval_seconds: float = 300.0,
        max_queue_size: int = 10000,
    ) -> None:
        """Initialize unified feedback orchestrator.

        Args:
            model_router: Optional model router for feedback routing
            consolidation_interval_seconds: How often to trigger consolidation (default 1 hour)
            health_check_interval_seconds: How often to check component health (default 5 min)
            max_queue_size: Maximum queue size per component type
        """
        super().__init__(
            layer=OrchestrationLayer.APPLICATION,
            name="unified_feedback",
            orchestration_type=OrchestrationType.COORDINATION,
        )
        self.consolidation_interval = consolidation_interval_seconds
        self.health_check_interval = health_check_interval_seconds
        self.max_queue_size = max_queue_size
        self._feedback_queues: dict[ComponentType, deque] = {
            ComponentType.MODEL: deque(maxlen=max_queue_size),
            ComponentType.TOOL: deque(maxlen=max_queue_size),
            ComponentType.AGENT: deque(maxlen=max_queue_size),
            ComponentType.THRESHOLD: deque(maxlen=max_queue_size),
            ComponentType.PROMPT: deque(maxlen=max_queue_size),
            ComponentType.MEMORY: deque(maxlen=max_queue_size),
        }
        self.model_feedback_queue = self._feedback_queues[ComponentType.MODEL]
        self.tool_feedback_queue = self._feedback_queues[ComponentType.TOOL]
        self.agent_feedback_queue = self._feedback_queues[ComponentType.AGENT]
        self.threshold_feedback_queue = self._feedback_queues[ComponentType.THRESHOLD]
        self.prompt_feedback_queue = self._feedback_queues[ComponentType.PROMPT]
        self.memory_feedback_queue = self._feedback_queues[ComponentType.MEMORY]
        self._model_router = model_router
        self._tool_router = None
        self._agent_router = None
        self._rag_feedback = None
        self._prompt_library = None
        self._threshold_bandit = None
        self._rag_consolidator = None
        self._feature_engineer = None
        self._shadow_deployer = None
        self._metrics = OrchestratorMetrics(
            signals_by_source=dict.fromkeys(FeedbackSource, 0), signals_by_component=dict.fromkeys(ComponentType, 0)
        )
        self._start_time = time.time()
        self._component_health: dict[str, dict[str, Any]] = {}
        self._disabled_components: set[str] = set()
        self._tasks_started = False
        self._shutdown_event = asyncio.Event()

    def _start_background_tasks(self) -> None:
        """Start background processing tasks (lazy initialization).

        Called automatically on first orchestrate() call.
        Uses lazy initialization to avoid RuntimeError when no event loop exists.
        """
        if self._tasks_started:
            return
        try:
            feedback_task = asyncio.create_task(self._feedback_processing_loop())
            consolidation_task = asyncio.create_task(self._consolidation_loop())
            health_task = asyncio.create_task(self._health_monitoring_loop())
            self._background_tasks.add(feedback_task)
            self._background_tasks.add(consolidation_task)
            self._background_tasks.add(health_task)
            self._tasks_started = True
            logger.info("background_tasks_started", orchestrator="unified_feedback", task_count=3)
        except RuntimeError:
            logger.debug("background_tasks_deferred", reason="no_event_loop")

    async def orchestrate(self, context: OrchestrationContext, **kwargs: Any) -> StepResult:
        """Execute unified feedback orchestration.

        This method serves as the main entry point for feedback processing.
        On first call, it starts background tasks. Subsequent calls can submit
        feedback directly or trigger specific operations.

        Args:
            context: Orchestration context with tenant/request metadata
            **kwargs: Operation-specific parameters:
                - operation: str - "submit_feedback", "get_metrics", "get_health"
                - signal: UnifiedFeedbackSignal - Feedback signal to submit
                - trajectory: AgentTrajectory - Trajectory to extract feedback from
                - ... other operation-specific params

        Returns:
            StepResult with operation outcome
        """
        self._log_orchestration_start(context, **kwargs)
        if not self._tasks_started:
            self._start_background_tasks()
        operation = kwargs.get("operation", "submit_feedback")
        try:
            if operation == "submit_feedback":
                signal = kwargs.get("signal")
                if not signal:
                    return StepResult.fail(
                        "Missing required parameter: signal", error_category=ErrorCategory.VALIDATION
                    )
                result = self.submit_feedback(signal)
            elif operation == "submit_trajectory_feedback":
                trajectory = kwargs.get("trajectory")
                if not trajectory:
                    return StepResult.fail(
                        "Missing required parameter: trajectory", error_category=ErrorCategory.VALIDATION
                    )
                result = await self.submit_trajectory_feedback(trajectory)
            elif operation == "get_metrics":
                metrics = self.get_metrics()
                result = StepResult.ok(result={"metrics": metrics})
            elif operation == "get_health":
                health = self.get_component_health_report()
                result = StepResult.ok(result={"health": health})
            elif operation == "start":
                self._start_background_tasks()
                result = StepResult.ok(result={"status": "started", "background_tasks": len(self._background_tasks)})
            elif operation == "stop":
                result = await self.stop()
            else:
                result = StepResult.fail(f"Unknown operation: {operation}", error_category=ErrorCategory.VALIDATION)
            self._log_orchestration_end(context, result)
            return result
        except Exception as e:
            logger.exception("orchestration_error", operation=operation, error=str(e))
            result = StepResult.fail(f"Orchestration failed: {e}", error_category=ErrorCategory.PROCESSING)
            self._log_orchestration_end(context, result)
            return result

    def submit_feedback(self, signal: UnifiedFeedbackSignal | FeedbackSignal) -> StepResult:
        """Submit a feedback signal for processing.

        Args:
            signal: Feedback signal to submit

        Returns:
            StepResult indicating success/failure
        """
        try:
            if isinstance(signal, FeedbackSignal):
                signal = signal.to_unified()
            if not isinstance(signal, UnifiedFeedbackSignal):
                return StepResult.fail("Invalid signal type", error_category=ErrorCategory.VALIDATION)
            if not 0.0 <= signal.reward <= 1.0:
                return StepResult.fail(
                    f"Reward must be in [0.0, 1.0], got {signal.reward}", error_category=ErrorCategory.VALIDATION
                )
            if not 0.0 <= signal.confidence <= 1.0:
                return StepResult.fail(
                    f"Confidence must be in [0.0, 1.0], got {signal.confidence}",
                    error_category=ErrorCategory.VALIDATION,
                )
            queue = self._feedback_queues.get(signal.component_type)
            if not queue:
                return StepResult.fail(
                    f"Unknown component type: {signal.component_type}", error_category=ErrorCategory.VALIDATION
                )
            queue.append(signal)
            self._metrics.signals_by_source[signal.source] = self._metrics.signals_by_source.get(signal.source, 0) + 1
            self._metrics.signals_by_component[signal.component_type] = (
                self._metrics.signals_by_component.get(signal.component_type, 0) + 1
            )
            logger.debug(
                "feedback_queued",
                signal_id=signal.signal_id,
                source=signal.source.value,
                component=signal.component_type.value,
                reward=signal.reward,
                queue_size=len(queue),
            )
            return StepResult.ok(result={"signal_id": signal.signal_id, "queued": True, "queue_size": len(queue)})
        except Exception as e:
            logger.exception("submit_feedback_error", error=str(e))
            return StepResult.fail(f"Failed to submit feedback: {e}", error_category=ErrorCategory.PROCESSING)

    def submit_tool_feedback(
        self,
        tool_name: str,
        reward: float,
        confidence: float = 0.8,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Submit feedback for a tool execution.

        Args:
            tool_name: Name of the tool
            reward: Reward signal (0.0-1.0)
            confidence: Confidence in the reward (0.0-1.0)
            context: Additional context
            metadata: Additional metadata

        Returns:
            StepResult from submit_feedback()
        """
        signal = UnifiedFeedbackSignal(
            source=FeedbackSource.TOOL_EXECUTION,
            component_type=ComponentType.TOOL,
            component_id=tool_name,
            reward=reward,
            confidence=confidence,
            context=context or {},
            metadata=metadata or {},
        )
        return self.submit_feedback(signal)

    def submit_agent_feedback(
        self,
        agent_id: str,
        reward: float,
        confidence: float = 0.8,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Submit feedback for an agent task.

        Args:
            agent_id: Agent identifier
            reward: Reward signal (0.0-1.0)
            confidence: Confidence in the reward (0.0-1.0)
            context: Additional context
            metadata: Additional metadata

        Returns:
            StepResult from submit_feedback()
        """
        signal = UnifiedFeedbackSignal(
            source=FeedbackSource.AGENT_TASK,
            component_type=ComponentType.AGENT,
            component_id=agent_id,
            reward=reward,
            confidence=confidence,
            context=context or {},
            metadata=metadata or {},
        )
        return self.submit_feedback(signal)

    def submit_rag_feedback(
        self,
        retrieval_id: str,
        reward: float,
        confidence: float = 0.8,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StepResult:
        """Submit feedback for a RAG retrieval.

        Args:
            retrieval_id: Retrieval identifier
            reward: Reward signal (0.0-1.0)
            confidence: Confidence in the reward (0.0-1.0)
            context: Additional context
            metadata: Additional metadata

        Returns:
            StepResult from submit_feedback()
        """
        signal = UnifiedFeedbackSignal(
            source=FeedbackSource.RAG_RETRIEVAL,
            component_type=ComponentType.MEMORY,
            component_id=retrieval_id,
            reward=reward,
            confidence=confidence,
            context=context or {},
            metadata=metadata or {},
        )
        return self.submit_feedback(signal)

    async def submit_trajectory_feedback(self, trajectory: "AgentTrajectory") -> StepResult:
        """Extract and submit feedback from an agent trajectory.

        Analyzes trajectory to extract feedback for multiple components:
        - Model performance (from LLM calls)
        - Tool usage (from tool executions)
        - Agent coordination (from task completion)

        Args:
            trajectory: Agent trajectory to analyze

        Returns:
            StepResult with submitted signal count
        """
        try:
            signals_submitted = 0
            if hasattr(trajectory, "llm_calls") and trajectory.llm_calls:
                for call in trajectory.llm_calls:
                    model_id = call.get("model", "unknown")
                    reward = self._calculate_model_reward(call)
                    signal = UnifiedFeedbackSignal(
                        source=FeedbackSource.TRAJECTORY,
                        component_type=ComponentType.MODEL,
                        component_id=model_id,
                        reward=reward,
                        confidence=0.8,
                        context={"call": call},
                        metadata={"trajectory_id": trajectory.trajectory_id},
                    )
                    result = self.submit_feedback(signal)
                    if result.success:
                        signals_submitted += 1
            if hasattr(trajectory, "tool_calls") and trajectory.tool_calls:
                for call in trajectory.tool_calls:
                    tool_name = call.get("tool", "unknown")
                    reward = self._calculate_tool_reward(call)
                    signal = UnifiedFeedbackSignal(
                        source=FeedbackSource.TRAJECTORY,
                        component_type=ComponentType.TOOL,
                        component_id=tool_name,
                        reward=reward,
                        confidence=0.7,
                        context={"call": call},
                        metadata={"trajectory_id": trajectory.trajectory_id},
                    )
                    result = self.submit_feedback(signal)
                    if result.success:
                        signals_submitted += 1
            if hasattr(trajectory, "success"):
                agent_id = getattr(trajectory, "agent_id", "unknown")
                reward = 1.0 if trajectory.success else 0.0
                signal = UnifiedFeedbackSignal(
                    source=FeedbackSource.TRAJECTORY,
                    component_type=ComponentType.AGENT,
                    component_id=agent_id,
                    reward=reward,
                    confidence=0.9,
                    context={"trajectory": trajectory.__dict__},
                    metadata={"trajectory_id": trajectory.trajectory_id},
                )
                result = self.submit_feedback(signal)
                if result.success:
                    signals_submitted += 1
            logger.info(
                "trajectory_feedback_extracted",
                trajectory_id=trajectory.trajectory_id,
                signals_submitted=signals_submitted,
            )
            return StepResult.ok(
                result={"trajectory_id": trajectory.trajectory_id, "signals_submitted": signals_submitted}
            )
        except Exception as e:
            logger.exception("trajectory_feedback_error", error=str(e))
            return StepResult.fail(f"Failed to process trajectory: {e}", error_category=ErrorCategory.PROCESSING)

    def _calculate_model_reward(self, llm_call: dict[str, Any]) -> float:
        """Calculate reward for a model call based on success, latency, cost."""
        success = llm_call.get("success", True)
        latency = llm_call.get("latency_ms", 0)
        cost = llm_call.get("cost_usd", 0)
        if not success:
            return 0.0
        reward = 1.0
        reward -= min(latency / 10000, 0.3)
        reward -= min(cost * 100, 0.2)
        return max(0.0, min(1.0, reward))

    def _calculate_tool_reward(self, tool_call: dict[str, Any]) -> float:
        """Calculate reward for a tool call based on success and relevance."""
        success = tool_call.get("success", True)
        relevance = tool_call.get("relevance_score", 0.5)
        if not success:
            return 0.0
        return max(0.0, min(1.0, relevance))

    async def _feedback_processing_loop(self) -> None:
        """Background loop to process queued feedback.

        Runs every 1 second, processes feedback from all queues,
        and routes to appropriate bandit systems.
        """
        logger.info("feedback_processing_loop_started")
        while not self._shutdown_event.is_set():
            try:
                for component_type, queue in self._feedback_queues.items():
                    if not queue:
                        continue
                    batch_size = min(10, len(queue))
                    for _ in range(batch_size):
                        if not queue:
                            break
                        signal = queue.popleft()
                        if component_type == ComponentType.MODEL:
                            await self._process_model_feedback(signal)
                        elif component_type == ComponentType.TOOL:
                            await self._process_tool_feedback(signal)
                        elif component_type == ComponentType.AGENT:
                            await self._process_agent_feedback(signal)
                        self._metrics.signals_processed += 1
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                logger.info("feedback_processing_loop_cancelled")
                break
            except Exception as e:
                logger.exception("feedback_processing_error", error=str(e))
                await asyncio.sleep(1.0)
        logger.info("feedback_processing_loop_stopped")

    async def _consolidation_loop(self) -> None:
        """Background loop to trigger memory consolidation.

        Runs every consolidation_interval (default 1 hour),
        checks if consolidation should be triggered based on
        quality signals and RAG feedback.
        """
        logger.info("consolidation_loop_started", interval_seconds=self.consolidation_interval)
        while not self._shutdown_event.is_set():
            try:
                should_consolidate = await self._check_rag_consolidation_trigger()
                if should_consolidate:
                    await self._trigger_memory_consolidation()
                    self._metrics.consolidations_triggered += 1
                    self._metrics.last_consolidation = time.time()
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.consolidation_interval)
            except asyncio.CancelledError:
                logger.info("consolidation_loop_cancelled")
                break
            except Exception as e:
                logger.exception("consolidation_loop_error", error=str(e))
                await asyncio.sleep(60.0)
        logger.info("consolidation_loop_stopped")

    async def _health_monitoring_loop(self) -> None:
        """Background loop to monitor component health.

        Runs every health_check_interval (default 5 minutes),
        calculates health scores for each component, and
        auto-disables components that fall below thresholds.
        """
        logger.info("health_monitoring_loop_started", interval_seconds=self.health_check_interval)
        while not self._shutdown_event.is_set():
            try:
                await self._check_component_health()
                self._metrics.health_checks_performed += 1
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.health_check_interval)
            except asyncio.CancelledError:
                logger.info("health_monitoring_loop_cancelled")
                break
            except Exception as e:
                logger.exception("health_monitoring_error", error=str(e))
                await asyncio.sleep(60.0)
        logger.info("health_monitoring_loop_stopped")

    async def _process_model_feedback(self, signal: UnifiedFeedbackSignal) -> None:
        """Process feedback for model routing bandit."""
        if not self._model_router:
            try:
                from ultimate_discord_intelligence_bot.services.rl_router_registry import get_rl_model_router

                self._model_router = get_rl_model_router()
            except Exception as e:
                logger.warning("model_router_load_failed", error=str(e))
                return
        if self._model_router:
            try:
                context_vector = self._extract_context_vector(signal)
                await self._model_router.update_with_feedback(
                    model_id=signal.component_id, reward=signal.reward, context=context_vector, metadata=signal.metadata
                )
                logger.debug("model_feedback_processed", model_id=signal.component_id, reward=signal.reward)
            except Exception as e:
                logger.exception("model_feedback_processing_error", error=str(e))

    async def _process_tool_feedback(self, signal: UnifiedFeedbackSignal) -> None:
        """Process feedback for tool routing (stub)."""

    async def _process_agent_feedback(self, signal: UnifiedFeedbackSignal) -> None:
        """Process feedback for agent routing (stub)."""

    def _extract_context_vector(self, signal: UnifiedFeedbackSignal) -> np.ndarray:
        """Extract context vector from feedback signal for bandit update."""
        features = []
        source_map = {source: i for i, source in enumerate(FeedbackSource)}
        features.append(source_map.get(signal.source, 0) / len(FeedbackSource))
        comp_map = {comp: i for i, comp in enumerate(ComponentType)}
        features.append(comp_map.get(signal.component_type, 0) / len(ComponentType))
        features.append(signal.confidence)
        hour = signal.timestamp % 86400 / 86400
        features.append(hour)
        while len(features) < 10:
            features.append(0.0)
        return np.array(features[:10], dtype=np.float32)

    async def _trigger_memory_consolidation(self) -> None:
        """Trigger memory consolidation via RAG consolidator."""
        if not self._rag_consolidator:
            try:
                from platform.rl.rag.rag_quality_feedback import get_rag_feedback

                self._rag_feedback = get_rag_feedback()
                self._rag_consolidator = getattr(self._rag_feedback, "consolidator", None)
            except Exception as e:
                logger.warning("rag_consolidator_load_failed", error=str(e))
                return
        if self._rag_consolidator:
            try:
                await self._rag_consolidator.consolidate()
                logger.info("memory_consolidation_triggered")
            except Exception as e:
                logger.exception("memory_consolidation_error", error=str(e))

    async def _check_component_health(self) -> None:
        """Check health of all components and auto-disable unhealthy ones."""
        for component_type, queue in self._feedback_queues.items():
            queue_utilization = len(queue) / self.max_queue_size if self.max_queue_size > 0 else 0
            avg_reward = self._metrics.average_reward_by_component.get(component_type.value, 0.5)
            health_score = (1.0 - queue_utilization) * avg_reward
            self._component_health[component_type.value] = {
                "health_score": health_score,
                "queue_utilization": queue_utilization,
                "average_reward": avg_reward,
                "last_checked": time.time(),
            }
            if health_score < 0.2:
                self._disabled_components.add(component_type.value)
                logger.warning("component_auto_disabled", component=component_type.value, health_score=health_score)
            elif health_score > 0.5 and component_type.value in self._disabled_components:
                self._disabled_components.remove(component_type.value)
                logger.info("component_re_enabled", component=component_type.value, health_score=health_score)

    async def _check_rag_consolidation_trigger(self) -> bool:
        """Check if RAG consolidation should be triggered based on quality signals."""
        if not self._rag_feedback:
            try:
                from platform.rl.rag.rag_quality_feedback import get_rag_feedback

                self._rag_feedback = get_rag_feedback()
            except Exception as e:
                logger.warning("rag_feedback_load_failed", error=str(e))
                return False
        if self._rag_feedback:
            try:
                should_trigger = await self._rag_feedback.should_consolidate()
                return should_trigger
            except Exception as e:
                logger.exception("rag_consolidation_check_error", error=str(e))
        return False

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics.

        Returns:
            Dictionary with metrics including:
                - signals_processed: Total signals processed
                - signals_by_source: Breakdown by feedback source
                - signals_by_component: Breakdown by component type
                - consolidations_triggered: Number of consolidations
                - health_checks_performed: Number of health checks
                - uptime_seconds: Orchestrator uptime
        """
        self._metrics.uptime_seconds = time.time() - self._start_time
        return {
            "signals_processed": self._metrics.signals_processed,
            "signals_by_source": {source.value: count for source, count in self._metrics.signals_by_source.items()},
            "signals_by_component": {comp.value: count for comp, count in self._metrics.signals_by_component.items()},
            "consolidations_triggered": self._metrics.consolidations_triggered,
            "health_checks_performed": self._metrics.health_checks_performed,
            "uptime_seconds": self._metrics.uptime_seconds,
            "last_consolidation": self._metrics.last_consolidation,
        }

    def get_component_health_report(self) -> dict[str, Any]:
        """Get component health status.

        Returns:
            Dictionary with health metrics for each component type
        """
        return {
            "components": self._component_health,
            "disabled": list(self._disabled_components),
            "overall_health": sum(comp["health_score"] for comp in self._component_health.values())
            / len(self._component_health)
            if self._component_health
            else 1.0,
        }

    async def stop(self) -> StepResult:
        """Stop all background processing tasks.

        Returns:
            StepResult indicating shutdown status
        """
        logger.info("stopping_unified_feedback_orchestrator")
        self._shutdown_event.set()
        await self.cleanup()
        logger.info(
            "unified_feedback_orchestrator_stopped",
            signals_processed=self._metrics.signals_processed,
            uptime_seconds=time.time() - self._start_time,
        )
        return StepResult.ok(result={"status": "stopped", "signals_processed": self._metrics.signals_processed})

    async def cleanup(self) -> None:
        """Clean shutdown of orchestrator and background tasks.

        Overrides BaseOrchestrator.cleanup() to add shutdown event signaling.
        """
        self._shutdown_event.set()
        await super().cleanup()


_orchestrator_instance: UnifiedFeedbackOrchestrator | None = None


def get_unified_feedback_orchestrator() -> UnifiedFeedbackOrchestrator:
    """Get global unified feedback orchestrator instance.

    Maintains backward compatibility with old singleton pattern.
    Creates instance on first call and returns same instance thereafter.

    Returns:
        Global UnifiedFeedbackOrchestrator instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = UnifiedFeedbackOrchestrator()
        logger.info("unified_feedback_orchestrator_created")
    return _orchestrator_instance


def set_unified_feedback_orchestrator(orchestrator: UnifiedFeedbackOrchestrator) -> None:
    """Set global unified feedback orchestrator instance.

    Allows external code to override the singleton instance.

    Args:
        orchestrator: Orchestrator instance to use as global singleton
    """
    global _orchestrator_instance
    _orchestrator_instance = orchestrator
    logger.info("unified_feedback_orchestrator_overridden")


get_orchestrator = get_unified_feedback_orchestrator
set_orchestrator = set_unified_feedback_orchestrator
