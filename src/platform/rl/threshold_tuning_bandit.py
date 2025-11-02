"""Threshold Tuning Bandit - Adaptive quality threshold optimization.

Integrates existing rl_quality_threshold_optimizer.py into unified AI/ML/RL system.
Uses contextual bandit to dynamically adjust quality thresholds per content-type
to balance cost savings with quality retention.

This module provides a bridge between the existing QualityThresholdOptimizer
and the unified feedback orchestrator, adding:
- Context-aware threshold selection
- Integration with feedback loops
- Unified metrics and observability
- Multi-objective optimization (cost vs quality)
"""

from __future__ import annotations

import contextlib
import logging
from collections import deque
from dataclasses import dataclass
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult


logger = logging.getLogger(__name__)


@dataclass
class ThresholdSelection:
    """Result of threshold selection."""

    word_count_min: int
    sentence_count_min: int
    coherence_min: float
    overall_quality_min: float
    config_id: str
    confidence: float
    reasoning: str


@dataclass
class ThresholdFeedback:
    """Feedback for threshold decision."""

    config_id: str
    content_type: str
    bypass_decision: bool
    cost_saved_usd: float
    quality_score: float
    processing_time_saved_s: float
    timestamp: float


class ThresholdTuningBandit:
    """Contextual bandit for adaptive quality threshold tuning.

    Integrates with UnifiedFeedbackOrchestrator to learn optimal quality thresholds
    per content-type, balancing cost savings with quality retention.
    """

    def __init__(self):
        """Initialize threshold tuning bandit."""
        # Import optimizer lazily to avoid circular dependencies
        self.optimizer = None
        self._feedback_queue: deque[ThresholdFeedback] = deque(maxlen=1000)

        # Statistics
        self.selections_count = 0
        self.feedback_count = 0
        self.total_cost_saved = 0.0
        self.total_time_saved = 0.0

        # Per-content-type tracking
        self.content_type_stats: dict[str, dict[str, Any]] = {}

        logger.info("ThresholdTuningBandit initialized")

    def _get_optimizer(self):
        """Lazy load the optimizer."""
        if self.optimizer is None:
            try:
                from ultimate_discord_intelligence_bot.tools.analysis.rl_quality_threshold_optimizer import (
                    get_quality_threshold_optimizer,
                )

                self.optimizer = get_quality_threshold_optimizer()
                logger.info("Loaded QualityThresholdOptimizer")
            except ImportError as e:
                logger.warning(f"Failed to load QualityThresholdOptimizer: {e}")
        return self.optimizer

    async def select_thresholds(
        self,
        content_type: str = "general",
        context: dict[str, Any] | None = None,
        optimization_target: str = "balanced",  # balanced, cost, quality
    ) -> StepResult:
        """Select optimal quality thresholds for content type.

        Args:
            content_type: Type of content (video, podcast, article, etc.)
            context: Additional context for selection
            optimization_target: Optimization goal (balanced, cost, quality)

        Returns:
            StepResult with ThresholdSelection data
        """
        try:
            optimizer = self._get_optimizer()
            if optimizer is None:
                # Fallback to defaults if optimizer unavailable
                return self._get_default_thresholds(content_type)

            # Extract context for optimizer
            ctx = context or {}
            estimated_tokens = ctx.get("estimated_tokens", 0)
            recent_bypass_rate = self._get_recent_bypass_rate(content_type)
            budget_pressure = self._calculate_budget_pressure(ctx)

            # Build optimization context
            from ultimate_discord_intelligence_bot.tools.analysis.rl_quality_threshold_optimizer import (
                OptimizationContext,
            )

            opt_context = OptimizationContext(
                content_type=content_type,
                tenant=ctx.get("tenant", "default"),
                estimated_tokens=estimated_tokens,
                recent_bypass_rate=recent_bypass_rate,
                budget_pressure=budget_pressure,
            )

            # Select thresholds using optimizer
            threshold_config = optimizer.select_thresholds(
                content_type=content_type,
                tenant=ctx.get("tenant", "default"),
                context=opt_context,
            )

            self.selections_count += 1

            # Calculate confidence based on optimizer stats
            confidence = self._calculate_confidence(optimizer, content_type, threshold_config.config_id)

            # Build reasoning
            reasoning = self._build_reasoning(
                content_type, threshold_config, optimization_target, recent_bypass_rate, budget_pressure
            )

            selection = ThresholdSelection(
                word_count_min=threshold_config.word_count_min,
                sentence_count_min=threshold_config.sentence_count_min,
                coherence_min=threshold_config.coherence_min,
                overall_quality_min=threshold_config.overall_quality_min,
                config_id=threshold_config.config_id,
                confidence=confidence,
                reasoning=reasoning,
            )

            return StepResult.ok(data=selection)

        except Exception as e:
            logger.error(f"Threshold selection failed: {e}")
            return self._get_default_thresholds(content_type)

    def submit_threshold_feedback(
        self,
        config_id: str,
        content_type: str,
        bypass_decision: bool,
        cost_saved_usd: float,
        quality_score: float,
        processing_time_saved_s: float = 0.0,
    ) -> None:
        """Submit feedback for threshold decision.

        Args:
            config_id: ID of threshold configuration used
            content_type: Type of content processed
            bypass_decision: Whether content was bypassed (True) or fully processed (False)
            cost_saved_usd: Estimated cost savings in USD
            quality_score: Quality score of content (0.0-1.0)
            processing_time_saved_s: Time saved in seconds
        """
        import time

        feedback = ThresholdFeedback(
            config_id=config_id,
            content_type=content_type,
            bypass_decision=bypass_decision,
            cost_saved_usd=cost_saved_usd,
            quality_score=quality_score,
            processing_time_saved_s=processing_time_saved_s,
            timestamp=time.time(),
        )

        self._feedback_queue.append(feedback)
        self.feedback_count += 1

        # Update statistics
        if bypass_decision:
            self.total_cost_saved += cost_saved_usd
            self.total_time_saved += processing_time_saved_s

        # Update content-type stats
        if content_type not in self.content_type_stats:
            self.content_type_stats[content_type] = {
                "bypass_count": 0,
                "process_count": 0,
                "total_cost_saved": 0.0,
                "total_time_saved": 0.0,
                "avg_quality": 0.0,
            }

        stats = self.content_type_stats[content_type]
        if bypass_decision:
            stats["bypass_count"] += 1
            stats["total_cost_saved"] += cost_saved_usd
            stats["total_time_saved"] += processing_time_saved_s
        else:
            stats["process_count"] += 1

        # Update average quality (EMA)
        alpha = 0.2
        stats["avg_quality"] = alpha * quality_score + (1 - alpha) * stats["avg_quality"]

    def process_feedback_batch(self, batch_size: int = 20) -> None:
        """Process batch of feedback to update optimizer.

        Args:
            batch_size: Maximum number of feedback items to process
        """
        optimizer = self._get_optimizer()
        if optimizer is None:
            return

        processed = 0
        while self._feedback_queue and processed < batch_size:
            feedback = self._feedback_queue.popleft()

            # Update optimizer
            try:
                optimizer.update_reward(
                    content_type=feedback.content_type,
                    tenant="default",  # TODO: Extract from context
                    bypass_decision=feedback.bypass_decision,
                    cost_saved_usd=feedback.cost_saved_usd,
                    quality_score=feedback.quality_score,
                    config_id=feedback.config_id,
                )
                processed += 1
            except Exception as e:
                logger.error(f"Failed to update optimizer with feedback: {e}")

        if processed > 0:
            logger.debug(f"Processed {processed} threshold feedback items")

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics.

        Returns:
            Dictionary of metrics
        """
        optimizer = self._get_optimizer()

        metrics = {
            "selections_count": self.selections_count,
            "feedback_count": self.feedback_count,
            "total_cost_saved_usd": self.total_cost_saved,
            "total_time_saved_s": self.total_time_saved,
            "feedback_queue_size": len(self._feedback_queue),
            "content_type_stats": self.content_type_stats.copy(),
        }

        # Add optimizer metrics if available
        if optimizer:
            with contextlib.suppress(Exception):
                metrics["optimizer_state"] = {
                    "exploration_rate": optimizer.exploration_rate,
                    "total_pulls": sum(
                        arm.pulls for arms in optimizer.arms_by_context.values() for arm in arms.values()
                    ),
                }

        return metrics

    def _get_default_thresholds(self, content_type: str) -> StepResult:
        """Get default thresholds as fallback."""
        selection = ThresholdSelection(
            word_count_min=500,
            sentence_count_min=10,
            coherence_min=0.6,
            overall_quality_min=0.65,
            config_id="default",
            confidence=0.5,
            reasoning=f"Using default thresholds for {content_type} (optimizer unavailable)",
        )
        return StepResult.ok(data=selection)

    def _get_recent_bypass_rate(self, content_type: str) -> float:
        """Calculate recent bypass rate for content type."""
        if content_type not in self.content_type_stats:
            return 0.5  # Default

        stats = self.content_type_stats[content_type]
        total = stats["bypass_count"] + stats["process_count"]
        if total == 0:
            return 0.5

        return stats["bypass_count"] / total

    def _calculate_budget_pressure(self, context: dict[str, Any]) -> float:
        """Calculate budget pressure from context.

        Returns value between 0.0 (no pressure) and 1.0 (high pressure).
        """
        # Extract budget indicators from context
        budget_limit = context.get("budget_limit", 0)
        budget_used = context.get("budget_used", 0)

        if budget_limit == 0:
            return 0.0

        utilization = budget_used / budget_limit
        # Pressure increases as we approach limit
        if utilization < 0.7:
            return 0.0
        elif utilization < 0.85:
            return 0.3
        elif utilization < 0.95:
            return 0.6
        else:
            return 0.9

    def _calculate_confidence(self, optimizer, content_type: str, config_id: str) -> float:
        """Calculate confidence in threshold selection."""
        try:
            context_key = optimizer._get_context_key(content_type, "default")
            if context_key in optimizer.arms_by_context:
                arms = optimizer.arms_by_context[context_key]
                if config_id in arms:
                    arm = arms[config_id]
                    # Confidence based on number of pulls and performance
                    sample_confidence = min(arm.pulls / 50.0, 1.0)  # More samples = more confidence
                    performance_confidence = max(arm.mean_reward, 0.0)
                    return 0.6 * sample_confidence + 0.4 * performance_confidence

            return 0.5  # Default confidence for unexplored arms

        except Exception:
            return 0.5

    def _build_reasoning(
        self,
        content_type: str,
        threshold_config,
        optimization_target: str,
        recent_bypass_rate: float,
        budget_pressure: float,
    ) -> str:
        """Build human-readable reasoning for threshold selection."""
        parts = [f"Selected '{threshold_config.config_id}' config for {content_type}"]

        if optimization_target == "cost":
            parts.append("optimizing for cost savings")
        elif optimization_target == "quality":
            parts.append("optimizing for quality retention")
        else:
            parts.append("balancing cost and quality")

        if budget_pressure > 0.6:
            parts.append(f"(high budget pressure: {budget_pressure:.1%})")

        if recent_bypass_rate > 0.0:
            parts.append(f"recent bypass rate: {recent_bypass_rate:.1%}")

        return ", ".join(parts)


# Global singleton instance
_threshold_bandit_instance: ThresholdTuningBandit | None = None
_threshold_bandit_lock = None


def get_threshold_bandit() -> ThresholdTuningBandit:
    """Get or create the global threshold bandit instance."""
    global _threshold_bandit_instance, _threshold_bandit_lock

    if _threshold_bandit_lock is None:
        import threading

        _threshold_bandit_lock = threading.Lock()

    if _threshold_bandit_instance is None:
        with _threshold_bandit_lock:
            if _threshold_bandit_instance is None:
                _threshold_bandit_instance = ThresholdTuningBandit()

    return _threshold_bandit_instance


__all__ = [
    "ThresholdFeedback",
    "ThresholdSelection",
    "ThresholdTuningBandit",
    "get_threshold_bandit",
]
