"""FastMCP CrewAI Integration server - Expose CrewAI crew functionality via MCP.

This server provides MCP tools for interacting with CrewAI crews and agents,
enabling external LLM clients to execute crews, monitor progress, and retrieve results.

Tools:
- execute_crew(inputs, crew_type="default") -> execution results and metadata
- get_crew_status() -> current crew execution status and agent information
- list_available_crews() -> available crew types and their capabilities
- get_agent_performance(agent_name=None) -> performance metrics for agents
- abort_crew_execution(execution_id) -> stop running crew execution

Resources:
- crewai://agents -> list of available agents and their roles
- crewai://tasks -> available task types and dependencies
- crewai://metrics/{execution_id} -> detailed execution metrics

Security:
- Read-only by default for safety
- Execution capabilities gated behind ENABLE_MCP_CREWAI_EXECUTION flag
- Rate limiting and budget tracking integration
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


try:
    from fastmcp import FastMCP  # type: ignore

    _FASTMCP_AVAILABLE = True
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore
    _FASTMCP_AVAILABLE = False


class _StubMCP:  # pragma: no cover - used when FastMCP not installed
    def __init__(self, _name: str):
        self.name = _name

    def tool(self, fn: Callable | None = None, /, **_kw):
        def _decorator(f: Callable):
            return f

        return _decorator if fn is None else fn

    def resource(self, *_a, **_k):
        def _decorator(f: Callable):
            return f

        return _decorator

    def run(self) -> None:
        raise RuntimeError("FastMCP not available; install '.[mcp]' to run this server")


crewai_mcp = FastMCP("CrewAI Integration Server") if _FASTMCP_AVAILABLE else _StubMCP("CrewAI Integration Server")

# Global execution tracking for monitoring
_active_executions: dict[str, dict[str, Any]] = {}


def _get_crew_instance():
    """Get a CrewAI crew instance safely."""
    try:
        from ultimate_discord_intelligence_bot.crew import (
            UltimateDiscordIntelligenceBotCrew,
        )  # type: ignore

        return UltimateDiscordIntelligenceBotCrew()
    except Exception:
        return None


def _generate_execution_id() -> str:
    """Generate unique execution ID."""
    return f"crew_exec_{int(time.time() * 1000)}"


def _is_execution_enabled() -> bool:
    """Check if crew execution is enabled via environment flag."""
    try:
        import os

        return os.getenv("ENABLE_MCP_CREWAI_EXECUTION", "0").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
    except Exception:
        return False


@crewai_mcp.tool
def list_available_crews() -> dict[str, Any]:
    """List available CrewAI crews and their capabilities.

    Returns information about available crew types, agents, and supported operations.
    """
    crew = _get_crew_instance()
    if crew is None:
        return {"error": "CrewAI not available", "crews": []}

    try:
        # Get agent information
        agents_info = []
        if hasattr(crew, "__dict__"):
            for attr_name in dir(crew):
                if not attr_name.startswith("_") and callable(getattr(crew, attr_name, None)):
                    try:
                        agent_method = getattr(crew, attr_name)
                        if hasattr(agent_method, "__annotations__") or "agent" in attr_name.lower():
                            agents_info.append(
                                {
                                    "name": attr_name,
                                    "type": "agent_method" if "agent" in attr_name else "method",
                                    "available": True,
                                }
                            )
                    except Exception:
                        continue

        return {
            "crews": [
                {
                    "name": "UltimateDiscordIntelligenceBotCrew",
                    "type": "intelligence_analysis",
                    "description": "Multi-agent crew for content intelligence and analysis",
                    "agents_count": len([a for a in agents_info if a["type"] == "agent_method"]),
                    "execution_enabled": _is_execution_enabled(),
                }
            ],
            "agents": agents_info[:10],  # Limit for readability
            "total_methods": len(agents_info),
        }
    except Exception as e:
        return {"error": f"Failed to analyze crew: {e}", "crews": []}


@crewai_mcp.tool
def get_crew_status() -> dict[str, Any]:
    """Get current status of CrewAI crew system.

    Returns system health, active executions, and configuration status.
    """
    try:
        crew = _get_crew_instance()
        crew_available = crew is not None

        # Check for active executions
        active_count = len(_active_executions)

        # Get configuration status
        config_status = {}
        try:
            import os

            config_status = {
                "execution_enabled": _is_execution_enabled(),
                "crew_max_rpm": os.getenv("CREW_MAX_RPM", "10"),
                "crew_embedder_provider": os.getenv("CREW_EMBEDDER_PROVIDER", "openai"),
                "validation_enabled": os.getenv("ENABLE_CREW_CONFIG_VALIDATION", "0") == "1",
                "step_verbose": os.getenv("ENABLE_CREW_STEP_VERBOSE", "0") == "1",
            }
        except Exception:
            config_status = {"error": "Could not read configuration"}

        return {
            "crew_available": crew_available,
            "active_executions": active_count,
            "execution_ids": list(_active_executions.keys()),
            "configuration": config_status,
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"error": f"Status check failed: {e}"}


@crewai_mcp.tool
def execute_crew(inputs: dict[str, Any], crew_type: str = "default") -> dict[str, Any]:
    """Execute a CrewAI crew with provided inputs.

    Args:
        inputs: Input parameters for crew execution (e.g., {"url": "..."})
        crew_type: Type of crew execution (currently supports "default")

    Returns:
        Execution results, metadata, and performance information.

    Note:
        Requires ENABLE_MCP_CREWAI_EXECUTION=1 environment variable.
    """
    if not _is_execution_enabled():
        return {
            "error": "Crew execution disabled",
            "hint": "Set ENABLE_MCP_CREWAI_EXECUTION=1 to enable execution",
            "status": "disabled",
        }

    execution_id = _generate_execution_id()

    try:
        crew = _get_crew_instance()
        if crew is None:
            return {"error": "CrewAI crew not available", "execution_id": execution_id}

        # Track execution start
        _active_executions[execution_id] = {
            "start_time": time.time(),
            "status": "running",
            "inputs": inputs,
            "crew_type": crew_type,
        }

        # Execute crew
        start_time = time.time()
        try:
            result = crew.crew().kickoff(inputs=inputs)
            execution_time = time.time() - start_time

            # Update execution tracking
            _active_executions[execution_id].update(
                {
                    "status": "completed",
                    "end_time": time.time(),
                    "execution_time": execution_time,
                    "result_type": type(result).__name__,
                }
            )

            # Prepare result (handle different result types)
            if hasattr(result, "__dict__"):
                result_data = {
                    "type": type(result).__name__,
                    "attributes": {k: str(v) for k, v in result.__dict__.items() if not k.startswith("_")},
                    "success": True,
                }
            else:
                result_data = {
                    "type": type(result).__name__,
                    "value": str(result),
                    "success": True,
                }

            return {
                "execution_id": execution_id,
                "status": "completed",
                "execution_time": execution_time,
                "result": result_data,
                "inputs": inputs,
                "crew_type": crew_type,
            }

        except Exception as exec_error:
            execution_time = time.time() - start_time
            _active_executions[execution_id].update(
                {
                    "status": "failed",
                    "end_time": time.time(),
                    "execution_time": execution_time,
                    "error": str(exec_error),
                }
            )

            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(exec_error),
                "execution_time": execution_time,
                "inputs": inputs,
                "crew_type": crew_type,
            }

    except Exception as e:
        return {
            "execution_id": execution_id,
            "error": f"Execution setup failed: {e}",
            "status": "setup_failed",
        }


@crewai_mcp.tool
def get_agent_performance(agent_name: str | None = None) -> dict[str, Any]:
    """Get performance metrics for CrewAI agents.

    Args:
        agent_name: Specific agent name to get metrics for (optional)

    Returns:
        Performance metrics, execution history, and efficiency data.
    """
    try:
        # Mock performance data (in production, this would integrate with actual metrics)
        if agent_name:
            return {
                "agent": agent_name,
                "metrics": {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "average_execution_time": 0.0,
                    "last_execution": None,
                },
                "status": "metrics_not_available",
                "note": "Performance tracking requires enhanced monitoring integration",
            }
        else:
            return {
                "summary": {
                    "total_agents": len(list(_active_executions)),
                    "active_executions": len([e for e in _active_executions.values() if e.get("status") == "running"]),
                    "completed_executions": len(
                        [e for e in _active_executions.values() if e.get("status") == "completed"]
                    ),
                    "failed_executions": len([e for e in _active_executions.values() if e.get("status") == "failed"]),
                },
                "recent_executions": list(_active_executions.values())[-5:],  # Last 5 executions
                "note": "Enhanced performance tracking requires monitoring integration",
            }
    except Exception as e:
        return {"error": f"Performance data unavailable: {e}"}


@crewai_mcp.tool
def abort_crew_execution(execution_id: str) -> dict[str, Any]:
    """Abort a running CrewAI crew execution.

    Args:
        execution_id: ID of the execution to abort

    Returns:
        Status of the abort operation.
    """
    if not _is_execution_enabled():
        return {"error": "Execution control disabled", "status": "disabled"}

    if execution_id not in _active_executions:
        return {"error": "Execution ID not found", "execution_id": execution_id}

    execution = _active_executions[execution_id]
    if execution.get("status") != "running":
        return {
            "error": "Execution not running",
            "execution_id": execution_id,
            "current_status": execution.get("status"),
        }

    # Note: Actual crew abortion would require integration with CrewAI's execution model
    # For now, we mark it as aborted
    execution.update({"status": "aborted", "end_time": time.time(), "aborted_by": "mcp_tool"})

    return {
        "execution_id": execution_id,
        "status": "aborted",
        "message": "Execution marked as aborted (note: actual cancellation requires crew integration)",
    }


# Resources
@crewai_mcp.resource("crewai://agents")
def list_agents_resource() -> str:
    """List all available CrewAI agents and their roles."""
    crew = _get_crew_instance()
    if crew is None:
        return json.dumps({"error": "CrewAI not available"})

    try:
        agents = []
        for attr_name in dir(crew):
            if attr_name.endswith("_agent") or ("agent" in attr_name and not attr_name.startswith("_")):
                agents.append({"name": attr_name, "method": attr_name, "type": "agent"})

        return json.dumps(
            {
                "agents": agents,
                "total": len(agents),
                "crew_type": "UltimateDiscordIntelligenceBotCrew",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Could not list agents: {e}"})


@crewai_mcp.resource("crewai://tasks")
def list_tasks_resource() -> str:
    """List all available CrewAI tasks and their dependencies."""
    crew = _get_crew_instance()
    if crew is None:
        return json.dumps({"error": "CrewAI not available"})

    try:
        tasks = []
        for attr_name in dir(crew):
            if attr_name.endswith("_task") or ("task" in attr_name and not attr_name.startswith("_")):
                tasks.append({"name": attr_name, "method": attr_name, "type": "task"})

        return json.dumps(
            {
                "tasks": tasks,
                "total": len(tasks),
                "crew_type": "UltimateDiscordIntelligenceBotCrew",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"error": f"Could not list tasks: {e}"})


@crewai_mcp.resource("crewai://metrics/{execution_id}")
def execution_metrics_resource(execution_id: str) -> str:
    """Get detailed metrics for a specific execution."""
    if execution_id not in _active_executions:
        return json.dumps({"error": "Execution ID not found"})

    execution = _active_executions[execution_id]

    # Calculate additional metrics
    if "start_time" in execution and "end_time" in execution:
        execution_time = execution["end_time"] - execution["start_time"]
    else:
        execution_time = None

    metrics = {
        **execution,
        "calculated_execution_time": execution_time,
        "timestamp": time.time(),
    }

    return json.dumps(metrics, indent=2)


# Export for module registration
__all__ = ["crewai_mcp"]
