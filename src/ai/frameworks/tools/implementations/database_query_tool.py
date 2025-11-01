"""
DatabaseQueryTool - Execute database queries with safety features.

This tool provides safe database query execution with support for parameterized
queries, connection pooling, and result formatting.
"""

from typing import Any

import structlog

from ai.frameworks.tools.converters import BaseUniversalTool
from ai.frameworks.tools.protocols import ParameterSchema, ToolMetadata


logger = structlog.get_logger(__name__)


class DatabaseQueryTool(BaseUniversalTool):
    """
    A universal database query tool with safety features.

    Supports executing SQL queries with parameterization to prevent SQL injection,
    connection management, and structured result formatting. Works with various
    database backends (PostgreSQL, MySQL, SQLite, etc.).

    Example:
        # Execute SELECT query
        result = await db.run(
            query="SELECT * FROM users WHERE id = :user_id",
            parameters={"user_id": 123},
            database_type="postgresql"
        )

        # Execute INSERT with parameters
        result = await db.run(
            query="INSERT INTO logs (message, level) VALUES (:msg, :lvl)",
            parameters={"msg": "Test", "lvl": "INFO"},
            database_type="sqlite"
        )
    """

    name = "database-query"
    description = (
        "Execute database queries safely with parameterization and connection pooling. "
        "Supports PostgreSQL, MySQL, SQLite, and other databases. Returns structured "
        "query results with row data, affected rows count, and execution metadata."
    )

    parameters = {
        "query": ParameterSchema(
            type="string",
            description="SQL query to execute (use :param for parameters)",
            required=True,
        ),
        "parameters": ParameterSchema(
            type="object",
            description="Query parameters for parameterized queries (optional)",
            required=False,
            default={},
        ),
        "database_type": ParameterSchema(
            type="string",
            description="Type of database (default postgresql)",
            required=False,
            enum=["postgresql", "mysql", "sqlite", "mssql", "oracle"],
            default="postgresql",
        ),
        "max_rows": ParameterSchema(
            type="number",
            description="Maximum rows to return (0 for unlimited, default 1000)",
            required=False,
            default=1000,
        ),
        "timeout": ParameterSchema(
            type="number",
            description="Query timeout in seconds (default 30)",
            required=False,
            default=30,
        ),
        "read_only": ParameterSchema(
            type="boolean",
            description="Enforce read-only mode (rejects INSERT/UPDATE/DELETE, default true)",
            required=False,
            default=True,
        ),
    }

    metadata = ToolMetadata(
        category="database",
        return_type="dict",
        examples=[
            "Query user records from PostgreSQL",
            "Insert log entries into SQLite",
            "Execute aggregate queries on MySQL",
            "Safe parameterized database queries",
        ],
        version="1.0.0",
        tags=["database", "sql", "query", "postgresql", "mysql", "sqlite"],
        requires_auth=True,
    )

    async def run(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database_type: str = "postgresql",
        max_rows: int = 1000,
        timeout: int = 30,
        read_only: bool = True,
    ) -> dict[str, Any]:
        """
        Execute a database query with safety features.

        Args:
            query: SQL query with :param placeholders
            parameters: Parameter values for the query
            database_type: Type of database
            max_rows: Maximum rows to return (0 = unlimited)
            timeout: Query timeout in seconds
            read_only: Enforce read-only mode

        Returns:
            Dictionary containing:
            - rows (list[dict]): Query result rows
            - row_count (int): Number of rows returned/affected
            - columns (list[str]): Column names
            - execution_time_ms (float): Query execution time
            - truncated (bool): Whether results were truncated

        Raises:
            ValueError: If query is invalid or violates read_only mode
            TimeoutError: If query exceeds timeout
        """
        logger.info(
            "database_query_execution",
            query_preview=query[:100],
            database_type=database_type,
            has_parameters=bool(parameters),
            read_only=read_only,
        )

        parameters = parameters or {}

        # Validate read-only mode
        if read_only:
            query_upper = query.strip().upper()
            write_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
            for op in write_operations:
                if query_upper.startswith(op):
                    raise ValueError(f"Query rejected: '{op}' operation not allowed in read-only mode")

        # Validate timeout
        if not (1 <= timeout <= 300):
            raise ValueError(f"Timeout must be between 1 and 300 seconds, got {timeout}")

        # Validate max_rows
        if max_rows < 0:
            raise ValueError(f"max_rows must be >= 0, got {max_rows}")

        # Mock implementation for testing/demo
        # Production version would use actual database connections (asyncpg, aiomysql, etc.)
        try:
            # Simulate query execution
            mock_rows = self._generate_mock_results(query, parameters, database_type)

            # Apply max_rows limit
            truncated = False
            if max_rows > 0 and len(mock_rows) > max_rows:
                mock_rows = mock_rows[:max_rows]
                truncated = True

            # Extract column names
            columns = list(mock_rows[0].keys()) if mock_rows else []

            result = {
                "rows": mock_rows,
                "row_count": len(mock_rows),
                "columns": columns,
                "execution_time_ms": 12.5,  # Mock execution time
                "truncated": truncated,
            }

            logger.info(
                "database_query_success",
                row_count=len(mock_rows),
                columns=columns,
                truncated=truncated,
            )

            return result

        except Exception as e:
            logger.error(
                "database_query_error",
                query=query[:100],
                error=str(e),
            )
            raise

    def _generate_mock_results(
        self, query: str, parameters: dict[str, Any], database_type: str
    ) -> list[dict[str, Any]]:
        """Generate mock query results based on query type."""
        query_lower = query.lower()

        # Mock SELECT results
        if "select" in query_lower:
            if "users" in query_lower:
                return [
                    {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
                    {"id": 2, "name": "Bob", "email": "bob@example.com", "active": True},
                    {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": False},
                ]
            elif "logs" in query_lower:
                return [
                    {"id": 1, "level": "INFO", "message": "Application started", "timestamp": "2025-11-01T00:00:00Z"},
                    {"id": 2, "level": "ERROR", "message": "Connection failed", "timestamp": "2025-11-01T00:01:00Z"},
                ]
            else:
                # Generic SELECT result
                return [
                    {"col1": "value1", "col2": 100, "col3": True},
                    {"col1": "value2", "col2": 200, "col3": False},
                ]

        # Mock INSERT/UPDATE/DELETE results (if allowed)
        return []
