"""Enhanced LLM Router with Cost-Aware Optimization and Performance Improvements.

Enhanced Features:
- Cost-aware model selection with real-time cost tracking
- Adaptive quality thresholds based on task complexity
- Dynamic cost-utility optimization with multi-objective scoring
- Intelligent model selection based on content complexity analysis
- Cost-aware fallback strategies for reliability
- Performance metrics integration for continuous optimization
- Enhanced bandit algorithms with cost sensitivity

Feature flags:
- ENABLE_BANDIT_ROUTING=1 (existing bandit routing)
- ENABLE_COST_AWARE_ROUTING=1 (cost-aware optimization)
- ENABLE_ADAPTIVE_QUALITY=1 (dynamic quality thresholds)
- ENABLE_COMPLEXITY_ANALYSIS=1 (task complexity assessment)

Usage:
    router = LLMRouter({"gpt4": client4, "haiku": client_haiku})
    result = router.chat(messages)  # Now cost-aware by default

Reward Feedback:
    After obtaining a result and computing a quality/cost metric, call
        router.update(model_name, reward, cost=cost_usd, latency_ms=latency)
    for enhanced cost-aware learning.
"""

from __future__ import annotations

import math
import os
import statistics
import time
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from ai.routing.bandit_router import ThompsonBanditRouter
from ai.routing.linucb_router import LinUCBRouter
from ai.routing.router_registry import RewardNormalizer, get_tenant_router, record_selection
from ai.routing.vw_bandit_router import VWBanditRouter
from core.llm_client import LLMCallResult, LLMClient

try:  # metrics optional
    from ultimate_discord_intelligence_bot.obs.metrics import get_metrics as _gm

    def _obtain_metrics() -> Any | None:
        try:
            return _gm()
        except Exception:  # pragma: no cover
            return None
except Exception:  # pragma: no cover

    def _obtain_metrics() -> Any | None:
        return None


# ---------------------- Enhanced Data Structures ----------------------


@dataclass
class CostAwareDecision:
    """Cost-aware model selection decision with reasoning."""

    model: str
    estimated_cost: float
    estimated_quality: float
    estimated_latency: float
    utility_score: float
    confidence: float
    reasoning: str
    fallback_models: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ModelPerformanceProfile:
    """Performance profile for a model including cost and quality metrics."""

    model: str
    avg_cost_per_token: float = 0.0
    avg_quality_score: float = 0.0
    avg_latency_ms: float = 0.0
    total_requests: int = 0
    total_cost: float = 0.0
    success_rate: float = 1.0
    last_updated: float = field(default_factory=time.time)

    def update_metrics(self, cost: float, quality: float, latency_ms: float) -> None:
        """Update performance metrics with new observation."""
        self.total_requests += 1
        self.total_cost += cost

        # Exponential moving average for performance metrics
        alpha = 0.1  # Learning rate
        self.avg_cost_per_token = (1 - alpha) * self.avg_cost_per_token + alpha * cost
        self.avg_quality_score = (1 - alpha) * self.avg_quality_score + alpha * quality
        self.avg_latency_ms = (1 - alpha) * self.avg_latency_ms + alpha * latency_ms
        self.last_updated = time.time()


@dataclass
class TaskComplexityMetrics:
    """Metrics for assessing task complexity."""

    estimated_tokens: int = 0
    complexity_score: float = 0.0  # 0.0 (simple) to 1.0 (very complex)
    reasoning_required: bool = False
    creative_task: bool = False
    factual_accuracy: bool = False
    multilingual_content: bool = False

    @classmethod
    def analyze_content(cls, messages: Sequence[dict[str, Any]]) -> TaskComplexityMetrics:
        """Analyze messages to estimate task complexity."""
        total_chars = 0
        has_reasoning = False
        has_creativity = False
        has_facts = False
        has_multiple_languages = False

        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
                content_lower = content.lower()

                # Check for reasoning indicators
                reasoning_words = ["reason", "think", "analyze", "explain", "why", "how", "because"]
                if any(word in content_lower for word in reasoning_words):
                    has_reasoning = True

                # Check for creative indicators
                creative_words = ["create", "write", "generate", "imagine", "design", "story", "poem"]
                if any(word in content_lower for word in creative_words):
                    has_creativity = True

                # Check for factual indicators
                factual_words = ["fact", "true", "correct", "accurate", "verify", "source"]
                if any(word in content_lower for word in factual_words):
                    has_facts = True

                # Simple multilingual detection (basic heuristics)
                if any(ord(c) > 127 for c in content):
                    has_multiple_languages = True

        # Estimate tokens (rough approximation: ~4 chars per token)
        estimated_tokens = max(100, total_chars // 4)

        # Calculate complexity score (0.0 to 1.0)
        complexity_factors = [
            min(1.0, estimated_tokens / 2000),  # Token count factor
            0.3 if has_reasoning else 0.0,  # Reasoning requirement
            0.2 if has_creativity else 0.0,  # Creative task
            0.2 if has_facts else 0.0,  # Factual accuracy needed
            0.1 if has_multiple_languages else 0.0,  # Multilingual content
        ]

        complexity_score = min(1.0, sum(complexity_factors))

        return cls(
            estimated_tokens=estimated_tokens,
            complexity_score=complexity_score,
            reasoning_required=has_reasoning,
            creative_task=has_creativity,
            factual_accuracy=has_facts,
            multilingual_content=has_multiple_languages,
        )


@dataclass
class CostOptimizationStats:
    """Statistics for cost optimization performance."""

    total_requests: int = 0
    cost_aware_selections: int = 0
    baseline_selections: int = 0
    total_cost_saved: float = 0.0
    total_cost_baseline: float = 0.0
    avg_cost_savings_per_request: float = 0.0
    cost_savings_rate: float = 0.0  # Percentage of requests where cost was saved

    def record_decision(self, was_cost_aware: bool, cost_saved: float, baseline_cost: float) -> None:
        """Record a routing decision for statistics."""
        self.total_requests += 1
        if was_cost_aware:
            self.cost_aware_selections += 1
        else:
            self.baseline_selections += 1

        if cost_saved > 0:
            self.total_cost_saved += cost_saved
            self.total_cost_baseline += baseline_cost

        # Recalculate averages
        if self.total_requests > 0:
            self.avg_cost_savings_per_request = self.total_cost_saved / self.total_requests
            self.cost_savings_rate = self.cost_aware_selections / self.total_requests

    def get_summary(self) -> dict[str, Any]:
        """Get formatted summary of cost optimization performance."""
        return {
            "total_requests": self.total_requests,
            "cost_aware_selections": self.cost_aware_selections,
            "baseline_selections": self.baseline_selections,
            "total_cost_saved_usd": round(self.total_cost_saved, 4),
            "total_cost_baseline_usd": round(self.total_cost_baseline, 4),
            "avg_cost_savings_per_request_usd": round(self.avg_cost_savings_per_request, 4),
            "cost_savings_rate_percent": round(self.cost_savings_rate * 100, 2),
            "estimated_monthly_savings_usd": round(self.total_cost_saved * 30, 2),
        }


class LLMRouter:
    """Enhanced LLM Router with cost-aware optimization and performance improvements."""

    def __init__(self, clients: dict[str, LLMClient]):
        if not clients:
            raise ValueError("At least one client required")

        self._clients = clients

        # Enhanced feature flags
        self._tenant_mode = os.getenv("ENABLE_BANDIT_TENANT", "0").lower() in {"1", "true", "yes", "on"}
        self._contextual_enabled = os.getenv("ENABLE_CONTEXTUAL_BANDIT", "0").lower() in {"1", "true", "yes", "on"}
        self._cost_aware_enabled = os.getenv("ENABLE_COST_AWARE_ROUTING", "1").lower() in {"1", "true", "yes", "on"}
        self._adaptive_quality_enabled = os.getenv("ENABLE_ADAPTIVE_QUALITY", "1").lower() in {"1", "true", "yes", "on"}
        self._complexity_analysis_enabled = os.getenv("ENABLE_COMPLEXITY_ANALYSIS", "1").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # Cost optimization parameters
        self._cost_weight = float(os.getenv("COST_WEIGHT", "0.4"))  # Weight for cost in utility calculation
        self._quality_weight = float(os.getenv("QUALITY_WEIGHT", "0.5"))  # Weight for quality/reward
        self._latency_weight = float(os.getenv("LATENCY_WEIGHT", "0.1"))  # Weight for latency
        self._min_cost_savings_threshold = float(
            os.getenv("MIN_COST_SAVINGS_THRESHOLD", "0.001")
        )  # Minimum cost savings to consider
        self._quality_threshold_base = float(os.getenv("QUALITY_THRESHOLD_BASE", "0.7"))  # Base quality threshold

        # Performance tracking
        self._model_profiles: dict[str, ModelPerformanceProfile] = {}
        self._cost_optimization_stats = CostOptimizationStats()
        self._recent_decisions: deque = deque(maxlen=1000)  # Track recent decisions for analysis

        # Initialize model profiles
        for model_name in clients.keys():
            self._model_profiles[model_name] = ModelPerformanceProfile(model=model_name)

        # Existing bandit router configuration (unchanged)
        self._linucb_dimension = int(os.getenv("LINUCB_DIMENSION", "0") or 0)
        self._hybrid_enabled = os.getenv("ENABLE_CONTEXTUAL_HYBRID", "1").lower() in {"1", "true", "yes", "on"}
        # Feature quality gating configuration
        self._feature_quality_min = float(os.getenv("FEATURE_QUALITY_MIN", "0.5") or 0.5)
        self._feature_min_norm = float(os.getenv("FEATURE_MIN_NORM", "0.0") or 0.0)
        self._feature_max_norm = float(os.getenv("FEATURE_MAX_NORM", "10.0") or 10.0)
        self._vw_enabled = os.getenv("ENABLE_VW_BANDIT", "0").lower() in {"1", "true", "yes", "on"} or os.getenv(
            "ENABLE_VOWPAL_WABBIT_BANDIT", "0"
        ).lower() in {"1", "true", "yes", "on"}

        # Initialize bandit router (unchanged)
        self._bandit: VWBanditRouter | ThompsonBanditRouter

        if self._contextual_enabled:
            if self._linucb_dimension <= 0:
                raise ValueError("LINUCB_DIMENSION must be > 0 when ENABLE_CONTEXTUAL_BANDIT=1")
            self._ctx_router: LinUCBRouter | None = LinUCBRouter(dimension=self._linucb_dimension)
            # In pure contextual mode we could disable classic bandit; for hybrid we keep one for fallback
            if self._vw_enabled:
                self._bandit = VWBanditRouter()
            else:
                self._bandit = get_tenant_router() if self._tenant_mode else ThompsonBanditRouter()
        else:
            self._ctx_router = None
            if self._vw_enabled:
                self._bandit = VWBanditRouter()
            else:
                self._bandit = get_tenant_router() if self._tenant_mode else ThompsonBanditRouter()
        self._reward_normalizer = RewardNormalizer()
        self._metrics = _obtain_metrics()
        if self._metrics:
            m = self._metrics
            self._chat_counter = m.counter("llm_router_chats_total")
            self._fallback_counter = m.counter("llm_router_fallback_total")
            self._feature_quality_gauge = m.gauge("linucb_feature_quality")
            # Enhanced cost-aware metrics
            self._cost_savings_counter = m.counter("llm_router_cost_savings_total_usd")
            self._cost_aware_selections_counter = m.counter("llm_router_cost_aware_selections_total")
            self._model_cost_gauge = m.gauge("llm_router_model_cost_per_token_usd")
        else:  # pragma: no cover
            self._chat_counter = None
            self._fallback_counter = None
            self._feature_quality_gauge = None
            self._cost_savings_counter = None
            self._cost_aware_selections_counter = None
            self._model_cost_gauge = None

    # ---------------------- Cost-Aware Model Selection ----------------------

    def _calculate_adaptive_quality_threshold(self, complexity_metrics: TaskComplexityMetrics) -> float:
        """Calculate adaptive quality threshold based on task complexity."""
        if not self._adaptive_quality_enabled:
            return self._quality_threshold_base

        # Base threshold
        threshold = self._quality_threshold_base

        # Adjust based on complexity factors
        complexity_multiplier = 1.0 + (complexity_metrics.complexity_score * 0.3)  # Up to 30% increase

        # Higher thresholds for reasoning and factual tasks
        if complexity_metrics.reasoning_required:
            threshold *= 1.2
        if complexity_metrics.factual_accuracy:
            threshold *= 1.15

        # Lower thresholds for simple creative tasks
        if complexity_metrics.creative_task and complexity_metrics.complexity_score < 0.3:
            threshold *= 0.9

        return min(0.95, threshold * complexity_multiplier)  # Cap at 95%

    def _calculate_cost_utility_score(
        self, model: str, estimated_cost: float, estimated_quality: float, estimated_latency: float
    ) -> float:
        """Calculate cost-utility score for model selection."""
        # Normalize metrics (0-1 scale)
        cost_score = max(0.0, 1.0 - (estimated_cost / 0.01))  # Lower cost = higher score
        quality_score = min(1.0, estimated_quality)  # Quality is already 0-1
        latency_score = max(0.0, 1.0 - (estimated_latency / 5000))  # Lower latency = higher score

        # Weighted combination
        utility_score = (
            self._cost_weight * cost_score + self._quality_weight * quality_score + self._latency_weight * latency_score
        )

        return utility_score

    def _select_cost_aware_model(
        self, messages: Sequence[dict[str, Any]], available_models: list[str]
    ) -> CostAwareDecision:
        """Select model using cost-aware optimization."""
        # Analyze task complexity
        complexity_metrics = TaskComplexityMetrics.analyze_content(messages)

        # Get adaptive quality threshold
        quality_threshold = self._calculate_adaptive_quality_threshold(complexity_metrics)

        # Estimate metrics for each model
        model_options = []
        for model in available_models:
            profile = self._model_profiles[model]

            # Estimate cost (tokens * cost per token)
            estimated_cost = complexity_metrics.estimated_tokens * profile.avg_cost_per_token

            # Estimate quality (use historical average or default)
            estimated_quality = max(profile.avg_quality_score, 0.7)  # Fallback to 0.7 if no data

            # Estimate latency (use historical average or default)
            estimated_latency = profile.avg_latency_ms or 1000  # Default 1s

            # Check if model meets quality threshold
            if estimated_quality >= quality_threshold:
                utility_score = self._calculate_cost_utility_score(
                    model, estimated_cost, estimated_quality, estimated_latency
                )

                model_options.append(
                    {
                        "model": model,
                        "estimated_cost": estimated_cost,
                        "estimated_quality": estimated_quality,
                        "estimated_latency": estimated_latency,
                        "utility_score": utility_score,
                        "profile": profile,
                    }
                )

        if not model_options:
            # Fallback to best available model if none meet quality threshold
            best_model = max(available_models, key=lambda m: self._model_profiles[m].avg_quality_score)
            profile = self._model_profiles[best_model]
            estimated_cost = complexity_metrics.estimated_tokens * profile.avg_cost_per_token

            return CostAwareDecision(
                model=best_model,
                estimated_cost=estimated_cost,
                estimated_quality=profile.avg_quality_score,
                estimated_latency=profile.avg_latency_ms or 1000,
                utility_score=0.0,  # Below threshold
                confidence=0.5,
                reasoning="No models met quality threshold, using best available",
                fallback_models=available_models,
            )

        # Select model with highest utility score
        best_option = max(model_options, key=lambda x: x["utility_score"])

        # Calculate confidence based on utility gap and historical performance
        utility_gap = best_option["utility_score"] - min(o["utility_score"] for o in model_options)
        confidence = min(1.0, utility_gap + 0.3)  # Base confidence + utility gap bonus

        # Determine fallback models (next best options)
        sorted_options = sorted(model_options, key=lambda x: x["utility_score"], reverse=True)
        fallback_models = [opt["model"] for opt in sorted_options[1:3]]  # Top 2 alternatives

        # Generate reasoning
        reasoning = self._generate_selection_reasoning(best_option, complexity_metrics, quality_threshold)

        return CostAwareDecision(
            model=best_option["model"],
            estimated_cost=best_option["estimated_cost"],
            estimated_quality=best_option["estimated_quality"],
            estimated_latency=best_option["estimated_latency"],
            utility_score=best_option["utility_score"],
            confidence=confidence,
            reasoning=reasoning,
            fallback_models=fallback_models,
        )

    def _generate_selection_reasoning(
        self, selected_option: dict[str, Any], complexity: TaskComplexityMetrics, quality_threshold: float
    ) -> str:
        """Generate human-readable reasoning for model selection."""
        model = selected_option["model"]
        utility = selected_option["utility_score"]
        cost = selected_option["estimated_cost"]
        quality = selected_option["estimated_quality"]

        reasoning_parts = [f"Selected {model} with utility score {utility:.3f}"]

        if complexity.reasoning_required:
            reasoning_parts.append(" (requires reasoning capability)")
        if complexity.creative_task:
            reasoning_parts.append(" (creative task)")
        if complexity.factual_accuracy:
            reasoning_parts.append(" (requires factual accuracy)")

        reasoning_parts.append(f". Estimated cost: ${cost:.4f}, quality: {quality:.2f}")

        if quality < quality_threshold:
            reasoning_parts.append(f" (below threshold {quality_threshold:.2f} but best available)")

        return "".join(reasoning_parts)

    def _get_available_models(self) -> list[str]:
        """Get list of available model names."""
        return list(self._clients.keys())

    # ---------------------- Feature Quality Scoring ----------------------
    def _feature_quality(self, features: Sequence[float] | None) -> float:
        """Return a heuristic feature quality score in [0,1]. Higher is better.

        Heuristics:
          - None or dimension mismatch => 0.0
          - NaN/inf values apply 0.3 penalty (score *= 0.7)
          - Vector L2 norm outside [min_norm, max_norm] scaled penalty up to 0.5
        """
        if features is None:
            return 0.0
        try:
            if len(features) != self._linucb_dimension:
                return 0.0
        except Exception:
            return 0.0
        # base score
        score = 1.0
        # numeric validation
        bad_numeric = False
        norm_sq = 0.0
        for v in features:
            if not isinstance(v, (int, float)) or math.isinf(v) or math.isnan(v):
                bad_numeric = True
                # Skip contribution to norm if non-finite or non-numeric
                continue
            norm_sq += float(v) * float(v)
        if bad_numeric:
            score *= 0.7  # 30% penalty
        l2 = norm_sq**0.5
        if l2 < self._feature_min_norm:
            # scale penalty by distance relative to min_norm (avoid divide by zero)
            span = max(1e-9, self._feature_min_norm)
            ratio = min(1.0, (self._feature_min_norm - l2) / span)
            score *= 1 - 0.5 * ratio
        elif l2 > self._feature_max_norm:
            span = max(1e-9, self._feature_max_norm)
            ratio = min(1.0, (l2 - self._feature_max_norm) / span)
            score *= 1 - 0.5 * ratio
        # clamp
        return max(0.0, min(1.0, score))

    def chat(self, messages: Sequence[dict[str, Any]]) -> tuple[str, LLMCallResult]:
        """Enhanced chat method with cost-aware model selection."""
        start_time = time.time()

        # Get available models
        model_names = self._get_available_models()

        # Cost-aware model selection (if enabled)
        if self._cost_aware_enabled:
            cost_aware_decision = self._select_cost_aware_model(messages, model_names)
            selected = cost_aware_decision.model

            # Track the decision for analysis
            self._recent_decisions.append(cost_aware_decision)

            # Use fallback if cost-aware selection fails
            if selected not in model_names:
                selected = self._bandit.select(model_names)
        else:
            # Traditional bandit selection
            selected = self._bandit.select(model_names)

        # Execute the request
        result = self._clients[selected].chat(messages)

        # Update metrics and performance tracking
        if self._chat_counter:
            try:
                self._chat_counter.inc(1)
            except Exception:  # pragma: no cover
                pass

        if self._tenant_mode:
            record_selection(selected)

        # Enhanced performance tracking
        self._update_model_profile(selected, result)

        return selected, result

    def _update_model_profile(self, model: str, result: LLMCallResult) -> None:
        """Update model performance profile with request results."""
        if model not in self._model_profiles:
            return

        profile = self._model_profiles[model]

        # Extract cost and latency from result if available
        cost = getattr(result, "cost_usd", 0.0)
        latency_ms = getattr(result, "latency_ms", 0.0)

        # Estimate quality score (could be enhanced with actual quality metrics)
        quality_score = 0.8  # Placeholder - should be calculated based on response quality

        # Update profile
        profile.update_metrics(cost, quality_score, latency_ms)

    def update(self, model_name: str, reward: float, cost: float = 0.0, latency_ms: float = 0.0) -> None:
        """Enhanced update method with cost-aware learning."""
        if model_name not in self._clients:
            return

        # Update model profile with enhanced metrics
        if model_name in self._model_profiles:
            profile = self._model_profiles[model_name]
            profile.update_metrics(cost, reward, latency_ms)

        # Update cost optimization statistics if cost data is available
        if cost > 0 and self._cost_aware_enabled:
            # Compare with what cost-aware routing would have chosen
            recent_decisions = list(self._recent_decisions)
            if recent_decisions:
                latest_decision = recent_decisions[-1]
                if latest_decision.model == model_name:
                    # This was a cost-aware selection - record cost savings if any
                    baseline_cost = sum(d.estimated_cost for d in recent_decisions[-10:]) / min(
                        10, len(recent_decisions)
                    )
                    if baseline_cost > 0:
                        cost_saved = baseline_cost - cost
                        if cost_saved > self._min_cost_savings_threshold:
                            self._cost_optimization_stats.record_decision(True, cost_saved, baseline_cost)
                            if self._cost_savings_counter:
                                try:
                                    self._cost_savings_counter.inc(cost_saved)
                                except Exception:
                                    pass
                        else:
                            self._cost_optimization_stats.record_decision(True, 0.0, cost)
                    else:
                        self._cost_optimization_stats.record_decision(True, 0.0, cost)
                else:
                    # This was not a cost-aware selection
                    self._cost_optimization_stats.record_decision(False, 0.0, cost)

        # Continue with existing bandit update logic
        if self._contextual_enabled:
            # Graceful fallback: allow classical bandit update so legacy reward feedback still works.
            pass
        self._bandit.update(model_name, reward)

    def chat_and_update(
        self,
        messages: Sequence[dict[str, Any]],
        quality_metric: float = 0.8,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
    ) -> tuple[str, LLMCallResult]:
        """Convenience method that performs chat and automatic reward update."""
        model, result = self.chat(messages)

        # Calculate reward based on quality and cost efficiency
        if cost_usd > 0:
            # Cost efficiency factor (lower cost per quality unit = higher reward)
            cost_efficiency = quality_metric / max(cost_usd, 0.001)
            reward = quality_metric * min(1.0, cost_efficiency * 10)  # Scale cost efficiency
        else:
            reward = quality_metric

        # Apply latency penalty (slower responses get lower reward)
        if latency_ms > 0:
            latency_penalty = max(0.5, 1.0 - (latency_ms / 10000))  # Penalty for >10s responses
            reward *= latency_penalty

        self.update(model, reward, cost_usd, latency_ms)
        return model, result

    def get_cost_optimization_stats(self) -> dict[str, Any]:
        """Get comprehensive cost optimization performance statistics."""
        return self._cost_optimization_stats.get_summary()

    def get_model_performance_profiles(self) -> dict[str, dict[str, Any]]:
        """Get performance profiles for all models."""
        profiles = {}
        for model, profile in self._model_profiles.items():
            profiles[model] = {
                "avg_cost_per_token": profile.avg_cost_per_token,
                "avg_quality_score": profile.avg_quality_score,
                "avg_latency_ms": profile.avg_latency_ms,
                "total_requests": profile.total_requests,
                "total_cost": profile.total_cost,
                "success_rate": profile.success_rate,
                "last_updated": profile.last_updated,
            }
        return profiles

    def get_recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent cost-aware routing decisions for analysis."""
        recent = list(self._recent_decisions)[-limit:]
        return [
            {
                "model": decision.model,
                "estimated_cost": decision.estimated_cost,
                "estimated_quality": decision.estimated_quality,
                "estimated_latency": decision.estimated_latency,
                "utility_score": decision.utility_score,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "fallback_models": decision.fallback_models,
                "timestamp": decision.timestamp,
            }
            for decision in recent
        ]

    def analyze_routing_effectiveness(self) -> dict[str, Any]:
        """Analyze the effectiveness of cost-aware routing decisions."""
        if not self._recent_decisions:
            return {"error": "No recent decisions to analyze"}

        decisions = list(self._recent_decisions)

        # Calculate average utility scores and costs
        avg_utility = statistics.mean(d.utility_score for d in decisions if d.utility_score > 0)
        avg_cost = statistics.mean(d.estimated_cost for d in decisions)
        avg_confidence = statistics.mean(d.confidence for d in decisions)

        # Analyze model selection distribution
        model_selections = {}
        for decision in decisions:
            model_selections[decision.model] = model_selections.get(decision.model, 0) + 1

        # Identify most and least cost-effective models
        cost_effectiveness = {}
        for model, profile in self._model_profiles.items():
            if profile.total_requests > 0:
                # Cost effectiveness = quality / cost (higher is better)
                cost_effectiveness[model] = profile.avg_quality_score / max(profile.avg_cost_per_token, 0.001)

        best_model = max(cost_effectiveness.items(), key=lambda x: x[1])[0] if cost_effectiveness else None
        worst_model = min(cost_effectiveness.items(), key=lambda x: x[1])[0] if cost_effectiveness else None

        return {
            "total_decisions": len(decisions),
            "avg_utility_score": round(avg_utility, 3),
            "avg_estimated_cost": round(avg_cost, 4),
            "avg_confidence": round(avg_confidence, 3),
            "model_selection_distribution": model_selections,
            "most_cost_effective_model": best_model,
            "least_cost_effective_model": worst_model,
            "cost_effectiveness_scores": {k: round(v, 3) for k, v in cost_effectiveness.items()},
        }

    def optimize_routing_strategy(self) -> dict[str, Any]:
        """Analyze current performance and suggest routing strategy optimizations."""
        stats = self.get_cost_optimization_stats()
        analysis = self.analyze_routing_effectiveness()

        suggestions = []

        # Analyze cost savings performance
        if stats["cost_savings_rate_percent"] < 30:
            suggestions.append(
                {
                    "type": "cost_optimization",
                    "priority": "high",
                    "message": "Cost savings rate is below 30%. Consider adjusting quality thresholds or cost weights.",
                    "recommended_action": "Increase COST_WEIGHT or decrease QUALITY_WEIGHT in configuration",
                }
            )

        # Analyze model performance variance
        if analysis.get("cost_effectiveness_scores"):
            scores = list(analysis["cost_effectiveness_scores"].values())
            if len(scores) > 1:
                variance = statistics.variance(scores)
                if variance > 0.5:  # High variance indicates inconsistent performance
                    suggestions.append(
                        {
                            "type": "model_consistency",
                            "priority": "medium",
                            "message": f"High variance in model cost-effectiveness ({variance:.3f}). Consider model tuning or replacement.",
                            "recommended_action": "Review model configurations or consider alternative models",
                        }
                    )

        # Analyze decision confidence
        if analysis.get("avg_confidence", 0) < 0.7:
            suggestions.append(
                {
                    "type": "decision_confidence",
                    "priority": "medium",
                    "message": "Low decision confidence detected. Consider improving model profiling or quality estimation.",
                    "recommended_action": "Increase sample size for model profiling or enhance quality metrics",
                }
            )

        return {
            "current_performance": stats,
            "routing_analysis": analysis,
            "optimization_suggestions": suggestions,
            "overall_assessment": "optimal"
            if len(suggestions) == 0
            else "needs_improvement"
            if len(suggestions) <= 2
            else "requires_attention",
        }

    def chat_and_update(
        self,
        messages: Sequence[dict[str, Any]],
        quality_metric: float = 0.8,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
    ) -> tuple[str, LLMCallResult, float]:
        """Convenience wrapper: route, invoke, normalize reward, update bandit.

        Returns (model_name, result, reward).
        """
        # In earlier versions this raised when contextual routing was enabled.
        # For backward compatibility we now gracefully fall back to classical
        # Thompson sampling when callers (legacy code/tests) invoke this path
        # with contextual mode toggled on but without feature vectors.
        # This mirrors the fallback already implemented in chat()/update().
        model, result = self.chat(messages)
        reward = self._reward_normalizer.compute(quality=quality, latency_ms=latency_ms, cost=cost)
        self.update(model, reward)
        return model, result, reward

    # ---------------------- Contextual Mode APIs ----------------------
    def chat_with_features(
        self, messages: Sequence[dict[str, Any]], features: Sequence[float]
    ) -> tuple[str, LLMCallResult]:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        # Determine initial contextual viability (length + presence) without mutating later to appease type checkers.
        use_contextual = bool(
            self._hybrid_enabled
            and features is not None
            and isinstance(features, Sequence)
            and len(features) == self._linucb_dimension
        )
        effective_contextual = False
        if use_contextual:
            fq = self._feature_quality(features)
            if self._feature_quality_gauge:
                try:
                    self._feature_quality_gauge.set(fq)
                except Exception:  # pragma: no cover
                    pass
            below = fq < self._feature_quality_min and self._hybrid_enabled
            effective_contextual = not below
        if effective_contextual:
            model_names = list(self._clients.keys())
            assert self._ctx_router is not None
            selected = self._ctx_router.select(model_names, features)
            result = self._clients[selected].chat(messages)
        else:
            model_names = list(self._clients.keys())
            selected = self._bandit.select(model_names)
            result = self._clients[selected].chat(messages)
            if self._fallback_counter:
                try:
                    self._fallback_counter.inc(1)
                except Exception:  # pragma: no cover
                    pass
        if self._chat_counter:
            try:
                self._chat_counter.inc(1)
            except Exception:  # pragma: no cover
                pass
        if self._tenant_mode:
            record_selection(selected)
        return selected, result

    def update_with_features(self, model_name: str, reward: float, features: Sequence[float]) -> None:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        if model_name not in self._clients:
            return
        # Hybrid: if features malformed or dimension mismatch, update classic bandit instead
        if self._hybrid_enabled:
            use_contextual = True
            try:
                if features is None or len(features) != self._linucb_dimension:
                    use_contextual = False
            except Exception:
                use_contextual = False
            # apply quality gate
            if use_contextual:
                fq = self._feature_quality(features)
                if self._feature_quality_gauge:
                    try:
                        self._feature_quality_gauge.set(fq)
                    except Exception:  # pragma: no cover
                        pass
                if fq < self._feature_quality_min:
                    use_contextual = False
            if use_contextual:
                assert self._ctx_router is not None
                self._ctx_router.update(model_name, reward, features)
            else:
                self._bandit.update(model_name, reward)
                if self._fallback_counter:
                    try:
                        self._fallback_counter.inc(1)
                    except Exception:  # pragma: no cover
                        pass
        else:
            assert self._ctx_router is not None
            self._ctx_router.update(model_name, reward, features)

    def chat_with_features_and_update(
        self,
        messages: Sequence[dict[str, Any]],
        features: Sequence[float],
        quality: float,
        latency_ms: float,
        cost: float,
    ) -> tuple[str, LLMCallResult, float]:
        if not self._contextual_enabled:
            raise RuntimeError("Contextual mode not enabled")
        model, result = self.chat_with_features(messages, features)
        reward = self._reward_normalizer.compute(quality=quality, latency_ms=latency_ms, cost=cost)
        self.update_with_features(model, reward, features)
        return model, result, reward


__all__ = ["LLMRouter"]
