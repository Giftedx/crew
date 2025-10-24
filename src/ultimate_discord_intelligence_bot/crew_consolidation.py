"""Crew consolidation shim for unified crew entry points.

This module provides a unified interface for accessing different crew implementations
while maintaining backward compatibility and allowing gradual migration through
feature flags.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .settings import Settings


if TYPE_CHECKING:
    from .crew import UltimateDiscordIntelligenceBotCrew


logger = logging.getLogger(__name__)


class CrewConsolidationShim:
    """Shim for consolidating multiple crew implementations.

    This class provides a unified interface for accessing different crew
    implementations while maintaining backward compatibility. It routes
    to the appropriate crew based on feature flags.
    """

    def __init__(self, settings: Settings | None = None):
        """Initialize crew consolidation shim.

        Args:
            settings: Optional settings instance. If None, creates new one.
        """
        self.settings = settings or Settings()
        self.feature_flags = self.settings.feature_flags
        self._crew_instance: UltimateDiscordIntelligenceBotCrew | None = None

    def get_crew(self) -> UltimateDiscordIntelligenceBotCrew:
        """Get the appropriate crew instance based on feature flags.

        Returns:
            UltimateDiscordIntelligenceBotCrew: The appropriate crew instance.
        """
        if self._crew_instance is not None:
            return self._crew_instance

        # Route to appropriate crew based on feature flags
        if self.feature_flags.ENABLE_CREW_REFACTORED:
            logger.info("Using refactored crew implementation")
            from .crew_refactored import UltimateDiscordIntelligenceBotCrew
        elif self.feature_flags.ENABLE_CREW_MODULAR:
            logger.info("Using modular crew implementation")
            from .crew_modular import UltimateDiscordIntelligenceBotCrew
        elif self.feature_flags.ENABLE_CREW_NEW:
            logger.info("Using new crew implementation")
            from .crew_new import UltimateDiscordIntelligenceBotCrew
        elif self.feature_flags.ENABLE_LEGACY_CREW:
            logger.info("Using legacy crew implementation")
            # Import legacy crew if it exists
            try:
                from .crew_legacy import UltimateDiscordIntelligenceBotCrew
            except ImportError:
                logger.warning("Legacy crew not found, falling back to default")
                from .crew import UltimateDiscordIntelligenceBotCrew
        else:
            # Default to canonical crew
            logger.info("Using canonical crew implementation")
            from .crew import UltimateDiscordIntelligenceBotCrew

        self._crew_instance = UltimateDiscordIntelligenceBotCrew()
        return self._crew_instance

    def get_crew_info(self) -> dict[str, Any]:
        """Get information about the current crew implementation.

        Returns:
            dict: Information about the current crew implementation.
        """
        crew_type = "unknown"

        if self.feature_flags.ENABLE_CREW_REFACTORED:
            crew_type = "refactored"
        elif self.feature_flags.ENABLE_CREW_MODULAR:
            crew_type = "modular"
        elif self.feature_flags.ENABLE_CREW_NEW:
            crew_type = "new"
        elif self.feature_flags.ENABLE_LEGACY_CREW:
            crew_type = "legacy"
        else:
            crew_type = "canonical"

        return {
            "crew_type": crew_type,
            "feature_flags": {
                "ENABLE_LEGACY_CREW": self.feature_flags.ENABLE_LEGACY_CREW,
                "ENABLE_CREW_MODULAR": self.feature_flags.ENABLE_CREW_MODULAR,
                "ENABLE_CREW_REFACTORED": self.feature_flags.ENABLE_CREW_REFACTORED,
                "ENABLE_CREW_NEW": self.feature_flags.ENABLE_CREW_NEW,
            },
            "settings": {
                "environment": self.settings.environment,
                "debug": self.settings.debug,
            },
        }

    def validate_crew_availability(self) -> bool:
        """Validate that the selected crew implementation is available.

        Returns:
            bool: True if crew is available, False otherwise.
        """
        try:
            crew = self.get_crew()
            return crew is not None
        except Exception as e:
            logger.error(f"Failed to get crew instance: {e}")
            return False

    def get_available_crews(self) -> list[str]:
        """Get list of available crew implementations.

        Returns:
            list[str]: List of available crew implementation names.
        """
        available = ["canonical"]  # Always available

        try:
            from .crew_refactored import UltimateDiscordIntelligenceBotCrew

            available.append("refactored")
        except ImportError:
            pass

        try:
            from .crew_modular import UltimateDiscordIntelligenceBotCrew

            available.append("modular")
        except ImportError:
            pass

        try:
            from .crew_new import UltimateDiscordIntelligenceBotCrew

            available.append("new")
        except ImportError:
            pass

        try:
            from .crew_legacy import UltimateDiscordIntelligenceBotCrew

            available.append("legacy")
        except ImportError:
            pass

        return available


# Global shim instance for easy access
_crew_shim: CrewConsolidationShim | None = None


def get_crew_shim() -> CrewConsolidationShim:
    """Get the global crew consolidation shim.

    Returns:
        CrewConsolidationShim: The global crew consolidation shim.
    """
    global _crew_shim
    if _crew_shim is None:
        _crew_shim = CrewConsolidationShim()
    return _crew_shim


def get_crew() -> UltimateDiscordIntelligenceBotCrew:
    """Get the appropriate crew instance.

    Returns:
        UltimateDiscordIntelligenceBotCrew: The appropriate crew instance.
    """
    return get_crew_shim().get_crew()


def get_crew_info() -> dict[str, Any]:
    """Get information about the current crew implementation.

    Returns:
        dict: Information about the current crew implementation.
    """
    return get_crew_shim().get_crew_info()


def validate_crew() -> bool:
    """Validate that the selected crew implementation is available.

    Returns:
        bool: True if crew is available, False otherwise.
    """
    return get_crew_shim().validate_crew_availability()


def get_available_crews() -> list[str]:
    """Get list of available crew implementations.

    Returns:
        list[str]: List of available crew implementation names.
    """
    return get_crew_shim().get_available_crews()


# Backward compatibility aliases
UltimateDiscordIntelligenceBotCrew = get_crew
