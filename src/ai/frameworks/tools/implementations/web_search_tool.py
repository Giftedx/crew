"""Universal web search tool compatible with all frameworks."""

from __future__ import annotations

from typing import Any

import structlog

from ai.frameworks.tools import BaseUniversalTool, ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class WebSearchTool(BaseUniversalTool):
    """Universal web search tool using DuckDuckGo.

    This tool performs web searches and returns structured results that work
    across CrewAI, LangGraph, AutoGen, and LlamaIndex frameworks.

    Example:
        ```python
        tool = WebSearchTool()
        result = await tool.run(query="Python programming", max_results=5)
        ```
    """

    name = "web-search"
    description = "Search the web for information using DuckDuckGo. Returns relevant search results with titles, URLs, and snippets."

    parameters = {
        "query": ParameterSchema(
            type="string",
            description="The search query to execute",
            required=True,
        ),
        "max_results": ParameterSchema(
            type="number",
            description="Maximum number of results to return (1-20)",
            required=False,
            default=10,
        ),
        "region": ParameterSchema(
            type="string",
            description="Region code for localized results (e.g., 'us-en', 'uk-en')",
            required=False,
            default="wt-wt",  # worldwide
            enum=["wt-wt", "us-en", "uk-en", "ca-en", "au-en"],
        ),
    }

    metadata = ToolMetadata(
        category="web",
        return_type="list[dict]",
        examples=[
            {
                "query": "artificial intelligence news",
                "max_results": 5,
                "result": "List of 5 search results with titles, URLs, and snippets",
            },
        ],
        requires_auth=False,
        version="1.0.0",
        tags=["search", "web", "duckduckgo", "information-retrieval"],
    )

    async def run(
        self,
        query: str,
        max_results: int = 10,
        region: str = "wt-wt",
    ) -> list[dict[str, Any]]:
        """Execute web search.

        Args:
            query: Search query string
            max_results: Maximum results to return (1-20)
            region: Region code for localization

        Returns:
            List of search results, each containing:
            - title: Result title
            - url: Result URL
            - snippet: Text snippet/description

        Raises:
            ValueError: If max_results is out of range
            RuntimeError: If search request fails
        """
        # Validate max_results
        if not 1 <= max_results <= 20:
            raise ValueError(f"max_results must be between 1 and 20, got {max_results}")

        logger.info(
            "web_search_executing",
            query=query,
            max_results=max_results,
            region=region,
        )

        try:
            # For demo purposes, return mock data
            # In production, this would make actual HTTP requests
            logger.info(
                "web_search_mock_execution",
                query=query,
                max_results=max_results,
                region=region,
            )

            # Return mock results demonstrating the structure
            results = self._parse_duckduckgo_html("", max_results)

            logger.info(
                "web_search_completed",
                query=query,
                results_count=len(results),
            )

            return results

        except Exception as e:
            logger.error(
                "web_search_failed",
                query=query,
                error=str(e),
                exc_info=True,
            )
            raise RuntimeError(f"Web search failed: {e}") from e

    def _parse_duckduckgo_html(self, html: str, max_results: int) -> list[dict[str, Any]]:
        """Parse DuckDuckGo HTML results.

        Note: This is a simplified parser. Production code should use BeautifulSoup.
        """
        # For now, return mock data to demonstrate the tool structure
        # In production, this would parse the actual HTML
        results = []

        for i in range(min(max_results, 5)):
            results.append(
                {
                    "title": f"Search Result {i + 1}",
                    "url": f"https://example.com/result{i + 1}",
                    "snippet": f"This is a snippet for search result {i + 1}. It contains relevant information about the query.",
                }
            )

        return results
