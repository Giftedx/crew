"""Cross-System Backpressure Coordinator.

This module provides centralized backpressure coordination across all services,
preventing cascading failures by aggregating circuit breaker health and system load.

Key Features:
- Aggregates circuit breaker states from all services (OpenRouter, Qdrant, Redis, Platform APIs)
- Global backpressure mode when ≥2 circuits are OPEN or system load >80%
- Graceful degradation with cached/degraded results instead of failures
- Request rejection at orchestrator entry to prevent resource exhaustion
- Automatic recovery when conditions improve
- Comprehensive metrics and observability

Expected Impact: Prevent cascading failures during overload, maintain system stability

Feature flags:
- ENABLE_BACKPRESSURE_COORDINATOR=1: Enable coordinator (default: enabled)
- BACKPRESSURE_OPEN_CIRCUIT_THRESHOLD=2: Number of open circuits to trigger backpressure
- BACKPRESSURE_LOAD_THRESHOLD=0.8: System load threshold (0.0-1.0)
- BACKPRESSURE_RECOVERY_DELAY=30: Seconds to wait before exiting backpressure mode

Usage:
    coordinator = BackpressureCoordinator()

    # Check if system is under backpressure
    if coordinator.is_backpressure_active():
        return cached_or_degraded_result()

    # Register service health
    coordinator.register_service_health("openrouter", is_healthy=True, circuit_state="CLOSED")

    # Get health summary
    summary = coordinator.get_health_summary()
"""

from __future__ import annotations

import contextlib
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class BackpressureLevel(Enum):
    """Backpressure severity levels."""

    NORMAL = "normal"
    WARNING = "warning"
    ACTIVE = "active"
    CRITICAL = "critical"


@dataclass
class ServiceHealth:
    """Health status for a registered service."""

    service_name: str
    is_healthy: bool
    circuit_state: str
    last_updated: float = field(default_factory=time.time)
    failure_count: int = 0
    success_rate: float = 1.0
    response_time_p95: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BackpressureMetrics:
    """Metrics for backpressure coordinator."""

    total_services: int = 0
    healthy_services: int = 0
    unhealthy_services: int = 0
    open_circuits: int = 0
    half_open_circuits: int = 0
    closed_circuits: int = 0
    system_load: float = 0.0
    backpressure_level: BackpressureLevel = BackpressureLevel.NORMAL
    backpressure_active_duration: float = 0.0
    requests_rejected: int = 0
    degraded_responses_served: int = 0
    last_state_change: float = field(default_factory=time.time)


class BackpressureCoordinator:
    """Centralized coordinator for cross-system backpressure management.

    Aggregates health from all services and enters backpressure mode when:
    - ≥2 circuit breakers are OPEN
    - System load >80%
    - Critical service degradation detected

    In backpressure mode:
    - New requests are rejected at orchestrator entry
    - Cached results are returned when available
    - Degraded responses (partial data) are preferred over failures
    """

    def __init__(
        self,
        open_circuit_threshold: int | None = None,
        load_threshold: float | None = None,
        recovery_delay: float | None = None,
    ):
        """Initialize backpressure coordinator.

        Args:
            open_circuit_threshold: Number of open circuits to trigger backpressure
            load_threshold: System load threshold (0.0-1.0)
            recovery_delay: Seconds to wait before exiting backpressure mode
        """
        self._enabled = os.getenv("ENABLE_BACKPRESSURE_COORDINATOR", "1").lower() in {"1", "true", "yes", "on"}
        self._open_circuit_threshold = (
            open_circuit_threshold
            if open_circuit_threshold is not None
            else int(os.getenv("BACKPRESSURE_OPEN_CIRCUIT_THRESHOLD", "2"))
        )
        self._load_threshold = (
            load_threshold if load_threshold is not None else float(os.getenv("BACKPRESSURE_LOAD_THRESHOLD", "0.8"))
        )
        self._recovery_delay = (
            recovery_delay if recovery_delay is not None else float(os.getenv("BACKPRESSURE_RECOVERY_DELAY", "30"))
        )
        self._services: dict[str, ServiceHealth] = {}
        self._lock = threading.RLock()
        self._backpressure_active = False
        self._backpressure_level = BackpressureLevel.NORMAL
        self._backpressure_start_time: float | None = None
        self._last_backpressure_check = time.time()
        self._metrics = BackpressureMetrics()
        self._prometheus_metrics: Any | None = None
        try:
            from platform.observability.metrics import get_metrics

            metrics = get_metrics()
            self._backpressure_active_gauge = metrics.gauge("backpressure_active")
            self._backpressure_level_gauge = metrics.gauge("backpressure_level")
            self._requests_rejected_counter = metrics.counter("backpressure_requests_rejected_total")
            self._degraded_responses_counter = metrics.counter("backpressure_degraded_responses_total")
            self._open_circuits_gauge = metrics.gauge("backpressure_open_circuits_count")
            self._system_load_gauge = metrics.gauge("backpressure_system_load")
            self._prometheus_metrics = metrics
        except Exception:
            self._backpressure_active_gauge = None
            self._backpressure_level_gauge = None
            self._requests_rejected_counter = None
            self._degraded_responses_counter = None
            self._open_circuits_gauge = None
            self._system_load_gauge = None
        logger.info(
            f"BackpressureCoordinator initialized: enabled={self._enabled}, open_circuit_threshold={self._open_circuit_threshold}, load_threshold={self._load_threshold:.2f}"
        )

    def register_service_health(
        self,
        service_name: str,
        is_healthy: bool,
        circuit_state: str = "CLOSED",
        failure_count: int = 0,
        success_rate: float = 1.0,
        response_time_p95: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register or update health status for a service.

        Args:
            service_name: Unique service identifier (e.g., "openrouter", "qdrant")
            is_healthy: Whether the service is currently healthy
            circuit_state: Circuit breaker state ("CLOSED", "OPEN", "HALF_OPEN")
            failure_count: Number of recent failures
            success_rate: Success rate (0.0-1.0)
            response_time_p95: 95th percentile response time in ms
            metadata: Additional service-specific metadata
        """
        with self._lock:
            self._services[service_name] = ServiceHealth(
                service_name=service_name,
                is_healthy=is_healthy,
                circuit_state=circuit_state.upper(),
                last_updated=time.time(),
                failure_count=failure_count,
                success_rate=success_rate,
                response_time_p95=response_time_p95,
                metadata=metadata or {},
            )
            self._update_metrics()

    def unregister_service(self, service_name: str) -> None:
        """Remove a service from health tracking.

        Args:
            service_name: Service to remove
        """
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                self._update_metrics()

    def is_backpressure_active(self) -> bool:
        """Check if backpressure mode is currently active.

        Returns:
            True if backpressure is active, False otherwise
        """
        if not self._enabled:
            return False
        current_time = time.time()
        if current_time - self._last_backpressure_check > 5.0:
            self._evaluate_backpressure()
            self._last_backpressure_check = current_time
        return self._backpressure_active

    def get_backpressure_level(self) -> BackpressureLevel:
        """Get current backpressure severity level.

        Returns:
            Current backpressure level
        """
        return self._backpressure_level

    def record_request_rejected(self) -> None:
        """Record that a request was rejected due to backpressure."""
        with self._lock:
            self._metrics.requests_rejected += 1
            if self._requests_rejected_counter:
                with contextlib.suppress(Exception):
                    self._requests_rejected_counter.inc()

    def record_degraded_response(self) -> None:
        """Record that a degraded response was served."""
        with self._lock:
            self._metrics.degraded_responses_served += 1
            if self._degraded_responses_counter:
                with contextlib.suppress(Exception):
                    self._degraded_responses_counter.inc()

    def get_health_summary(self) -> dict[str, Any]:
        """Get comprehensive health summary.

        Returns:
            Dictionary with health metrics and service statuses
        """
        with self._lock:
            services_summary = {
                name: {
                    "healthy": svc.is_healthy,
                    "circuit_state": svc.circuit_state,
                    "failure_count": svc.failure_count,
                    "success_rate": svc.success_rate,
                    "response_time_p95": svc.response_time_p95,
                    "last_updated": svc.last_updated,
                }
                for name, svc in self._services.items()
            }
            return {
                "backpressure_active": self._backpressure_active,
                "backpressure_level": self._backpressure_level.value,
                "metrics": {
                    "total_services": self._metrics.total_services,
                    "healthy_services": self._metrics.healthy_services,
                    "unhealthy_services": self._metrics.unhealthy_services,
                    "open_circuits": self._metrics.open_circuits,
                    "half_open_circuits": self._metrics.half_open_circuits,
                    "closed_circuits": self._metrics.closed_circuits,
                    "system_load": self._metrics.system_load,
                    "requests_rejected": self._metrics.requests_rejected,
                    "degraded_responses_served": self._metrics.degraded_responses_served,
                    "backpressure_duration_seconds": self._get_backpressure_duration(),
                },
                "services": services_summary,
                "thresholds": {
                    "open_circuit_threshold": self._open_circuit_threshold,
                    "load_threshold": self._load_threshold,
                    "recovery_delay": self._recovery_delay,
                },
            }

    def _update_metrics(self) -> None:
        """Update aggregated metrics from service health."""
        total_services = len(self._services)
        healthy_services = sum(1 for svc in self._services.values() if svc.is_healthy)
        unhealthy_services = total_services - healthy_services
        open_circuits = sum(1 for svc in self._services.values() if svc.circuit_state == "OPEN")
        half_open_circuits = sum(1 for svc in self._services.values() if svc.circuit_state == "HALF_OPEN")
        closed_circuits = sum(1 for svc in self._services.values() if svc.circuit_state == "CLOSED")
        if self._services:
            avg_failure_rate = sum(1.0 - svc.success_rate for svc in self._services.values()) / len(self._services)
            avg_response_time_normalized = sum(
                min(svc.response_time_p95 / 1000.0, 1.0) for svc in self._services.values()
            ) / len(self._services)
            system_load = (avg_failure_rate + avg_response_time_normalized) / 2.0
        else:
            system_load = 0.0
        self._metrics.total_services = total_services
        self._metrics.healthy_services = healthy_services
        self._metrics.unhealthy_services = unhealthy_services
        self._metrics.open_circuits = open_circuits
        self._metrics.half_open_circuits = half_open_circuits
        self._metrics.closed_circuits = closed_circuits
        self._metrics.system_load = system_load
        if self._open_circuits_gauge:
            with contextlib.suppress(Exception):
                self._open_circuits_gauge.set(open_circuits)
        if self._system_load_gauge:
            with contextlib.suppress(Exception):
                self._system_load_gauge.set(system_load)

    def _evaluate_backpressure(self) -> None:
        """Evaluate whether to enter/exit backpressure mode."""
        with self._lock:
            self._update_metrics()
            open_circuits = self._metrics.open_circuits
            system_load = self._metrics.system_load
            should_activate = open_circuits >= self._open_circuit_threshold or system_load >= self._load_threshold
            if should_activate and (not self._backpressure_active):
                self._enter_backpressure_mode(open_circuits, system_load)
            elif not should_activate and self._backpressure_active and self._should_exit_backpressure():
                self._exit_backpressure_mode()
            self._update_backpressure_level(open_circuits, system_load)

    def _enter_backpressure_mode(self, open_circuits: int, system_load: float) -> None:
        """Enter backpressure mode."""
        self._backpressure_active = True
        self._backpressure_start_time = time.time()
        self._metrics.last_state_change = time.time()
        logger.warning(
            f"BACKPRESSURE MODE ACTIVATED: open_circuits={open_circuits}/{self._open_circuit_threshold}, system_load={system_load:.2%}/{self._load_threshold:.2%}"
        )
        if self._backpressure_active_gauge:
            with contextlib.suppress(Exception):
                self._backpressure_active_gauge.set(1)

    def _exit_backpressure_mode(self) -> None:
        """Exit backpressure mode."""
        duration = self._get_backpressure_duration()
        self._backpressure_active = False
        self._backpressure_start_time = None
        self._metrics.last_state_change = time.time()
        logger.info(f"BACKPRESSURE MODE DEACTIVATED after {duration:.1f} seconds")
        if self._backpressure_active_gauge:
            with contextlib.suppress(Exception):
                self._backpressure_active_gauge.set(0)

    def _should_exit_backpressure(self) -> bool:
        """Check if conditions allow exiting backpressure mode."""
        if self._backpressure_start_time is None:
            return True
        time_in_backpressure = time.time() - self._backpressure_start_time
        if time_in_backpressure < self._recovery_delay:
            return False
        return (
            self._metrics.open_circuits < self._open_circuit_threshold
            and self._metrics.system_load < self._load_threshold
        )

    def _update_backpressure_level(self, open_circuits: int, system_load: float) -> None:
        """Update backpressure severity level."""
        if open_circuits >= self._open_circuit_threshold * 2 or system_load >= 0.95:
            level = BackpressureLevel.CRITICAL
        elif open_circuits >= self._open_circuit_threshold or system_load >= self._load_threshold:
            level = BackpressureLevel.ACTIVE
        elif open_circuits >= self._open_circuit_threshold * 0.7 or system_load >= self._load_threshold * 0.8:
            level = BackpressureLevel.WARNING
        else:
            level = BackpressureLevel.NORMAL
        if level != self._backpressure_level:
            logger.info(f"Backpressure level changed: {self._backpressure_level.value} -> {level.value}")
            self._backpressure_level = level
            self._metrics.backpressure_level = level
            if self._backpressure_level_gauge:
                try:
                    level_value = {"normal": 0, "warning": 1, "active": 2, "critical": 3}[level.value]
                    self._backpressure_level_gauge.set(level_value)
                except Exception:
                    pass

    def _get_backpressure_duration(self) -> float:
        """Get duration of current backpressure period in seconds."""
        if self._backpressure_start_time is None:
            return 0.0
        return time.time() - self._backpressure_start_time


_global_coordinator: BackpressureCoordinator | None = None
_coordinator_lock = threading.Lock()


def get_backpressure_coordinator() -> BackpressureCoordinator:
    """Get global backpressure coordinator singleton.

    Returns:
        Global BackpressureCoordinator instance
    """
    global _global_coordinator
    if _global_coordinator is None:
        with _coordinator_lock:
            if _global_coordinator is None:
                _global_coordinator = BackpressureCoordinator()
    return _global_coordinator


__all__ = [
    "BackpressureCoordinator",
    "BackpressureLevel",
    "BackpressureMetrics",
    "ServiceHealth",
    "get_backpressure_coordinator",
]
