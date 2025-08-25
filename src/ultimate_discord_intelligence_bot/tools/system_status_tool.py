"""Utilities for gathering basic host metrics.

This lightweight tool avoids external dependencies by relying solely on the
Python standard library. It captures CPU load averages, disk utilisation and
memory consumption so the monitoring agent can surface resource pressure in
Discord alerts.
"""

import os
import platform
import shutil
from typing import Dict

from crewai_tools import BaseTool


class SystemStatusTool(BaseTool):
    """Collect simple system metrics."""

    name: str = "System Status Tool"
    description: str = (
        "Return CPU load averages, disk usage and memory statistics"
    )

    def _get_memory(self) -> Dict[str, float]:
        """Read memory usage from /proc/meminfo if available."""
        mem_total = mem_free = 0.0
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as fh:
                info: Dict[str, float] = {}
                for line in fh:
                    key, value = line.split(":", 1)
                    info[key.strip()] = float(value.strip().split()[0]) * 1024
            mem_total = info.get("MemTotal", 0.0)
            mem_free = info.get("MemAvailable", info.get("MemFree", 0.0))
        except Exception:
            pass
        mem_used = mem_total - mem_free if mem_total else 0.0
        return {
            "mem_total": mem_total,
            "mem_used": mem_used,
            "mem_free": mem_free,
        }

    def _run(self) -> Dict[str, float]:
        try:
            load1, load5, load15 = os.getloadavg()
        except (AttributeError, OSError):
            load1 = load5 = load15 = 0.0

        disk = shutil.disk_usage("/")
        memory = self._get_memory()
        return {
            "status": "success",
            "platform": platform.system(),
            "load_avg_1m": load1,
            "load_avg_5m": load5,
            "load_avg_15m": load15,
            "disk_total": float(disk.total),
            "disk_used": float(disk.used),
            "disk_free": float(disk.free),
            **memory,
        }

    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
