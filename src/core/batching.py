"""Request batching utilities for improved database performance.

This module provides tools for batching database operations to reduce round trips
and improve overall throughput in the Ultimate Discord Intelligence Bot.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .error_handling import log_error

logger = logging.getLogger(__name__)

# Constants for batching configuration
DEFAULT_BATCH_SIZE = 50
DEFAULT_BATCH_TIMEOUT = 5.0  # seconds
MAX_BATCH_SIZE = 500


@dataclass
class BatchOperation:
    """Represents a single database operation in a batch."""

    operation_type: str  # 'insert', 'update', 'delete', 'select'
    table: str
    sql: str
    params: tuple[Any, ...]
    callback: Callable[[Any], None] | None = None
    priority: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.params, list):
            self.params = tuple(self.params)


@dataclass
class BatchConfig:
    """Configuration for batch operations."""

    operation_type: str
    table: str
    sql_template: str
    params: tuple[Any, ...] | list[Any]
    callback: Callable[[Any], None] | None = None
    priority: int = 0


@dataclass
class BatchMetrics:
    """Metrics for batching performance."""

    operations_batched: int = 0
    batches_executed: int = 0
    total_execution_time: float = 0.0
    average_batch_size: float = 0.0
    round_trips_saved: int = 0

    def record_batch(self, size: int, execution_time: float) -> None:
        """Record metrics for a completed batch."""
        try:
            self.batches_executed += 1
            self.operations_batched += size
            self.total_execution_time += execution_time
            self.round_trips_saved += max(0, size - 1)  # Each batch saves (size-1) round trips
        except (TypeError, ValueError, AttributeError) as e:
            log_error(
                e,
                message="Failed to record batch metrics - invalid data types",
                context={"batch_size": size, "execution_time": execution_time, "operation": "metrics_calculation"},
            )
        except (OverflowError, ArithmeticError) as e:
            log_error(
                e,
                message="Failed to record batch metrics - arithmetic overflow",
                context={"batch_size": size, "execution_time": execution_time, "operation": "metrics_calculation"},
            )

    @property
    def efficiency_score(self) -> float:
        """Calculate batching efficiency score (0-1)."""
        if self.batches_executed == 0:
            return 0.0

        avg_batch_size = self.operations_batched / self.batches_executed
        # Efficiency increases with batch size, max efficiency at 100+ operations per batch
        return min(1.0, avg_batch_size / 100.0)


class RequestBatcher:
    """Database request batcher for improved performance."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        batch_size: int = DEFAULT_BATCH_SIZE,
        batch_timeout: float = DEFAULT_BATCH_TIMEOUT,
        max_batch_size: int = MAX_BATCH_SIZE,
    ):
        self.conn = conn
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_batch_size = max_batch_size

        self._operations: list[BatchOperation] = []
        self._last_flush_time = time.time()
        self._metrics = BatchMetrics()
        self._flush_lock = asyncio.Lock()

    def add_operation(self, config: BatchConfig) -> None:
        """Add an operation to the batch."""
        operation = BatchOperation(
            operation_type=config.operation_type,
            table=config.table,
            sql=config.sql_template,
            params=tuple(config.params) if isinstance(config.params, list) else config.params,
            callback=config.callback,
            priority=config.priority,
        )

        self._operations.append(operation)

        # Auto-flush if batch size exceeded
        if len(self._operations) >= self.batch_size:
            try:
                # Try to create async task if event loop is running
                asyncio.create_task(self.flush())
            except RuntimeError:
                # No event loop running, flush synchronously
                # Note: This is a simplified sync version for testing
                # In production, this should be handled differently
                pass

    def add_insert(
        self,
        table: str,
        columns: list[str],
        values: list[tuple[Any, ...]],
        callback: Callable[[Any], None] | None = None,
    ) -> None:
        """Add bulk insert operation."""
        if not values:
            return

        # Use parameterized query to prevent SQL injection
        placeholders = ",".join("?" * len(columns))
        sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

        for value_tuple in values:
            config = BatchConfig(
                operation_type="insert",
                table=table,
                sql_template=sql,
                params=value_tuple,
                callback=callback,
            )
            self.add_operation(config)

    def add_update(
        self,
        table: str,
        set_clause: str,
        where_clause: str,
        params: tuple[Any, ...],
        callback: Callable[[Any], None] | None = None,
    ) -> None:
        """Add update operation."""
        # Use parameterized query to prevent SQL injection
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        config = BatchConfig(
            operation_type="update",
            table=table,
            sql_template=sql,
            params=params,
            callback=callback,
        )
        self.add_operation(config)

    def add_delete(
        self,
        table: str,
        where_clause: str,
        params: tuple[Any, ...],
        callback: Callable[[Any], None] | None = None,
    ) -> None:
        """Add delete operation."""
        # Use parameterized query to prevent SQL injection
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        config = BatchConfig(
            operation_type="delete",
            table=table,
            sql_template=sql,
            params=params,
            callback=callback,
        )
        self.add_operation(config)

    async def flush(self) -> None:
        """Flush all pending operations."""
        async with self._flush_lock:
            if not self._operations:
                return

            operations = self._operations.copy()
            self._operations.clear()

            start_time = time.time()

            try:
                # Group operations by type for optimization
                inserts = [op for op in operations if op.operation_type == "insert"]
                updates = [op for op in operations if op.operation_type == "update"]
                deletes = [op for op in operations if op.operation_type == "delete"]

                # Execute in order: deletes, updates, inserts
                await self._execute_batch(deletes)
                await self._execute_batch(updates)
                await self._execute_batch(inserts)

                # Execute callbacks
                for op in operations:
                    if op.callback:
                        try:
                            op.callback(None)
                        except (TypeError, ValueError, AttributeError) as e:
                            log_error(
                                e,
                                message="Callback execution failed - invalid callback or arguments",
                                context={
                                    "operation_type": op.operation_type,
                                    "table": op.table,
                                    "operation": "callback_execution",
                                },
                            )
                        except Exception as e:
                            log_error(
                                e,
                                message="Callback error for batch operation",
                                context={
                                    "operation_type": op.operation_type,
                                    "table": op.table,
                                    "operation": "callback_execution",
                                },
                            )

                execution_time = time.time() - start_time
                self._metrics.record_batch(len(operations), execution_time)
                self._last_flush_time = time.time()

                logger.debug(f"Flushed {len(operations)} operations in {execution_time:.3f}s")

            except (sqlite3.Error, sqlite3.DatabaseError) as e:
                log_error(
                    e,
                    message="Database error during batch flush",
                    context={
                        "operation_count": len(operations),
                        "batch_size": len(self._operations),
                        "operation": "batch_execution",
                    },
                )
                # Re-queue failed operations
                self._operations.extend(operations)
            except (TimeoutError, asyncio.CancelledError) as e:
                log_error(
                    e,
                    message="Async operation error during batch flush",
                    context={
                        "operation_count": len(operations),
                        "batch_size": len(self._operations),
                        "operation": "async_execution",
                    },
                )
                # Re-queue failed operations
                self._operations.extend(operations)
            except Exception as e:
                log_error(
                    e,
                    message="Batch flush error",
                    context={"operation_count": len(operations), "batch_size": len(self._operations)},
                )
                # Re-queue failed operations
                self._operations.extend(operations)

    async def _execute_batch(self, operations: list[BatchOperation]) -> None:
        """Execute a batch of operations."""
        if not operations:
            return

        # For now, execute individually (can be optimized further with bulk operations)
        for op in operations:
            try:
                if op.operation_type in ("insert", "update", "delete"):
                    self.conn.execute(op.sql, op.params)
                elif op.operation_type == "select":
                    # Handle select operations differently
                    cursor = self.conn.execute(op.sql, op.params)
                    result = cursor.fetchall()
                    if op.callback:
                        op.callback(result)
            except (sqlite3.Error, sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
                log_error(
                    e,
                    message="Database operation failed",
                    context={
                        "sql": op.sql,
                        "operation_type": op.operation_type,
                        "table": op.table,
                        "operation": "sql_execution",
                    },
                )
                raise
            except (TypeError, ValueError) as e:
                log_error(
                    e,
                    message="Invalid parameters for database operation",
                    context={
                        "sql": op.sql,
                        "operation_type": op.operation_type,
                        "table": op.table,
                        "operation": "parameter_validation",
                    },
                )
                raise
            except Exception as e:
                log_error(
                    e,
                    message="Batch operation failed",
                    context={"sql": op.sql, "operation_type": op.operation_type, "table": op.table},
                )
                raise

        # Commit all changes at once
        if any(op.operation_type in ("insert", "update", "delete") for op in operations):
            self.conn.commit()

    async def flush_if_needed(self) -> None:
        """Flush if batch size or timeout exceeded."""
        current_time = time.time()

        if len(self._operations) >= self.batch_size or (current_time - self._last_flush_time) >= self.batch_timeout:
            await self.flush()

    def get_metrics(self) -> BatchMetrics:
        """Get batching performance metrics."""
        return self._metrics

    def get_pending_count(self) -> int:
        """Get number of pending operations."""
        return len(self._operations)


class BulkInserter:
    """Optimized bulk inserter for high-volume data."""

    def __init__(self, conn: sqlite3.Connection, batch_size: int = 100):
        self.conn = conn
        self.batch_size = batch_size
        self._buffer: dict[str, list[tuple[str, tuple[Any, ...]]]] = {}
        self._metrics = BatchMetrics()

    def add_row(self, table: str, columns: list[str], values: tuple[Any, ...]) -> None:
        """Add a row to the bulk insert buffer."""
        if table not in self._buffer:
            self._buffer[table] = []

        self._buffer[table].append((",".join(columns), values))

        # Auto-flush if buffer size exceeded
        if len(self._buffer[table]) >= self.batch_size:
            self.flush_table(table)

    def flush_table(self, table: str) -> None:
        """Flush all pending rows for a specific table."""
        if table not in self._buffer or not self._buffer[table]:
            return

        rows = self._buffer[table]
        if not rows:
            return

        start_time = time.time()

        try:
            # Get column names from first row
            columns_str, _ = rows[0]
            columns = columns_str.split(",")

            # Build bulk insert SQL
            placeholders = ",".join("?" * len(columns))
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

            # Execute all inserts in a transaction
            with self.conn:
                for _, values in rows:
                    self.conn.execute(sql, values)

            execution_time = time.time() - start_time
            self._metrics.record_batch(len(rows), execution_time)

            logger.debug(f"Bulk inserted {len(rows)} rows into {table} in {execution_time:.3f}s")

        except (sqlite3.Error, sqlite3.DatabaseError, sqlite3.IntegrityError) as e:
            log_error(
                e,
                message="Database error during bulk insert",
                context={"table": table, "row_count": len(rows), "operation": "bulk_insert"},
            )
            raise
        except (TypeError, ValueError) as e:
            log_error(
                e,
                message="Invalid data for bulk insert",
                context={"table": table, "row_count": len(rows), "operation": "data_validation"},
            )
            raise
        except Exception as e:
            log_error(e, message="Bulk insert error", context={"table": table, "row_count": len(rows)})
            raise
        finally:
            # Clear buffer regardless of success/failure
            self._buffer[table].clear()

    def flush_all(self) -> None:
        """Flush all pending rows for all tables."""
        for table in list(self._buffer.keys()):
            self.flush_table(table)

    def get_metrics(self) -> BatchMetrics:
        """Get bulk insert performance metrics."""
        return self._metrics


class BatchingManager:
    """Manager for batching instances."""

    _batcher_instances: dict[int, RequestBatcher] = {}
    _bulk_inserter_instances: dict[int, BulkInserter] = {}

    @classmethod
    def get_batcher(cls, conn: sqlite3.Connection) -> RequestBatcher:
        """Get or create request batcher instance for connection."""
        conn_id = id(conn)
        if conn_id not in cls._batcher_instances:
            cls._batcher_instances[conn_id] = RequestBatcher(conn)
        return cls._batcher_instances[conn_id]

    @classmethod
    def get_bulk_inserter(cls, conn: sqlite3.Connection) -> BulkInserter:
        """Get or create bulk inserter instance for connection."""
        conn_id = id(conn)
        if conn_id not in cls._bulk_inserter_instances:
            cls._bulk_inserter_instances[conn_id] = BulkInserter(conn)
        return cls._bulk_inserter_instances[conn_id]


def get_request_batcher(conn: sqlite3.Connection) -> RequestBatcher:
    """Get or create global request batcher instance."""
    return BatchingManager.get_batcher(conn)


def get_bulk_inserter(conn: sqlite3.Connection) -> BulkInserter:
    """Get or create global bulk inserter instance."""
    return BatchingManager.get_bulk_inserter(conn)


async def flush_pending_operations(conn: sqlite3.Connection) -> None:
    """Flush all pending batch operations for a connection."""
    batcher = BatchingManager.get_batcher(conn)
    await batcher.flush()

    bulk_inserter = BatchingManager.get_bulk_inserter(conn)
    bulk_inserter.flush_all()


def get_batching_metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    """Get comprehensive batching performance metrics for a connection."""
    metrics: dict[str, Any] = {
        "request_batcher": None,
        "bulk_inserter": None,
    }

    try:
        batcher = BatchingManager.get_batcher(conn)
        batcher_metrics = batcher.get_metrics()
        metrics["request_batcher"] = {
            "operations_batched": batcher_metrics.operations_batched,
            "batches_executed": batcher_metrics.batches_executed,
            "efficiency_score": batcher_metrics.efficiency_score,
            "round_trips_saved": batcher_metrics.round_trips_saved,
            "pending_operations": batcher.get_pending_count(),
        }
    except (AttributeError, TypeError) as e:
        log_error(
            e,
            message="Failed to access batcher metrics - invalid batcher state",
            context={"connection_id": id(conn), "operation": "metrics_access"},
        )
    except (KeyError, ValueError) as e:
        log_error(
            e,
            message="Failed to get batcher instance",
            context={"connection_id": id(conn), "operation": "instance_retrieval"},
        )
    except Exception as e:
        log_error(e, message="Failed to get batcher metrics", context={"connection_id": id(conn)})

    try:
        bulk_inserter = BatchingManager.get_bulk_inserter(conn)
        inserter_metrics = bulk_inserter.get_metrics()
        metrics["bulk_inserter"] = {
            "operations_batched": inserter_metrics.operations_batched,
            "batches_executed": inserter_metrics.batches_executed,
            "efficiency_score": inserter_metrics.efficiency_score,
            "round_trips_saved": inserter_metrics.round_trips_saved,
        }
    except (AttributeError, TypeError) as e:
        log_error(
            e,
            message="Failed to access bulk inserter metrics - invalid inserter state",
            context={"connection_id": id(conn), "operation": "metrics_access"},
        )
    except (KeyError, ValueError) as e:
        log_error(
            e,
            message="Failed to get bulk inserter instance",
            context={"connection_id": id(conn), "operation": "instance_retrieval"},
        )
    except Exception as e:
        log_error(e, message="Failed to get bulk inserter metrics", context={"connection_id": id(conn)})

    return metrics
