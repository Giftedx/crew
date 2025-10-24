"""
MCP Client for external AI API integration.

This module provides a client for integrating with external AI APIs
and analytical utilities through the Model Context Protocol (MCP).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

from ..step_result import StepResult
from ..tenancy.helpers import require_tenant


logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an MCP tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    provider: str
    endpoint: str
    api_key: str | None = None
    timeout: int = 30


@dataclass
class MCPResponse:
    """Represents a response from an MCP tool."""

    success: bool
    data: Any
    error: str | None = None
    latency_ms: float = 0.0
    cost_tokens: int | None = None


class MCPClient:
    """Client for MCP server integration."""

    def __init__(self, base_url: str = "https://api.mcp.io", api_key: str | None = None):
        """Initialize MCP client.

        Args:
            base_url: Base URL for MCP server
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: aiohttp.ClientSession | None = None
        self.tools: dict[str, MCPTool] = {}
        self.request_count = 0
        self.total_latency = 0.0

        logger.info("Initialized MCPClient with base URL: %s", base_url)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if self.session is None or self.session.closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    @require_tenant(strict_flag_enabled=False)
    async def register_tool(
        self,
        tool: MCPTool,
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Register an MCP tool.

        Args:
            tool: MCP tool definition
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult indicating success/failure
        """
        try:
            await self._ensure_session()

            # Register tool with MCP server
            registration_data = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "provider": tool.provider,
                "endpoint": tool.endpoint,
                "tenant": tenant,
                "workspace": workspace,
            }

            url = f"{self.base_url}/tools/register"
            if self.session is None:
                return StepResult.fail("MCP client session not initialized")
            async with self.session.post(url, json=registration_data) as response:
                if response.status == 200:
                    self.tools[tool.name] = tool
                    logger.info("Registered MCP tool: %s", tool.name)
                    return StepResult.ok(data={"tool_name": tool.name, "registered": True})
                else:
                    error_text = await response.text()
                    return StepResult.fail(f"Failed to register tool: {error_text}")

        except Exception as e:
            logger.error("Failed to register MCP tool %s: %s", tool.name, str(e))
            return StepResult.fail(f"Failed to register tool: {e!s}")

    @require_tenant(strict_flag_enabled=False)
    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Execute an MCP tool.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with tool execution result
        """
        try:
            if tool_name not in self.tools:
                return StepResult.fail(f"Tool not found: {tool_name}")

            await self._ensure_session()

            start_time = time.time()

            # Prepare execution request
            execution_data = {
                "tool_name": tool_name,
                "parameters": parameters,
                "tenant": tenant,
                "workspace": workspace,
            }

            # Execute tool
            url = f"{self.base_url}/tools/execute"
            if self.session is None:
                return StepResult.fail("MCP client session not initialized")
            async with self.session.post(url, json=execution_data) as response:
                execution_time = (time.time() - start_time) * 1000
                self.request_count += 1
                self.total_latency += execution_time

                if response.status == 200:
                    result_data = await response.json()
                    logger.debug(
                        "Executed MCP tool %s (latency: %.1fms)",
                        tool_name,
                        execution_time,
                    )

                    return StepResult.ok(
                        data={
                            "result": result_data,
                            "latency_ms": execution_time,
                            "tool_name": tool_name,
                        }
                    )
                else:
                    error_text = await response.text()
                    logger.warning(
                        "MCP tool execution failed: %s (status: %d)",
                        error_text,
                        response.status,
                    )
                    return StepResult.fail(f"Tool execution failed: {error_text}")

        except Exception as e:
            logger.error("Failed to execute MCP tool %s: %s", tool_name, str(e))
            return StepResult.fail(f"Tool execution failed: {e!s}")

    async def list_tools(self) -> StepResult:
        """List all registered MCP tools.

        Returns:
            StepResult with list of tools
        """
        try:
            tools_list = []
            for tool_name, tool in self.tools.items():
                tools_list.append(
                    {
                        "name": tool_name,
                        "description": tool.description,
                        "provider": tool.provider,
                        "endpoint": tool.endpoint,
                    }
                )

            return StepResult.ok(data={"tools": tools_list})

        except Exception as e:
            logger.error("Failed to list MCP tools: %s", str(e))
            return StepResult.fail(f"Failed to list tools: {e!s}")

    async def get_tool_schema(self, tool_name: str) -> StepResult:
        """Get schema for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            StepResult with tool schema
        """
        try:
            if tool_name not in self.tools:
                return StepResult.fail(f"Tool not found: {tool_name}")

            tool = self.tools[tool_name]
            schema = {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "provider": tool.provider,
            }

            return StepResult.ok(data=schema)

        except Exception as e:
            logger.error("Failed to get tool schema for %s: %s", tool_name, str(e))
            return StepResult.fail(f"Failed to get tool schema: {e!s}")

    async def health_check(self) -> StepResult:
        """Check MCP server health.

        Returns:
            StepResult with health status
        """
        try:
            await self._ensure_session()

            url = f"{self.base_url}/health"
            if self.session is None:
                return StepResult.fail("MCP client session not initialized")
            async with self.session.get(url) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return StepResult.ok(data=health_data)
                else:
                    return StepResult.fail(f"Health check failed: {response.status}")

        except Exception as e:
            logger.error("MCP health check failed: %s", str(e))
            return StepResult.fail(f"Health check failed: {e!s}")

    async def get_stats(self) -> StepResult:
        """Get MCP client statistics.

        Returns:
            StepResult with client statistics
        """
        try:
            avg_latency = self.total_latency / self.request_count if self.request_count > 0 else 0.0

            stats = {
                "total_requests": self.request_count,
                "average_latency_ms": avg_latency,
                "total_latency_ms": self.total_latency,
                "registered_tools": len(self.tools),
                "base_url": self.base_url,
            }

            return StepResult.ok(data=stats)

        except Exception as e:
            logger.error("Failed to get MCP stats: %s", str(e))
            return StepResult.fail(f"Failed to get stats: {e!s}")


def create_default_mcp_tools() -> list[MCPTool]:
    """Create default MCP tools for common AI operations.

    Returns:
        List of default MCP tools
    """
    return [
        MCPTool(
            name="web_search",
            description="Search the web for information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 10},
                },
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "snippet": {"type": "string"},
                            },
                        },
                    },
                },
            },
            provider="web_search",
            endpoint="https://api.search.io/search",
        ),
        MCPTool(
            name="image_analysis",
            description="Analyze images using computer vision",
            input_schema={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of image to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["objects", "faces", "text", "general"],
                        "default": "general",
                    },
                },
                "required": ["image_url"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "analysis": {"type": "object"},
                    "confidence": {"type": "number"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                },
            },
            provider="vision_ai",
            endpoint="https://api.vision.ai/analyze",
        ),
        MCPTool(
            name="data_analysis",
            description="Perform statistical analysis on data",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "array", "description": "Data to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["descriptive", "correlation", "regression", "clustering"],
                        "default": "descriptive",
                    },
                },
                "required": ["data"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "statistics": {"type": "object"},
                    "insights": {"type": "array", "items": {"type": "string"}},
                    "visualizations": {"type": "array", "items": {"type": "string"}},
                },
            },
            provider="analytics_ai",
            endpoint="https://api.analytics.ai/analyze",
        ),
        MCPTool(
            name="code_review",
            description="Review code for quality and security issues",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                    "language": {"type": "string", "description": "Programming language"},
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["security", "performance", "style"],
                    },
                },
                "required": ["code", "language"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "severity": {"type": "string"},
                                "message": {"type": "string"},
                                "line": {"type": "integer"},
                            },
                        },
                    },
                    "score": {"type": "number"},
                    "suggestions": {"type": "array", "items": {"type": "string"}},
                },
            },
            provider="code_ai",
            endpoint="https://api.code.ai/review",
        ),
    ]
