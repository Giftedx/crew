"""Adapter layer for AdaptiveRoutingManager to match ConversationalPipeline interface.

This module provides adapter methods that bridge the gap between the pipeline's
expected interface and the actual AdaptiveRoutingManager/OpenRouterService APIs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ultimate_discord_intelligence_bot.step_result import StepResult


if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.services.openrouter_service import OpenRouterService
    from ultimate_discord_intelligence_bot.services.openrouter_service.adaptive_routing import AdaptiveRoutingManager


logger = logging.getLogger(__name__)


class RoutingAdapter:
    """Adapter that provides suggest_model() and estimate_cost() for AdaptiveRoutingManager."""

    def __init__(self, routing_manager: AdaptiveRoutingManager, openrouter_service: OpenRouterService):
        """Initialize adapter with routing manager and OpenRouter service."""
        self.routing_manager = routing_manager
        self.openrouter_service = openrouter_service

    async def suggest_model(
        self, task_type: str, context: dict[str, Any]
    ) -> StepResult[dict[str, Any]]:
        """Suggest a model for the given task type and context.
        
        Args:
            task_type: Type of task (e.g., 'decision_making', 'response_generation')
            context: Context dictionary with prompt_length, complexity, etc.
            
        Returns:
            StepResult with model information in data dict with 'model' key.
        """
        try:
            # Get candidate models for this task type from OpenRouterService
            models_map = getattr(self.openrouter_service, "models_map", {})
            candidates = models_map.get(task_type, models_map.get("general", ["openai/gpt-4o-mini"]))
            
            # Use AdaptiveRoutingManager's suggest method
            suggestion = self.routing_manager.suggest(
                task_type=task_type,
                candidates=candidates,
                context=context,
            )
            
            if suggestion is None:
                # Fallback: use first candidate
                selected_model = candidates[0] if candidates else "openai/gpt-4o-mini"
                logger.debug(f"Routing manager returned None, using fallback: {selected_model}")
            else:
                trial_index, selected_model = suggestion
                
            return StepResult.ok(data={"model": selected_model, "task_type": task_type})
            
        except Exception as e:
            logger.error(f"Failed to suggest model: {e}", exc_info=True)
            # Fallback to default
            default_model = "openai/gpt-4o-mini"
            return StepResult.ok(data={"model": default_model, "task_type": task_type})

    async def estimate_cost(
        self,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        prompt: str | None = None,
        max_tokens: int = 500,
    ) -> StepResult[dict[str, Any]]:
        """Estimate the cost of generating a response.
        
        Args:
            model: Model name (optional, uses default if not provided)
            input_tokens: Input token count (optional, will estimate from prompt if provided)
            output_tokens: Output token count (optional, uses max_tokens if not provided)
            prompt: Input prompt text (optional, used if input_tokens not provided)
            max_tokens: Maximum output tokens (used if output_tokens not provided)
            
        Returns:
            StepResult with dict containing 'estimated_cost' key.
        """
        try:
            # Determine input tokens
            if input_tokens is None:
                if prompt:
                    prompt_engine = getattr(self.openrouter_service, "prompt_engine", None)
                    if prompt_engine:
                        token_count = prompt_engine.count_tokens(prompt, model)
                        if isinstance(token_count, StepResult):
                            input_tokens = int(token_count.data) if token_count.success else len(prompt.split()) * 1.3
                        else:
                            input_tokens = int(token_count)
                    else:
                        input_tokens = int(len(prompt.split()) * 1.3)  # Rough estimate
                else:
                    input_tokens = 100  # Default fallback
            else:
                input_tokens = int(input_tokens)
            
            # Determine output tokens
            if output_tokens is None:
                output_tokens = int(max_tokens)
            else:
                output_tokens = int(output_tokens)
            
            # Get model (default if not provided)
            if not model:
                models_map = getattr(self.openrouter_service, "models_map", {})
                candidates = models_map.get("general", ["openai/gpt-4o-mini"])
                model = candidates[0] if candidates else "openai/gpt-4o-mini"
            
            # Use OpenRouterService's token meter
            token_meter = getattr(self.openrouter_service, "token_meter", None)
            
            if not token_meter:
                logger.warning("Token meter not available, using simple estimate")
                # Simple fallback: assume $0.001 per 1K tokens
                cost = ((input_tokens + output_tokens) / 1000) * 0.001
                return StepResult.ok(data={"estimated_cost": cost})
            
            # Estimate cost using token meter
            effective_prices = dict(token_meter.model_prices)
            
            # Apply tenant pricing overrides if available
            tenant_registry = getattr(self.openrouter_service, "tenant_registry", None)
            if tenant_registry:
                from ultimate_discord_intelligence_bot.tenancy import current_tenant
                tenant_ctx = current_tenant()
                if tenant_ctx:
                    effective_prices.update(tenant_registry.get_pricing_map(tenant_ctx))
            
            input_cost = token_meter.estimate_cost(input_tokens, model, prices=effective_prices)
            if isinstance(input_cost, StepResult):
                input_cost = input_cost.data if input_cost.success else 0.0
            
            output_cost = token_meter.estimate_cost(output_tokens, model, prices=effective_prices)
            if isinstance(output_cost, StepResult):
                output_cost = output_cost.data if output_cost.success else 0.0
            
            total_cost = float(input_cost) + float(output_cost)
            return StepResult.ok(data={"estimated_cost": total_cost})
            
        except Exception as e:
            logger.error(f"Failed to estimate cost: {e}", exc_info=True)
            # Fallback: simple estimate
            in_tokens = input_tokens if input_tokens else 100
            out_tokens = output_tokens if output_tokens else max_tokens
            cost = ((in_tokens + out_tokens) / 1000) * 0.001
            return StepResult.ok(data={"estimated_cost": cost})


class PromptEngineAdapter:
    """Adapter that provides generate_response() for PromptEngine while delegating other methods."""
    
    def __init__(self, prompt_engine: Any, openrouter_service: OpenRouterService):
        """Initialize adapter with prompt engine and OpenRouter service."""
        self._prompt_engine = prompt_engine
        self.openrouter_service = openrouter_service
        
        # Delegate common PromptEngine methods
        # Using __getattr__ to forward all other attributes to the underlying prompt_engine
        # This ensures compatibility with existing code that uses PromptEngine methods
    
    def __getattr__(self, name: str) -> Any:
        """Delegate all other attributes to the underlying prompt engine."""
        return getattr(self._prompt_engine, name)
    
    async def generate_response(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> StepResult[str]:
        """Generate a response using the prompt engine and OpenRouter service.
        
        Args:
            prompt: Input prompt
            model: Model name (optional, will be chosen if not provided)
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            
        Returns:
            StepResult with generated response text.
        """
        try:
            # If no model specified, choose one
            if not model:
                task_type = "general"
                models_map = getattr(self.openrouter_service, "models_map", {})
                candidates = models_map.get(task_type, models_map.get("general", ["openai/gpt-4o-mini"]))
                model = candidates[0] if candidates else "openai/gpt-4o-mini"
            
            # Use OpenRouterService's route method to generate response
            result = self.openrouter_service.route(
                prompt=prompt,
                task_type="response_generation",
                model=model,
            )
            
            if isinstance(result, dict):
                if result.get("status") == "success":
                    response = result.get("response", "")
                    return StepResult.ok(data=response)
                else:
                    error = result.get("error", "Unknown error")
                    return StepResult.fail(f"Generation failed: {error}")
            else:
                # Unexpected return type
                logger.warning(f"OpenRouterService.route returned unexpected type: {type(result)}")
                return StepResult.fail("Unexpected response format")
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}", exc_info=True)
            return StepResult.fail(f"Response generation failed: {e!s}")

