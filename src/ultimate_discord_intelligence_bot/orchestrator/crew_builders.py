"""Crew building functions for CrewAI agent orchestration.

This module provides functions for building, caching, and configuring CrewAI agents
and crews for the autonomous intelligence workflow.

NOTE: This file has been decomposed into focused modules:
- crew_builders_focused.py - Core crew building logic and task creation
- agent_managers.py - Agent creation, caching, and context management

This file is maintained for backward compatibility.
"""

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Backward Compatibility Imports
# ============================================================================

# Re-export CrewAI types for backward compatibility
from crewai import Crew, Process, Task

# Import functions from the new focused modules for backward compatibility
from .agent_managers import get_or_create_agent, populate_agent_tool_context
from .crew_builders_focused import (
    build_crew_with_tasks,
    build_intelligence_crew,
    create_acquisition_task,
    create_analysis_tasks,
    create_knowledge_integration_task,
    create_transcription_task,
)
from .task_callbacks import task_completion_callback

# Export all functions for backward compatibility
__all__ = [
    # CrewAI types
    "Crew",
    "Process",
    "Task",
    # Main crew building function
    "build_intelligence_crew",
    # Task creation functions
    "create_acquisition_task",
    "create_transcription_task",
    "create_analysis_tasks",
    "create_knowledge_integration_task",
    "build_crew_with_tasks",
    # Agent management functions
    "populate_agent_tool_context",
    "get_or_create_agent",
    # Task callbacks
    "task_completion_callback",
]
