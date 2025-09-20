#!/usr/bin/env python3
"""
Advanced Bandits Production Deployment Automation

Comprehensive deployment automation for rolling out advanced contextual bandits
to production with health checks, monitoring, and automatic rollback capabilities.

Features:
- Gradual rollout with configurable percentages
- Health checks and performance validation
- Automatic rollback on degraded performance
- Monitoring dashboard integration
- Configuration management
- Zero-downtime deployment
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DeploymentConfig:
    """Configuration for advanced bandits deployment."""

    # Rollout configuration
    initial_rollout_percentage: float = 0.05  # Start with 5%
    max_rollout_percentage: float = 1.0  # Maximum 100%
    rollout_increment: float = 0.1  # Increase by 10% each step
    rollout_interval_minutes: int = 30  # Wait 30 minutes between increments

    # Domains to deploy
    target_domains: list[str] = None

    # Health check thresholds
    min_success_rate: float = 0.95  # 95% minimum success rate
    max_latency_degradation: float = 0.2  # 20% max latency increase
    min_reward_improvement: float = -0.05  # Allow 5% reward decrease initially

    # Monitoring
    health_check_interval_seconds: int = 60  # Check every minute
    health_check_window_minutes: int = 10  # Look at last 10 minutes

    # Rollback conditions
    consecutive_failed_checks: int = 3  # Rollback after 3 failed checks
    critical_error_threshold: float = 0.05  # Rollback if >5% critical errors

    # Environment
    environment: str = "production"
    deployment_id: str = None

    def __post_init__(self):
        if self.target_domains is None:
            self.target_domains = ["model_routing", "content_analysis", "user_engagement"]
        if self.deployment_id is None:
            self.deployment_id = f"deploy_{int(time.time())}"


@dataclass
class HealthMetrics:
    """Health metrics for deployment monitoring."""

    timestamp: datetime
    domain: str
    success_rate: float
    average_latency_ms: float
    average_reward: float
    error_rate: float
    request_count: int
    rollout_percentage: float


@dataclass
class DeploymentStatus:
    """Current deployment status."""

    deployment_id: str
    start_time: datetime
    current_phase: str  # initializing, rolling_out, completed, failed, rolling_back
    current_rollout_percentage: float
    target_domains: list[str]
    completed_domains: list[str]
    failed_domains: list[str]
    health_status: str  # healthy, degraded, critical
    last_health_check: datetime
    consecutive_failed_checks: int
    rollback_reason: str | None = None


class HealthChecker:
    """Monitors system health during deployment."""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.baseline_metrics = {}  # Store baseline performance
        self.current_metrics = {}  # Store current performance

    async def establish_baseline(self, domains: list[str]) -> dict[str, HealthMetrics]:
        """Establish baseline performance metrics before deployment."""
        logger.info("Establishing baseline performance metrics...")

        baseline = {}
        for domain in domains:
            # In a real implementation, this would query actual metrics from monitoring systems
            # For demo purposes, we'll simulate baseline metrics
            metrics = await self._simulate_metrics_collection(domain, 0.0)  # 0% rollout = baseline
            baseline[domain] = metrics
            logger.info(
                f"Baseline for {domain}: success_rate={metrics.success_rate:.3f}, "
                f"latency={metrics.average_latency_ms:.1f}ms, reward={metrics.average_reward:.3f}"
            )

        self.baseline_metrics = baseline
        return baseline

    async def _simulate_metrics_collection(self, domain: str, rollout_percentage: float) -> HealthMetrics:
        """Simulate metrics collection from monitoring system."""

        # Simulate baseline performance (pre-advanced bandits)
        baseline_performance = {
            "model_routing": {"success_rate": 0.98, "latency": 500, "reward": 0.72},
            "content_analysis": {"success_rate": 0.97, "latency": 800, "reward": 0.68},
            "user_engagement": {"success_rate": 0.99, "latency": 300, "reward": 0.75},
        }

        base = baseline_performance.get(domain, {"success_rate": 0.98, "latency": 500, "reward": 0.70})

        # Simulate advanced bandit improvements (gradual improvement with rollout)
        if rollout_percentage > 0:
            # Advanced bandits generally improve performance, but with some variance
            improvement_factor = rollout_percentage * 0.15  # Up to 15% improvement at full rollout
            variance = (time.time() % 1 - 0.5) * 0.1  # ±5% variance

            success_rate = min(1.0, base["success_rate"] + improvement_factor * 0.02 + variance * 0.01)
            latency = base["latency"] * (1 - improvement_factor * 0.1 + variance * 0.05)
            reward = base["reward"] * (1 + improvement_factor + variance * 0.1)

            # Simulate occasional degradation during rollout
            if rollout_percentage < 0.2 and time.time() % 10 < 1:  # 10% chance of degradation in early rollout
                success_rate *= 0.95
                latency *= 1.1
                reward *= 0.98
        else:
            success_rate = base["success_rate"]
            latency = base["latency"]
            reward = base["reward"]

        return HealthMetrics(
            timestamp=datetime.now(UTC),
            domain=domain,
            success_rate=success_rate,
            average_latency_ms=latency,
            average_reward=reward,
            error_rate=1.0 - success_rate,
            request_count=int(100 + (time.time() % 100)),  # Simulate 100-200 requests
            rollout_percentage=rollout_percentage,
        )

    async def check_health(self, domains: list[str], rollout_percentage: float) -> tuple[bool, str]:
        """Check current health status against baseline."""

        health_issues = []

        for domain in domains:
            current = await self._simulate_metrics_collection(domain, rollout_percentage)
            self.current_metrics[domain] = current

            if domain not in self.baseline_metrics:
                health_issues.append(f"{domain}: No baseline metrics available")
                continue

            baseline = self.baseline_metrics[domain]

            # Check success rate
            if current.success_rate < self.config.min_success_rate:
                health_issues.append(
                    f"{domain}: Success rate {current.success_rate:.3f} below threshold {self.config.min_success_rate:.3f}"
                )

            # Check latency degradation
            latency_increase = (current.average_latency_ms - baseline.average_latency_ms) / baseline.average_latency_ms
            if latency_increase > self.config.max_latency_degradation:
                health_issues.append(
                    f"{domain}: Latency increased by {latency_increase:.1%} (threshold: {self.config.max_latency_degradation:.1%})"
                )

            # Check reward degradation
            reward_change = (current.average_reward - baseline.average_reward) / baseline.average_reward
            if reward_change < self.config.min_reward_improvement:
                health_issues.append(
                    f"{domain}: Reward decreased by {-reward_change:.1%} (threshold: {-self.config.min_reward_improvement:.1%})"
                )

            # Check error rate
            if current.error_rate > self.config.critical_error_threshold:
                health_issues.append(
                    f"{domain}: Critical error rate {current.error_rate:.3f} above threshold {self.config.critical_error_threshold:.3f}"
                )

            logger.info(
                f"Health check {domain}: success={current.success_rate:.3f}, "
                f"latency={current.average_latency_ms:.1f}ms, reward={current.average_reward:.3f}"
            )

        is_healthy = len(health_issues) == 0
        status_message = "System healthy" if is_healthy else f"Health issues: {'; '.join(health_issues)}"

        return is_healthy, status_message


class DeploymentManager:
    """Manages the deployment process with health monitoring and rollback."""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.health_checker = HealthChecker(config)
        self.status = DeploymentStatus(
            deployment_id=config.deployment_id,
            start_time=datetime.now(UTC),
            current_phase="initializing",
            current_rollout_percentage=0.0,
            target_domains=config.target_domains.copy(),
            completed_domains=[],
            failed_domains=[],
            health_status="unknown",
            last_health_check=datetime.now(UTC),
            consecutive_failed_checks=0,
        )

        logger.info(f"Deployment manager initialized: {config.deployment_id}")

    async def deploy(self) -> bool:
        """Execute the full deployment process."""

        try:
            # Phase 1: Initialize and establish baseline
            self.status.current_phase = "initializing"
            logger.info("🚀 Starting advanced bandits deployment...")

            # Establish baseline metrics
            await self.health_checker.establish_baseline(self.config.target_domains)

            # Phase 2: Gradual rollout
            self.status.current_phase = "rolling_out"
            rollout_successful = await self._execute_gradual_rollout()

            if rollout_successful:
                self.status.current_phase = "completed"
                self.status.completed_domains = self.config.target_domains.copy()
                logger.info("✅ Deployment completed successfully!")
                return True
            else:
                self.status.current_phase = "failed"
                logger.error("❌ Deployment failed!")
                return False

        except Exception as e:
            logger.error(f"Deployment failed with exception: {e}")
            self.status.current_phase = "failed"
            await self._rollback(f"Exception during deployment: {e}")
            return False

    async def _execute_gradual_rollout(self) -> bool:
        """Execute gradual rollout with health monitoring."""

        rollout_percentage = self.config.initial_rollout_percentage

        while rollout_percentage <= self.config.max_rollout_percentage:
            logger.info(f"📈 Rolling out to {rollout_percentage:.1%} of traffic...")

            # Update configuration
            await self._update_rollout_configuration(rollout_percentage)
            self.status.current_rollout_percentage = rollout_percentage

            # Wait for metrics to stabilize
            logger.info(f"⏳ Waiting {self.config.rollout_interval_minutes} minutes for metrics to stabilize...")
            for i in range(self.config.rollout_interval_minutes):
                await asyncio.sleep(60)  # Wait 1 minute

                # Perform health check every minute
                is_healthy, status_message = await self.health_checker.check_health(
                    self.config.target_domains, rollout_percentage
                )

                self.status.last_health_check = datetime.now(UTC)

                if is_healthy:
                    self.status.health_status = "healthy"
                    self.status.consecutive_failed_checks = 0
                    logger.info(f"✅ Health check passed: {status_message}")
                else:
                    self.status.consecutive_failed_checks += 1
                    self.status.health_status = "degraded" if self.status.consecutive_failed_checks < 3 else "critical"
                    logger.warning(
                        f"⚠️  Health check failed ({self.status.consecutive_failed_checks}): {status_message}"
                    )

                    # Check if we should rollback
                    if self.status.consecutive_failed_checks >= self.config.consecutive_failed_checks:
                        logger.error("💥 Too many consecutive health check failures - initiating rollback")
                        await self._rollback(f"Consecutive health check failures: {status_message}")
                        return False

            # If we survived the stabilization period, move to next rollout percentage
            if rollout_percentage >= self.config.max_rollout_percentage:
                break

            rollout_percentage = min(
                self.config.max_rollout_percentage, rollout_percentage + self.config.rollout_increment
            )

        logger.info("🎯 Rollout completed successfully!")
        return True

    async def _update_rollout_configuration(self, rollout_percentage: float):
        """Update system configuration for new rollout percentage."""

        # In a real implementation, this would update environment variables,
        # configuration files, or API calls to the configuration service

        config_updates = {
            "ENABLE_RL_ADVANCED": "true",
            "ENABLE_RL_SHADOW_EVAL": "true",
            "ENABLE_RL_MONITORING": "true",
            "RL_ROLLOUT_PERCENTAGE": str(rollout_percentage),
            "RL_ROLLOUT_DOMAINS": ",".join(self.config.target_domains),
            "DEPLOYMENT_ID": self.config.deployment_id,
        }

        logger.info(f"Updating configuration: RL_ROLLOUT_PERCENTAGE={rollout_percentage:.1%}")

        # Simulate configuration update
        for key, value in config_updates.items():
            os.environ[key] = value

        # In production, this might involve:
        # - Updating Kubernetes ConfigMaps
        # - Calling configuration management APIs
        # - Updating service mesh routing rules
        # - Rolling restart of services (if needed)

        # Simulate brief deployment time
        await asyncio.sleep(2)

    async def _rollback(self, reason: str):
        """Perform automatic rollback to previous stable state."""

        logger.error(f"🔄 Initiating rollback: {reason}")

        self.status.current_phase = "rolling_back"
        self.status.rollback_reason = reason

        try:
            # Disable advanced bandits
            await self._update_rollout_configuration(0.0)

            # Set environment variables to disable advanced features
            rollback_config = {"ENABLE_RL_ADVANCED": "false", "RL_ROLLOUT_PERCENTAGE": "0.0"}

            for key, value in rollback_config.items():
                os.environ[key] = value

            # Wait for rollback to take effect
            await asyncio.sleep(10)

            # Verify rollback success
            is_healthy, status_message = await self.health_checker.check_health(self.config.target_domains, 0.0)

            if is_healthy:
                logger.info("✅ Rollback completed successfully")
                self.status.current_phase = "rolled_back"
                self.status.health_status = "healthy"
            else:
                logger.error(f"❌ Rollback verification failed: {status_message}")
                self.status.current_phase = "rollback_failed"
                self.status.health_status = "critical"

        except Exception as e:
            logger.error(f"💥 Rollback failed: {e}")
            self.status.current_phase = "rollback_failed"

    def get_deployment_report(self) -> dict[str, Any]:
        """Generate comprehensive deployment report."""

        duration = datetime.now(UTC) - self.status.start_time

        report = {
            "deployment_summary": {
                "deployment_id": self.status.deployment_id,
                "start_time": self.status.start_time.isoformat(),
                "duration_minutes": duration.total_seconds() / 60,
                "current_phase": self.status.current_phase,
                "final_rollout_percentage": self.status.current_rollout_percentage,
                "health_status": self.status.health_status,
                "success": self.status.current_phase in ["completed"],
                "rollback_reason": self.status.rollback_reason,
            },
            "configuration": asdict(self.config),
            "domains": {
                "target": self.status.target_domains,
                "completed": self.status.completed_domains,
                "failed": self.status.failed_domains,
            },
            "health_metrics": {},
            "recommendations": [],
        }

        # Add current health metrics
        for domain, metrics in self.health_checker.current_metrics.items():
            report["health_metrics"][domain] = asdict(metrics)

        # Generate recommendations
        recommendations = []

        if self.status.current_phase == "completed":
            recommendations.append("Deployment completed successfully - monitor for 24 hours")
            recommendations.append("Consider increasing rollout increment for faster future deployments")
        elif self.status.current_phase == "failed":
            recommendations.append("Investigate root cause of deployment failure")
            recommendations.append("Review and adjust health check thresholds if needed")
            recommendations.append("Consider gradual rollout with smaller increments")
        elif self.status.current_phase == "rolled_back":
            recommendations.append("Investigate rollback trigger and fix underlying issues")
            recommendations.append("Test advanced bandits in staging environment")
            recommendations.append("Consider A/B testing with smaller user segments")

        if self.status.consecutive_failed_checks > 0:
            recommendations.append("Review monitoring and alerting configuration")

        report["recommendations"] = recommendations

        return report

    def save_deployment_report(self, output_path: str = None) -> str:
        """Save deployment report to file."""

        if output_path is None:
            output_path = f"deployment_report_{self.config.deployment_id}.json"

        report = self.get_deployment_report()

        output_file = Path(output_path)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Deployment report saved: {output_file.absolute()}")
        return str(output_file.absolute())


class DeploymentCLI:
    """Command-line interface for deployment management."""

    @staticmethod
    def create_config_from_args() -> DeploymentConfig:
        """Create deployment configuration from command line arguments."""

        import argparse

        parser = argparse.ArgumentParser(description="Advanced Bandits Production Deployment")

        parser.add_argument(
            "--initial-rollout", type=float, default=0.05, help="Initial rollout percentage (default: 0.05)"
        )
        parser.add_argument("--max-rollout", type=float, default=1.0, help="Maximum rollout percentage (default: 1.0)")
        parser.add_argument(
            "--rollout-increment", type=float, default=0.1, help="Rollout increment per step (default: 0.1)"
        )
        parser.add_argument(
            "--rollout-interval", type=int, default=30, help="Minutes between rollout steps (default: 30)"
        )
        parser.add_argument(
            "--domains",
            nargs="+",
            default=["model_routing", "content_analysis", "user_engagement"],
            help="Domains to deploy (default: all)",
        )
        parser.add_argument(
            "--min-success-rate", type=float, default=0.95, help="Minimum success rate threshold (default: 0.95)"
        )
        parser.add_argument(
            "--max-latency-degradation", type=float, default=0.2, help="Maximum latency degradation (default: 0.2)"
        )
        parser.add_argument("--environment", default="production", help="Deployment environment (default: production)")
        parser.add_argument("--deployment-id", help="Custom deployment ID (default: auto-generated)")

        # For demo purposes, use shorter intervals
        parser.add_argument("--demo", action="store_true", help="Use demo settings with shorter intervals")

        args = parser.parse_args()

        config = DeploymentConfig(
            initial_rollout_percentage=args.initial_rollout,
            max_rollout_percentage=args.max_rollout,
            rollout_increment=args.rollout_increment,
            rollout_interval_minutes=args.rollout_interval,
            target_domains=args.domains,
            min_success_rate=args.min_success_rate,
            max_latency_degradation=args.max_latency_degradation,
            environment=args.environment,
            deployment_id=args.deployment_id,
        )

        # Demo mode with faster intervals
        if args.demo:
            config.rollout_interval_minutes = 1  # 1 minute instead of 30
            config.health_check_interval_seconds = 10  # 10 seconds instead of 60
            config.initial_rollout_percentage = 0.2  # Start higher for demo
            config.rollout_increment = 0.3  # Larger increments for demo

        return config


async def main():
    """Main deployment orchestrator."""

    # Create configuration
    config = DeploymentCLI.create_config_from_args()

    print("🚀 Advanced Bandits Production Deployment")
    print("=" * 60)
    print(f"Deployment ID: {config.deployment_id}")
    print(f"Target Domains: {', '.join(config.target_domains)}")
    print(f"Rollout Plan: {config.initial_rollout_percentage:.1%} → {config.max_rollout_percentage:.1%}")
    print(f"Environment: {config.environment}")
    print("=" * 60)

    # Initialize deployment manager
    manager = DeploymentManager(config)

    # Execute deployment
    start_time = time.time()
    success = await manager.deploy()
    total_time = time.time() - start_time

    # Generate and save report
    report_path = manager.save_deployment_report()
    report = manager.get_deployment_report()

    # Display summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)

    status_emoji = "✅" if success else "❌"
    print(f"{status_emoji} Status: {report['deployment_summary']['current_phase']}")
    print(f"⏱️  Duration: {total_time / 60:.1f} minutes")
    print(f"📈 Final Rollout: {report['deployment_summary']['final_rollout_percentage']:.1%}")
    print(f"🏥 Health Status: {report['deployment_summary']['health_status']}")

    if report["deployment_summary"]["rollback_reason"]:
        print(f"🔄 Rollback Reason: {report['deployment_summary']['rollback_reason']}")

    print("\n🎯 Domain Status:")
    for domain in config.target_domains:
        if domain in report["health_metrics"]:
            metrics = report["health_metrics"][domain]
            print(f"  {domain}:")
            print(f"    Success Rate: {metrics['success_rate']:.3f}")
            print(f"    Avg Latency: {metrics['average_latency_ms']:.0f}ms")
            print(f"    Avg Reward: {metrics['average_reward']:.3f}")

    print("\n💡 Recommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")

    print(f"\n📁 Report saved: {report_path}")

    if success:
        print("\n🎉 Deployment completed successfully!")
        return 0
    else:
        print("\n💥 Deployment failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
