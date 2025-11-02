"""Path configuration for the Ultimate Discord Intelligence Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PathConfig:
    """Path configuration with validation and type safety.

    Manages all file and directory paths for the system, providing
    a centralized way to configure storage locations.
    """

    # Base directories
    base_dir: Path
    downloads_dir: Path
    config_dir: Path
    logs_dir: Path
    processing_dir: Path
    temp_dir: Path

    # yt-dlp paths
    ytdlp_dir: Path
    ytdlp_config: Path
    ytdlp_archive: Path

    # Credentials and secrets
    google_credentials: Path | None = None
    openai_credentials: Path | None = None

    # Cache directories
    cache_dir: Path | None = None
    vector_cache_dir: Path | None = None

    def __post_init__(self):
        """Validate paths after initialization."""
        self._validate_paths()
        self._ensure_directories()

    def _validate_paths(self) -> None:
        """Validate path configuration."""
        # Ensure base directory is absolute
        if not self.base_dir.is_absolute():
            self.base_dir = self.base_dir.resolve()

        # Ensure all subdirectories are relative to base_dir
        if not self.downloads_dir.is_absolute():
            self.downloads_dir = self.base_dir / self.downloads_dir

        if not self.config_dir.is_absolute():
            self.config_dir = self.base_dir / self.config_dir

        if not self.logs_dir.is_absolute():
            self.logs_dir = self.base_dir / self.logs_dir

        if not self.processing_dir.is_absolute():
            self.processing_dir = self.base_dir / self.processing_dir

        if not self.temp_dir.is_absolute():
            self.temp_dir = self.base_dir / self.temp_dir

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.base_dir,
            self.downloads_dir,
            self.config_dir,
            self.logs_dir,
            self.processing_dir,
            self.temp_dir,
        ]

        # Add optional directories if they exist
        if self.cache_dir:
            directories.append(self.cache_dir)
        if self.vector_cache_dir:
            directories.append(self.vector_cache_dir)

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_path(self, path_type: str) -> Path:
        """Get a path by type."""
        path_mapping = {
            "base": self.base_dir,
            "downloads": self.downloads_dir,
            "config": self.config_dir,
            "logs": self.logs_dir,
            "processing": self.processing_dir,
            "temp": self.temp_dir,
            "ytdlp": self.ytdlp_dir,
            "ytdlp_config": self.ytdlp_config,
            "ytdlp_archive": self.ytdlp_archive,
            "cache": self.cache_dir,
            "vector_cache": self.vector_cache_dir,
        }

        if path_type in path_mapping:
            result = path_mapping[path_type]
            if result is None:
                raise ValueError(f"Path {path_type} is not configured")
            return result
        else:
            raise ValueError(f"Unknown path type: {path_type}")

    def set_path(self, path_type: str, path: Path) -> None:
        """Set a path by type."""
        if path_type == "base":
            self.base_dir = path
        elif path_type == "downloads":
            self.downloads_dir = path
        elif path_type == "config":
            self.config_dir = path
        elif path_type == "logs":
            self.logs_dir = path
        elif path_type == "processing":
            self.processing_dir = path
        elif path_type == "temp":
            self.temp_dir = path
        elif path_type == "ytdlp":
            self.ytdlp_dir = path
        elif path_type == "ytdlp_config":
            self.ytdlp_config = path
        elif path_type == "ytdlp_archive":
            self.ytdlp_archive = path
        elif path_type == "cache":
            self.cache_dir = path
        elif path_type == "vector_cache":
            self.vector_cache_dir = path
        else:
            raise ValueError(f"Unknown path type: {path_type}")

    @classmethod
    def from_env(cls) -> PathConfig:
        """Create path configuration from environment variables."""
        # Get base directory from environment or use default
        base_dir = Path(os.getenv("CREWAI_BASE_DIR", Path.home() / "crew_data"))

        # Get subdirectories from environment or use defaults
        downloads_dir = Path(os.getenv("CREWAI_DOWNLOADS_DIR", base_dir / "Downloads"))
        config_dir = Path(os.getenv("CREWAI_CONFIG_DIR", base_dir / "Config"))
        logs_dir = Path(os.getenv("CREWAI_LOGS_DIR", base_dir / "Logs"))
        processing_dir = Path(os.getenv("CREWAI_PROCESSING_DIR", base_dir / "Processing"))
        temp_dir = Path(os.getenv("CREWAI_TEMP_DIR", base_dir / "temp"))

        # Get yt-dlp paths
        ytdlp_dir = Path(os.getenv("CREWAI_YTDLP_DIR", base_dir / "yt-dlp"))
        ytdlp_config = Path(os.getenv("CREWAI_YTDLP_CONFIG", ytdlp_dir / "config" / "crewai-system.conf"))
        ytdlp_archive = Path(os.getenv("CREWAI_YTDLP_ARCHIVE", ytdlp_dir / "archives" / "crewai_downloads.txt"))

        # Get credentials paths
        google_credentials = os.getenv("GOOGLE_CREDENTIALS")
        openai_credentials = os.getenv("OPENAI_CREDENTIALS")

        # Get cache directories
        cache_dir = os.getenv("CACHE_DIR")
        vector_cache_dir = os.getenv("VECTOR_CACHE_DIR")

        return cls(
            base_dir=base_dir,
            downloads_dir=downloads_dir,
            config_dir=config_dir,
            logs_dir=logs_dir,
            processing_dir=processing_dir,
            temp_dir=temp_dir,
            ytdlp_dir=ytdlp_dir,
            ytdlp_config=ytdlp_config,
            ytdlp_archive=ytdlp_archive,
            google_credentials=Path(google_credentials) if google_credentials else None,
            openai_credentials=Path(openai_credentials) if openai_credentials else None,
            cache_dir=Path(cache_dir) if cache_dir else None,
            vector_cache_dir=Path(vector_cache_dir) if vector_cache_dir else None,
        )
