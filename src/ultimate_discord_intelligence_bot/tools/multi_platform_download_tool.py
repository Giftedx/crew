"""Select the appropriate downloader based on URL domain."""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, Type, Optional
from urllib.parse import urlparse
from pydantic import Field

from crewai.tools import BaseTool

from .yt_dlp_download_tool import (
    YtDlpDownloadTool,
    YouTubeDownloadTool,
    TwitchDownloadTool,
    KickDownloadTool,
    TwitterDownloadTool,
    InstagramDownloadTool,
    TikTokDownloadTool,
    RedditDownloadTool,
)
from .discord_download_tool import DiscordDownloadTool

logger = logging.getLogger(__name__)


class MultiPlatformDownloadTool(BaseTool):
    """Dispatch to the correct platform downloader."""

    name: str = "Multi-Platform Download Tool"
    description: str = "Download media from supported platforms via yt-dlp. Provide url and optional quality."

    def __init__(self) -> None:
        super().__init__()
        self._dispatch: Dict[str, Type[BaseTool]] = {
            "youtube.com": YouTubeDownloadTool,
            "youtu.be": YouTubeDownloadTool,
            "twitch.tv": TwitchDownloadTool,
            "kick.com": KickDownloadTool,
            "twitter.com": TwitterDownloadTool,
            "x.com": TwitterDownloadTool,
            "instagram.com": InstagramDownloadTool,
            # TikTok share links often use vm.tiktok.com or vt.tiktok.com aliases
            "vm.tiktok.com": TikTokDownloadTool,
            "vt.tiktok.com": TikTokDownloadTool,
            "tiktok.com": TikTokDownloadTool,
            "reddit.com": RedditDownloadTool,
            "redd.it": RedditDownloadTool,
            "v.redd.it": RedditDownloadTool,
            "cdn.discordapp.com": DiscordDownloadTool,
            "media.discordapp.net": DiscordDownloadTool,
        }

    def _validate_url(self, url: str) -> Optional[str]:
        """Validate URL format and return error message if invalid."""
        if not url or not isinstance(url, str):
            return "URL is required and must be a string"
        
        if not url.strip():
            return "URL cannot be empty"
            
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return "URL must include protocol (http/https) and domain"
        except Exception as e:
            return f"Invalid URL format: {str(e)}"
            
        return None

    def _get_platform_from_url(self, url: str) -> Optional[str]:
        """Extract platform name from URL for metadata."""
        try:
            domain = urlparse(url).netloc.lower()
            for pattern in self._dispatch.keys():
                if domain.endswith(pattern):
                    # Convert domain to friendly platform name
                    if "youtube" in pattern or "youtu.be" in pattern:
                        return "YouTube"
                    elif "twitch" in pattern:
                        return "Twitch"
                    elif "kick" in pattern:
                        return "Kick"
                    elif "twitter" in pattern or "x.com" in pattern:
                        return "Twitter/X"
                    elif "instagram" in pattern:
                        return "Instagram"
                    elif "tiktok" in pattern:
                        return "TikTok"
                    elif "reddit" in pattern or "redd" in pattern:
                        return "Reddit"
                    elif "discord" in pattern:
                        return "Discord"
                    return pattern.capitalize()
            return "Unknown"
        except Exception:
            return "Unknown"

    def _run(self, url: str, quality: str = "1080p") -> Dict[str, Any]:
        """
        Route URL to the appropriate downloader with comprehensive error handling.

        Parameters
        ----------
        url:
            Media link to fetch (required)
        quality:
            Preferred quality setting passed through to the underlying
            platform tool. Defaults to ``1080p``.

        Returns
        -------
        Dict containing download results, metadata, and error information
        """
        start_time = time.time()
        
        # Input validation
        url_error = self._validate_url(url)
        if url_error:
            return {
                "status": "error",
                "error": url_error,
                "url": url,
                "quality": quality,
                "timestamp": time.time()
            }
        
        # Quality validation and normalization
        if not quality or not isinstance(quality, str):
            quality = "1080p"  # Default fallback
            
        platform = self._get_platform_from_url(url)
        logger.info(f"Processing {platform} URL: {url} with quality: {quality}")
        
        try:
            domain = urlparse(url).netloc.lower()
            
            # Find matching platform downloader
            for pattern, tool_cls in self._dispatch.items():
                if domain.endswith(pattern):
                    logger.debug(f"Using {tool_cls.__name__} for domain {domain}")
                    
                    # Execute download with error handling
                    result = tool_cls().run(url, quality=quality)
                    
                    # Ensure result is a dictionary
                    if not isinstance(result, dict):
                        result = {"status": "success", "data": result}
                    
                    # Add metadata
                    result.update({
                        "platform": platform,
                        "processing_time": time.time() - start_time,
                        "url": url,
                        "quality": quality,
                        "timestamp": time.time()
                    })
                    
                    logger.info(f"Successfully processed {platform} URL in {result['processing_time']:.2f}s")
                    return result
            
            # No matching platform found
            supported_platforms = list(set(self._dispatch.keys()))
            error_msg = f"Unsupported platform for URL: {url}. Supported domains: {', '.join(sorted(supported_platforms))}"
            
            logger.warning(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "platform": platform,
                "supported_platforms": supported_platforms,
                "url": url,
                "quality": quality,
                "processing_time": time.time() - start_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            error_msg = f"Unexpected error processing {platform} URL: {str(e)}"
            logger.error(error_msg)
            
            return {
                "status": "error",
                "error": error_msg,
                "platform": platform,
                "url": url,
                "quality": quality,
                "processing_time": time.time() - start_time,
                "timestamp": time.time()
            }

    def run(self, url: str, quality: str = "1080p") -> Dict[str, Any]:
        """Public wrapper with type safety."""
        return self._run(url, quality=quality)
