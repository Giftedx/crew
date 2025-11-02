"""PostgreSQL state persistence backend for production database storage."""

import json
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


class PostgreSQLBackend:
    """PostgreSQL storage backend for workflow state.

    This backend stores state in a PostgreSQL database, providing
    robust, ACID-compliant storage suitable for production deployments
    with high concurrency and reliability requirements.

    Note: Requires asyncpg package. Install with: pip install asyncpg

    Attributes:
        connection_string: PostgreSQL connection string
        table_name: Name of the state table
        pool: Connection pool (created lazily)
    """

    def __init__(
        self,
        connection_string: str,
        table_name: str = "workflow_states",
    ) -> None:
        """Initialize the PostgreSQL backend.

        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://user:password@host:port/database
            table_name: Name of the state table
        """
        try:
            import asyncpg
        except ImportError as e:
            raise ImportError(
                "PostgreSQL support requires the 'asyncpg' package. Install it with: pip install asyncpg"
            ) from e

        self.connection_string = connection_string
        self.table_name = table_name
        self.pool = None

        logger.info("postgresql_backend_initialized", table_name=table_name)

    async def _get_pool(self):
        """Get or create connection pool.

        Returns:
            Connection pool
        """
        if self.pool is None:
            import asyncpg

            self.pool = await asyncpg.create_pool(self.connection_string)
            await self._create_table()
            logger.info("connection_pool_created", backend="postgresql")

        return self.pool

    async def _create_table(self) -> None:
        """Create the workflow_states table if it doesn't exist."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    workflow_id TEXT PRIMARY KEY,
                    state_jsonb JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Create index on updated_at for efficient listing
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_updated_at
                ON {self.table_name} (updated_at DESC)
            """)

        logger.debug("table_created_or_verified", backend="postgresql")

    async def save(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Save state to PostgreSQL.

        Args:
            workflow_id: Unique identifier for the workflow
            state: Serialized state dictionary
        """
        pool = await self._get_pool()
        state_json = json.dumps(state)

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self.table_name} (workflow_id, state_jsonb, updated_at)
                VALUES ($1, $2::jsonb, CURRENT_TIMESTAMP)
                ON CONFLICT (workflow_id) DO UPDATE SET
                    state_jsonb = EXCLUDED.state_jsonb,
                    updated_at = CURRENT_TIMESTAMP
                """,
                workflow_id,
                state_json,
            )

        logger.info(
            "state_saved",
            workflow_id=workflow_id,
            backend="postgresql",
            size=len(state_json),
        )

    async def load(self, workflow_id: str) -> dict[str, Any] | None:
        """Load state from PostgreSQL.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Serialized state dictionary or None if not found
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT state_jsonb FROM {self.table_name} WHERE workflow_id = $1",
                workflow_id,
            )

        if row:
            state = json.loads(row["state_jsonb"])
            logger.info("state_loaded", workflow_id=workflow_id, backend="postgresql")
            return state
        else:
            logger.warning("state_not_found", workflow_id=workflow_id, backend="postgresql")
            return None

    async def delete(self, workflow_id: str) -> bool:
        """Delete state from PostgreSQL.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            True if deleted, False if not found
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE workflow_id = $1",
                workflow_id,
            )

        # Parse result like "DELETE 1"
        deleted = int(result.split()[-1]) > 0

        if deleted:
            logger.info("state_deleted", workflow_id=workflow_id, backend="postgresql")
        else:
            logger.warning("state_not_found_for_delete", workflow_id=workflow_id, backend="postgresql")

        return deleted

    async def list_workflows(self) -> list[str]:
        """List all workflow IDs in PostgreSQL.

        Returns:
            List of workflow IDs ordered by most recently updated
        """
        pool = await self._get_pool()

        async with pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT workflow_id FROM {self.table_name} ORDER BY updated_at DESC")

        workflows = [row["workflow_id"] for row in rows]
        logger.info("workflows_listed", count=len(workflows), backend="postgresql")
        return workflows

    async def close(self) -> None:
        """Close the connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("connection_pool_closed", backend="postgresql")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._get_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
