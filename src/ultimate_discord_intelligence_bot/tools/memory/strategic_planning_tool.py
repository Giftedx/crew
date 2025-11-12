"""Compatibility shim for ultimate_discord_intelligence_bot.tools.memory.strategic_planning_tool

Re-exports StrategicPlanningTool from its new location in domains.memory.vector.
"""

from domains.memory.vector.strategic_planning_tool import StrategicPlanningTool


__all__ = ["StrategicPlanningTool"]
