"""Creator Intelligence MCP Server.

Exposes TOS-compliant content ingestion, Knowledge Graph, and Vector DB tools
for the Creator Intelligence system.

Tools:
- ingest_youtube_video: Fetch and store YouTube video with metadata and transcript
- ingest_twitch_clip: Fetch and store Twitch clip
- query_creator_content: Search creator content using semantic similarity
- initialize_collections: Set up Vector DB collections for a tenant/workspace
- get_collection_stats: Get statistics for a collection

Resources:
- kg://schema: Knowledge Graph schema definition

Enable with: ENABLE_MCP_CREATOR_INTELLIGENCE=1
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

# Optional FastMCP dependency
try:
    from fastmcp import FastMCP

    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

    # Stub for when not installed
    from typing import Any

    class FastMCP:  # type: ignore
        def __init__(self, name: str):
            pass

        def tool(self, fn: Callable[..., Any] | None = None, /, **kwargs: Any) -> Callable[..., Any]:
            def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
                return f

            return decorator if fn is None else fn

        def resource(self, uri: str) -> Callable[..., Any]:
            def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
                return f

            return decorator


# Initialize MCP server
creator_intelligence_mcp = FastMCP("Creator Intelligence")

# Lazy-load tools to avoid import errors when dependencies missing
_ingestion_tools = None
_collection_manager = None


def _get_ingestion_tools() -> Any:
    """Lazy-load ingestion tools."""
    global _ingestion_tools

    if _ingestion_tools is None:
        try:
            from mcp_server.tools.creator_intelligence_ingestion import (
                get_ingestion_tools,
            )

            _ingestion_tools = get_ingestion_tools(enable_vector_storage=True)
        except Exception as e:
            logger.error(f"Failed to load ingestion tools: {e}")
            raise

    return _ingestion_tools


def _get_collection_manager() -> Any:
    """Lazy-load collection manager."""
    global _collection_manager

    if _collection_manager is None:
        try:
            from memory.creator_intelligence_collections import get_collection_manager

            _collection_manager = get_collection_manager(enable_semantic_cache=True)
        except Exception as e:
            logger.error(f"Failed to load collection manager: {e}")
            raise

    return _collection_manager


@creator_intelligence_mcp.tool
def ingest_youtube_video(
    url: str,
    tenant: str = "default",
    workspace: str = "main",
    fetch_transcript: bool = True,
) -> dict[str, Any]:
    """Ingest a YouTube video with metadata and optional transcript.

    This tool fetches public metadata from YouTube, optionally retrieves
    available transcripts, generates embeddings, and stores all data in
    the Knowledge Graph and Vector DB for future retrieval.

    Args:
        url: YouTube video URL (youtube.com/watch?v=... or youtu.be/...)
        tenant: Tenant identifier for data isolation (default: "default")
        workspace: Workspace identifier (default: "main")
        fetch_transcript: Whether to fetch available transcripts (default: True)

    Returns:
        Dictionary with ingestion results including:
        - platform: "youtube"
        - content_id: Video ID
        - title: Video title
        - creator_id: Channel ID or name
        - has_transcript: Whether transcript was retrieved
        - stored_in_vector_db: Whether embeddings were stored

    Example:
        >>> ingest_youtube_video(
        ...     url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        ...     tenant="h3podcast",
        ...     workspace="production",
        ... )
        {'platform': 'youtube', 'content_id': 'dQw4w9WgXcQ', ...}
    """
    tools = _get_ingestion_tools()

    result = tools.ingest_youtube_video(
        url=url,
        tenant=tenant,
        workspace=workspace,
        fetch_transcript=fetch_transcript,
    )

    if result.success:
        return result.data or {}
    else:
        raise RuntimeError(f"Ingestion failed: {result.error}")


@creator_intelligence_mcp.tool
def ingest_twitch_clip(
    url: str,
    tenant: str = "default",
    workspace: str = "main",
) -> dict[str, Any]:
    """Ingest a Twitch clip with metadata.

    Args:
        url: Twitch clip URL
        tenant: Tenant identifier (default: "default")
        workspace: Workspace identifier (default: "main")

    Returns:
        Dictionary with ingestion results

    Example:
        >>> ingest_twitch_clip(
        ...     url="https://clips.twitch.tv/ABC123",
        ...     tenant="hasanabi",
        ... )
    """
    tools = _get_ingestion_tools()

    result = tools.ingest_twitch_clip(
        url=url,
        tenant=tenant,
        workspace=workspace,
    )

    if result.success:
        return result.data or {}
    else:
        raise RuntimeError(f"Ingestion failed: {result.error}")


@creator_intelligence_mcp.tool
def query_creator_content(
    query_text: str,
    collection_type: str = "episodes",
    tenant: str = "default",
    workspace: str = "main",
    limit: int = 10,
    score_threshold: float = 0.7,
) -> dict[str, Any]:
    """Search creator content using semantic similarity.

    This tool embeds your query text and searches the Vector DB for similar
    content, enabling powerful semantic search across all ingested creator
    content.

    Args:
        query_text: Search query in natural language
        collection_type: Type of content to search (episodes, segments, claims, quotes, topics)
        tenant: Tenant identifier (default: "default")
        workspace: Workspace identifier (default: "main")
        limit: Maximum number of results (default: 10)
        score_threshold: Minimum similarity score 0.0-1.0 (default: 0.7)

    Returns:
        Dictionary with search results including:
        - results: List of matching content items
        - cache_hit: Whether results came from semantic cache
        - result_count: Number of results returned

    Example:
        >>> query_creator_content(
        ...     query_text="debate about artificial intelligence",
        ...     collection_type="episodes",
        ...     tenant="h3podcast",
        ... )
    """
    manager = _get_collection_manager()

    # Generate embedding for query
    from memory.embedding_service import get_embedding_service

    embedding_service = get_embedding_service()

    # Select embedding model based on collection type
    model_map = {
        "episodes": "balanced",  # 768-dim for quality
        "segments": "fast",  # 384-dim for speed
        "claims": "balanced",
        "quotes": "fast",
        "topics": "balanced",
    }

    model_choice = model_map.get(collection_type, "fast")

    # Generate query embedding
    embed_result = embedding_service.embed_text(query_text, model=model_choice, use_cache=True)

    if not embed_result.success:
        raise RuntimeError(f"Failed to generate query embedding: {embed_result.error}")

    query_embedding = embed_result.data["embedding"]

    # Query collection with semantic caching
    result = manager.query_with_cache(
        collection_type=collection_type,  # type: ignore
        query_embedding=query_embedding,
        query_text=query_text,
        tenant=tenant,
        workspace=workspace,
        limit=limit,
        score_threshold=score_threshold,
    )

    if result.success:
        return result.data or {}
    else:
        raise RuntimeError(f"Query failed: {result.error}")


@creator_intelligence_mcp.tool
def initialize_collections(
    tenant: str = "default",
    workspace: str = "main",
) -> dict[str, Any]:
    """Initialize all Creator Intelligence collections for a tenant/workspace.

    This tool sets up the specialized Vector DB collections (episodes, segments,
    claims, quotes, topics) with optimal configuration for production workloads.

    Args:
        tenant: Tenant identifier (default: "default")
        workspace: Workspace identifier (default: "main")

    Returns:
        Dictionary with initialization results including:
        - initialized: List of collection names created
        - total: Number of collections initialized

    Example:
        >>> initialize_collections(tenant="h3podcast", workspace="production")
        {'initialized': ['creator_episodes', ...], 'total': 5}
    """
    manager = _get_collection_manager()

    result = manager.initialize_collections(tenant=tenant, workspace=workspace)

    if result.success:
        return result.data or {}
    else:
        raise RuntimeError(f"Collection initialization failed: {result.error}")


@creator_intelligence_mcp.tool
def get_collection_stats(
    collection_type: str = "episodes",
    tenant: str = "default",
    workspace: str = "main",
) -> dict[str, Any]:
    """Get statistics for a Creator Intelligence collection.

    Args:
        collection_type: Type of collection (episodes, segments, claims, quotes, topics)
        tenant: Tenant identifier (default: "default")
        workspace: Workspace identifier (default: "main")

    Returns:
        Dictionary with collection statistics including:
        - vectors_count: Number of vectors in collection
        - quantization_enabled: Whether INT8 quantization is active
        - sparse_vectors_enabled: Whether sparse vectors are enabled

    Example:
        >>> get_collection_stats(collection_type="episodes", tenant="h3podcast")
        {'vectors_count': 1234, 'quantization_enabled': True, ...}
    """
    manager = _get_collection_manager()

    result = manager.get_collection_stats(
        collection_type=collection_type,  # type: ignore
        tenant=tenant,
        workspace=workspace,
    )

    if result.success:
        return result.data or {}
    else:
        raise RuntimeError(f"Failed to get stats: {result.error}")


@creator_intelligence_mcp.resource("kg://schema")
def get_kg_schema() -> str:
    """Get the Knowledge Graph schema definition.

    Returns:
        YAML schema definition as string
    """
    from pathlib import Path

    # Try to find schema.yaml
    possible_paths = [
        Path("crew/schema.yaml"),
        Path("schema.yaml"),
        Path(__file__).parent.parent.parent.parent / "crew" / "schema.yaml",
    ]

    for schema_path in possible_paths:
        if schema_path.exists():
            return schema_path.read_text()

    return "# Schema not found - ensure schema.yaml is in project root"


def main() -> None:
    """Run the Creator Intelligence MCP server."""
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP not available. Install with: pip install .[mcp]")
        return

    server_name = "Creator Intelligence MCP Server"

    logger.info("🚀 Starting Creator Intelligence MCP Server")
    logger.info(f"   Server Name: {server_name}")
    logger.info("   Available Tools:")
    logger.info("     - ingest_youtube_video")
    logger.info("     - ingest_twitch_clip")
    logger.info("     - query_creator_content")
    logger.info("     - initialize_collections")
    logger.info("     - get_collection_stats")
    logger.info("   Available Resources:")
    logger.info("     - kg://schema")

    # Run server
    creator_intelligence_mcp.run()


if __name__ == "__main__":
    main()
