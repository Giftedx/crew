"""Service registry for dependency injection and service discovery.

This module provides a centralized registry for managing service dependencies
and enabling dynamic service discovery within the OpenRouter service ecosystem.
"""

from __future__ import annotations

import logging
import threading
from platform.core.step_result import StepResult
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable

    from .facade import OpenRouterServiceFacade
    from .service import OpenRouterService
log = logging.getLogger(__name__)


class ServiceRegistry:
    """Central registry for service dependencies and discovery.

    This registry provides a thread-safe way to register, retrieve, and manage
    service instances throughout the application lifecycle.
    """

    from typing import ClassVar

    _instances: ClassVar[dict[str, Any]] = {}
    _factories: ClassVar[dict[str, Callable[[], Any]]] = {}
    _lock: ClassVar[threading.RLock] = threading.RLock()

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        """Register a service instance.

        Args:
            name: Unique name for the service
            instance: The service instance to register
        """
        with cls._lock:
            cls._instances[name] = instance
            log.debug("Registered service: %s", name)

    @classmethod
    def register_factory(cls, name: str, factory: Callable[[], Any]) -> None:
        """Register a service factory function.

        Args:
            name: Unique name for the service
            factory: Factory function that creates the service instance
        """
        with cls._lock:
            cls._factories[name] = factory
            log.debug("Registered service factory: %s", name)

    @classmethod
    def get(cls, name: str) -> Any | None:
        """Get a registered service instance.

        Args:
            name: Name of the service to retrieve

        Returns:
            The service instance or None if not found
        """
        with cls._lock:
            if name in cls._instances:
                return cls._instances[name]
            if name in cls._factories:
                try:
                    instance = cls._factories[name]()
                    cls._instances[name] = instance
                    log.debug("Created service from factory: %s", name)
                    return instance
                except Exception as e:
                    log.error("Failed to create service from factory %s: %s", name, e)
                    return None
            log.warning("Service not found: %s", name)
            return None

    @classmethod
    def get_or_create(cls, name: str, factory: Callable[[], Any]) -> Any:
        """Get existing service or create new one using factory.

        Args:
            name: Name of the service
            factory: Factory function to create service if not exists

        Returns:
            The service instance
        """
        with cls._lock:
            if name in cls._instances:
                return cls._instances[name]
            try:
                instance = factory()
                cls._instances[name] = instance
                log.debug("Created new service: %s", name)
                return instance
            except Exception as e:
                log.error("Failed to create service %s: %s", name, e)
                raise

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a service instance.

        Args:
            name: Name of the service to unregister

        Returns:
            True if service was unregistered, False if not found
        """
        with cls._lock:
            if name in cls._instances:
                del cls._instances[name]
                log.debug("Unregistered service: %s", name)
                return True
            return False

    @classmethod
    def clear(cls) -> None:
        """Clear all registered services and factories."""
        with cls._lock:
            cls._instances.clear()
            cls._factories.clear()
            log.debug("Cleared all services from registry")

    @classmethod
    def list_services(cls) -> list[str]:
        """List all registered service names.

        Returns:
            List of registered service names
        """
        with cls._lock:
            return list(cls._instances.keys())

    @classmethod
    def list_factories(cls) -> list[str]:
        """List all registered factory names.

        Returns:
            List of registered factory names
        """
        with cls._lock:
            return list(cls._factories.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a service is registered.

        Args:
            name: Name of the service to check

        Returns:
            True if service is registered, False otherwise
        """
        with cls._lock:
            return name in cls._instances or name in cls._factories


class OpenRouterServiceRegistry:
    """Specialized registry for OpenRouter service components."""

    OPENROUTER_SERVICE = "openrouter_service"
    OPENROUTER_FACADE = "openrouter_facade"
    CACHE_MANAGER = "cache_manager"
    BUDGET_MANAGER = "budget_manager"
    METRICS_COLLECTOR = "metrics_collector"

    @classmethod
    def register_openrouter_service(cls, service: OpenRouterService, **kwargs: Any) -> None:
        """Register the main OpenRouter service.

        Args:
            service: The OpenRouter service instance
            **kwargs: Additional configuration options
        """
        ServiceRegistry.register(cls.OPENROUTER_SERVICE, service)
        if not ServiceRegistry.is_registered(cls.OPENROUTER_FACADE):
            from .facade import OpenRouterServiceFacade

            facade = OpenRouterServiceFacade(service)
            ServiceRegistry.register(cls.OPENROUTER_FACADE, facade)

    @classmethod
    def get_openrouter_service(cls) -> OpenRouterService | None:
        """Get the registered OpenRouter service.

        Returns:
            The OpenRouter service instance or None
        """
        return ServiceRegistry.get(cls.OPENROUTER_SERVICE)

    @classmethod
    def get_openrouter_facade(cls) -> OpenRouterServiceFacade | None:
        """Get the registered OpenRouter service facade.

        Returns:
            The OpenRouter service facade or None
        """
        return ServiceRegistry.get(cls.OPENROUTER_FACADE)

    @classmethod
    def create_default_service(cls, **kwargs: Any) -> OpenRouterService:
        """Create and register a default OpenRouter service.

        Args:
            **kwargs: Configuration options for the service

        Returns:
            The created OpenRouter service instance
        """
        from .service import OpenRouterService

        service = OpenRouterService(**kwargs)
        cls.register_openrouter_service(service)
        return service

    @classmethod
    def get_or_create_service(cls, **kwargs: Any) -> OpenRouterService:
        """Get existing service or create new one.

        Args:
            **kwargs: Configuration options for new service

        Returns:
            The OpenRouter service instance
        """
        existing = cls.get_openrouter_service()
        if existing:
            return existing
        return cls.create_default_service(**kwargs)

    @classmethod
    def health_check(cls) -> StepResult:
        """Perform health check on all registered services.

        Returns:
            StepResult with health status of all services
        """
        try:
            health_status = {}
            service = cls.get_openrouter_service()
            if service:
                health_status["openrouter_service"] = "registered"
            else:
                health_status["openrouter_service"] = "not_registered"
            facade = cls.get_openrouter_facade()
            if facade:
                facade_health = facade.health_check()
                health_status["facade"] = "healthy" if facade_health.success else "unhealthy"
            else:
                health_status["facade"] = "not_registered"
            all_healthy = all(status in ("registered", "healthy") for status in health_status.values())
            if all_healthy:
                return StepResult.ok(data={"status": "healthy", "services": health_status})
            else:
                return StepResult.fail(f"Service health issues: {health_status}")
        except Exception as e:
            return StepResult.fail(f"Health check failed: {e!s}")

    @classmethod
    def get_service_stats(cls) -> dict[str, Any]:
        """Get statistics about registered services.

        Returns:
            Dictionary with service statistics
        """
        return {
            "registered_services": ServiceRegistry.list_services(),
            "registered_factories": ServiceRegistry.list_factories(),
            "openrouter_service_registered": ServiceRegistry.is_registered(cls.OPENROUTER_SERVICE),
            "openrouter_facade_registered": ServiceRegistry.is_registered(cls.OPENROUTER_FACADE),
        }
