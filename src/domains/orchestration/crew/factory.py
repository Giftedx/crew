"""Factory for creating crew executors.

This module implements the factory pattern for creating different types
of crew executors based on requirements.
"""

from __future__ import annotations

import structlog

from domains.orchestration.crew.executor import UnifiedCrewExecutor
from domains.orchestration.crew.interfaces import CrewConfig, CrewExecutor, CrewFactory


logger = structlog.get_logger(__name__)


class DefaultCrewFactory(CrewFactory):
    """Default factory for creating crew executors.

    This factory creates instances of crew executors based on the
    requested type. Currently supports:
    - 'unified': UnifiedCrewExecutor (recommended)
    - 'default': Alias for 'unified'
    """

    def __init__(self) -> None:
        """Initialize the factory."""
        self._executors: dict[str, type[CrewExecutor]] = {
            "unified": UnifiedCrewExecutor,
            "default": UnifiedCrewExecutor,
        }
        logger.debug("crew_factory_initialized", available_executors=list(self._executors.keys()))

    def create_executor(self, executor_type: str, config: CrewConfig) -> CrewExecutor:
        """Create a crew executor.

        Args:
            executor_type: Type of executor to create
            config: Configuration for the executor

        Returns:
            A CrewExecutor instance

        Raises:
            ValueError: If executor_type is not supported
        """
        if executor_type not in self._executors:
            available = ", ".join(self._executors.keys())
            msg = f"Unknown executor type: {executor_type}. Available types: {available}"
            logger.error(
                "crew_factory_unknown_type", executor_type=executor_type, available_types=list(self._executors.keys())
            )
            raise ValueError(msg)
        executor_class = self._executors[executor_type]
        executor = executor_class(config)
        logger.info("crew_executor_created", executor_type=executor_type, tenant_id=config.tenant_id)
        return executor

    def get_available_executors(self) -> list[str]:
        """Get list of available executor types.

        Returns:
            List of supported executor type names
        """
        return list(self._executors.keys())

    def register_executor(self, executor_type: str, executor_class: type[CrewExecutor]) -> None:
        """Register a custom executor type.

        Args:
            executor_type: Name for the executor type
            executor_class: Class implementing CrewExecutor
        """
        if executor_type in self._executors:
            logger.warning("crew_factory_executor_override", executor_type=executor_type)
        self._executors[executor_type] = executor_class
        logger.info("crew_factory_executor_registered", executor_type=executor_type)


_factory: DefaultCrewFactory | None = None


def get_crew_factory() -> DefaultCrewFactory:
    """Get the global crew factory instance.

    Returns:
        The singleton factory instance
    """
    global _factory
    if _factory is None:
        _factory = DefaultCrewFactory()
    return _factory
