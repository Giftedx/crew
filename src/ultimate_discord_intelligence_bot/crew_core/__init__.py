"""Unified crew core components.

This package consolidates all crew execution logic from the legacy crew*.py files
into a cohesive, maintainable structure following 2025 best practices.

Architecture:
- interfaces.py: Core protocols and data classes
- executor.py: Unified execution logic
- factory.py: Factory for creating executors
- error_handling.py: Consolidated error handling
- insights.py: Insight generation helpers

Migration from legacy:
- crew.py -> executor.py (main logic)
- crew_new.py -> executor.py (merged)
- crew_modular.py -> executor.py (merged)
- crew_refactored.py -> executor.py (merged)
- crew_consolidation.py -> executor.py (merged)
- crew_error_handler.py -> error_handling.py
- crew_insight_helpers.py -> insights.py
"""

from ultimate_discord_intelligence_bot.crew_core.compat import (
    CrewAdapter,
    UltimateDiscordIntelligenceBotCrew,
    UltimateDiscordIntelligenceBotCrewAdapter,
)
from ultimate_discord_intelligence_bot.crew_core.error_handling import (
    CrewErrorHandler,
)
from ultimate_discord_intelligence_bot.crew_core.executor import (
    UnifiedCrewExecutor,
)
from ultimate_discord_intelligence_bot.crew_core.factory import (
    DefaultCrewFactory,
    get_crew_factory,
)
from ultimate_discord_intelligence_bot.crew_core.insights import (
    CrewInsightGenerator,
)
from ultimate_discord_intelligence_bot.crew_core.interfaces import (
    CrewConfig,
    CrewExecutionResult,
    CrewExecutor,
    CrewFactory,
    CrewTask,
)


__all__ = [
    # Compatibility Layer (legacy crew.py API)
    "CrewAdapter",
    "UltimateDiscordIntelligenceBotCrew",
    "UltimateDiscordIntelligenceBotCrewAdapter",
    # Interfaces
    "CrewConfig",
    "CrewExecutionResult",
    "CrewExecutor",
    "CrewFactory",
    "CrewTask",
    # Implementations
    "CrewErrorHandler",
    "CrewInsightGenerator",
    "DefaultCrewFactory",
    "UnifiedCrewExecutor",
    "get_crew_factory",
]

__version__ = "1.0.0"
