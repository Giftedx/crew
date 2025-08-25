"""Backward compatible import for YouTube downloads.

The implementation now lives in :mod:`yt_dlp_download_tool`. This stub maintains
the previous import path used by existing code and tests.
"""

from .yt_dlp_download_tool import YouTubeDownloadTool  # noqa: F401

