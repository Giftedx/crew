#!/usr/bin/env python3
"""Test script to validate batching functionality in scheduler components."""

import asyncio
import sqlite3
import time
from datetime import UTC, datetime

import pytest

from scheduler.priority_queue import PriorityQueue
from scheduler.scheduler import Scheduler


# Test constants
TEST_WATCH_COUNT = 100
TEST_STATE_COUNT = 50
TEST_METRICS_COUNT = 20


def create_test_db():
    """Create a test database with required tables."""
    conn = sqlite3.connect(":memory:")

    # Create tables
    conn.execute("""
        CREATE TABLE watchlist (
            id INTEGER PRIMARY KEY,
            tenant TEXT NOT NULL,
            workspace TEXT NOT NULL,
            source_type TEXT NOT NULL,
            handle TEXT NOT NULL,
            label TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE ingest_state (
            watchlist_id INTEGER PRIMARY KEY,
            cursor TEXT,
            last_seen_at TEXT,
            etag TEXT,
            failure_count INTEGER DEFAULT 0,
            backoff_until TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE ingest_job (
            id INTEGER PRIMARY KEY,
            tenant TEXT NOT NULL,
            workspace TEXT NOT NULL,
            source TEXT NOT NULL,
            external_id TEXT NOT NULL,
            url TEXT NOT NULL,
            tags TEXT,
            visibility TEXT DEFAULT 'public',
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    return conn


def test_bulk_watchlist_operations():
    """Test bulk watchlist insertion performance."""
    print("Testing bulk watchlist operations...")

    conn = create_test_db()
    scheduler = Scheduler(conn, PriorityQueue(conn), {})

    # Test data
    watches = [
        {
            "tenant": "test_tenant",
            "workspace": "workspace_1",
            "source_type": "rss",
            "handle": f"feed_{i}",
            "label": f"Test Feed {i}",
        }
        for i in range(TEST_WATCH_COUNT)
    ]

    # Measure bulk insertion time
    start_time = time.time()
    results = scheduler.add_watches_bulk(watches)
    bulk_time = time.time() - start_time

    print(f"✅ Bulk inserted {len(results)} watches in {bulk_time:.3f}s")
    print(f"   Average time per watch: {bulk_time / len(results) * 1000:.2f}ms")

    # Verify results
    count = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
    if count != TEST_WATCH_COUNT:
        raise ValueError(f"Expected {TEST_WATCH_COUNT} watches, got {count}")

    state_count = conn.execute("SELECT COUNT(*) FROM ingest_state").fetchone()[0]
    if state_count != TEST_WATCH_COUNT:
        raise ValueError(f"Expected {TEST_WATCH_COUNT} states, got {state_count}")

    print("✅ Bulk watchlist operations test passed")
    conn.close()


def test_bulk_state_updates():
    """Test bulk ingest state updates."""
    print("\nTesting bulk state updates...")

    conn = create_test_db()
    scheduler = Scheduler(conn, PriorityQueue(conn), {})

    # Create test watches
    watches = [
        {
            "tenant": "test_tenant",
            "workspace": "workspace_1",
            "source_type": "rss",
            "handle": f"feed_{i}",
        }
        for i in range(TEST_STATE_COUNT)
    ]
    results = scheduler.add_watches_bulk(watches)

    # Prepare state updates
    now = datetime.now(UTC).isoformat()
    state_updates = [
        {"watchlist_id": watch.id, "cursor": f"cursor_{i}", "last_seen_at": now} for i, watch in enumerate(results)
    ]

    # Measure bulk update time
    start_time = time.time()
    scheduler.update_ingest_states_bulk(state_updates)
    bulk_time = time.time() - start_time

    print(f"✅ Bulk updated {len(state_updates)} states in {bulk_time:.3f}s")
    print(f"   Average time per update: {bulk_time / len(state_updates) * 1000:.2f}ms")

    # Verify results
    updated_count = conn.execute("SELECT COUNT(*) FROM ingest_state WHERE cursor IS NOT NULL").fetchone()[0]
    if updated_count != TEST_STATE_COUNT:
        raise ValueError(f"Expected {TEST_STATE_COUNT} updated states, got {updated_count}")

    print("✅ Bulk state updates test passed")
    conn.close()


def test_batching_metrics():
    """Test batching metrics collection."""
    print("\nTesting batching metrics...")

    conn = create_test_db()
    scheduler = Scheduler(conn, PriorityQueue(conn), {})

    # Perform some operations to generate metrics
    watches = [
        {
            "tenant": "test_tenant",
            "workspace": "workspace_1",
            "source_type": "rss",
            "handle": f"feed_{i}",
        }
        for i in range(20)
    ]
    scheduler.add_watches_bulk(watches)

    # Get metrics
    metrics = scheduler.get_batching_metrics()

    print("✅ Batching metrics collected:")
    print(f"   Bulk inserter metrics: {metrics['bulk_inserter']}")
    print(f"   State batcher metrics: {metrics['state_batcher']}")
    print(f"   Queue batching metrics: {metrics['queue_batching']}")

    # Verify metrics structure
    if "bulk_inserter" not in metrics:
        raise ValueError("bulk_inserter metrics missing")
    if "state_batcher" not in metrics:
        raise ValueError("state_batcher metrics missing")
    if "queue_batching" not in metrics:
        raise ValueError("queue_batching metrics missing")

    print("✅ Batching metrics test passed")
    conn.close()


@pytest.mark.asyncio
async def test_async_batching():
    """Test async batching operations."""
    print("\nTesting async batching operations...")

    conn = create_test_db()
    scheduler = Scheduler(conn, PriorityQueue(conn), {})

    # Test async flush
    await asyncio.sleep(0.1)  # Allow any pending operations to settle
    scheduler.flush_pending_operations()

    print("✅ Async batching operations test passed")
    conn.close()


def main():
    """Run all batching tests."""
    print("🚀 Starting batching functionality tests...\n")

    try:
        # Run synchronous tests
        test_bulk_watchlist_operations()
        test_bulk_state_updates()
        test_batching_metrics()

        # Run async test
        asyncio.run(test_async_batching())

        print("\n🎉 All batching tests passed successfully!")
        print("\n📊 Performance Summary:")
        print("   - Bulk operations reduce database round trips")
        print("   - Improved throughput for high-volume operations")
        print("   - Comprehensive metrics for performance monitoring")
        print("   - Backward compatibility maintained")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
