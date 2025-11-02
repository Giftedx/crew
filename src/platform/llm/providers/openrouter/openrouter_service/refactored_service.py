"""Refactored OpenRouter service with extracted route components.

This module provides a clean, maintainable implementation of the OpenRouter service
by breaking down the monolithic route method into focused, composable components.
"""
from __future__ import annotations
import copy
import logging
from platform.config.configuration import get_config
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any
from platform.rl.learning_engine import LearningEngine
if TYPE_CHECKING:
    from ultimate_discord_intelligence_bot.tenancy.context import TenantContext
    from ultimate_discord_intelligence_bot.tenancy.registry import TenantRegistry
from .route_components import CacheManager, CostCalculator, MetricsRecorder, NetworkExecutor, OfflineExecutor, RewardCalculator, RouteContext, RouteResult, TenantResolver
log = logging.getLogger(__name__)

class RefactoredOpenRouterService:
    """Refactored OpenRouter service with clean separation of concerns."""

    def __init__(self, models_map: dict[str, list[str]] | None=None, learning_engine: LearningEngine | None=None, api_key: str | None=None, provider_opts: dict[str, Any] | None=None, logger: Any | None=None, token_meter: Any | None=None, cache: Any | None=None, tenant_registry: TenantRegistry | None=None, semantic_cache: Any | None=None) -> None:
        """Initialize the refactored service."""
        self.models_map = models_map or self._get_default_models()
        self.learning = learning_engine or LearningEngine()
        self.api_key = api_key
        self.provider_opts = copy.deepcopy(provider_opts or {})
        self.logger = logger
        self.token_meter = token_meter or self._create_default_token_meter()
        self.tenant_registry = tenant_registry
        self.semantic_cache = semantic_cache
        self.tenant_resolver = TenantResolver(tenant_registry)
        self.cost_calculator = CostCalculator(self.token_meter, tenant_registry)
        self.reward_calculator = RewardCalculator(tenant_registry)
        self.cache_manager = CacheManager(semantic_cache, cache)
        self.offline_executor = OfflineExecutor(token_meter.prompt_engine if token_meter else None, self.learning, self.reward_calculator, MetricsRecorder())
        self.network_executor = NetworkExecutor(api_key or '', token_meter.prompt_engine if token_meter else None, self.learning, self.reward_calculator, MetricsRecorder())

    def _get_default_models(self) -> dict[str, list[str]]:
        """Get default model configuration."""
        config = get_config()
        env_general = config.get_setting('openrouter_general_model')
        env_analysis = config.get_setting('openrouter_analysis_model')
        return {'general': [env_general or 'openai/gpt-4o-mini'], 'analysis': [env_analysis or env_general or 'openai/gpt-4o-mini']}

    def _create_default_token_meter(self) -> Any:
        """Create a default token meter for testing."""

        class DefaultTokenMeter:

            def __init__(self):
                self.model_prices = {'openai/gpt-4o-mini': 0.00015, 'openai/gpt-4o': 0.005}
                self.max_cost_per_request = 1.0

            def count_tokens(self, text: str, model: str) -> int:
                return len(text) // 4

            def estimate_cost(self, tokens: int, model: str, prices: dict[str, float] | None=None) -> float:
                """Estimate cost and return as float."""
                price_map = prices or self.model_prices
                price = price_map.get(model, 0.0001)
                return price * (tokens / 1000)

            def affordable_model(self, tokens: int, candidates: list[str], prices: dict[str, float] | None=None) -> str | None:
                """Return the cheapest affordable model."""
                max_cost = self.max_cost_per_request or float('inf')
                price_map = prices or self.model_prices
                for model in sorted(candidates, key=lambda m: price_map.get(m, 0.0)):
                    cost = self.estimate_cost(tokens, model, prices=price_map)
                    if cost <= max_cost:
                        return model
                return None
        return DefaultTokenMeter()

    def route(self, prompt: str, task_type: str='general', model: str | None=None, provider_opts: dict[str, Any] | None=None) -> StepResult:
        """Route a prompt with clean separation of concerns."""
        try:
            tenant_context = self.tenant_resolver.resolve_context('openrouter_service')
            effective_models = self.tenant_resolver.get_effective_models(self.models_map, tenant_context)
            provider_prefs = self.tenant_resolver.get_provider_preferences(tenant_context)
            chosen_model = model or self._choose_model(effective_models, task_type)
            provider = self._merge_provider_options(provider_prefs, provider_opts)
            provider_family = self._extract_provider_family(provider)
            tokens_in, projected_cost, affordable = self.cost_calculator.calculate_costs(prompt, chosen_model, effective_models, task_type, tenant_context)
            context = RouteContext(prompt=prompt, task_type=task_type, model=chosen_model, provider_opts=provider_opts, tenant_context=tenant_context, effective_models=effective_models, provider=provider, provider_family=provider_family, tokens_in=tokens_in, projected_cost=projected_cost, effective_max=self._get_effective_max(tenant_context), cache_key=None, namespace=self._get_namespace(tenant_context))
            context.cache_key = self._generate_cache_key(context.prompt, context.model, context.provider)
            cache_result = self._check_caches(context)
            if cache_result:
                return self._convert_to_step_result(cache_result)
            can_proceed, error_msg, fallback_model = self.cost_calculator.enforce_budget_limits(projected_cost, task_type, chosen_model, affordable, tokens_in, context.effective_max, tenant_context)
            if not can_proceed:
                return StepResult.fail(error_msg or 'Budget limit exceeded')
            if fallback_model:
                context.model = fallback_model
                context.tokens_in, context.projected_cost, _ = self.cost_calculator.calculate_costs(prompt, fallback_model, effective_models, task_type, tenant_context)
            if self._is_offline_mode():
                result = self.offline_executor.execute(context, context.projected_cost, context.effective_max, tenant_context)
            else:
                result = self.network_executor.execute(context, context.projected_cost, context.effective_max, tenant_context)
            if result.status == 'success':
                self.cache_manager.set_cache_results(prompt, context.model, self._convert_to_dict(result), context.namespace, context.cache_key)
            return self._convert_to_step_result(result)
        except Exception as exc:
            log.error('Route execution failed: %s', exc, exc_info=True)
            return StepResult.fail(f'Route execution failed: {exc}')

    def _choose_model(self, effective_models: dict[str, list[str]], task_type: str) -> str:
        """Choose model from effective models."""
        available_models = effective_models.get(task_type, effective_models.get('general', []))
        if not available_models:
            return 'openai/gpt-4o-mini'
        return self.learning.select_model(task_type, available_models)

    def _merge_provider_options(self, base: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
        """Merge provider options with deep merge."""

        def _deep_merge(base_dict: dict[str, Any], overrides_dict: dict[str, Any]) -> dict[str, Any]:
            result = copy.deepcopy(base_dict)
            for key, value in overrides_dict.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = _deep_merge(result[key], value)
                else:
                    result[key] = copy.deepcopy(value)
            return result
        result = copy.deepcopy(self.provider_opts)
        if base:
            result = _deep_merge(result, base)
        if overrides:
            result = _deep_merge(result, overrides)
        return result

    def _extract_provider_family(self, provider: dict[str, Any]) -> str:
        """Extract provider family from provider options."""
        try:
            order = provider.get('order') if isinstance(provider, dict) else None
            if isinstance(order, list) and order:
                return str(order[0])
        except Exception:
            pass
        return 'unknown'

    def _get_effective_max(self, tenant_context: TenantContext | None) -> float:
        """Get effective maximum cost per request."""
        base_max = self.token_meter.max_cost_per_request if self.token_meter and self.token_meter.max_cost_per_request is not None else float('inf')
        if self.tenant_registry and tenant_context:
            per_task_limit = self.tenant_registry.get_per_request_limit(tenant_context, 'general')
            if per_task_limit is not None:
                return min(base_max, per_task_limit)
        return base_max

    def _get_namespace(self, tenant_context: TenantContext | None) -> str | None:
        """Get namespace for caching."""
        if tenant_context:
            try:
                return f'{getattr(tenant_context, 'tenant_id', 'unknown')}:{getattr(tenant_context, 'workspace_id', 'unknown')}'
            except Exception:
                pass
        return None

    def _check_caches(self, context: RouteContext) -> RouteResult | None:
        """Check both semantic and traditional caches."""
        semantic_result = self.cache_manager.get_semantic_cache_result(context.prompt, context.model, context.namespace, getattr(self, 'semantic_cache_shadow_mode', False), getattr(self, 'semantic_cache_promotion_enabled', False), getattr(self, 'semantic_cache_promotion_threshold', 0.9))
        if semantic_result:
            return semantic_result
        traditional_result = self.cache_manager.get_traditional_cache_result(context.cache_key, context.model)
        if traditional_result:
            return traditional_result
        return None

    def _generate_cache_key(self, prompt: str, model: str, provider: dict[str, Any]) -> str:
        """Generate cache key for traditional cache."""
        import hashlib

        def _sig(obj: Any) -> str:
            if isinstance(obj, dict):
                return '{' + ','.join((f'{k}:{_sig(obj[k])}' for k in sorted(obj))) + '}'
            if isinstance(obj, list):
                return '[' + ','.join((_sig(x) for x in obj)) + ']'
            return str(obj)
        provider_sig = _sig(provider) if provider else '{}'
        key_string = f'{prompt}|provider={provider_sig}'
        digest = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
        return f'{model}:{digest}'

    def _is_offline_mode(self) -> bool:
        """Check if service is in offline mode."""
        return not bool(self.api_key)

    def _convert_to_dict(self, result: RouteResult) -> dict[str, Any]:
        """Convert RouteResult to dictionary for caching."""
        return {'status': result.status, 'model': result.model, 'response': result.response, 'tokens': result.tokens, 'provider': result.provider, 'cached': result.cached, 'cache_type': result.cache_type}

    def _convert_to_step_result(self, result: RouteResult) -> StepResult:
        """Convert RouteResult to StepResult."""
        if result.status == 'success':
            return StepResult.ok(data=self._convert_to_dict(result))
        else:
            return StepResult.fail(result.error or 'Unknown error')