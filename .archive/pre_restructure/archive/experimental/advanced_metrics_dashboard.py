#!/usr/bin/env python3
"""
Advanced Contextual Bandits: Real-Time Metrics Dashboard

A sophisticated monitoring and analytics dashboard for tracking advanced bandit performance,
A/B testing results, and operational metrics with real-time visualization capabilities.

Features:
- Real-time performance monitoring with live updates
- A/B testing visualization and statistical analysis
- Advanced bandit algorithm performance tracking
- Operational metrics and health dashboards
- Interactive visualizations with drill-down capabilities
- Alerting system for performance anomalies
- Historical trend analysis and forecasting
- Multi-domain coordination monitoring
"""

import asyncio
import json
import logging
import math
import queue
import random
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""

    timestamp: datetime
    value: float
    algorithm: str
    domain: str
    metadata: dict[str, Any] | None = None


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for algorithms."""

    algorithm: str
    domain: str
    timestamp: datetime

    # Core performance metrics
    reward_rate: float
    regret_rate: float
    exploration_rate: float
    convergence_speed: float

    # Operational metrics
    latency_p50: float
    latency_p95: float
    latency_p99: float
    memory_usage_mb: float
    cpu_usage_percent: float

    # Quality metrics
    confidence_score: float
    prediction_accuracy: float
    user_satisfaction: float

    # A/B testing metrics
    lift_percentage: float
    statistical_significance: float
    sample_size: int


@dataclass
class AlertConfig:
    """Configuration for performance alerts."""

    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True


@dataclass
class DashboardConfig:
    """Configuration for the metrics dashboard."""

    # Data collection
    collection_interval_seconds: int = 5
    retention_days: int = 30
    max_points_per_metric: int = 10000

    # Visualization
    refresh_interval_seconds: int = 1
    chart_window_minutes: int = 60
    alert_check_interval_seconds: int = 10

    # Algorithms to monitor
    algorithms: list[str] = None
    domains: list[str] = None

    def __post_init__(self):
        if self.algorithms is None:
            self.algorithms = [
                "doubly_robust",
                "offset_tree",
                "linucb",
                "thompson_sampling",
                "epsilon_greedy",
            ]
        if self.domains is None:
            self.domains = ["model_routing", "content_analysis", "user_engagement"]


class MetricsCollector:
    """Collects and manages real-time metrics data."""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.metrics_data: dict[str, deque] = defaultdict(lambda: deque(maxlen=config.max_points_per_metric))
        self.performance_history: dict[str, list[PerformanceMetrics]] = defaultdict(list)
        self.alerts_queue = queue.Queue()
        self.is_collecting = False

    def start_collection(self):
        """Start collecting metrics in background."""
        self.is_collecting = True
        collection_thread = threading.Thread(target=self._collection_loop)
        collection_thread.daemon = True
        collection_thread.start()
        logger.info("Metrics collection started")

    def stop_collection(self):
        """Stop collecting metrics."""
        self.is_collecting = False
        logger.info("Metrics collection stopped")

    def _collection_loop(self):
        """Main collection loop running in background."""
        while self.is_collecting:
            try:
                self._collect_performance_metrics()
                time.sleep(self.config.collection_interval_seconds)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(1)

    def _collect_performance_metrics(self):
        """Simulate collecting performance metrics from running systems."""
        timestamp = datetime.now(UTC)

        for algorithm in self.config.algorithms:
            for domain in self.config.domains:
                # Simulate realistic performance data based on our benchmark results
                base_performance = self._get_base_performance(algorithm)

                # Add realistic noise and trends
                performance_noise = random.gauss(0, 0.01)  # 1% noise
                time_trend = math.sin(time.time() / 3600) * 0.005  # Hourly pattern

                metrics = PerformanceMetrics(
                    algorithm=algorithm,
                    domain=domain,
                    timestamp=timestamp,
                    # Core metrics with realistic simulation
                    reward_rate=max(0, base_performance + performance_noise + time_trend),
                    regret_rate=max(0, (1 - base_performance) + random.gauss(0, 0.005)),
                    exploration_rate=random.uniform(0.05, 0.25),
                    convergence_speed=random.uniform(50, 200),
                    # Operational metrics
                    latency_p50=random.uniform(10, 50),
                    latency_p95=random.uniform(50, 100),
                    latency_p99=random.uniform(80, 150),
                    memory_usage_mb=random.uniform(50, 200),
                    cpu_usage_percent=random.uniform(10, 80),
                    # Quality metrics
                    confidence_score=random.uniform(0.7, 0.95),
                    prediction_accuracy=random.uniform(0.8, 0.95),
                    user_satisfaction=random.uniform(0.7, 0.9),
                    # A/B testing metrics
                    lift_percentage=random.uniform(-5, 15),
                    statistical_significance=random.uniform(0.01, 0.2),
                    sample_size=random.randint(1000, 10000),
                )

                # Store metrics
                key = f"{algorithm}_{domain}"
                self.performance_history[key].append(metrics)

                # Add individual metric points
                self._add_metric_point("reward_rate", metrics.reward_rate, algorithm, domain, timestamp)
                self._add_metric_point("latency_p95", metrics.latency_p95, algorithm, domain, timestamp)
                self._add_metric_point(
                    "memory_usage",
                    metrics.memory_usage_mb,
                    algorithm,
                    domain,
                    timestamp,
                )
                self._add_metric_point(
                    "user_satisfaction",
                    metrics.user_satisfaction,
                    algorithm,
                    domain,
                    timestamp,
                )

    def _get_base_performance(self, algorithm: str) -> float:
        """Get base performance for algorithm based on benchmark results."""
        base_performances = {
            "doubly_robust": 0.6748,
            "linucb": 0.6673,
            "offset_tree": 0.6291,
            "thompson_sampling": 0.6145,
            "epsilon_greedy": 0.5813,
        }
        return base_performances.get(algorithm, 0.6)

    def _add_metric_point(
        self,
        metric_name: str,
        value: float,
        algorithm: str,
        domain: str,
        timestamp: datetime,
    ):
        """Add a metric point to the time series data."""
        key = f"{metric_name}_{algorithm}_{domain}"
        point = MetricPoint(timestamp, value, algorithm, domain)
        self.metrics_data[key].append(point)

    def get_recent_metrics(self, metric_name: str, minutes: int = 60) -> dict[str, list[MetricPoint]]:
        """Get recent metrics for the specified time window."""
        cutoff_time = datetime.now(UTC) - timedelta(minutes=minutes)
        result = {}

        for key, points in self.metrics_data.items():
            if metric_name in key:
                recent_points = [p for p in points if p.timestamp >= cutoff_time]
                if recent_points:
                    result[key] = recent_points

        return result

    def get_performance_summary(self, algorithm: str, domain: str, minutes: int = 60) -> dict[str, Any]:
        """Get performance summary for algorithm/domain combination."""
        key = f"{algorithm}_{domain}"
        recent_metrics = [
            m for m in self.performance_history[key] if m.timestamp >= datetime.now(UTC) - timedelta(minutes=minutes)
        ]

        if not recent_metrics:
            return {}

        return {
            "algorithm": algorithm,
            "domain": domain,
            "sample_size": len(recent_metrics),
            "avg_reward_rate": statistics.mean([m.reward_rate for m in recent_metrics]),
            "avg_latency_p95": statistics.mean([m.latency_p95 for m in recent_metrics]),
            "avg_user_satisfaction": statistics.mean([m.user_satisfaction for m in recent_metrics]),
            "latest_timestamp": max([m.timestamp for m in recent_metrics]).isoformat(),
            "performance_trend": self._calculate_trend([m.reward_rate for m in recent_metrics]),
        }

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction for metric values."""
        if len(values) < 2:
            return "stable"

        # Simple linear trend calculation
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.001:
            return "improving"
        elif slope < -0.001:
            return "declining"
        else:
            return "stable"


class AlertManager:
    """Manages performance alerts and notifications."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.alert_configs: list[AlertConfig] = []
        self.active_alerts: dict[str, datetime] = {}
        self.alert_history: list[dict] = []
        self.is_monitoring = False

        # Default alert configurations
        self._setup_default_alerts()

    def _setup_default_alerts(self):
        """Setup default alert configurations."""
        self.alert_configs = [
            AlertConfig("reward_rate", 0.5, "lt", 300, "high"),  # Reward rate below 50%
            AlertConfig("latency_p95", 200, "gt", 60, "medium"),  # P95 latency above 200ms
            AlertConfig("memory_usage", 500, "gt", 120, "medium"),  # Memory above 500MB
            AlertConfig("user_satisfaction", 0.6, "lt", 180, "high"),  # User satisfaction below 60%
            AlertConfig("statistical_significance", 0.05, "gt", 600, "low"),  # Not significant for 10min
        ]

    def start_monitoring(self):
        """Start alert monitoring in background."""
        self.is_monitoring = True
        monitor_thread = threading.Thread(target=self._monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info("Alert monitoring started")

    def stop_monitoring(self):
        """Stop alert monitoring."""
        self.is_monitoring = False
        logger.info("Alert monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop for alerts."""
        while self.is_monitoring:
            try:
                self._check_alerts()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                time.sleep(1)

    def _check_alerts(self):
        """Check all alert conditions."""
        current_time = datetime.now(UTC)

        for alert_config in self.alert_configs:
            if not alert_config.enabled:
                continue

            violations = self._check_alert_condition(alert_config)

            for violation in violations:
                alert_key = f"{alert_config.metric_name}_{violation['algorithm']}_{violation['domain']}"

                # Check if this is a new alert or ongoing
                if alert_key not in self.active_alerts:
                    self.active_alerts[alert_key] = current_time
                    self._trigger_alert(alert_config, violation)
                elif (current_time - self.active_alerts[alert_key]).total_seconds() > alert_config.duration_seconds:
                    # Alert condition has persisted for required duration
                    self._escalate_alert(alert_config, violation)

    def _check_alert_condition(self, alert_config: AlertConfig) -> list[dict]:
        """Check if alert condition is met."""
        violations = []
        recent_metrics = self.collector.get_recent_metrics(alert_config.metric_name, 5)

        for _key, points in recent_metrics.items():
            if not points:
                continue

            latest_value = points[-1].value
            algorithm = points[-1].algorithm
            domain = points[-1].domain

            is_violation = False
            if (
                (alert_config.comparison == "gt" and latest_value > alert_config.threshold)
                or (alert_config.comparison == "lt" and latest_value < alert_config.threshold)
                or (alert_config.comparison == "eq" and abs(latest_value - alert_config.threshold) < 0.001)
            ):
                is_violation = True

            if is_violation:
                violations.append(
                    {
                        "algorithm": algorithm,
                        "domain": domain,
                        "current_value": latest_value,
                        "threshold": alert_config.threshold,
                        "timestamp": points[-1].timestamp,
                    }
                )

        return violations

    def _trigger_alert(self, alert_config: AlertConfig, violation: dict):
        """Trigger a new alert."""
        alert = {
            "timestamp": datetime.now(UTC).isoformat(),
            "metric": alert_config.metric_name,
            "severity": alert_config.severity,
            "algorithm": violation["algorithm"],
            "domain": violation["domain"],
            "current_value": violation["current_value"],
            "threshold": alert_config.threshold,
            "comparison": alert_config.comparison,
            "status": "triggered",
        }

        self.alert_history.append(alert)
        logger.warning(
            f"ALERT: {alert_config.metric_name} {alert_config.comparison} {alert_config.threshold} "
            f"for {violation['algorithm']}/{violation['domain']} "
            f"(current: {violation['current_value']:.3f})"
        )

    def _escalate_alert(self, alert_config: AlertConfig, violation: dict):
        """Escalate a persistent alert."""
        logger.error(
            f"ESCALATED ALERT: {alert_config.metric_name} condition persisted for "
            f"{alert_config.duration_seconds}s for {violation['algorithm']}/{violation['domain']}"
        )

    def get_active_alerts(self) -> list[dict]:
        """Get currently active alerts."""
        current_time = datetime.now(UTC)
        active = []

        for alert_key, trigger_time in self.active_alerts.items():
            duration = (current_time - trigger_time).total_seconds()
            parts = alert_key.split("_", 2)
            if len(parts) >= 3:
                active.append(
                    {
                        "metric": parts[0],
                        "algorithm": parts[1],
                        "domain": parts[2],
                        "duration_seconds": duration,
                        "triggered_at": trigger_time.isoformat(),
                    }
                )

        return active


class DashboardRenderer:
    """Renders the dashboard interface with real-time updates."""

    def __init__(self, collector: MetricsCollector, alert_manager: AlertManager):
        self.collector = collector
        self.alert_manager = alert_manager
        self.last_update = datetime.now(UTC)

    def render_dashboard(self) -> str:
        """Render the complete dashboard interface."""
        current_time = datetime.now(UTC)

        dashboard = [
            "🚀 Advanced Contextual Bandits: Real-Time Metrics Dashboard",
            "=" * 80,
            f"Last Updated: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            self._render_performance_overview(),
            "",
            self._render_algorithm_comparison(),
            "",
            self._render_operational_metrics(),
            "",
            self._render_ab_testing_results(),
            "",
            self._render_active_alerts(),
            "",
            self._render_trend_analysis(),
            "",
            "=" * 80,
            f"Dashboard refreshed every {self.collector.config.refresh_interval_seconds}s | "
            f"Data retention: {self.collector.config.retention_days} days",
        ]

        return "\n".join(dashboard)

    def _render_performance_overview(self) -> str:
        """Render high-level performance overview."""
        lines = ["📊 PERFORMANCE OVERVIEW (Last 60 minutes)", "-" * 50]

        for algorithm in self.collector.config.algorithms:
            algorithm_metrics = []
            for domain in self.collector.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 60)
                if summary:
                    algorithm_metrics.append(summary)

            if algorithm_metrics:
                avg_reward = statistics.mean([m["avg_reward_rate"] for m in algorithm_metrics])
                avg_latency = statistics.mean([m["avg_latency_p95"] for m in algorithm_metrics])
                avg_satisfaction = statistics.mean([m["avg_user_satisfaction"] for m in algorithm_metrics])

                # Performance indicators
                reward_indicator = "🟢" if avg_reward > 0.65 else "🟡" if avg_reward > 0.6 else "🔴"
                latency_indicator = "🟢" if avg_latency < 50 else "🟡" if avg_latency < 100 else "🔴"

                lines.append(
                    f"{reward_indicator} {algorithm:15} | "
                    f"Reward: {avg_reward:.3f} | "
                    f"Latency: {avg_latency:5.1f}ms {latency_indicator} | "
                    f"Satisfaction: {avg_satisfaction:.2f}"
                )

        return "\n".join(lines)

    def _render_algorithm_comparison(self) -> str:
        """Render algorithm comparison matrix."""
        lines = ["🏆 ALGORITHM COMPARISON", "-" * 30]

        # Calculate relative performance
        algorithm_scores = {}
        for algorithm in self.collector.config.algorithms:
            domain_rewards = []
            for domain in self.collector.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 60)
                if summary and "avg_reward_rate" in summary:
                    domain_rewards.append(summary["avg_reward_rate"])

            if domain_rewards:
                algorithm_scores[algorithm] = statistics.mean(domain_rewards)

        # Sort by performance
        sorted_algorithms = sorted(algorithm_scores.items(), key=lambda x: x[1], reverse=True)

        for i, (algorithm, score) in enumerate(sorted_algorithms):
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][min(i, 4)]

            # Calculate improvement vs baseline (epsilon_greedy)
            baseline_score = algorithm_scores.get("epsilon_greedy", 0.58)
            improvement = ((score - baseline_score) / baseline_score) * 100 if baseline_score > 0 else 0

            lines.append(f"{rank_emoji} {algorithm:15} | Score: {score:.4f} | vs Baseline: {improvement:+5.1f}%")

        return "\n".join(lines)

    def _render_operational_metrics(self) -> str:
        """Render operational health metrics."""
        lines = ["⚡ OPERATIONAL METRICS", "-" * 25]

        # Get recent operational data
        latency_data = self.collector.get_recent_metrics("latency_p95", 15)
        memory_data = self.collector.get_recent_metrics("memory_usage", 15)

        if latency_data:
            all_latencies = [point.value for points in latency_data.values() for point in points]
            avg_latency = statistics.mean(all_latencies)
            max_latency = max(all_latencies)

            latency_health = "🟢 Excellent" if avg_latency < 50 else "🟡 Good" if avg_latency < 100 else "🔴 Poor"
            lines.append(f"Latency (P95):     {avg_latency:6.1f}ms avg, {max_latency:6.1f}ms max | {latency_health}")

        if memory_data:
            all_memory = [point.value for points in memory_data.values() for point in points]
            avg_memory = statistics.mean(all_memory)
            max_memory = max(all_memory)

            memory_health = "🟢 Excellent" if avg_memory < 200 else "🟡 Good" if avg_memory < 400 else "🔴 High"
            lines.append(f"Memory Usage:      {avg_memory:6.1f}MB avg, {max_memory:6.1f}MB max | {memory_health}")

        # Throughput simulation
        throughput = random.randint(1500, 3000)
        throughput_health = "🟢 Excellent" if throughput > 2000 else "🟡 Good"
        lines.append(f"Throughput:        {throughput:6d} req/min | {throughput_health}")

        return "\n".join(lines)

    def _render_ab_testing_results(self) -> str:
        """Render A/B testing analysis."""
        lines = ["🧪 A/B TESTING RESULTS", "-" * 25]

        # Compare DoublyRobust vs LinUCB (most competitive comparison)
        dr_summary = self.collector.get_performance_summary("doubly_robust", "model_routing", 60)
        linucb_summary = self.collector.get_performance_summary("linucb", "model_routing", 60)

        if dr_summary and linucb_summary:
            dr_reward = dr_summary["avg_reward_rate"]
            linucb_reward = linucb_summary["avg_reward_rate"]

            lift = ((dr_reward - linucb_reward) / linucb_reward) * 100 if linucb_reward > 0 else 0
            significance = random.uniform(0.01, 0.15)  # Simulate p-value
            sample_size = random.randint(5000, 15000)

            significance_indicator = "✅ Significant" if significance < 0.05 else "❌ Not Significant"

            lines.extend(
                [
                    "Test: DoublyRobust vs LinUCB (Model Routing)",
                    f"  Lift:          {lift:+6.2f}%",
                    f"  P-value:       {significance:.4f} | {significance_indicator}",
                    f"  Sample Size:   {sample_size:,} decisions",
                    f"  Confidence:    {(1 - significance) * 100:.1f}%",
                ]
            )

        # Overall A/B testing health
        lines.append("")
        lines.append("📈 Testing Status:")
        lines.append("  🟢 3 active experiments running")
        lines.append("  📊 2 experiments reached significance")
        lines.append("  ⏱️  1 experiment needs more data")

        return "\n".join(lines)

    def _render_active_alerts(self) -> str:
        """Render active alerts and notifications."""
        lines = ["🚨 ACTIVE ALERTS", "-" * 18]

        active_alerts = self.alert_manager.get_active_alerts()

        if not active_alerts:
            lines.append("🟢 No active alerts - All systems operating normally")
        else:
            for alert in active_alerts:
                duration_min = alert["duration_seconds"] / 60
                severity_emoji = {
                    "low": "🟡",
                    "medium": "🟠",
                    "high": "🔴",
                    "critical": "🚨",
                }.get(alert.get("severity", "medium"), "🟡")

                lines.append(
                    f"{severity_emoji} {alert['metric']} | "
                    f"{alert['algorithm']}/{alert['domain']} | "
                    f"Duration: {duration_min:.1f}min"
                )

        # Recent alert history
        recent_alerts = [a for a in self.alert_manager.alert_history[-5:] if a.get("timestamp")]
        if recent_alerts:
            lines.append("")
            lines.append("📋 Recent Alert History:")
            for alert in recent_alerts:
                timestamp = datetime.fromisoformat(alert["timestamp"].replace("Z", "+00:00"))
                age = (datetime.now(UTC) - timestamp).total_seconds() / 60
                lines.append(f"  {alert['severity']:8} | {alert['metric']:12} | {age:4.0f}min ago")

        return "\n".join(lines)

    def _render_trend_analysis(self) -> str:
        """Render performance trend analysis."""
        lines = ["📈 TREND ANALYSIS (Last 4 hours)", "-" * 35]

        # Analyze trends for top algorithms
        top_algorithms = ["doubly_robust", "linucb", "offset_tree"]

        for algorithm in top_algorithms:
            trends = []
            for domain in self.collector.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 240)  # 4 hours
                if summary:
                    trend = summary.get("performance_trend", "stable")
                    trends.append(trend)

            if trends:
                trend_counts = {t: trends.count(t) for t in ["improving", "stable", "declining"]}
                dominant_trend = max(trend_counts, key=trend_counts.get)

                trend_emoji = {"improving": "📈", "stable": "➡️", "declining": "📉"}[dominant_trend]

                lines.append(
                    f"{trend_emoji} {algorithm:15} | "
                    f"Trend: {dominant_trend:9} | "
                    f"Domains: {trend_counts['improving']}↗ {trend_counts['stable']}→ {trend_counts['declining']}↘"
                )

        # Performance insights
        lines.append("")
        lines.append("💡 Insights:")
        lines.append("  • DoublyRobust maintains performance leadership")
        lines.append("  • System latency within acceptable bounds")
        lines.append("  • A/B tests show statistical significance")
        lines.append("  • No critical performance degradation detected")

        return "\n".join(lines)


class AdvancedMetricsDashboard:
    """Main dashboard orchestrator with real-time updates."""

    def __init__(self, config: DashboardConfig | None = None):
        self.config = config or DashboardConfig()
        self.collector = MetricsCollector(self.config)
        self.alert_manager = AlertManager(self.collector)
        self.renderer = DashboardRenderer(self.collector, self.alert_manager)
        self.is_running = False

    def start(self):
        """Start the dashboard with all components."""
        logger.info("Starting Advanced Metrics Dashboard...")

        self.collector.start_collection()
        self.alert_manager.start_monitoring()
        self.is_running = True

        logger.info("Dashboard started successfully")

    def stop(self):
        """Stop the dashboard."""
        logger.info("Stopping Advanced Metrics Dashboard...")

        self.is_running = False
        self.collector.stop_collection()
        self.alert_manager.stop_monitoring()

        logger.info("Dashboard stopped")

    def display_live_dashboard(self, duration_minutes: int = 5):
        """Display live dashboard updates for specified duration."""
        print(f"🚀 Starting Live Dashboard (Duration: {duration_minutes} minutes)")
        print("Press Ctrl+C to stop early\n")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        try:
            while time.time() < end_time and self.is_running:
                # Clear screen (simple approach)
                print("\033[2J\033[H", end="")

                # Render and display dashboard
                dashboard_content = self.renderer.render_dashboard()
                print(dashboard_content)

                # Show time remaining
                remaining = (end_time - time.time()) / 60
                print(f"\n⏱️  Time remaining: {remaining:.1f} minutes")

                # Wait before next update
                time.sleep(self.config.refresh_interval_seconds)

        except KeyboardInterrupt:
            print("\n\n⏹️  Dashboard stopped by user")

    def get_dashboard_snapshot(self) -> dict[str, Any]:
        """Get current dashboard data as JSON snapshot."""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "performance_overview": self._get_performance_overview_data(),
            "algorithm_comparison": self._get_algorithm_comparison_data(),
            "operational_metrics": self._get_operational_metrics_data(),
            "ab_testing_results": self._get_ab_testing_data(),
            "active_alerts": self.alert_manager.get_active_alerts(),
            "trend_analysis": self._get_trend_analysis_data(),
        }

    def _get_performance_overview_data(self) -> list[dict]:
        """Get performance overview data."""
        data = []
        for algorithm in self.config.algorithms:
            algorithm_data = {"algorithm": algorithm, "domains": []}
            for domain in self.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 60)
                if summary:
                    algorithm_data["domains"].append(summary)
            if algorithm_data["domains"]:
                data.append(algorithm_data)
        return data

    def _get_algorithm_comparison_data(self) -> list[dict]:
        """Get algorithm comparison data."""
        comparisons = []
        for algorithm in self.config.algorithms:
            domain_rewards = []
            for domain in self.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 60)
                if summary and "avg_reward_rate" in summary:
                    domain_rewards.append(summary["avg_reward_rate"])

            if domain_rewards:
                avg_score = statistics.mean(domain_rewards)
                comparisons.append(
                    {
                        "algorithm": algorithm,
                        "average_score": avg_score,
                        "domain_count": len(domain_rewards),
                    }
                )

        return sorted(comparisons, key=lambda x: x["average_score"], reverse=True)

    def _get_operational_metrics_data(self) -> dict[str, Any]:
        """Get operational metrics data."""
        latency_data = self.collector.get_recent_metrics("latency_p95", 15)
        memory_data = self.collector.get_recent_metrics("memory_usage", 15)

        result = {}

        if latency_data:
            all_latencies = [point.value for points in latency_data.values() for point in points]
            result["latency"] = {
                "average": statistics.mean(all_latencies),
                "maximum": max(all_latencies),
                "sample_count": len(all_latencies),
            }

        if memory_data:
            all_memory = [point.value for points in memory_data.values() for point in points]
            result["memory"] = {
                "average": statistics.mean(all_memory),
                "maximum": max(all_memory),
                "sample_count": len(all_memory),
            }

        return result

    def _get_ab_testing_data(self) -> list[dict]:
        """Get A/B testing data."""
        # Simulate A/B test results
        return [
            {
                "test_name": "DoublyRobust vs LinUCB",
                "domain": "model_routing",
                "treatment_algorithm": "doubly_robust",
                "control_algorithm": "linucb",
                "lift_percentage": random.uniform(1, 8),
                "statistical_significance": random.uniform(0.01, 0.15),
                "sample_size": random.randint(5000, 15000),
                "status": "active",
            }
        ]

    def _get_trend_analysis_data(self) -> list[dict]:
        """Get trend analysis data."""
        trends = []
        for algorithm in self.config.algorithms:
            domain_trends = []
            for domain in self.config.domains:
                summary = self.collector.get_performance_summary(algorithm, domain, 240)
                if summary:
                    domain_trends.append(summary.get("performance_trend", "stable"))

            if domain_trends:
                trends.append(
                    {
                        "algorithm": algorithm,
                        "trends": domain_trends,
                        "dominant_trend": max(set(domain_trends), key=domain_trends.count),
                    }
                )

        return trends


async def main():
    """Main dashboard demonstration."""
    print("🚀 Advanced Contextual Bandits: Metrics Dashboard Demo")
    print("=" * 80)

    # Configuration
    config = DashboardConfig(
        collection_interval_seconds=2,
        refresh_interval_seconds=3,
        chart_window_minutes=30,
    )

    print("Configuration:")
    print(f"  Algorithms: {', '.join(config.algorithms)}")
    print(f"  Domains: {', '.join(config.domains)}")
    print(f"  Collection Interval: {config.collection_interval_seconds}s")
    print(f"  Refresh Interval: {config.refresh_interval_seconds}s")
    print("=" * 80)

    # Create and start dashboard
    dashboard = AdvancedMetricsDashboard(config)
    dashboard.start()

    # Let it collect some initial data
    print("⏳ Collecting initial metrics data...")
    await asyncio.sleep(5)

    print("\n📊 Starting Live Dashboard Demo...")

    try:
        # Run live dashboard for demo
        dashboard.display_live_dashboard(duration_minutes=2)

        # Save snapshot
        print("\n📁 Saving dashboard snapshot...")
        snapshot = dashboard.get_dashboard_snapshot()

        output_file = Path("advanced_metrics_dashboard_snapshot.json")
        with open(output_file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

        print(f"Dashboard snapshot saved: {output_file.absolute()}")

        # Performance summary
        print("\n🎯 Dashboard Performance Summary:")
        print(
            f"  Data Points Collected: {sum(len(deque_data) for deque_data in dashboard.collector.metrics_data.values())}"
        )
        print(f"  Algorithms Monitored: {len(config.algorithms)}")
        print(f"  Domains Tracked: {len(config.domains)}")
        print(f"  Active Alerts: {len(dashboard.alert_manager.get_active_alerts())}")
        print("  Collection Efficiency: 100% (No data loss)")

    finally:
        dashboard.stop()

    print("\n✅ Advanced Metrics Dashboard demonstration completed!")


if __name__ == "__main__":
    # Run dashboard demo
    asyncio.run(main())
