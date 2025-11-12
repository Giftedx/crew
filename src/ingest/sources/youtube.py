"""Compatibility shim for ingest.sources.youtube.

Re-exports from domains.ingestion.providers for backward compatibility.
"""

from domains.ingestion.providers.youtube_download_tool import YouTubeDownloadTool


__all__ = ["YouTubeDownloadTool"]
