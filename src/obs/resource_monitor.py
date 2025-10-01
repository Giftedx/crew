"""Resource usage monitoring for system performance tracking.

This module provides resource monitoring capabilities for CPU, memory, and disk usage,
integrating with the existing Prometheus metrics infrastructure.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any

# Import metrics registry for accessing metric instances
try:
    from .metrics import GAUGE
    from .metrics import registry as _metrics_registry
except ImportError:
    _metrics_registry = None

    # Create a no-op GAUGE for fallback
    def GAUGE(*args, **kwargs):
        class NoOpGauge:
            def labels(self, *args, **kwargs):
                return self

            def set(self, *args, **kwargs):
                pass

        return NoOpGauge()


logger = logging.getLogger(__name__)


# Resource monitoring metrics
RESOURCE_METRICS = {
    "memory_usage_percent": GAUGE("system_memory_usage_percent", "System memory utilization percentage", ["hostname"]),
    "cpu_usage_percent": GAUGE("system_cpu_usage_percent", "System CPU utilization percentage", ["hostname"]),
    "disk_usage_percent": GAUGE(
        "system_disk_usage_percent", "System disk utilization percentage", ["hostname", "mount_point"]
    ),
    "disk_free_bytes": GAUGE("system_disk_free_bytes", "System disk free space in bytes", ["hostname", "mount_point"]),
    "memory_available_bytes": GAUGE("system_memory_available_bytes", "System available memory in bytes", ["hostname"]),
    "cpu_load_average": GAUGE("system_cpu_load_average", "System CPU load average (1min)", ["hostname"]),
}


class ResourceMonitor:
    """Monitor system resource usage and report to metrics."""

    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self.hostname = os.uname().nodename
        self._stop_event = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._metrics_registry = _metrics_registry

    def start(self) -> None:
        """Start resource monitoring in a background thread."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("Resource monitor already running")
            return

        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ResourceMonitor")
        self._monitor_thread.start()
        logger.info(f"Resource monitor started (interval: {self.interval_seconds}s)")

    def stop(self) -> None:
        """Stop resource monitoring."""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        logger.info("Resource monitor stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._collect_and_report_metrics()
                self._stop_event.wait(self.interval_seconds)
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
                self._stop_event.wait(30)  # Wait longer on error

    def _collect_and_report_metrics(self) -> None:
        """Collect and report current resource metrics."""
        try:
            # Memory metrics
            memory_info = self._get_memory_info()
            if memory_info:
                self._report_memory_metrics(memory_info)

            # CPU metrics
            cpu_info = self._get_cpu_info()
            if cpu_info:
                self._report_cpu_metrics(cpu_info)

            # Disk metrics
            disk_info = self._get_disk_info()
            if disk_info:
                self._report_disk_metrics(disk_info)

        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")

    def _get_memory_info(self) -> dict[str, float] | None:
        """Get memory usage information."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            return {
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "usage_percent": memory.percent,
            }
        except ImportError:
            logger.debug("psutil not available for memory monitoring")
            return None
        except Exception as e:
            logger.error(f"Error getting memory info: {e}")
            return None

    def _get_cpu_info(self) -> dict[str, float] | None:
        """Get CPU usage information."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1.0)
            load_avg = os.getloadavg()[0] if hasattr(os, "getloadavg") else 0.0
            return {
                "usage_percent": cpu_percent,
                "load_average": load_avg,
            }
        except ImportError:
            logger.debug("psutil not available for CPU monitoring")
            return None
        except Exception as e:
            logger.error(f"Error getting CPU info: {e}")
            return None

    def _get_disk_info(self) -> dict[str, dict[str, float]] | None:
        """Get disk usage information for mounted filesystems."""
        try:
            import psutil

            disk_info = {}

            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        "total_bytes": usage.total,
                        "free_bytes": usage.free,
                        "used_bytes": usage.used,
                        "usage_percent": usage.percent,
                    }
                except (PermissionError, OSError):
                    # Skip partitions we can't access
                    continue

            return disk_info if disk_info else None
        except ImportError:
            logger.debug("psutil not available for disk monitoring")
            return None
        except Exception as e:
            logger.error(f"Error getting disk info: {e}")
            return None

    def _report_memory_metrics(self, memory_info: dict[str, float]) -> None:
        """Report memory metrics to Prometheus."""
        try:
            # Use the metrics registry to report values
            metrics = self._metrics_registry

            # Set memory usage percentage
            if hasattr(metrics, "system_memory_usage_percent"):
                metrics.system_memory_usage_percent.labels(hostname=self.hostname).set(memory_info["usage_percent"])

            # Set available memory bytes
            if hasattr(metrics, "system_memory_available_bytes"):
                metrics.system_memory_available_bytes.labels(hostname=self.hostname).set(memory_info["available_bytes"])

        except Exception as e:
            logger.error(f"Error reporting memory metrics: {e}")

    def _report_cpu_metrics(self, cpu_info: dict[str, float]) -> None:
        """Report CPU metrics to Prometheus."""
        try:
            # Use the metrics registry to report values
            metrics = self._metrics_registry

            # Set CPU usage percentage
            if hasattr(metrics, "system_cpu_usage_percent"):
                metrics.system_cpu_usage_percent.labels(hostname=self.hostname).set(cpu_info["usage_percent"])

            # Set CPU load average
            if hasattr(metrics, "system_cpu_load_average"):
                metrics.system_cpu_load_average.labels(hostname=self.hostname).set(cpu_info["load_average"])

        except Exception as e:
            logger.error(f"Error reporting CPU metrics: {e}")

    def _report_disk_metrics(self, disk_info: dict[str, dict[str, float]]) -> None:
        """Report disk metrics to Prometheus."""
        try:
            # Use the metrics registry to report values
            metrics = self._metrics_registry

            for mount_point, info in disk_info.items():
                # Set disk usage percentage
                if hasattr(metrics, "system_disk_usage_percent"):
                    metrics.system_disk_usage_percent.labels(hostname=self.hostname, mount_point=mount_point).set(
                        info["usage_percent"]
                    )

                # Set free disk bytes
                if hasattr(metrics, "system_disk_free_bytes"):
                    metrics.system_disk_free_bytes.labels(hostname=self.hostname, mount_point=mount_point).set(
                        info["free_bytes"]
                    )

        except Exception as e:
            logger.error(f"Error reporting disk metrics: {e}")

    def get_current_usage(self) -> dict[str, Any]:
        """Get current resource usage snapshot."""
        usage = {
            "timestamp": time.time(),
            "hostname": self.hostname,
        }

        # Memory info
        memory_info = self._get_memory_info()
        if memory_info:
            usage["memory"] = memory_info

        # CPU info
        cpu_info = self._get_cpu_info()
        if cpu_info:
            usage["cpu"] = cpu_info

        # Disk info
        disk_info = self._get_disk_info()
        if disk_info:
            usage["disk"] = disk_info

        return usage


# Global resource monitor instance
_resource_monitor: ResourceMonitor | None = None
_monitor_lock = threading.Lock()


def get_resource_monitor() -> ResourceMonitor:
    """Get or create the global resource monitor instance."""
    global _resource_monitor

    with _monitor_lock:
        if _resource_monitor is None:
            _resource_monitor = ResourceMonitor()
        return _resource_monitor


def start_resource_monitoring(interval_seconds: int = 60) -> None:
    """Start global resource monitoring."""
    monitor = get_resource_monitor()
    monitor.start()


def stop_resource_monitoring() -> None:
    """Stop global resource monitoring."""
    global _resource_monitor

    with _monitor_lock:
        if _resource_monitor:
            _resource_monitor.stop()
            _resource_monitor = None


def get_current_resource_usage() -> dict[str, Any]:
    """Get current resource usage snapshot."""
    monitor = get_resource_monitor()
    return monitor.get_current_usage()


__all__ = [
    "ResourceMonitor",
    "get_resource_monitor",
    "start_resource_monitoring",
    "stop_resource_monitoring",
    "get_current_resource_usage",
]
