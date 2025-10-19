"""Monitoring orchestration strategy for platform content monitoring.

Implements real-time monitoring across multiple platforms with intelligent
scheduling, content velocity tracking, and automated content processing.
"""

from __future__ import annotations

import logging
from typing import Any

from ultimate_discord_intelligence_bot.services.monitoring_orchestrator import (
    RealTimeMonitoringOrchestrator,
)
from ultimate_discord_intelligence_bot.step_result import StepResult

logger = logging.getLogger(__name__)


class MonitoringStrategy:
    """Monitoring orchestration strategy.

    Provides platform monitoring with:
    - Real-time content discovery
    - Intelligent scheduling per platform
    - Priority-based monitoring
    - Automated content processing
    - Multi-platform coordination
    """

    name: str = "monitoring"
    description: str = "Real-time platform monitoring with intelligent scheduling"

    def __init__(self):
        """Initialize monitoring strategy."""
        self._orchestrator = RealTimeMonitoringOrchestrator()
        logger.info("MonitoringStrategy initialized")

    async def execute_workflow(
        self,
        url: str,
        depth: str = "standard",
        tenant: str = "default",
        workspace: str = "main",
        **kwargs: Any,
    ) -> StepResult:
        """Execute monitoring workflow.

        Args:
            url: Platform URL or identifier to monitor
            depth: Monitoring depth (frequency)
            tenant: Tenant identifier
            workspace: Workspace identifier
            **kwargs: Additional parameters (platform, creators, interval_minutes)

        Returns:
            StepResult with monitoring status
        """
        from obs.metrics import get_metrics

        metrics = get_metrics()
        metrics.counter(
            "orchestration_strategy_executions_total",
            labels={"strategy": self.name, "outcome": "started"},
        )

        try:
            logger.info(
                f"Executing monitoring workflow: url={url}, tenant={tenant}, workspace={workspace}"
            )

            # Extract platform from kwargs or URL
            platform = kwargs.get("platform", self._extract_platform_from_url(url))

            # Start monitoring orchestrator if not already running
            start_result = await self._orchestrator.start_monitoring(
                tenant=tenant, workspace=workspace
            )

            if not start_result.success and "already running" not in (
                start_result.error or ""
            ):
                return StepResult.fail(
                    f"Failed to start monitoring: {start_result.error}",
                    step="monitoring_start",
                )

            # Check if specific platform monitoring is requested
            if platform:
                # Monitor specific platform
                monitor_result = await self._orchestrator.monitor_platform(
                    platform=platform,
                    creators=kwargs.get("creators", []),
                    priority=kwargs.get("priority", 2),
                )

                if monitor_result.success:
                    metrics.counter(
                        "orchestration_strategy_executions_total",
                        labels={"strategy": self.name, "outcome": "success"},
                    )
                    return StepResult.ok(
                        platform=platform,
                        monitoring_result=monitor_result.data,
                        mode="monitoring",
                        message=f"Platform {platform} monitoring completed",
                    )
                else:
                    return StepResult.fail(
                        f"Platform monitoring failed: {monitor_result.error}",
                        platform=platform,
                        step="platform_monitoring",
                    )
            else:
                # Return monitoring status
                return StepResult.ok(
                    monitoring_active=True,
                    tenant=tenant,
                    workspace=workspace,
                    mode="monitoring",
                    message="Monitoring orchestrator is active",
                )

        except Exception as exc:
            logger.error(f"Monitoring workflow failed: {exc}", exc_info=True)
            metrics.counter(
                "orchestration_strategy_executions_total",
                labels={"strategy": self.name, "outcome": "failure"},
            )
            return StepResult.fail(
                f"Monitoring orchestration failed: {exc}",
                step="monitoring_workflow",
            )

    def _extract_platform_from_url(self, url: str) -> str | None:
        """Extract platform identifier from URL.

        Args:
            url: Platform URL

        Returns:
            Platform identifier or None
        """
        url_lower = url.lower()

        platform_patterns = {
            "youtube": ["youtube.com", "youtu.be"],
            "twitch": ["twitch.tv"],
            "tiktok": ["tiktok.com"],
            "instagram": ["instagram.com"],
            "twitter": ["twitter.com", "x.com"],
            "reddit": ["reddit.com"],
            "discord": ["discord.com", "discord.gg"],
        }

        for platform, patterns in platform_patterns.items():
            if any(pattern in url_lower for pattern in patterns):
                return platform

        return None

    async def initialize(self) -> None:
        """Initialize strategy resources."""
        logger.info("MonitoringStrategy resources initialized")

    async def cleanup(self) -> None:
        """Cleanup strategy resources."""
        # Stop monitoring orchestrator
        try:
            await self._orchestrator.stop_monitoring()
        except Exception as exc:
            logger.warning(f"Error stopping monitoring: {exc}")

        logger.info("MonitoringStrategy resources cleaned up")


__all__ = ["MonitoringStrategy"]
