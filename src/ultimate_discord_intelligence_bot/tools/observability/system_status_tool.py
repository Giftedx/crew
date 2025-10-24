"""Utilities for gathering basic host metrics.

This lightweight tool avoids external dependencies by relying solely on the
Python standard library. It captures CPU load averages, disk utilisation and
memory consumption so the monitoring agent can surface resource pressure in
Discord alerts.
"""

import logging
import os
import platform
import shutil

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

# NOTE: Import order intentionally groups stdlib then third-party for clarity.
from ._base import BaseTool


logger = logging.getLogger(__name__)


class SystemStatusTool(BaseTool[StepResult]):
    """Collect comprehensive system metrics for monitoring and alerting.

    Gathers system performance metrics including CPU load averages, disk usage,
    and memory consumption. Uses lightweight standard library methods to avoid
    external dependencies while providing essential monitoring data.

    Args:
        tenant: Tenant identifier for data isolation
        workspace: Workspace identifier for organization

    Returns:
        StepResult with system metrics including:
        - platform: Operating system name
        - load_avg_1m/5m/15m: CPU load averages
        - disk_total/used/free: Disk space in bytes
        - mem_total/used/free: Memory usage in bytes

    Raises:
        StepResult.fail: If system metrics collection fails

    Example:
        >>> tool = SystemStatusTool()
        >>> result = tool._run()
        >>> assert result.success
        >>> print(f"CPU Load: {result.data['load_avg_1m']}")
    """

    name: str = "System Status Tool"
    description: str = "Return CPU load averages, disk usage and memory statistics"

    def __init__(self) -> None:  # pragma: no cover - trivial init
        super().__init__()
        self._metrics = get_metrics()

    def _get_memory(self) -> dict[str, float]:
        """Read memory usage from /proc/meminfo if available."""
        mem_total = mem_free = 0.0
        try:
            with open("/proc/meminfo", encoding="utf-8") as fh:
                info: dict[str, float] = {}
                for line in fh:
                    key, value = line.split(":", 1)
                    info[key.strip()] = float(value.strip().split()[0]) * 1024
            mem_total = info.get("MemTotal", 0.0)
            mem_free = info.get("MemAvailable", info.get("MemFree", 0.0))
        except Exception as exc:  # pragma: no cover - defensive path
            logger.debug("Failed reading /proc/meminfo: %s", exc)
        mem_used = mem_total - mem_free if mem_total else 0.0
        return {
            "mem_total": mem_total,
            "mem_used": mem_used,
            "mem_free": mem_free,
        }

    def _run(self, tenant: str = "global", workspace: str = "global") -> StepResult:
        """Collect system metrics with comprehensive error handling.

        Args:
            tenant: Tenant identifier for isolation
            workspace: Workspace identifier

        Returns:
            StepResult with system metrics or error information
        """
        from ultimate_discord_intelligence_bot.step_result import ErrorContext

        context = ErrorContext(
            operation="system_metrics_collection",
            component="SystemStatusTool",
            tenant=tenant,
            workspace=workspace,
        )

        try:
            # Get CPU load averages with fallback
            try:
                load1, load5, load15 = os.getloadavg()
            except (AttributeError, OSError):
                load1 = load5 = load15 = 0.0

            # Get disk usage
            disk = shutil.disk_usage("/")

            # Get memory usage
            memory = self._get_memory()

            data = {
                "platform": platform.system(),
                "load_avg_1m": load1,
                "load_avg_5m": load5,
                "load_avg_15m": load15,
                "disk_total": float(disk.total),
                "disk_used": float(disk.used),
                "disk_free": float(disk.free),
                "mem_total": float(memory.get("mem_total", 0.0)),
                "mem_used": float(memory.get("mem_used", 0.0)),
                "mem_free": float(memory.get("mem_free", 0.0)),
            }

            self._metrics.counter("tool_runs_total", labels={"tool": "system_status", "outcome": "success"}).inc()
            return StepResult.ok(data=data)

        except Exception as e:
            self._metrics.counter("tool_runs_total", labels={"tool": "system_status", "outcome": "error"}).inc()
            return StepResult.system_error(
                error=f"Failed to collect system metrics: {e!s}", context=context, platform=platform.system()
            )

    def run(self) -> StepResult:  # pragma: no cover - thin wrapper
        try:
            return self._run()
        except Exception as exc:  # pragma: no cover - unexpected path
            self._metrics.counter("tool_runs_total", labels={"tool": "system_status", "outcome": "error"}).inc()
            return StepResult.fail(error=str(exc), platform="system", command="collect status")
