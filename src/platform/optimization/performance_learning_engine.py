"""
Performance Learning Engine - Continuous System Optimization

This service orchestrates cache and model routing optimization, providing
request-level and system-level optimization with automated tuning.
"""
from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from platform.core.step_result import StepResult
from typing import Any

import numpy as np

from .rl_cache_optimizer import CacheContext, RLCacheOptimizer
from .rl_model_router import RLModelRouter, RoutingContext, TaskComplexity


logger = logging.getLogger(__name__)

class OptimizationLevel(Enum):
    """Optimization level enumeration."""
    REQUEST = 'request'
    BATCH = 'batch'
    SYSTEM = 'system'
    TENANT = 'tenant'

class OptimizationGoal(Enum):
    """Optimization goal enumeration."""
    LATENCY = 'latency'
    COST = 'cost'
    QUALITY = 'quality'
    THROUGHPUT = 'throughput'
    BALANCED = 'balanced'

@dataclass
class OptimizationRequest:
    """Request for system optimization."""
    request_id: str
    optimization_level: OptimizationLevel
    goals: list[OptimizationGoal]
    context: dict[str, Any]
    constraints: dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    tenant: str = ''
    workspace: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    """Result of optimization process."""
    request_id: str
    success: bool
    optimizations_applied: list[dict[str, Any]]
    performance_improvements: dict[str, float]
    estimated_impact: dict[str, Any]
    recommendations: list[dict[str, Any]]
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_rate_per_second: float = 0.0
    average_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    model_routing_accuracy: float = 0.0
    cost_per_request_usd: float = 0.0
    throughput_per_second: float = 0.0
    resource_utilization: dict[str, float] = field(default_factory=dict)

class PerformanceLearningEngine:
    """Performance learning engine for continuous system optimization."""

    def __init__(self):
        """Initialize the performance learning engine."""
        self.model_router = RLModelRouter()
        self.cache_optimizer = RLCacheOptimizer()
        self.optimization_history: list[OptimizationResult] = []
        self.system_metrics_history: list[SystemMetrics] = []
        self.performance_baselines: dict[str, float] = {}
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        self.optimization_frequency = 300
        self.last_optimization = datetime.utcnow()
        self.performance_targets = {'latency_p95_ms': 2000.0, 'error_rate': 0.01, 'cache_hit_rate': 0.6, 'cost_per_request_usd': 0.001, 'throughput_per_second': 100.0}
        self._initialize_baselines()

    async def optimize_request(self, request: OptimizationRequest) -> StepResult:
        """
        Optimize a single request using RL-based routing and caching.

        Args:
            request: Optimization request

        Returns:
            StepResult with optimization results
        """
        try:
            start_time = datetime.utcnow()
            routing_context = self._extract_routing_context(request)
            cache_context = self._extract_cache_context(request)
            optimizations_applied = []
            performance_improvements = {}
            if 'model_routing' in request.goals or OptimizationGoal.BALANCED in request.goals:
                routing_result = await self.model_router.route_request(routing_context)
                if routing_result.success:
                    optimizations_applied.append({'type': 'model_routing', 'details': routing_result.data, 'impact': 'latency_and_cost'})
            if 'cache_optimization' in request.goals or OptimizationGoal.BALANCED in request.goals:
                cache_result = await self.cache_optimizer.optimize_cache_operation(cache_context, 'store')
                if cache_result.success:
                    optimizations_applied.append({'type': 'cache_optimization', 'details': cache_result.data, 'impact': 'latency_and_cost'})
            performance_improvements = self._calculate_performance_improvements(request, optimizations_applied)
            recommendations = self._generate_optimization_recommendations(request, optimizations_applied, performance_improvements)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result = OptimizationResult(request_id=request.request_id, success=len(optimizations_applied) > 0, optimizations_applied=optimizations_applied, performance_improvements=performance_improvements, estimated_impact=self._estimate_impact(optimizations_applied), recommendations=recommendations, execution_time_ms=execution_time)
            self.optimization_history.append(result)
            return StepResult.ok(data={'optimization_result': result, 'request': request, 'optimization_metadata': {'engine_version': '1.0', 'optimization_timestamp': datetime.utcnow().isoformat()}})
        except Exception as e:
            logger.error(f'Request optimization failed: {e!s}')
            return StepResult.fail(f'Request optimization failed: {e!s}')

    async def optimize_system(self, system_metrics: SystemMetrics) -> StepResult:
        """
        Perform system-wide optimization based on current metrics.

        Args:
            system_metrics: Current system performance metrics

        Returns:
            StepResult with system optimization results
        """
        try:
            self.system_metrics_history.append(system_metrics)
            performance_analysis = self._analyze_system_performance(system_metrics)
            system_optimizations = []
            if performance_analysis['model_routing_needs_optimization']:
                routing_optimization = await self._optimize_model_routing_system(system_metrics)
                if routing_optimization:
                    system_optimizations.append(routing_optimization)
            if performance_analysis['cache_needs_optimization']:
                cache_optimization = await self._optimize_cache_system(system_metrics)
                if cache_optimization:
                    system_optimizations.append(cache_optimization)
            if performance_analysis['resource_allocation_needs_optimization']:
                resource_optimization = self._optimize_resource_allocation(system_metrics)
                if resource_optimization:
                    system_optimizations.append(resource_optimization)
            result = OptimizationResult(request_id=f'system_opt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}', success=len(system_optimizations) > 0, optimizations_applied=system_optimizations, performance_improvements=self._calculate_system_improvements(system_optimizations), estimated_impact=self._estimate_system_impact(system_optimizations), recommendations=self._generate_system_recommendations(performance_analysis), execution_time_ms=0.0)
            self.optimization_history.append(result)
            return StepResult.ok(data={'system_optimization_result': result, 'performance_analysis': performance_analysis, 'system_metrics': system_metrics, 'optimization_metadata': {'optimization_type': 'system_wide', 'optimization_timestamp': datetime.utcnow().isoformat()}})
        except Exception as e:
            logger.error(f'System optimization failed: {e!s}')
            return StepResult.fail(f'System optimization failed: {e!s}')

    async def update_performance_feedback(self, feedback_data: dict[str, Any]) -> StepResult:
        """
        Update performance feedback for learning.

        Args:
            feedback_data: Performance feedback data

        Returns:
            StepResult with learning update status
        """
        try:
            if 'model_routing_feedback' in feedback_data:
                routing_feedback = feedback_data['model_routing_feedback']
                await self.model_router.update_reward(routing_feedback['model_id'], routing_feedback['task_id'], routing_feedback)
            if 'cache_feedback' in feedback_data:
                cache_feedback = feedback_data['cache_feedback']
                await self.cache_optimizer.update_cache_performance(cache_feedback['action'], cache_feedback)
            self._update_performance_baselines(feedback_data)
            if self._should_trigger_learning():
                await self._trigger_learning_cycle()
            return StepResult.ok(data={'feedback_processed': True, 'learning_triggered': self._should_trigger_learning(), 'updated_baselines': self.performance_baselines, 'feedback_timestamp': datetime.utcnow().isoformat()})
        except Exception as e:
            logger.error(f'Performance feedback update failed: {e!s}')
            return StepResult.fail(f'Performance feedback update failed: {e!s}')

    def get_optimization_statistics(self) -> StepResult:
        """
        Get comprehensive optimization statistics.

        Returns:
            StepResult with optimization statistics
        """
        try:
            router_stats = self.model_router.get_routing_statistics()
            cache_stats = self.cache_optimizer.get_cache_statistics()
            engine_stats = self._calculate_engine_statistics()
            return StepResult.ok(data={'engine_statistics': engine_stats, 'model_router_statistics': router_stats.data if router_stats.success else {}, 'cache_optimizer_statistics': cache_stats.data if cache_stats.success else {}, 'performance_baselines': self.performance_baselines, 'performance_targets': self.performance_targets, 'optimization_history_size': len(self.optimization_history), 'system_metrics_history_size': len(self.system_metrics_history)})
        except Exception as e:
            logger.error(f'Failed to get optimization statistics: {e!s}')
            return StepResult.fail(f'Failed to get optimization statistics: {e!s}')

    def _extract_routing_context(self, request: OptimizationRequest) -> StepResult:
        """Extract routing context from optimization request."""
        context_data = request.context
        return RoutingContext(task_type=context_data.get('task_type', 'general'), complexity=TaskComplexity(context_data.get('complexity', 'moderate')), token_estimate=context_data.get('token_estimate', 1000), latency_requirement_ms=context_data.get('latency_requirement_ms'), cost_budget_usd=context_data.get('cost_budget_usd'), quality_requirement=context_data.get('quality_requirement', 0.8), tenant=request.tenant, workspace=request.workspace, metadata=request.metadata)

    def _extract_cache_context(self, request: OptimizationRequest) -> StepResult:
        """Extract cache context from optimization request."""
        context_data = request.context
        return CacheContext(key_pattern=context_data.get('cache_key', 'default'), access_frequency=context_data.get('access_frequency', 1.0), data_size=context_data.get('data_size', 1000), time_since_last_access=context_data.get('time_since_last_access', 0.0), time_of_day=datetime.utcnow().hour, day_of_week=datetime.utcnow().weekday(), tenant=request.tenant, workspace=request.workspace, metadata=request.metadata)

    def _calculate_performance_improvements(self, request: OptimizationRequest, optimizations: list[dict[str, Any]]) -> StepResult:
        """Calculate estimated performance improvements."""
        improvements = {}
        for optimization in optimizations:
            if optimization['type'] == 'model_routing':
                improvements['latency_improvement'] = improvements.get('latency_improvement', 0) + 0.15
                improvements['cost_improvement'] = improvements.get('cost_improvement', 0) + 0.2
            elif optimization['type'] == 'cache_optimization':
                improvements['cache_hit_rate_improvement'] = improvements.get('cache_hit_rate_improvement', 0) + 0.1
                improvements['latency_improvement'] = improvements.get('latency_improvement', 0) + 0.25
        return improvements

    def _generate_optimization_recommendations(self, request: OptimizationRequest, optimizations: list[dict[str, Any]], improvements: dict[str, float]) -> StepResult:
        """Generate optimization recommendations."""
        recommendations = []
        if any(opt['type'] == 'model_routing' for opt in optimizations):
            recommendations.append({'type': 'model_routing', 'priority': 'high', 'description': 'Optimized model selection for better performance', 'expected_benefit': '15-20% latency reduction, 20-25% cost reduction'})
        if any(opt['type'] == 'cache_optimization' for opt in optimizations):
            recommendations.append({'type': 'cache_optimization', 'priority': 'medium', 'description': 'Improved cache strategy for faster access', 'expected_benefit': '10-15% cache hit rate improvement, 25-30% latency reduction'})
        if request.optimization_level == OptimizationLevel.SYSTEM:
            recommendations.append({'type': 'system_optimization', 'priority': 'high', 'description': 'System-wide optimization applied', 'expected_benefit': 'Overall system performance improvement'})
        return recommendations

    def _estimate_impact(self, optimizations: list[dict[str, Any]]) -> StepResult:
        """Estimate impact of optimizations."""
        total_impact = {'latency_reduction_percent': 0.0, 'cost_reduction_percent': 0.0, 'quality_improvement_percent': 0.0, 'throughput_improvement_percent': 0.0}
        for optimization in optimizations:
            if optimization['type'] == 'model_routing':
                total_impact['latency_reduction_percent'] += 15.0
                total_impact['cost_reduction_percent'] += 20.0
                total_impact['quality_improvement_percent'] += 5.0
            elif optimization['type'] == 'cache_optimization':
                total_impact['latency_reduction_percent'] += 25.0
                total_impact['throughput_improvement_percent'] += 10.0
        return total_impact

    def _analyze_system_performance(self, metrics: SystemMetrics) -> StepResult:
        """Analyze system performance against targets."""
        analysis = {'overall_health': 'good', 'model_routing_needs_optimization': False, 'cache_needs_optimization': False, 'resource_allocation_needs_optimization': False, 'performance_issues': []}
        if metrics.p95_latency_ms > self.performance_targets['latency_p95_ms']:
            analysis['performance_issues'].append('High P95 latency')
            analysis['model_routing_needs_optimization'] = True
        if metrics.error_rate > self.performance_targets['error_rate']:
            analysis['performance_issues'].append('High error rate')
            analysis['model_routing_needs_optimization'] = True
        if metrics.cache_hit_rate < self.performance_targets['cache_hit_rate']:
            analysis['performance_issues'].append('Low cache hit rate')
            analysis['cache_needs_optimization'] = True
        if metrics.cost_per_request_usd > self.performance_targets['cost_per_request_usd']:
            analysis['performance_issues'].append('High cost per request')
            analysis['model_routing_needs_optimization'] = True
        if metrics.throughput_per_second < self.performance_targets['throughput_per_second']:
            analysis['performance_issues'].append('Low throughput')
            analysis['resource_allocation_needs_optimization'] = True
        if len(analysis['performance_issues']) > 2:
            analysis['overall_health'] = 'poor'
        elif len(analysis['performance_issues']) > 0:
            analysis['overall_health'] = 'degraded'
        return analysis

    async def _optimize_model_routing_system(self, metrics: SystemMetrics) -> StepResult:
        """Optimize model routing system-wide."""
        if metrics.error_rate > 0.05:
            self.model_router.bandit.exploration_rate = min(0.2, self.model_router.bandit.exploration_rate + 0.05)
        elif metrics.error_rate < 0.01:
            self.model_router.bandit.exploration_rate = max(0.05, self.model_router.bandit.exploration_rate - 0.02)
        return {'type': 'model_routing_system', 'action': 'adjusted_exploration_rate', 'new_exploration_rate': self.model_router.bandit.exploration_rate, 'reasoning': 'System-wide model routing optimization'}

    async def _optimize_cache_system(self, metrics: SystemMetrics) -> StepResult:
        """Optimize cache system-wide."""
        if metrics.cache_hit_rate < 0.5:
            return {'type': 'cache_system', 'action': 'increase_cache_aggressiveness', 'reasoning': 'Low cache hit rate detected'}
        return None

    def _optimize_resource_allocation(self, metrics: SystemMetrics) -> StepResult:
        """Optimize resource allocation system-wide."""
        high_utilization_resources = [resource for resource, utilization in metrics.resource_utilization.items() if utilization > 0.8]
        if high_utilization_resources:
            return {'type': 'resource_allocation', 'action': 'scale_resources', 'high_utilization_resources': high_utilization_resources, 'reasoning': 'High resource utilization detected'}
        return None

    def _calculate_system_improvements(self, optimizations: list[dict[str, Any]]) -> StepResult:
        """Calculate system-wide improvements."""
        improvements = {}
        for optimization in optimizations:
            if optimization['type'] == 'model_routing_system':
                improvements['routing_accuracy'] = 0.05
            elif optimization['type'] == 'cache_system':
                improvements['cache_efficiency'] = 0.1
            elif optimization['type'] == 'resource_allocation':
                improvements['resource_efficiency'] = 0.15
        return improvements

    def _estimate_system_impact(self, optimizations: list[dict[str, Any]]) -> StepResult:
        """Estimate system-wide impact."""
        return {'expected_latency_improvement': '5-15%', 'expected_cost_reduction': '10-20%', 'expected_throughput_improvement': '10-25%', 'optimization_count': len(optimizations)}

    def _generate_system_recommendations(self, analysis: dict[str, Any]) -> StepResult:
        """Generate system-level recommendations."""
        recommendations = []
        if analysis['model_routing_needs_optimization']:
            recommendations.append({'type': 'model_routing', 'priority': 'high', 'description': 'Optimize model routing for better performance', 'action': 'Adjust model selection parameters'})
        if analysis['cache_needs_optimization']:
            recommendations.append({'type': 'cache_optimization', 'priority': 'medium', 'description': 'Improve cache hit rates', 'action': 'Adjust cache strategies and TTL'})
        if analysis['resource_allocation_needs_optimization']:
            recommendations.append({'type': 'resource_allocation', 'priority': 'high', 'description': 'Optimize resource allocation', 'action': 'Scale resources or redistribute load'})
        return recommendations

    def _update_performance_baselines(self, feedback_data: dict[str, Any]):
        """Update performance baselines with new feedback."""
        alpha = 0.1
        if 'latency_ms' in feedback_data:
            current_latency = self.performance_baselines.get('average_latency_ms', 1000.0)
            new_latency = feedback_data['latency_ms']
            self.performance_baselines['average_latency_ms'] = (1 - alpha) * current_latency + alpha * new_latency
        if 'cost_usd' in feedback_data:
            current_cost = self.performance_baselines.get('average_cost_usd', 0.001)
            new_cost = feedback_data['cost_usd']
            self.performance_baselines['average_cost_usd'] = (1 - alpha) * current_cost + alpha * new_cost
        if 'quality_score' in feedback_data:
            current_quality = self.performance_baselines.get('average_quality_score', 0.8)
            new_quality = feedback_data['quality_score']
            self.performance_baselines['average_quality_score'] = (1 - alpha) * current_quality + alpha * new_quality

    def _should_trigger_learning(self) -> StepResult:
        """Determine if learning should be triggered."""
        time_since_last = (datetime.utcnow() - self.last_optimization).total_seconds()
        return time_since_last >= self.optimization_frequency

    async def _trigger_learning_cycle(self):
        """Trigger a learning cycle."""
        self.last_optimization = datetime.utcnow()
        if len(self.optimization_history) > 10:
            recent_results = self.optimization_history[-10:]
            success_rate = sum(1 for r in recent_results if r.success) / len(recent_results)
            if success_rate > 0.8:
                self.exploration_rate = max(0.05, self.exploration_rate - 0.01)
            elif success_rate < 0.6:
                self.exploration_rate = min(0.2, self.exploration_rate + 0.02)

    def _calculate_engine_statistics(self) -> StepResult:
        """Calculate engine-level statistics."""
        if not self.optimization_history:
            return {'status': 'no_data'}
        total_optimizations = len(self.optimization_history)
        successful_optimizations = sum(1 for r in self.optimization_history if r.success)
        success_rate = successful_optimizations / total_optimizations
        all_improvements = [r.performance_improvements for r in self.optimization_history if r.performance_improvements]
        avg_improvements = {}
        if all_improvements:
            for key in all_improvements[0]:
                avg_improvements[key] = np.mean([imp.get(key, 0) for imp in all_improvements])
        return {'total_optimizations': total_optimizations, 'successful_optimizations': successful_optimizations, 'success_rate': success_rate, 'average_improvements': avg_improvements, 'learning_rate': self.learning_rate, 'exploration_rate': self.exploration_rate, 'last_optimization': self.last_optimization.isoformat()}

    def _initialize_baselines(self):
        """Initialize performance baselines."""
        self.performance_baselines = {'average_latency_ms': 1000.0, 'average_cost_usd': 0.001, 'average_quality_score': 0.8, 'cache_hit_rate': 0.6, 'error_rate': 0.01}

    def save_state(self, filepath: str) -> StepResult:
        """Save engine state to file."""
        try:
            router_state_result = self.model_router.save_state(f'{filepath}_router.pkl')
            if not router_state_result.success:
                logger.warning(f'Failed to save router state: {router_state_result.error}')
            cache_state_result = self.cache_optimizer.save_state(f'{filepath}_cache.pkl')
            if not cache_state_result.success:
                logger.warning(f'Failed to save cache state: {cache_state_result.error}')
            engine_state = {'optimization_history': self.optimization_history[-1000:], 'system_metrics_history': self.system_metrics_history[-1000:], 'performance_baselines': self.performance_baselines, 'learning_rate': self.learning_rate, 'exploration_rate': self.exploration_rate, 'last_optimization': self.last_optimization}
            with open(f'{filepath}_engine.pkl', 'wb') as f:
                pickle.dump(engine_state, f)
            return StepResult.ok(data={'saved_to': filepath})
        except Exception as e:
            logger.error(f'Failed to save engine state: {e!s}')
            return StepResult.fail(f'Failed to save engine state: {e!s}')

    def load_state(self, filepath: str) -> StepResult:
        """Load engine state from file."""
        try:
            router_state_result = self.model_router.load_state(f'{filepath}_router.pkl')
            if not router_state_result.success:
                logger.warning(f'Failed to load router state: {router_state_result.error}')
            cache_state_result = self.cache_optimizer.load_state(f'{filepath}_cache.pkl')
            if not cache_state_result.success:
                logger.warning(f'Failed to load cache state: {cache_state_result.error}')
            with open(f'{filepath}_engine.pkl', 'rb') as f:
                engine_state = pickle.load(f)
            self.optimization_history = engine_state.get('optimization_history', [])
            self.system_metrics_history = engine_state.get('system_metrics_history', [])
            self.performance_baselines = engine_state.get('performance_baselines', self.performance_baselines)
            self.learning_rate = engine_state.get('learning_rate', self.learning_rate)
            self.exploration_rate = engine_state.get('exploration_rate', self.exploration_rate)
            self.last_optimization = engine_state.get('last_optimization', datetime.utcnow())
            return StepResult.ok(data={'loaded_from': filepath})
        except Exception as e:
            logger.error(f'Failed to load engine state: {e!s}')
            return StepResult.fail(f'Failed to load engine state: {e!s}')
