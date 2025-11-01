"""LLM adapter for unified router integration with CrewAI agents.

This module provides an adapter that allows the unified router to be used
as an LLM provider for CrewAI agents, enabling seamless integration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base_router import RoutingRequest, UnifiedRouter


if TYPE_CHECKING:
    from collections.abc import Sequence


class RouterLLMAdapter:
    """Adapter that makes UnifiedRouter compatible with CrewAI LLM interface."""

    def __init__(self, router: UnifiedRouter | None = None) -> None:
        """Initialize adapter with unified router."""
        self.router = router or UnifiedRouter()
        self.model_name = "unified-router"

    def invoke(self, messages: Sequence[dict[str, Any]], **kwargs: Any) -> Any:
        """Invoke the router to get a response.

        This method is called by CrewAI when the agent needs to make an LLM call.
        It converts the CrewAI call into a routing request and returns the response.
        """
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)

        # Extract constraints from kwargs
        constraints = self._extract_constraints(kwargs)

        # Create routing request
        request = RoutingRequest(
            prompt=prompt,
            context={"messages": messages, "kwargs": kwargs},
            constraints=constraints,
            tenant=kwargs.get("tenant", "default"),
            workspace=kwargs.get("workspace", "default"),
        )

        # Route the request
        result = self.router.route(request)

        if not result.success:
            # Return error response
            return {
                "content": f"Routing failed: {result.error}",
                "model": "error",
                "usage": {"total_tokens": 0},
            }

        # Extract routing decision
        decision = result.data["data"]

        # For now, return a mock response since we don't have actual LLM calls
        # In a real implementation, this would call the selected model
        return {
            "content": f"Mock response from {decision.model_id} (via {decision.strategy_used} routing)",
            "model": decision.model_id,
            "usage": {"total_tokens": 100},  # Mock token usage
            "routing_info": {
                "strategy": decision.strategy_used,
                "reasoning": decision.reasoning,
                "estimated_cost": decision.estimated_cost,
                "estimated_latency": decision.estimated_latency,
            },
        }

    def _messages_to_prompt(self, messages: Sequence[dict[str, Any]]) -> str:
        """Convert message sequence to prompt string."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        return "\n".join(prompt_parts)

    def _extract_constraints(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Extract routing constraints from kwargs."""
        constraints = {}

        # Map common LLM parameters to routing constraints
        if "temperature" in kwargs:
            # Higher temperature might indicate need for more creative models
            if kwargs["temperature"] > 0.8:
                constraints["min_quality"] = 0.8  # Prefer higher quality models
            else:
                constraints["min_quality"] = 0.6

        if "max_tokens" in kwargs and kwargs["max_tokens"] > 1000:
            # Longer responses might benefit from more capable models
            constraints["min_quality"] = max(constraints.get("min_quality", 0.6), 0.7)

        # Check for explicit routing preferences
        if "minimize_cost" in kwargs:
            constraints["minimize_cost"] = kwargs["minimize_cost"]

        if "minimize_latency" in kwargs:
            constraints["minimize_latency"] = kwargs["minimize_latency"]

        if "max_cost" in kwargs:
            constraints["max_cost"] = kwargs["max_cost"]

        if "max_latency" in kwargs:
            constraints["max_latency"] = kwargs["max_latency"]

        return constraints

    def get_stats(self) -> dict[str, Any]:
        """Get router statistics."""
        return self.router.get_strategy_stats()

    def clear_cache(self) -> None:
        """Clear router cache."""
        self.router.clear_cache()


def create_router_llm(router: UnifiedRouter | None = None) -> RouterLLMAdapter:
    """Create a router-based LLM adapter for CrewAI agents."""
    return RouterLLMAdapter(router)
