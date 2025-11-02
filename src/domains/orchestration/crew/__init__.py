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
from domains.orchestration.crew.compat import CrewAdapter, UltimateDiscordIntelligenceBotCrew, UltimateDiscordIntelligenceBotCrewAdapter
from domains.orchestration.crew.error_handling import CrewErrorHandler
from domains.orchestration.crew.executor import UnifiedCrewExecutor
from domains.orchestration.crew.factory import DefaultCrewFactory, get_crew_factory
from domains.orchestration.crew.insights import CrewInsightGenerator
from domains.orchestration.crew.interfaces import CrewConfig, CrewExecutionResult, CrewExecutor, CrewFactory, CrewTask

def get_crew() -> UltimateDiscordIntelligenceBotCrewAdapter:
    """Get the default crew instance for backward compatibility.

    This function provides backward compatibility for code using the old
    `get_crew()` pattern from legacy crew.py files.

    Returns:
        UltimateDiscordIntelligenceBotCrewAdapter: A configured crew adapter instance

    Example:
        >>> from ultimate_discord_intelligence_bot.crew_core import get_crew
        >>> crew = get_crew()
        >>> crew_obj = crew.crew()
        >>> result = crew_obj.kickoff(inputs={"url": "..."})
    """
    return UltimateDiscordIntelligenceBotCrewAdapter()
__all__ = ['CrewAdapter', 'CrewConfig', 'CrewErrorHandler', 'CrewExecutionResult', 'CrewExecutor', 'CrewFactory', 'CrewInsightGenerator', 'CrewTask', 'DefaultCrewFactory', 'UltimateDiscordIntelligenceBotCrew', 'UltimateDiscordIntelligenceBotCrewAdapter', 'UnifiedCrewExecutor', 'get_crew', 'get_crew_factory']
__version__ = '1.0.0'