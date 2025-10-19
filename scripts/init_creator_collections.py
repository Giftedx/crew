#!/usr/bin/env python3
"""Initialize Creator Intelligence Collections in Qdrant.

This script sets up the specialized collections for the Creator Intelligence system
with optimal configuration for production workloads.

Usage:
    python scripts/init_creator_collections.py --tenant <tenant> --workspace <workspace>
    python scripts/init_creator_collections.py --all  # Initialize for all tenants

Environment Variables:
    QDRANT_URL: Qdrant server URL (default: http://localhost:6333)
    QDRANT_API_KEY: Optional API key for Qdrant Cloud
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from memory.creator_intelligence_collections import COLLECTION_CONFIGS, get_collection_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def init_collections_for_tenant(tenant: str, workspace: str) -> bool:
    """Initialize all creator intelligence collections for a tenant/workspace.

    Args:
        tenant: Tenant identifier
        workspace: Workspace identifier

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"🚀 Initializing Creator Intelligence collections for {tenant}:{workspace}")

    try:
        # Get collection manager
        manager = get_collection_manager(enable_semantic_cache=True)

        # Initialize all collections
        result = manager.initialize_collections(tenant=tenant, workspace=workspace)

        if result.success:
            data = result.data or {}
            logger.info(f"✅ Successfully initialized {data.get('total', 0)} collections")
            logger.info(f"📦 Collections: {', '.join(data.get('initialized', []))}")
            return True
        else:
            logger.error(f"❌ Collection initialization failed: {result.error}")
            if result.metadata:
                logger.error(f"   Failed collections: {result.metadata.get('failed', [])}")
            return False

    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}")
        return False


def verify_collections(tenant: str, workspace: str) -> bool:
    """Verify that collections were created successfully.

    Args:
        tenant: Tenant identifier
        workspace: Workspace identifier

    Returns:
        True if all collections exist and are healthy, False otherwise
    """
    logger.info(f"🔍 Verifying collections for {tenant}:{workspace}")

    manager = get_collection_manager()
    all_healthy = True

    for collection_type in COLLECTION_CONFIGS.keys():
        result = manager.get_collection_stats(
            collection_type=collection_type,  # type: ignore
            tenant=tenant,
            workspace=workspace,
        )

        if result.success:
            stats = result.data or {}
            logger.info(
                f"  ✅ {collection_type}: "
                f"{stats.get('vectors_count', 0)} vectors, "
                f"quantization={'enabled' if stats.get('quantization_enabled') else 'disabled'}"
            )
        else:
            logger.error(f"  ❌ {collection_type}: {result.error}")
            all_healthy = False

    return all_healthy


def print_collection_info() -> None:
    """Print information about available collections."""
    print("\n📚 Creator Intelligence Collections:")
    print("=" * 60)

    for name, config in COLLECTION_CONFIGS.items():
        print(f"\n🔹 {name.upper()}")
        print(f"   Collection: {config.name}")
        print(f"   Description: {config.description}")
        print(f"   Embedding Model: {config.embedding_model}")
        print(f"   Dimension: {config.dimension}")
        print(f"   Quantization: {'enabled' if config.enable_quantization else 'disabled'}")
        print(f"   Sparse Vectors: {'enabled' if config.enable_sparse_vectors else 'disabled'}")
        print(f"   Semantic Cache: {'enabled' if config.enable_semantic_cache else 'disabled'}")

        if config.payload_schema:
            print(f"   Payload Fields: {', '.join(config.payload_schema.keys())}")

    print("\n" + "=" * 60 + "\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize Creator Intelligence collections in Qdrant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize for a specific tenant/workspace
  python scripts/init_creator_collections.py --tenant default --workspace main

  # Initialize with verification
  python scripts/init_creator_collections.py --tenant default --workspace main --verify

  # Show collection information only
  python scripts/init_creator_collections.py --info

  # Initialize for default tenant with custom workspace
  python scripts/init_creator_collections.py --workspace research_team
        """,
    )

    parser.add_argument(
        "--tenant",
        type=str,
        default="default",
        help="Tenant identifier (default: default)",
    )

    parser.add_argument(
        "--workspace",
        type=str,
        default="main",
        help="Workspace identifier (default: main)",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify collections after initialization",
    )

    parser.add_argument(
        "--info",
        action="store_true",
        help="Show collection information and exit",
    )

    args = parser.parse_args()

    # Show collection info if requested
    if args.info:
        print_collection_info()
        return 0

    # Initialize collections
    logger.info("=" * 60)
    logger.info("Creator Intelligence Collection Initialization")
    logger.info("=" * 60)

    success = init_collections_for_tenant(tenant=args.tenant, workspace=args.workspace)

    if not success:
        logger.error("❌ Initialization failed")
        return 1

    # Verify if requested
    if args.verify:
        logger.info("\n" + "=" * 60)
        logger.info("Verification")
        logger.info("=" * 60)

        if not verify_collections(tenant=args.tenant, workspace=args.workspace):
            logger.error("❌ Verification failed")
            return 1

    logger.info("\n✨ All operations completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
