"""Compatibility shim for platform.llm.providers.openrouter.facade imports.

Re-exports facade module from openrouter_service subdirectory.
"""

# Re-export everything from the actual facade module
from platform.llm.providers.openrouter.openrouter_service import facade as _mod
from platform.llm.providers.openrouter.openrouter_service.facade import *  # noqa: F403

# Backward compatibility aliases
from platform.llm.providers.openrouter.openrouter_service.facade import (
    FacadeBudgetManager as BudgetManager,
)
from platform.llm.providers.openrouter.openrouter_service.facade import (
    FacadeCacheManager as CacheManager,
)
from platform.llm.providers.openrouter.openrouter_service.facade import (
    FacadeMetricsCollector as MetricsCollector,
)


__all__ = [*getattr(_mod, "__all__", []), "BudgetManager", "CacheManager", "MetricsCollector"]
