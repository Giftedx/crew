"""Agent management utilities for CrewAI orchestration.

This module provides functions for agent creation, caching, and context management
in the autonomous intelligence workflow.

Extracted from crew_builders.py to improve maintainability and organization.
"""

import contextlib
import logging
from typing import Any

from ultimate_discord_intelligence_bot.settings import Settings


# Module-level logger
logger = logging.getLogger(__name__)


def populate_agent_tool_context(
    agent: Any,
    context_data: dict[str, Any],
    logger_instance: logging.Logger | None = None,
    metrics_instance: Any | None = None,
) -> None:
    """Populate shared context on all tool wrappers for an agent.

    This is CRITICAL for CrewAI agents to receive structured data. Without this,
    tools receive empty parameters and fail or return meaningless results.

    Args:
        agent: CrewAI Agent instance with tools attribute
        context_data: Dictionary of data to make available to all tools
        logger_instance: Optional logger instance
        metrics_instance: Optional metrics instance for tracking
    """
    _logger = logger_instance or logger

    if not hasattr(agent, "tools"):
        _logger.warning(f"Agent {getattr(agent, 'role', 'unknown')} has no tools attribute")
        return

    # ENHANCED CONTEXT PROPAGATION LOGGING
    # Show exactly what data is available and what format it's in
    context_summary = {}
    for k, v in context_data.items():
        if isinstance(v, str):
            context_summary[k] = f"str({len(v)} chars)"
        elif isinstance(v, (list, dict)):
            context_summary[k] = f"{type(v).__name__}({len(v)} items)"
        else:
            context_summary[k] = type(v).__name__

    _logger.warning(f"🔧 POPULATING CONTEXT for agent {getattr(agent, 'role', 'unknown')}")
    _logger.warning(f"   📦 Data summary: {context_summary}")

    # Show critical fields with previews
    if "transcript" in context_data:
        preview = str(context_data["transcript"])[:200]
        _logger.warning(f"   📝 Transcript preview: {preview}...")
    if "file_path" in context_data:
        _logger.warning(f"   📁 File path: {context_data['file_path']}")
    if "url" in context_data:
        _logger.warning(f"   🔗 URL: {context_data['url']}")

    # If Mem0 tool is available, add it to the agent's tools
    # This allows agents to access long-term memory dynamically
    try:
        from ..tools.mem0_memory_tool import Mem0MemoryTool

        settings = Settings()
        if settings.enable_enhanced_memory and settings.mem0_api_key:
            if not any(isinstance(t, Mem0MemoryTool) for t in agent.tools):
                agent.tools.append(Mem0MemoryTool())
                _logger.info(f"🧠 Added Mem0MemoryTool to agent: {getattr(agent, 'role', 'unknown')}")
    except ImportError:
        _logger.debug("Mem0MemoryTool not available, skipping.")
    except Exception as e:
        _logger.warning(f"⚠️ Failed to add Mem0MemoryTool to agent: {e}")

    populated_count = 0
    for tool in agent.tools:
        if hasattr(tool, "update_context"):
            tool.update_context(context_data)
            populated_count += 1
            _logger.debug(
                f"✅ Populated context for {getattr(tool, 'name', tool.__class__.__name__)}: "
                f"{list(context_data.keys())}"
            )

    if populated_count > 0:
        _logger.warning(
            f"✅ CONTEXT POPULATED on {populated_count} tools for agent {getattr(agent, 'role', 'unknown')}"
        )
        # Track context population for monitoring
        if metrics_instance:
            with contextlib.suppress(Exception):
                metrics_instance.counter(
                    "autointel_context_populated",
                    labels={
                        "agent": getattr(agent, "role", "unknown"),
                        "tools_count": populated_count,
                        "has_transcript": "transcript" in context_data or "text" in context_data,
                    },
                ).inc()
    else:
        _logger.error(f"❌ CONTEXT POPULATION FAILED: 0 tools updated for agent {getattr(agent, 'role', 'unknown')}")


def get_or_create_agent(
    agent_name: str,
    agent_coordinators: dict[str, Any],
    crew_instance: Any,
    logger_instance: logging.Logger | None = None,
) -> Any:
    """Get agent from coordinators cache or create and cache it.

    CRITICAL: This ensures agents are created ONCE and reused across stages.
    Repeated calls to crew_instance.agent_method() create FRESH agents with
    EMPTY tools, bypassing context population. Always use this method.

    Args:
        agent_name: Name of agent method (e.g., 'analysis_cartographer')
        agent_coordinators: Dictionary to cache agents (will be mutated)
        crew_instance: UltimateDiscordIntelligenceBotCrew instance
        logger_instance: Optional logger instance

    Returns:
        Cached agent instance with persistent tool context

    Raises:
        ValueError: If agent_name doesn't exist in crew_instance
    """
    _logger = logger_instance or logger

    # Return cached agent if available
    if agent_name in agent_coordinators:
        _logger.debug(f"✅ Reusing cached agent: {agent_name}")
        return agent_coordinators[agent_name]

    # Create new agent and cache it
    agent_method = getattr(crew_instance, agent_name, None)
    if not agent_method:
        raise ValueError(f"Unknown agent: {agent_name}")

    agent = agent_method()
    agent_coordinators[agent_name] = agent

    _logger.info(f"✨ Created and cached new agent: {agent_name}")
    return agent
