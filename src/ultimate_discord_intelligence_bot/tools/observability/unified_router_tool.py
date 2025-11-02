"""Unified Router Tool - CrewAI tool for unified LLM routing

This tool provides CrewAI agents with access to the unified routing system,
enabling intelligent model selection, cost optimization, and budget management
across all routing backends.
"""
from __future__ import annotations
import logging
import time
from typing import Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from platform.observability.metrics import get_metrics
from ultimate_discord_intelligence_bot.routing import RoutingRequest, UnifiedCostTracker, UnifiedRouterConfig, UnifiedRouterService
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class UnifiedRouterInput(BaseModel):
    """Input schema for unified router tool"""
    prompt: str = Field(..., description='The prompt to route')
    task_type: str = Field(default='general', description='Type of task (general, analysis, creative, etc.)')
    quality_requirement: str = Field(default='balanced', description='Quality requirement: fast, balanced, high_quality')
    budget_limit: float | None = Field(default=None, description='Maximum cost for this request')
    max_tokens: int | None = Field(default=None, description='Maximum tokens to generate')
    temperature: float | None = Field(default=None, description='Temperature for generation')
    context: dict[str, Any] | None = Field(default=None, description='Additional context for routing')

class CostTrackingInput(BaseModel):
    """Input schema for cost tracking operations"""
    operation: str = Field(..., description='Operation: set_budget, get_status, record_cost, get_analytics')
    tenant_id: str = Field(..., description='Tenant identifier')
    workspace_id: str = Field(..., description='Workspace identifier')
    daily_limit: float | None = Field(default=None, description='Daily budget limit')
    monthly_limit: float | None = Field(default=None, description='Monthly budget limit')
    per_request_limit: float | None = Field(default=None, description='Per-request budget limit')
    model: str | None = Field(default=None, description='Model used (for cost recording)')
    provider: str | None = Field(default=None, description='Provider used (for cost recording)')
    cost: float | None = Field(default=None, description='Cost to record')
    tokens_used: int | None = Field(default=None, description='Tokens used (for cost recording)')
    days: int | None = Field(default=30, description='Days for analytics (default: 30)')

class UnifiedRouterTool(BaseTool):
    """Unified router tool for CrewAI agents"""
    name: str = 'unified_router_tool'
    description: str = 'Provides intelligent LLM routing with cost optimization and budget management. Routes requests through the best available model based on quality requirements, budget constraints, and performance history. Integrates OpenRouter, RL Model Router, Learning Engine, and other routing backends into a single unified system.'
    args_schema: type[BaseModel] = UnifiedRouterInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            router_config = UnifiedRouterConfig(enable_openrouter=True, enable_rl_router=True, enable_learning_engine=True, enable_cost_tracking=True, enable_performance_monitoring=True, default_budget_limit=10.0, quality_threshold=0.7, fallback_strategy='cost_optimized')
            self._router_service = UnifiedRouterService(router_config)
            self._cost_tracker = UnifiedCostTracker()
            logger.info('Unified router tool initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize unified router tool: {e}')
            self._router_service = None
            self._cost_tracker = None

    def _run(self, prompt: str, task_type: str='general', quality_requirement: str='balanced', budget_limit: float | None=None, max_tokens: int | None=None, temperature: float | None=None, context: dict[str, Any] | None=None, tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Execute unified routing request"""
        metrics = get_metrics()
        start_time = time.time()
        try:
            if not self._router_service:
                return StepResult.fail('Unified router service not initialized')
            routing_request = RoutingRequest(prompt=prompt, task_type=task_type, quality_requirement=quality_requirement, budget_limit=budget_limit, max_tokens=max_tokens, temperature=temperature, context=context, tenant_id=tenant_id, workspace_id=workspace_id)
            if self._cost_tracker and budget_limit:
                compliance_check = self._cost_tracker.check_budget_compliance(tenant_id, workspace_id, budget_limit)
                if not compliance_check.success:
                    return StepResult.fail(f'Budget compliance check failed: {compliance_check.error}')
            import asyncio
            result = asyncio.run(self._router_service.route_request(routing_request, tenant_id, workspace_id))
            if not result.success:
                return StepResult.fail(f'Routing failed: {result.error}')
            routing_result = result.data
            if self._cost_tracker:
                cost_record_result = self._cost_tracker.record_cost(tenant_id=tenant_id, workspace_id=workspace_id, model=routing_result.selected_model, provider=routing_result.provider, cost=float(routing_result.estimated_cost), tokens_used=None, request_type='routing', metadata={'task_type': task_type, 'quality_requirement': quality_requirement, 'routing_method': routing_result.routing_method, 'confidence_score': routing_result.confidence_score, 'fallback_used': routing_result.fallback_used})
                if not cost_record_result.success:
                    logger.warning(f'Failed to record cost: {cost_record_result.error}')
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'success'})
            return StepResult.ok(data={'selected_model': routing_result.selected_model, 'provider': routing_result.provider, 'estimated_cost': float(routing_result.estimated_cost), 'confidence_score': routing_result.confidence_score, 'routing_method': routing_result.routing_method, 'fallback_used': routing_result.fallback_used, 'metadata': routing_result.metadata, 'timestamp': routing_result.timestamp.isoformat()})
        except Exception as e:
            logger.error(f'Error in unified router tool: {e}', exc_info=True)
            metrics.counter('tool_runs_total', labels={'tool': self.__class__.__name__, 'outcome': 'error'})
            return StepResult.fail(f'Unified routing failed: {e!s}', error_context={'exception': str(e)})
        finally:
            metrics.histogram('tool_run_seconds', time.time() - start_time, labels={'tool': self.__class__.__name__})

class CostTrackingTool(BaseTool):
    """Cost tracking tool for CrewAI agents"""
    name: str = 'cost_tracking_tool'
    description: str = 'Manages cost tracking, budget limits, and spending analytics across all routing systems. Provides budget management, cost recording, compliance checking, and spending analytics for tenant/workspace isolation and cost optimization.'
    args_schema: type[BaseModel] = CostTrackingInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self._cost_tracker = UnifiedCostTracker()
            logger.info('Cost tracking tool initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize cost tracking tool: {e}')
            self._cost_tracker = None

    def _run(self, operation: str, tenant_id: str, workspace_id: str, daily_limit: float | None=None, monthly_limit: float | None=None, per_request_limit: float | None=None, model: str | None=None, provider: str | None=None, cost: float | None=None, tokens_used: int | None=None, days: int=30) -> StepResult:
        """Execute cost tracking operation"""
        try:
            if not self._cost_tracker:
                return StepResult.fail('Cost tracker not initialized')
            if operation == 'set_budget':
                if daily_limit is None or monthly_limit is None:
                    return StepResult.fail('Daily and monthly limits are required for set_budget')
                result = self._cost_tracker.set_budget(tenant_id=tenant_id, workspace_id=workspace_id, daily_limit=daily_limit, monthly_limit=monthly_limit, per_request_limit=per_request_limit or 1.0)
                return result
            elif operation == 'get_status':
                result = self._cost_tracker.get_budget_status(tenant_id=tenant_id, workspace_id=workspace_id)
                if result.success:
                    status = result.data
                    return StepResult.ok(data={'daily_spent': float(status.daily_spent), 'monthly_spent': float(status.monthly_spent), 'daily_remaining': float(status.daily_remaining), 'monthly_remaining': float(status.monthly_remaining), 'daily_limit': float(status.daily_limit), 'monthly_limit': float(status.monthly_limit), 'alert_level': status.alert_level, 'last_reset': status.last_reset.isoformat(), 'next_reset': status.next_reset.isoformat()})
                else:
                    return result
            elif operation == 'record_cost':
                if model is None or provider is None or cost is None:
                    return StepResult.fail('Model, provider, and cost are required for record_cost')
                result = self._cost_tracker.record_cost(tenant_id=tenant_id, workspace_id=workspace_id, model=model, provider=provider, cost=cost, tokens_used=tokens_used)
                return result
            elif operation == 'get_analytics':
                result = self._cost_tracker.get_cost_analytics(tenant_id=tenant_id, workspace_id=workspace_id, days=days)
                return result
            else:
                return StepResult.fail(f'Unknown operation: {operation}')
        except Exception as e:
            logger.error(f'Error in cost tracking tool: {e}', exc_info=True)
            return StepResult.fail(f'Cost tracking failed: {e!s}', error_context={'exception': str(e)})

class RouterStatusTool(BaseTool):
    """Router status tool for CrewAI agents"""
    name: str = 'router_status_tool'
    description: str = 'Provides status information about the unified router system including available backends, performance metrics, and system health.'
    args_schema: type[BaseModel] = BaseModel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            router_config = UnifiedRouterConfig()
            self._router_service = UnifiedRouterService(router_config)
            self._cost_tracker = UnifiedCostTracker()
            logger.info('Router status tool initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize router status tool: {e}')
            self._router_service = None
            self._cost_tracker = None

    def _run(self, tenant_id: str='default', workspace_id: str='main') -> StepResult:
        """Get router system status"""
        try:
            status_info = {}
            if self._router_service:
                status_info['router_status'] = self._router_service.get_router_status()
                performance_metrics = self._router_service.get_performance_metrics(tenant_id=tenant_id, workspace_id=workspace_id)
                status_info['performance_metrics'] = performance_metrics
            if self._cost_tracker:
                budget_status = self._cost_tracker.get_budget_status(tenant_id=tenant_id, workspace_id=workspace_id)
                if budget_status.success:
                    status_info['budget_status'] = {'daily_spent': float(budget_status.data.daily_spent), 'monthly_spent': float(budget_status.data.monthly_spent), 'daily_remaining': float(budget_status.data.daily_remaining), 'monthly_remaining': float(budget_status.data.monthly_remaining), 'alert_level': budget_status.data.alert_level}
                else:
                    status_info['budget_status'] = {'error': budget_status.error}
            return StepResult.ok(data=status_info)
        except Exception as e:
            logger.error(f'Error in router status tool: {e}', exc_info=True)
            return StepResult.fail(f'Status retrieval failed: {e!s}', error_context={'exception': str(e)})