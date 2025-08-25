"""Utilities for gathering basic host metrics.

This lightweight tool avoids external dependencies by relying solely on the
Python standard library. It captures CPU load averages and disk utilisation
so the monitoring agent can surface resource pressure in Discord alerts.
"""

import os
import platform
import shutil
from typing import Dict

from crewai_tools import BaseTool


class SystemStatusTool(BaseTool):
    """Collect simple system metrics."""

    name: str = "System Status Tool"
    description: str = "Return CPU load averages and disk usage statistics"

    def _run(self) -> Dict[str, float]:
        try:
            load1, load5, load15 = os.getloadavg()
        except (AttributeError, OSError):
            load1 = load5 = load15 = 0.0

        disk = shutil.disk_usage("/")
        return {
            "status": "success",
            "platform": platform.system(),
            "load_avg_1m": load1,
            "load_avg_5m": load5,
            "load_avg_15m": load15,
            "disk_total": float(disk.total),
            "disk_used": float(disk.used),
            "disk_free": float(disk.free),
        }

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
