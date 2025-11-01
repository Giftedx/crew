"""Framework abstraction layer for multi-framework AI agent support.

This package provides a universal interface for executing AI agent workflows
across multiple frameworks (CrewAI, LangGraph, AutoGen, LlamaIndex) without
changing application code.

Architecture:
- protocols.py: FrameworkAdapter protocol defining the universal interface
- crewai/: CrewAI framework implementation
- langgraph/: LangGraph framework implementation
- autogen/: AutoGen framework implementation
- llamaindex/: LlamaIndex framework implementation
- tools/: Universal tool system for cross-framework tool usage
- state/: Unified state management and persistence

Usage:
    ```python
    from ai.frameworks import get_framework_adapter
    from ultimate_discord_intelligence_bot.crew_core import CrewConfig, CrewTask

    # Get framework adapter (defaults to CrewAI for backward compatibility)
    adapter = get_framework_adapter("crewai")  # or "langgraph", "autogen", "llamaindex"

    # Execute task using any framework
    task = CrewTask(task_id="demo", task_type="analysis", description="Analyze content", inputs={})
    config = CrewConfig(tenant_id="default")
    result = await adapter.execute_task(task, config)
    ```

Key Benefits:
- **Framework Agnostic**: Switch frameworks without code changes
- **Progressive Migration**: Migrate workflows incrementally
- **Best-of-Breed**: Use each framework's strengths optimally
- **Backward Compatible**: Existing CrewAI code continues to work
"""

from __future__ import annotations

from ai.frameworks.protocols import FrameworkAdapter


__all__ = [
    "FrameworkAdapter",
    "get_framework_adapter",
    "list_available_frameworks",
    "register_framework_adapter",
]

# Registry will be populated by framework adapters
_FRAMEWORK_REGISTRY: dict[str, type[FrameworkAdapter]] = {}


# Auto-register available framework adapters
def _auto_register_adapters() -> None:
    """Auto-register all available framework adapters."""
    # Try to register CrewAI adapter
    try:
        from ai.frameworks.crewai import CrewAIFrameworkAdapter

        _FRAMEWORK_REGISTRY["crewai"] = CrewAIFrameworkAdapter
    except ImportError:
        pass  # CrewAI adapter not available

    # Try to register LangGraph adapter (when implemented)
    try:
        from ai.frameworks.langgraph import LangGraphFrameworkAdapter  # type: ignore[attr-defined]

        _FRAMEWORK_REGISTRY["langgraph"] = LangGraphFrameworkAdapter  # type: ignore[assignment]
    except ImportError:
        pass  # LangGraph adapter not available

    # Try to register AutoGen adapter (when implemented)
    try:
        from ai.frameworks.autogen import AutoGenFrameworkAdapter  # type: ignore[attr-defined]

        _FRAMEWORK_REGISTRY["autogen"] = AutoGenFrameworkAdapter  # type: ignore[assignment]
    except ImportError:
        pass  # AutoGen adapter not available

    # Try to register LlamaIndex adapter (when implemented)
    try:
        from ai.frameworks.llamaindex import LlamaIndexFrameworkAdapter  # type: ignore[attr-defined]

        _FRAMEWORK_REGISTRY["llamaindex"] = LlamaIndexFrameworkAdapter  # type: ignore[assignment]
    except ImportError:
        pass  # LlamaIndex adapter not available


def register_framework_adapter(name: str, adapter_class: type[FrameworkAdapter]) -> None:
    """Register a framework adapter implementation.

    Args:
        name: Framework name (e.g., "crewai", "langgraph")
        adapter_class: FrameworkAdapter implementation class
    """
    _FRAMEWORK_REGISTRY[name] = adapter_class


def get_framework_adapter(name: str = "crewai") -> FrameworkAdapter:
    """Get a framework adapter instance by name.

    Args:
        name: Framework name (default: "crewai" for backward compatibility)

    Returns:
        FrameworkAdapter instance

    Raises:
        ValueError: If framework name not registered
    """
    if name not in _FRAMEWORK_REGISTRY:
        raise ValueError(f"Unknown framework: {name}. Available: {list(_FRAMEWORK_REGISTRY.keys())}")
    return _FRAMEWORK_REGISTRY[name]()


def list_available_frameworks() -> list[str]:
    """List all registered framework names.

    Returns:
        List of framework names
    """
    return list(_FRAMEWORK_REGISTRY.keys())


# Auto-register adapters on module import
_auto_register_adapters()
