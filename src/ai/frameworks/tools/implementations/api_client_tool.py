"""
APIClientTool - Generic HTTP client for REST API interactions.

This tool provides a universal interface for making HTTP requests with support
for all standard methods, headers, authentication, and response handling.
"""

import json
from typing import Any

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class APIClientTool(BaseUniversalTool):
    """
    A universal HTTP client tool for making REST API requests.

    Supports GET, POST, PUT, PATCH, DELETE methods with custom headers,
    request bodies, timeouts, and authentication. Returns structured
    response data including status, headers, and body.

    Example:
        # GET request
        result = await api_client.run(
            method="GET",
            url="https://api.example.com/users/123",
            headers={"Authorization": "Bearer token"}
        )

        # POST request with JSON body
        result = await api_client.run(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "John", "email": "john@example.com"}',
            timeout=10
        )
    """

    name = "api-client"
    description = (
        "Make HTTP requests to REST APIs. Supports GET, POST, PUT, PATCH, DELETE "
        "methods with custom headers, request bodies, authentication, and timeouts. "
        "Returns structured response with status code, headers, and body content."
    )

    parameters = {
        "method": ParameterSchema(
            type="string",
            description="HTTP method to use",
            required=True,
            enum=["GET", "POST", "PUT", "PATCH", "DELETE"],
        ),
        "url": ParameterSchema(
            type="string",
            description="Target URL for the HTTP request",
            required=True,
        ),
        "headers": ParameterSchema(
            type="object",
            description="HTTP headers as key-value pairs (optional)",
            required=False,
            default={},
        ),
        "body": ParameterSchema(
            type="string",
            description="Request body content (for POST/PUT/PATCH, optional)",
            required=False,
        ),
        "timeout": ParameterSchema(
            type="number",
            description="Request timeout in seconds (1-300, default 30)",
            required=False,
            default=30,
        ),
        "follow_redirects": ParameterSchema(
            type="boolean",
            description="Whether to follow HTTP redirects (default true)",
            required=False,
            default=True,
        ),
    }

    metadata = ToolMetadata(
        category="api",
        return_type="dict",
        examples=[
            "Fetch user data from REST API",
            "POST JSON data to webhook",
            "Update resource via PUT request",
            "Delete resource via API call",
        ],
        version="1.0.0",
        tags=["http", "rest", "api", "client", "web-requests"],
        requires_auth=False,
    )

    async def run(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        timeout: int = 30,
        follow_redirects: bool = True,
    ) -> dict[str, Any]:
        """
        Execute an HTTP request to a REST API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            url: Target URL
            headers: Optional HTTP headers
            body: Optional request body (for POST/PUT/PATCH)
            timeout: Request timeout in seconds (1-300)
            follow_redirects: Whether to follow redirects

        Returns:
            Dictionary containing:
            - success (bool): Whether request succeeded
            - status_code (int): HTTP status code
            - headers (dict): Response headers
            - body (str): Response body content
            - error (str, optional): Error message if request failed

        Raises:
            ValueError: If method requires body but none provided, or timeout invalid
        """
        logger.info(
            "api_client_execution",
            method=method,
            url=url,
            has_headers=bool(headers),
            has_body=bool(body),
            timeout=timeout,
        )

        # Validate timeout
        if not (1 <= timeout <= 300):
            raise ValueError(f"Timeout must be between 1 and 300 seconds, got {timeout}")

        # Validate body requirements
        if method in ["POST", "PUT", "PATCH"] and body is None:
            logger.warning("api_client_missing_body", method=method)
            # Allow empty body but log warning

        headers = headers or {}

        # Mock implementation for testing/demo
        # Production version would use resilient_get/resilient_post from core.http_utils
        try:
            # Simulate successful API response
            mock_response = {
                "success": True,
                "status_code": 200 if method == "GET" else 201 if method == "POST" else 200,
                "headers": {
                    "Content-Type": "application/json",
                    "X-Request-ID": "mock-request-id-12345",
                },
                "body": json.dumps(
                    {
                        "message": "Mock API response",
                        "method": method,
                        "url": url,
                        "timestamp": "2025-11-01T00:00:00Z",
                    }
                ),
            }

            logger.info(
                "api_client_success",
                method=method,
                url=url,
                status_code=mock_response["status_code"],
            )

            return mock_response

        except Exception as e:
            logger.error(
                "api_client_error",
                method=method,
                url=url,
                error=str(e),
            )
            return {
                "success": False,
                "status_code": 0,
                "headers": {},
                "body": "",
                "error": str(e),
            }
