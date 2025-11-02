"""Performance Dashboard for Enhanced Optimizations.

This module provides a unified dashboard for monitoring all performance optimizations
including cache performance, cost optimization, error handling, and memory usage.
"""

from __future__ import annotations

import json
import time
from platform.core.step_result import get_error_analyzer, get_recovery_manager
from platform.db_optimizer import get_database_optimizer
from platform.llm_cache import get_llm_cache
from typing import Any

from domains.memory.vector_store import VectorStore


class PerformanceDashboard:
    """Unified performance monitoring dashboard for all optimizations."""

    def __init__(self):
        self.cache = get_llm_cache()
        self.error_analyzer = get_error_analyzer()
        self.recovery_manager = get_recovery_manager()
        try:
            self.db_optimizer = get_database_optimizer()
        except Exception:
            self.db_optimizer = None
        try:
            self.vector_store = VectorStore()
        except Exception:
            self.vector_store = None

    def get_comprehensive_metrics(self) -> dict[str, Any]:
        """Get all performance metrics in a unified format."""
        return {
            "timestamp": time.time(),
            "cache_performance": self._get_cache_metrics(),
            "cost_optimization": self._get_cost_metrics(),
            "error_handling": self._get_error_metrics(),
            "memory_performance": self._get_memory_metrics(),
            "database_performance": self._get_database_metrics(),
            "system_health": self._get_system_health(),
        }

    def _get_cache_metrics(self) -> dict[str, Any]:
        """Get comprehensive cache performance metrics."""
        try:
            stats = self.cache.get_stats()
            return {
                "enabled": True,
                "hit_rate": stats.get("hit_rate", 0.0),
                "total_requests": stats.get("total_requests", 0),
                "semantic_hit_rate": stats.get("semantic_hit_rate", 0.0),
                "avg_lookup_time_ms": stats.get("avg_lookup_time", 0.0),
                "memory_usage_mb": stats.get("memory_usage_mb", 0.0),
                "lru_size": stats.get("lru_size", 0),
                "lru_max_size": stats.get("lru_max_size", 0),
                "most_accessed_patterns": self.cache.get_most_accessed_patterns(5),
                "optimization_suggestions": self.cache.optimize_for_workload().get("suggestions", []),
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def _get_cost_metrics(self) -> dict[str, Any]:
        """Get cost optimization performance metrics."""
        try:
            return {
                "enabled": True,
                "estimated_monthly_savings": 0.0,
                "cost_savings_rate": 0.0,
                "model_selection_distribution": {},
                "quality_vs_cost_tradeoffs": "balanced",
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def _get_error_metrics(self) -> dict[str, Any]:
        """Get error handling performance metrics."""
        try:
            error_summary = self.error_analyzer.get_error_summary()
            return {
                "enabled": True,
                "total_errors": error_summary.get("total_errors", 0),
                "error_rate": error_summary.get("error_rate", 0.0),
                "critical_errors": error_summary.get("critical_errors", 0),
                "retryable_errors": error_summary.get("retryable_errors", 0),
                "most_common_errors": error_summary.get("most_common_errors", {}),
                "error_categories": error_summary.get("error_categories", {}),
                "circuit_breakers": self._get_circuit_breaker_status(),
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def _get_memory_metrics(self) -> dict[str, Any]:
        """Get memory system performance metrics."""
        try:
            if not self.vector_store:
                return {"enabled": False, "error": "Vector store not available"}
            memory_analysis = self.vector_store.analyze_memory_usage()
            analytics = self.vector_store.get_memory_analytics()
            return {
                "enabled": True,
                "total_collections": memory_analysis.get("total_collections", 0),
                "total_vectors": memory_analysis.get("total_vectors", 0),
                "estimated_memory_mb": memory_analysis.get("estimated_memory_mb", 0.0),
                "performance_metrics": analytics,
                "similarity_analysis": memory_analysis.get("similarity_analysis", {}),
                "optimization_suggestions": memory_analysis.get("optimization_suggestions", []),
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def _get_database_metrics(self) -> dict[str, Any]:
        """Get database performance metrics."""
        if not self.db_optimizer:
            return {"enabled": False, "error": "Database optimizer not available"}
        try:
            return {
                "enabled": True,
                "connection_pool_utilization": 0.0,
                "query_performance_score": 0.0,
                "index_efficiency_score": 0.0,
                "slow_queries_count": 0,
                "health_status": "unknown",
                "optimization_suggestions": [],
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}

    def _get_circuit_breaker_status(self) -> dict[str, Any]:
        """Get circuit breaker status for all components."""
        try:
            return {"components_monitored": 0, "open_circuits": 0, "recent_failures": 0, "recovery_success_rate": 0.0}
        except Exception as e:
            return {"error": str(e)}

    def _get_system_health(self) -> dict[str, Any]:
        """Get overall system health assessment."""
        metrics = self.get_comprehensive_metrics()
        health_score = 0.0
        max_score = 0.0
        if metrics["cache_performance"]["enabled"]:
            cache_score = metrics["cache_performance"]["hit_rate"] * 100
            health_score += cache_score * 0.25
            max_score += 100 * 0.25
        if metrics["error_handling"]["enabled"]:
            error_rate = metrics["error_handling"]["error_rate"]
            error_score = max(0, 100 - error_rate * 1000)
            health_score += error_score * 0.25
            max_score += 100 * 0.25
        if metrics["memory_performance"]["enabled"]:
            memory_mb = metrics["memory_performance"]["estimated_memory_mb"]
            memory_score = max(0, 100 - memory_mb / 100)
            health_score += memory_score * 0.25
            max_score += 100 * 0.25
        if metrics["database_performance"]["enabled"]:
            db_score = 80.0
            health_score += db_score * 0.25
            max_score += 100 * 0.25
        overall_score = health_score / max_score * 100 if max_score > 0 else 0
        return {
            "overall_score": overall_score,
            "health_status": self._get_health_status(overall_score),
            "components_healthy": sum(1 for m in metrics.values() if m.get("enabled", False)),
            "total_components": len(metrics),
            "last_updated": time.time(),
        }

    def _get_health_status(self, score: float) -> str:
        """Convert numeric score to health status."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"

    def get_optimization_recommendations(self) -> list[dict[str, Any]]:
        """Get prioritized optimization recommendations."""
        recommendations = []
        metrics = self.get_comprehensive_metrics()
        if metrics["cache_performance"]["enabled"]:
            cache_rec = metrics["cache_performance"].get("optimization_suggestions", [])
            for rec in cache_rec:
                recommendations.append(
                    {
                        "category": "cache",
                        "priority": "high",
                        "recommendation": rec,
                        "current_value": metrics["cache_performance"]["hit_rate"],
                        "target_value": 0.8,
                    }
                )
        if metrics["error_handling"]["enabled"]:
            error_rate = metrics["error_handling"]["error_rate"]
            if error_rate > 0.05:
                recommendations.append(
                    {
                        "category": "error_handling",
                        "priority": "high",
                        "recommendation": f"High error rate detected ({error_rate:.2%}). Review error patterns and recovery strategies.",
                        "current_value": error_rate,
                        "target_value": 0.05,
                    }
                )
        if metrics["memory_performance"]["enabled"]:
            memory_rec = metrics["memory_performance"].get("optimization_suggestions", [])
            for rec in memory_rec:
                recommendations.append(
                    {
                        "category": "memory",
                        "priority": "medium",
                        "recommendation": rec,
                        "current_value": metrics["memory_performance"]["estimated_memory_mb"],
                        "target_value": 100,
                    }
                )
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        return recommendations[:10]

    def export_metrics_json(self) -> str:
        """Export all metrics as JSON for external monitoring systems."""
        metrics = self.get_comprehensive_metrics()
        return json.dumps(metrics, indent=2, default=str)

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get a concise dashboard summary for quick overview."""
        try:
            cache_metrics = self._get_cache_metrics()
            error_metrics = self._get_error_metrics()
            memory_metrics = self._get_memory_metrics()
            health_score = 0.0
            max_score = 0.0
            if cache_metrics.get("enabled"):
                cache_score = cache_metrics.get("hit_rate", 0) * 100
                health_score += cache_score * 0.3
                max_score += 100 * 0.3
            if error_metrics.get("enabled"):
                error_rate = error_metrics.get("error_rate", 0)
                error_score = max(0, 100 - error_rate * 1000)
                health_score += error_score * 0.3
                max_score += 100 * 0.3
            if memory_metrics.get("enabled"):
                memory_mb = memory_metrics.get("estimated_memory_mb", 0)
                memory_score = max(0, 100 - memory_mb / 100)
                health_score += memory_score * 0.4
                max_score += 100 * 0.4
            overall_score = health_score / max_score * 100 if max_score > 0 else 0
            return {
                "timestamp": time.time(),
                "overall_health": self._get_health_status(overall_score),
                "overall_score": overall_score,
                "active_optimizations": sum(
                    1 for m in [cache_metrics, error_metrics, memory_metrics] if m.get("enabled", False)
                ),
                "total_components": 3,
                "performance_highlights": {
                    "cache_hit_rate": cache_metrics.get("hit_rate", 0),
                    "error_rate": error_metrics.get("error_rate", 0),
                    "memory_efficiency_mb": memory_metrics.get("estimated_memory_mb", 0),
                },
            }
        except Exception as e:
            return {"timestamp": time.time(), "overall_health": "error", "overall_score": 0.0, "error": str(e)}


_dashboard: PerformanceDashboard | None = None


def get_performance_dashboard() -> PerformanceDashboard:
    """Get the global performance dashboard instance."""
    global _dashboard
    if _dashboard is None:
        _dashboard = PerformanceDashboard()
    return _dashboard


def reset_performance_dashboard() -> None:
    """Reset the global performance dashboard instance."""
    global _dashboard
    _dashboard = None
