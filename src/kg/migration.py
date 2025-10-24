"""Migration utilities for creator KG schema.

This module provides utilities for migrating existing KG stores to the
creator schema and validating schema integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .creator_kg_store import CreatorKGStore
from .store import KGStore


class KGMigration:
    """Handles migration of KG stores to creator schema."""

    def __init__(self, source_path: str, target_path: str | None = None):
        """Initialize migration with source and target paths."""
        self.source_path = source_path
        self.target_path = target_path or source_path
        self.source_store = KGStore(source_path)
        self.target_store = CreatorKGStore(target_path)

    def migrate_schema(self) -> dict[str, Any]:
        """Migrate from base KGStore to CreatorKGStore."""
        results = {
            "nodes_migrated": 0,
            "edges_migrated": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            # Migrate nodes
            nodes_result = self._migrate_nodes()
            results["nodes_migrated"] = nodes_result["count"]
            results["errors"].extend(nodes_result["errors"])
            results["warnings"].extend(nodes_result["warnings"])

            # Migrate edges
            edges_result = self._migrate_edges()
            results["edges_migrated"] = edges_result["count"]
            results["errors"].extend(edges_result["errors"])
            results["warnings"].extend(edges_result["warnings"])

            # Validate migration
            validation_result = self._validate_migration()
            results["validation"] = validation_result

        except Exception as e:
            results["errors"].append(f"Migration failed: {e!s}")

        return results

    def _migrate_nodes(self) -> dict[str, Any]:
        """Migrate nodes from source to target store."""
        result = {"count": 0, "errors": [], "warnings": []}

        try:
            # Get all nodes from source
            cur = self.source_store.conn.cursor()
            cur.execute("SELECT * FROM kg_nodes")
            rows = cur.fetchall()

            for row in rows:
                try:
                    # Parse attributes
                    attrs = json.loads(row["attrs_json"]) if row["attrs_json"] else {}

                    # Add to target store with validation
                    self.target_store.add_creator_node(
                        tenant=row["tenant"],
                        node_type=row["type"],
                        name=row["name"],
                        attrs=attrs,
                        created_at=row["created_at"],
                    )
                    result["count"] += 1

                except Exception as e:
                    result["errors"].append(f"Failed to migrate node {row['id']}: {e!s}")

        except Exception as e:
            result["errors"].append(f"Failed to read nodes: {e!s}")

        return result

    def _migrate_edges(self) -> dict[str, Any]:
        """Migrate edges from source to target store."""
        result = {"count": 0, "errors": [], "warnings": []}

        try:
            # Get all edges from source
            cur = self.source_store.conn.cursor()
            cur.execute("SELECT * FROM kg_edges")
            rows = cur.fetchall()

            for row in rows:
                try:
                    # Add to target store with validation
                    self.target_store.add_creator_edge(
                        src_id=row["src_id"],
                        dst_id=row["dst_id"],
                        edge_type=row["type"],
                        weight=row["weight"],
                        provenance_id=row["provenance_id"],
                        created_at=row["created_at"],
                    )
                    result["count"] += 1

                except Exception as e:
                    result["warnings"].append(f"Failed to migrate edge {row['id']}: {e!s}")

        except Exception as e:
            result["errors"].append(f"Failed to read edges: {e!s}")

        return result

    def _validate_migration(self) -> dict[str, Any]:
        """Validate the migrated data."""
        return self.target_store.validate_schema_integrity()

    def create_backup(self, backup_path: str) -> bool:
        """Create a backup of the source database."""
        try:
            source_path = Path(self.source_path)
            backup_path = Path(backup_path)

            if source_path.exists():
                import shutil

                shutil.copy2(source_path, backup_path)
                return True
            return False
        except Exception:
            return False

    def rollback(self, backup_path: str) -> bool:
        """Rollback to backup if migration fails."""
        try:
            backup_path = Path(backup_path)
            target_path = Path(self.target_path)

            if backup_path.exists():
                import shutil

                shutil.copy2(backup_path, target_path)
                return True
            return False
        except Exception:
            return False


def migrate_kg_store(
    source_path: str,
    target_path: str | None = None,
    create_backup: bool = True,
) -> dict[str, Any]:
    """Migrate a KG store to creator schema.

    Args:
        source_path: Path to source KG store
        target_path: Path to target KG store (defaults to source_path)
        create_backup: Whether to create a backup before migration

    Returns:
        Migration results dictionary
    """
    migration = KGMigration(source_path, target_path)

    # Create backup if requested
    if create_backup:
        backup_path = f"{source_path}.backup"
        if not migration.create_backup(backup_path):
            return {"error": "Failed to create backup"}

    # Perform migration
    results = migration.migrate_schema()

    # Add backup info to results
    if create_backup:
        results["backup_path"] = f"{source_path}.backup"

    return results


def validate_kg_store(path: str) -> dict[str, Any]:
    """Validate a KG store against creator schema.

    Args:
        path: Path to KG store

    Returns:
        Validation results dictionary
    """
    try:
        store = CreatorKGStore(path)
        return {
            "valid": True,
            "integrity": store.validate_schema_integrity(),
            "stats": store.get_schema_stats(),
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
        }


def create_sample_creator_data(store: CreatorKGStore, tenant: str = "sample") -> dict[str, Any]:
    """Create sample creator data for testing.

    Args:
        store: Creator KG store
        tenant: Tenant identifier

    Returns:
        Dictionary with created node IDs
    """
    results = {}

    try:
        # Create creators
        h3_id = store.add_creator_node(
            tenant=tenant,
            node_type="creator",
            name="H3 Podcast",
            attrs={
                "platform": "YouTube",
                "channel_id": "UCBJycsmduvYEL83R_U4JriQ",
                "subscriber_count": 3000000,
                "category": "Comedy",
                "language": "English",
            },
        )
        results["h3_creator"] = h3_id

        hasan_id = store.add_creator_node(
            tenant=tenant,
            node_type="creator",
            name="Hasan Piker",
            attrs={
                "platform": "Twitch",
                "channel_id": "hasanabi",
                "subscriber_count": 2000000,
                "category": "Politics",
                "language": "English",
            },
        )
        results["hasan_creator"] = hasan_id

        # Create episodes
        episode_id = store.add_creator_node(
            tenant=tenant,
            node_type="episode",
            name="H3 Podcast #123",
            attrs={
                "title": "H3 Podcast #123 - The Great Debate",
                "duration": 7200,  # 2 hours
                "upload_date": "2024-01-15",
                "platform": "YouTube",
                "view_count": 500000,
                "like_count": 25000,
            },
        )
        results["episode"] = episode_id

        # Create topics
        politics_id = store.add_creator_node(
            tenant=tenant,
            node_type="topic",
            name="Politics",
            attrs={
                "category": "Current Events",
                "trending_score": 0.8,
                "sentiment": "neutral",
            },
        )
        results["politics_topic"] = politics_id

        # Create claims
        claim_id = store.add_creator_node(
            tenant=tenant,
            node_type="claim",
            name="Election was stolen",
            attrs={
                "text": "The 2020 election was stolen from Donald Trump",
                "speaker": "Ethan Klein",
                "timestamp": 1800,  # 30 minutes into episode
                "confidence": 0.3,
                "verification_status": "disputed",
            },
        )
        results["claim"] = claim_id

        # Create edges
        store.add_creator_edge(h3_id, episode_id, "hosts")
        store.add_creator_edge(episode_id, politics_id, "discusses")
        store.add_creator_edge(h3_id, claim_id, "makes_claim")

        results["success"] = True

    except Exception as e:
        results["error"] = str(e)
        results["success"] = False

    return results


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python migration.py <command> [args]")
        print("Commands:")
        print("  migrate <source_path> [target_path]")
        print("  validate <path>")
        print("  sample <path>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        if len(sys.argv) < 3:
            print("Usage: python migration.py migrate <source_path> [target_path]")
            sys.exit(1)

        source_path = sys.argv[2]
        target_path = sys.argv[3] if len(sys.argv) > 3 else None

        results = migrate_kg_store(source_path, target_path)
        print(json.dumps(results, indent=2))

    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: python migration.py validate <path>")
            sys.exit(1)

        path = sys.argv[2]
        results = validate_kg_store(path)
        print(json.dumps(results, indent=2))

    elif command == "sample":
        if len(sys.argv) < 3:
            print("Usage: python migration.py sample <path>")
            sys.exit(1)

        path = sys.argv[2]
        store = CreatorKGStore(path)
        results = create_sample_creator_data(store)
        print(json.dumps(results, indent=2))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
