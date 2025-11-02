"""SQLite state persistence backend for local file-based storage."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import structlog


logger = structlog.get_logger(__name__)


class SQLiteBackend:
    """SQLite storage backend for workflow state.

    This backend stores state in a local SQLite database file, providing
    persistent storage that survives process restarts. Suitable for
    single-machine deployments and development.

    Attributes:
        db_path: Path to the SQLite database file
        _conn: SQLite connection (created lazily)
    """

    def __init__(self, db_path: str | Path = "workflow_states.db") -> None:
        """Initialize the SQLite backend.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        logger.info("sqlite_backend_initialized", db_path=str(self.db_path))

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create SQLite connection.

        Returns:
            SQLite connection
        """
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._create_table()
        return self._conn

    def _create_table(self) -> None:
        """Create the workflow_states table if it doesn't exist."""
        conn = self._conn or self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_states (
                workflow_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.debug("table_created_or_verified", backend="sqlite")

    async def save(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Save state to SQLite.

        Args:
            workflow_id: Unique identifier for the workflow
            state: Serialized state dictionary
        """
        conn = self._get_connection()
        state_json = json.dumps(state)

        conn.execute(
            """
            INSERT INTO workflow_states (workflow_id, state_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(workflow_id) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
        """,
            (workflow_id, state_json),
        )
        conn.commit()

        logger.info("state_saved", workflow_id=workflow_id, backend="sqlite", size=len(state_json))

    async def load(self, workflow_id: str) -> dict[str, Any] | None:
        """Load state from SQLite.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Serialized state dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.execute("SELECT state_json FROM workflow_states WHERE workflow_id = ?", (workflow_id,))
        row = cursor.fetchone()

        if row:
            state = json.loads(row["state_json"])
            logger.info("state_loaded", workflow_id=workflow_id, backend="sqlite")
            return state
        else:
            logger.warning("state_not_found", workflow_id=workflow_id, backend="sqlite")
            return None

    async def delete(self, workflow_id: str) -> bool:
        """Delete state from SQLite.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.execute("DELETE FROM workflow_states WHERE workflow_id = ?", (workflow_id,))
        conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("state_deleted", workflow_id=workflow_id, backend="sqlite")
        else:
            logger.warning("state_not_found_for_delete", workflow_id=workflow_id, backend="sqlite")

        return deleted

    async def list_workflows(self) -> list[str]:
        """List all workflow IDs in SQLite.

        Returns:
            List of workflow IDs
        """
        conn = self._get_connection()
        cursor = conn.execute("SELECT workflow_id FROM workflow_states ORDER BY updated_at DESC")
        workflows = [row["workflow_id"] for row in cursor.fetchall()]

        logger.info("workflows_listed", count=len(workflows), backend="sqlite")
        return workflows

    def close(self) -> None:
        """Close the SQLite connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("connection_closed", backend="sqlite")

    def __del__(self) -> None:
        """Cleanup: close connection on deletion."""
        self.close()
