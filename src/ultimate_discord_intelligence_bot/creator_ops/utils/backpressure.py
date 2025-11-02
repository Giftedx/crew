"""
Backpressure handling for managing system load and preventing overload.
Provides queue depth monitoring and adaptive throttling.
"""
import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from typing import Any, TypeVar
from platform.core.step_result import StepResult
logger = logging.getLogger(__name__)
T = TypeVar('T')

class BackpressureError(Exception):
    """Raised when backpressure limits are exceeded."""

    def __init__(self, message: str, queue_depth: int, max_depth: int):
        super().__init__(message)
        self.queue_depth = queue_depth
        self.max_depth = max_depth

class BackpressureHandler:
    """
    Handles backpressure by monitoring queue depths and applying throttling.

    Prevents system overload by rejecting requests when queues are full
    and implementing adaptive throttling based on system load.
    """

    def __init__(self, max_queue_depth: int=100, warning_threshold: float=0.7, critical_threshold: float=0.9, name: str='backpressure_handler'):
        """
        Initialize backpressure handler.

        Args:
            max_queue_depth: Maximum allowed queue depth
            warning_threshold: Warning threshold as fraction of max depth
            critical_threshold: Critical threshold as fraction of max depth
            name: Name for logging
        """
        self.max_queue_depth = max_queue_depth
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.name = name
        self.warning_depth = int(max_queue_depth * warning_threshold)
        self.critical_depth = int(max_queue_depth * critical_threshold)
        self.current_depth = 0
        self.depth_history: deque[tuple[float, int]] = deque(maxlen=100)
        self.throttle_factor = 1.0
        self.last_throttle_adjustment = time.time()
        self.throttle_adjustment_interval = 5.0
        self._lock = asyncio.Lock()

    async def acquire(self, required_slots: int=1) -> bool:
        """
        Try to acquire slots in the queue.

        Args:
            required_slots: Number of slots needed

        Returns:
            True if slots acquired, False if backpressure limit exceeded
        """
        async with self._lock:
            if self.current_depth + required_slots > self.max_queue_depth:
                logger.warning(f'Backpressure {self.name}: queue full, rejecting request. Current depth: {self.current_depth}, required: {required_slots}, max: {self.max_queue_depth}')
                return False
            self.current_depth += required_slots
            self._record_depth()
            self._adjust_throttling()
            logger.debug(f'Backpressure {self.name}: acquired {required_slots} slots, depth: {self.current_depth}')
            return True

    async def release(self, released_slots: int=1) -> None:
        """
        Release slots from the queue.

        Args:
            released_slots: Number of slots to release
        """
        async with self._lock:
            self.current_depth = max(0, self.current_depth - released_slots)
            self._record_depth()
            self._adjust_throttling()
            logger.debug(f'Backpressure {self.name}: released {released_slots} slots, depth: {self.current_depth}')

    async def wait_for_slots(self, required_slots: int=1, timeout: float | None=None) -> bool:
        """
        Wait for slots to become available.

        Args:
            required_slots: Number of slots needed
            timeout: Maximum time to wait in seconds

        Returns:
            True if slots acquired, False if timeout
        """
        start_time = time.time()
        while True:
            if await self.acquire(required_slots):
                return True
            if timeout and time.time() - start_time >= timeout:
                return False
            await asyncio.sleep(0.1)

    def _record_depth(self) -> None:
        """Record current queue depth with timestamp."""
        now = time.time()
        self.depth_history.append((now, self.current_depth))

    def _adjust_throttling(self) -> None:
        """Adjust throttling based on current queue depth."""
        now = time.time()
        if now - self.last_throttle_adjustment < self.throttle_adjustment_interval:
            return
        self.last_throttle_adjustment = now
        recent_cutoff = now - 30.0
        recent_depths = [depth for timestamp, depth in self.depth_history if timestamp > recent_cutoff]
        if not recent_depths:
            return
        avg_depth = sum(recent_depths) / len(recent_depths)
        if avg_depth > self.critical_depth:
            self.throttle_factor = max(0.1, self.throttle_factor * 0.8)
            logger.warning(f'Backpressure {self.name}: critical load, throttling to {self.throttle_factor:.2f}')
        elif avg_depth > self.warning_depth:
            self.throttle_factor = max(0.3, self.throttle_factor * 0.9)
            logger.info(f'Backpressure {self.name}: high load, throttling to {self.throttle_factor:.2f}')
        elif avg_depth < self.warning_depth * 0.5:
            self.throttle_factor = min(1.0, self.throttle_factor * 1.1)
            if self.throttle_factor > 0.95:
                self.throttle_factor = 1.0
                logger.info(f'Backpressure {self.name}: load normal, throttling disabled')

    async def should_throttle(self) -> bool:
        """
        Check if current request should be throttled.

        Returns:
            True if request should be throttled
        """
        if self.throttle_factor >= 1.0:
            return False
        import random
        return random.random() > self.throttle_factor

    def get_status(self) -> dict[str, Any]:
        """Get current backpressure handler status."""
        recent_cutoff = time.time() - 30.0
        recent_depths = [depth for timestamp, depth in self.depth_history if timestamp > recent_cutoff]
        avg_depth = sum(recent_depths) / len(recent_depths) if recent_depths else 0
        return {'name': self.name, 'current_depth': self.current_depth, 'max_depth': self.max_queue_depth, 'warning_depth': self.warning_depth, 'critical_depth': self.critical_depth, 'average_depth_30s': avg_depth, 'throttle_factor': self.throttle_factor, 'utilization': self.current_depth / self.max_queue_depth, 'status': self._get_status_level()}

    def _get_status_level(self) -> str:
        """Get current status level."""
        if self.current_depth >= self.critical_depth:
            return 'critical'
        elif self.current_depth >= self.warning_depth:
            return 'warning'
        else:
            return 'normal'

class BackpressureManager:
    """Manages multiple backpressure handlers for different services."""

    def __init__(self):
        self.handlers: dict[str, BackpressureHandler] = {}

    def get_handler(self, name: str, max_queue_depth: int=100, warning_threshold: float=0.7, critical_threshold: float=0.9) -> BackpressureHandler:
        """
        Get or create a backpressure handler.

        Args:
            name: Handler name
            max_queue_depth: Maximum queue depth
            warning_threshold: Warning threshold
            critical_threshold: Critical threshold

        Returns:
            Backpressure handler instance
        """
        if name not in self.handlers:
            self.handlers[name] = BackpressureHandler(max_queue_depth=max_queue_depth, warning_threshold=warning_threshold, critical_threshold=critical_threshold, name=name)
        return self.handlers[name]

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all backpressure handlers."""
        return {name: handler.get_status() for name, handler in self.handlers.items()}

    async def cleanup(self) -> None:
        """Clean up expired depth history from all handlers."""
        for handler in self.handlers.values():
            cutoff = time.time() - 300.0
            handler.depth_history = deque([(ts, depth) for ts, depth in handler.depth_history if ts > cutoff], maxlen=100)
backpressure_manager = BackpressureManager()

def with_backpressure(handler_name: str, required_slots: int=1, timeout: float | None=None, manager: BackpressureManager | None=None):
    """
    Decorator to add backpressure handling to functions.

    Args:
        handler_name: Name of backpressure handler to use
        required_slots: Number of slots required
        timeout: Maximum time to wait for slots
        manager: Backpressure manager to use (default: global)
    """
    if manager is None:
        manager = backpressure_manager

    def decorator(func: Callable[..., T]) -> Callable[..., T]:

        async def async_wrapper(*args, **kwargs) -> T:
            handler = manager.get_handler(handler_name)
            if await handler.should_throttle():
                raise BackpressureError(f'Request throttled by backpressure handler {handler_name}', handler.current_depth, handler.max_queue_depth)
            if not await handler.wait_for_slots(required_slots, timeout):
                raise BackpressureError(f'Backpressure limit exceeded for {handler_name}', handler.current_depth, handler.max_queue_depth)
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            finally:
                await handler.release(required_slots)

        def sync_wrapper(*args, **kwargs) -> T:
            handler = manager.get_handler(handler_name)
            if handler.current_depth + required_slots > handler.max_queue_depth:
                raise BackpressureError(f'Backpressure limit exceeded for {handler_name}', handler.current_depth, handler.max_queue_depth)
            handler.current_depth += required_slots
            try:
                return func(*args, **kwargs)
            finally:
                handler.current_depth = max(0, handler.current_depth - required_slots)
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator

def with_result_backpressure(handler_name: str, required_slots: int=1, timeout: float | None=None, manager: BackpressureManager | None=None):
    """
    Decorator to add backpressure handling to StepResult functions.

    Args:
        handler_name: Name of backpressure handler to use
        required_slots: Number of slots required
        timeout: Maximum time to wait for slots
        manager: Backpressure manager to use (default: global)
    """
    if manager is None:
        manager = backpressure_manager

    def decorator(func: Callable[..., StepResult]) -> Callable[..., StepResult]:

        async def async_wrapper(*args, **kwargs) -> StepResult:
            handler = manager.get_handler(handler_name)
            try:
                if await handler.should_throttle():
                    return StepResult.fail(f'Request throttled by backpressure handler {handler_name}')
                if not await handler.wait_for_slots(required_slots, timeout):
                    return StepResult.fail(f'Backpressure limit exceeded for {handler_name}')
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                return StepResult.fail(f'Function failed: {e!s}')
            finally:
                await handler.release(required_slots)

        def sync_wrapper(*args, **kwargs) -> StepResult:
            handler = manager.get_handler(handler_name)
            if handler.current_depth + required_slots > handler.max_queue_depth:
                return StepResult.fail(f'Backpressure limit exceeded for {handler_name}')
            handler.current_depth += required_slots
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                return StepResult.fail(f'Function failed: {e!s}')
            finally:
                handler.current_depth = max(0, handler.current_depth - required_slots)
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator