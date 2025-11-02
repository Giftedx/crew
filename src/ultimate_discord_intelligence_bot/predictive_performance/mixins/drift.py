from __future__ import annotations
import logging
import statistics
try:
    from scipy import stats
except ImportError:
    stats = None
from typing import TYPE_CHECKING
from platform.time import default_utc_now
from ..models import ModelDriftAlert
if TYPE_CHECKING:
    from collections import deque
logger = logging.getLogger(__name__)

class DriftDetectionMixin:

    def _identify_drift_factors(self, baseline_data: list, recent_data: list) -> list[str]:
        factors: list[str] = []
        try:
            baseline_contexts = [p.get('context', {}) for p in baseline_data]
            recent_contexts = [p.get('context', {}) for p in recent_data]
            baseline_errors = sum((1 for ctx in baseline_contexts if ctx.get('error_occurred', False))) / len(baseline_contexts)
            recent_errors = sum((1 for ctx in recent_contexts if ctx.get('error_occurred', False))) / len(recent_contexts)
            if abs(recent_errors - baseline_errors) > 0.1:
                factors.append(f'Error rate changed from {baseline_errors:.1%} to {recent_errors:.1%}')
            baseline_tools: list[str] = []
            recent_tools: list[str] = []
            for ctx in baseline_contexts:
                baseline_tools.extend(ctx.get('tools_used', []))
            for ctx in recent_contexts:
                recent_tools.extend(ctx.get('tools_used', []))
            if baseline_tools and recent_tools and (set(baseline_tools) != set(recent_tools)):
                factors.append('Changes in tool usage patterns detected')
        except Exception as e:
            logger.debug(f'Drift factors analysis error: {e}')
        return factors if factors else ['Standard operational variance']

    def _analyze_metric_drift(self, metric_name: str, historical_data: deque) -> ModelDriftAlert | None:
        try:
            data_points = list(historical_data)
            baseline_size = len(data_points) // 2
            baseline_data = data_points[:baseline_size]
            recent_data = data_points[baseline_size:]
            baseline_values = [p['value'] for p in baseline_data]
            recent_values = [p['value'] for p in recent_data]
            baseline_mean = statistics.mean(baseline_values)
            recent_mean = statistics.mean(recent_values)
            if stats is None:
                ks_statistic = abs(recent_mean - baseline_mean) / max(abs(baseline_mean), 0.001)
                p_value = 0.1
            else:
                ks_statistic, p_value = stats.ks_2samp(baseline_values, recent_values)
            drift_magnitude = abs(recent_mean - baseline_mean) / max(abs(baseline_mean), 0.001)
            if ks_statistic > self.drift_detection_threshold or p_value < 0.05:
                drift_type = 'performance_drift' if 'quality' in metric_name or 'response_time' in metric_name else 'data_drift'
                contributing_factors = self._identify_drift_factors(baseline_data, recent_data)
                remediation_suggestions = self._generate_drift_remediation(metric_name, drift_type, drift_magnitude)
                return ModelDriftAlert(model_name=metric_name, drift_type=drift_type, drift_magnitude=min(1.0, drift_magnitude), detection_timestamp=default_utc_now(), baseline_performance=baseline_mean, current_performance=recent_mean, contributing_factors=contributing_factors, remediation_suggestions=remediation_suggestions)
        except Exception as e:
            logger.debug(f'Drift analysis failed for {metric_name}: {e}')
        return None

    def _generate_drift_remediation(self, metric_name: str, drift_type: str, magnitude: float) -> list[str]:
        suggestions: list[str] = []
        if drift_type == 'performance_drift':
            if magnitude > 0.3:
                suggestions.extend(['Immediate performance review and debugging required', 'Check for recent configuration or model changes', 'Consider temporary rollback to previous version'])
            else:
                suggestions.extend(['Monitor performance trends closely', 'Review recent changes in operational patterns', 'Consider gradual retuning or recalibration'])
        elif drift_type == 'data_drift':
            suggestions.extend(['Analyze input data distribution changes', 'Review data preprocessing and validation', 'Consider model retraining with recent data', 'Implement data quality monitoring'])
        if 'quality' in metric_name:
            suggestions.append('Review quality assessment criteria and thresholds')
        elif 'response_time' in metric_name:
            suggestions.append('Investigate infrastructure and resource constraints')
        return suggestions