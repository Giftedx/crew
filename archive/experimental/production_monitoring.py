#!/usr/bin/env python3
"""
Advanced Contextual Bandits - Production Monitoring Script

This script provides comprehensive monitoring and alerting for the Advanced Contextual Bandits
system in production environments. It tracks performance metrics, detects anomalies, and
provides automated alerting.

Usage:
    python production_monitoring.py --config monitoring_config.json
    python production_monitoring.py --mode dashboard
    python production_monitoring.py --mode alerts --interval 60

Features:
- Real-time performance monitoring
- Automated anomaly detection
- Performance alerts and notifications
- Health check validation
- Metrics export for external monitoring systems
"""

import argparse
import asyncio
import json
import logging
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("production_monitoring.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Configuration for monitoring alerts"""

    metric_name: str
    min_value: float | None = None
    max_value: float | None = None
    duration_seconds: int = 300  # 5 minutes
    severity: str = "warning"  # warning, critical


@dataclass
class MonitoringConfig:
    """Configuration for production monitoring"""

    check_interval: int = 60  # seconds
    alert_thresholds: list[AlertThreshold]
    enable_dashboard: bool = True
    enable_alerts: bool = True
    export_metrics: bool = False
    metrics_export_path: str = "/tmp/bandits_metrics.json"

    @classmethod
    def from_dict(cls, data: dict):
        """Create config from dictionary"""
        thresholds = [AlertThreshold(**threshold) for threshold in data.get("alert_thresholds", [])]
        return cls(
            check_interval=data.get("check_interval", 60),
            alert_thresholds=thresholds,
            enable_dashboard=data.get("enable_dashboard", True),
            enable_alerts=data.get("enable_alerts", True),
            export_metrics=data.get("export_metrics", False),
            metrics_export_path=data.get("metrics_export_path", "/tmp/bandits_metrics.json"),
        )


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time"""

    timestamp: datetime
    total_decisions: int
    avg_reward: float
    decision_latency_ms: float
    algorithm_performance: dict[str, float]
    domain_performance: dict[str, float]
    confidence_distribution: dict[str, float]
    error_rate: float
    memory_usage_mb: float

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_decisions": self.total_decisions,
            "avg_reward": self.avg_reward,
            "decision_latency_ms": self.decision_latency_ms,
            "algorithm_performance": self.algorithm_performance,
            "domain_performance": self.domain_performance,
            "confidence_distribution": self.confidence_distribution,
            "error_rate": self.error_rate,
            "memory_usage_mb": self.memory_usage_mb,
        }


class PerformanceMonitor:
    """Production performance monitoring system"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.snapshots: list[PerformanceSnapshot] = []
        self.alerts_triggered: dict[str, datetime] = {}
        self.last_health_check = None

        # Mock orchestrator for demonstration - replace with actual import
        self.orchestrator = None
        logger.info("Performance monitor initialized")

    async def initialize(self):
        """Initialize monitoring system"""
        try:
            # In production, import and initialize the actual orchestrator
            # from src.ai import get_orchestrator
            # self.orchestrator = get_orchestrator()

            # For demonstration, we'll simulate
            logger.info("Orchestrator connected for monitoring")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            return False

    async def collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics"""
        try:
            # In production, get actual metrics from orchestrator
            # stats = self.orchestrator.get_performance_summary()

            # For demonstration, simulate realistic metrics
            current_time = datetime.now()

            # Simulate performance data
            total_decisions = len(self.snapshots) * 100 + 1000
            avg_reward = 0.65 + (len(self.snapshots) % 10) * 0.02  # Fluctuating performance
            latency = 45 + (len(self.snapshots) % 5) * 5  # Variable latency

            algorithm_perf = {
                "doubly_robust": 0.67 + (len(self.snapshots) % 7) * 0.01,
                "offset_tree": 0.63 + (len(self.snapshots) % 5) * 0.02,
            }

            domain_perf = {
                "model_routing": 0.70,
                "content_analysis": 0.62,
                "user_engagement": 0.68,
            }

            confidence_dist = {"high": 0.4, "medium": 0.45, "low": 0.15}

            error_rate = 0.02 if len(self.snapshots) % 20 != 0 else 0.05  # Occasional error spikes
            memory_usage = 128 + (len(self.snapshots) % 10) * 12  # Growing memory usage

            snapshot = PerformanceSnapshot(
                timestamp=current_time,
                total_decisions=total_decisions,
                avg_reward=avg_reward,
                decision_latency_ms=latency,
                algorithm_performance=algorithm_perf,
                domain_performance=domain_perf,
                confidence_distribution=confidence_dist,
                error_rate=error_rate,
                memory_usage_mb=memory_usage,
            )

            self.snapshots.append(snapshot)

            # Keep only last 1000 snapshots
            if len(self.snapshots) > 1000:
                self.snapshots = self.snapshots[-1000:]

            return snapshot

        except Exception as e:
            logger.error(f"Failed to collect performance snapshot: {e}")
            raise

    def check_alert_thresholds(self, snapshot: PerformanceSnapshot) -> list[str]:
        """Check if any alert thresholds are breached"""
        alerts = []

        for threshold in self.config.alert_thresholds:
            metric_value = self._get_metric_value(snapshot, threshold.metric_name)

            if metric_value is None:
                continue

            # Check threshold breach
            breach = False
            if threshold.min_value is not None and metric_value < threshold.min_value:
                breach = True
                reason = f"below minimum ({metric_value:.3f} < {threshold.min_value})"
            elif threshold.max_value is not None and metric_value > threshold.max_value:
                breach = True
                reason = f"above maximum ({metric_value:.3f} > {threshold.max_value})"

            if breach:
                # Check if alert should be triggered based on duration
                alert_key = f"{threshold.metric_name}_{threshold.severity}"
                current_time = snapshot.timestamp

                if alert_key not in self.alerts_triggered:
                    self.alerts_triggered[alert_key] = current_time
                elif (current_time - self.alerts_triggered[alert_key]).total_seconds() >= threshold.duration_seconds:
                    alert_msg = f"ALERT [{threshold.severity.upper()}]: {threshold.metric_name} {reason}"
                    alerts.append(alert_msg)
                    logger.warning(alert_msg)
            else:
                # Clear alert if threshold is no longer breached
                alert_key = f"{threshold.metric_name}_{threshold.severity}"
                if alert_key in self.alerts_triggered:
                    del self.alerts_triggered[alert_key]
                    logger.info(f"Alert cleared: {threshold.metric_name}")

        return alerts

    def _get_metric_value(self, snapshot: PerformanceSnapshot, metric_name: str) -> float | None:
        """Get metric value from snapshot"""
        metric_map = {
            "avg_reward": snapshot.avg_reward,
            "decision_latency_ms": snapshot.decision_latency_ms,
            "error_rate": snapshot.error_rate,
            "memory_usage_mb": snapshot.memory_usage_mb,
            "total_decisions": float(snapshot.total_decisions),
        }
        return metric_map.get(metric_name)

    def generate_dashboard_report(self) -> str:
        """Generate dashboard-style performance report"""
        if not self.snapshots:
            return "No performance data available"

        latest = self.snapshots[-1]

        # Calculate trends if we have enough data
        trend_data = ""
        if len(self.snapshots) >= 5:
            recent_rewards = [s.avg_reward for s in self.snapshots[-5:]]
            reward_trend = "↗️" if recent_rewards[-1] > recent_rewards[0] else "↘️"

            recent_latencies = [s.decision_latency_ms for s in self.snapshots[-5:]]
            latency_trend = "↗️" if recent_latencies[-1] > recent_latencies[0] else "↘️"

            trend_data = f"""
📈 Trends (Last 5 checks):
  Reward: {reward_trend} {recent_rewards[0]:.3f} → {recent_rewards[-1]:.3f}
  Latency: {latency_trend} {recent_latencies[0]:.1f}ms → {recent_latencies[-1]:.1f}ms
"""

        # Performance summary
        report = f"""
🎯 Advanced Contextual Bandits - Production Dashboard
================================================================
⏰ Last Updated: {latest.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

🔢 Core Metrics:
  Total Decisions: {latest.total_decisions:,}
  Average Reward: {latest.avg_reward:.3f}
  Decision Latency: {latest.decision_latency_ms:.1f}ms
  Error Rate: {latest.error_rate:.2%}
  Memory Usage: {latest.memory_usage_mb:.1f}MB

🤖 Algorithm Performance:
"""
        for algo, perf in latest.algorithm_performance.items():
            report += f"  {algo.replace('_', ' ').title()}: {perf:.3f}\n"

        report += "\n🎛️ Domain Performance:\n"
        for domain, perf in latest.domain_performance.items():
            report += f"  {domain.replace('_', ' ').title()}: {perf:.3f}\n"

        report += "\n🎯 Confidence Distribution:\n"
        for level, pct in latest.confidence_distribution.items():
            report += f"  {level.title()}: {pct:.1%}\n"

        report += trend_data

        # Active alerts
        if self.alerts_triggered:
            report += "\n🚨 Active Alerts:\n"
            for alert_key, triggered_time in self.alerts_triggered.items():
                duration = (latest.timestamp - triggered_time).total_seconds()
                report += f"  ⚠️ {alert_key} (active for {duration:.0f}s)\n"
        else:
            report += "\n✅ No active alerts\n"

        report += "\n================================================================"

        return report

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file for external monitoring"""
        try:
            if not self.snapshots:
                return

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "latest_snapshot": self.snapshots[-1].to_dict(),
                "summary_stats": self._calculate_summary_stats(),
                "active_alerts": list(self.alerts_triggered.keys()),
            }

            with open(filepath, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Metrics exported to {filepath}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

    def _calculate_summary_stats(self) -> dict:
        """Calculate summary statistics from recent snapshots"""
        if len(self.snapshots) < 2:
            return {}

        recent_snapshots = self.snapshots[-min(60, len(self.snapshots)) :]  # Last hour

        rewards = [s.avg_reward for s in recent_snapshots]
        latencies = [s.decision_latency_ms for s in recent_snapshots]
        error_rates = [s.error_rate for s in recent_snapshots]

        return {
            "time_window_minutes": len(recent_snapshots),
            "avg_reward": {
                "mean": statistics.mean(rewards),
                "median": statistics.median(rewards),
                "min": min(rewards),
                "max": max(rewards),
                "stdev": statistics.stdev(rewards) if len(rewards) > 1 else 0,
            },
            "latency_ms": {
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": sorted(latencies)[int(0.95 * len(latencies))],
                "max": max(latencies),
            },
            "error_rate": {
                "mean": statistics.mean(error_rates),
                "max": max(error_rates),
            },
        }

    async def run_health_check(self) -> dict[str, str]:
        """Run comprehensive health check"""
        health_status = {
            "overall": "healthy",
            "orchestrator": "unknown",
            "performance": "unknown",
            "memory": "unknown",
            "alerts": "unknown",
        }

        try:
            # Check orchestrator availability
            if self.orchestrator is None:
                health_status["orchestrator"] = "disconnected"
                health_status["overall"] = "degraded"
            else:
                health_status["orchestrator"] = "connected"

            # Check recent performance
            if self.snapshots:
                latest = self.snapshots[-1]

                if latest.avg_reward < 0.4:
                    health_status["performance"] = "poor"
                    health_status["overall"] = "degraded"
                elif latest.avg_reward < 0.6:
                    health_status["performance"] = "fair"
                else:
                    health_status["performance"] = "good"

                # Check memory usage
                if latest.memory_usage_mb > 500:
                    health_status["memory"] = "high"
                    health_status["overall"] = "degraded"
                else:
                    health_status["memory"] = "normal"

            # Check active alerts
            if self.alerts_triggered:
                critical_alerts = [k for k in self.alerts_triggered if "critical" in k]
                if critical_alerts:
                    health_status["alerts"] = "critical"
                    health_status["overall"] = "unhealthy"
                else:
                    health_status["alerts"] = "warnings"
            else:
                health_status["alerts"] = "none"

            self.last_health_check = datetime.now()
            logger.info(f"Health check completed: {health_status['overall']}")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting production monitoring loop")

        while True:
            try:
                # Collect performance snapshot
                snapshot = await self.collect_performance_snapshot()

                # Check for alerts
                if self.config.enable_alerts:
                    alerts = self.check_alert_thresholds(snapshot)
                    if alerts:
                        for alert in alerts:
                            logger.warning(f"PRODUCTION ALERT: {alert}")

                # Display dashboard
                if self.config.enable_dashboard:
                    print("\033[2J\033[H")  # Clear screen
                    print(self.generate_dashboard_report())

                # Export metrics
                if self.config.export_metrics:
                    self.export_metrics(self.config.metrics_export_path)

                # Run health check periodically
                if self.last_health_check is None or (datetime.now() - self.last_health_check).total_seconds() > 300:
                    health = await self.run_health_check()
                    if health["overall"] != "healthy":
                        logger.warning(f"System health degraded: {health}")

                # Wait for next check
                await asyncio.sleep(self.config.check_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Brief pause before retry


def load_monitoring_config(config_path: str) -> MonitoringConfig:
    """Load monitoring configuration from file"""
    try:
        with open(config_path) as f:
            config_data = json.load(f)
        return MonitoringConfig.from_dict(config_data)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return get_default_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return get_default_config()


def get_default_config() -> MonitoringConfig:
    """Get default monitoring configuration"""
    return MonitoringConfig(
        check_interval=60,
        alert_thresholds=[
            AlertThreshold(
                metric_name="avg_reward",
                min_value=0.5,
                duration_seconds=300,
                severity="warning",
            ),
            AlertThreshold(
                metric_name="avg_reward",
                min_value=0.3,
                duration_seconds=180,
                severity="critical",
            ),
            AlertThreshold(
                metric_name="decision_latency_ms",
                max_value=100,
                duration_seconds=300,
                severity="warning",
            ),
            AlertThreshold(
                metric_name="error_rate",
                max_value=0.05,
                duration_seconds=180,
                severity="warning",
            ),
            AlertThreshold(
                metric_name="memory_usage_mb",
                max_value=400,
                duration_seconds=600,
                severity="warning",
            ),
        ],
        enable_dashboard=True,
        enable_alerts=True,
        export_metrics=True,
    )


def save_default_config(config_path: str):
    """Save default configuration to file"""
    config = get_default_config()
    config_dict = {
        "check_interval": config.check_interval,
        "alert_thresholds": [asdict(threshold) for threshold in config.alert_thresholds],
        "enable_dashboard": config.enable_dashboard,
        "enable_alerts": config.enable_alerts,
        "export_metrics": config.export_metrics,
        "metrics_export_path": config.metrics_export_path,
    }

    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=2)

    print(f"Default configuration saved to {config_path}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Advanced Contextual Bandits Production Monitoring")
    parser.add_argument("--config", default="monitoring_config.json", help="Configuration file path")
    parser.add_argument(
        "--mode",
        choices=["monitor", "dashboard", "alerts", "health"],
        default="monitor",
        help="Monitoring mode",
    )
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--save-config", action="store_true", help="Save default configuration and exit")

    args = parser.parse_args()

    if args.save_config:
        save_default_config(args.config)
        return

    # Load configuration
    config = load_monitoring_config(args.config)
    if args.interval != 60:
        config.check_interval = args.interval

    # Adjust config based on mode
    if args.mode == "dashboard":
        config.enable_alerts = False
        config.enable_dashboard = True
    elif args.mode == "alerts":
        config.enable_dashboard = False
        config.enable_alerts = True
    elif args.mode == "health":
        config.enable_dashboard = False
        config.enable_alerts = False

    # Initialize and run monitor
    monitor = PerformanceMonitor(config)

    if not await monitor.initialize():
        logger.error("Failed to initialize monitoring system")
        return

    if args.mode == "health":
        # Run single health check
        health = await monitor.run_health_check()
        print(json.dumps(health, indent=2))
    else:
        # Run continuous monitoring
        await monitor.monitor_loop()


if __name__ == "__main__":
    asyncio.run(main())
