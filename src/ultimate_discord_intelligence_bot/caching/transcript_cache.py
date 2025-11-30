"""Transcript caching implementation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


class TranscriptCache:
    """Cache for audio transcriptions."""

    def __init__(self, root: Optional[str] = None, enabled: bool = False):
        """Initialize the transcript cache.

        Args:
            root: Root directory for cache storage. If None, defaults to .cache/transcripts
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        if root:
            self.root = Path(root)
        else:
            self.root = Path(".cache/transcripts")
        self.logger = logging.getLogger(__name__)

    def _get_path(self, video_id: str, model_name: Optional[str]) -> Path:
        """Get the cache file path for a video ID and model."""
        model_part = f"_{model_name}" if model_name else ""
        safe_id = "".join(c for c in video_id if c.isalnum() or c in "-_")
        return self.root / f"{safe_id}{model_part}.json"

    def load(self, video_id: Optional[str], model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load a transcript from cache.

        Args:
            video_id: The video/content ID
            model_name: The model name used for transcription

        Returns:
            Cached transcript data or None if not found/disabled
        """
        if not self.enabled or not video_id:
            return None

        try:
            cache_path = self._get_path(video_id, model_name)
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.logger.debug(f"Cache hit for {video_id}")
                    return data
        except Exception as e:
            self.logger.warning(f"Failed to load cache for {video_id}: {e}")

        return None

    def store(
        self,
        video_id: Optional[str],
        model_name: Optional[str],
        transcript: str,
        segments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Store a transcript in cache.

        Args:
            video_id: The video/content ID
            model_name: The model name used for transcription
            transcript: The full transcript text
            segments: Optional list of transcript segments
        """
        if not self.enabled or not video_id:
            return

        try:
            if not self.root.exists():
                self.root.mkdir(parents=True, exist_ok=True)

            cache_path = self._get_path(video_id, model_name)
            data = {
                "video_id": video_id,
                "model": model_name,
                "transcript": transcript,
                "segments": segments,
            }

            # Better timestamp handling
            from datetime import datetime, timezone
            data["cached_at"] = datetime.now(timezone.utc).isoformat()

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Cached transcript for {video_id}")

        except Exception as e:
            self.logger.warning(f"Failed to store cache for {video_id}: {e}")
