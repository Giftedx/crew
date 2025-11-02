"""
Infrastructure-layer resilience orchestration.

Provides enterprise-grade resilience patterns including:
- Circuit breakers
- Retry with exponential backoff
- Adaptive routing
- Health monitoring
- Graceful degradation

This orchestrator manages background health monitoring tasks and integrates
with the unified orchestration framework.
"""
from __future__ import annotations
import asyncio
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeVar
import structlog
from platform.circuit_breaker import CircuitBreaker, CircuitConfig
from platform.error_handling import log_error
from platform.orchestration.protocols import BaseOrchestrator, OrchestrationContext, OrchestrationLayer, OrchestrationType
from platform.observability import metrics
from platform.core.step_result import ErrorCategory, StepResult
if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
logger = structlog.get_logger(__name__)
T = TypeVar('T')

class ResilienceStrategy(Enum):
    """Resilience execution strategies."""
    FAIL_FAST = 'fail_fast'
    GRACEFUL_DEGRADE = 'graceful_degrade'
    RETRY = 'retry'
    CIRCUIT_BREAKER = 'circuit_breaker'
    ADAPTIVE_ROUTING = 'adaptive_routing'

@dataclass
class ServiceHealth:
    """Tracks health metrics for a service."""
    success_count: int = 0
    error_count: int = 0
    total_requests: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_check: float = field(default_factory=time.time)
    is_healthy: bool = True

@dataclass
class ResilienceConfig:
    """Configuration for resilience orchestrator."""
    max_retry_attempts: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 30.0
    retry_jitter: bool = True
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    health_check_interval: float = 30.0
    health_success_threshold: float = 0.7
    health_latency_threshold: float = 5.0
    enable_adaptive_routing: bool = True
    routing_weight_min: float = 0.1
    routing_weight_max: float = 2.0

class ResilienceOrchestrator(BaseOrchestrator):
    """
    Infrastructure-layer orchestrator for resilience patterns.

    Provides circuit breaking, retries, adaptive routing, and health monitoring.
    Manages background tasks for continuous health assessment.
    """

    def __init__(self, config: ResilienceConfig | None=None) -> None:
        """
        Initialize resilience orchestrator.

        Args:
            config: Optional resilience configuration.
        """
        super().__init__(layer=OrchestrationLayer.INFRASTRUCTURE, name='resilience', orchestration_type=OrchestrationType.ADAPTIVE)
        self.config = config or ResilienceConfig()
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.service_health: dict[str, ServiceHealth] = {}
        self.routing_weights: defaultdict[str, float] = defaultdict(lambda: 1.0)
        self._background_tasks: set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        self._monitoring_started = False
        logger.info('resilience_orchestrator_initialized', config={'max_retry_attempts': self.config.max_retry_attempts, 'health_check_interval': self.config.health_check_interval, 'enable_adaptive_routing': self.config.enable_adaptive_routing})

    async def orchestrate(self, context: OrchestrationContext, **kwargs: Any) -> StepResult:
        """
        Execute with resilience patterns.

        Expected kwargs:
            service_name (str): Name of service being executed
            primary_func (Callable): Primary function to execute
            fallback_func (Callable | None): Optional fallback function
            strategy (ResilienceStrategy): Resilience strategy to apply

        Args:
            context: Orchestration context with tenant and request info.
            **kwargs: Execution parameters.

        Returns:
            StepResult with execution outcome.
        """
        if not self._monitoring_started:
            self._start_health_monitoring()
        self._log_orchestration_start(context, **kwargs)
        service_name = kwargs.get('service_name')
        primary_func = kwargs.get('primary_func')
        fallback_func = kwargs.get('fallback_func')
        strategy = kwargs.get('strategy', ResilienceStrategy.FAIL_FAST)
        if not service_name:
            result = StepResult.fail('Missing required parameter: service_name', error_category=ErrorCategory.PROCESSING)
            self._log_orchestration_end(context, result)
            return result
        if not primary_func:
            result = StepResult.fail('Missing required parameter: primary_func', error_category=ErrorCategory.PROCESSING)
            self._log_orchestration_end(context, result)
            return result
        start_time = time.time()
        result: StepResult
        try:
            if strategy == ResilienceStrategy.FAIL_FAST:
                data = await self._execute_fail_fast(service_name, primary_func)
            elif strategy == ResilienceStrategy.GRACEFUL_DEGRADE:
                data = await self._execute_graceful_degrade(service_name, primary_func, fallback_func)
            elif strategy == ResilienceStrategy.RETRY:
                data = await self._execute_with_retry(service_name, primary_func)
            elif strategy == ResilienceStrategy.CIRCUIT_BREAKER:
                data = await self._execute_with_circuit_breaker(service_name, primary_func, fallback_func)
            elif strategy == ResilienceStrategy.ADAPTIVE_ROUTING:
                data = await self._execute_with_adaptive_routing(service_name, primary_func, **kwargs)
            else:
                result = StepResult.fail(f'Unknown resilience strategy: {strategy}', error_category=ErrorCategory.PROCESSING)
                self._log_orchestration_end(context, result)
                return result
            execution_time = time.time() - start_time
            self._record_success(service_name, execution_time)
            result = StepResult.ok(result={'service': service_name, 'strategy': strategy.value, 'execution_time': execution_time, 'data': data})
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_failure(service_name, execution_time, e)
            result = StepResult.fail(f'Resilience execution failed: {e}', error_category=ErrorCategory.PROCESSING, metadata={'service': service_name, 'strategy': strategy.value, 'execution_time': execution_time, 'error': str(e)})
        self._log_orchestration_end(context, result)
        return result

    async def cleanup(self) -> None:
        """
        Clean shutdown of orchestrator and background tasks.

        Cancels health monitoring, waits for task completion, and
        closes circuit breakers.
        """
        logger.info('shutting_down_resilience_orchestrator')
        self._shutdown_event.set()
        for task in self._background_tasks:
            if not task.done():
                task.cancel()
        if self._background_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*self._background_tasks, return_exceptions=True), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning('background_tasks_cleanup_timeout')
        for name, cb in self.circuit_breakers.items():
            if hasattr(cb, 'shutdown'):
                try:
                    await cb.shutdown()
                except Exception as e:
                    logger.warning('circuit_breaker_shutdown_failed', cb=name, error=str(e))
        logger.info('resilience_orchestrator_shutdown_complete')

    def _start_health_monitoring(self) -> None:
        """Start background health monitoring task."""
        if self._monitoring_started:
            return
        try:
            task = asyncio.create_task(self._health_monitor_loop())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            self._monitoring_started = True
            logger.info('health_monitoring_started')
        except RuntimeError as e:
            logger.warning('health_monitoring_deferred', reason=str(e))

    async def _execute_fail_fast(self, service_name: str, func: Callable[..., Awaitable[T]]) -> T:
        """Execute without retries or fallbacks."""
        return await func()

    async def _execute_graceful_degrade(self, service_name: str, primary_func: Callable[..., Awaitable[T]], fallback_func: Callable[..., Awaitable[T]] | None) -> T:
        """Try primary, immediately fall back on failure."""
        try:
            return await primary_func()
        except Exception as e:
            logger.warning('primary_function_failed_using_fallback', service=service_name, error=str(e))
            if fallback_func:
                return await fallback_func()
            raise

    async def _execute_with_retry(self, service_name: str, func: Callable[..., Awaitable[T]]) -> T:
        """Execute with exponential backoff and jitter."""
        last_error: Exception | None = None
        for attempt in range(self.config.max_retry_attempts):
            try:
                return await func()
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retry_attempts - 1:
                    delay = min(self.config.base_retry_delay * 2 ** attempt, self.config.max_retry_delay)
                    if self.config.retry_jitter:
                        delay *= random.uniform(0.5, 1.5)
                    logger.warning('retry_attempt', service=service_name, attempt=attempt + 1, max_attempts=self.config.max_retry_attempts, delay=delay, error=str(e))
                    await asyncio.sleep(delay)
        logger.error('all_retries_failed', service=service_name, attempts=self.config.max_retry_attempts)
        if last_error:
            raise last_error
        raise RuntimeError(f'All retries failed for {service_name}')

    async def _execute_with_circuit_breaker(self, service_name: str, primary_func: Callable[..., Awaitable[T]], fallback_func: Callable[..., Awaitable[T]] | None) -> T:
        """Execute with circuit breaker pattern."""
        cb = self._get_or_create_circuit_breaker(service_name, fallback_func)
        return await cb.execute(primary_func)

    async def _execute_with_adaptive_routing(self, service_name: str, func: Callable[..., Awaitable[T]], **kwargs: Any) -> T:
        """Execute with adaptive routing based on health."""
        if not self._is_service_healthy(service_name):
            logger.warning('service_unhealthy_enabling_degraded_mode', service=service_name)
        weight = self.routing_weights[service_name]
        logger.debug('adaptive_routing', service=service_name, weight=weight)
        return await func()

    def _get_or_create_circuit_breaker(self, service_name: str, fallback_func: Callable[..., Awaitable[T]] | None) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            config = CircuitConfig(failure_threshold=self.config.failure_threshold, recovery_timeout=self.config.recovery_timeout, success_threshold=self.config.success_threshold)
            self.circuit_breakers[service_name] = CircuitBreaker(name=service_name, config=config, fallback_func=fallback_func)
        return self.circuit_breakers[service_name]

    def _get_or_create_service_health(self, service_name: str) -> ServiceHealth:
        """Get or create health tracker for service."""
        if service_name not in self.service_health:
            self.service_health[service_name] = ServiceHealth()
        return self.service_health[service_name]

    def _record_success(self, service_name: str, execution_time: float) -> None:
        """Record successful execution."""
        health = self._get_or_create_service_health(service_name)
        health.success_count += 1
        health.total_requests += 1
        health.response_times.append(execution_time)
        health.last_check = time.time()
        self._update_routing_weight(service_name, success=True, latency=execution_time)
        try:
            with metrics.label_ctx(service=service_name, outcome='success'):
                metrics.RESILIENCE_REQUESTS.inc()
                metrics.RESILIENCE_LATENCY.observe(execution_time)
        except Exception as e:
            logger.warning('metrics_publish_failed', error=str(e))

    def _record_failure(self, service_name: str, execution_time: float, error: Exception) -> None:
        """Record failed execution."""
        health = self._get_or_create_service_health(service_name)
        health.error_count += 1
        health.total_requests += 1
        health.response_times.append(execution_time)
        health.last_check = time.time()
        self._update_routing_weight(service_name, success=False, latency=execution_time)
        log_error(error, {'service': service_name, 'execution_time': execution_time})
        try:
            with metrics.label_ctx(service=service_name, outcome='failure'):
                metrics.RESILIENCE_REQUESTS.inc()
                metrics.RESILIENCE_ERRORS.inc()
                metrics.RESILIENCE_LATENCY.observe(execution_time)
        except Exception as e:
            logger.warning('metrics_publish_failed', error=str(e))

    def _is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy based on metrics."""
        health = self.service_health.get(service_name)
        if not health or health.total_requests == 0:
            return True
        success_rate = health.success_count / health.total_requests
        if success_rate < self.config.health_success_threshold:
            return False
        if health.response_times:
            avg_response_time = sum(health.response_times) / len(health.response_times)
            if avg_response_time > self.config.health_latency_threshold:
                return False
        return True

    def _update_routing_weight(self, service_name: str, success: bool, latency: float) -> None:
        """Update routing weight based on performance."""
        if not self.config.enable_adaptive_routing:
            return
        current_weight = self.routing_weights[service_name]
        if success and latency < self.config.health_latency_threshold:
            new_weight = min(current_weight * 1.1, self.config.routing_weight_max)
        else:
            new_weight = max(current_weight * 0.9, self.config.routing_weight_min)
        self.routing_weights[service_name] = new_weight

    async def _health_monitor_loop(self) -> None:
        """Background task for continuous health monitoring."""
        logger.info('health_monitor_started')
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()
            except Exception as e:
                logger.error('health_check_failed', error=str(e))
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.config.health_check_interval)
                break
            except asyncio.TimeoutError:
                pass
        logger.info('health_monitor_stopped')

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all tracked services."""
        for service_name, health in self.service_health.items():
            was_healthy = health.is_healthy
            is_healthy = self._is_service_healthy(service_name)
            health.is_healthy = is_healthy
            if was_healthy != is_healthy:
                logger.info('service_health_changed', service=service_name, old_status='healthy' if was_healthy else 'unhealthy', new_status='healthy' if is_healthy else 'unhealthy', success_rate=health.success_count / health.total_requests if health.total_requests > 0 else 0)

    def get_health_summary(self) -> dict[str, Any]:
        """
        Get comprehensive health status.

        Returns:
            Dictionary with health information for all services.
        """
        degradation_mode = any((cb.is_open() for cb in self.circuit_breakers.values()))
        return {'degradation_mode': degradation_mode, 'circuit_breakers': {name: {'state': cb.get_state(), 'failure_count': cb.failure_count} for name, cb in self.circuit_breakers.items()}, 'service_health': {name: {'is_healthy': health.is_healthy, 'success_count': health.success_count, 'error_count': health.error_count, 'total_requests': health.total_requests, 'success_rate': health.success_count / health.total_requests if health.total_requests > 0 else 0, 'avg_response_time': sum(health.response_times) / len(health.response_times) if health.response_times else 0} for name, health in self.service_health.items()}}
_resilience_orchestrator: ResilienceOrchestrator | None = None

def get_resilience_orchestrator() -> ResilienceOrchestrator:
    """Get the global resilience orchestrator instance."""
    global _resilience_orchestrator
    if _resilience_orchestrator is None:
        _resilience_orchestrator = ResilienceOrchestrator()
    return _resilience_orchestrator

def resilient_execute(service_name: str, strategy: ResilienceStrategy=ResilienceStrategy.RETRY) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Decorator for adding resilience to async functions.

    Args:
        service_name: Name of the service being executed.
        strategy: Resilience strategy to apply.

    Returns:
        Decorator function.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            orchestrator = get_resilience_orchestrator()
            from platform.orchestration import OrchestrationContext
            context = OrchestrationContext(tenant_id='default', request_id=f'decorator-{id(func)}')
            result = await orchestrator.orchestrate(context, service_name=service_name, primary_func=lambda: func(*args, **kwargs), fallback_func=None, strategy=strategy)
            if not result.success:
                raise RuntimeError(result.error or 'Resilience execution failed')
            return result.data.get('data')
        return wrapper
    return decorator