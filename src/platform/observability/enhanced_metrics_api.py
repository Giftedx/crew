"""Enhanced Metrics API with Web Dashboard Support.

This module provides an enhanced metrics API with web dashboard capabilities,
and exposes JSON endpoints consumed by dashboards and automation. It also
implements short-lived caching for LangSmith evaluation metrics to reduce load
on the Prometheus bridge while keeping data fresh.
"""
from __future__ import annotations
import copy
import importlib
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Any
try:
    from flask import Flask, jsonify, render_template_string, request
    FLASK_AVAILABLE = True
except ImportError:
    Flask = None
    jsonify = render_template_string = request = None
    FLASK_AVAILABLE = False
    print('⚠️  Flask not available - enhanced metrics API will not be available')
from platform.observability.dashboard_templates import get_base_template, get_simple_dashboard
EVALUATION_METRICS_CACHE_TTL_SECONDS = 10

class EnhancedMetricsAPI:
    """Enhanced metrics API with web dashboard support."""

    def __init__(self, app: Flask | None=None):
        if not FLASK_AVAILABLE:
            raise ImportError('Flask is required for enhanced metrics API')
        self.app = app or Flask(__name__)
        self._evaluation_metrics_cache: dict[str, Any] | None = None
        self._evaluation_metrics_cache_timestamp: float | None = None
        self._evaluation_metrics_cache_lock = Lock()
        self._setup_routes()

    def _setup_routes(self) -> None:

        @self.app.route('/')
        def dashboard() -> str:
            """Main dashboard page."""
            return render_template_string(get_base_template())

        @self.app.route('/simple')
        def simple_dashboard() -> str:
            """Simple dashboard page."""
            return render_template_string(get_simple_dashboard())

        @self.app.route('/api/metrics/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat(), 'service': 'enhanced-metrics-api', 'version': '1.0.0'})

        @self.app.route('/api/metrics/system')
        def get_system_metrics():
            """Get system-wide metrics."""
            try:
                from platform.observability.metrics_collector import get_system_metrics
                metrics = get_system_metrics()
                return jsonify({'status': 'success', 'data': {'total_tool_calls': metrics.total_tool_calls, 'total_execution_time': metrics.total_execution_time, 'active_tools': metrics.active_tools, 'system_uptime': metrics.system_uptime, 'memory_usage_mb': metrics.memory_usage_mb, 'cpu_usage_percent': metrics.cpu_usage_percent, 'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None, 'health_score': self._calculate_health_score()}})
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

        @self.app.route('/api/metrics/tools')
        def get_all_tool_metrics():
            """Get metrics for all tools."""
            try:
                from platform.observability.metrics_collector import get_metrics_collector
                collector = get_metrics_collector()
                metrics = collector.get_all_tool_metrics()
                enhanced_metrics = {name: {**tool_metrics.__dict__, 'health_status': self._get_tool_health_status(tool_metrics), 'performance_tier': self._get_performance_tier(tool_metrics)} for name, tool_metrics in metrics.items()}
                return jsonify({'status': 'success', 'data': {'tool_count': len(metrics), 'tools': enhanced_metrics}})
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

        @self.app.route('/api/metrics/tools/<tool_name>')
        def get_tool_metrics(tool_name: str):
            """Get metrics for a specific tool."""
            try:
                from platform.observability.metrics_collector import get_tool_metrics
                metrics = get_tool_metrics(tool_name)
                if not metrics:
                    return (jsonify({'status': 'error', 'error': f"Tool '{tool_name}' not found"}), 404)
                return jsonify({'status': 'success', 'data': {**metrics.__dict__, 'health_status': self._get_tool_health_status(metrics), 'performance_tier': self._get_performance_tier(metrics), 'recommendations': self._get_tool_recommendations(metrics)}})
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

        @self.app.route('/api/metrics/analytics')
        def get_analytics():
            """Get advanced analytics and insights."""
            try:
                from platform.observability.metrics_collector import get_metrics_collector
                collector = get_metrics_collector()
                all_metrics = collector.get_all_tool_metrics()
                analytics = {'performance_insights': self._analyze_performance(all_metrics), 'trend_analysis': self._analyze_trends(all_metrics), 'bottleneck_analysis': self._analyze_bottlenecks(all_metrics), 'optimization_recommendations': self._get_optimization_recommendations(all_metrics)}
                return jsonify({'status': 'success', 'data': analytics})
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

        @self.app.route('/api/metrics/evaluations')
        def get_evaluation_metrics():
            """Get aggregated LangSmith evaluation metrics."""
            try:
                refresh_arg = request.args.get('refresh', '').lower() if request else ''
                force_refresh = refresh_arg in {'1', 'true', 'yes', 'force'}
                evaluation_metrics = self._get_trajectory_evaluation_metrics(force_refresh=force_refresh)
                return jsonify({'status': 'success', 'data': evaluation_metrics})
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

        @self.app.route('/api/metrics/export')
        def export_metrics():
            """Export metrics with enhanced formatting."""
            try:
                from platform.observability.metrics_collector import get_metrics_collector
                collector = get_metrics_collector()
                export_file = f'enhanced_metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'
                if collector.export_metrics(export_file):
                    return jsonify({'status': 'success', 'message': f'Enhanced metrics exported to {export_file}', 'export_file': export_file, 'export_timestamp': datetime.now(timezone.utc).isoformat()})
                return (jsonify({'status': 'error', 'error': 'Failed to export metrics'}), 500)
            except Exception as exc:
                return (jsonify({'status': 'error', 'error': str(exc)}), 500)

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score."""
        try:
            from platform.observability.metrics_collector import get_metrics_collector
            collector = get_metrics_collector()
            all_metrics = collector.get_all_tool_metrics()
            if not all_metrics:
                return 0.0
            total_score = 0
            tool_count = 0
            for tool_metrics in all_metrics.values():
                if tool_metrics.total_calls > 0:
                    success_score = tool_metrics.success_rate * 0.7
                    max_expected_time = 5.0
                    performance_score = max(0, (max_expected_time - tool_metrics.average_execution_time) / max_expected_time) * 0.3
                    tool_score = success_score + performance_score
                    total_score += tool_score
                    tool_count += 1
            return float(total_score / tool_count * 100) if tool_count > 0 else 0.0
        except Exception:
            return 0.0

    def _get_tool_health_status(self, tool_metrics) -> str:
        """Get health status for a specific tool."""
        if tool_metrics.total_calls == 0:
            return 'inactive'
        elif tool_metrics.success_rate >= 0.9:
            return 'excellent'
        elif tool_metrics.success_rate >= 0.8:
            return 'good'
        elif tool_metrics.success_rate >= 0.6:
            return 'fair'
        else:
            return 'poor'

    def _get_performance_tier(self, tool_metrics) -> str:
        """Get performance tier for a tool."""
        if tool_metrics.total_calls == 0:
            return 'unused'
        if tool_metrics.average_execution_time <= 0.5:
            return 'fast'
        if tool_metrics.average_execution_time <= 2.0:
            return 'normal'
        if tool_metrics.average_execution_time <= 5.0:
            return 'slow'
        return 'very_slow'

    def _get_tool_recommendations(self, tool_metrics) -> list[str]:
        """Get recommendations for a specific tool."""
        recommendations: list[str] = []
        if tool_metrics.total_calls == 0:
            recommendations.append('Tool is unused - consider removing or investigating usage patterns')
        elif tool_metrics.success_rate < 0.8:
            recommendations.append('Low success rate - investigate error patterns and improve error handling')
        elif tool_metrics.average_execution_time > 5.0:
            recommendations.append('High execution time - consider optimization or caching')
        elif tool_metrics.failed_calls > tool_metrics.successful_calls:
            recommendations.append('More failures than successes - critical issue requiring immediate attention')
        else:
            recommendations.append('Tool is performing well')
        return recommendations

    def _analyze_performance(self, all_metrics) -> dict:
        """Analyze overall performance patterns."""
        if not all_metrics:
            return {'message': 'No metrics available for analysis'}
        total_calls = sum((tool.total_calls for tool in all_metrics.values()))
        avg_success_rate = sum((tool.success_rate for tool in all_metrics.values())) / len(all_metrics)
        avg_execution_time = sum((tool.average_execution_time for tool in all_metrics.values())) / len(all_metrics)
        return {'total_calls': total_calls, 'average_success_rate': avg_success_rate, 'average_execution_time': avg_execution_time, 'performance_trend': 'stable' if avg_success_rate > 0.8 else 'declining'}

    def _analyze_trends(self, all_metrics) -> dict:
        """Analyze performance trends."""
        return {'trend_period': 'last_24_hours', 'call_volume_trend': 'stable', 'performance_trend': 'stable', 'error_rate_trend': 'stable'}

    def _analyze_bottlenecks(self, all_metrics) -> dict:
        """Analyze system bottlenecks."""
        bottlenecks = []
        for tool_metrics in all_metrics.values():
            if tool_metrics.average_execution_time > 3.0:
                bottlenecks.append({'tool': tool_metrics.tool_name, 'issue': 'high_execution_time', 'value': tool_metrics.average_execution_time, 'impact': 'high' if tool_metrics.average_execution_time > 5.0 else 'medium'})
            elif tool_metrics.success_rate < 0.7:
                bottlenecks.append({'tool': tool_metrics.tool_name, 'issue': 'low_success_rate', 'value': tool_metrics.success_rate, 'impact': 'high' if tool_metrics.success_rate < 0.5 else 'medium'})
        return {'bottlenecks': bottlenecks, 'critical_issues': len([b for b in bottlenecks if b['impact'] == 'high']), 'total_issues': len(bottlenecks)}

    def _get_optimization_recommendations(self, all_metrics) -> list[str]:
        """Get system-wide optimization recommendations."""
        recommendations = []
        slow_tools = [tool for tool in all_metrics.values() if tool.average_execution_time > 3.0]
        error_prone_tools = [tool for tool in all_metrics.values() if tool.success_rate < 0.8]
        if slow_tools:
            recommendations.append(f'Consider optimizing {len(slow_tools)} slow tools for better performance')
        if error_prone_tools:
            recommendations.append(f'Investigate {len(error_prone_tools)} tools with low success rates')
        if not slow_tools and (not error_prone_tools):
            recommendations.append('System is performing well - consider monitoring for capacity planning')
        return recommendations

    def _ensure_evaluation_metrics_cache_state(self) -> None:
        if not hasattr(self, '_evaluation_metrics_cache_lock'):
            self._evaluation_metrics_cache_lock = Lock()
        if not hasattr(self, '_evaluation_metrics_cache'):
            self._evaluation_metrics_cache = None
        if not hasattr(self, '_evaluation_metrics_cache_timestamp'):
            self._evaluation_metrics_cache_timestamp = None

    def _get_trajectory_evaluation_metrics(self, *, force_refresh: bool=False) -> dict[str, Any]:
        """Aggregate LangSmith trajectory evaluation metrics with caching."""
        self._ensure_evaluation_metrics_cache_state()
        cache_lock: Lock = self._evaluation_metrics_cache_lock
        now = time.monotonic()
        with cache_lock:
            cached_payload = self._evaluation_metrics_cache
            cache_timestamp = self._evaluation_metrics_cache_timestamp
            if not force_refresh and cached_payload is not None and (cache_timestamp is not None) and (now - cache_timestamp < EVALUATION_METRICS_CACHE_TTL_SECONDS):
                return copy.deepcopy(cached_payload)
        result = self._compute_trajectory_evaluation_metrics()
        with cache_lock:
            self._evaluation_metrics_cache = copy.deepcopy(result)
            self._evaluation_metrics_cache_timestamp = now
        return result

    def _compute_trajectory_evaluation_metrics(self) -> dict[str, Any]:
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        try:
            obs_metrics = importlib.import_module('obs.metrics')
        except Exception:
            return self._evaluation_metrics_disabled('metrics_module_unavailable', timestamp_iso)
        counter = getattr(obs_metrics, 'TRAJECTORY_EVALUATIONS', None)
        if counter is None or not hasattr(counter, 'collect'):
            return self._evaluation_metrics_disabled('prometheus_unavailable', timestamp_iso)
        try:
            collected = counter.collect()
        except Exception:
            return self._evaluation_metrics_disabled('collection_failed', timestamp_iso)
        if collected is None:
            families: list[Any] = []
        else:
            try:
                families = list(collected)
            except TypeError:
                families = []
        per_scope: dict[tuple[str, str], dict[str, float]] = {}
        total_success = 0.0
        total_failure = 0.0
        for family in families:
            samples = getattr(family, 'samples', None)
            if not samples:
                continue
            for sample in samples:
                if getattr(sample, 'name', '') != 'trajectory_evaluations_total':
                    continue
                value_raw = getattr(sample, 'value', 0)
                try:
                    value = float(value_raw)
                except (TypeError, ValueError):
                    continue
                labels = getattr(sample, 'labels', {}) or {}
                tenant = str(labels.get('tenant', 'unknown'))
                workspace = str(labels.get('workspace', 'unknown'))
                entry = per_scope.setdefault((tenant, workspace), {'tenant': tenant, 'workspace': workspace, 'total': 0.0, 'success': 0.0, 'failure': 0.0})
                entry['total'] += value
                if self._is_success_label(labels.get('success')):
                    entry['success'] += value
                    total_success += value
                else:
                    entry['failure'] += value
                    total_failure += value
        per_tenant: list[dict[str, Any]] = []
        for entry in per_scope.values():
            total = entry['total']
            success = entry['success']
            failure = entry['failure']
            per_tenant.append({'tenant': entry['tenant'], 'workspace': entry['workspace'], 'total': self._coerce_metric(total), 'success': self._coerce_metric(success), 'failure': self._coerce_metric(failure), 'success_rate': success / total if total else 0.0})
        per_tenant.sort(key=lambda item: item['total'], reverse=True)
        total = total_success + total_failure
        success_rate = total_success / total if total else 0.0
        return {'enabled': True, 'total': self._coerce_metric(total), 'success_count': self._coerce_metric(total_success), 'failure_count': self._coerce_metric(total_failure), 'success_rate': success_rate, 'per_tenant': per_tenant, 'last_updated': timestamp_iso}

    @staticmethod
    def _is_success_label(value: Any) -> bool:
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {'1', 'true', 'yes', 'success', 'pass', 'passed'}

    @staticmethod
    def _coerce_metric(value: float) -> float | int:
        as_float = float(value)
        return int(as_float) if as_float.is_integer() else as_float

    def _evaluation_metrics_disabled(self, reason: str, timestamp_iso: str) -> dict[str, Any]:
        return {'enabled': False, 'reason': reason, 'total': 0, 'success_count': 0, 'failure_count': 0, 'success_rate': 0.0, 'per_tenant': [], 'last_updated': timestamp_iso}

    def run(self, host: str='127.0.0.1', port: int=5002, debug: bool=False):
        """Run the enhanced metrics API server."""
        if not FLASK_AVAILABLE:
            raise ImportError('Flask is required to run the enhanced metrics API')
        print(f'🚀 Starting Enhanced Metrics API on http://{host}:{port}')
        print('📊 Available endpoints:')
        print('  • GET  / - Main dashboard')
        print('  • GET  /simple - Simple dashboard')
        print('  • GET  /api/metrics/health - Health check')
        print('  • GET  /api/metrics/system - System metrics')
        print('  • GET  /api/metrics/tools - All tool metrics')
        print('  • GET  /api/metrics/tools/<name> - Specific tool metrics')
        print('  • GET  /api/metrics/analytics - Advanced analytics')
        print('  • GET  /api/metrics/evaluations - LangSmith evaluations')
        print('  • GET  /api/metrics/export - Export metrics')
        self.app.run(host=host, port=port, debug=debug)

def create_enhanced_metrics_api() -> EnhancedMetricsAPI:
    """Create a new enhanced metrics API instance."""
    if not FLASK_AVAILABLE:
        raise ImportError('Flask is required for enhanced metrics API')
    return EnhancedMetricsAPI()

def run_enhanced_metrics_api(host: str='127.0.0.1', port: int=5002, debug: bool=False):
    """Run the enhanced metrics API server."""
    api = create_enhanced_metrics_api()
    api.run(host=host, port=port, debug=debug)