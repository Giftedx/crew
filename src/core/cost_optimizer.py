"""Cost optimization and budget management for the multi-agent orchestration platform.

This module provides comprehensive cost tracking, optimization strategies,
and budget enforcement across all components of the orchestration platform.
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

@dataclass
class CostMetrics:
    """Cost metrics for tracking spend and optimization opportunities."""
    component: str
    operation: str
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    model_used: str = ''
    cache_hit: bool = False
    optimization_applied: str = ''
    timestamp: float = field(default_factory=time.time)

@dataclass
class BudgetConfig:
    """Budget configuration for cost management."""
    daily_budget_usd: float = 100.0
    per_request_max_usd: float = 1.0
    alert_threshold_percent: float = 80.0
    tenant_budget_usd: float = 50.0
    workspace_budget_usd: float = 25.0

class CostOptimizer:
    """Comprehensive cost optimization and budget management system."""

    def __init__(self):
        self.cost_history: list[CostMetrics] = []
        self.budget_config = BudgetConfig()
        self.model_pricing = {'gpt-4': {'input': 0.03 / 1000, 'output': 0.06 / 1000}, 'gpt-4-turbo': {'input': 0.01 / 1000, 'output': 0.03 / 1000}, 'gpt-3.5-turbo': {'input': 0.001 / 1000, 'output': 0.002 / 1000}, 'gpt-3.5': {'input': 0.001 / 1000, 'output': 0.002 / 1000}, 'claude-3-opus': {'input': 0.015 / 1000, 'output': 0.075 / 1000}, 'claude-3-sonnet': {'input': 0.003 / 1000, 'output': 0.015 / 1000}, 'claude-3-haiku': {'input': 0.00025 / 1000, 'output': 0.00125 / 1000}, 'gemini-pro': {'input': 0.0005 / 1000, 'output': 0.0015 / 1000}, 'gemini-pro-vision': {'input': 0.0005 / 1000, 'output': 0.0015 / 1000}, 'llama-2-70b': {'input': 0.0003 / 1000, 'output': 0.0003 / 1000}, 'llama-3-70b': {'input': 0.0004 / 1000, 'output': 0.0004 / 1000}, 'default': {'input': 0.001 / 1000, 'output': 0.002 / 1000}}
        self.optimization_strategies = ['prompt_compression', 'cache_utilization', 'model_selection', 'batch_processing', 'streaming_responses']

    def calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost for a specific model and token usage."""
        try:
            if model not in self.model_pricing:
                logger.warning(f'Unknown model pricing for {model}, using gpt-3.5-turbo rates')
                model = 'gpt-3.5-turbo'
            pricing = self.model_pricing[model]
            input_cost = tokens_input * pricing['input']
            output_cost = tokens_output * pricing['output']
            return input_cost + output_cost
        except Exception as e:
            logger.error(f'Cost calculation failed: {e}')
            return 0.0

    def record_cost(self, component: str, operation: str, model: str, tokens_input: int, tokens_output: int, cache_hit: bool=False, optimization_applied: str='') -> StepResult:
        """Record cost metrics for analysis and optimization."""
        try:
            cost_usd = self.calculate_cost(model, tokens_input, tokens_output)
            metrics = CostMetrics(component=component, operation=operation, tokens_input=tokens_input, tokens_output=tokens_output, cost_usd=cost_usd, model_used=model, cache_hit=cache_hit, optimization_applied=optimization_applied)
            self.cost_history.append(metrics)
            budget_check = self.check_budget_constraints(cost_usd)
            if not budget_check.success:
                return budget_check
            return StepResult.ok(data={'cost_recorded': cost_usd, 'metrics': metrics.__dict__, 'budget_status': 'within_limits'})
        except Exception as e:
            logger.error(f'Cost recording failed: {e}')
            return StepResult.fail(f'Cost recording failed: {e!s}')

    def check_budget_constraints(self, cost_usd: float) -> StepResult:
        """Check if cost exceeds budget constraints."""
        try:
            if cost_usd > self.budget_config.per_request_max_usd:
                return StepResult.fail(f'Request cost (${cost_usd:.4f}) exceeds per-request limit (${self.budget_config.per_request_max_usd:.4f})')
            daily_spend = self.get_daily_spend()
            if daily_spend + cost_usd > self.budget_config.daily_budget_usd:
                return StepResult.fail(f'Request would exceed daily budget (${daily_spend:.2f} + ${cost_usd:.4f} > ${self.budget_config.daily_budget_usd:.2f})')
            return StepResult.ok(data={'budget_check': 'passed'})
        except Exception as e:
            logger.error(f'Budget constraint check failed: {e}')
            return StepResult.fail(f'Budget check failed: {e!s}')

    def get_daily_spend(self) -> float:
        """Calculate total spend for the current day."""
        try:
            today = time.time() - 24 * 60 * 60
            daily_costs = [metrics.cost_usd for metrics in self.cost_history if metrics.timestamp >= today]
            return sum(daily_costs)
        except Exception as e:
            logger.error(f'Daily spend calculation failed: {e}')
            return 0.0

    def analyze_cost_patterns(self) -> StepResult:
        """Analyze cost patterns and identify optimization opportunities."""
        try:
            if not self.cost_history:
                return StepResult.fail('No cost data available for analysis')
            component_costs = {}
            model_costs = {}
            cache_impact = {'hits': 0, 'misses': 0, 'hit_savings': 0.0}
            for metrics in self.cost_history:
                if metrics.component not in component_costs:
                    component_costs[metrics.component] = []
                component_costs[metrics.component].append(metrics.cost_usd)
                if metrics.model_used not in model_costs:
                    model_costs[metrics.model_used] = []
                model_costs[metrics.model_used].append(metrics.cost_usd)
                if metrics.cache_hit:
                    cache_impact['hits'] += 1
                    cache_impact['hit_savings'] += metrics.cost_usd * 0.8
                else:
                    cache_impact['misses'] += 1
            total_cost = sum((metrics.cost_usd for metrics in self.cost_history))
            avg_cost_per_request = total_cost / len(self.cost_history)
            component_totals = {comp: sum(costs) for comp, costs in component_costs.items()}
            highest_cost_component = max(component_totals.items(), key=lambda x: x[1])
            model_totals = {model: sum(costs) for model, costs in model_costs.items()}
            most_expensive_model = max(model_totals.items(), key=lambda x: x[1])
            total_requests = len(self.cost_history)
            cache_hit_rate = cache_impact['hits'] / total_requests if total_requests > 0 else 0
            return StepResult.ok(data={'cost_analysis': {'total_cost_usd': total_cost, 'total_requests': total_requests, 'average_cost_per_request': avg_cost_per_request, 'daily_spend': self.get_daily_spend()}, 'component_breakdown': component_totals, 'model_breakdown': model_totals, 'highest_cost_component': {'component': highest_cost_component[0], 'cost_usd': highest_cost_component[1], 'percentage': highest_cost_component[1] / total_cost * 100}, 'most_expensive_model': {'model': most_expensive_model[0], 'cost_usd': most_expensive_model[1], 'percentage': most_expensive_model[1] / total_cost * 100}, 'cache_impact': {'hit_rate': cache_hit_rate, 'estimated_savings_usd': cache_impact['hit_savings'], 'hits': cache_impact['hits'], 'misses': cache_impact['misses']}})
        except Exception as e:
            logger.error(f'Cost pattern analysis failed: {e}')
            return StepResult.fail(f'Cost analysis failed: {e!s}')

    def get_optimization_recommendations(self) -> StepResult:
        """Get cost optimization recommendations based on analysis."""
        try:
            analysis = self.analyze_cost_patterns()
            if not analysis.success:
                return analysis
            data = analysis.data
            recommendations = []
            cache_hit_rate = data['cache_impact']['hit_rate']
            if cache_hit_rate < 0.6:
                recommendations.append({'type': 'cache_optimization', 'priority': 'high', 'description': f'Cache hit rate is {cache_hit_rate:.1%}, target is 60%+', 'potential_savings': '20-40% of total cost', 'action': 'Implement prompt compression and semantic caching'})
            most_expensive = data['most_expensive_model']
            if most_expensive['percentage'] > 50:
                recommendations.append({'type': 'model_optimization', 'priority': 'high', 'description': f'{most_expensive['model']} accounts for {most_expensive['percentage']:.1f}% of costs', 'potential_savings': f'${most_expensive['cost_usd'] * 0.3:.2f}', 'action': f'Consider routing simple tasks to cheaper models instead of {most_expensive['model']}'})
            highest_cost_comp = data['highest_cost_component']
            if highest_cost_comp['percentage'] > 40:
                recommendations.append({'type': 'component_optimization', 'priority': 'medium', 'description': f'{highest_cost_comp['component']} is the highest cost component', 'potential_savings': f'${highest_cost_comp['cost_usd'] * 0.2:.2f}', 'action': f'Optimize {highest_cost_comp['component']} operations and caching'})
            daily_spend = data['cost_analysis']['daily_spend']
            if daily_spend > self.budget_config.daily_budget_usd * 0.8:
                recommendations.append({'type': 'budget_optimization', 'priority': 'high', 'description': f'Daily spend (${daily_spend:.2f}) approaching budget limit', 'potential_savings': f'${daily_spend * 0.25:.2f}', 'action': 'Implement request throttling and cost-aware routing'})
            avg_cost = data['cost_analysis']['average_cost_per_request']
            if avg_cost > 0.01:
                recommendations.append({'type': 'prompt_optimization', 'priority': 'medium', 'description': f'Average cost per request is ${avg_cost:.4f}', 'potential_savings': '15-30% of token costs', 'action': 'Implement prompt compression and template optimization'})
            return StepResult.ok(data={'optimization_recommendations': recommendations, 'total_recommendations': len(recommendations), 'high_priority_count': sum((1 for r in recommendations if r['priority'] == 'high')), 'estimated_total_savings': sum((float(r['potential_savings'].replace('$', '').replace('%', '')) for r in recommendations if '$' in r['potential_savings']))})
        except Exception as e:
            logger.error(f'Optimization recommendations failed: {e}')
            return StepResult.fail(f'Recommendations failed: {e!s}')

    def simulate_optimization_impact(self, strategy: str) -> StepResult:
        """Simulate the impact of a specific optimization strategy."""
        try:
            analysis = self.analyze_cost_patterns()
            if not analysis.success:
                return analysis
            data = analysis.data
            total_cost = data['cost_analysis']['total_cost_usd']
            savings_estimates = {'prompt_compression': 0.25, 'cache_utilization': 0.3, 'model_selection': 0.2, 'batch_processing': 0.15, 'streaming_responses': 0.1}
            if strategy not in savings_estimates:
                return StepResult.fail(f'Unknown optimization strategy: {strategy}')
            savings_percent = savings_estimates[strategy]
            estimated_savings = total_cost * savings_percent
            new_total_cost = total_cost - estimated_savings
            return StepResult.ok(data={'optimization_strategy': strategy, 'current_total_cost': total_cost, 'estimated_savings': estimated_savings, 'new_total_cost': new_total_cost, 'savings_percentage': savings_percent * 100, 'roi_estimate': f'{estimated_savings / (total_cost * 0.1) * 100:.1f}%'})
        except Exception as e:
            logger.error(f'Optimization simulation failed: {e}')
            return StepResult.fail(f'Simulation failed: {e!s}')

    def health_check(self) -> StepResult:
        """Health check for the cost optimizer."""
        try:
            return StepResult.ok(data={'cost_optimizer_healthy': True, 'cost_records': len(self.cost_history), 'models_tracked': len(self.model_pricing), 'optimization_strategies': len(self.optimization_strategies), 'daily_budget': self.budget_config.daily_budget_usd, 'daily_spend': self.get_daily_spend(), 'budget_utilization': self.get_daily_spend() / self.budget_config.daily_budget_usd * 100, 'timestamp': time.time()})
        except Exception as e:
            logger.error(f'Cost optimizer health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')
_cost_optimizer: CostOptimizer | None = None

def get_cost_optimizer() -> CostOptimizer:
    """Get the global cost optimizer instance."""
    global _cost_optimizer
    if _cost_optimizer is None:
        _cost_optimizer = CostOptimizer()
    return _cost_optimizer