"""FastMCP Client Integration for CrewAI Agents.

This tool enables CrewAI agents to interact with external MCP servers using FastMCP 2.0
client libraries, providing seamless integration between CrewAI workflows and MCP ecosystems.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from ultimate_discord_intelligence_bot.obs.metrics import get_metrics
from ultimate_discord_intelligence_bot.step_result import StepResult

from ._base import BaseTool


try:
    from fastmcp import Client

    _CLIENT_AVAILABLE = True
except ImportError:
    _CLIENT_AVAILABLE = False
    Client = None


class FastMCPClientTool(BaseTool[StepResult]):
    """Tool for calling external MCP servers from CrewAI agents using FastMCP 2.0."""

    name: str = "FastMCP Client Tool"
    description: str = "Call tools on external MCP servers using FastMCP 2.0 client library."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    def _validate_server_url(self, server_url: str) -> bool:
        """Validate that the server URL is allowed."""
        allowed_patterns = ["stdio://", "http://localhost:", "https://", "mcp://"]
        return any(server_url.startswith(pattern) for pattern in allowed_patterns)

    async def _call_mcp_tool_async(self, server_url: str, tool_name: str, arguments: dict[str, Any]) -> StepResult:
        """Asynchronously call an MCP tool on an external server."""
        if not _CLIENT_AVAILABLE:
            return StepResult.fail(
                "FastMCP client not available. Install with: pip install fastmcp", step="client_check"
            )
        if not self._validate_server_url(server_url):
            return StepResult.fail(f"Server URL not allowed: {server_url}", step="validation")
        try:
            async with Client(server_url) as client:
                available_tools: list[str] | None = None
                with contextlib.suppress(Exception):
                    tools = await client.list_tools()
                    available_tools = [tool.name for tool in tools]
                if available_tools is not None and tool_name not in available_tools:
                    return StepResult.fail(
                        f"Tool '{tool_name}' not available on server",
                        step="tool_validation",
                        metadata={"available_tools": available_tools},
                    )
                result = await client.call_tool(tool_name, arguments=arguments)
                return StepResult.ok(data={"result": result, "server_url": server_url, "tool_name": tool_name})
        except Exception as e:
            return StepResult.fail(
                f"MCP tool call failed: {e}",
                step="mcp_call",
                metadata={"server_url": server_url, "tool_name": tool_name, "arguments": arguments},
            )

    def run(self, server_url: str, tool_name: str, arguments: dict[str, Any] | None = None) -> StepResult:
        """Call a tool on an external MCP server.

        Args:
            server_url: URL of the MCP server (stdio://, http://, https://)
            tool_name: Name of the tool to call on the server
            arguments: Arguments to pass to the tool

        Returns:
            StepResult with the tool result or error information
        """
        if not _CLIENT_AVAILABLE:
            return StepResult.fail(
                "FastMCP client not available. Install with: pip install fastmcp", step="client_check"
            )
        if not server_url or not tool_name:
            return StepResult.fail("server_url and tool_name are required", step="validation")
        arguments = arguments or {}
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self._call_mcp_tool_async(server_url, tool_name, arguments))
                    )
                    result = future.result(timeout=30)
            else:
                result = loop.run_until_complete(self._call_mcp_tool_async(server_url, tool_name, arguments))
                with contextlib.suppress(Exception):
                    outcome = "success" if result.success else "error"
                    self._metrics.counter(
                        "tool_runs_total",
                        labels={
                            "tool": "fastmcp_client",
                            "server": server_url.split("://")[0] if "://" in server_url else "unknown",
                            "outcome": outcome,
                        },
                    ).inc()
            return result
        except Exception as e:
            return StepResult.fail(f"MCP client call failed: {e}", step="execution")


class MCPResourceTool(BaseTool[StepResult]):
    """Tool for reading resources from external MCP servers."""

    name: str = "MCP Resource Tool"
    description: str = "Read resources from external MCP servers using FastMCP 2.0 client."

    def __init__(self) -> None:
        super().__init__()
        self._metrics = get_metrics()

    async def _read_mcp_resource_async(self, server_url: str, resource_uri: str) -> StepResult:
        """Asynchronously read a resource from an MCP server."""
        if not _CLIENT_AVAILABLE:
            return StepResult.fail("FastMCP client not available", step="client_check")
        try:
            async with Client(server_url) as client:
                try:
                    resources = await client.list_resources()
                    available_uris = [res.uri for res in resources]
                    if resource_uri not in available_uris:
                        return StepResult.fail(
                            f"Resource '{resource_uri}' not available",
                            step="resource_validation",
                            metadata={"available_resources": available_uris},
                        )
                except Exception:
                    pass
                resource = await client.read_resource(resource_uri)
                return StepResult.ok(data={"resource": resource, "uri": resource_uri, "server_url": server_url})
        except Exception as e:
            return StepResult.fail(
                f"MCP resource read failed: {e}",
                step="resource_read",
                metadata={"uri": resource_uri, "server_url": server_url},
            )

    def run(self, server_url: str, resource_uri: str) -> StepResult:
        """Read a resource from an external MCP server.

        Args:
            server_url: URL of the MCP server
            resource_uri: URI of the resource to read

        Returns:
            StepResult with the resource content or error information
        """
        if not _CLIENT_AVAILABLE:
            return StepResult.fail(
                "FastMCP client not available. Install with: pip install fastmcp", step="client_check"
            )
        if not server_url or not resource_uri:
            return StepResult.fail("server_url and resource_uri are required", step="validation")
        try:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self._read_mcp_resource_async(server_url, resource_uri))
                    )
                    result = future.result(timeout=30)
            else:
                result = loop.run_until_complete(self._read_mcp_resource_async(server_url, resource_uri))
            with contextlib.suppress(Exception):
                outcome = "success" if result.success else "error"
                self._metrics.counter(
                    "tool_runs_total",
                    labels={
                        "tool": "mcp_resource",
                        "server": server_url.split("://")[0] if "://" in server_url else "unknown",
                        "outcome": outcome,
                    },
                ).inc()
            return result
        except Exception as e:
            return StepResult.fail(f"MCP resource read failed: {e}", step="execution")


__all__ = ["FastMCPClientTool", "MCPResourceTool"]
