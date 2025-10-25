"""
MCP Tool Wrapper for CrewAI integration.

This module provides a wrapper that makes MCP tools available
as CrewAI tools for agent use.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from crewai import BaseTool

from ..services.mcp_client import MCPClient
from ..step_result import StepResult


logger = logging.getLogger(__name__)


class MCPToolInput(BaseModel):
    """Input schema for MCP tool wrapper."""

    tool_name: str = Field(description="Name of the MCP tool to execute")
    parameters: dict[str, Any] = Field(description="Parameters for the tool")
    tenant: str = Field(default="", description="Tenant identifier")
    workspace: str = Field(default="", description="Workspace identifier")


class MCPToolWrapper(BaseTool):
    """Wrapper for MCP tools to be used as CrewAI tools."""

    name: str = "mcp_tool_wrapper"
    description: str = "Execute MCP (Model Context Protocol) tools for enhanced AI capabilities"
    args_schema: type[BaseModel] = MCPToolInput

    def __init__(self, mcp_client: MCPClient | None = None, **kwargs):
        """Initialize MCP tool wrapper.

        Args:
            mcp_client: MCP client instance
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.mcp_client = mcp_client or MCPClient()
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure MCP client is initialized and tools are registered."""
        if not self._initialized:
            try:
                # Register default tools if not already registered
                from ..services.mcp_client import create_default_mcp_tools

                default_tools = create_default_mcp_tools()
                for tool in default_tools:
                    await self.mcp_client.register_tool(tool)

                self._initialized = True
                logger.info("MCP tool wrapper initialized with %d tools", len(default_tools))

            except Exception as e:
                logger.error("Failed to initialize MCP tool wrapper: %s", str(e))
                raise

    def _run(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Execute an MCP tool synchronously.

        Args:
            tool_name: Name of the MCP tool to execute
            parameters: Tool parameters
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with tool execution result
        """
        try:
            # Run async operation in sync context
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._async_run(tool_name, parameters, tenant, workspace),
                    )
                    return future.result()
            else:
                return asyncio.run(self._async_run(tool_name, parameters, tenant, workspace))

        except Exception as e:
            logger.error("Failed to execute MCP tool %s: %s", tool_name, str(e))
            return StepResult.fail(f"MCP tool execution failed: {e!s}")

    async def _async_run(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        tenant: str = "",
        workspace: str = "",
    ) -> StepResult:
        """Execute an MCP tool asynchronously.

        Args:
            tool_name: Name of the MCP tool to execute
            parameters: Tool parameters
            tenant: Tenant identifier
            workspace: Workspace identifier

        Returns:
            StepResult with tool execution result
        """
        try:
            await self._ensure_initialized()

            # Execute the MCP tool
            result = await self.mcp_client.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                tenant=tenant,
                workspace=workspace,
            )

            if result.success:
                logger.debug("Successfully executed MCP tool: %s", tool_name)
                return StepResult.ok(
                    data={
                        "tool_name": tool_name,
                        "result": result.data["result"],
                        "latency_ms": result.data.get("latency_ms", 0),
                    }
                )
            else:
                logger.warning("MCP tool execution failed: %s", result.error)
                return StepResult.fail(f"Tool execution failed: {result.error}")

        except Exception as e:
            logger.error("Failed to execute MCP tool %s: %s", tool_name, str(e))
            return StepResult.fail(f"MCP tool execution failed: {e!s}")


class WebSearchTool(BaseTool):
    """Web search tool using MCP."""

    name: str = "web_search"
    description: str = "Search the web for information using MCP web search tool"
    args_schema: type[BaseModel] | None = None

    def __init__(self, mcp_client: MCPClient | None = None, **kwargs):
        """Initialize web search tool.

        Args:
            mcp_client: MCP client instance
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.mcp_wrapper = MCPToolWrapper(mcp_client)

    def _run(self, query: str, max_results: int = 10, **kwargs) -> str:
        """Search the web for information.

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Search results as string
        """
        try:
            result = self.mcp_wrapper._run(
                tool_name="web_search",
                parameters={"query": query, "max_results": max_results},
                **kwargs,
            )

            if result.success:
                results = result.data["result"]["results"]
                formatted_results = []
                for item in results:
                    formatted_results.append(
                        f"Title: {item.get('title', 'N/A')}\n"
                        f"URL: {item.get('url', 'N/A')}\n"
                        f"Snippet: {item.get('snippet', 'N/A')}\n"
                    )
                return "\n".join(formatted_results)
            else:
                return f"Search failed: {result.error}"

        except Exception as e:
            logger.error("Web search failed: %s", str(e))
            return f"Search error: {e!s}"


class ImageAnalysisTool(BaseTool):
    """Image analysis tool using MCP."""

    name: str = "image_analysis"
    description: str = "Analyze images using computer vision via MCP"
    args_schema: type[BaseModel] | None = None

    def __init__(self, mcp_client: MCPClient | None = None, **kwargs):
        """Initialize image analysis tool.

        Args:
            mcp_client: MCP client instance
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.mcp_wrapper = MCPToolWrapper(mcp_client)

    def _run(
        self,
        image_url: str,
        analysis_type: str = "general",
        **kwargs,
    ) -> str:
        """Analyze an image.

        Args:
            image_url: URL of the image to analyze
            analysis_type: Type of analysis (objects, faces, text, general)
            **kwargs: Additional parameters

        Returns:
            Analysis results as string
        """
        try:
            result = self.mcp_wrapper._run(
                tool_name="image_analysis",
                parameters={"image_url": image_url, "analysis_type": analysis_type},
                **kwargs,
            )

            if result.success:
                analysis_data = result.data["result"]
                return (
                    f"Analysis Type: {analysis_type}\n"
                    f"Confidence: {analysis_data.get('confidence', 'N/A')}\n"
                    f"Labels: {', '.join(analysis_data.get('labels', []))}\n"
                    f"Details: {analysis_data.get('analysis', {})}"
                )
            else:
                return f"Image analysis failed: {result.error}"

        except Exception as e:
            logger.error("Image analysis failed: %s", str(e))
            return f"Analysis error: {e!s}"


class DataAnalysisTool(BaseTool):
    """Data analysis tool using MCP."""

    name: str = "data_analysis"
    description: str = "Perform statistical analysis on data using MCP"
    args_schema: type[BaseModel] | None = None

    def __init__(self, mcp_client: MCPClient | None = None, **kwargs):
        """Initialize data analysis tool.

        Args:
            mcp_client: MCP client instance
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.mcp_wrapper = MCPToolWrapper(mcp_client)

    def _run(
        self,
        data: list[Any],
        analysis_type: str = "descriptive",
        **kwargs,
    ) -> str:
        """Analyze data.

        Args:
            data: Data to analyze
            analysis_type: Type of analysis (descriptive, correlation, regression, clustering)
            **kwargs: Additional parameters

        Returns:
            Analysis results as string
        """
        try:
            result = self.mcp_wrapper._run(
                tool_name="data_analysis",
                parameters={"data": data, "analysis_type": analysis_type},
                **kwargs,
            )

            if result.success:
                analysis_data = result.data["result"]
                return (
                    f"Analysis Type: {analysis_type}\n"
                    f"Statistics: {analysis_data.get('statistics', {})}\n"
                    f"Insights: {', '.join(analysis_data.get('insights', []))}\n"
                    f"Visualizations: {', '.join(analysis_data.get('visualizations', []))}"
                )
            else:
                return f"Data analysis failed: {result.error}"

        except Exception as e:
            logger.error("Data analysis failed: %s", str(e))
            return f"Analysis error: {e!s}"


class CodeReviewTool(BaseTool):
    """Code review tool using MCP."""

    name: str = "code_review"
    description: str = "Review code for quality and security issues using MCP"
    args_schema: type[BaseModel] | None = None

    def __init__(self, mcp_client: MCPClient | None = None, **kwargs):
        """Initialize code review tool.

        Args:
            mcp_client: MCP client instance
            **kwargs: Additional arguments for BaseTool
        """
        super().__init__(**kwargs)
        self.mcp_wrapper = MCPToolWrapper(mcp_client)

    def _run(
        self,
        code: str,
        language: str,
        focus_areas: list[str] | None = None,
        **kwargs,
    ) -> str:
        """Review code.

        Args:
            code: Code to review
            language: Programming language
            focus_areas: Areas to focus on (security, performance, style)
            **kwargs: Additional parameters

        Returns:
            Review results as string
        """
        try:
            if focus_areas is None:
                focus_areas = ["security", "performance", "style"]

            result = self.mcp_wrapper._run(
                tool_name="code_review",
                parameters={
                    "code": code,
                    "language": language,
                    "focus_areas": focus_areas,
                },
                **kwargs,
            )

            if result.success:
                review_data = result.data["result"]
                issues = review_data.get("issues", [])
                score = review_data.get("score", 0)
                suggestions = review_data.get("suggestions", [])

                result_text = f"Code Review Score: {score}/10\n\n"
                result_text += f"Issues Found: {len(issues)}\n"
                for issue in issues:
                    result_text += f"- {issue.get('type', 'Unknown')}: {issue.get('message', 'N/A')} (Line {issue.get('line', 'N/A')})\n"

                if suggestions:
                    result_text += "\nSuggestions:\n"
                    for suggestion in suggestions:
                        result_text += f"- {suggestion}\n"

                return result_text
            else:
                return f"Code review failed: {result.error}"

        except Exception as e:
            logger.error("Code review failed: %s", str(e))
            return f"Review error: {e!s}"
