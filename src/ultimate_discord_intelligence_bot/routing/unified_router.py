"""Unified Router Service - Single interface for all LLM routing backends

This service consolidates all routing implementations into a single, coherent
interface that provides intelligent model selection, cost optimization, and
performance tracking across all routing systems.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ultimate_discord_intelligence_bot.step_result import StepResult
from ultimate_discord_intelligence_bot.tenancy.context import current_tenant


# Import existing routing implementations
try:
    from ultimate_discord_intelligence_bot.services.openrouter_service import (
        OpenRouterService,
    )
except ImportError:
    OpenRouterService = None

try:
    from ultimate_discord_intelligence_bot.services.rl_model_router import RLModelRouter
except ImportError:
    RLModelRouter = None

# Deprecated: CoreLLMRouter and CoreRouter removed in Phase 6
# All routing now unified through OpenRouterService
# See ADR-0003 for routing consolidation rationale

logger = logging.getLogger(__name__)


@dataclass
class RoutingRequest:
    """Request for unified routing"""

    prompt: str
    task_type: str = "general"
    context: dict[str, Any] | None = None
    budget_limit: float | None = None
    quality_requirement: str = "balanced"  # fast, balanced, high_quality
    tenant_id: str | None = None
    workspace_id: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


@dataclass
class RoutingResult:
    """Result from unified routing"""

    selected_model: str
    provider: str
    estimated_cost: float
    confidence_score: float = 1.0
    routing_method: str = "unified"
    fallback_used: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedRouterConfig:
    """Configuration for unified router service"""

    enable_openrouter: bool = True
    enable_rl_router: bool = True
    enable_learning_engine: bool = True
    enable_cost_tracking: bool = True
    enable_performance_monitoring: bool = True
    default_budget_limit: float = 10.0
    quality_threshold: float = 0.7
    fallback_strategy: str = "cost_optimized"  # cost_optimized, quality_first, balanced


class UnifiedRouterService:
    """Unified interface to all routing backends with intelligent selection"""

    def __init__(self, config: UnifiedRouterConfig | None = None):
        self.config = config or UnifiedRouterConfig()
        self._initialized = False
        self._routers = {}
        self._performance_metrics = {}

        # Initialize routers based on configuration
        self._initialize_routers()

    def _initialize_routers(self) -> None:
        """Initialize all configured routing backends"""
        try:
            # OpenRouter Service
            if self.config.enable_openrouter and OpenRouterService:
                try:
                    self._routers["openrouter"] = OpenRouterService()
                    logger.info("OpenRouter backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenRouter: {e}")

            # RL Model Router
            if self.config.enable_rl_router and RLModelRouter:
                try:
                    self._routers["rl_router"] = RLModelRouter()
                    logger.info("RL Model Router backend initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize RL Model Router: {e}")

            # Phase 6: Core Router and CoreLLMRouter deprecated
            # Removed: CoreRouter (Learning Engine) - functionality in OpenRouterService
            # Removed: CoreLLMRouter - replaced by OpenRouterService with bandit plugins
            # See ADR-0003 for routing consolidation rationale

            self._initialized = True
            logger.info(f"Unified router service initialized with {len(self._routers)} backends")

        except Exception as e:
            logger.error(f"Failed to initialize unified router service: {e}")
            self._initialized = False

    async def route_request(
        self,
        request: RoutingRequest,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
    ) -> StepResult:
        """Route request through unified routing system"""
        try:
            if not self._initialized:
                return StepResult.fail("Unified router service not initialized")

            # Resolve tenant context
            ctx = current_tenant()
            if tenant_id is None:
                tenant_id = getattr(ctx, "tenant_id", "default") if ctx else "default"
            if workspace_id is None:
                workspace_id = getattr(ctx, "workspace_id", "main") if ctx else "main"

            # Update request with tenant context
            request.tenant_id = tenant_id
            request.workspace_id = workspace_id

            # Apply budget limits
            if request.budget_limit is None:
                request.budget_limit = self.config.default_budget_limit

            # Get routing recommendations from all backends
            routing_candidates = []

            # OpenRouter routing
            if "openrouter" in self._routers:
                openrouter_result = await self._route_openrouter(request)
                if openrouter_result.success:
                    routing_candidates.extend(openrouter_result.data)

            # RL Router routing
            if "rl_router" in self._routers:
                rl_result = await self._route_rl_router(request)
                if rl_result.success:
                    routing_candidates.extend(rl_result.data)

            # Learning Engine routing
            if "learning_engine" in self._routers:
                learning_result = await self._route_learning_engine(request)
                if learning_result.success:
                    routing_candidates.extend(learning_result.data)

            # Core LLM Router
            if "core_llm" in self._routers:
                core_result = await self._route_core_llm(request)
                if core_result.success:
                    routing_candidates.extend(core_result.data)

            if not routing_candidates:
                return StepResult.fail("No routing candidates available")

            # Apply unified selection logic
            selected_route = await self._select_optimal_route(routing_candidates, request)

            # Record routing decision for learning
            await self._record_routing_decision(request, selected_route, routing_candidates)

            return StepResult.ok(data=selected_route)

        except Exception as e:
            logger.error(f"Error in unified routing: {e}", exc_info=True)
            return StepResult.fail(f"Unified routing failed: {e!s}")

    async def _route_openrouter(self, request: RoutingRequest) -> StepResult:
        """Route through OpenRouter service"""
        try:
            openrouter = self._routers["openrouter"]

            # Use OpenRouter's routing logic
            if hasattr(openrouter, "route_model"):
                result = await openrouter.route_model(
                    task_type=request.task_type,
                    candidate_models=[],  # Let OpenRouter decide
                    prompt=request.prompt,
                    context_payload={
                        "tenant": request.tenant_id,
                        "workspace": request.workspace_id,
                        "budget_limit": request.budget_limit,
                        "quality_requirement": request.quality_requirement,
                    },
                )

                if result and result.get("selected_model"):
                    return StepResult.ok(
                        data=[
                            {
                                "model": result["selected_model"],
                                "provider": "openrouter",
                                "estimated_cost": result.get("estimated_cost", 0.0),
                                "confidence": result.get("confidence", 0.8),
                                "routing_method": "openrouter",
                                "metadata": result,
                            }
                        ]
                    )

            return StepResult.fail("OpenRouter routing failed")

        except Exception as e:
            logger.debug(f"OpenRouter routing failed: {e}")
            return StepResult.fail(str(e))

    async def _route_rl_router(self, request: RoutingRequest) -> StepResult:
        """Route through RL Model Router"""
        try:
            rl_router = self._routers["rl_router"]

            # Use RL Router's routing logic
            if hasattr(rl_router, "route_model"):
                result = await rl_router.route_model(
                    task_type=request.task_type,
                    candidate_models=[],  # Let RL router decide
                    prompt=request.prompt,
                    context_payload={
                        "tenant": request.tenant_id,
                        "workspace": request.workspace_id,
                        "budget_limit": request.budget_limit,
                        "quality_requirement": request.quality_requirement,
                    },
                )

                if result and result.get("selected_model"):
                    return StepResult.ok(
                        data=[
                            {
                                "model": result["selected_model"],
                                "provider": "rl_router",
                                "estimated_cost": result.get("estimated_cost", 0.0),
                                "confidence": result.get("confidence", 0.9),
                                "routing_method": "rl_router",
                                "metadata": result,
                            }
                        ]
                    )

            return StepResult.fail("RL Router routing failed")

        except Exception as e:
            logger.debug(f"RL Router routing failed: {e}")
            return StepResult.fail(str(e))

    async def _route_learning_engine(self, request: RoutingRequest) -> StepResult:
        """Route through Learning Engine"""
        try:
            learning_engine = self._routers["learning_engine"]

            # Use Learning Engine's routing logic
            if hasattr(learning_engine, "select_model"):
                result = learning_engine.select_model(
                    task_type=request.task_type,
                    prompt=request.prompt,
                    budget_limit=request.budget_limit,
                )

                if result:
                    return StepResult.ok(
                        data=[
                            {
                                "model": result.get("model", "unknown"),
                                "provider": "learning_engine",
                                "estimated_cost": result.get("cost", 0.0),
                                "confidence": result.get("confidence", 0.7),
                                "routing_method": "learning_engine",
                                "metadata": result,
                            }
                        ]
                    )

            return StepResult.fail("Learning Engine routing failed")

        except Exception as e:
            logger.debug(f"Learning Engine routing failed: {e}")
            return StepResult.fail(str(e))

    async def _route_core_llm(self, request: RoutingRequest) -> StepResult:
        """Route through Core LLM Router"""
        try:
            core_llm = self._routers["core_llm"]

            # Use Core LLM Router's routing logic
            if hasattr(core_llm, "route"):
                result = core_llm.route(
                    prompt=request.prompt,
                    task_type=request.task_type,
                    budget=request.budget_limit,
                )

                if result:
                    return StepResult.ok(
                        data=[
                            {
                                "model": result.get("model", "unknown"),
                                "provider": "core_llm",
                                "estimated_cost": result.get("cost", 0.0),
                                "confidence": result.get("confidence", 0.6),
                                "routing_method": "core_llm",
                                "metadata": result,
                            }
                        ]
                    )

            return StepResult.fail("Core LLM Router routing failed")

        except Exception as e:
            logger.debug(f"Core LLM Router routing failed: {e}")
            return StepResult.fail(str(e))

    async def _select_optimal_route(self, candidates: list[dict[str, Any]], request: RoutingRequest) -> RoutingResult:
        """Select optimal route from candidates using unified logic"""
        try:
            if not candidates:
                raise ValueError("No routing candidates available")

            # Filter candidates by budget
            budget_filtered = [c for c in candidates if c.get("estimated_cost", 0) <= request.budget_limit]

            if not budget_filtered:
                # If no candidates fit budget, use cheapest
                budget_filtered = sorted(candidates, key=lambda x: x.get("estimated_cost", 0))

            # Apply quality requirements
            if request.quality_requirement == "high_quality":
                # Prefer higher confidence scores
                sorted_candidates = sorted(budget_filtered, key=lambda x: x.get("confidence", 0), reverse=True)
            elif request.quality_requirement == "fast":
                # Prefer lower cost
                sorted_candidates = sorted(budget_filtered, key=lambda x: x.get("estimated_cost", 0))
            else:  # balanced
                # Balance cost and quality
                sorted_candidates = sorted(
                    budget_filtered,
                    key=lambda x: (x.get("estimated_cost", 0) * 0.6 + (1 - x.get("confidence", 0)) * 0.4),
                )

            # Select best candidate
            best_candidate = sorted_candidates[0]

            # Check if fallback was used
            fallback_used = best_candidate != candidates[0]

            return RoutingResult(
                selected_model=best_candidate["model"],
                provider=best_candidate["provider"],
                estimated_cost=best_candidate["estimated_cost"],
                confidence_score=best_candidate["confidence"],
                routing_method=best_candidate["routing_method"],
                fallback_used=fallback_used,
                metadata={
                    "candidates_evaluated": len(candidates),
                    "budget_filtered": len(budget_filtered),
                    "selection_reason": self._get_selection_reason(best_candidate, request),
                    "all_candidates": candidates,
                },
            )

        except Exception as e:
            logger.warning(f"Route selection failed: {e}")
            # Fallback to first candidate
            fallback = candidates[0]
            return RoutingResult(
                selected_model=fallback["model"],
                provider=fallback["provider"],
                estimated_cost=fallback["estimated_cost"],
                confidence_score=fallback["confidence"],
                routing_method=fallback["routing_method"],
                fallback_used=True,
                metadata={"error": str(e), "fallback_reason": "selection_failed"},
            )

    def _get_selection_reason(self, candidate: dict[str, Any], request: RoutingRequest) -> str:
        """Get human-readable reason for route selection"""
        if request.quality_requirement == "high_quality":
            return f"Selected for high quality (confidence: {candidate['confidence']:.2f})"
        elif request.quality_requirement == "fast":
            return f"Selected for speed (cost: ${candidate['estimated_cost']:.4f})"
        else:
            return f"Selected for balanced approach (cost: ${candidate['estimated_cost']:.4f}, confidence: {candidate['confidence']:.2f})"

    async def _record_routing_decision(
        self,
        request: RoutingRequest,
        selected_route: RoutingResult,
        all_candidates: list[dict[str, Any]],
    ) -> None:
        """Record routing decision for learning and analytics"""
        try:
            decision_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tenant_id": request.tenant_id,
                "workspace_id": request.workspace_id,
                "task_type": request.task_type,
                "quality_requirement": request.quality_requirement,
                "budget_limit": request.budget_limit,
                "selected_model": selected_route.selected_model,
                "selected_provider": selected_route.provider,
                "estimated_cost": selected_route.estimated_cost,
                "confidence_score": selected_route.confidence_score,
                "routing_method": selected_route.routing_method,
                "fallback_used": selected_route.fallback_used,
                "candidates_count": len(all_candidates),
                "selection_reason": selected_route.metadata.get("selection_reason", "unknown"),
            }

            # Store in performance metrics
            key = f"{request.tenant_id}:{request.workspace_id}:{request.task_type}"
            if key not in self._performance_metrics:
                self._performance_metrics[key] = []

            self._performance_metrics[key].append(decision_record)

            # Keep only last 100 decisions per key
            if len(self._performance_metrics[key]) > 100:
                self._performance_metrics[key] = self._performance_metrics[key][-100:]

            # Update learning systems if available
            if "rl_router" in self._routers and hasattr(self._routers["rl_router"], "update_reward"):
                await self._routers["rl_router"].update_reward(
                    context_payload={
                        "tenant": request.tenant_id,
                        "workspace": request.workspace_id,
                        "task_type": request.task_type,
                    },
                    reward=selected_route.confidence_score,
                    metadata=decision_record,
                )

            logger.debug(f"Recorded routing decision: {decision_record}")

        except Exception as e:
            logger.warning(f"Failed to record routing decision: {e}")

    def get_performance_metrics(self, tenant_id: str | None = None, workspace_id: str | None = None) -> dict[str, Any]:
        """Get performance metrics for routing decisions"""
        try:
            if tenant_id and workspace_id:
                key = f"{tenant_id}:{workspace_id}"
                metrics = self._performance_metrics.get(key, [])
            else:
                # Return all metrics
                metrics = []
                for key_metrics in self._performance_metrics.values():
                    metrics.extend(key_metrics)

            if not metrics:
                return {"total_decisions": 0, "metrics": []}

            # Calculate summary statistics
            total_decisions = len(metrics)
            avg_confidence = sum(m["confidence_score"] for m in metrics) / total_decisions
            avg_cost = sum(m["estimated_cost"] for m in metrics) / total_decisions
            fallback_rate = sum(m["fallback_used"] for m in metrics) / total_decisions

            # Group by routing method
            method_counts = {}
            for metric in metrics:
                method = metric["routing_method"]
                method_counts[method] = method_counts.get(method, 0) + 1

            return {
                "total_decisions": total_decisions,
                "avg_confidence": avg_confidence,
                "avg_cost": avg_cost,
                "fallback_rate": fallback_rate,
                "method_distribution": method_counts,
                "recent_decisions": metrics[-10:] if len(metrics) > 10 else metrics,
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    def get_router_status(self) -> dict[str, bool]:
        """Get status of all routing backends"""
        return {
            "initialized": self._initialized,
            "routers": dict.fromkeys(self._routers.keys(), True),
            "config": {
                "openrouter": self.config.enable_openrouter,
                "rl_router": self.config.enable_rl_router,
                "learning_engine": self.config.enable_learning_engine,
                "cost_tracking": self.config.enable_cost_tracking,
            },
        }
