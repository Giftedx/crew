from __future__ import annotations
import logging
import time
from collections import deque
from typing import Any
import numpy as np
from platform.observability import metrics as obs_metrics
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.linear_model import LinearRegression
except Exception:
    IsolationForest = None

    class LinearRegression:

        def __init__(self) -> None:
            self._coef: float | None = None
            self._intercept: float | None = None

        def fit(self, X: np.ndarray, y: np.ndarray) -> LinearRegression:
            x = X.reshape(-1)
            slope, intercept = np.polyfit(x, y, 1) if len(x) >= 2 else (0.0, float(y.mean() if len(y) else 0.0))
            self._coef = float(slope)
            self._intercept = float(intercept)
            return self

        def predict(self, X: list[list[float]] | np.ndarray) -> np.ndarray:
            if self._coef is None or self._intercept is None:
                raise RuntimeError('Model not fitted')
            X_arr = np.array(X)
            x = X_arr.reshape(-1)
            return self._coef * x + self._intercept

        def score(self, X: np.ndarray, y: np.ndarray) -> float:
            y_pred = self.predict(X)
            ss_res = float(np.sum((y - y_pred) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2)) if len(y) else 0.0
            return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
from core.time import default_utc_now
from platform.observability.metrics import get_metrics
from ..advanced_performance_analytics import AdvancedPerformanceAnalytics
from ..enhanced_performance_monitor import EnhancedPerformanceMonitor
from .mixins import CapacityForecastingMixin, DriftDetectionMixin, ScenarioGenerationMixin, TrendAnalysisMixin, WarningDetectionMixin
from .models import CapacityForecast, EarlyWarningAlert, ModelDriftAlert, PerformancePrediction, PredictionConfidence
try:
    from platform.observability import tracing as _obs_tracing
except Exception:

    class _NoOpSpan:

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def set_attribute(self, *args, **kwargs):
            return None

    class _NoOpTracing:

        def start_span(self, _name):
            return _NoOpSpan()
    _obs_tracing = _NoOpTracing()
_metrics = get_metrics()
logger = logging.getLogger(__name__)

def _record_outcome(component: str, outcome: str) -> None:
    labels = {**obs_metrics.label_ctx(), 'component': component, 'outcome': outcome}
    try:
        _metrics.counter('predictive_engine_runs_total', labels=labels).inc()
    except Exception as exc:
        logger.debug('metrics emit failed (component=%s, outcome=%s): %s', component, outcome, exc)

def _record_duration(component: str, outcome: str, duration: float) -> None:
    labels = {**obs_metrics.label_ctx(), 'component': component, 'outcome': outcome}
    try:
        _metrics.histogram('predictive_engine_duration_seconds', duration, labels)
    except Exception as exc:
        logger.debug('metrics duration emit failed (component=%s): %s', component, exc)

def _set_gauge(name: str, value: float, component: str, extra_labels: dict[str, str] | None=None) -> None:
    labels = {**obs_metrics.label_ctx(), 'component': component}
    if extra_labels:
        labels.update(extra_labels)
    try:
        _metrics.gauge(name, labels=labels).set(value)
    except Exception as exc:
        logger.debug('metrics gauge emit failed (%s): %s', name, exc)

class PredictivePerformanceInsights(TrendAnalysisMixin, WarningDetectionMixin, CapacityForecastingMixin, DriftDetectionMixin, ScenarioGenerationMixin):
    """Predictive analytics engine for performance insights."""

    def __init__(self, analytics_engine: AdvancedPerformanceAnalytics | None=None, enhanced_monitor: EnhancedPerformanceMonitor | None=None) -> None:
        self.analytics_engine = analytics_engine or AdvancedPerformanceAnalytics()
        self.enhanced_monitor = enhanced_monitor or EnhancedPerformanceMonitor()
        self.active_predictions: dict[str, list[PerformancePrediction]] = {}
        self.early_warnings: list[EarlyWarningAlert] = []
        self.capacity_forecasts: dict[str, CapacityForecast] = {}
        self.model_drift_alerts: list[ModelDriftAlert] = []
        self.historical_metrics: dict[str, deque] = {}
        self.max_history_size = 1000
        self.prediction_models: dict[str, Any] = {}
        self.model_accuracy_threshold = 0.7
        self.drift_detection_threshold = 0.15
        self.isolation_forests: dict[str, Any] = {}

    async def generate_comprehensive_predictions(self, prediction_horizon: int=12) -> dict[str, Any]:
        start_time = time.perf_counter()
        component = 'comprehensive'
        with _obs_tracing.start_span('predictive.generate_comprehensive_predictions') as span:
            span.set_attribute('prediction_horizon', prediction_horizon)
            outcome = 'success'
            total_predictions = total_warnings = total_forecasts = total_drift_alerts = 0
            reliability_score = 0.0
            try:
                await self._update_historical_metrics()
                predictions = await self._generate_performance_predictions(prediction_horizon)
                warnings = await self._generate_early_warnings()
                capacity_forecasts = await self._perform_capacity_forecasting()
                drift_alerts = await self._detect_model_drift()
                optimization_scenarios = await self._generate_optimization_scenarios()
                reliability_score = self._calculate_prediction_reliability()
                actionable_recommendations = self._generate_predictive_recommendations(predictions, warnings, capacity_forecasts, drift_alerts)
                total_predictions = sum((len(preds) for preds in predictions.values()))
                total_warnings = len(warnings)
                total_forecasts = len(capacity_forecasts)
                total_drift_alerts = len(drift_alerts)
                result: dict[str, Any] = {'prediction_timestamp': default_utc_now().isoformat(), 'prediction_horizon': prediction_horizon, 'reliability_score': reliability_score, 'performance_predictions': {'total_predictions': total_predictions, 'high_confidence': self._count_by_confidence(predictions, PredictionConfidence.HIGH), 'predictions_by_agent': predictions}, 'early_warnings': {'total_warnings': total_warnings, 'critical': len([w for w in warnings if getattr(w, 'severity', None) and w.severity.value == 'critical']), 'urgent': len([w for w in warnings if getattr(w, 'severity', None) and w.severity.value == 'urgent']), 'active_warnings': warnings}, 'capacity_forecasts': {'total_forecasts': total_forecasts, 'breach_alerts': len([f for f in capacity_forecasts.values() if f.projected_breach_time is not None]), 'forecasts': capacity_forecasts}, 'model_drift': {'total_alerts': total_drift_alerts, 'significant_drift': len([d for d in drift_alerts if d.drift_magnitude > 0.3]), 'drift_alerts': drift_alerts}, 'optimization_scenarios': optimization_scenarios, 'actionable_recommendations': actionable_recommendations, 'prediction_confidence': self._assess_overall_confidence(predictions)}
                span.set_attribute('total_predictions', total_predictions)
                span.set_attribute('total_warnings', total_warnings)
                span.set_attribute('total_capacity_forecasts', total_forecasts)
                span.set_attribute('total_drift_alerts', total_drift_alerts)
                span.set_attribute('reliability_score', reliability_score)
            except Exception as e:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(e))
                logger.error('Comprehensive predictions generation failed: %s', e)
                result = {'error': str(e), 'timestamp': default_utc_now().isoformat()}
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_predictions_total', float(total_predictions), component)
                _set_gauge('predictive_engine_warnings_total', float(total_warnings), component)
                _set_gauge('predictive_engine_capacity_forecasts_total', float(total_forecasts), component)
                _set_gauge('predictive_engine_drift_alerts_total', float(total_drift_alerts), component)
                _set_gauge('predictive_engine_reliability_score', float(reliability_score), component)
            return result

    async def _update_historical_metrics(self) -> None:
        start_time = time.perf_counter()
        component = 'historical_update'
        with _obs_tracing.start_span('predictive.update_historical_metrics') as span:
            ingested_points = 0
            outcome = 'success'
            try:
                if hasattr(self.enhanced_monitor, 'real_time_metrics'):
                    for agent_name, agent_data in self.enhanced_monitor.real_time_metrics.items():
                        recent_interactions = agent_data.get('recent_interactions', [])
                        for interaction in recent_interactions[-10:]:
                            timestamp = interaction.get('timestamp', default_utc_now())
                            quality_key = f'{agent_name}_quality'
                            if quality_key not in self.historical_metrics:
                                self.historical_metrics[quality_key] = deque(maxlen=self.max_history_size)
                            self.historical_metrics[quality_key].append({'timestamp': timestamp, 'value': interaction.get('response_quality', 0), 'context': {'response_time': interaction.get('response_time', 0), 'tools_used': interaction.get('tools_used', []), 'error_occurred': interaction.get('error_occurred', False)}})
                            ingested_points += 1
                            time_key = f'{agent_name}_response_time'
                            if time_key not in self.historical_metrics:
                                self.historical_metrics[time_key] = deque(maxlen=self.max_history_size)
                            self.historical_metrics[time_key].append({'timestamp': timestamp, 'value': interaction.get('response_time', 0), 'context': {'quality': interaction.get('response_quality', 0), 'complexity': len(interaction.get('tools_used', [])), 'success': not interaction.get('error_occurred', False)}})
                            ingested_points += 1
            except Exception as exc:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(exc))
                logger.debug('Historical metrics update error: %s', exc)
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            span.set_attribute('points_ingested', ingested_points)
            span.set_attribute('known_metrics', len(self.historical_metrics))
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_historical_points_ingested', float(ingested_points), component)

    async def _generate_performance_predictions(self, prediction_horizon: int) -> dict[str, list[PerformancePrediction]]:
        predictions: dict[str, list[PerformancePrediction]] = {}
        start_time = time.perf_counter()
        component = 'performance_predictions'
        with _obs_tracing.start_span('predictive.generate_performance_predictions') as span:
            outcome = 'success'
            try:
                for metric_name, historical_data in self.historical_metrics.items():
                    if len(historical_data) >= 20:
                        prediction = self._create_metric_prediction(metric_name, historical_data, prediction_horizon)
                        if prediction and prediction.confidence_level != PredictionConfidence.LOW:
                            agent_name = metric_name.split('_')[0]
                            predictions.setdefault(agent_name, []).append(prediction)
            except Exception as exc:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(exc))
                logger.debug('Performance predictions error: %s', exc)
            total_predictions = sum((len(p) for p in predictions.values()))
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            span.set_attribute('prediction_groups', len(predictions))
            span.set_attribute('total_predictions', total_predictions)
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_prediction_groups', float(len(predictions)), component)
                _set_gauge('predictive_engine_predictions_total', float(total_predictions), component)
            return predictions

    def _create_metric_prediction(self, metric_name: str, historical_data: deque, horizon: int) -> PerformancePrediction | None:
        try:
            values = [point['value'] for point in historical_data]
            X = np.array(range(len(values))).reshape(-1, 1)
            y = np.array(values)
            model = LinearRegression()
            model.fit(X, y)
            accuracy = model.score(X, y)
            if accuracy < self.model_accuracy_threshold:
                return None
            future_x = len(values) + horizon
            predicted_value = model.predict([[future_x]])[0]
            residuals = y - model.predict(X)
            mse = (residuals ** 2).mean()
            std_error = float(np.sqrt(mse * (1 + 1 / len(values))))
            margin = 1.96 * std_error
            confidence_interval = (float(predicted_value - margin), float(predicted_value + margin))
            confidence_level = self._determine_confidence_level(accuracy, len(values))
            contributing_factors = self._identify_contributing_factors(metric_name, historical_data)
            uncertainty_factors = self._identify_uncertainty_factors(values, accuracy)
            return PerformancePrediction(metric_name=metric_name, prediction_horizon=horizon, predicted_value=float(predicted_value), confidence_interval=confidence_interval, confidence_level=confidence_level, model_accuracy=float(accuracy), prediction_timestamp=default_utc_now(), contributing_factors=contributing_factors, uncertainty_factors=uncertainty_factors)
        except Exception as e:
            logger.debug(f'Metric prediction failed for {metric_name}: {e}')
            return None

    async def _generate_early_warnings(self) -> list[EarlyWarningAlert]:
        warnings: list[EarlyWarningAlert] = []
        start_time = time.perf_counter()
        component = 'early_warnings'
        with _obs_tracing.start_span('predictive.generate_early_warnings') as span:
            outcome = 'success'
            try:
                for metric_name, historical_data in self.historical_metrics.items():
                    if 'quality' in metric_name and len(historical_data) >= 10:
                        w = self._check_quality_degradation_warning(metric_name, historical_data)
                        if w:
                            warnings.append(w)
                    elif 'response_time' in metric_name and len(historical_data) >= 10:
                        w = self._check_performance_degradation_warning(metric_name, historical_data)
                        if w:
                            warnings.append(w)
                capacity_warning = await self._check_capacity_warnings()
                if capacity_warning:
                    warnings.extend(capacity_warning)
            except Exception as exc:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(exc))
                logger.debug('Early warnings generation error: %s', exc)
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            span.set_attribute('warnings_total', len(warnings))
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_warnings_total', float(len(warnings)), component)
            return warnings

    async def _perform_capacity_forecasting(self) -> dict[str, CapacityForecast]:
        forecasts: dict[str, CapacityForecast] = {}
        start_time = time.perf_counter()
        component = 'capacity_forecast'
        with _obs_tracing.start_span('predictive.perform_capacity_forecasting') as span:
            outcome = 'success'
            try:
                total_interactions_over_time = self._get_interaction_volume_trend()
                if len(total_interactions_over_time) >= 10:
                    volume_forecast = self._forecast_interaction_volume(total_interactions_over_time)
                    forecasts['interaction_volume'] = CapacityForecast(resource_type='compute', current_utilization=total_interactions_over_time[-1] if total_interactions_over_time else 0, predicted_utilization=volume_forecast['predictions'], capacity_threshold=volume_forecast['threshold'], projected_breach_time=volume_forecast['breach_time'], scaling_recommendations=volume_forecast['recommendations'], cost_implications=volume_forecast['cost_implications'])
            except Exception as exc:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(exc))
                logger.debug('Capacity forecasting error: %s', exc)
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            span.set_attribute('forecast_count', len(forecasts))
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_capacity_forecasts_total', float(len(forecasts)), component)
            return forecasts

    async def _detect_model_drift(self) -> list[ModelDriftAlert]:
        drift_alerts: list[ModelDriftAlert] = []
        start_time = time.perf_counter()
        component = 'model_drift'
        with _obs_tracing.start_span('predictive.detect_model_drift') as span:
            outcome = 'success'
            try:
                for metric_name, historical_data in self.historical_metrics.items():
                    if len(historical_data) >= 50:
                        drift_alert = self._analyze_metric_drift(metric_name, historical_data)
                        if drift_alert:
                            drift_alerts.append(drift_alert)
            except Exception as exc:
                outcome = 'error'
                span.set_attribute('error', True)
                span.set_attribute('error.message', str(exc))
                logger.debug('Model drift detection error: %s', exc)
            duration = time.perf_counter() - start_time
            span.set_attribute('duration_seconds', duration)
            span.set_attribute('status', outcome)
            span.set_attribute('drift_alerts', len(drift_alerts))
            _record_outcome(component, outcome)
            _record_duration(component, outcome, duration)
            if outcome == 'success':
                _set_gauge('predictive_engine_drift_alerts_total', float(len(drift_alerts)), component)
            return drift_alerts

    def _generate_predictive_recommendations(self, predictions: dict, warnings: list[EarlyWarningAlert], capacity_forecasts: dict, drift_alerts: list[ModelDriftAlert]) -> list[dict[str, Any]]:
        try:
            parent_impl = getattr(super(), '_generate_predictive_recommendations', None)
            if callable(parent_impl):
                return parent_impl(predictions, warnings, capacity_forecasts, drift_alerts)
        except Exception as exc:
            logger.debug('Predictive recommendations delegation failed: %s', exc)
        recs: list[dict[str, Any]] = []
        try:
            for w in warnings:
                recs.append({'priority': getattr(getattr(w, 'severity', None), 'value', 'medium'), 'category': getattr(w, 'alert_type', 'general'), 'title': getattr(w, 'title', 'Address Warning'), 'description': getattr(w, 'description', ''), 'actions': getattr(w, 'recommended_actions', []), 'timeline': 'immediate', 'confidence': getattr(getattr(w, 'confidence', None), 'value', 'medium')})
        except Exception:
            return []
        return recs

    def _calculate_prediction_reliability(self) -> float:
        try:
            import statistics
            reliability_scores: list[float] = []
            for predictions in self.active_predictions.values():
                for prediction in predictions:
                    confidence_weight = {PredictionConfidence.VERY_HIGH: 1.0, PredictionConfidence.HIGH: 0.8, PredictionConfidence.MEDIUM: 0.6, PredictionConfidence.LOW: 0.3}.get(prediction.confidence_level, 0.5)
                    weighted_accuracy = prediction.model_accuracy * confidence_weight
                    reliability_scores.append(float(weighted_accuracy))
            return statistics.mean(reliability_scores) if reliability_scores else 0.7
        except Exception:
            return 0.7

    def _count_by_confidence(self, predictions: dict, confidence_level: PredictionConfidence) -> int:
        count = 0
        for agent_predictions in predictions.values():
            count += sum((1 for pred in agent_predictions if pred.confidence_level == confidence_level))
        return count

    def _assess_overall_confidence(self, predictions: dict) -> dict[str, Any]:
        total_predictions = sum((len(preds) for preds in predictions.values()))
        if total_predictions == 0:
            return {'overall_confidence': 'insufficient_data', 'confidence_score': 0.0}
        confidence_distribution = {'very_high': self._count_by_confidence(predictions, PredictionConfidence.VERY_HIGH), 'high': self._count_by_confidence(predictions, PredictionConfidence.HIGH), 'medium': self._count_by_confidence(predictions, PredictionConfidence.MEDIUM), 'low': self._count_by_confidence(predictions, PredictionConfidence.LOW)}
        weights = {'very_high': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.3}
        weighted_score = sum((count * weights[level] for level, count in confidence_distribution.items())) / total_predictions
        if weighted_score >= 0.8:
            overall_confidence = 'high'
        elif weighted_score >= 0.6:
            overall_confidence = 'medium'
        else:
            overall_confidence = 'low'
        return {'overall_confidence': overall_confidence, 'confidence_score': float(weighted_score), 'distribution': confidence_distribution, 'total_predictions': total_predictions}

async def run_predictive_analysis(prediction_horizon: int=12) -> dict[str, Any]:
    predictive_engine = PredictivePerformanceInsights()
    return await predictive_engine.generate_comprehensive_predictions(prediction_horizon)

async def get_early_warning_alerts() -> list[EarlyWarningAlert]:
    predictive_engine = PredictivePerformanceInsights()
    return await predictive_engine._generate_early_warnings()
__all__ = ['PredictivePerformanceInsights', 'get_early_warning_alerts', 'run_predictive_analysis']