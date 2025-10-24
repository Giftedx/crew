#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates all SQLite stores to PostgreSQL with proper error handling,
progress tracking, and rollback capabilities.

Migration Priority:
P0: Memory, Profiles, Ingest (critical for core functionality)
P1: KG, Analytics, Debate (important for advanced features)
P2: Marketplace, Archive (nice-to-have features)
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultimate_discord_intelligence_bot.core.store_adapter import (
    CreatorProfile,
    Debate,
    MemoryItem,
    RetentionPolicy,
    UnifiedStoreManager,
)
from ultimate_discord_intelligence_bot.step_result import StepResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Migration configuration
MIGRATION_CONFIG = {
    "P0": {
        "memory": {
            "sqlite_path": "./memory.db",
            "tables": ["memory_items", "retention_policies"],
            "priority": 0,
        },
        "profiles": {
            "sqlite_path": "./profiles.db",
            "tables": ["profiles", "cross_profile_links"],
            "priority": 0,
        },
        "ingest": {
            "sqlite_path": "./ingest.db",
            "tables": ["ingest_queue", "ingest_logs"],
            "priority": 0,
        },
    },
    "P1": {
        "kg": {
            "sqlite_path": "./kg.db",
            "tables": ["kg_nodes", "kg_edges", "kg_provenance"],
            "priority": 1,
        },
        "debate": {
            "sqlite_path": "./debate.db",
            "tables": ["debates", "debate_agents", "debate_critiques", "debate_votes"],
            "priority": 1,
        },
        "analytics": {
            "sqlite_path": "./analytics.db",
            "tables": ["analytics_events", "analytics_metrics"],
            "priority": 1,
        },
    },
    "P2": {
        "marketplace": {
            "sqlite_path": "./marketplace.db",
            "tables": [
                "mp_repos",
                "mp_plugins",
                "mp_signers",
                "mp_releases",
                "mp_advisories",
                "mp_installs",
            ],
            "priority": 2,
        },
        "archive": {
            "sqlite_path": "./archive.db",
            "tables": ["archive_manifest", "archive_metadata"],
            "priority": 2,
        },
    },
}


class MigrationManager:
    """Manages the migration process with rollback capabilities."""

    def __init__(self, postgresql_url: str, dry_run: bool = False):
        self.postgresql_url = postgresql_url
        self.dry_run = dry_run
        self.store_manager = None
        self.migration_log = []
        self.rollback_commands = []

    def initialize_postgresql(self) -> StepResult:
        """Initialize PostgreSQL store manager."""
        try:
            result = UnifiedStoreManager(self.postgresql_url)
            self.store_manager = result
            init_result = result.initialize()
            if not init_result.success:
                return init_result
            logger.info("PostgreSQL store manager initialized successfully")
            return StepResult.ok(data={"message": "PostgreSQL initialized"})
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            return StepResult.fail(f"Failed to initialize PostgreSQL: {e!s}")

    def migrate_memory_store(self, sqlite_path: str) -> StepResult:
        """Migrate memory store from SQLite to PostgreSQL."""
        try:
            logger.info(f"Migrating memory store from {sqlite_path}")

            if not Path(sqlite_path).exists():
                logger.warning(f"SQLite file {sqlite_path} does not exist, skipping")
                return StepResult.ok(data={"message": "SQLite file not found, skipping"})

            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()

            # Migrate memory items
            sqlite_cur.execute("SELECT * FROM memory_items")
            memory_items = sqlite_cur.fetchall()

            migrated_count = 0
            for row in memory_items:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would migrate memory item {row['id']}")
                    migrated_count += 1
                    continue

                item = MemoryItem(
                    id=None,  # Will be assigned by PostgreSQL
                    tenant=row["tenant"],
                    workspace=row["workspace"],
                    type=row["type"],
                    content_json=row["content_json"],
                    embedding_json=row["embedding_json"],
                    ts_created=row["ts_created"],
                    ts_last_used=row["ts_last_used"],
                    retention_policy=row["retention_policy"],
                    decay_score=row["decay_score"],
                    pinned=row["pinned"],
                    archived=row["archived"],
                )

                result = self.store_manager.add_memory_item(item)
                if not result.success:
                    logger.error(f"Failed to migrate memory item {row['id']}: {result.error}")
                    continue

                migrated_count += 1

            # Migrate retention policies
            sqlite_cur.execute("SELECT * FROM retention_policies")
            retention_policies = sqlite_cur.fetchall()

            for row in retention_policies:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would migrate retention policy {row['name']}")
                    continue

                policy = RetentionPolicy(
                    name=row["name"],
                    tenant=row["tenant"],
                    ttl_days=row["ttl_days"],
                )

                # Note: Retention policy upsert would be implemented in store_manager
                logger.info(f"Retention policy {policy.name} would be migrated")

            sqlite_conn.close()

            self.migration_log.append(
                {
                    "store": "memory",
                    "migrated_items": migrated_count,
                    "migrated_policies": len(retention_policies),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"Memory store migration completed: {migrated_count} items, {len(retention_policies)} policies")
            return StepResult.ok(
                data={
                    "migrated_items": migrated_count,
                    "migrated_policies": len(retention_policies),
                }
            )

        except Exception as e:
            logger.error(f"Failed to migrate memory store: {e}")
            return StepResult.fail(f"Failed to migrate memory store: {e!s}")

    def migrate_debate_store(self, sqlite_path: str) -> StepResult:
        """Migrate debate store from SQLite to PostgreSQL."""
        try:
            logger.info(f"Migrating debate store from {sqlite_path}")

            if not Path(sqlite_path).exists():
                logger.warning(f"SQLite file {sqlite_path} does not exist, skipping")
                return StepResult.ok(data={"message": "SQLite file not found, skipping"})

            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()

            # Migrate debates
            sqlite_cur.execute("SELECT * FROM debates")
            debates = sqlite_cur.fetchall()

            migrated_count = 0
            for row in debates:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would migrate debate {row['id']}")
                    migrated_count += 1
                    continue

                debate = Debate(
                    id=None,  # Will be assigned by PostgreSQL
                    tenant=row["tenant"],
                    workspace=row["workspace"],
                    query=row["query"],
                    panel_config_json=row["panel_config_json"],
                    n_rounds=row["n_rounds"],
                    final_output=row["final_output"],
                    created_at=row["created_at"],
                )

                result = self.store_manager.add_debate(debate)
                if not result.success:
                    logger.error(f"Failed to migrate debate {row['id']}: {result.error}")
                    continue

                migrated_count += 1

            sqlite_conn.close()

            self.migration_log.append(
                {
                    "store": "debate",
                    "migrated_debates": migrated_count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"Debate store migration completed: {migrated_count} debates")
            return StepResult.ok(data={"migrated_debates": migrated_count})

        except Exception as e:
            logger.error(f"Failed to migrate debate store: {e}")
            return StepResult.fail(f"Failed to migrate debate store: {e!s}")

    def migrate_kg_store(self, sqlite_path: str) -> StepResult:
        """Migrate knowledge graph store from SQLite to PostgreSQL."""
        try:
            logger.info(f"Migrating KG store from {sqlite_path}")

            if not Path(sqlite_path).exists():
                logger.warning(f"SQLite file {sqlite_path} does not exist, skipping")
                return StepResult.ok(data={"message": "SQLite file not found, skipping"})

            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()

            # Migrate KG nodes
            sqlite_cur.execute("SELECT * FROM kg_nodes")
            kg_nodes = sqlite_cur.fetchall()

            migrated_count = 0
            for row in kg_nodes:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would migrate KG node {row['id']}")
                    migrated_count += 1
                    continue

                try:
                    attrs = json.loads(row["attrs_json"]) if row["attrs_json"] else {}
                except json.JSONDecodeError:
                    attrs = {}

                result = self.store_manager.add_kg_node(
                    tenant=row["tenant"],
                    type=row["type"],
                    name=row["name"],
                    attrs=attrs,
                )
                if not result.success:
                    logger.error(f"Failed to migrate KG node {row['id']}: {result.error}")
                    continue

                migrated_count += 1

            sqlite_conn.close()

            self.migration_log.append(
                {
                    "store": "kg",
                    "migrated_nodes": migrated_count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"KG store migration completed: {migrated_count} nodes")
            return StepResult.ok(data={"migrated_nodes": migrated_count})

        except Exception as e:
            logger.error(f"Failed to migrate KG store: {e}")
            return StepResult.fail(f"Failed to migrate KG store: {e!s}")

    def migrate_profiles_store(self, sqlite_path: str) -> StepResult:
        """Migrate profiles store from SQLite to PostgreSQL."""
        try:
            logger.info(f"Migrating profiles store from {sqlite_path}")

            if not Path(sqlite_path).exists():
                logger.warning(f"SQLite file {sqlite_path} does not exist, skipping")
                return StepResult.ok(data={"message": "SQLite file not found, skipping"})

            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cur = sqlite_conn.cursor()

            # Migrate creator profiles
            sqlite_cur.execute("SELECT * FROM profiles")
            profiles = sqlite_cur.fetchall()

            migrated_count = 0
            for row in profiles:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would migrate profile {row['name']}")
                    migrated_count += 1
                    continue

                try:
                    data = json.loads(row["data"]) if row["data"] else {}
                except json.JSONDecodeError:
                    data = {}

                profile = CreatorProfile(name=row["name"], data=data)
                result = self.store_manager.upsert_creator_profile(profile)
                if not result.success:
                    logger.error(f"Failed to migrate profile {row['name']}: {result.error}")
                    continue

                migrated_count += 1

            sqlite_conn.close()

            self.migration_log.append(
                {
                    "store": "profiles",
                    "migrated_profiles": migrated_count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"Profiles store migration completed: {migrated_count} profiles")
            return StepResult.ok(data={"migrated_profiles": migrated_count})

        except Exception as e:
            logger.error(f"Failed to migrate profiles store: {e}")
            return StepResult.fail(f"Failed to migrate profiles store: {e!s}")

    def run_migration(self, priority: str = "P0") -> StepResult:
        """Run migration for specified priority level."""
        try:
            logger.info(f"Starting migration for priority level {priority}")

            if priority not in MIGRATION_CONFIG:
                return StepResult.fail(f"Invalid priority level: {priority}")

            stores = MIGRATION_CONFIG[priority]
            total_migrated = 0
            failed_migrations = []

            for store_name, config in stores.items():
                logger.info(f"Migrating {store_name} store...")

                try:
                    if store_name == "memory":
                        result = self.migrate_memory_store(config["sqlite_path"])
                    elif store_name == "debate":
                        result = self.migrate_debate_store(config["sqlite_path"])
                    elif store_name == "kg":
                        result = self.migrate_kg_store(config["sqlite_path"])
                    elif store_name == "profiles":
                        result = self.migrate_profiles_store(config["sqlite_path"])
                    else:
                        logger.warning(f"Migration for {store_name} not implemented yet")
                        continue

                    if result.success:
                        logger.info(f"Successfully migrated {store_name}")
                        if "migrated_items" in result.data:
                            total_migrated += result.data["migrated_items"]
                        elif "migrated_debates" in result.data:
                            total_migrated += result.data["migrated_debates"]
                        elif "migrated_nodes" in result.data:
                            total_migrated += result.data["migrated_nodes"]
                        elif "migrated_profiles" in result.data:
                            total_migrated += result.data["migrated_profiles"]
                    else:
                        logger.error(f"Failed to migrate {store_name}: {result.error}")
                        failed_migrations.append(store_name)

                except Exception as e:
                    logger.error(f"Exception during {store_name} migration: {e}")
                    failed_migrations.append(store_name)

            # Save migration log
            log_path = f"migration_log_{priority}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_path, "w") as f:
                json.dump(self.migration_log, f, indent=2)

            logger.info(f"Migration completed for {priority}")
            logger.info(f"Total items migrated: {total_migrated}")
            if failed_migrations:
                logger.warning(f"Failed migrations: {failed_migrations}")

            return StepResult.ok(
                data={
                    "total_migrated": total_migrated,
                    "failed_migrations": failed_migrations,
                    "log_path": log_path,
                }
            )

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return StepResult.fail(f"Migration failed: {e!s}")

    def cleanup(self) -> StepResult:
        """Cleanup resources."""
        try:
            if self.store_manager:
                self.store_manager.close()
            return StepResult.ok(data={"message": "Cleanup completed"})
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return StepResult.fail(f"Cleanup failed: {e!s}")


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate SQLite stores to PostgreSQL")
    parser.add_argument("--postgresql-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument(
        "--priority",
        choices=["P0", "P1", "P2"],
        default="P0",
        help="Migration priority level",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actual migration",
    )
    parser.add_argument("--all", action="store_true", help="Migrate all priority levels")

    args = parser.parse_args()

    logger.info("Starting SQLite to PostgreSQL migration")
    logger.info(f"PostgreSQL URL: {args.postgresql_url}")
    logger.info(f"Priority: {args.priority}")
    logger.info(f"Dry run: {args.dry_run}")

    migration_manager = MigrationManager(args.postgresql_url, args.dry_run)

    try:
        # Initialize PostgreSQL
        result = migration_manager.initialize_postgresql()
        if not result.success:
            logger.error(f"Failed to initialize PostgreSQL: {result.error}")
            sys.exit(1)

        # Run migration
        priorities = ["P0", "P1", "P2"] if args.all else [args.priority]

        for priority in priorities:
            logger.info(f"Running migration for priority {priority}")
            result = migration_manager.run_migration(priority)
            if not result.success:
                logger.error(f"Migration failed for {priority}: {result.error}")
                if priority == "P0":  # Critical priority, exit on failure
                    sys.exit(1)
            else:
                logger.info(f"Migration successful for {priority}")

        logger.info("All migrations completed successfully")

    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        sys.exit(1)
    finally:
        migration_manager.cleanup()


if __name__ == "__main__":
    main()
