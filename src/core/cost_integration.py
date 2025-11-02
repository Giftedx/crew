"""Integration layer for cost monitoring, alerting, and optimization.

This module provides a unified interface that integrates the existing
BudgetManager, CostOptimizer, and the new CostAlertManager.
"""
from __future__ import annotations
import logging
import time
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)

class CostMonitoringIntegration:
    """Unified cost monitoring, alerting, and optimization integration."""

    def __init__(self) -> None:
        from .cost_alerts import AlertThresholds, get_cost_alert_manager
        from .cost_optimizer import get_cost_optimizer
        from .token_meter import BudgetError, budget
        self.budget_store = budget
        self.cost_optimizer = get_cost_optimizer()
        self.alert_manager = get_cost_alert_manager()
        self.BudgetError = BudgetError
        self.alert_thresholds = AlertThresholds(budget_warning_percent=75.0, budget_critical_percent=90.0, budget_emergency_percent=95.0, cost_spike_multiplier=3.0, cost_spike_window_minutes=15, high_cost_request_usd=0.1, daily_warning_percent=80.0, daily_critical_percent=95.0, model_cost_anomaly_multiplier=2.5)

    def process_request_with_monitoring(self, model: str, tokens_input: int, tokens_output: int, component: str='unknown', tenant_id: str='default', workspace_id: str='main', check_alerts: bool=True) -> StepResult:
        """Process a request with comprehensive cost monitoring and alerting."""
        try:
            cost_usd = self.cost_optimizer.calculate_cost(model, tokens_input, tokens_output)
            try:
                self.budget_store.preflight(cost_usd)
            except self.BudgetError as e:
                return StepResult.fail(f'Budget preflight failed: {e!s}')
            cost_result = self.cost_optimizer.record_cost(component=component, operation='request_processing', model=model, tokens_input=tokens_input, tokens_output=tokens_output, cache_hit=False, optimization_applied='')
            if not cost_result.success:
                logger.warning(f'Cost recording failed: {cost_result.error}')
            if check_alerts:
                try:
                    budget_manager = self.budget_store._get()
                    alert_result = self.alert_manager.check_cost_alerts(cost_usd=cost_usd, model=model, component=component, tenant_id=tenant_id, workspace_id=workspace_id, budget_manager=budget_manager, cost_optimizer=self.cost_optimizer)
                    if not alert_result.success:
                        logger.warning(f'Cost alert checking failed: {alert_result.error}')
                except Exception as e:
                    logger.error(f'Alert checking failed: {e}')
            self.budget_store.charge(cost_usd)
            return StepResult.ok(data={'cost_usd': cost_usd, 'model': model, 'tokens_input': tokens_input, 'tokens_output': tokens_output, 'component': component, 'tenant_id': tenant_id, 'workspace_id': workspace_id, 'budget_remaining': self.budget_store._get().daily_budget - self.budget_store._get().spent_today})
        except Exception as e:
            logger.error(f'Cost monitoring integration failed: {e}')
            return StepResult.fail(f'Cost monitoring failed: {e!s}')

    def get_comprehensive_cost_report(self, tenant_id: str | None=None, workspace_id: str | None=None) -> StepResult:
        """Get comprehensive cost report including metrics, alerts, and recommendations."""
        try:
            cost_analysis = self.cost_optimizer.analyze_cost_patterns()
            if not cost_analysis.success:
                return cost_analysis
            recommendations = self.cost_optimizer.get_optimization_recommendations()
            if not recommendations.success:
                recommendations = StepResult.ok(data={'optimization_recommendations': []})
            alert_summary = self.alert_manager.get_alert_summary(tenant_id, workspace_id)
            if not alert_summary.success:
                alert_summary = StepResult.ok(data={'total_alerts': 0, 'recent_alerts_24h': 0, 'severity_breakdown': {}, 'alert_type_breakdown': {}, 'latest_alerts': []})
            budget_manager = self.budget_store._get()
            daily_spend = budget_manager.spent_today
            daily_budget = budget_manager.daily_budget
            daily_utilization = daily_spend / daily_budget * 100 if daily_budget > 0 else 0
            return StepResult.ok(data={'cost_analysis': cost_analysis.data, 'optimization_recommendations': recommendations.data.get('optimization_recommendations', []), 'alert_summary': alert_summary.data, 'budget_status': {'daily_spend_usd': daily_spend, 'daily_budget_usd': daily_budget, 'daily_utilization_percent': daily_utilization, 'per_request_limit_usd': budget_manager.max_per_request, 'budget_status': self._get_budget_status(daily_utilization)}, 'timestamp': time.time()})
        except Exception as e:
            logger.error(f'Comprehensive cost report generation failed: {e}')
            return StepResult.fail(f'Cost report generation failed: {e!s}')

    def _get_budget_status(self, utilization_percent: float) -> str:
        """Get budget status based on utilization."""
        if utilization_percent >= self.alert_thresholds.budget_emergency_percent:
            return 'emergency'
        elif utilization_percent >= self.alert_thresholds.budget_critical_percent:
            return 'critical'
        elif utilization_percent >= self.alert_thresholds.budget_warning_percent:
            return 'warning'
        else:
            return 'healthy'

    def simulate_optimization_impact(self, strategy: str) -> StepResult:
        """Simulate the impact of optimization strategies."""
        try:
            return self.cost_optimizer.simulate_optimization_impact(strategy)
        except Exception as e:
            logger.error(f'Optimization simulation failed: {e}')
            return StepResult.fail(f'Optimization simulation failed: {e!s}')

    def health_check(self) -> StepResult:
        """Comprehensive health check for all cost monitoring systems."""
        try:
            budget_manager = self.budget_store._get()
            optimizer_health = self.cost_optimizer.health_check()
            alert_health = self.alert_manager.health_check()
            return StepResult.ok(data={'cost_monitoring_integration_healthy': True, 'budget_store': {'daily_spend': budget_manager.spent_today, 'daily_budget': budget_manager.daily_budget, 'per_request_limit': budget_manager.max_per_request, 'utilization_percent': budget_manager.spent_today / budget_manager.daily_budget * 100}, 'cost_optimizer': optimizer_health.data if optimizer_health.success else {'healthy': False}, 'alert_manager': alert_health.data if alert_health.success else {'healthy': False}, 'timestamp': time.time()})
        except Exception as e:
            logger.error(f'Cost monitoring health check failed: {e}')
            return StepResult.fail(f'Health check failed: {e!s}')
_cost_monitoring_integration: CostMonitoringIntegration | None = None

def get_cost_monitoring_integration() -> CostMonitoringIntegration:
    """Get the global cost monitoring integration instance."""
    global _cost_monitoring_integration
    if _cost_monitoring_integration is None:
        _cost_monitoring_integration = CostMonitoringIntegration()
    return _cost_monitoring_integration
__all__ = ['CostMonitoringIntegration', 'get_cost_monitoring_integration']